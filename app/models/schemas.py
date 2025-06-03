from pydantic import BaseModel
from enum import Enum
from typing import Any, List, Optional, Dict


class CaptionResponse(BaseModel):
    """Response model containing caption and metadata."""
    filename: str
    caption: str
    tags: List[str] = []
    processing_time: float


class BatchCaptionResponse(BaseModel):
    """Response model for batch captioning results."""
    results: List["ImageCaptionResult"]
    total_processing_time: float


class ImageCaptionResult(BaseModel):
    image_path: str
    caption: Optional[str] = None
    tags: Optional[List[str]] = None
    error: Optional[str] = None


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class AsyncTaskStatus(BaseModel):
    task_id: str
    status: TaskStatus
    message: Optional[str] = None
    result: Optional[List[ImageCaptionResult]] = None
    error_details: Optional[str] = None


class AsyncBatchCaptionResponse(BaseModel):
    message: str
    task_id: str
