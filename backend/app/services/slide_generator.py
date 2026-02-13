print("🔥 USING FIXED SLIDE GENERATOR 🔥")

from typing import List, Dict
import uuid
import copy

from app.services.dataset_profiler import profile_dataset
from app.services.evaluator import pick_rule


def new_id() -> str:
    return str(uuid.uuid4())


# --------------------------------------------------
# Slide Generator (RULE DRIVEN + DETERMINISTIC)
# --------------------------------------------------

def generate_slides(project_id: str, datasets: List[Dict]) -> List[Dict]:

    # skip merged-cell datasets deterministically
    datasets = [d for d in datasets if not d.get("has_merged_cells")]

    slides: List[Dict] = []
    pos = 0

    # --------------------------------------------------
    # OVERVIEW SLIDE
    # --------------------------------------------------

    slides.append({
        "slideId": new_id(),
        "layoutVersion": 1,
        "generated": True,
        "role": "overview",
        "position": pos,
        "type": "overview",
        "title": "Performance Summary",
        "locked": False,
        "elements": [
            {
                "id": new_id(),
                "type": "title",
                "value": "Performance Summary",
                "x": 80,
                "y": 40,
                "fontSize": 28,
            },
            {
                "id": new_id(),
                "type": "text",
                "value": "Auto-generated dashboard",
                "x": 80,
                "y": 90,
                "fontSize": 16,
            },
        ],
    })

    pos += 1

    # --------------------------------------------------
    # DATASET SLIDES
    # --------------------------------------------------

    for d in datasets:

        profile = profile_dataset(d)
        decision = pick_rule(profile)

        print("DATASET:", d["name"])
        print("PROFILE:", profile)
        print("DECISION:", decision)

        base_name = d["name"]

        # ==================================================
        # SCHOOL REG VS PART → PIE PER SCHOOL
        # ==================================================

        if decision.get("split_slides"):

            buckets = {}

            for r in d.get("preview", []):

                key = (
                    r.get("School Name")
                    or r.get("school")
                    or r.get("School")
                )

                if not key:
                    continue

                try:
                    part = float(r.get("Participated"))
                    notp = float(r.get("Not Participated"))
                    reg = float(r.get("Registered") or 0)
                except Exception:
                    continue

                buckets[key] = {
                    "Participated": part,
                    "Not Participated": notp,
                    "Registered": reg,
                }

            for school, vals in buckets.items():

                preview = [
                    {"Category": "Participated", "Value": vals["Participated"]},
                    {"Category": "Not Participated", "Value": vals["Not Participated"]},
                ]

                elements: List[Dict] = []

                elements.append({
                    "id": new_id(),
                    "type": "title",
                    "value": f"{base_name} - {school}",
                    "x": 60,
                    "y": 40,
                    "fontSize": 24,
                })

                elements.append({
                    "id": new_id(),
                    "type": "chart",
                    "chartType": decision["chart"],
                    "datasetName": base_name,
                    "datasetFamily": profile.get("dataset_family"),
                    "metricTypes": profile.get("metric_types"),
                    "preview": preview,
                    "schema": {},
                    "x": 80,
                    "y": 120,
                    "width": 620,
                    "height": 420,
                })

                elements.append({
                    "id": new_id(),
                    "type": "text",
                    "value": f"Registered: {int(vals['Registered'])}",
                    "x": 780,
                    "y": 190,
                    "width": 220,
                    "height": 90,
                    "fontSize": 16,
                    "boxed": True,
                })

                slides.append({
                    "slideId": new_id(),
                    "layoutVersion": 1,
                    "generated": True,
                    "role": "dataset",
                    "dataset_id": d["id"],
                    "position": pos,
                    "type": "dataset",
                    "title": f"{base_name} - {school}",
                    "locked": False,
                    "elements": elements,
                })

                pos += 1

            continue

        # ==================================================
        # GRADE REG VS PART → grouped bars
        # ==================================================

        local_dataset = d

        if (
            profile.get("special_case") == "reg_vs_part"
            and profile.get("entity") == "grade"
        ):

            new_preview = []

            for r in d.get("preview", []):
                new_preview.append({
                    "Grade": r.get("Grade"),
                    "Registered": r.get("Registered"),
                    "Participated": r.get("Participated"),
                    "Participation %": r.get("Participation %"),
                })

            local_dataset = copy.deepcopy(d)
            local_dataset["preview"] = new_preview

        # ==================================================
        # DEFAULT SLIDE
        # ==================================================

        elements: List[Dict] = []

        elements.append({
            "id": new_id(),
            "type": "title",
            "value": base_name,
            "x": 60,
            "y": 40,
            "fontSize": 24,
        })

        print(f"[PROFILE] Dataset: {d['name']} | Family: {profile['dataset_family']} | Types: {profile['metric_types']}")

        elements.append({
            "id": new_id(),
            "type": "chart",
            "chartType": decision.get("chart", "column"),
            "datasetName": base_name,
            "datasetFamily": profile.get("dataset_family"),
            "metricTypes": profile.get("metric_types"),
            "preview": local_dataset.get("preview"),
            "schema": local_dataset.get("schema"),
            "x": 80,
            "y": 120,
            "width": 680,
            "height": 420,
        })

        slides.append({
            "slideId": new_id(),
            "layoutVersion": 1,
            "generated": True,
            "role": "dataset",
            "dataset_id": d["id"],
            "position": pos,
            "type": "dataset",
            "title": base_name,
            "locked": False,
            "elements": elements,
        })

        pos += 1

    return slides
