from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    x: float = Field(ge=0)
    y: float = Field(ge=0)
    width: float = Field(gt=0)
    height: float = Field(gt=0)


class Detection(BaseModel):
    class_name: str = Field(min_length=1, max_length=120)
    confidence: float = Field(ge=0, le=1)
    box: BoundingBox


class ShelfRegion(BaseModel):
    label: str
    status: str
    confidence: float | None = Field(default=None, ge=0, le=1)
    box: BoundingBox


class ShelfAssessment(BaseModel):
    status: str
    object_coverage: float = Field(ge=0, le=1)
    low_stock_supported: bool
    note: str


class AnalysisResponse(BaseModel):
    id: UUID
    user_id: UUID
    image_name: str
    status: str
    image_width: int
    image_height: int
    detection_count: int
    class_counts: dict[str, int]
    detections: list[Detection]
    shelf_assessment: ShelfAssessment
    shelf_regions: list[ShelfRegion]
    model_name: str
    model_version: str
    created_at: datetime
    completed_at: datetime | None = None


class AnalysisListItem(BaseModel):
    id: UUID
    image_name: str
    status: str
    detection_count: int
    model_name: str
    model_version: str
    created_at: datetime
    completed_at: datetime | None = None
