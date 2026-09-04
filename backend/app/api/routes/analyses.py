from __future__ import annotations

import tempfile
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status

from app.core.auth import AuthenticatedUser, get_current_user
from app.db import connection, database_configured
from app.repositories.analyses import AnalysisRepository
from app.schemas.analysis import AnalysisListItem, AnalysisResponse, Detection, ShelfAssessment
from app.services.vision import VisionService
from app.utils.image_validation import safe_filename, validate_image_upload

router = APIRouter(prefix="/analyses", tags=["analyses"])
vision_service = VisionService()
repository = AnalysisRepository(connection)


def _response(data: dict) -> AnalysisResponse:
    detections = [Detection.model_validate(item) for item in data["detections"]]
    counts: dict[str, int] = {}
    for detection in detections:
        counts[detection.class_name] = counts.get(detection.class_name, 0) + 1
    assessment = ShelfAssessment(
        status="unknown",
        object_coverage=float(data.get("object_coverage") or 0.0),
        low_stock_supported=False,
        note="Stock-level and empty-shelf inference is not claimed for the general COCO detector.",
    )
    return AnalysisResponse(
        id=data["id"], user_id=data["user_id"], image_name=data["image_name"], status=data["status"],
        image_width=data["image_width"], image_height=data["image_height"],
        detection_count=data["detection_count"], class_counts=counts, detections=detections,
        shelf_assessment=assessment, shelf_regions=[], model_name=data["model_name"],
        model_version=data["model_version"], created_at=data["created_at"], completed_at=data["completed_at"],
    )


@router.post("", response_model=AnalysisResponse, status_code=status.HTTP_201_CREATED)
async def create_analysis(
    file: UploadFile = File(...),
    user: AuthenticatedUser = Depends(get_current_user),
) -> AnalysisResponse:
    if not database_configured():
        raise HTTPException(status_code=503, detail="DATABASE_URL is not configured")
    try:
        data = await file.read()
        validate_image_upload(file.filename, file.content_type, data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    display_name = safe_filename(file.filename)
    suffix = Path(display_name).suffix.lower()
    with tempfile.NamedTemporaryFile(prefix="retail-analysis-", suffix=suffix, delete=True) as temp:
        temp.write(data)
        temp.flush()
        try:
            analysis = vision_service.analyze(temp.name)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=503, detail="Computer-vision inference is unavailable") from exc

    stored = repository.create(
        user_id=user.id, email=user.email, image_name=display_name,
        width=analysis.width, height=analysis.height, detections=analysis.detections,
        model_name="YOLOX-Tiny", model_version="0.1.1rc0", object_coverage=analysis.object_coverage,
    )
    return _response(stored)


@router.get("", response_model=list[AnalysisListItem])
def list_analyses(user: AuthenticatedUser = Depends(get_current_user)) -> list[AnalysisListItem]:
    if not database_configured():
        raise HTTPException(status_code=503, detail="DATABASE_URL is not configured")
    return [AnalysisListItem.model_validate(item) for item in repository.list(user_id=user.id)]


@router.get("/{analysis_id}", response_model=AnalysisResponse)
def get_analysis(analysis_id: UUID, user: AuthenticatedUser = Depends(get_current_user)) -> AnalysisResponse:
    if not database_configured():
        raise HTTPException(status_code=503, detail="DATABASE_URL is not configured")
    data = repository.get(user_id=user.id, analysis_id=analysis_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return _response(data)


@router.delete("/{analysis_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_analysis(analysis_id: UUID, user: AuthenticatedUser = Depends(get_current_user)) -> Response:
    if not database_configured():
        raise HTTPException(status_code=503, detail="DATABASE_URL is not configured")
    if not repository.delete(user_id=user.id, analysis_id=analysis_id):
        raise HTTPException(status_code=404, detail="Analysis not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
