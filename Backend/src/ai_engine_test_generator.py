"""
ai_engine/test_generator.py - AI-powered test case generation
Uses Gemini to intelligently generate test cases from descriptions
"""

import json
import re
import os
import time
from collections import deque
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from google import genai

from loguru import logger


def _load_env_file() -> None:
    """Load Backend/.env values into process environment (non-destructive)."""
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


@dataclass
class TestCase:
    """Data class representing a test case"""
    id: str
    name: str
    description: str
    preconditions: List[str]
    steps: List[str]
    expected_results: List[str]
    test_data: Dict[str, Any]
    priority: str  # high, medium, low
    category: str  # functional, regression, smoke, performance, security
    tags: List[str]
    author: str = "AI"
    created_date: str = None

    def __post_init__(self):
        if self.created_date is None:
            self.created_date = datetime.now().isoformat()

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2)


class TestGenerator:
    """AI-powered test case generator"""
    GEMINI_FIXED_MODEL = "gemini-2.5-flash"
    GEMINI_MAX_RETRIES = 5
    GEMINI_RETRY_BASE_SECONDS = 1
    MAX_DESCRIPTION_CHARS = 20000
    MAX_TESTS_PER_REQUEST = 10

    def __init__(
        self,
        model: str = "gemini-2.5-flash",
        ai_provider: str = "gemini",
        api_key: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 8192,
        ollama_host: str = "http://localhost:11434",
        ollama_timeout: int = 600
    ):
        """
        Initialize test generator

        Args:
            model: Model name
            ai_provider: AI provider (gemini only)
            api_key: API key for the provider
            temperature: Creativity level (0-1)
            max_tokens: Maximum tokens in response (unused — Gemini uses its own default)
            ollama_host: Ollama base URL (reserved, unused)
            ollama_timeout: Timeout for Ollama requests in seconds (reserved, unused)
        """
        _load_env_file()

        env_temp = float(os.getenv("AI_TEMPERATURE", str(temperature)))
        env_ollama_host = os.getenv("OLLAMA_HOST", ollama_host)
        env_ollama_timeout = int(os.getenv("OLLAMA_TIMEOUT", str(ollama_timeout)))

        self.model = self.GEMINI_FIXED_MODEL
        self.ai_provider = "gemini"
        self.temperature = env_temp
        self.ollama_host = env_ollama_host.rstrip("/")
        self.ollama_timeout = env_ollama_timeout
        self.api_key = api_key or self._resolve_api_key("gemini")
        self.client = None
        self.gemini_max_requests_per_minute = int(os.getenv("GEMINI_MAX_REQUESTS_PER_MINUTE", "10"))
        self._request_timestamps: deque[float] = deque()

        # Initialize Gemini client once, after _load_env_file() has run
        if self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini client: {str(e)}")
                self.client = None

        logger.info(f"Initialized TestGenerator with {self.ai_provider}/{self.model}")

    # ------------------------------------------------------------------ #
    #  Public methods                                                       #
    # ------------------------------------------------------------------ #

    def generate_from_description(
        self,
        description: str,
        test_count: int = 10,
        include_edge_cases: bool = True,
        include_negative_tests: bool = True,
        priority: str = "medium",
        category: str = "functional"
    ) -> List[TestCase]:
        """
        Generate test cases from feature description.

        Args:
            description: Feature description or user story
            test_count: Number of test cases to generate
            include_edge_cases: Include edge case tests
            include_negative_tests: Include negative scenario tests
            priority: Default priority level
            category: Test category

        Returns:
            List of generated TestCase objects
        """
        logger.info(f"Generating {test_count} test cases from description")
        safe_description = self._prepare_description(description)
        remaining = max(1, test_count)
        all_cases: List[TestCase] = []
        batch_index = 0

        while remaining > 0:
            batch_index += 1
            batch_count = min(self.MAX_TESTS_PER_REQUEST, remaining)
            prompt = self._build_generation_prompt(
                description=safe_description,
                test_count=batch_count,
                include_edge_cases=include_edge_cases,
                include_negative_tests=include_negative_tests,
                priority=priority,
                category=category
            )

            response = self._call_ai(prompt)
            batch_cases = self._parse_test_cases(response, priority, category)

            if not batch_cases:
                logger.warning(
                    f"Batch {batch_index}: unparseable model output, using deterministic fallback"
                )
                # FIX: ส่ง index ที่ถูกต้องเพื่อให้ id ไม่ซ้ำ
                current_index = len(all_cases) + 1
                batch_cases = [self._build_fallback_test_case(
                    safe_description, priority, category, index=current_index
                )]

            all_cases.extend(batch_cases[:batch_count])
            remaining -= batch_count

            if remaining > 0:
                time.sleep(1)

        logger.info(f"Generated {len(all_cases)} test cases")
        return all_cases[:test_count]

    def generate_from_user_story(
        self,
        story: str,
        acceptance_criteria: List[str],
        test_count: int = 10
    ) -> List[TestCase]:
        """Generate test cases from user story and acceptance criteria."""
        logger.info("Generating test cases from user story")

        prompt = f"""
        Generate comprehensive test cases for the following user story:

        STORY: {story}

        ACCEPTANCE CRITERIA:
        {chr(10).join(f'- {ac}' for ac in acceptance_criteria)}

        Create {test_count} test cases that cover:
        1. All acceptance criteria
        2. Edge cases and boundary conditions
        3. Negative scenarios
        4. Performance considerations
        5. Security aspects

        For each test case, provide:
        - Test ID (TC_XXX)
        - Name
        - Description
        - Preconditions
        - Step-by-step actions
        - Expected results
        - Test data
        - Priority (High/Medium/Low)
        - Category (Functional/Regression/Smoke/Performance/Security)
        - Tags

        Return as JSON array.
        """

        response = self._call_ai(prompt)
        test_cases = self._parse_test_cases(response)

        logger.info(f"Generated {len(test_cases)} test cases from user story")
        return test_cases

    def generate_regression_tests(
        self,
        feature_name: str,
        previous_bugs: List[str],
        test_count: int = 5
    ) -> List[TestCase]:
        """Generate regression test cases based on previous bugs."""
        logger.info(f"Generating regression tests for {feature_name}")

        bug_list = "\n".join(f"- Bug: {bug}" for bug in previous_bugs)

        prompt = f"""
        Create regression test cases to prevent these bugs from happening again:

        Feature: {feature_name}

        Previous Bugs:
        {bug_list}

        Generate {test_count} test cases that specifically test the areas where bugs occurred.
        Each test case should be designed to catch the regression early.

        Return as JSON array with detailed test cases.
        """

        response = self._call_ai(prompt)
        test_cases = self._parse_test_cases(response, category="regression")

        logger.info(f"Generated {len(test_cases)} regression test cases")
        return test_cases

    def optimize_test_cases(
        self,
        test_cases: List[TestCase],
        criteria: str = "reduce_redundancy"
    ) -> List[TestCase]:
        """Optimize existing test cases to remove redundancy and improve coverage."""
        logger.info(f"Optimizing {len(test_cases)} test cases")

        test_cases_json = json.dumps([tc.to_dict() for tc in test_cases], indent=2)

        prompt = f"""
        Analyze and optimize these test cases based on {criteria}:

        {test_cases_json}

        Provide optimized test cases by:
        1. Removing redundant test cases
        2. Consolidating similar tests
        3. Improving coverage gaps
        4. Prioritizing high-impact tests

        Return as JSON array.
        """

        response = self._call_ai(prompt)
        optimized = self._parse_test_cases(response)

        logger.info(f"Optimized to {len(optimized)} test cases")
        return optimized

    def generate_edge_cases(
        self,
        feature_description: str,
        test_count: int = 5
    ) -> List[TestCase]:
        """Generate edge case test cases."""
        logger.info("Generating edge case test cases")

        prompt = f"""
        Generate {test_count} edge case test cases for this feature:

        {feature_description}

        Focus on:
        - Boundary conditions
        - Extreme values
        - Special characters
        - Unicode and international characters
        - Large data sets
        - Null/empty values
        - Concurrency issues

        Return as JSON array with detailed edge case test cases.
        """

        response = self._call_ai(prompt)
        test_cases = self._parse_test_cases(response, category="edge_case")

        return test_cases

    def save_test_cases(
        self,
        test_cases: List[TestCase],
        output_path: Path
    ) -> None:
        """Save test cases to JSON file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "generated_at": datetime.now().isoformat(),
            "total_tests": len(test_cases),
            "test_cases": [tc.to_dict() for tc in test_cases]
        }

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Saved {len(test_cases)} test cases to {output_path}")

    def load_test_cases(self, input_path: Path) -> List[TestCase]:
        """Load test cases from JSON file."""
        with open(input_path, "r") as f:
            data = json.load(f)

        test_cases = []
        for tc_data in data.get("test_cases", []):
            test_cases.append(TestCase(**tc_data))

        logger.info(f"Loaded {len(test_cases)} test cases from {input_path}")
        return test_cases

    # ------------------------------------------------------------------ #
    #  Private methods                                                      #
    # ------------------------------------------------------------------ #

    def _build_generation_prompt(
        self,
        description: str,
        test_count: int,
        include_edge_cases: bool,
        include_negative_tests: bool,
        priority: str,
        category: str
    ) -> str:
        """Build the prompt for test case generation."""
        extra_instructions = []
        if include_edge_cases:
            extra_instructions.append("- Include edge case scenarios with boundary values")
        if include_negative_tests:
            extra_instructions.append("- Include negative test scenarios (error handling)")
        extra_text = "\n".join(extra_instructions) if extra_instructions else ""

        return f"""Generate exactly {test_count} AI website automation test cases.

