"""
BLIP Image Captioning Microservice
---------------------------------
This FastAPI application provides endpoints for generating captions for images using the BLIP model.
It is designed to work as a microservice that processes images that have been uploaded
to the main backend service. Images are sent to this service in either batch or single and processed to return caption.
"""

import uvicorn
from .api import create_app
from .core.config import settings, logger  # Import settings and logger

# Create the FastAPI application
app = create_app()

if __name__ == "__main__":
    # This block is typically for direct execution of main.py (e.g., python app/main.py)
    # It's often better to use run.py or uvicorn command directly for more control.
    # Using settings from config for consistency if run directly.
    logger.info(
        f"Running directly from app/main.py on {settings.HOST}:{settings.PORT}")
    uvicorn.run(app, host=settings.HOST, port=settings.PORT,
                reload=settings.RELOAD, log_level=settings.LOG_LEVEL.lower())
