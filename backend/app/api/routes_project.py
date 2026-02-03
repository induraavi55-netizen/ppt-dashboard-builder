from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
import uuid

from app.core.db import get_db
from app.models.slide import Slide
from app.models.project import Project
from app.models.dataset import Dataset

from app.schemas.api import (
    SaveProjectRequest,
    RegenerateProjectRequest,
    MarkManualSlideRequest,
)

from app.services.slide_generator import generate_slides


router = APIRouter(prefix="/projects", tags=["projects"])


# =====================================================
# SAVE PROJECT SLIDES
# =====================================================
@router.post("/save")
def save_project(payload: SaveProjectRequest, db: Session = Depends(get_db)):

    uuid.UUID(payload.project_id)

    project = db.query(Project).filter(
        Project.id == payload.project_id
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    existing_slides = db.query(Slide).filter(
        Slide.project_id == payload.project_id
    ).all()

    existing_map = {
        s.slide_json["slideId"]: s
        for s in existing_slides
        if s.slide_json and "slideId" in s.slide_json
    }

    incoming_ids = set()

    for slide_json in payload.slides:

        sid = slide_json.get("slideId")
        if not sid:
            continue

        incoming_ids.add(sid)

        position = slide_json.get("position", 0)

        if sid in existing_map:
            slide_json.setdefault(
                "generated",
                existing_map[sid].slide_json.get("generated", True),
            )
        else:
            slide_json.setdefault("generated", True)

        if sid in existing_map:

            db_slide = existing_map[sid]
            db_slide.slide_json = slide_json
            db_slide.position = position
            flag_modified(db_slide, "slide_json")

        else:

            db.add(
                Slide(
                    project_id=payload.project_id,
                    slide_json=slide_json,
                    position=position,
                )
            )

    for sid, slide in existing_map.items():
        if sid not in incoming_ids:
            db.delete(slide)

    db.commit()

    return {"status": "saved", "slides": len(payload.slides)}


# =====================================================
# LOAD PROJECT
# =====================================================
@router.get("/{project_id}")
def load_project(project_id: str, db: Session = Depends(get_db)):

    uuid.UUID(project_id)

    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    datasets = db.query(Dataset).filter(
        Dataset.project_id == project_id
    ).all()

    slides = (
        db.query(Slide)
        .filter(Slide.project_id == project_id)
        .order_by(Slide.position.asc())
        .all()
    )

    return {
        "project": {
            "id": str(project.id),
            "name": project.name,
        },
        "datasets": [
            {
                "id": str(d.id),
                "name": d.name,
                "columns": d.columns,
                "schema": d.schema,
                "preview": d.preview,
            }
            for d in datasets
        ],
        "slides": [s.slide_json for s in slides],
    }


# =====================================================
# REGENERATE AUTO SLIDES (FIXED)
# =====================================================
@router.post("/regenerate")
def regenerate_project(
    payload: RegenerateProjectRequest,
    db: Session = Depends(get_db),
):

    uuid.UUID(payload.project_id)

    project = db.query(Project).filter(
        Project.id == payload.project_id
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # ----------------------------------
    # Load existing slides BEFORE delete
    # ----------------------------------
    existing = db.query(Slide).filter(
        Slide.project_id == payload.project_id
    ).all()

    manual = [s for s in existing if s.slide_json.get("generated") is False]
    autos = [s for s in existing if s.slide_json.get("generated") is True]

    used_positions = {s.position for s in manual}

    dataset_pos = {}
    group_pos = {}
    overview_pos = None

    for s in autos:
        role = s.slide_json.get("role")
        if role == "overview":
            overview_pos = s.position
        if role == "dataset":
            dataset_pos[s.slide_json.get("dataset_id")] = s.position
        if role == "group":
            group_pos[s.slide_json.get("group")] = s.position

    manual_overview_exists = any(
        s.slide_json.get("role") == "overview" for s in manual
    )

    # ----------------------------------
    # Delete old autos
    # ----------------------------------
    db.query(Slide).filter(
        Slide.project_id == payload.project_id,
        Slide.slide_json["generated"].as_boolean().is_(True),
    ).delete(synchronize_session=False)

    # ----------------------------------
    # Reload datasets
    # ----------------------------------
    datasets = db.query(Dataset).filter(
        Dataset.project_id == payload.project_id
    ).all()

    dataset_payloads = [
        {
            "id": str(d.id),
            "name": d.name,
            "schema": d.schema,
            "columns": d.columns,
            "preview": d.preview,
        }
        for d in datasets
    ]

    new_slides = generate_slides(payload.project_id, dataset_payloads)

    # ----------------------------------
    # Position allocator
    # ----------------------------------
    pos = 0

    def next_free():
        nonlocal pos
        while pos in used_positions:
            pos += 1
        used_positions.add(pos)
        return pos

    # ----------------------------------
    # Insert regenerated autos
    # ----------------------------------
    for s in new_slides:

        role = s.get("role")

        # skip overview regen if manual
        if role == "overview" and manual_overview_exists:
            continue

        preferred = None

        if role == "overview":
            preferred = overview_pos
        elif role == "dataset":
            preferred = dataset_pos.get(s.get("dataset_id"))
        elif role == "group":
            preferred = group_pos.get(s.get("group"))

        if preferred is not None and preferred not in used_positions:
            safe_pos = preferred
            used_positions.add(preferred)
        else:
            safe_pos = next_free()

        s["position"] = safe_pos

        db.add(
            Slide(
                project_id=payload.project_id,
                slide_json=s,
                position=safe_pos,
            )
        )

    db.commit()

    return {
        "status": "regenerated",
        "slides_created": len(new_slides),
    }


# =====================================================
# MARK SLIDE MANUAL
# =====================================================
@router.post("/mark-manual")
def mark_slide_manual(
    payload: MarkManualSlideRequest,
    db: Session = Depends(get_db),
):

    slides = (
        db.query(Slide)
        .filter(Slide.project_id == payload.project_id)
        .order_by(Slide.position.asc())
        .all()
    )

    target = next(
        (s for s in slides if s.slide_json["slideId"] == payload.slide_id),
        None,
    )

    if not target:
        raise HTTPException(status_code=404, detail="Slide not found")

    target.slide_json["generated"] = False
    flag_modified(target, "slide_json")

    db.commit()

    return {
        "status": "ok",
        "slide_id": payload.slide_id,
        "generated": False,
    }
