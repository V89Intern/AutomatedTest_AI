# 📚 AI-Powered Automated Testing System - Setup Guide

## 📖 Table of Contents
1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Database Setup](#database-setup)
5. [Running Examples](#running-examples)
6. [Troubleshooting](#troubleshooting)

---

## ✅ Prerequisites

### System Requirements
- **Python**: 3.10 or higher
- **OS**: Windows, macOS, or Linux
- **RAM**: Minimum 4GB (8GB recommended)
- **Disk Space**: 2GB minimum

### Required Software
```bash
# Check Python version
python --version  # Should be 3.10+

# Check pip is installed
pip --version
```

### Optional but Recommended
- Git for version control
- Docker for containerization
- Docker Compose for orchestration

---

## 🚀 Installation Steps

### 1. Clone/Create Project
```bash
# Create project directory
mkdir ai-testing-system
cd ai-testing-system

# Initialize Git (optional)
git init
git config user.email "your@email.com"
git config user.name "Your Name"
```

### 2. Create Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate

# Verify activation (you should see (venv) in terminal)
```

### 3. Install Dependencies
```bash
# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# Verify installation
pip list
```

### 4. Directory Structure Setup
```bash
# Create project structure
mkdir -p src/{ai_engine,test_frameworks,screenshot_manager,report_generator,database,utils}
mkdir -p test_data/{test_cases,screenshots/{baseline,current,diffs},test_results}
mkdir -p reports/{html,pdf,markdown}
mkdir -p ci_cd
mkdir -p scripts
mkdir -p examples
mkdir -p tests/{unit,integration,e2e}
mkdir -p logs
```

### 5. Copy Configuration Files
```bash
# Copy example environment file
cp .env.example .env

# Create project root __init__ files
touch src/__init__.py
touch examples/__init__.py
touch tests/__init__.py
```

---

## ⚙️ Configuration

### Environment Variables (.env)

Create `.env` file in project root:

```bash
# AI Configuration
ANTHROPIC_API_KEY=your-anthropic-api-key-here
OPENAI_API_KEY=your-openai-api-key-here
AI_MODEL=claude-3.5-sonnet
AI_PROVIDER=anthropic  # or openai, ollama
AI_TEMPERATURE=0.7
AI_MAX_TOKENS=2000

# Database Configuration
DATABASE_URL=sqlite:///test_results.db
# For PostgreSQL: postgresql://user:password@localhost/dbname
DB_ECHO=false
DB_POOL_SIZE=10

# Testing Configuration
BROWSER=chrome  # chrome, firefox, safari, edge
HEADLESS=true
TIMEOUT=10
IMPLICIT_WAIT=5
EXPLICIT_WAIT=15
RETRY_COUNT=3
RETRY_DELAY=1

# Screenshot Configuration
SCREENSHOT_FORMAT=png  # png or jpg
SCREENSHOT_QUALITY=95
AUTO_SCREENSHOT=true
COMPARE_THRESHOLD=0.95
VISUAL_REGRESSION=true

# Report Configuration
GENERATE_HTML=true
GENERATE_PDF=true
GENERATE_MARKDOWN=true
INCLUDE_CHARTS=true
REPORT_THEME=dark  # dark or light

# Paths (relative to project root)
TEST_DATA_PATH=./test_data
SCREENSHOTS_PATH=./test_data/screenshots
REPORTS_PATH=./reports
LOG_FILE=./logs/app.log

# Performance
PARALLEL_TESTS=1
MAX_WORKERS=4
SLOW_TEST_THRESHOLD=5

# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Email Notifications (optional)
SEND_EMAIL_REPORTS=false
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_FROM=your-email@gmail.com
EMAIL_PASSWORD=your-app-password

# Base URL for testing
BASE_URL=http://localhost:8000
API_TIMEOUT=30

# Feature Flags
ENABLE_SELF_HEALING=true
ENABLE_AI_ANALYSIS=true
ENABLE_VIDEO_RECORDING=false
ENABLE_PERFORMANCE_METRICS=true

# Environment
ENVIRONMENT=development  # development, testing, production
```

### API Key Setup

#### For Anthropic (Claude)
1. Go to https://console.anthropic.com
2. Sign up or log in
3. Navigate to API Keys section
4. Create new API key
5. Copy and paste in `.env`: `ANTHROPIC_API_KEY=your-key`

#### For OpenAI (ChatGPT)
1. Go to https://platform.openai.com
2. Sign up or log in
3. Navigate to API Keys
4. Create new API key
5. Copy and paste in `.env`: `OPENAI_API_KEY=your-key`

---

## 🗄️ Database Setup

### SQLite (Default - No Setup Required)
SQLite is included with Python, no additional setup needed.

### PostgreSQL (Optional - Production)

#### Install PostgreSQL
```bash
# macOS
brew install postgresql
brew services start postgresql

# Windows
# Download from https://www.postgresql.org/download/windows/

# Linux (Ubuntu)
sudo apt-get install postgresql postgresql-contrib
sudo service postgresql start
```

#### Create Database
```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE ai_testing;
CREATE USER tester WITH PASSWORD 'secure_password';
ALTER ROLE tester SET client_encoding TO 'utf8';
ALTER ROLE tester SET default_transaction_isolation TO 'read committed';
ALTER ROLE tester SET default_transaction_deferrable TO on;
ALTER ROLE tester SET default_transaction_level TO 'read committed';
GRANT ALL PRIVILEGES ON DATABASE ai_testing TO tester;
\q

# Update .env
DATABASE_URL=postgresql://tester:secure_password@localhost/ai_testing
```

### Initialize Database
```bash
# Run database initialization
python scripts/init_db.py

# Output should show:
# ✅ Database initialized successfully
# ✅ Tables created
# ✅ Ready to use
```

---

## 📦 Browser Drivers Setup

### Chrome/Chromium
```bash
# For Selenium - Install webdriver-manager
pip install webdriver-manager

# For Playwright
playwright install chromium
```

### Firefox
```bash
# For Selenium
pip install webdriver-manager

# For Playwright
playwright install firefox
```

### Safari (macOS only)
```bash
# For Selenium
pip install webdriver-manager

# For Playwright
playwright install webkit
```

---

## 🔧 Running Examples

### Example 1: Generate AI Test Cases
```bash
# Create example file
cat > examples/01_generate_tests.py << 'EOF'
#!/usr/bin/env python
"""Example: Generate test cases using AI"""

import sys
sys.path.insert(0, '.')

from src.ai_engine.test_generator import TestGenerator
from pathlib import Path

# Initialize generator
generator = TestGenerator(
    model="claude-3.5-sonnet",
    ai_provider="anthropic"
)

# Generate test cases from description
test_cases = generator.generate_from_description(
    description="User login page with email and password fields",
    test_count=5,
    include_edge_cases=True,
    include_negative_tests=True
)

# Display results
print(f"Generated {len(test_cases)} test cases:\n")
for tc in test_cases:
    print(f"ID: {tc.id}")
    print(f"Name: {tc.name}")
    print(f"Priority: {tc.priority}")
    print(f"Steps: {len(tc.steps)}")
    print("-" * 50)

# Save test cases
output_path = Path("test_data/test_cases/generated_tests.json")
generator.save_test_cases(test_cases, output_path)
print(f"\n✅ Test cases saved to {output_path}")
EOF

# Run it
python examples/01_generate_tests.py
```

### Example 2: Capture Screenshots
```bash
# Create example file
cat > examples/02_capture_screenshots.py << 'EOF'
#!/usr/bin/env python
"""Example: Capture and compare screenshots"""

import sys
sys.path.insert(0, '.')

from src.screenshot_manager.capture import ScreenshotCapture
from pathlib import Path

# Initialize capture
capture = ScreenshotCapture(
    base_path=Path("test_data/screenshots"),
    format="png",
    quality=95
)

# This example shows how to use it with Selenium
# (actual usage requires a WebDriver instance)
print("✅ ScreenshotCapture initialized")
print(f"Baseline path: {capture.baseline_path}")
print(f"Current path: {capture.current_path}")
print(f"Diffs path: {capture.diffs_path}")
EOF

python examples/02_capture_screenshots.py
```

### Example 3: Generate HTML Report
```bash
# Create example file
cat > examples/03_generate_report.py << 'EOF'
#!/usr/bin/env python
"""Example: Generate HTML test report"""

import sys
sys.path.insert(0, '.')

from src.report_generator.html_reporter import HTMLReporter, TestResult
from pathlib import Path

# Create sample test results
results = [
    TestResult(
        test_id="TC_001",
        test_name="Login with valid credentials",
        status="passed",
        duration=2.5,
        tags=["login", "functional"]
    ),
    TestResult(
        test_id="TC_002",
        test_name="Login with invalid password",
        status="failed",
        duration=3.2,
        error_details="Expected error message not displayed",
        tags=["login", "negative"]
    ),
    TestResult(
        test_id="TC_003",
        test_name="Login with empty fields",
        status="passed",
        duration=1.8,
        tags=["login", "validation"]
    ),
]

# Generate report
reporter = HTMLReporter(output_path=Path("reports/html"))
report_path = reporter.generate(
    test_results=results,
    report_title="Sample Test Report",
    include_charts=True
)

print(f"✅ Report generated: {report_path}")
EOF

python examples/03_generate_report.py
```

---

## ✅ Verification

After installation, verify everything works:

```bash
# 1. Check Python version
python --version

# 2. Check virtual environment
which python  # Should show venv path

# 3. Check installed packages
pip list | grep -E 'pytest|selenium|anthropic|openai'

# 4. Check directories
ls -la src/
ls -la test_data/
ls -la reports/

# 5. Test imports
python -c "from pathlib import Path; print('✅ Path works')"
python -c "from loguru import logger; print('✅ Loguru works')"
python -c "import pytest; print('✅ Pytest works')"

# 6. Run examples
python examples/01_generate_tests.py
python examples/02_capture_screenshots.py
python examples/03_generate_report.py
```

---

## 🐛 Troubleshooting

### Issue: ModuleNotFoundError
```bash
# Solution: Ensure virtual environment is activated
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate      # Windows
```

### Issue: API Key not working
```bash
# Solution 1: Check .env file exists and has correct key
cat .env | grep API_KEY

# Solution 2: Reload environment
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('ANTHROPIC_API_KEY'))"

# Solution 3: Verify API key on provider's website
```

### Issue: Database connection error
```bash
# Solution 1: Check database URL in .env
cat .env | grep DATABASE_URL

# Solution 2: For SQLite, check file permissions
ls -la test_results.db

# Solution 3: For PostgreSQL, verify connection
psql -U postgres -h localhost -d ai_testing
```

### Issue: Chrome/Firefox driver not found
```bash
# Solution: Install webdriver-manager or playwright drivers
pip install webdriver-manager
playwright install

# Or set up manually:
# Download from chromedriver.chromium.org
# Add to PATH or specify in config
```

### Issue: Requirements installation fails
```bash
# Solution 1: Upgrade pip
pip install --upgrade pip setuptools wheel

# Solution 2: Install one by one
pip install pytest
pip install selenium
pip install anthropic
# ... etc

# Solution 3: Check Python version compatibility
python --version  # Need 3.10+
```

---

## 🎯 Next Steps

1. ✅ Complete installation
2. ✅ Run examples
3. ✅ Read QUICK_START.md
4. ✅ Check API_REFERENCE.md
5. ✅ Review BEST_PRACTICES.md
6. ✅ Set up CI/CD integration
7. ✅ Start writing your tests!

---

## 📞 Support

For issues or questions:
1. Check TROUBLESHOOTING.md
2. Review example files in `examples/` directory
3. Check logs in `logs/` directory
4. Consult provider documentation:
   - Anthropic: https://docs.anthropic.com
   - OpenAI: https://platform.openai.com/docs

---

**Version**: 1.0.0  
**Last Updated**: April 2024  
**Created by**: AI Testing Team
