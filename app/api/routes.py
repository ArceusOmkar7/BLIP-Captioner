from fastapi import APIRouter, HTTPException, BackgroundTasks, File, UploadFile, Form
from fastapi.responses import FileResponse
from typing import List, Dict
import time
import os
from PIL import Image  # Required for image processing

from ..core.config import logger
# Updated schema imports
from ..models.schemas import CaptionResponse, BatchCaptionResponse
# Updated model imports
from ..model import generate_caption_from_image, save_upload_file_temp, remove_temp_file
# Keep for async batch if re-enabled
from ..core.utils import process_image_background

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint to verify API status."""
    return {"status": "healthy", "service": "BLIP Image Captioning API"}


@router.get("/")
async def root():
    """Serve the web interface for testing."""
    return FileResponse("static/index.html")


@router.post("/caption", response_model=CaptionResponse)
async def caption_image(image: UploadFile = File(...)):
    """
    Generate caption for a single image.
    Accepts an image file upload.

    Args:
        image: Uploaded image file

    Returns:
        CaptionResponse with generated caption

    Raises:
        HTTPException: If image processing fails
    """
    start_time = time.time()
    temp_path = None

    try:
        # Validate image file type
        if not image.content_type.startswith("image/"):
            raise HTTPException(
                status_code=400,
                detail=f"File must be an image, got {image.content_type}"
            )

        # Save image to a temporary file
        temp_path, filename = await save_upload_file_temp(image)

        # Process the image using PIL
        with Image.open(temp_path) as img_file:
            img = img_file.convert("RGB")  # Ensure RGB for model
            caption = generate_caption_from_image(img)

        # Calculate processing time
        processing_time = time.time() - start_time

        return CaptionResponse(
            filename=filename,  # Use filename from temp save
            caption=caption,
            processing_time=processing_time
        )

    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # Clean up the temporary file
        if temp_path:
            remove_temp_file(temp_path)


@router.post("/batch-caption", response_model=BatchCaptionResponse)
async def batch_caption_images(images: List[UploadFile] = File(...)):
    """
    Generate captions for multiple images.
    Accepts a list of image file uploads.

    Args:
        images: List of uploaded image files

    Returns:
        BatchCaptionResponse with results for all processed images

    Raises:
        HTTPException: If no valid images are processed or other errors occur
    """
    start_global_time = time.time()
    results = []
    failed_images: Dict[str, str] = {}
    temp_files_to_clean = []  # Keep track of temp files for cleanup

    try:
        for image_file in images:
            temp_path_single = None
            image_start_time = time.time()
            try:
                # Validate image file type
                if not image_file.content_type.startswith("image/"):
                    failed_images[
                        image_file.filename or "unknown_file"] = f"Not an image file: {image_file.content_type}"
                    continue  # Skip to the next file

                # Save image to a temporary file
                temp_path_single, filename = await save_upload_file_temp(image_file)
                temp_files_to_clean.append(temp_path_single)

                # Process the image using PIL
                with Image.open(temp_path_single) as img_file:
                    img = img_file.convert("RGB")  # Ensure RGB for model
                    caption = generate_caption_from_image(img)

                # Calculate processing time for this image
                processing_time_single = time.time() - image_start_time

                results.append(CaptionResponse(
                    filename=filename,
                    caption=caption,
                    processing_time=processing_time_single
                ))

            except Exception as e_single:
                error_msg = str(e_single)
                logger.error(
                    f"Error processing image {image_file.filename or 'unknown_file'}: {error_msg}")
                failed_images[image_file.filename or "unknown_file"] = error_msg
                # If temp_path_single was created before error, it will be cleaned in finally

        # Calculate total processing time for the batch
        total_processing_time = time.time() - start_global_time

        # If no images were successfully processed, raise an error
        if not results and failed_images:
            raise HTTPException(
                status_code=400,
                detail=f"No images were successfully processed. Errors: {failed_images}"
            )
        elif not results:
            raise HTTPException(
                status_code=400,
                detail="No images provided or all failed silently before processing."
            )

        # Create response object
        response = BatchCaptionResponse(
            results=results,
            total_processing_time=total_processing_time
        )

        # Add failed images information to the response if any (as an extra attribute)
        if failed_images:
            setattr(response, "failed_images", failed_images)

        return response

    finally:
        # Clean up all temporary files created during the batch processing
        for temp_file_path in temp_files_to_clean:
            remove_temp_file(temp_file_path)


@router.post("/async-batch-caption", response_model=BatchCaptionResponse)
async def async_batch_caption_images(images: List[UploadFile] = File(...), background_tasks: BackgroundTasks = None):
    """
    Process multiple images asynchronously using background tasks.
    Accepts a list of image file uploads.

    Args:
        images: List of uploaded image files
        background_tasks: FastAPI background tasks handler

    Returns:
        Initial BatchCaptionResponse (may be empty or partial, results populated by background tasks)
        A more descriptive message about background processing initiation.
    """
    start_global_time = time.time()
    results_list_for_bg = []  # This list will be populated by background tasks
    failed_images_bg: Dict[str, str] = {}
    # Temp files will be managed by the background task itself
    temp_files_managed_by_bg = []
    processed_count = 0

    if not background_tasks:
        raise HTTPException(
            status_code=500, detail="BackgroundTasks handler not available.")

    for image_file in images:
        try:
            if not image_file.content_type.startswith("image/"):
                failed_images_bg[
                    image_file.filename or "unknown_file"] = f"Not an image file: {image_file.content_type}"
                continue

            # Save temp file; path will be passed to background task for its management
            temp_path_bg, filename_bg = await save_upload_file_temp(image_file)
            # temp_files_managed_by_bg.append(temp_path_bg) # No longer needed here, bg task handles its own temp file

            background_tasks.add_task(
                process_image_background,
                temp_path_bg,  # Pass temp path to bg task
                filename_bg,
                results_list_for_bg,
                # Use global start for consistent timing if needed, or pass individual start
                start_global_time
            )
            processed_count += 1

        except Exception as e_setup:
            logger.error(
                f"Error setting up background task for {image_file.filename or 'unknown_file'}: {str(e_setup)}")
            failed_images_bg[
                image_file.filename or "unknown_file"] = f"Setup error: {str(e_setup)}"
            # If temp file was created before error in setup, it might need cleanup here
            # However, save_upload_file_temp is robust; if it fails, no temp file path is returned.

    if processed_count == 0 and not failed_images_bg:
        raise HTTPException(
            status_code=400, detail="No valid image files provided for async processing.")

    # Immediate response indicating tasks are scheduled
    # Note: `results_list_for_bg` will be empty here as tasks run in background.
    # The actual results would need to be fetched via another mechanism (e.g., polling, websockets)
    # For this example, we return an initial response.

    response_message = f"{processed_count} image(s) scheduled for background captioning."
    if failed_images_bg:
        response_message += f" Failed to schedule: {len(failed_images_bg)} image(s). Details: {failed_images_bg}"

    # This response is more of an acknowledgement
    # A real-world scenario might return a task ID to check status
    return {
        "message": response_message,
        "scheduled_count": processed_count,
        "failed_to_schedule": failed_images_bg,
        "initial_results": [],  # results_list_for_bg will be populated by background tasks
        "total_processing_time": 0  # This would be updated upon completion
    }

# Note: The original /async-batch-caption endpoint was complex due to background tasks.
# The provided update simplifies its immediate response, highlighting that actual results
# from background tasks need a separate retrieval mechanism not covered here.
# The `process_image_background` in utils.py would need to handle its own temp file removal.
