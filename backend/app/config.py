"""Application configuration loaded from environment variables."""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Central configuration — never hardcode secrets."""

    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini")
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

    WEATHER_BASE_URL: str = os.getenv(
        "WEATHER_BASE_URL", "https://api.open-meteo.com/v1/forecast"
    )
    GEOCODING_BASE_URL: str = os.getenv(
        "GEOCODING_BASE_URL", "https://geocoding-api.open-meteo.com/v1/search"
    )

    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./weather_bot.db")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Timeouts for external API calls (seconds)
    API_TIMEOUT: int = int(os.getenv("API_TIMEOUT", "10"))

    # Max message length accepted from the user
    MAX_MESSAGE_LENGTH: int = int(os.getenv("MAX_MESSAGE_LENGTH", "2000"))


settings = Settings()
