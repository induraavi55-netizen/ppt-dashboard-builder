from pathlib import Path
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.dataset import Dataset
from app.services.dataset_profiler import profile_dataset
from app.services.ppt.slide_builder import build_ppt_from_slides


EXPORT_DIR = Path("exports")
EXPORT_DIR.mkdir(exist_ok=True)


def export_project_to_ppt(project, slides, db: Session, debug_mode: bool = False):

    # -----------------------------------
    # Load datasets for lookup
    # -----------------------------------
    datasets = (
        db.query(Dataset)
        .filter(Dataset.project_id == project.id)
        .all()
    )

    dataset_map = {
        str(d.id): {
            "preview": d.preview,
            "schema": d.schema,
            "name": d.name,
            "profile": profile_dataset({
                "name": d.name,
                "schema": d.schema,
                "preview": d.preview
            })
        }
        for d in datasets
    }

    # -----------------------------------
    # Inject dataset info into slide JSON
    # -----------------------------------
    for slide in slides:

        slide_json = slide.slide_json

        for el in slide_json.get("elements", []):

            if el.get("type") != "chart":
                continue

            dataset_id = el.get("datasetId")

            if not dataset_id:
                continue

            dataset_info = dataset_map.get(dataset_id)

            if not dataset_info:
                continue

            # inject for renderer
            el["preview"] = dataset_info["preview"]
            el["schema"] = dataset_info["schema"]
            el["datasetName"] = dataset_info["name"]
            el["metricTypes"] = dataset_info["profile"].get("metric_types")
            el["datasetFamily"] = dataset_info["profile"].get("dataset_family")

    # -----------------------------------
    # Build PPTX
    # -----------------------------------
    filename = f"{project.name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pptx"
    output_path = EXPORT_DIR / filename

    ppt_path = build_ppt_from_slides(
        project=project,
        slides=slides,
        output_path=output_path,
        debug_mode=debug_mode,
    )

    return str(ppt_path)
