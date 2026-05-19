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
""" """FiveGi ผมเพิ่ม crawl มาของgoogle ช่วยเรียกดูเว็บและเช็คจากนั้นก็แก้การทำซ้ำการถ่ายภาพซ้ำหรือการเข้าหน้าเดิม และเพิ่มเวลาการtimeout ให้รอANIMETION ของเว็บแสดง ไฟล์รายงานให้บอทอธิบายแล้วดูได้ครับ """
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
        try:
            page.goto(url, wait_until="networkidle", timeout=timeout * 1000)
        except Exception:
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=timeout * 1000)
            except Exception as e:
                browser.close()
                return {"url": url, "error": str(e), "title": "", "top_elements": [], "internal_links": []}
        page.wait_for_timeout(2000)
        context = _snapshot_page(page)
        browser.close()
        return context


def _snapshot_page(page) -> Dict[str, Any]:
    return page.evaluate(
        r"""
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

          const internalLinks = Array.from(document.querySelectorAll('a[href]'))
            .map(a => a.href)
            .filter(h => h.startsWith(location.origin) && !h.includes('#') && h !== location.href)
            .slice(0, 20);

          return {
            title: document.title || '',
            url: location.href,
            forms: document.querySelectorAll('form').length,
            buttons: document.querySelectorAll('button, input[type="submit"], [role="button"]').length,
            links: document.querySelectorAll('a[href]').length,
            inputs: document.querySelectorAll('input, textarea, select').length,
            top_elements: top,
            internal_links: internalLinks,
          };
        }
        """
    )


def _norm_url(u: str) -> str:
    return u.rstrip("/").split("?")[0].split("#")[0]


def _crawl_site(url: str, timeout: int, max_pages: int = 10, crawl_all: bool = False) -> List[Dict[str, Any]]:
    """ crawl_all=True จะเก็บทุกหน้าที่พบ (จำกัดที่ 100 หน้าเพื่อความปลอดภัย) """
    if sync_playwright is None:
        return []

    hard_limit = 100 if crawl_all else max_pages
    queued: set = {_norm_url(url)}   # ป้องกัน URL เข้า queue ซ้ำ
    crawled: set = set()             # ป้องกัน snapshot ซ้ำ (รวม redirect)
    queue: List[str] = [url]
    contexts: List[Dict[str, Any]] = []
    label = "all" if crawl_all else str(max_pages)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        while queue and len(contexts) < hard_limit:
            current_url = queue.pop(0)
            try:
                page.goto(current_url, wait_until="networkidle", timeout=timeout * 1000)
                page.wait_for_timeout(1500)

                final_url = page.url
                norm_final = _norm_url(final_url)

                # ถ้า มาหน้าที่ snapshot ไปแล้วจะข้ามไปเลย  ก็ประมาณเช็คURL
                if norm_final in crawled:
                    continue
                crawled.add(norm_final)

                ctx = _snapshot_page(page)
                ctx["url"] = final_url
                contexts.append(ctx)
                print(f"[CRAWL] {len(contexts)}/{label} — {ctx.get('title', '')} | {final_url}")

                for link in ctx.get("internal_links", []):
                    norm_link = _norm_url(link)
                    if norm_link not in queued:
                        queued.add(norm_link)
                        queue.append(link)
            except Exception as e:
                print(f"[CRAWL] skip {current_url}: {e}")

        browser.close()

    print(f"[CRAWL] เสร็จสิ้น: พบ {len(contexts)} หน้า")
    return contexts


def _generate_website_cases(generator: TestGenerator, base_url: str, page_contexts: List[Dict[str, Any]], test_count: int) -> List[TestCase]:
    """ยิง Gemini ครั้งเดียวโดยรวม context ทุกหน้าไว้ในครั้งเดียว"""
    pages_summary = ""
    for i, ctx in enumerate(page_contexts, 1):
        elements = ctx.get("top_elements", [])[:30]
        pages_summary += f"""
--- PAGE {i}: {ctx.get("title", "")} ---
URL: {ctx.get("url", base_url)}
Elements: {json.dumps(elements, ensure_ascii=False)}
"""

    prompt = f"""
