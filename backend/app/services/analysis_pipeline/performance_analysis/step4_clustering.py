import pandas as pd
from pathlib import Path
from app.core.logging_utils import JobLogger

DATA_DIR = Path("data")   # folder with Grade_7.xlsx, Grade_8.xlsx, etc.

# --------------------------------------------------
# STEP 1: COLLECT *_formatted SHEETS
# --------------------------------------------------

subject_buckets = {}

for file_path in DATA_DIR.glob("*.xlsx"):

    file_stem = file_path.stem   # Grade_7

    xls = pd.ExcelFile(file_path)

    for sheet in xls.sheet_names:

        sheet_clean = sheet.strip().lower()

        if sheet_clean.endswith("_formatted"):

            base_subject = sheet_clean.replace("_formatted", "")

            df = pd.read_excel(file_path, sheet_name=sheet)

            subject_buckets.setdefault(base_subject, []).append(
                (file_stem, df)
            )

            JobLogger.log(f"Collected {sheet} from {file_path.name}")

# --------------------------------------------------
# STEP 2: WRITE SUBJECT FILES + ALL_GRADES
# --------------------------------------------------

OUTPUT_DIR = DATA_DIR / "clustered"
OUTPUT_DIR.mkdir(exist_ok=True)

for subject, sheets in subject_buckets.items():

    if not sheets:
        continue

    out_file = OUTPUT_DIR / f"{subject}.xlsx"

    with pd.ExcelWriter(out_file, engine="openpyxl") as writer:

        combined_frames = []

        for sheet_name, df in sheets:

            # write individual grade sheet
            df.to_excel(writer, sheet_name=sheet_name, index=False)

            # keep for combined view
            temp = df.copy()
            temp["Source Grade File"] = sheet_name
            combined_frames.append(temp)

        # ---- create ALL_GRADES sheet ----
        combined_df = pd.concat(combined_frames, ignore_index=True)

        combined_df.to_excel(writer, sheet_name="ALL_GRADES", index=False)

    JobLogger.log(f"Created {out_file.name} (with ALL_GRADES)")

# --------------------------------------------------
# STEP 3: BUILD all_subjects.xlsx FROM ALL_GRADES
# --------------------------------------------------

MASTER_FILE = OUTPUT_DIR / "all_subjects.xlsx"

with pd.ExcelWriter(MASTER_FILE, engine="openpyxl") as writer:

    for subject_file in OUTPUT_DIR.glob("*.xlsx"):

        # don't recursively read the master file
        if subject_file.name.lower() == "all_subjects.xlsx":
            continue

        subject_name = subject_file.stem.lower()

        xls = pd.ExcelFile(subject_file)

        if "ALL_GRADES" not in xls.sheet_names:
            JobLogger.log(f"Skipping {subject_file.name} (no ALL_GRADES)")
            continue

        df = pd.read_excel(subject_file, sheet_name="ALL_GRADES")

        new_sheet = f"all_grades_{subject_name}"

        # Excel sheet names max 31 chars
        df.to_excel(writer, sheet_name=new_sheet[:31], index=False)

        JobLogger.log(f"Added {new_sheet} to all_subjects.xlsx")

JobLogger.log("\n✅ Finished building per-subject files and all_subjects.xlsx")

# --------------------------------------------------
# STEP 4: BUILD PERFORMANCE SUMMARY IN all_subjects.xlsx
# --------------------------------------------------

summary_rows = []

# reopen the master file we just created
xls = pd.ExcelFile(MASTER_FILE)

for sheet in xls.sheet_names:

    if not sheet.lower().startswith("all_grades_"):
        continue

    subject = sheet.replace("all_grades_", "")

    df = pd.read_excel(MASTER_FILE, sheet_name=sheet)

    if "Performance (%)" not in df.columns:
        JobLogger.log(f"Skipping {sheet} (no Performance (%) column)")
        continue

    # force numeric in case Excel got cute
    perf = pd.to_numeric(df["Performance (%)"], errors="coerce")

    avg_perf = perf.mean()
    if pd.isna(avg_perf):
        avg_perf = 0

    summary_rows.append({
        "Subject": subject,
        "Avg Performance": round(avg_perf, 0)
    })

summary_df = pd.DataFrame(summary_rows)

# append Perf_summary sheet
with pd.ExcelWriter(
    MASTER_FILE,
    engine="openpyxl",
    mode="a",
    if_sheet_exists="replace"
) as writer:

    summary_df.to_excel(writer, sheet_name="Perf_summary", index=False)

JobLogger.log("\n📊 Added Perf_summary to all_subjects.xlsx")

