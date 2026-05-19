"""
config.py - Centralized configuration management for AI Testing System
Loads configuration from environment variables and .env file
"""

import os
from dotenv import load_dotenv
from pathlib import Path
from typing import Optional

# Load environment variables from Backend/.env
_env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=_env_path)

class Config:
    """Base configuration class"""
    
    # Project Paths
    PROJECT_ROOT = Path(__file__).parent.parent
    SRC_PATH = PROJECT_ROOT / "src"
    TEST_DATA_PATH = Path(os.getenv("TEST_DATA_PATH", PROJECT_ROOT / "test_data"))
    SCREENSHOTS_PATH = Path(os.getenv("SCREENSHOTS_PATH", TEST_DATA_PATH / "screenshots"))
    REPORTS_PATH = Path(os.getenv("REPORTS_PATH", PROJECT_ROOT / "reports"))
    TEST_CASES_PATH = TEST_DATA_PATH / "test_cases"
    TEST_RESULTS_PATH = TEST_DATA_PATH / "test_results"
    
    # AI Configuration
    # AI_MODEL = os.getenv("AI_MODEL", "gemini-2.5-flash")
    AI_MODEL = os.getenv("AI_MODEL", "gemini-2.5-flash")
    ANTHROPIC_API_KEY = ""
    OPENAI_API_KEY = ""
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    OLLAMA_HOST = "http://localhost:11434"
    OLLAMA_TIMEOUT = 600
    AI_PROVIDER = "gemini"
    AI_TEMPERATURE = 0.7
    AI_MAX_TOKENS = 5000
    
    # Database Configuration
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///test_results.db")
    DB_ECHO = os.getenv("DB_ECHO", "False").lower() == "true"
    DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", 10))
    DB_POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", 3600))
    
    # Testing Configuration
    BROWSER = os.getenv("BROWSER", "chrome").lower()  # chrome, firefox, safari, edge
    HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"
    TIMEOUT = int(os.getenv("TIMEOUT", 10))
    IMPLICIT_WAIT = int(os.getenv("IMPLICIT_WAIT", 5))
    EXPLICIT_WAIT = int(os.getenv("EXPLICIT_WAIT", 15))
    RETRY_COUNT = int(os.getenv("RETRY_COUNT", 3))
    RETRY_DELAY = int(os.getenv("RETRY_DELAY", 1))
    
    # Screenshot Configuration
    SCREENSHOT_FORMAT = os.getenv("SCREENSHOT_FORMAT", "png")  # png, jpg
    SCREENSHOT_QUALITY = int(os.getenv("SCREENSHOT_QUALITY", 95))
    AUTO_SCREENSHOT = os.getenv("AUTO_SCREENSHOT", "true").lower() == "true"
    COMPARE_THRESHOLD = float(os.getenv("COMPARE_THRESHOLD", 0.95))
    VISUAL_REGRESSION = os.getenv("VISUAL_REGRESSION", "true").lower() == "true"
    
    # Report Configuration
    GENERATE_HTML = os.getenv("GENERATE_HTML", "true").lower() == "true"
    GENERATE_PDF = os.getenv("GENERATE_PDF", "true").lower() == "true"
    GENERATE_MARKDOWN = os.getenv("GENERATE_MARKDOWN", "true").lower() == "true"
    INCLUDE_CHARTS = os.getenv("INCLUDE_CHARTS", "true").lower() == "true"
    INCLUDE_VIDEOS = os.getenv("INCLUDE_VIDEOS", "false").lower() == "true"
    REPORT_THEME = os.getenv("REPORT_THEME", "dark")  # dark, light
    
    # Performance Configuration
    PARALLEL_TESTS = int(os.getenv("PARALLEL_TESTS", 1))
    MAX_WORKERS = int(os.getenv("MAX_WORKERS", 4))
    SLOW_TEST_THRESHOLD = int(os.getenv("SLOW_TEST_THRESHOLD", 5))  # seconds
    
    # Logging Configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = Path(os.getenv("LOG_FILE", PROJECT_ROOT / "logs" / "app.log"))
    LOG_FORMAT = "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
    
    # Email Notification
    SEND_EMAIL_REPORTS = os.getenv("SEND_EMAIL_REPORTS", "false").lower() == "true"
    EMAIL_SMTP_SERVER = os.getenv("EMAIL_SMTP_SERVER", "smtp.gmail.com")
    EMAIL_SMTP_PORT = int(os.getenv("EMAIL_SMTP_PORT", 587))
    EMAIL_FROM = os.getenv("EMAIL_FROM", "")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
    EMAIL_TO = os.getenv("EMAIL_TO", "").split(",")
    
    # CI/CD Configuration
    CI_CD_PROVIDER = os.getenv("CI_CD_PROVIDER", "local")  # local, github, gitlab, jenkins
    WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
    
    # Feature Flags
    ENABLE_SELF_HEALING = os.getenv("ENABLE_SELF_HEALING", "true").lower() == "true"
    ENABLE_AI_ANALYSIS = os.getenv("ENABLE_AI_ANALYSIS", "true").lower() == "true"
    ENABLE_VIDEO_RECORDING = os.getenv("ENABLE_VIDEO_RECORDING", "false").lower() == "true"
    ENABLE_PERFORMANCE_METRICS = os.getenv("ENABLE_PERFORMANCE_METRICS", "true").lower() == "true"
    
    # API Endpoints (for testing)
    BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
    API_TIMEOUT = int(os.getenv("API_TIMEOUT", 30))
    
    # Proxy Configuration
    USE_PROXY = os.getenv("USE_PROXY", "false").lower() == "true"
    PROXY_URL = os.getenv("PROXY_URL", "")
    
    # Validation
    AUTH_TOKEN = os.getenv("AUTH_TOKEN", "")
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    
    # Create necessary directories
    @classmethod
    def create_directories(cls):
        """Create all necessary directories if they don't exist"""
        directories = [
            cls.TEST_DATA_PATH,
            cls.SCREENSHOTS_PATH,
            cls.SCREENSHOTS_PATH / "baseline",
            cls.SCREENSHOTS_PATH / "current",
            cls.SCREENSHOTS_PATH / "diffs",
            cls.REPORTS_PATH,
            cls.REPORTS_PATH / "html",
            cls.REPORTS_PATH / "pdf",
            cls.REPORTS_PATH / "markdown",
            cls.TEST_CASES_PATH,
            cls.TEST_RESULTS_PATH,
            cls.LOG_FILE.parent,
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)


