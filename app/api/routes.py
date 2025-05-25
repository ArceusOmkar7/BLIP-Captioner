from fastapi import APIRouter, HTTPException, BackgroundTasks, File, UploadFile, Form, Request
from fastapi.responses import FileResponse
from typing import List, Dict
import time
import os
from PIL import Image  # Required for image processing

from ..core.config import logger
# Updated schema imports
from ..models.schemas import (
    CaptionResponse,
    BatchCaptionResponse,
    ImageCaptionResult,
    AsyncTaskStatus,
    TaskStatus,
    AsyncBatchCaptionResponse
)
# Updated model imports
from ..model import generate_caption_from_image, save_upload_file_temp, remove_temp_file
# Keep for async batch if re-enabled
from ..core.utils import process_image_background

router = APIRouter()

# In-memory storage for task statuses and results
# In a production environment, consider using a more persistent store like Redis or a database.
task_store: Dict[str, AsyncTaskStatus] = {}


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

    for image_file in images:
        temp_path_single = None
        image_start_time = time.time()
        filename = image_file.filename or f"unknown_image_{int(time.time())}"
        try:
            # Validate image file type
            if not image_file.content_type or not image_file.content_type.startswith("image/"):
                failed_images[
                    filename] = f"Not an image file or unknown content type: {image_file.content_type}"
                results.append(ImageCaptionResult(
                    image_path=filename, error=failed_images[filename]))
                continue

            # Save image to a temporary file
            # actual_filename might differ if sanitized
            temp_path_single, actual_filename = await save_upload_file_temp(image_file)
            temp_files_to_clean.append(temp_path_single)

            # Process the image using PIL
            with Image.open(temp_path_single) as img_file:
                img = img_file.convert("RGB")  # Ensure RGB for model
                caption = generate_caption_from_image(img)

            # Calculate processing time for this image
            processing_time_single = time.time() - image_start_time

            results.append(ImageCaptionResult(
                image_path=actual_filename,  # Use the actual filename from save_upload_file_temp
                caption=caption
            ))
            logger.info(
                f"Successfully captioned {actual_filename} in {processing_time_single:.2f}s")

        except Exception as e_single:
            error_msg = str(e_single)
            logger.error(f"Error processing image {filename}: {error_msg}")
            failed_images[filename] = error_msg
            results.append(ImageCaptionResult(
                image_path=filename, error=error_msg))
            # If temp_path_single was created before error, it will be cleaned in finally
        finally:
            # Ensure it's added if error occurred before append
            if temp_path_single and temp_path_single not in temp_files_to_clean:
                if os.path.exists(temp_path_single):  # only add if it exists
                    temp_files_to_clean.append(temp_path_single)

    # Calculate total processing time for the batch
    total_processing_time = time.time() - start_global_time
    logger.info(
        f"Batch captioning completed in {total_processing_time:.2f}s. Success: {len(results) - len(failed_images)}, Failed: {len(failed_images)}")

    # Create response object
    response = BatchCaptionResponse(
        results=results,
        total_processing_time=total_processing_time,
        # failed_images=failed_images # No longer a direct field in BatchCaptionResponse, errors are in ImageCaptionResult
    )

    # If no images were successfully processed, but some attempts were made
    if not any(r.caption for r in results) and results:
        # This condition might need refinement based on how you want to report partial vs total failure
        logger.warning("No images were successfully captioned in the batch.")
        # The response will naturally contain the errors per image.

    elif not results:  # No images were provided or all failed very early
        logger.error(
            "No images provided or all failed before any processing attempt.")
        raise HTTPException(
            status_code=400,
            detail="No images provided or all failed silently before processing."
        )

    return response


