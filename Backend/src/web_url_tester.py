"""
Unified AI-driven web tester:
- HTTP availability check
- DOM snapshot collection
- Gemini-generated action-based test cases
- Playwright execution for generated actions
- HTML report

AI Test Constraints/Goals:
1. ตรวจสอบว่า "ทุกหน้า" ของเว็บไซต์สามารถเข้าถึงและทำงานได้ (Page availability & basic functionality)
2. ตรวจสอบ "ความเร็วในการตอบสนอง" (Response time) ของแต่ละหน้า/แต่ละ action
3. สร้าง "รายงานผลการทดสอบ" ในรูปแบบเอกสาร (Documented report) เพื่อยืนยันผลลัพธ์และความถูกต้อง

Usage:
    python Backend/src/web_url_tester.py --url https://example.com
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ai_engine_test_generator import TestGenerator, TestCase
from report_generator_html import HTMLReporter, TestResult
from screenshot_manager_capture import ScreenshotCapture
from src_config import config

# PDF & Upload dependencies
import subprocess
import shutil
import tempfile
import os

def generate_pdf_report(html_path: Path, pdf_path: Path) -> bool:
    """
    Convert HTML report to PDF using pdfkit (requires wkhtmltopdf) or fallback to weasyprint if available.
    Returns True if success, False otherwise.
    """
    try:
        import pdfkit
        pdfkit.from_file(str(html_path), str(pdf_path))
        return True
    except ImportError:
        try:
            from weasyprint import HTML
            HTML(filename=str(html_path)).write_pdf(str(pdf_path))
            return True
        except ImportError:
            print("[ERROR] Neither pdfkit nor weasyprint is installed. Cannot generate PDF report.")
            return False
    except Exception as e:
        print(f"[ERROR] Failed to generate PDF: {e}")
        return False

def upload_report(file_path: Path, destination: str = None) -> bool:
    """
    Upload report file to a destination. (Stub: extend for Google Drive/S3/FTP as needed)
    Returns True if upload is successful.
    """
    # Example: just print path, or extend to real upload logic
    print(f"[UPLOAD] Would upload {file_path} to {destination or 'default location'}")
    # TODO: Implement actual upload logic here
    return True

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None


def _safe_name_from_url(url: str) -> str:
    cleaned = (
        url.replace("https://", "")
        .replace("http://", "")
        .replace("/", "_")
        .replace("?", "_")
        .replace("&", "_")
        .replace("=", "_")
        .replace(":", "_")
    )
    return cleaned[:80] or "web_test"


def run_http_test(url: str, timeout: int) -> TestResult:
    start = time.time()
    try:
        response = requests.get(url, timeout=timeout)
        status_ok = response.status_code < 400
        return TestResult(
            test_id="WEB_HTTP_001",
            test_name="HTTP availability",
            status="passed" if status_ok else "failed",
            duration=time.time() - start,
            message=f"Status code: {response.status_code}",
            tags=["web", "http", "smoke"],
            error_details=None if status_ok else f"Unexpected status code: {response.status_code}",
        )
    except Exception as exc:
        return TestResult(
            test_id="WEB_HTTP_001",
            test_name="HTTP availability",
            status="error",
            duration=time.time() - start,
            tags=["web", "http", "smoke"],
            error_details=str(exc),
        )


def _collect_page_context(url: str, timeout: int) -> Dict[str, Any]:
    if sync_playwright is None:
        return {"url": url, "error": "playwright_not_installed"}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=timeout * 1000)
        page.wait_for_timeout(1200)

        context = page.evaluate(
            """
            () => {
              const norm = (s) => (s || '').replace(/\s+/g, ' ').trim();
              const elements = Array.from(document.querySelectorAll('button, a, input, select, textarea, [role="button"], [onclick]'));
              const top = elements
                .filter((el) => {
                  const r = el.getBoundingClientRect();
                  const style = window.getComputedStyle(el);
                  return r.width > 0 && r.height > 0 && style.display !== 'none' && style.visibility !== 'hidden';
                })
                .slice(0, 80)
                .map((el) => ({
                  tag: (el.tagName || '').toLowerCase(),
                  type: el.getAttribute('type') || '',
                  role: el.getAttribute('role') || '',
                  id: el.id || '',
                  name: el.getAttribute('name') || '',
                  text: norm(el.innerText || el.value || el.getAttribute('aria-label') || el.getAttribute('placeholder') || ''),
                  href: el.getAttribute('href') || '',
                  classes: norm(el.className || ''),
                }));

              return {
                title: document.title || '',
                url: location.href,
                forms: document.querySelectorAll('form').length,
                buttons: document.querySelectorAll('button, input[type="submit"], [role="button"]').length,
                links: document.querySelectorAll('a[href]').length,
                inputs: document.querySelectorAll('input, textarea, select').length,
                top_elements: top,
              };
            }
            """
        )
        browser.close()
        return context


def _generate_website_cases(generator: TestGenerator, target_url: str, page_context: Dict[str, Any], test_count: int) -> List[TestCase]:
    prompt = f"""
