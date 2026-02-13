from fastapi import APIRouter, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session

from app.services.excel_parser import parse_excel
from app.core.db import SessionLocal
from app.models.project import Project
from app.models.dataset import Dataset
from app.services.slide_generator import generate_slides
from app.models.slide import Slide
from app.services.dataset_profiler import profile_dataset
from app.services.dataset_service import detect_dataset_type_from_name


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

    print(f" [Upload] Extracted {len(datasets)} datasets from file.")
    if len(datasets) == 0:
        print(" [Upload] WARNING: No datasets found! Dashboard will be empty.")

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

    response_payload = {
        "project_id": str(project.id),
        "projectName": project.name,
        "datasets": [
            {
                "id": str(d["id"]),
                "name": d["name"],
                "detected_type": detect_dataset_type_from_name(d["name"]),
                "profile": profile_dataset({
                    "name": d["name"],
                    "schema": d["schema"],
                    "preview": d["preview"]
                }),
                "row_count": len(d["preview"]),
                "col_count": len(d["columns"]),
                "preview": d["preview"],
                "schema": d["schema"]
            }
            for d in dataset_outputs
        ],
        "slides_created": len(slides),
    }
    print(f" [Upload] Returning success. Project: {project.id}, Datasets: {len(dataset_outputs)}")
    return response_payload