async def process_batch_images_async(task_id: str, prepared_files: List[Dict[str, str]], initial_results: List[ImageCaptionResult]):
    """
    Background task to process a batch of pre-saved images asynchronously.
    Updates the task_store with status and results.
    `prepared_files` contains dicts like: {"path": "/tmp/xyz", "original_name": "foo.jpg"}
    `initial_results` contains ImageCaptionResult for files that failed pre-processing.
    """
    if task_id not in task_store:
        logger.error(
            f"Task {task_id} not found in task_store at start of background processing. Aborting.")
        return

    task_store[task_id].status = TaskStatus.PROCESSING
    task_store[task_id].message = f"Processing {len(prepared_files)} images..."
    logger.info(
        f"Task {task_id}: Starting background processing for {len(prepared_files)} images.")

    # Combine initial_results (from pre-processing failures) with new results
    final_results: List[ImageCaptionResult] = list(initial_results)

    for file_info in prepared_files:
        temp_path_single = file_info["path"]
        original_filename = file_info["original_name"]
        # saved_filename = file_info.get("saved_name") # Actual name on disk, if needed for detailed logging

        try:
            # File is already saved at temp_path_single.
            with Image.open(temp_path_single) as img_file:
                img = img_file.convert("RGB")
                caption = generate_caption_from_image(img)
            final_results.append(ImageCaptionResult(
                image_path=original_filename, caption=caption))
            logger.info(
                f"Task {task_id}: Successfully captioned {original_filename} (from path: {temp_path_single})")

        except Exception as e:
            error_msg = str(e)
            final_results.append(ImageCaptionResult(
                image_path=original_filename, error=error_msg))
            logger.error(
                f"Task {task_id}: Error processing image {original_filename} (from path: {temp_path_single}): {error_msg}")
        finally:
            # Clean up the temporary file that was created by the endpoint for this background task
            if temp_path_single and os.path.exists(temp_path_single):
                remove_temp_file(temp_path_single)
            else:
                logger.warning(
                    f"Task {task_id}: Temporary file {temp_path_single} for {original_filename} not found for cleanup or already removed.")

    task_store[task_id].result = final_results

    # Determine final status based on processing outcomes for files handled by this BG task
    bg_task_files_original_names = {
        pf["original_name"] for pf in prepared_files}
    bg_task_processed_results = [
        r for r in final_results if r.image_path in bg_task_files_original_names]

    successful_in_bg_count = sum(
        1 for r in bg_task_processed_results if r.caption and not r.error)
    processed_in_bg_count = len(prepared_files)

    if processed_in_bg_count > 0:
        if successful_in_bg_count == 0:  # All files attempted in BG failed
            task_store[task_id].status = TaskStatus.FAILED
            task_store[
                task_id].message = f"Processing failed for all {processed_in_bg_count} images in background. Total results: {len(final_results)}."
        else:
            task_store[task_id].status = TaskStatus.COMPLETED
            task_store[
                task_id].message = f"Processing complete. {successful_in_bg_count}/{processed_in_bg_count} images captioned successfully in background. Total results: {len(final_results)}."
    # No files were actually processed in background (e.g. prepared_files was empty)
    else:
        # This case should ideally be handled before starting the BG task, but as a fallback:
        # If no successes at all including pre-processing
        if not any(r.caption for r in final_results):
            task_store[task_id].status = TaskStatus.FAILED
        else:
            task_store[task_id].status = TaskStatus.COMPLETED
        task_store[
            task_id].message = f"Processing complete (no new images processed in background). Total results: {len(final_results)}."

    logger.info(
        f"Task {task_id}: Background processing finished. Status: {task_store[task_id].status}. Results updated with {len(final_results)} entries.")


