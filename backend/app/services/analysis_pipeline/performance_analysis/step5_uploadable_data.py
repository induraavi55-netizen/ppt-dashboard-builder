import pandas as pd
from pathlib import Path
import re
from app.core.logging_utils import JobLogger

# ----------------------------
# PATHS
# ----------------------------

DATA_DIR = Path("data")
CLUSTERED_DIR = DATA_DIR / "clustered"

OUTPUT_FILE = DATA_DIR / "uploadable data.xlsx"


# ----------------------------
# NORMALIZATION
# ----------------------------

def normalize_name(name: str) -> str:
    name = name.strip().lower()
    name = re.sub(r"\s+", "_", name)
    name = re.sub(r"_+", "_", name)
    return name


def safe_sheet_name(name: str) -> str:
    invalid = r'[]:*?/\\'
    for ch in invalid:
        name = name.replace(ch, "")
    return name[:31]


# ----------------------------
# COLLECT SHEETS (ORDERED)
# ----------------------------

sheets_to_write = {}





# ======================================================
# 1) REG VS PART FIRST
# ======================================================

reg_file = None

for file_path in DATA_DIR.glob("*.xlsx"):
    if normalize_name(file_path.stem) == "reg_vs_part":
        reg_file = file_path
        break

if reg_file:

    prefix = normalize_name(reg_file.stem)

    JobLogger.log(f"Scanning {reg_file.name}")

    xls = pd.ExcelFile(reg_file)

    for sheet in xls.sheet_names:

        norm_sheet = normalize_name(sheet)

        if norm_sheet in ["schl_wise", "grade_wise"]:

            df = pd.read_excel(reg_file, sheet_name=sheet)

            new_name = safe_sheet_name(
                f"{prefix}_{norm_sheet}"
            )

            sheets_to_write[new_name] = df

            JobLogger.log(f"  → grabbed {sheet} → {new_name}")
# ======================================================
# 2) clustered/all_subjects SECOND
# ======================================================

all_sub_file = CLUSTERED_DIR / "all_subjects.xlsx"

if all_sub_file.exists():

    prefix = normalize_name(all_sub_file.stem)

    JobLogger.log(f"Scanning {all_sub_file.name}")

    xls = pd.ExcelFile(all_sub_file)

    for sheet in xls.sheet_names:

        norm_sheet = normalize_name(sheet)

        if norm_sheet == "perf_summary":

            df = pd.read_excel(all_sub_file, sheet_name=sheet)

            new_name = safe_sheet_name(
                f"{prefix}_{norm_sheet}"
            )

            sheets_to_write[new_name] = df

            JobLogger.log(f"  → grabbed {sheet} → {new_name}")


# ======================================================
# 3) GRADE FILES LAST (NUMERIC ORDER)
# ======================================================

grade_files = []

for file_path in DATA_DIR.glob("*.xlsx"):

    norm_name = normalize_name(file_path.stem)

    if norm_name.startswith("grade_"):
        grade_files.append(file_path)


def extract_grade_num(path: Path):
    m = re.search(r"grade_(\d+)", normalize_name(path.stem))
    return int(m.group(1)) if m else 999


grade_files = sorted(grade_files, key=extract_grade_num)

for file_path in grade_files:

    prefix = normalize_name(file_path.stem)

    JobLogger.log(f"Scanning {file_path.name}")

    xls = pd.ExcelFile(file_path)

    for sheet in xls.sheet_names:

        norm_sheet = normalize_name(sheet)

        if (
            norm_sheet == "sub_wise_avg_perf"
            or norm_sheet.endswith("_lo")
            or norm_sheet.endswith("_qlvl")
        ):

            df = pd.read_excel(file_path, sheet_name=sheet)

            new_name = safe_sheet_name(
                f"{prefix}_{norm_sheet}"
            )

            sheets_to_write[new_name] = df

            JobLogger.log(f"  → grabbed {sheet} → {new_name}")


# ----------------------------
# WRITE OUTPUT
# ----------------------------

JobLogger.log("\nWriting consolidated workbook...")

with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:

    for sheet_name, df in sheets_to_write.items():
        df.to_excel(writer, sheet_name=sheet_name, index=False)

JobLogger.log("Finished. uploadable data.xlsx created.")
