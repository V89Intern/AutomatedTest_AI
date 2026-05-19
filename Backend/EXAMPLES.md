# 📖 Examples and Use Cases

## Table of Contents
1. [Basic Examples](#basic-examples)
2. [Web Testing Examples](#web-testing-examples)
3. [API Testing Examples](#api-testing-examples)
4. [Advanced Scenarios](#advanced-scenarios)
5. [Real-World Use Cases](#real-world-use-cases)

---

## Basic Examples

### Example 1: Generate Simple Test Cases

```python
#!/usr/bin/env python
"""Generate test cases for a login feature"""

from src.ai_engine.test_generator import TestGenerator
from pathlib import Path

# Initialize
generator = TestGenerator(
    model="claude-3.5-sonnet",
    ai_provider="anthropic"
)

# Generate test cases
test_cases = generator.generate_from_description(
    description="""
    Login Feature:
    - Email/password authentication
    - Remember me checkbox
    - Forgot password link
    - Form validation
    - Error messages
    - Rate limiting after 5 failed attempts
    """,
    test_count=15,
    include_edge_cases=True,
    include_negative_tests=True,
    priority="high",
    category="functional"
)

# Display results
print(f"Generated {len(test_cases)} test cases\n")
for test in test_cases[:5]:
    print(f"ID: {test.id}")
    print(f"Name: {test.name}")
    print(f"Priority: {test.priority}")
    print(f"Tags: {test.tags}")
    print(f"Steps: {len(test.steps)}")
    print()

# Save for later use
output_path = Path("test_data/test_cases/login_tests.json")
generator.save_test_cases(test_cases, output_path)
print(f"✅ Saved {len(test_cases)} test cases to {output_path}")
```

---

### Example 2: Generate from User Story

```python
#!/usr/bin/env python
"""Generate tests from agile user story"""

from src.ai_engine.test_generator import TestGenerator

generator = TestGenerator()

# Agile user story
test_cases = generator.generate_from_user_story(
    story="""
    As a customer
    I want to add items to my shopping cart
    So that I can purchase multiple products at once
    """,
    acceptance_criteria=[
        "User can add single or multiple items",
        "Item quantity can be updated",
        "Items can be removed from cart",
        "Cart total updates automatically",
        "Out of stock items show warning",
        "Session persists for 30 minutes",
        "Cart works without login (guest checkout)"
    ],
    test_count=12
)

print(f"Generated {len(test_cases)} test cases from user story")

# Categorize by type
functional_tests = [t for t in test_cases if t.category == "functional"]
regression_tests = [t for t in test_cases if t.category == "regression"]

print(f"Functional: {len(functional_tests)}")
print(f"Regression: {len(regression_tests)}")
```

---

### Example 3: Generate Edge Cases

```python
#!/usr/bin/env python
"""Generate edge case tests for payment processing"""

from src.ai_engine.test_generator import TestGenerator

generator = TestGenerator()

edge_cases = generator.generate_edge_cases(
    feature_description="""
    Payment Processing:
    - Credit card payment
    - Support Visa, Mastercard, Amex
    - CVV validation
    - Expiry date validation
    - Amount: $0.01 to $999,999.99
    """,
    test_count=10
)

# Display edge case examples
print("Edge Case Tests Generated:")
for test in edge_cases[:3]:
    print(f"\n{test.name}")
    print(f"Test Data: {test.test_data}")
    print(f"Expected: {test.expected_results}")
```

---

### Example 4: HTML Report Generation

```python
#!/usr/bin/env python
"""Generate comprehensive HTML test report"""

from src.report_generator.html_reporter import HTMLReporter, TestResult
from datetime import datetime
from pathlib import Path

# Create test results
results = [
    TestResult(
        test_id="TC_001",
        test_name="Login with valid credentials",
        status="passed",
        duration=2.3,
        tags=["login", "smoke", "functional"]
    ),
    TestResult(
        test_id="TC_002",
        test_name="Login with invalid password",
        status="failed",
        duration=3.1,
        error_details="Expected error message not shown\nActual: System returns 500 error",
        tags=["login", "negative"]
    ),
    TestResult(
        test_id="TC_003",
        test_name="Login rate limiting",
        status="passed",
        duration=5.2,
        tags=["login", "security"]
    ),
    TestResult(
        test_id="TC_004",
        test_name="Remember me functionality",
        status="passed",
        duration=2.8,
        tags=["login", "functional"]
    ),
    TestResult(
        test_id="TC_005",
        test_name="Forgot password flow",
        status="skipped",
        duration=0.0,
        message="Waiting for password reset email service",
        tags=["login", "recovery"]
    ),
]

# Generate report
reporter = HTMLReporter(output_path=Path("reports/html"))
report_path = reporter.generate(
    test_results=results,
    report_title="Login Feature Test Report - Sprint 12",
    include_charts=True
)

print(f"✅ Report generated: {report_path}")
print(f"📊 Results: {len([r for r in results if r.status == 'passed'])} passed, "
      f"{len([r for r in results if r.status == 'failed'])} failed")

# Open in browser (optional)
import webbrowser
webbrowser.open(f"file://{report_path.absolute()}")
```

---

## Web Testing Examples

### Example 5: Selenium with Screenshot Comparison

```python
#!/usr/bin/env python
"""Web testing with Selenium and screenshot comparison"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from src.screenshot_manager.capture import ScreenshotCapture
from pathlib import Path

# Initialize
driver = webdriver.Chrome()
capture = ScreenshotCapture(
    base_path=Path("test_data/screenshots"),
    format="png",
    quality=95
)

try:
    # Navigate
    driver.get("https://example.com/login")
    
    # Wait and interact
    email = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "email"))
    )
    email.send_keys("test@example.com")
    driver.find_element(By.ID, "password").send_keys("password123")
    
    # Capture screenshot
    screenshot = capture.capture_selenium(
        driver,
        test_name="login_page",
        test_id="TC_001",
        full_page=False
    )
    
    print(f"✅ Screenshot captured: {screenshot.filename}")
    
    # Compare with baseline
    is_match, similarity, diff_path = capture.compare_with_baseline(
        screenshot.file_path,
        "login_page",
        threshold=0.95
    )
    
    if is_match:
        print(f"✅ Visual regression test PASSED ({similarity:.2%})")
    else:
        print(f"❌ Visual regression test FAILED ({similarity:.2%})")
        print(f"Diff saved: {diff_path}")
    
    # Click submit
    driver.find_element(By.ID, "submit").click()
    
    # Capture result screen
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "dashboard"))
    )
    
    capture.capture_selenium(
        driver,
        test_name="dashboard_page",
        test_id="TC_001_success"
    )
    
finally:
    driver.quit()
```

---

### Example 6: Playwright with Multiple Screenshots

```python
#!/usr/bin/env python
"""Web testing with Playwright"""

from playwright.sync_api import sync_playwright
from src.screenshot_manager.capture import ScreenshotCapture
from pathlib import Path

capture = ScreenshotCapture()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    try:
        # Login flow
        page.goto("https://example.com/login")
        
        # Screenshot 1: Login page
        capture.capture_playwright(
            page,
            test_name="01_login_page",
            test_id="TC_LOGIN_001"
        )
        
        # Fill form
        page.fill("#email", "test@example.com")
        page.fill("#password", "password123")
        page.click("#submit")
        
        # Wait for navigation
        page.wait_for_selector(".dashboard")
        
        # Screenshot 2: Dashboard
        capture.capture_playwright(
            page,
            test_name="02_dashboard",
            test_id="TC_LOGIN_002",
            full_page=True
        )
        
        # Navigate to settings
        page.click("#settings-link")
        page.wait_for_selector(".settings-page")
        
        # Screenshot 3: Settings page
        capture.capture_playwright(
            page,
            test_name="03_settings_page",
            test_id="TC_LOGIN_003"
        )
        
        print("✅ All screenshots captured")
        
        # Update baselines
        updated = capture.update_all_baselines()
        print(f"✅ Updated {updated} baselines")
        
    finally:
        browser.close()
```

---

## API Testing Examples

### Example 7: REST API Testing

```python
#!/usr/bin/env python
"""REST API testing with test case generation"""

import requests
import json
from src.ai_engine.test_generator import TestGenerator

# Generate test cases for API
generator = TestGenerator()

test_cases = generator.generate_from_description(
    description="""
    REST API Endpoints:
    - GET /api/users/{id} - Retrieve user
    - POST /api/users - Create user
    - PUT /api/users/{id} - Update user
    - DELETE /api/users/{id} - Delete user
    - GET /api/users - List users with pagination
    
    Requirements:
    - Authentication required (Bearer token)
    - Rate limiting: 100 requests/minute
    - Validation: Email, phone format
    - Error codes: 400, 401, 403, 404, 500
    """,
    test_count=20
)

# Execute API tests
base_url = "http://localhost:8000/api"
headers = {"Authorization": "Bearer test-token"}

results = []
for test_case in test_cases[:5]:  # Run first 5 tests
    try:
        # Parse test data
        endpoint = test_case.test_data.get("endpoint", "/users")
        method = test_case.test_data.get("method", "GET")
        payload = test_case.test_data.get("payload", {})
        
        # Make request
        url = f"{base_url}{endpoint}"
        
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, json=payload, headers=headers)
        elif method == "PUT":
            response = requests.put(url, json=payload, headers=headers)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        
        # Check result
        expected_status = test_case.test_data.get("expected_status", 200)
        is_success = response.status_code == expected_status
        
        print(f"{'✅' if is_success else '❌'} {test_case.name}")
        print(f"  Status: {response.status_code} (expected {expected_status})")
        
    except Exception as e:
        print(f"❌ {test_case.name}")
        print(f"  Error: {str(e)}")
```

---

## Advanced Scenarios

### Example 8: Regression Testing from Bugs

```python
#!/usr/bin/env python
"""Generate regression tests from previous bugs"""

from src.ai_engine.test_generator import TestGenerator

generator = TestGenerator()

# Generate tests to prevent regression
regression_tests = generator.generate_regression_tests(
    feature_name="Payment Processing",
    previous_bugs=[
        "Bug #123: Payment fails when amount contains decimal point",
        "Bug #456: Currency conversion applies wrong rate",
        "Bug #789: Transaction timeout causes duplicate charges",
        "Bug #012: CVV validation bypassed with special characters"
    ],
    test_count=8
)

# These tests specifically target areas where bugs occurred
print(f"Generated {len(regression_tests)} regression prevention tests")

for test in regression_tests:
    print(f"\n{test.name}")
    print(f"Category: {test.category}")
    print(f"Test Data: {test.test_data}")
```

---

### Example 9: Multi-Browser Testing

```python
#!/usr/bin/env python
"""Run tests across multiple browsers"""

from selenium import webdriver
from src.screenshot_manager.capture import ScreenshotCapture
from pathlib import Path

# Test configuration
browsers = ["chrome", "firefox", "edge"]
test_url = "https://example.com"

capture = ScreenshotCapture()

results = {}

for browser_name in browsers:
    print(f"\n{'='*50}")
    print(f"Testing on {browser_name.upper()}")
    print(f"{'='*50}")
    
    try:
        if browser_name == "chrome":
            driver = webdriver.Chrome()
        elif browser_name == "firefox":
            driver = webdriver.Firefox()
        elif browser_name == "edge":
            driver = webdriver.Edge()
        
        # Navigate
        driver.get(test_url)
        
        # Capture screenshot
        screenshot = capture.capture_selenium(
            driver,
            test_name=f"{browser_name}_homepage",
            test_id=f"MULTI_BROWSER_{browser_name.upper()}"
        )
        
        # Compare with baseline
        is_match, similarity, _ = capture.compare_with_baseline(
            screenshot.file_path,
            f"{browser_name}_baseline",
            threshold=0.90  # Slightly lower for cross-browser
        )
        
        results[browser_name] = {
            "screenshot": screenshot.filename,
            "match": is_match,
            "similarity": f"{similarity:.2%}"
        }
        
        print(f"✅ {browser_name}: Captured - {screenshot.filename}")
        
        driver.quit()
        
    except Exception as e:
        print(f"❌ {browser_name}: {str(e)}")
        results[browser_name] = {"error": str(e)}

# Summary
print(f"\n{'='*50}")
print("Cross-Browser Testing Summary:")
print(f"{'='*50}")
for browser, result in results.items():
    if "error" not in result:
        status = "✅ PASS" if result["match"] else "❌ FAIL"
        print(f"{browser}: {status} ({result['similarity']})")
    else:
        print(f"{browser}: ❌ ERROR - {result['error']}")
```

---

## Real-World Use Cases

### Example 10: E-Commerce Purchase Flow Testing

```python
#!/usr/bin/env python
"""Complete e-commerce purchase flow test"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from src.ai_engine.test_generator import TestGenerator
from src.report_generator.html_reporter import HTMLReporter, TestResult
from src.screenshot_manager.capture import ScreenshotCapture
from pathlib import Path
import time

class EcommercePurchaseFlow:
    def __init__(self):
        self.driver = None
        self.capture = ScreenshotCapture()
        self.reporter = HTMLReporter()
        self.results = []
    
    def test_complete_purchase(self):
        """Test complete purchase flow"""
        self.driver = webdriver.Chrome()
        
        try:
            # Step 1: Browse products
            self._test_browse_products()
            
            # Step 2: Add to cart
            self._test_add_to_cart()
            
            # Step 3: Checkout
            self._test_checkout()
            
            # Step 4: Payment
            self._test_payment()
            
            # Step 5: Confirmation
            self._test_order_confirmation()
            
        finally:
            self.driver.quit()
    
    def _test_browse_products(self):
        """Test browsing products"""
        try:
            self.driver.get("https://example-store.com")
            
            # Wait for product list
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "product-card"))
            )
            
            # Capture screenshot
            self.capture.capture_selenium(
                self.driver,
                test_name="product_listing",
                test_id="ECOM_001"
            )
            
            self.results.append(TestResult(
                test_id="ECOM_001",
                test_name="Browse Products",
                status="passed",
                duration=2.5,
                tags=["ecommerce", "smoke"]
            ))
            print("✅ Browse Products: PASSED")
            
        except Exception as e:
            self.results.append(TestResult(
                test_id="ECOM_001",
                test_name="Browse Products",
                status="failed",
                duration=0.0,
                error_details=str(e),
                tags=["ecommerce", "smoke"]
            ))
            print(f"❌ Browse Products: FAILED - {str(e)}")
    
    def _test_add_to_cart(self):
        """Test adding items to cart"""
        try:
            # Click first product
            self.driver.find_element(By.CLASS_NAME, "product-card").click()
            
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "add-to-cart"))
            ).click()
            
            # Verify cart updated
            WebDriverWait(self.driver, 10).until(
                EC.text_to_be_present_in_element((By.CLASS_NAME, "cart-badge"), "1")
            )
            
            self.results.append(TestResult(
                test_id="ECOM_002",
                test_name="Add to Cart",
                status="passed",
                duration=1.8,
                tags=["ecommerce", "functional"]
            ))
            print("✅ Add to Cart: PASSED")
            
        except Exception as e:
            self.results.append(TestResult(
                test_id="ECOM_002",
                test_name="Add to Cart",
                status="failed",
                duration=0.0,
                error_details=str(e),
                tags=["ecommerce", "functional"]
            ))
            print(f"❌ Add to Cart: FAILED - {str(e)}")
    
    def _test_checkout(self):
        """Test checkout process"""
        try:
            # Open cart
            self.driver.find_element(By.CLASS_NAME, "cart-icon").click()
            
            # Click checkout
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "checkout-button"))
            ).click()
            
            # Wait for checkout page
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "checkout-form"))
            )
            
            self.results.append(TestResult(
                test_id="ECOM_003",
                test_name="Checkout",
                status="passed",
                duration=2.1,
                tags=["ecommerce", "functional"]
            ))
            print("✅ Checkout: PASSED")
            
        except Exception as e:
            self.results.append(TestResult(
                test_id="ECOM_003",
                test_name="Checkout",
                status="failed",
                duration=0.0,
                error_details=str(e),
                tags=["ecommerce", "functional"]
            ))
            print(f"❌ Checkout: FAILED - {str(e)}")
    
    def _test_payment(self):
        """Test payment processing"""
        try:
            # Fill payment details
            self.driver.find_element(By.ID, "card-number").send_keys("4111111111111111")
            self.driver.find_element(By.ID, "card-name").send_keys("Test User")
            
            # Process payment
            self.driver.find_element(By.ID, "pay-button").click()
            
            # Wait for success
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CLASS_NAME, "payment-success"))
            )
            
            self.results.append(TestResult(
                test_id="ECOM_004",
                test_name="Payment Processing",
                status="passed",
                duration=4.3,
                tags=["ecommerce", "payment"]
            ))
            print("✅ Payment Processing: PASSED")
            
        except Exception as e:
            self.results.append(TestResult(
                test_id="ECOM_004",
                test_name="Payment Processing",
                status="failed",
                duration=0.0,
                error_details=str(e),
                tags=["ecommerce", "payment"]
            ))
            print(f"❌ Payment Processing: FAILED - {str(e)}")
    
    def _test_order_confirmation(self):
        """Test order confirmation"""
        try:
            # Verify order number displayed
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "order-number"))
            )
            
            # Capture confirmation screen
            self.capture.capture_selenium(
                self.driver,
                test_name="order_confirmation",
                test_id="ECOM_005"
            )
            
            self.results.append(TestResult(
                test_id="ECOM_005",
                test_name="Order Confirmation",
                status="passed",
                duration=1.5,
                tags=["ecommerce", "functional"]
            ))
            print("✅ Order Confirmation: PASSED")
            
        except Exception as e:
            self.results.append(TestResult(
                test_id="ECOM_005",
                test_name="Order Confirmation",
                status="failed",
                duration=0.0,
                error_details=str(e),
                tags=["ecommerce", "functional"]
            ))
            print(f"❌ Order Confirmation: FAILED - {str(e)}")
    
    def generate_report(self):
        """Generate HTML report"""
        reporter = HTMLReporter()
        report_path = reporter.generate(
            test_results=self.results,
            report_title="E-Commerce Purchase Flow Test Report",
            include_charts=True
        )
        print(f"\n✅ Report generated: {report_path}")
        return report_path


# Run test
if __name__ == "__main__":
    flow = EcommercePurchaseFlow()
    flow.test_complete_purchase()
    flow.generate_report()
```

---

## Running These Examples

```bash
# Install dependencies
pip install selenium playwright anthropic pytest

# Download drivers
playwright install

# Set up environment
cp .env.example .env
# Edit .env with your API keys

# Run examples
python examples/example_1_generate_tests.py
python examples/example_5_selenium_screenshots.py
python examples/example_10_ecommerce_flow.py
```

---

**Version**: 1.0.0 | **Last Updated**: April 2024
