"""
Configuration management for the ChatGPT Account Creator Bot.
Loads settings from environment variables (.env file).
"""

import os
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()


class Config:
    # ------------------------------------------------------------------ #
    # OpenAI / ChatGPT                                                     #
    # ------------------------------------------------------------------ #
    SIGNUP_URL: str = os.getenv("SIGNUP_URL", "https://chat.openai.com/auth/login")
    API_URL: str = os.getenv("API_URL", "https://api.openai.com")

    # ------------------------------------------------------------------ #
    # Browser                                                              #
    # ------------------------------------------------------------------ #
    HEADLESS: bool = os.getenv("HEADLESS", "true").lower() != "false"
    SLOW_MO: int = int(os.getenv("SLOW_MO", "0"))
    TIMEOUT: int = int(os.getenv("TIMEOUT", "30000"))
    USER_AGENT: str = os.getenv(
        "USER_AGENT",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    )

    # ------------------------------------------------------------------ #
    # Proxy                                                                #
    # ------------------------------------------------------------------ #
    PROXY_ENABLED: bool = os.getenv("PROXY_ENABLED", "false").lower() == "true"
    PROXY_URL: str = os.getenv("PROXY_URL", "")
    PROXY_USERNAME: str = os.getenv("PROXY_USERNAME", "")
    PROXY_PASSWORD: str = os.getenv("PROXY_PASSWORD", "")

    # ------------------------------------------------------------------ #
    # Email                                                                #
    # ------------------------------------------------------------------ #
    EMAIL_PROVIDER: str = os.getenv("EMAIL_PROVIDER", "tempmail")  # tempmail | gmail | custom
    GMAIL_USERNAME: str = os.getenv("GMAIL_USERNAME", "")
    GMAIL_PASSWORD: str = os.getenv("GMAIL_PASSWORD", "")  # App-specific password
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_SECURE: bool = os.getenv("SMTP_SECURE", "false").lower() == "true"
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASS: str = os.getenv("SMTP_PASS", "")

    # ------------------------------------------------------------------ #
    # Database                                                             #
    # ------------------------------------------------------------------ #
    DB_PATH: str = os.getenv("DB_PATH", "./data/accounts.db")

    # ------------------------------------------------------------------ #
    # Rate limiting                                                        #
    # ------------------------------------------------------------------ #
    RATE_LIMIT_PER_DAY: int = int(os.getenv("RATE_LIMIT_PER_DAY", "5"))
    DELAY_BETWEEN: int = int(os.getenv("DELAY_BETWEEN", "60"))  # seconds

    # ------------------------------------------------------------------ #
    # Logging                                                              #
    # ------------------------------------------------------------------ #
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
    LOG_FILE: str = os.getenv("LOG_FILE", "./logs/app.log")

    # ------------------------------------------------------------------ #
    # API Server                                                           #
    # ------------------------------------------------------------------ #
    PORT: int = int(os.getenv("PORT", "3000"))
    HOST: str = os.getenv("HOST", "localhost")


config = Config()
