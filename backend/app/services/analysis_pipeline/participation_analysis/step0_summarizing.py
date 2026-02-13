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

EXAM_GRADES = PIPELINE_CONFIG["exam_grades"]

PARTICIPATING_SCHOOLS = PIPELINE_CONFIG["participating_schools"]

DATA_DIR = Path("data")
FILE = DATA_DIR / "REG VS PART.xlsx"
SHEET = "Assessment Participation"

# -----------------------------
# LOAD RAW (TWO HEADER ROWS)
# -----------------------------

raw = pd.read_excel(FILE, sheet_name=SHEET, header=None)




# real data starts from row index 2
df = raw.iloc[2:].copy()

# second row contains grade numbers
header_row = raw.iloc[1]

cols = list(header_row)

# fix first columns
cols[0] = "S.No"
cols[1] = "School Name"
cols[2] = "District"

# totals
cols[15] = "Total Registered"
cols[28] = "Total Participated"

# last two
cols[-2] = "Contact Name"
cols[-1] = "Contact Phone"

df.columns = cols

JobLogger.log("\n===== DEBUG: ASSIGNED COLUMNS =====")
for i, c in enumerate(df.columns):
    JobLogger.log(f"{i} {c}")

# drop total row
df = df[df["School Name"].astype(str).str.lower() != "total"]

JobLogger.log("\n===== DEBUG: DF SHAPE AFTER DROP TOTAL =====")
JobLogger.log(str(df.shape))

JobLogger.log("\n===== DEBUG: SCHOOL NAMES =====")
JobLogger.log(str(df["School Name"].unique()))

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

# keep only exam grades
reg_idx = [i for i in reg_idx if reg_grade_map[i] in EXAM_GRADES]
part_idx = [i for i in part_idx if part_grade_map[i] in EXAM_GRADES]

JobLogger.log(f"\n===== DEBUG: REG IDX ===== {reg_idx}")
JobLogger.log(f"===== DEBUG: PART IDX ===== {part_idx}")

# -----------------------------
# FILTER SCHOOLS FIRST
# -----------------------------

df["School Name"] = df["School Name"].astype(str).str.strip()

school_filter = [s.lower() for s in PARTICIPATING_SCHOOLS]

df_filt = df[
    df["School Name"]
        .str.lower()
        .isin(school_filter)
]

# -----------------------------
# SCHOOL TOTALS (SAFE)
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
).fillna(0) # Handle 0/0 -> NaN

# Handle x/0 -> inf
overall["Participation %"] = overall["Participation %"].replace([np.inf, -np.inf], 0)

# Now safe to cast
overall["Participation %"] = overall["Participation %"].round(0).astype(int)



JobLogger.log("\n===== DEBUG: OVERALL =====")
JobLogger.log(str(overall))


# -----------------------------
# WRITE BACK TO SAME FILE
# -----------------------------

with pd.ExcelWriter(FILE, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
    school_totals.to_excel(writer, sheet_name="schl_wise", index=False)
    overall.to_excel(writer, sheet_name="grade_wise", index=False)

JobLogger.log("\n✅ DONE. Sheets written:")
JobLogger.log(" - schl_wise")
JobLogger.log(" - grade_wise")