class DevelopmentConfig(Config):
    """Development environment configuration"""
    DEBUG = True
    TESTING = False
    LOG_LEVEL = "DEBUG"
    HEADLESS = False
    DB_ECHO = True


class TestingConfig(Config):
    """Testing environment configuration"""
    DEBUG = True
    TESTING = True
    DATABASE_URL = "sqlite:///:memory:"
    HEADLESS = True
    PARALLEL_TESTS = 4
    RETRY_COUNT = 1


class ProductionConfig(Config):
    """Production environment configuration"""
    DEBUG = False
    TESTING = False
    LOG_LEVEL = "WARNING"
    HEADLESS = True
    RETRY_COUNT = 3
    # Production should use strong encryption and secure credentials
    SECURE_COOKIES = True
    SESSION_SECURE = True


# Configuration factory
def get_config(environment: Optional[str] = None) -> Config:
    """
    Get configuration based on environment
    
    Args:
        environment: Environment name (development, testing, production)
        
    Returns:
        Configuration object
    """
    if environment is None:
        environment = os.getenv("ENVIRONMENT", "development").lower()
    
    config_map = {
        "development": DevelopmentConfig,
        "testing": TestingConfig,
        "production": ProductionConfig,
    }
    
    config_class = config_map.get(environment, DevelopmentConfig)
    config_class.create_directories()
    return config_class()


# Default configuration instance
config = get_config()