FEATURE DESCRIPTION:
{description}

IMPORTANT RULES:
- Return ONLY raw JSON
- Do NOT use markdown
- Do NOT wrap response in ```json
- Do NOT explain anything
- Start response with [
- End response with ]
- Every test case MUST contain test_data.actions
- Actions MUST be executable by Playwright

ALLOWED ACTION TYPES:
- goto
- click
- fill
- press
- wait
- assert_url_contains
- assert_text_visible
- assert_element_visible

ACTION FORMAT EXAMPLES:

Click action:
{{
  "type": "click",
  "selector": "button[type='submit']"
}}

Fill action:
{{
  "type": "fill",
  "selector": "input[name='email']",
  "value": "test@example.com"
}}

Goto action:
{{
  "type": "goto",
  "value": "https://example.com"
}}

Assertion action:
{{
  "type": "assert_element_visible",
  "selector": ".hero-section"
}}

Wait action:
{{
  "type": "wait",
  "value": 1000
}}

REQUIREMENTS:
- Generate exactly {test_count} test cases
{extra_text}

- Cover:
  * navigation
  * clickable buttons
  * links
  * forms
  * inputs
  * responsiveness
  * page loading
  * error handling

- Each test case MUST contain these fields:

  * id
  * name
  * description
  * preconditions
  * steps
  * expected_results
  * test_data
  * priority
  * category
  * tags

FIELD RULES:

- id must be:
  TC_001
  TC_002

- priority must be:
  high
  medium
  low

- category must be:
  functional
  regression
  smoke
  performance
  security

- preconditions must always be a list
- steps must always be a list
- expected_results must always be a list
- tags must always be a list
- test_data must always be an object

CRITICAL:
test_data MUST contain:

{{
  "actions": [
    {{
      "type": "goto",
      "value": "https://example.com"
    }},
    {{
      "type": "click",
      "selector": "button"
    }},
    {{
      "type": "assert_element_visible",
      "selector": "body"
    }}
  ]
}}

FULL VALID RESPONSE EXAMPLE:

[
  {{
    "id": "TC_001",
    "name": "Verify homepage loads successfully",
    "description": "Check homepage accessibility and visibility",
    "preconditions": [],
    "steps": [
      "Open homepage",
      "Verify body is visible"
    ],
    "expected_results": [
      "Homepage loads successfully"
    ],
    "test_data": {{
      "actions": [
        {{
          "type": "goto",
          "value": "https://example.com"
        }},
        {{
          "type": "assert_element_visible",
          "selector": "body"
        }}
      ]
    }},
    "priority": "high",
    "category": "functional",
    "tags": ["homepage", "smoke"]
  }}
]

Return ONLY valid JSON array.

Remember:
- Return ONLY JSON, no markdown, no explanations
- Each test case is independent
- Include both positive and negative scenarios
- Make tests clear and maintainable"""

    def _prepare_description(self, description: str) -> str:
        """Trim and normalize large input to reduce token usage."""
        normalized = " ".join((description or "").split())
        if len(normalized) <= self.MAX_DESCRIPTION_CHARS:
            return normalized
        logger.warning(
            f"Input description too large ({len(normalized)} chars), "
            f"truncating to {self.MAX_DESCRIPTION_CHARS} chars"
        )
        return normalized[: self.MAX_DESCRIPTION_CHARS]

    def _call_ai(self, prompt: str) -> str:
        """
        Call Gemini API with retry logic for rate limits and server errors.

        FIX: reuse self.client instead of creating a new one every attempt.
        FIX: remove max_output_tokens so Gemini uses its own maximum,
             preventing JSON from being truncated mid-response.
        """
        from google.genai import errors

        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required when AI_PROVIDER=gemini")

        # Lazily initialise client if it wasn't ready at startup
        if self.client is None:
            self.client = genai.Client(api_key=self.api_key)

        model_name = self._normalize_gemini_model_name(self.model)

        for attempt in range(self.GEMINI_MAX_RETRIES):
            try:
                self._enforce_rate_limit()

                # FIX: no max_output_tokens → full JSON is never cut off
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config={
                        "temperature": self.temperature,
                    }
                )

                if hasattr(response, "text"):
                    text_output = response.text.strip()
                elif hasattr(response, "candidates") and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, "content") and hasattr(candidate.content, "parts"):
                        text_output = "\n".join(
                            part.text
                            for part in candidate.content.parts
                            if hasattr(part, "text")
                        ).strip()
                    else:
                        text_output = ""
                else:
                    text_output = ""

                if not text_output:
                    raise RuntimeError("Empty text response from Gemini API")

                logger.debug(f"Gemini response length: {len(text_output)} chars")
                return text_output

            except (errors.ServerError, errors.RateLimitError) as e:
                if attempt < self.GEMINI_MAX_RETRIES - 1:
                    wait_time = self.GEMINI_RETRY_BASE_SECONDS * (2 ** attempt)
                    logger.warning(
                        f"API error (attempt {attempt + 1}/{self.GEMINI_MAX_RETRIES}): {e}. "
                        f"Retrying in {wait_time:.1f}s..."
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(f"AI API call failed after {self.GEMINI_MAX_RETRIES} attempts: {e}")
                    raise
            except Exception as e:
                logger.error(f"AI API call failed ({self.ai_provider}): {e}")
                raise

    def _parse_test_cases(
        self,
        response: str,
        priority: str = "medium",
        category: str = "functional"
    ) -> List[TestCase]:
        """Parse AI response into TestCase objects."""
        try:
            test_cases_data = self._extract_test_cases_payload(response)
            if not test_cases_data:
                logger.warning("No JSON found in response")
                return []

            test_cases = []
            for tc_data in test_cases_data:
                try:
                    tc_data.setdefault("id", f"TC_AUTO_{len(test_cases) + 1:03d}")
                    tc_data.setdefault("name", "AI Generated Test")
                    tc_data.setdefault("description", "Generated by Gemini")
                    tc_data.setdefault("preconditions", [])
                    tc_data.setdefault("steps", [])
                    tc_data.setdefault("expected_results", [])
                    tc_data.setdefault("test_data", {})
                    tc_data.setdefault("tags", [])
                    # FIX: apply caller-supplied defaults when AI omits these fields
                    tc_data.setdefault("priority", priority)
                    tc_data.setdefault("category", category)

                    test_cases.append(TestCase(**tc_data))
                except Exception as e:
                    logger.warning(f"Failed to parse test case: {e}")

            return test_cases

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}")
            return []

    def _build_fallback_test_case(
        self,
        description: str,
        priority: str,
        category: str,
        index: int = 1,   # FIX: accept index so id is never duplicated
    ) -> TestCase:
        """
        Create a safe fallback test case when model output is not parseable.
        Uses TEST_REAL_URL env var (set by web_url_tester.py --url) as the goto target.
        """
        url = self._get_real_test_url()
        short_desc = " ".join(description.strip().split())[:140]
        return TestCase(
            id=f"TC_{index:03d}",          # FIX: TC_001, TC_002, TC_003 …
            name="Basic page load and visibility test",
            description=f"Auto-generated test for: {short_desc}",
            preconditions=["Application under test is accessible"],
            steps=[
                "Navigate to the application",
                "Verify page loads successfully",
                "Confirm body element is visible",
            ],
            expected_results=[
                "Page loads without errors",
                "Body element is visible on the page",
                "Application is responsive",
            ],
            test_data={
                "actions": [
                    {"type": "goto", "value": url},   # FIX: real URL from --url
                    {"type": "wait", "value": 1000},
                    {"type": "assert_element_visible", "selector": "body"},
                ]
            },
            priority=priority,
            category=category,
            tags=["fallback", "smoke", "automated"],
        )

    def _get_real_test_url(self) -> str:
        """
        Return the target URL supplied via --url (stored in TEST_REAL_URL env var
        by web_url_tester.py before importing this module).
        Falls back to https://example.com/ if not set.
        """
        return os.getenv("TEST_REAL_URL", "https://example.com/")

    def _extract_test_cases_payload(self, response: str) -> List[Dict[str, Any]]:
        """Extract test case payload from common LLM JSON response shapes."""
        cleaned = self._clean_llm_response(response)
        decoder = json.JSONDecoder()

        # 1. Try to find a JSON array that starts with [{
        for match in re.finditer(r'\[\s*\{', cleaned):
            try:
                obj, _ = decoder.raw_decode(cleaned[match.start():])
                if isinstance(obj, list) and obj and all(isinstance(i, dict) for i in obj):
                    logger.debug(f"Extracted {len(obj)} test cases from JSON array")
                    return obj
            except json.JSONDecodeError:
                continue

        # 2. Fallback: scan character-by-character for any JSON value
        for idx, char in enumerate(cleaned):
            if char not in "[{":
                continue
            try:
                obj, _ = decoder.raw_decode(cleaned[idx:])
            except json.JSONDecodeError:
                continue

            if isinstance(obj, list) and obj:
                return obj
            if isinstance(obj, dict):
                if isinstance(obj.get("test_cases"), list):
                    return obj["test_cases"]
                if {"id", "name", "description"}.issubset(obj.keys()):
                    return [obj]

        logger.debug(
            f"Could not extract JSON from response.\n"
            f"Total chars: {len(cleaned)}\n"
            f"First 500 : {cleaned[:500]}\n"
            f"Last  200 : {cleaned[-200:]}"
        )
        return []

    def _clean_llm_response(self, response: str) -> str:
        """Remove common non-JSON wrappers from LLM responses."""
        text = response.strip()
        text = re.sub(r"<think>[\s\S]*?</think>", "", text, flags=re.IGNORECASE)
        text = re.sub(r"```json\s*([\s\S]*?)```", r"\1", text, flags=re.IGNORECASE)
        text = re.sub(r"```([\s\S]*?)```", r"\1", text)
        return text.strip()

    def _normalize_gemini_model_name(self, raw_model: str) -> str:
        """Normalize common malformed model strings from .env."""
        model = (raw_model or "").strip()
        if "=" in model:
            model = model.split("=")[-1].strip()
        model = model.replace("models/", "").strip()
        if model.startswith("gemini-"):
            return model
        return self.GEMINI_FIXED_MODEL

    def _resolve_api_key(self, provider: str) -> Optional[str]:
        """Resolve API key from env by provider."""
        key_map = {"gemini": "GEMINI_API_KEY"}
        env_key = key_map.get((provider or "").lower())
        return os.getenv(env_key) if env_key else None

    def _enforce_rate_limit(self) -> None:
        """Throttle requests to stay under the configured per-minute ceiling."""
        now = time.time()
        window = 60.0

        while self._request_timestamps and now - self._request_timestamps[0] >= window:
            self._request_timestamps.popleft()

        if len(self._request_timestamps) >= self.gemini_max_requests_per_minute:
            wait = window - (now - self._request_timestamps[0]) + 0.05
            wait = max(wait, 0.05)
            logger.warning(f"Local rate limiter active, waiting {wait:.2f}s")
            time.sleep(wait)
            now = time.time()
            while self._request_timestamps and now - self._request_timestamps[0] >= window:
                self._request_timestamps.popleft()

        self._request_timestamps.append(time.time())