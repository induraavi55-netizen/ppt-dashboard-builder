import pandas as pd
import numpy as np
from app.services.pipeline_state import get_pipeline_state, update_pipeline_state
from app.utils.excel_export import export_snapshot
from app.core.logging_utils import JobLogger

def run_step2():
    JobLogger.log("Starting Step 2 (In-Memory)...")
    
    state = get_pipeline_state()
    # Input: step0 data (contains _formatted_long)
    step0_data = state.get("step0", {})
    
    if not step0_data:
        JobLogger.log("Error: Step 0 data not found for Step 2.")
        return

    # Initialize step2 state
    state["step2"] = {}

    for filename, sheets_dict in step0_data.items():
        if filename not in state["step2"]:
            state["step2"][filename] = {}
            
        for sheet_name, df in sheets_dict.items():
            # Only operate on long sheets
            if not sheet_name.endswith("_formatted_long"):
                continue

            if df.empty:
                continue
                
            # Copy to avoid mutating step0 state if we modified it (we don't here, but good practice)
            df = df.copy()

            # Base name: english_formatted_long -> english
            base_name = sheet_name.replace("_formatted_long", "")

            # ---- LO-wise aggregation ----
            # Ensure columns exist
            if "LO" not in df.columns or "Credit" not in df.columns or "Question" not in df.columns:
                JobLogger.log(f"Skipping {sheet_name}: missing required columns")
                continue

            lo_df = (
                df.groupby("LO")
                  .agg(
                      Questions=("Question", lambda x: ",".join(sorted(map(str, x.unique())))),
                      Avg_Perf=("Credit", "mean"),
                  )
                  .reset_index()
            )

            lo_df["Avg Performance (%)"] = (
                lo_df["Avg_Perf"] * 100
            ).fillna(0)
            
            lo_df["Avg Performance (%)"] = lo_df["Avg Performance (%)"].replace([np.inf, -np.inf], 0)
            lo_df["Avg Performance (%)"] = lo_df["Avg Performance (%)"].round(0).astype(int)

            lo_df.drop(columns=["Avg_Perf"], inplace=True)

            # ---- Sort descending by performance ----
            lo_df = lo_df.sort_values(
                by=["Avg Performance (%)","LO"],
                ascending=[False,True]
            )

            out_sheet = f"{base_name}_lo"
            
            # Store in step2
            state["step2"][filename][out_sheet] = lo_df

    # Export Snapshot
    export_snapshot("step2_lo", state["step2"])
    JobLogger.log("Finished Step 2 (In-Memory).")

if __name__ == "__main__":
    run_step2()
