from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import uuid
import os

from app.core.db import get_db
from app.models.project import Project
from app.models.slide import Slide

from app.services.export_service import export_project_to_ppt


router = APIRouter(prefix="/export", tags=["export"])


@router.post("/{project_id}")
def export_project(
    project_id: str, 
    db: Session = Depends(get_db),
    x_export_debug: str | None = Header(default=None, alias="X-EXPORT-DEBUG"),
):
    
    debug_mode = x_export_debug == "true"

    uuid.UUID(project_id)

    project = (
        db.query(Project)
        .filter(Project.id == project_id)
        .first()
    )

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    slides = (
        db.query(Slide)
        .filter(Slide.project_id == project_id)
        .order_by(Slide.position.asc())
        .all()
    )

    if not slides:
        raise HTTPException(status_code=400, detail="No slides to export")

    try:
        ppt_path = export_project_to_ppt(
            project=project,
            slides=slides,
            db=db,
            debug_mode=debug_mode,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

    return FileResponse(
        ppt_path,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename=os.path.basename(ppt_path),
    )
