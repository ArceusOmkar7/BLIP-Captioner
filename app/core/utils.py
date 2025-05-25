import time
import os
from typing import List
import logging
import asyncio
from PIL import Image

from ..models.schemas import CaptionResponse
# Added remove_temp_file
from ..model import generate_caption_from_image, remove_temp_file

logger = logging.getLogger(__name__)


async def process_image_background(temp_path: str, filename: str, results: List[CaptionResponse], start_time: float):
    """
    Background task for processing a single image and cleaning up its temp file.

    Args:
        temp_path: Path to the temporary image file
        filename: Original filename of the image
        results: List to append results to
        start_time: Start time for processing time calculation
    """
    try:
        # Open image and generate caption
        image = Image.open(temp_path).convert("RGB")
        caption = generate_caption_from_image(image)

        # Calculate processing time
        processing_time = time.time() - start_time

        # Add result
        results.append(CaptionResponse(
            filename=filename,
            caption=caption,
            processing_time=processing_time
        ))

    except Exception as e:
        logger.error(
            f"Error in background processing for {filename}: {str(e)}")
    finally:
        # Ensure temporary file is removed after processing, whether successful or not
        if temp_path:
            remove_temp_file(temp_path)
            logger.info(f"Background task cleaned up temp file: {temp_path}")
