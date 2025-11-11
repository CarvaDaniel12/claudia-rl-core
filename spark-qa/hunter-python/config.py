"""
Hunter Python Configuration
Loads from .env file
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env
load_dotenv()

class Config:
    """Global configuration"""

    # Environment first (determines which credentials to use)
    ENVIRONMENT = os.getenv("ENVIRONMENT", "staging")  # Default: staging

    # Hostfully UI - Adaptive based on environment
    # Use class variable to check environment
    _env = os.getenv("ENVIRONMENT", "staging")
    EMAIL = os.getenv("HOSTFULLY_EMAIL",
                      "Daniel+sandbox@hostfully.com" if _env == "sandbox"
                      else "daniel+pmp@hostfully.com")  # staging default (PMP account!)
    PASSWORD = os.getenv("HOSTFULLY_PASSWORD", "pas123")

    # Environment URLs
    SANDBOX_URL = os.getenv("SANDBOX_URL", "https://sandbox.hostfully.com")
    AUTOMATION_V3_URL = os.getenv("AUTOMATION_V3_URL", "https://automation-v3.test.hostfully.com")
    STAGING_URL = os.getenv("STAGING_URL", "https://platform.test.hostfully.com")

    # API v3 - STAGING (UI + API mesma base!)
    API_BASE_URL = os.getenv("HOSTFULLY_API_BASE", "https://platform.test.hostfully.com/v3")
    API_KEY = os.getenv("HOSTFULLY_API_KEY", "CK4R0jGYEoNgdIXy")
    JWT_TOKEN = os.getenv("HOSTFULLY_JWT_TOKEN", "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3NjIxMDI0MjcsImV4cCI6MTc2MjE4ODgyNywiaXNzIjoiaG9zdGZ1bGx5UG1wIiwiYWN0IjoicHUiLCJzdWIiOiI4ODEwYWEyOS1iYWVmLTQwNmItODA3OS1mMWI4Y2M2MWIxYWIiLCJzdWlkIjoiMDU4NDAwOGEtYzcyYy00MjkyLTgwOGYtZGE2MDc0MTczNDMzIiwidXNlclVpZCI6Ijg4MTBhYTI5LWJhZWYtNDA2Yi04MDc5LWYxYjhjYzYxYjFhYiIsInVzZXJUeXBlIjoiRU1QTE9ZRUUiLCJpc3UiOmZhbHNlLCJ1YXMiOlsicG1wIiwiZ2JmIl19.M4WL3t6qpOJcgVxMathRmM2rT5AtMtnI942Z9YsIzyVpGPwCvqRBlO1YpN97P5jqjAVhc2LNvtJT9vrzrAgNCDgx5tQtu07HmUj8MaCvA7AUf_5GCuqqWoHKnX9pbm2tWCHVrz6JEnQu7MFPLHmekWt7zyt-aKEx9YXBuru-fLiMVdNCGdWhV2F4RL41eKuTFEtJa0PCbHul5iYQy327AwE4QpbR0oE5S8WVzP46W1rMzfgZYpbigg9ExwiBsyjxbFsWa_cdDiSZQZI5XUePRYouFpB-X3e7QsqXROyDaq_7N9KfP1B-cJloO3-6-Bo2OUvZgcTNGFt1RyRIaRUs7g")
    AGENCY_UID = os.getenv("HOSTFULLY_AGENCY_UID", "090f20e9-f60d-4398-8eac-6951169654b1")

    @property
    def BASE_URL(self):
        if self.ENVIRONMENT == "sandbox":
            return self.SANDBOX_URL
        elif self.ENVIRONMENT == "automation-v3":
            return self.AUTOMATION_V3_URL
        else:
            return self.STAGING_URL

    # Execution
    HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"
    PARALLEL_BROWSERS = int(os.getenv("PARALLEL_BROWSERS", "5"))
    TIMEOUT_MS = int(os.getenv("TIMEOUT_MS", "30000"))

    # Cleanup (NOW WORKING - search method!)
    ENABLE_CLEANUP = os.getenv("ENABLE_CLEANUP", "true").lower() == "true"

    # Storage
    BASE_DIR = Path(__file__).parent.parent
    RESULTS_DIR = BASE_DIR / "barril!!"
    SCREENSHOTS_DIR = RESULTS_DIR / "screenshots"
    LOGS_DIR = RESULTS_DIR / "logs"

    def __init__(self):
        # Create directories
        self.RESULTS_DIR.mkdir(exist_ok=True)
        self.SCREENSHOTS_DIR.mkdir(exist_ok=True)
        self.LOGS_DIR.mkdir(exist_ok=True)

# Singleton
config = Config()

