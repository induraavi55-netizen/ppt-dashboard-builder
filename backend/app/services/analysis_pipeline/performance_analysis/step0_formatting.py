import pandas as pd
from pathlib import Path
from app.core.logging_utils import JobLogger

# Folder containing your Excel files
DATA_DIR = Path("data")   # change to your folder path

# All Excel files in that folder
excel_files = [
    f for f in DATA_DIR.glob("*.xlsx")
    if f.name.lower().startswith("grade_")
]


for input_file in excel_files:


    JobLogger.log(f"Processing {input_file.name}...")

    xls = pd.ExcelFile(input_file)

    with pd.ExcelWriter(
        input_file,
        engine="openpyxl",
        mode="a",
        if_sheet_exists="replace",
    ) as writer:

        for sheet in xls.sheet_names:

            # Skip already processed sheets
            if sheet.endswith("_formatted") or sheet.endswith("_formatted_long"):
                continue

            df = pd.read_excel(input_file, sheet_name=sheet)

            # ---------- STEP 1: CREATE _formatted ----------

            base_cols = [
                "District",
                "SchoolName",
                "Student LoginId",
                "Subject",
            ]

            diff_cols = [c for c in df.columns if c.endswith("_difficulty_level")]
            lo_cols = [c for c in df.columns if c.endswith("_LO")]
            credit_cols = [c for c in df.columns if c.endswith("_credit")]

            selected_cols = base_cols + diff_cols + lo_cols + credit_cols
            selected_cols = [c for c in selected_cols if c in df.columns]

            formatted_df = df[selected_cols].copy()

            # Create school id
            formatted_df["school id"] = (
                formatted_df["Student LoginId"]
                .astype(str)
                .str[:6]
            )

            # Reorder
            cols = formatted_df.columns.tolist()
            idx = cols.index("Student LoginId") + 1
            cols.insert(idx, cols.pop(cols.index("school id")))
            formatted_df = formatted_df[cols]

            formatted_sheet = f"{sheet}_formatted"
            formatted_df.to_excel(writer, sheet_name=formatted_sheet, index=False)

            # ---------- STEP 2: CREATE _formatted_long ----------

            base_cols_long = [
                "District",
                "SchoolName",
                "Student LoginId",
                "school id",
                "Subject",
            ]

            records = []

            for i in range(1, 21):

                lo = f"Q{i}_LO"
                diff = f"Q{i}_difficulty_level"
                credit = f"Q{i}_credit"

                if all(c in formatted_df.columns for c in [lo, diff, credit]):

                    temp = formatted_df[base_cols_long + [lo, diff, credit]].copy()

                    temp["Question"] = f"Q{i}"

                    temp.rename(
                        columns={
                            lo: "LO",
                            diff: "Difficulty",
                            credit: "Credit",
                        },
                        inplace=True,
                    )

                    records.append(temp)

            if records:
                long_df = pd.concat(records, ignore_index=True)

                long_sheet = f"{sheet}_formatted_long"
                long_df.to_excel(writer, sheet_name=long_sheet, index=False)

    JobLogger.log(f"Finished {input_file.name}")

JobLogger.log("All files processed successfully.")
