import pandas as pd
from pathlib import Path
from app.core.logging_utils import JobLogger

DATA_DIR = Path("data")   # change folder if needed


excel_files = [
    f for f in DATA_DIR.glob("*.xlsx")
    if f.name.lower().startswith("grade_")
]

for input_file in excel_files:

    JobLogger.log(f"Updating performance metrics in {input_file.name}...")

    xls = pd.ExcelFile(input_file)

    pivot_rows = []   # store summary for this file

    with pd.ExcelWriter(
        input_file,
        engine="openpyxl",
        mode="a",
        if_sheet_exists="replace",
    ) as writer:

        for sheet in xls.sheet_names:

            # Only operate on _formatted sheets
            if not sheet.endswith("_formatted"):
                continue

            df = pd.read_excel(input_file, sheet_name=sheet)

            credit_cols = [c for c in df.columns if c.endswith("_credit")]

            if not credit_cols:
                continue

            # ---- calculations ----
            df["Total Credit"] = df[credit_cols].sum(axis=1)

            # Avoid division by zero
            denom = len(credit_cols)
            if denom > 0:
                df["Performance (%)"] = (df["Total Credit"] / denom * 100).fillna(0)
            else:
                df["Performance (%)"] = 0.0
            
            # Handle potential infinities from other sources
            import numpy as np
            df["Performance (%)"] = df["Performance (%)"].replace([np.inf, -np.inf], 0)
            
            df["Performance (%)"] = df["Performance (%)"].round(0).astype(int)

            # Write back updated formatted sheet
            df.to_excel(writer, sheet_name=sheet, index=False)

            # ---- collect pivot info ----
            base_name = sheet.replace("_formatted", "")
            avg_perf = round(df["Performance (%)"].mean(), 0)

            pivot_rows.append(
                {
                    "Sheet": base_name,
                    "Average Performance (%)": int(avg_perf),
                }
            )

        # ---------- WRITE PIVOT SHEET ----------
        if pivot_rows:
            pivot_df = pd.DataFrame(pivot_rows)

            pivot_df.to_excel(writer, sheet_name="Sub_wise_avg_perf", index=False)

    JobLogger.log(f"Finished {input_file.name}")

JobLogger.log("All _formatted sheets updated and pivot sheet created.")
