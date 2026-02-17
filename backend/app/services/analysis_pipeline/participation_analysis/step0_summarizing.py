import pandas as pd
import numpy as np
from pathlib import Path
from app.core.logging_utils import JobLogger

# -----------------------------
# CONFIG
# -----------------------------

from app.core.pipeline_config import PIPELINE_CONFIG

# -----------------------------
# CONFIG
# -----------------------------

USE_ALL = PIPELINE_CONFIG.get("useAll", True)
SCHOOLS_CONFIG = PIPELINE_CONFIG.get("schools", [])

# Grades setup (No filtering by default now, or logic based on new config)
# If useAll is True, we use ALL found grades.
# If useAll is False, we typically just filter schools for this summary view.
# The previous "EXAM_GRADES" list is technically legacy. 
# We will use ALL detected grades for the summary to be safe.

DATA_DIR = Path("data")
FILE = DATA_DIR / "REG VS PART.xlsx"
SHEET = "Assessment Participation"

# ... (Load raw, header, fix columns, drop total - same as before) ...
# I will retain lines 24-68 (loading) as they are fine. 
# I am targeting the FILTERING logic (lines 83-102) and CONFIG (lines 16-18)

# ...

# -----------------------------
# IDENTIFY GRADE COLUMN INDEXES
# -----------------------------

# registered block positions
reg_idx = list(range(3, 15))

# participated block positions
part_idx = list(range(16, 28))

# map index -> grade number
reg_grade_map = {i: int(float(df.columns[i])) for i in reg_idx}
part_grade_map = {i: int(float(df.columns[i])) for i in part_idx}

# keep only exam grades? 
# New Logic: Use ALL detected grades unless specific logic needed.
# We will assume all valid columns in "Assessment Participation" are grades we want.
# So we REMOVE the EXAM_GRADES filtering.
# reg_idx = [i for i in reg_idx if reg_grade_map[i] in EXAM_GRADES] 
# part_idx = [i for i in part_idx if part_grade_map[i] in EXAM_GRADES]

JobLogger.log(f"\n===== DEBUG: REG IDX ===== {reg_idx}")
JobLogger.log(f"===== DEBUG: PART IDX ===== {part_idx}")

# -----------------------------
# FILTER SCHOOLS
# -----------------------------

df["School Name"] = df["School Name"].astype(str).str.strip()

if not USE_ALL:
    # Filter by configured schools
    allowed_names = {s["schoolName"].lower() for s in SCHOOLS_CONFIG}
    JobLogger.log(f"Filtering for {len(allowed_names)} schools")
    df_filt = df[
        df["School Name"].str.lower().isin(allowed_names)
    ]
else:
    # Use ALL schools
    JobLogger.log("Using ALL schools (Default)")
    df_filt = df.copy()

# -----------------------------
# SCHOOL TOTALS (SAFE)
# -----------------------------
# ... lines 104+ can remain similar ...



JobLogger.log("\n===== DEBUG: OVERALL =====")
JobLogger.log(str(overall))


# -----------------------------
# WRITE BACK TO SAME FILE
# -----------------------------

with pd.ExcelWriter(FILE, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
    school_totals.to_excel(writer, sheet_name="schl_wise", index=False)
    overall.to_excel(writer, sheet_name="grade_wise", index=False)
    
    # --------------------------------------------------
    # REGISTER PREVIEW
    # --------------------------------------------------
    from app.core.preview_registry import register_preview
    
    preview_sheets = []
    
    # schl_wise
    st_preview = school_totals.head(100).fillna("")
    preview_sheets.append({
        "name": "schl_wise",
        "columns": list(st_preview.columns),
        "rows": st_preview.to_dict(orient="records")
    })
    
    # grade_wise
    ov_preview = overall.head(100).fillna("")
    preview_sheets.append({
        "name": "grade_wise",
        "columns": list(ov_preview.columns),
        "rows": ov_preview.to_dict(orient="records")
    })
    
    register_preview("participation-0", {"sheets": preview_sheets})

    JobLogger.log("\n✅ DONE. Sheets written and registered:")
    JobLogger.log(" - schl_wise")
    JobLogger.log(" - grade_wise")
