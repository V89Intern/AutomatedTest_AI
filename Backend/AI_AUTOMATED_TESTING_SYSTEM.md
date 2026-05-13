# 🤖 AI-Powered Automated Testing System

## 📋 ภาพรวมระบบ

ระบบอัตโนมัติสำหรับการทดสอบซอฟต์แวร์ที่ใช้ AI ในการสร้าง Test Cases, ออกแบบการทดสอบ, บันทึกผลลัพธ์, และสร้างรายงานอัตโนมัติ

### ✨ คุณสมบัติหลัก

- **🧠 AI-Generated Test Cases** - ใช้ Claude/OpenAI เพื่อสร้าง Test Cases อัตโนมัติ
- **🎯 Multi-Platform Testing** - รองรับ Web, API, Mobile, Desktop Applications
- **📸 Auto Screenshot Management** - บันทึก Screenshot อัตโนมัติและจัดการเวอร์ชัน
- **📊 Smart Report Generation** - สร้างรายงานแบบ HTML, PDF, Markdown พร้อม Charts
- **🔄 CI/CD Integration** - รองรับ Jenkins, GitHub Actions, GitLab CI
- **📈 Test Result Analytics** - วิเคราะห์ผลการทดสอบ, Trend Analysis, Coverage Report
- **🛡️ Self-Healing Tests** - Auto-fix element locators ที่เปลี่ยนแปลง

---

## 🚀 ติดตั้งระบบ

### 1. Prerequisites
```bash
Python 3.10+
pip (Python package manager)
```

### 2. Clone และ Setup
```bash
# สร้างโฟลเดอร์โปรเจคต์
mkdir ai-testing-system
cd ai-testing-system

# สร้าง Virtual Environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# หรือ
venv\Scripts\activate  # Windows

# ติดตั้ง Dependencies
pip install -r requirements.txt
```

### 3. Configuration
```bash
# คัดลอก .env template
cp .env.example .env

# แก้ไข .env ด้วย API keys ของคุณ
# ANTHROPIC_API_KEY=sk-xxxxx
# OPENAI_API_KEY=sk-xxxxx
# DATABASE_URL=sqlite:///test_results.db
```

### 4. Initialize Database
```bash
python scripts/init_db.py
```

---

## 📁 Project Structure

```
ai-testing-system/
├── 📄 README.md                    (ไฟล์นี้)
├── 📋 SETUP_GUIDE.md              (คำแนะนำการติดตั้งโดยละเอียด)
├── 📚 QUICK_START.md              (เริ่มต้นใช้งาน 5 นาที)
│
├── requirements.txt               (Python Dependencies)
├── .env.example                   (Environment Template)
├── pyproject.toml                 (Project Config)
│
├── 📁 src/
│   ├── __init__.py
│   ├── 🤖 ai_engine/             (AI Integration)
│   │   ├── __init__.py
│   │   ├── test_generator.py      (Generate Test Cases)
│   │   ├── smart_locator.py       (Find elements intelligently)
│   │   └── report_analyzer.py     (Analyze test results)
│   │
│   ├── 🧪 test_frameworks/       (Testing Frameworks)
│   │   ├── __init__.py
│   │   ├── web_tester.py          (Web App Testing - Selenium/Playwright)
│   │   ├── api_tester.py          (REST/GraphQL API Testing)
│   │   ├── mobile_tester.py       (Mobile App Testing - Appium)
│   │   └── base_tester.py         (Base class for all testers)
│   │
│   ├── 📸 screenshot_manager/    (Screenshot Management)
│   │   ├── __init__.py
│   │   ├── capture.py             (Capture screenshots)
│   │   ├── compare.py             (Compare images for diff detection)
│   │   └── version_control.py     (Manage screenshot versions)
│   │
│   ├── 📊 report_generator/      (Report Generation)
│   │   ├── __init__.py
│   │   ├── html_reporter.py       (Generate HTML reports)
│   │   ├── pdf_reporter.py        (Generate PDF reports)
│   │   ├── markdown_reporter.py   (Generate Markdown reports)
│   │   └── chart_builder.py       (Create charts & visualizations)
│   │
│   ├── 🗄️ database/              (Data Persistence)
│   │   ├── __init__.py
│   │   ├── models.py              (SQLAlchemy models)
│   │   ├── repository.py          (Data access layer)
│   │   └── migrations.py          (DB schema migrations)
│   │
│   ├── ⚙️ config.py               (Configuration management)
│   ├── 🔐 auth.py                 (API authentication)
│   └── 🛠️ utils.py                (Utility functions)
│
├── 📁 examples/
│   ├── test_web_app.py            (Web testing example)
│   ├── test_api.py                (API testing example)
│   ├── test_mobile.py             (Mobile testing example)
│   └── generate_test_cases.py     (AI test generation example)
│
├── 📁 tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── 📁 test_data/
│   ├── test_cases/                (Generated test case files)
│   ├── screenshots/               (Captured screenshots)
│   │   ├── baseline/
│   │   ├── current/
│   │   └── diffs/
│   └── test_results/              (Test execution results)
│
├── 📁 reports/
│   ├── html/                      (HTML reports)
│   ├── pdf/                       (PDF reports)
│   └── markdown/                  (Markdown documentation)
│
├── 📁 ci_cd/
│   ├── jenkins_pipeline.groovy    (Jenkins pipeline)
│   ├── github_actions.yml         (GitHub Actions workflow)
│   ├── gitlab_ci.yml              (GitLab CI config)
│   └── docker-compose.yml         (Docker setup)
│
└── 📁 scripts/
    ├── init_db.py                 (Initialize database)
    ├── run_tests.py               (Run test suite)
    ├── generate_report.py         (Generate reports)
    └── cleanup.py                 (Clean up old data)
```

