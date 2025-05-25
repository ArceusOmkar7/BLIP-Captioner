# Core package initialization
from .config import (
    logger,
    API_TITLE,
    API_DESCRIPTION,
    API_VERSION,
    CORS_ORIGINS,
    CORS_CREDENTIALS,
    CORS_METHODS,
    CORS_HEADERS
)
from .utils import process_image_background

__all__ = [
    "logger",
    "API_TITLE",
    "API_DESCRIPTION",
    "API_VERSION",
    "CORS_ORIGINS",
    "CORS_CREDENTIALS",
    "CORS_METHODS",
    "CORS_HEADERS",
    "process_image_background",
]