Generate {test_count} website test cases covering ALL pages below.
Base URL: {base_url}

PAGES FOUND:
{pages_summary}

STRICT SELECTOR RULES:
1) Use text-based selectors from element text in the list:
   "a:has-text('About')", "button:has-text('Submit')", "text=Contact"
2) Use tag+attribute only when text is empty:
   "a[href='/contact']", "input[name='email']", "input[type='submit']"
3) NEVER use class selectors (.nav-link, .btn) — unstable.
4) NEVER invent selectors not in the element lists above.
5) Each test must start with a goto action to its target page URL.

ACTION TYPES: goto, click, fill, press, wait, assert_url_contains, assert_text_visible, assert_element_visible
- click/fill/assert_element_visible → "selector" field
- goto/assert_url_contains/assert_text_visible → "value" field
- wait → "value" in milliseconds

Distribute test cases across all {len(page_contexts)} pages. Keep 3-6 actions per test. Return JSON array only.
"""

    return generator.generate_from_description(
        description=prompt,
        test_count=test_count,
        include_edge_cases=False,
        include_negative_tests=False,
        priority="high",
        category="functional",
    )


def _validate_test_cases(page, url: str, test_cases: List[TestCase], timeout_ms: int) -> List[TestCase]:
    """ตรวจ selector ของแต่ละ test case กับหน้าเว็บจริง — ตัดออกถ้าหาไม่เจอ"""
    valid_cases = []
    for tc in test_cases:
        actions = (tc.test_data or {}).get("actions", [])
        valid_actions = []
        try:
            page.goto(url, wait_until="networkidle", timeout=timeout_ms)
            page.wait_for_timeout(1500)
        except Exception:
            return test_cases  # ถ้าเปิดหน้าไม่ได้ ข้ามการตรวจ

        for action in actions:
            atype = str(action.get("type", "")).strip().lower()
            selector = action.get("selector")
            value = action.get("value")

            if atype in ("goto", "wait", "press"):
                valid_actions.append(action)
            elif atype in ("click", "fill", "assert_element_visible") and selector:
                try:
                    count = page.locator(str(selector)).count()
                    if count > 0:
                        valid_actions.append(action)
                except Exception:
                    pass
            elif atype == "assert_text_visible" and value:
                try:
                    count = page.get_by_text(str(value), exact=False).count()
                    if count > 0:
                        valid_actions.append(action)
                except Exception:
                    pass
            elif atype == "assert_url_contains" and value:
                valid_actions.append(action)

        if len(valid_actions) >= 2:
            tc.test_data["actions"] = valid_actions
            valid_cases.append(tc)

    return valid_cases if valid_cases else test_cases


def _run_action(page, action: Dict[str, Any], timeout_ms: int) -> None:
    action_type = str(action.get("type", "")).strip().lower()
    selector = action.get("selector")
    value = action.get("value")

    if action_type == "goto":
        page.goto(str(value), wait_until="networkidle", timeout=timeout_ms)
        # scroll ลงแล้วกลับขึ้น เพื่อ trigger scroll-animation ทั้งหมด
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(800)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(500)
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
    reuse_cases: bool = False,
    max_pages: int = 5,
    crawl_all: bool = False,
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
    page_contexts = _crawl_site(url, timeout, max_pages=max_pages, crawl_all=crawl_all)
    if not page_contexts:
        page_contexts = [_collect_page_context(url, timeout)]
    results.append(
        TestResult(
            test_id="AI_CTX_001",
            test_name="Collect page context",
            status="passed" if page_contexts else "failed",
            duration=time.time() - context_start,
            message=f"Crawled {len(page_contexts)} pages",
            tags=["ai", "context", "discovery"],
        )
    )

    ai_start = time.time()
    saved_path = Path(config.TEST_CASES_PATH) / "gemini_web_generated_cases.json"
    gen_error = None
    if reuse_cases and saved_path.exists():
        test_cases = generator.load_test_cases(saved_path)
        gen_message = f"Reused {len(test_cases)} saved test cases"
    else:
        try:
            test_cases = _generate_website_cases(generator, url, page_contexts, test_count=test_count)
            generator.save_test_cases(test_cases, saved_path)
            gen_message = f"Generated {len(test_cases)} test cases from {len(page_contexts)} pages"
        except Exception as e:
            gen_error = str(e).split("\n")[0]
            test_cases = []
            gen_message = f"AI generation failed: {gen_error}"
            print(f"[ERROR] Gemini failed — {gen_error}")
            print("[INFO] รันใหม่อีกครั้ง หรือใช้ --reuse-cases ถ้ามีชุดเก่าอยู่")
    results.append(
        TestResult(
            test_id="AI_GEN_001",
            test_name="Gemini generate website test cases",
            status="passed" if test_cases else "failed",
            duration=time.time() - ai_start,
            message=gen_message,
            error_details=gen_error,
            tags=["ai", "gemini", "generation"],
        )
    )
    if not test_cases:
        return results

    ui_start = time.time()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=config.HEADLESS)
            val_page = browser.new_page()
            test_cases = _validate_test_cases(val_page, url, test_cases, timeout * 1000)
            val_page.close()

            # Phase 1: รัน AI tests — track หน้าที่ screenshot สำเร็จจริงๆ
            snapped_pages: set = set()
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

                page = browser.new_page()
                try:
                    for action in actions:
                        _run_action(page, action, timeout * 1000)

                    final_norm = _norm_url(page.url)
                    if final_norm not in snapped_pages:
                        shot = capture.capture_playwright(page, test_name=f"{test_key}_tc_{i}", test_id=test_id, full_page=True)
                        snapped_pages.add(final_norm)
                    else:
                        shot = None
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
                            error_details=str(exc).split("\n")[0],
                            tags=["playwright", "ai", "generated"],
                        )
                    )
                finally:
                    page.close()

            # Phase 2: SNAP_ เฉพาะหน้าที่ยังไม่ได้ถ่ายจริงๆหรือขาดไม่ได้ถ่ายมา
            snap_i = len(test_cases) + 1
            for idx, ctx in enumerate(page_contexts, start=1):
                page_url = ctx.get("url", url)
                if _norm_url(page_url) in snapped_pages:
                    continue
                case_start = time.time()
                snap_id = f"SNAP_{idx:03d}"
                page = browser.new_page()
                try:
                    page.goto(page_url, wait_until="networkidle", timeout=timeout * 1000)
                    page.wait_for_timeout(1000)
                    shot = capture.capture_playwright(page, test_name=f"{test_key}_tc_{snap_i}", test_id=snap_id, full_page=True)
                    snapped_pages.add(_norm_url(page.url))
                    results.append(
                        TestResult(
                            test_id=snap_id,
                            test_name=f"Page snapshot: {ctx.get('title', page_url)}",
                            status="passed",
                            duration=time.time() - case_start,
                            message=f"Auto screenshot of {page_url}",
                            screenshot_path=shot.file_path if shot else None,
                            tags=["snapshot", "guaranteed"],
                        )
                    )
                except Exception as exc:
                    results.append(
                        TestResult(
                            test_id=snap_id,
                            test_name=f"Page snapshot: {ctx.get('title', page_url)}",
                            status="failed",
                            duration=time.time() - case_start,
                            error_details=str(exc).split("\n")[0],
                            tags=["snapshot", "guaranteed"],
                        )
                    )
                finally:
                    page.close()
                snap_i += 1

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
    parser.add_argument("--test-count", type=int, default=10, help="Number of AI test cases")
    parser.add_argument("--reuse-cases", action="store_true", help="Reuse last saved test cases (skip AI generation)")
    parser.add_argument("--max-pages", type=int, default=10, help="Max pages to crawl (default 10)")
    parser.add_argument("--crawl-all", action="store_true", default=True, help="Crawl all internal pages (up to 100)")
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
                reuse_cases=args.reuse_cases,
                max_pages=args.max_pages,
                crawl_all=args.crawl_all,
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