---

## 🎯 Quick Start (5 นาทีเริ่มต้น)

### 1️⃣ Generate AI Test Cases
```python
from src.ai_engine.test_generator import TestGenerator

generator = TestGenerator(model="claude-3.5-sonnet")
test_cases = generator.generate_from_description(
    description="Login page with email and password",
    test_count=10
)
```

### 2️⃣ Run Tests
```python
from src.test_frameworks.web_tester import WebTester

tester = WebTester(url="https://example.com")
results = tester.execute_tests(test_cases)
```

### 3️⃣ Capture Screenshots
```python
from src.screenshot_manager.capture import ScreenshotCapture

capture = ScreenshotCapture()
capture.take_screenshots(test_results)
capture.compare_with_baseline()
```

### 4️⃣ Generate Report
```python
from src.report_generator.html_reporter import HTMLReporter

reporter = HTMLReporter()
report = reporter.generate(
    test_results=results,
    screenshots=captures,
    include_charts=True
)
```

---

## 📚 Documentation Files

- **SETUP_GUIDE.md** - คำแนะนำติดตั้งเชิงลึก
- **QUICK_START.md** - เริ่มต้นใช้งาน 5 นาที
- **API_REFERENCE.md** - Reference สำหรับ API ทั้งหมด
- **EXAMPLES.md** - ตัวอย่าง Use Cases
- **TROUBLESHOOTING.md** - แก้ไขปัญหาทั่วไป
- **CI_CD_INTEGRATION.md** - ตั้งค่า Jenkins/GitHub Actions
- **BEST_PRACTICES.md** - Best practices สำหรับ automated testing

---

## 🔧 Configuration Files

### requirements.txt
```
selenium>=4.10.0
playwright>=1.35.0
pytest>=7.3.0
requests>=2.31.0
anthropic>=0.7.0
openai>=1.0.0
sqlalchemy>=2.0.0
pillow>=9.5.0
matplotlib>=3.7.0
pandas>=2.0.0
pydantic>=2.0.0
python-dotenv>=1.0.0
```

### .env.example
```
# AI Configuration
ANTHROPIC_API_KEY=your-api-key
OPENAI_API_KEY=your-api-key
AI_MODEL=claude-3.5-sonnet

# Database
DATABASE_URL=sqlite:///test_results.db

# Paths
SCREENSHOTS_PATH=./test_data/screenshots
REPORTS_PATH=./reports
TEST_DATA_PATH=./test_data

# Testing
BROWSER=chrome
HEADLESS=true
TIMEOUT=10
RETRY_COUNT=3

# Report
GENERATE_HTML=true
GENERATE_PDF=true
GENERATE_MARKDOWN=true
```

---

## 🚀 Running the System

### Run All Tests
```bash
python scripts/run_tests.py
```

### Generate Reports
```bash
python scripts/generate_report.py
```

### Run with Docker
```bash
docker-compose up
```

### Run via CI/CD
```bash
# GitHub Actions
git push

# Jenkins
curl -X POST http://jenkins-server/job/ai-testing/build

# GitLab CI
git push
```

---

## 📊 Example Output

### HTML Report
```html
AI Test Report - 2024-04-30
✅ Passed: 85/100 (85%)
⚠️  Flaky: 10/100 (10%)
❌ Failed: 5/100 (5%)
```

### Test Statistics
- Average Test Duration: 2.3s
- Total Coverage: 94%
- Performance Trend: ↑ +2% from previous run
- Regression: 0 new failures

---

## 💡 Key Features

### 🧠 AI Test Generation
- สร้าง test cases จาก user stories อัตโนมัติ
- Generate edge cases และ negative scenarios
- Self-learning from previous test failures

### 📸 Smart Screenshot Management
- Auto capture screenshots ระหว่าง test
- Visual regression detection
- Compare with baseline images
- Auto generate diff images

### 📊 Advanced Reporting
- Real-time test execution dashboard
- Historical trend analysis
- Coverage reports
- Performance metrics
- Screenshot comparisons
- Video recording support

### 🔄 CI/CD Integration
- Jenkins Pipeline support
- GitHub Actions workflows
- GitLab CI configuration
- Docker containerization

### 🛡️ Self-Healing
- Auto-fix broken selectors
- Element locator learning
- Shadow DOM support
- Dynamic content handling

---

## 🎓 Learning Resources

1. **Getting Started** → QUICK_START.md
2. **Setup Details** → SETUP_GUIDE.md
3. **API Reference** → API_REFERENCE.md
4. **Real Examples** → examples/ folder
5. **Best Practices** → BEST_PRACTICES.md
6. **Troubleshooting** → TROUBLESHOOTING.md

---

## 💬 Support & Contributing

- Report bugs: GitHub Issues
- Feature requests: GitHub Discussions
- Documentation: Wiki
- Community: Discord Channel

---

## 📄 License

MIT License - See LICENSE file

---

## 🎉 Next Steps

1. ✅ Read QUICK_START.md
2. ✅ Run the examples
3. ✅ Configure your environment
4. ✅ Generate your first AI test case
5. ✅ Execute and get reports
6. ✅ Integrate with CI/CD

Happy Testing! 🧪🚀

---

**Last Updated**: April 2024
**Version**: 1.0.0
**Maintained by**: AI Testing Team
