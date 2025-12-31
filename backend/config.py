"""
Configuration management for GoTo Call Automation System.

Loads configuration from environment variables and provides validation.
"""

import os
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # GoTo Connect API
    goto_api_key: str = Field(..., env="GOTO_API_KEY")
    goto_webhook_secret: str = Field(..., env="GOTO_WEBHOOK_SECRET")
    goto_api_base_url: str = Field(
        default="https://api.goto.com/v1",
        env="GOTO_API_BASE_URL"
    )

    # OpenAI API
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4-turbo-preview", env="OPENAI_MODEL")
    whisper_model: str = Field(default="whisper-1", env="WHISPER_MODEL")

    # Database
    database_url: str = Field(..., env="DATABASE_URL")
    db_pool_size: int = Field(default=10, env="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=20, env="DB_MAX_OVERFLOW")

    # Slack
    slack_webhook_url: Optional[str] = Field(default=None, env="SLACK_WEBHOOK_URL")
    slack_bot_token: Optional[str] = Field(default=None, env="SLACK_BOT_TOKEN")
    slack_channel: str = Field(default="#call-summaries", env="SLACK_CHANNEL")

    # Email
    smtp_host: Optional[str] = Field(default=None, env="SMTP_HOST")
    smtp_port: int = Field(default=587, env="SMTP_PORT")
    smtp_username: Optional[str] = Field(default=None, env="SMTP_USERNAME")
    smtp_password: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    smtp_from_email: Optional[str] = Field(default=None, env="SMTP_FROM_EMAIL")
    notification_email_recipients: list[str] = Field(
        default_factory=list,
        env="NOTIFICATION_EMAIL_RECIPIENTS"
    )

    # Application
    app_env: str = Field(default="development", env="APP_ENV")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")

    # Storage
    temp_dir: str = Field(default="/tmp/goto-automation", env="TEMP_DIR")
    max_audio_size_mb: int = Field(default=100, env="MAX_AUDIO_SIZE_MB")

    # Processing
    async_workers: int = Field(default=4, env="ASYNC_WORKERS")
    webhook_timeout_seconds: int = Field(default=30, env="WEBHOOK_TIMEOUT_SECONDS")

    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @field_validator("notification_email_recipients", mode='before')
    @classmethod
    def parse_email_recipients(cls, v) -> list[str]:
        """Parse comma-separated email recipients."""
        if isinstance(v, list):
            return v
        if not v or v == "":
            return []
        return [email.strip() for email in str(v).split(",") if email.strip()]

    @field_validator("log_level", mode='before')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v_upper

    @field_validator("temp_dir", mode='before')
    @classmethod
    def ensure_temp_dir(cls, v: str) -> str:
        """Ensure temp directory exists."""
        os.makedirs(v, exist_ok=True)
        return v

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app_env.lower() == "production"

    def has_slack_configured(self) -> bool:
        """Check if Slack is properly configured."""
        return bool(self.slack_webhook_url or self.slack_bot_token)

    def has_email_configured(self) -> bool:
        """Check if email is properly configured."""
        return all([
            self.smtp_host,
            self.smtp_username,
            self.smtp_password,
            self.smtp_from_email,
            self.notification_email_recipients
        ])


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get application settings singleton.

    Returns:
        Settings instance with all configuration loaded.

    Raises:
        ValidationError: If required environment variables are missing.
    """
    global _settings
    if _settings is None:
        _settings = Settings()
        logger.info(
            f"Settings loaded: env={_settings.app_env}, "
            f"log_level={_settings.log_level}"
        )
    return _settings


def configure_logging():
    """Configure application logging based on settings."""
    settings = get_settings()

    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Set third-party loggers to WARNING to reduce noise
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


if __name__ == "__main__":
    # Test configuration loading
    configure_logging()
    settings = get_settings()
    print(f"Configuration loaded successfully!")
    print(f"Environment: {settings.app_env}")
    print(f"Database: {settings.database_url[:20]}...")
    print(f"Slack configured: {settings.has_slack_configured()}")
    print(f"Email configured: {settings.has_email_configured()}")
