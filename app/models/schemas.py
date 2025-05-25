from pydantic import BaseModel
from typing import List


class CaptionResponse(BaseModel):
    """Response model containing caption and metadata."""
    filename: str
    caption: str
    processing_time: float


class BatchCaptionResponse(BaseModel):
    """Response model for batch captioning results."""
    results: List[CaptionResponse]
    total_processing_time: float
