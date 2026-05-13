"""
Quick smoke test for Ollama-first setup.
Generates test cases and saves them to test_data/test_cases.
"""

from pathlib import Path
import sys
import argparse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src_config import config
from ai_engine_test_generator import TestGenerator


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Ollama smoke test")
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run a fast smoke mode (fewer tests, shorter prompt, lower tokens)",
    )
    args = parser.parse_args()

    is_quick = args.quick
    max_tokens = 300 if is_quick else config.AI_MAX_TOKENS
    test_count = 1 if is_quick else 5
    feature_description = (
        "Simple login with email and password validation."
        if is_quick
        else """
    Login page with:
    - Email + password authentication
    - Validation errors for invalid input
    - Lockout after 5 failed attempts
    - Remember me option
    """
    )

    generator = TestGenerator(
        model=config.AI_MODEL,
        ai_provider=config.AI_PROVIDER,
        api_key=config.ANTHROPIC_API_KEY if config.AI_PROVIDER == "anthropic" else config.OPENAI_API_KEY,
        temperature=config.AI_TEMPERATURE,
        max_tokens=max_tokens,
        ollama_host=config.OLLAMA_HOST,
        ollama_timeout=config.OLLAMA_TIMEOUT,
    )

    test_cases = generator.generate_from_description(
        description=feature_description,
        test_count=test_count,
        include_edge_cases=not is_quick,
        include_negative_tests=not is_quick,
        priority="high",
        category="functional",
    )

    output_path = Path(config.TEST_CASES_PATH) / "ollama_generated_tests.json"
    generator.save_test_cases(test_cases, output_path)

    print(f"AI_PROVIDER: {config.AI_PROVIDER}")
    print(f"AI_MODEL: {config.AI_MODEL}")
    print(f"OLLAMA_TIMEOUT: {config.OLLAMA_TIMEOUT}s")
    print(f"QUICK_MODE: {is_quick}")
    print(f"Generated: {len(test_cases)} test cases")
    print(f"Saved to: {output_path}")


if __name__ == "__main__":
    main()
