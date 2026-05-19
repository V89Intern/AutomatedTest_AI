# 🚀 Quick Start - 5 Minutes to Your First Test

## ⚡ Super Fast Setup

### Step 1: Clone & Setup (2 minutes)
```bash
# Create project
mkdir ai-testing-system && cd ai-testing-system

# Create virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install anthropic pytest selenium pillow loguru jinja2 matplotlib

# Create structure
mkdir -p src/{ai_engine,screenshot_manager,report_generator} test_data reports/{html,pdf}
touch .env
```

### Step 2: Configure (1 minute)
Create `.env` file:
```
ANTHROPIC_API_KEY=your-api-key-here
AI_MODEL=claude-3.5-sonnet
HEADLESS=true
```

### Step 3: Copy Code Files (1 minute)
Copy these Python files to `src/`:
- `config.py` → `src/config.py`
- `ai_engine_test_generator.py` → `src/ai_engine/test_generator.py`
- `screenshot_manager_capture.py` → `src/screenshot_manager/capture.py`
- `report_generator_html.py` → `src/report_generator/html_reporter.py`

### Step 4: Run! (1 minute)

```bash
# Create and run example
cat > test_example.py << 'EOF'
#!/usr/bin/env python
"""Quick test example"""

import sys
sys.path.insert(0, '.')

# 1. Generate AI Test Cases
print("🤖 Generating AI test cases...")
from src.ai_engine.test_generator import TestGenerator

generator = TestGenerator(model="claude-3.5-sonnet", ai_provider="anthropic")
test_cases = generator.generate_from_description(
    description="Login page with email and password",
    test_count=3
)

print(f"✅ Generated {len(test_cases)} test cases:")
for tc in test_cases[:3]:
    print(f"  - {tc.name} [{tc.priority}]")

# 2. Generate HTML Report
print("\n📊 Generating test report...")
from src.report_generator.html_reporter import HTMLReporter, TestResult

results = [
    TestResult(test_id="TC_001", test_name="Login Valid", status="passed", duration=2.5, tags=["login"]),
    TestResult(test_id="TC_002", test_name="Login Invalid", status="failed", duration=3.1, tags=["login"]),
]

reporter = HTMLReporter()
report_path = reporter.generate(results, "Quick Start Report")
print(f"✅ Report saved: {report_path}")

print("\n🎉 Done! Check the reports/ directory for your HTML report")
EOF

python test_example.py
```

---

## 📚 What You Can Do Now

### 1. Generate Test Cases from Feature Description
```python
from src.ai_engine.test_generator import TestGenerator

generator = TestGenerator()
tests = generator.generate_from_description(
    "Shopping cart with add/remove items",
    test_count=10
)

# Access test details
for test in tests:
    print(f"Test: {test.name}")
    print(f"Steps: {test.steps}")
    print(f"Expected: {test.expected_results}")
```

### 2. Generate from User Story
```python
tests = generator.generate_from_user_story(
    story="As a user, I want to login with my email",
    acceptance_criteria=[
        "System should validate email format",
        "System should validate password strength",
        "System should show error for invalid credentials"
    ]
)
```

### 3. Generate Edge Cases
```python
edge_cases = generator.generate_edge_cases(
    feature_description="Payment form with credit card",
    test_count=5
)
```

### 4. Create HTML Report
```python
from src.report_generator.html_reporter import HTMLReporter, TestResult

results = [
    TestResult(
        test_id="TC_001",
        test_name="Login Test",
        status="passed",
        duration=2.5,
        tags=["login", "smoke"]
    ),
]

reporter = HTMLReporter()
report = reporter.generate(results, "My Report")
# Opens in browser → reports/html/test_report_YYYYMMDD_HHMMSS.html
```

### 5. Save & Load Test Cases
```python
from pathlib import Path

# Save
generator.save_test_cases(test_cases, Path("test_data/my_tests.json"))

# Load
loaded = generator.load_test_cases(Path("test_data/my_tests.json"))
```

---

## 🎯 Common Patterns

