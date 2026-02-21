import pandas as pd
import numpy as np
from pathlib import Path
from app.core.logging_utils import JobLogger
from app.core.pipeline_config import PIPELINE_CONFIG

# -----------------------------
# CONFIG
# -----------------------------

# Removed static evaluation of pipeline config

DATA_DIR = Path("data")
FILE = DATA_DIR / "REG VS PART.xlsx"
SHEET = "Assessment Participation"

# -----------------------------
# LOAD RAW (TWO HEADER ROWS)
# -----------------------------

raw = pd.read_excel(FILE, sheet_name=SHEET, header=None)

df = raw.iloc[2:].copy()
header_row = raw.iloc[1]

cols = list(header_row)

cols[0] = "S.No"
cols[1] = "School Name"
cols[2] = "District"

cols[15] = "Total Registered"
cols[28] = "Total Participated"

cols[-2] = "Contact Name"
cols[-1] = "Contact Phone"

df.columns = cols

# Clean school names
df["School Name"] = df["School Name"].astype(str).str.strip()

JobLogger.log("\n===== DEBUG: ORIGINAL SCHOOL NAMES =====")
JobLogger.log(str(df["School Name"].unique()))

# Drop total row
df = df[df["School Name"].str.lower() != "total"]

JobLogger.log("\n===== DEBUG: DF SHAPE AFTER DROP TOTAL =====")
JobLogger.log(str(df.shape))

# -----------------------------
# IDENTIFY GRADE COLUMN INDEXES
# -----------------------------

reg_idx = list(range(3, 15))
part_idx = list(range(16, 28))

reg_grade_map = {i: int(float(df.columns[i])) for i in reg_idx}
part_grade_map = {i: int(float(df.columns[i])) for i in part_idx}

JobLogger.log(f"\n===== DEBUG: REG IDX ===== {reg_idx}")
JobLogger.log(f"===== DEBUG: PART IDX ===== {part_idx}")

# -----------------------------
# FILTER SCHOOLS (FIXED)
# -----------------------------

# Extract config dynamically on each run
use_all = PIPELINE_CONFIG.get("useAll", True)
schools_config = PIPELINE_CONFIG.get("schools", [])

df_filt = df.copy()

if not use_all:

    allowed_schools = [
        sc.get("schoolName", "").strip().lower()
        for sc in schools_config
    ]

    JobLogger.log(f"\n===== DEBUG: ALLOWED SCHOOLS =====")
    JobLogger.log(str(allowed_schools))

    df_filt = df_filt[
        df_filt["School Name"]
        .str.lower()
        .isin(allowed_schools)
    ]

    JobLogger.log(f"Rows after school filter: {len(df_filt)}")

else:

    JobLogger.log("Using ALL schools")

JobLogger.log("\n===== DEBUG: FILTERED SCHOOL NAMES =====")
JobLogger.log(str(df_filt["School Name"].unique()))

# -----------------------------
# APPLY GRADE RANGE MASKING
# -----------------------------

if not use_all:

    JobLogger.log("Applying grade range masking")

    for sc in schools_config:

        school = sc.get("schoolName", "").strip().lower()
        f_grade = sc.get("fromGrade", 0)
        t_grade = sc.get("toGrade", 100)

        mask = df_filt["School Name"].str.lower() == school

        if not mask.any():
            continue

        # Registered columns
        for col_idx, grade in reg_grade_map.items():

            if not (f_grade <= grade <= t_grade):

                col_name = df.columns[col_idx]
                df_filt.loc[mask, col_name] = 0

        # Participated columns
        for col_idx, grade in part_grade_map.items():

            if not (f_grade <= grade <= t_grade):

                col_name = df.columns[col_idx]
                df_filt.loc[mask, col_name] = 0

# -----------------------------
# SCHOOL TOTALS
# -----------------------------

school_totals = df_filt[["School Name"]].copy()

school_totals["Registered"] = df_filt.iloc[:, reg_idx].sum(axis=1)
school_totals["Participated"] = df_filt.iloc[:, part_idx].sum(axis=1)

school_totals["Not Participated"] = (
    school_totals["Registered"] - school_totals["Participated"]
)

school_totals = school_totals[
    ["School Name", "Participated", "Not Participated", "Registered"]
]

JobLogger.log("\n===== DEBUG: SCHOOL TOTALS =====")
JobLogger.log(str(school_totals))

# -----------------------------
# OVERALL GRADE TOTALS
# -----------------------------

overall = pd.DataFrame({
    "Grade": [reg_grade_map[i] for i in reg_idx],
    "Registered": df_filt.iloc[:, reg_idx].sum().values,
    "Participated": df_filt.iloc[:, part_idx].sum().values,
})

overall["Registered"] = pd.to_numeric(overall["Registered"], errors="coerce").fillna(0)
overall["Participated"] = pd.to_numeric(overall["Participated"], errors="coerce").fillna(0)

overall["Participation %"] = (
    (overall["Participated"] / overall["Registered"]) * 100
).replace([np.inf, -np.inf], 0).fillna(0)

overall["Participation %"] = overall["Participation %"].round(0).astype(int)

# Remove grades with no registered students
JobLogger.log(f"Grades before filtering: {overall['Grade'].tolist()}")

overall = overall[overall["Registered"] > 0]

JobLogger.log(f"Grades after filtering: {overall['Grade'].tolist()}")

JobLogger.log("\n===== DEBUG: OVERALL =====")
JobLogger.log(str(overall))

# -----------------------------
# WRITE BACK
# -----------------------------

with pd.ExcelWriter(FILE, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:

    school_totals.to_excel(writer, sheet_name="schl_wise", index=False)
    overall.to_excel(writer, sheet_name="grade_wise", index=False)

    from app.core.preview_registry import register_preview

    register_preview("participation-0", {
        "sheets": [
            {
                "name": "schl_wise",
                "columns": list(school_totals.columns),
                "rows": school_totals.fillna("").to_dict("records")
            },
            {
                "name": "grade_wise",
                "columns": list(overall.columns),
                "rows": overall.fillna("").to_dict("records")
            }
        ]
    })

    JobLogger.log("\n✅ DONE. Participation step completed successfully.")