Generate {test_count} website test cases for this page.
URL: {target_url}
Page context JSON:
{json.dumps(page_context, ensure_ascii=False, indent=2)}

Rules:
1) Tests must be generic and adaptive, not hardcoded to one button only.
2) Cover navigation, form behavior, clickable elements, and negative behavior where possible.
3) Each test case must include action steps in test_data.actions.
4) Use only these action types: goto, click, fill, press, wait, assert_url_contains, assert_text_visible, assert_element_visible.
5) For click/fill/assert_element_visible, include a CSS selector in selector field.
6) For fill, include value field.
7) For goto/assert_url_contains/assert_text_visible, include value field.
8) Keep each case 3-8 actions.
9) Return JSON array only.

Expected shape for each test_data.actions item:
{{"type":"click","selector":"button[type='submit']"}}
"""

    return generator.generate_from_description(
        description=prompt,
        test_count=test_count,
        include_edge_cases=True,
        include_negative_tests=True,
        priority="high",
        category="functional",
    )


def _run_action(page, action: Dict[str, Any], timeout_ms: int) -> None:
    action_type = str(action.get("type", "")).strip().lower()
    selector = action.get("selector")
    value = action.get("value")

    if action_type == "goto":
        page.goto(str(value), wait_until="domcontentloaded", timeout=timeout_ms)
    elif action_type == "click":
        page.locator(str(selector)).first.click(timeout=timeout_ms)
    elif action_type == "fill":
        page.locator(str(selector)).first.fill(str(value or ""), timeout=timeout_ms)
    elif action_type == "press":
        page.keyboard.press(str(value or "Enter"))
    elif action_type == "wait":
        page.wait_for_timeout(int(value or 1000))
    elif action_type == "assert_url_contains":
        current = page.url
        expected = str(value or "")
        if expected not in current:
            raise AssertionError(f"URL mismatch: expected to contain '{expected}', got '{current}'")
    elif action_type == "assert_text_visible":
        text = str(value or "")
        page.get_by_text(text, exact=False).first.wait_for(state="visible", timeout=timeout_ms)
    elif action_type == "assert_element_visible":
        page.locator(str(selector)).first.wait_for(state="visible", timeout=timeout_ms)
    else:
        raise ValueError(f"Unsupported action type: {action_type}")


def run_ai_website_flow(
    url: str,
    timeout: int,
    capture: ScreenshotCapture,
    test_key: str,
    test_count: int,
) -> List[TestResult]:
    if sync_playwright is None:
        return [
            TestResult(
                test_id="WEB_UI_000",
                test_name="UI automation",
                status="skipped",
                duration=0.0,
                message="Playwright is not installed",
                tags=["web", "ui", "playwright"],
            )
        ]

    generator = TestGenerator(
        model=config.AI_MODEL,
        ai_provider=config.AI_PROVIDER,
        api_key=(
            config.GEMINI_API_KEY
            if config.AI_PROVIDER == "gemini"
            else config.ANTHROPIC_API_KEY
            if config.AI_PROVIDER == "anthropic"
            else config.OPENAI_API_KEY
        ),
        temperature=0.3,
        max_tokens=3000,
        ollama_host=config.OLLAMA_HOST,
        ollama_timeout=config.OLLAMA_TIMEOUT,
    )

    results: List[TestResult] = []

    context_start = time.time()
    page_context = _collect_page_context(url, timeout)
    results.append(
        TestResult(
            test_id="AI_CTX_001",
            test_name="Collect page context",
            status="passed" if "error" not in page_context else "failed",
            duration=time.time() - context_start,
            message=f"Collected context from {page_context.get('url', url)}",
            tags=["ai", "context", "discovery"],
            error_details=page_context.get("error"),
        )
    )

    ai_start = time.time()
    test_cases = _generate_website_cases(generator, url, page_context, test_count=test_count)
    generator.save_test_cases(test_cases, Path(config.TEST_CASES_PATH) / "gemini_web_generated_cases.json")
    results.append(
        TestResult(
            test_id="AI_GEN_001",
            test_name="Gemini generate website test cases",
            status="passed" if test_cases else "failed",
            duration=time.time() - ai_start,
            message=f"Generated {len(test_cases)} test cases",
            tags=["ai", "gemini", "generation"],
        )
    )

    ui_start = time.time()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=config.HEADLESS)
            page = browser.new_page()

            for i, tc in enumerate(test_cases, start=1):
                case_start = time.time()
                test_id = tc.id or f"WEB_TC_{i:03d}"
                actions = (tc.test_data or {}).get("actions", [])
                if not actions:
                    results.append(
                        TestResult(
                            test_id=test_id,
                            test_name=tc.name,
                            status="failed",
                            duration=time.time() - case_start,
                            error_details="No actions in test_data.actions",
                            tags=["playwright", "ai", "generated"],
                        )
                    )
                    continue

                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=timeout * 1000)
                    for action in actions:
                        _run_action(page, action, timeout * 1000)

                    shot = capture.capture_playwright(page, test_name=f"{test_key}_tc_{i}", test_id=test_id, full_page=True)
                    results.append(
                        TestResult(
                            test_id=test_id,
                            test_name=tc.name,
                            status="passed",
                            duration=time.time() - case_start,
                            message=f"Executed {len(actions)} actions",
                            screenshot_path=shot.file_path if shot else None,
                            tags=["playwright", "ai", "generated"],
                        )
                    )
                except Exception as exc:
                    results.append(
                        TestResult(
                            test_id=test_id,
                            test_name=tc.name,
                            status="failed",
                            duration=time.time() - case_start,
                            error_details=str(exc),
                            tags=["playwright", "ai", "generated"],
                        )
                    )
            browser.close()
    except Exception as exc:
        results.append(
            TestResult(
                test_id="WEB_UI_001",
                test_name="Playwright session",
                status="error",
                duration=time.time() - ui_start,
                error_details=str(exc),
                tags=["web", "ui", "playwright"],
            )
        )

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Gemini + Playwright automated web tester")
    parser.add_argument("--url", required=True, help="Target URL")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout in seconds")
    parser.add_argument("--skip-browser", action="store_true", help="Run HTTP check only")
    parser.add_argument("--test-count", type=int, default=5, help="Number of AI test cases")
    args = parser.parse_args()

    target_url = args.url.strip()
    test_key = _safe_name_from_url(target_url)

    capture = ScreenshotCapture(
        base_path=Path(config.SCREENSHOTS_PATH),
        format=config.SCREENSHOT_FORMAT,
        quality=config.SCREENSHOT_QUALITY,
    )
    reporter = HTMLReporter(output_path=Path(config.REPORTS_PATH) / "html")

    results = [run_http_test(target_url, args.timeout)]
    if not args.skip_browser:
        results.extend(
            run_ai_website_flow(
                target_url,
                args.timeout,
                capture,
                test_key,
                args.test_count,
            )
        )

    report = reporter.generate(
        test_results=results,
        report_title=f"Gemini + Playwright Web Test - {target_url}",
        include_charts=False,
    )


    # Generate PDF report
    pdf_path = report.with_suffix('.pdf')
    pdf_success = generate_pdf_report(report, pdf_path)
    if pdf_success:
        print(f"PDF report generated: {pdf_path}")
    else:
        print("[WARN] PDF report not generated.")

    # Upload reports (HTML and PDF)
    upload_report(report)
    if pdf_success:
        upload_report(pdf_path)

    passed = sum(1 for item in results if item.status == "passed")
    failed = sum(1 for item in results if item.status in ("failed", "error"))
    print(f"URL: {target_url}")
    print(f"Passed: {passed} | Failed/Error: {failed} | Total: {len(results)}")
    print(f"Report: {report}")


if __name__ == "__main__":
    main()
