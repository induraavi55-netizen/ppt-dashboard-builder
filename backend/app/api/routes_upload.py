from fastapi import APIRouter, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session

from app.services.excel_parser import parse_excel
from app.core.db import SessionLocal
from app.models.project import Project
from app.models.dataset import Dataset
from app.services.slide_generator import generate_slides
from app.models.slide import Slide


router = APIRouter(prefix="/upload-data", tags=["upload"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("")
async def upload_data(
    project_name: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    datasets = await parse_excel(file)

    # -------------------
    # CREATE PROJECT
    # -------------------
    project = Project(name=project_name)
    db.add(project)
    db.commit()
    db.refresh(project)

    dataset_outputs = []
    ids = []

    # -------------------
    # SAVE DATASETS
    # -------------------
    for d in datasets:
        ds = Dataset(
            project_id=project.id,
            name=d["name"],
            schema=d["schema"],
            columns=d["columns"],
            row_count=d["rows"],
            preview=d["preview"],
        )
        db.add(ds)
        db.flush()

        ids.append(ds.id)

        dataset_outputs.append({
            "id": str(ds.id),
            "name": ds.name,
            "columns": ds.columns,
            "schema": ds.schema,
            "preview": ds.preview,
        })

    db.commit()

    # -------------------
    # AUTO-GENERATE SLIDES
    # -------------------
    slides = generate_slides(project.id, dataset_outputs)

    for s in slides:
        db.add(
            Slide(
                project_id=project.id,
                slide_json=s,
                position=s["position"],
            )
        )

    db.commit()

    return {
        "project_id": project.id,
        "dataset_ids": ids,
        "slides_created": len(slides),
    }