@router.post("/async-batch-caption", response_model=AsyncBatchCaptionResponse, status_code=202)
async def async_batch_caption_images_endpoint(
    background_tasks: BackgroundTasks,
    images: List[UploadFile] = File(...)
):
    """
    Accepts multiple images for captioning. Images are saved to temporary files
    and then processed asynchronously in the background.
    Returns a task ID to check for status and results.
    """
    if not images:
        raise HTTPException(status_code=400, detail="No images provided.")

    task_id = f"task_{int(time.time())}_{os.urandom(4).hex()}"

    initial_results: List[ImageCaptionResult] = []
    files_to_process_in_bg: List[Dict[str, str]] = []

    logger.info(
        f"Task {task_id}: Received request for {len(images)} images. Starting pre-processing and saving.")

    for image_file in images:
        original_filename = image_file.filename or f"unknown_image_{int(time.time())}_{len(initial_results)}"
        temp_path_for_bg = None  # Path to the file saved by this endpoint for the BG task
        try:
            if not image_file.content_type or not image_file.content_type.startswith("image/"):
                error_msg = f"Skipped: Not an image file or unknown content type ({image_file.content_type})."
                logger.warning(
                    f"Task {task_id}: {error_msg} File: {original_filename}")
                initial_results.append(ImageCaptionResult(
                    image_path=original_filename, error=error_msg))
                continue

            # Save the uploaded file to a new temporary location.
            # This reads the UploadFile and creates a new file that will persist for the background task.
            temp_path_for_bg, saved_filename_on_disk = await save_upload_file_temp(image_file)

            files_to_process_in_bg.append({
                "path": temp_path_for_bg,
                "original_name": original_filename,
                # "saved_name": saved_filename_on_disk # Could be stored if needed
            })
            logger.info(
                f"Task {task_id}: Successfully saved {original_filename} to {temp_path_for_bg} for background processing.")

        except Exception as e:
            error_msg = f"Failed to save/prepare image for async processing: {str(e)}"
            logger.error(
                f"Task {task_id}: Error for image {original_filename}: {error_msg}")
            initial_results.append(ImageCaptionResult(
                image_path=original_filename, error=error_msg))
            # If temp_path_for_bg was created by save_upload_file_temp before an error,
            # save_upload_file_temp should ideally handle its own cleanup on failure.
            # If not, and we knew it was created, we might try to clean it here.
            # For now, assuming save_upload_file_temp is atomic or cleans up its own partial creations.

    # Initial task status based on pre-processing
    current_status: TaskStatus
    current_message: str

    if not files_to_process_in_bg:
        logger.warning(
            f"Task {task_id}: No image files were successfully prepared for background processing.")
        # COMPLETED if no files and no errors (empty input?)
        current_status = TaskStatus.FAILED if initial_results else TaskStatus.COMPLETED
        current_message = "Task failed: No valid image files could be prepared for processing."
        if not initial_results and not images:  # Should be caught by "if not images:" earlier
            current_message = "No images provided."
        # All images were filtered out silently (e.g. not image type but no exception)
        elif not initial_results and images:
            current_message = "No suitable image files found for processing."

    else:
        current_status = TaskStatus.PENDING
        current_message = f"Task received. {len(files_to_process_in_bg)} files queued for background processing. {len(initial_results)} files failed pre-processing."

    task_store[task_id] = AsyncTaskStatus(
        task_id=task_id,
        status=current_status,
        message=current_message,
        result=initial_results if initial_results else None
    )

    if files_to_process_in_bg:
        # Only add background task if there are files to process
        background_tasks.add_task(
            process_batch_images_async, task_id, files_to_process_in_bg, initial_results)
        logger.info(
            f"Task {task_id}: Queued background task for {len(files_to_process_in_bg)} files.")
        response_message = f"Batch captioning task accepted. {len(files_to_process_in_bg)} files queued. Check status for details."
    else:
        # No files to process in background, task is already effectively terminal (FAILED or COMPLETED with only pre-processing errors)
        logger.info(
            f"Task {task_id}: No files to process in background. Task status: {current_status}.")
        response_message = current_message  # Provide the more detailed message

    return AsyncBatchCaptionResponse(
        message=response_message,
        task_id=task_id
    )


@router.get("/async-batch-caption/status/{task_id}", response_model=AsyncTaskStatus)
async def get_async_batch_caption_status(task_id: str):
    """
    Retrieves the status and results of an asynchronous batch captioning task.
    """
    task = task_store.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")
    return task

# Note: The original /async-batch-caption endpoint was complex due to background tasks.
# The provided update simplifies its immediate response, highlighting that actual results
# from background tasks need a separate retrieval mechanism not covered here.
# The `process_image_background` in utils.py would need to handle its own temp file removal.
