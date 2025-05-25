import logging
from pathlib import Path
import os
from pydantic_settings import BaseSettings
from typing import List, Union, Optional  # Added Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API metadata
API_TITLE = "BLIP Image Captioning Microservice"
API_DESCRIPTION = "Microservice for generating captions for images using the BLIP model. Works with images uploaded by the main backend."
API_VERSION = "1.0.0"

# CORS settings
CORS_ORIGINS = ["*"]  # In production, replace with specific origins
CORS_CREDENTIALS = True
CORS_METHODS = ["*"]
CORS_HEADERS = ["*"]


class AppSettings(BaseSettings):
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1
    RELOAD: bool = True
    LOG_LEVEL: str = "info"
    # Example for model configuration, can be expanded
    MODEL_NAME: str = "Salesforce/blip-image-captioning-large"
    # For local model path, ensure it's an absolute path or resolvable
    MODEL_PATH: Optional[str] = None

    # To load .env file, if you choose to use one
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = 'ignore'  # Add this to ignore extra fields from .env not defined in AppSettings


settings = AppSettings()

# Update logger to use LOG_LEVEL from settings
# Ensure this is done after settings are loaded.
# The basicConfig should ideally be called only once.
# If run.py also calls it, this might need adjustment or centralization.

# Clear existing handlers if any, to avoid duplicate logs if basicConfig is called multiple times.
# This is a common pattern but ensure it fits the overall logging strategy.
if logging.root.handlers:
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

# Configure logging with the level from settings
# Convert log level string to uppercase as logging module expects (e.g., "INFO", "DEBUG")
log_level_upper = settings.LOG_LEVEL.upper()
logging.basicConfig(level=log_level_upper)
logger = logging.getLogger(__name__)  # Re-initialize logger with new level

logger.info(
    f"Application settings loaded: HOST={settings.HOST}, PORT={settings.PORT}, LOG_LEVEL={log_level_upper}")
logger.info(f"Model to be used: {settings.MODEL_NAME}")
if settings.MODEL_PATH:
    logger.info(f"Custom model path specified: {settings.MODEL_PATH}")
