import pandas as pd
from pathlib import Path
from app.core.logging_utils import JobLogger

DATA_DIR = Path("data")   # change if needed

excel_files = DATA_DIR.glob("*.xlsx")

for input_file in excel_files:

    JobLogger.log(f"Creating difficulty-level pivots in {input_file.name}...")

    xls = pd.ExcelFile(input_file)

    with pd.ExcelWriter(
        input_file,
        engine="openpyxl",
        mode="a",
        if_sheet_exists="replace",
    ) as writer:

        for sheet in xls.sheet_names:

            # Only operate on long sheets
            if not sheet.endswith("_formatted_long"):
                continue

            df = pd.read_excel(input_file, sheet_name=sheet)

            if df.empty:
                continue

            # Base name: english_formatted_long -> english
            base_name = sheet.replace("_formatted_long", "")

            # ---- Difficulty-wise aggregation ----
            diff_df = (
                df.groupby("Difficulty")
                  .agg(
                      Questions=("Question", lambda x: ",".join(sorted(x.unique()))),
                      Avg_Perf=("Credit", "mean"),
                  )
                  .reset_index()
            )

            diff_df["Avg Performance (%)"] = (
                diff_df["Avg_Perf"] * 100
            ).fillna(0) # Handle NaN

            import numpy as np
            diff_df["Avg Performance (%)"] = diff_df["Avg Performance (%)"].replace([np.inf, -np.inf], 0)

            diff_df["Avg Performance (%)"] = diff_df["Avg Performance (%)"].round(0).astype(int)

            diff_df.drop(columns=["Avg_Perf"], inplace=True)

            out_sheet = f"{base_name}_qlvl"

            diff_df.to_excel(writer, sheet_name=out_sheet, index=False)

            JobLogger.log(f"  → wrote {out_sheet}")

    JobLogger.log(f"Finished {input_file.name}")

JobLogger.log("All difficulty-level sheets created.")
