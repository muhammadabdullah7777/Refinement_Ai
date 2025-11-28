import logging
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    # DeepSeek API Configuration
    DEEPSEEK_API_KEY: str
    DEEPSEEK_API_URL: str = "https://api.deepseek.com/v1/chat/completions"
    
    # Moonshot API Configuration
    MOONSHOT_API_KEY: str
    MOONSHOT_API_URL: str = "https://api.moonshot.cn/v1/chat/completions"
    
    # Application Settings
    ENVIRONMENT: str = "development"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    
    # API Timeout Settings
    REQUEST_TIMEOUT: int = 30
    MAX_RETRIES: int = 3
    
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

# Create global settings instance
try:
    settings = Settings()
    logger.info("Settings loaded successfully.")
    # For debugging: print relevant settings (be cautious not to log sensitive keys in production)
    logger.info(f"DeepSeek URL: {settings.DEEPSEEK_API_URL}")
    logger.info(f"Moonshot URL: {settings.MOONSHOT_API_URL}")
except Exception as e:
    logger.error(f"Failed to load settings: {e}")
    logger.error("Ensure DEEPSEEK_API_KEY and MOONSHOT_API_KEY are set as environment variables.")
    raise # Re-raise to prevent application startup if essential settings are missing