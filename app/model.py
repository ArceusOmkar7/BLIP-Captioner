"""
BLIP Image Captioning Model
--------------------------
This module provides functionality for generating captions for images using the BLIP model.
It handles model loading, image processing, and caption generation.
"""

from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image
import torch
import logging
import os
import tempfile
from fastapi import UploadFile
import asyncio  # Added for async operations
from typing import List, Tuple, Dict, Any  # Added for type hinting
from .core.tags_extractor import extract_noun_phrases

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set device (GPU if available, otherwise CPU)
device = "cuda" if torch.cuda.is_available() else "cpu"
logger.info(f"Using device: {device}")

# Load model and processor at module import time
try:
    from .core.config import settings
    model_name = settings.MODEL_NAME

    logger.info(f"Loading BLIP model at startup: {model_name}")

    # Initialize the BLIP processor for image preprocessing with use_fast=True
    processor = BlipProcessor.from_pretrained(
        model_name,
        use_fast=True
    )

    # Initialize the BLIP model for caption generation
    model = BlipForConditionalGeneration.from_pretrained(
        model_name
    ).to(device)

    logger.info("BLIP model and processor loaded successfully at startup")
except Exception as e:
    logger.error(f"Error loading BLIP model at startup: {str(e)}")
    raise


def generate_caption_from_image(image: Image.Image) -> str:
    """
    Generate a caption for a PIL Image object using the BLIP model.

    Args:
        image (PIL.Image.Image): PIL Image object

    Returns:
        str: Generated caption describing the image    Raises:
        ValueError: If the image is invalid or can\'t be processed
        Exception: For other unexpected errors
    """
    try:
        # Ensure image is in RGB format
        if image.mode != "RGB":
            image = image.convert("RGB")

        # Preprocess image for the BLIP model
        inputs = processor(images=image, return_tensors="pt").to(device)

        # Generate caption
        output = model.generate(**inputs)

        # Decode the generated tokens into text
        caption = processor.decode(output[0], skip_special_tokens=True)

        logger.info(f"Generated caption: {caption}")
        return caption

    except Exception as e:
        logger.error(f"Error generating caption: {str(e)}")
        raise


def generate_caption_and_tags_from_image(image: Image.Image) -> Dict[str, Any]:
    """
    Generate both caption and tags for a PIL Image object using the BLIP model and NLP processing.

    Args:
        image (PIL.Image.Image): PIL Image object

    Returns:
        Dict[str, Any]: Dictionary containing 'caption' and 'tags' keys

    Raises:
        ValueError: If the image is invalid or can\'t be processed
        Exception: For other unexpected errors
    """
    try:
        # Generate caption first
        caption = generate_caption_from_image(image)

        # Extract tags from the caption
        tags = extract_noun_phrases(caption)

        logger.info(f"Generated caption: {caption}")
        logger.info(f"Extracted {len(tags)} tags: {tags}")

        return {
            "caption": caption,
            "tags": tags
        }

    except Exception as e:
        logger.error(f"Error generating caption and tags: {str(e)}")
        raise


async def save_upload_file_temp(upload_file: UploadFile) -> Tuple[str, str]:
    """
    Save an uploaded file to a temporary location.

    Args:
        upload_file (UploadFile): FastAPI UploadFile object

    Returns:
        Tuple[str, str]: Tuple containing temporary file path and original filename

    Raises:
        Exception: If saving the file fails
    """
    try:
        # Create a temporary file with appropriate extension
        suffix = os.path.splitext(upload_file.filename)[
            1] if upload_file.filename else ".jpg"  # Default to .jpg if no filename
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
            # Write content
            content = await upload_file.read()
            temp.write(content)
            temp_path = temp.name

        logger.info(f"Saved uploaded file temporarily to {temp_path}")
        # Return filename or base path
        return temp_path, upload_file.filename or os.path.basename(temp_path)

    except Exception as e:
        logger.error(f"Failed to save uploaded file: {e}")
        raise


def remove_temp_file(file_path: str) -> None:
    """
    Remove a temporary file.

    Args:
        file_path (str): Path to the temporary file
    """
    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
            logger.info(f"Removed temporary file: {file_path}")
    except Exception as e:
        logger.warning(f"Error removing temporary file {file_path}: {e}")


def generate_caption(image_path: str) -> str:
    """
    Generate a caption for an image using the BLIP model.

    This function is maintained for backward compatibility but now uses the
    image object-based caption generation.

    Args:
        image_path (str): Path to the image file

    Returns:
        str: Generated caption describing the image

    Raises:
        FileNotFoundError: If the image file doesn\'t exist
        ValueError: If the image file is invalid or can\'t be processed
        Exception: For other unexpected errors
    """
    try:
        # Load and convert image to RGB format
        image = Image.open(image_path).convert("RGB")

        # Use the shared implementation
        return generate_caption_from_image(image)

    except FileNotFoundError:
        logger.error(f"Image file not found: {image_path}")
        raise
    except Exception as e:
        logger.error(f"Error generating caption for {image_path}: {str(e)}")
        raise
