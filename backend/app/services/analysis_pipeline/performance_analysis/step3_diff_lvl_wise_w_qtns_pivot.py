import pandas as pd
import numpy as np
from app.services.pipeline_state import get_pipeline_state, update_pipeline_state
from app.utils.excel_export import export_snapshot
from app.core.logging_utils import JobLogger

def run_step3():
    JobLogger.log("Starting Step 3 (In-Memory)...")
    
    state = get_pipeline_state()
    # Input: step0 data (contains _formatted_long)
    step0_data = state.get("step0", {})
    
    if not step0_data:
        JobLogger.log("Error: Step 0 data not found for Step 3.")
        return

    # Initialize step3 state
    state["step3"] = {}

    for filename, sheets_dict in step0_data.items():
        if filename not in state["step3"]:
            state["step3"][filename] = {}
            
        for sheet_name, df in sheets_dict.items():
            # Only operate on long sheets
            if not sheet_name.endswith("_formatted_long"):
                continue

            if df.empty:
                continue

            # Copy
            df = df.copy()

            # Base name: english_formatted_long -> english
            base_name = sheet_name.replace("_formatted_long", "")

            # ---- Difficulty-wise aggregation ----
            if "Difficulty" not in df.columns or "Credit" not in df.columns or "Question" not in df.columns:
                 JobLogger.log(f"Skipping {sheet_name}: missing columns")
                 continue

            diff_df = (
                df.groupby("Difficulty")
                  .agg(
                      Questions=("Question", lambda x: ",".join(sorted(map(str, x.unique())))),
                      Avg_Perf=("Credit", "mean"),
                  )
                  .reset_index()
            )

            diff_df["Avg Performance (%)"] = (
                diff_df["Avg_Perf"] * 100
            ).fillna(0) # Handle NaN

            diff_df["Avg Performance (%)"] = diff_df["Avg Performance (%)"].replace([np.inf, -np.inf], 0)
            diff_df["Avg Performance (%)"] = diff_df["Avg Performance (%)"].round(0).astype(int)

            diff_df.drop(columns=["Avg_Perf"], inplace=True)

            out_sheet = f"{base_name}_qlvl"
            
            # Store in step3
            state["step3"][filename][out_sheet] = diff_df

    # Export Snapshot
    export_snapshot("step3_difficulty", state["step3"])
    JobLogger.log("Finished Step 3 (In-Memory).")

if __name__ == "__main__":
    run_step3()
