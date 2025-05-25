"""
BLIP Image Captioning Microservice
---------------------------------
This FastAPI application provides endpoints for generating captions for images using the BLIP model.
It is designed to work as a microservice that processes images that have been uploaded
to the main backend service. This service does not handle file uploads directly but
instead processes images based on their paths.
"""

import uvicorn
from .api import create_app

# Create the FastAPI application
app = create_app()

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
