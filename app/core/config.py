import logging
from pathlib import Path
import os

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