### Pattern 1: Full Test Generation & Reporting
```python
from src.ai_engine.test_generator import TestGenerator
from src.report_generator.html_reporter import HTMLReporter, TestResult

# Generate tests
generator = TestGenerator()
test_cases = generator.generate_from_description("Your feature", test_count=10)

# Simulate test results
results = [
    TestResult(
        test_id=tc.id,
        test_name=tc.name,
        status="passed" if i % 3 != 0 else "failed",
        duration=2.5 + i * 0.5,
        tags=tc.tags
    )
    for i, tc in enumerate(test_cases)
]

# Generate report
reporter = HTMLReporter()
reporter.generate(results, "Full Test Report")
```

### Pattern 2: Generate & Save for Later
```python
# Generate once
tests = generator.generate_from_description("Feature", test_count=20)

# Save to file
generator.save_test_cases(tests, Path("test_data/feature_tests.json"))

# Use later in test execution
from pathlib import Path
tests = generator.load_test_cases(Path("test_data/feature_tests.json"))
```

### Pattern 3: Regression Testing
```python
# Generate from previous bugs
tests = generator.generate_regression_tests(
    feature_name="Payment Processing",
    previous_bugs=[
        "Bug #123: Payment fails with special characters",
        "Bug #456: Discount not applied correctly"
    ],
    test_count=5
)
```

---

## 🔧 API Quick Reference

### TestGenerator Methods

| Method | Purpose | Example |
|--------|---------|---------|
| `generate_from_description()` | Create tests from feature description | `generator.generate_from_description("Login", 10)` |
| `generate_from_user_story()` | Create tests from user story & criteria | `generator.generate_from_user_story("As a user...", [...])` |
| `generate_regression_tests()` | Create tests from previous bugs | `generator.generate_regression_tests("Feature", [...])` |
| `generate_edge_cases()` | Create edge case tests | `generator.generate_edge_cases("Feature", 5)` |
| `optimize_test_cases()` | Optimize existing tests | `generator.optimize_test_cases(tests)` |
| `save_test_cases()` | Save to JSON file | `generator.save_test_cases(tests, Path(...))` |
| `load_test_cases()` | Load from JSON file | `generator.load_test_cases(Path(...))` |

### HTMLReporter Methods

| Method | Purpose | Example |
|--------|---------|---------|
| `generate()` | Create HTML report | `reporter.generate(results, "Title")` |

---

## 📊 Output Examples

### Generated Test Case
```json
{
  "id": "TC_001",
  "name": "Login with valid email and password",
  "description": "User should be able to login with valid credentials",
  "preconditions": ["User is on login page", "User has valid account"],
  "steps": [
    "Enter email: user@example.com",
    "Enter password: SecurePass123",
    "Click Login button",
    "Wait for dashboard to load"
  ],
  "expected_results": [
    "Login successful",
    "User redirected to dashboard",
    "User session is created"
  ],
  "test_data": {
    "email": "user@example.com",
    "password": "SecurePass123"
  },
  "priority": "high",
  "category": "functional",
  "tags": ["login", "smoke"]
}
```

### HTML Report
```
Generated at: reports/html/test_report_20240430_143022.html

Opens in browser with:
✅ 15 Passed (75%)
❌ 3 Failed (15%)
⏭️ 2 Skipped (10%)

Interactive charts, expandable test details, screenshots
```

---

## 🆘 Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: No module named 'anthropic'` | Run: `pip install anthropic` |
| `API key error` | Check `.env` file has `ANTHROPIC_API_KEY` |
| `No module found 'src'` | Run from project root, check folder structure |
| `ModuleNotFoundError: No module named 'loguru'` | Run: `pip install loguru` |

---

## 🎓 Learn More

- **Detailed Setup**: See `SETUP_GUIDE.md`
- **Full API Reference**: See `API_REFERENCE.md`
- **Best Practices**: See `BEST_PRACTICES.md`
- **Examples**: Check `examples/` folder

---

## 💡 What's Next?

1. ✅ Run your first test
2. ✅ Generate test cases for your feature
3. ✅ Create your first report
4. ✅ Integrate with Selenium/Playwright
5. ✅ Set up CI/CD pipeline
6. ✅ Enable screenshot comparison
7. ✅ Add email notifications

---

## 🚀 Ready?

```bash
# One-liner to get started
python test_example.py
```

Happy Testing! 🧪✨

---

**Version**: 1.0.0 | **Last Updated**: April 2024
