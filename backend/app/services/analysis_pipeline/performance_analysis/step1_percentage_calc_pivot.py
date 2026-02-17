import pandas as pd
import numpy as np
from app.services.pipeline_state import get_pipeline_state, update_pipeline_state
from app.utils.excel_export import export_snapshot
from app.core.logging_utils import JobLogger

def run_step1():
    JobLogger.log("Starting Step 1 (In-Memory)...")
    
    state = get_pipeline_state()
    # Input: step0 data
    step0_data = state.get("step0", {})
    
    if not step0_data:
        JobLogger.log("Error: Step 0 data not found in pipeline state.")
        # Optional: Try to load from export? For now fail safely.
        return

    # Initialize step1 state
    state["step1"] = {}

    for filename, sheets_dict in step0_data.items():
        if filename not in state["step1"]:
            state["step1"][filename] = {}
            
        pivot_rows = []
        
        for sheet_name, df in sheets_dict.items():
            # Only operate on _formatted sheets
            if not sheet_name.endswith("_formatted"):
                # If it's _long, we might just pass it through or ignore?
                # Usually Step 1 only touched _formatted. 
                # Let's preserve _long in Step 1 output for completeness if needed?
                # Or just keep it in Step 0. Future steps might need it.
                # User's pattern: "Input -> Process -> Output Snapshot".
                # If Step 2 needs _long, it can read from Step 0 or Step 1.
                # Ideally Step 1 State should contain everything needed for Step 2.
                # Let's copy _long to Step 1 state as well? 
                # Or just let Step 2 read Step 0 key if missing in Step 1?
                # Cleaner to just pass applicable data. 
                # Let's just process _formatted here.
                continue
                
            # Work on a copy
            df = df.copy()
            
            credit_cols = [c for c in df.columns if c.endswith("_credit")]
            
            if not credit_cols:
                # Just copy it?
                state["step1"][filename][sheet_name] = df
                continue

            # ---- calculations ----
            df["Total Credit"] = df[credit_cols].sum(axis=1)

            # Avoid division by zero
            denom = len(credit_cols)
            if denom > 0:
                df["Performance (%)"] = (df["Total Credit"] / denom * 100).fillna(0)
            else:
                df["Performance (%)"] = 0.0
            
            # Handle potential infinities
            df["Performance (%)"] = df["Performance (%)"].replace([np.inf, -np.inf], 0)
            df["Performance (%)"] = df["Performance (%)"].fillna(0).round(0).astype(int)
            
            # Save updated df to step1
            state["step1"][filename][sheet_name] = df
            
            # ---- collect pivot info ----
            base_name = sheet_name.replace("_formatted", "")
            
            # Safe mean calculation
            mean_val = df["Performance (%)"].mean()
            if pd.isna(mean_val):
                mean_val = 0
                
            avg_perf = round(mean_val, 0)
            
            pivot_rows.append({
                "Sheet": base_name,
                "Average Performance (%)": int(avg_perf),
            })

        # Create Pivot Sheet for this file
        if pivot_rows:
            pivot_df = pd.DataFrame(pivot_rows)
            state["step1"][filename]["Sub_wise_avg_perf"] = pivot_df

    # Export Snapshot
    # Export Snapshot
    export_snapshot("step1_performance", state["step1"])
    
    # --------------------------------------------------
    # REGISTER PREVIEW
    # --------------------------------------------------
    from app.core.preview_registry import register_preview
    
    preview_sheets = []
    MAX_PREVIEW_ROWS = 100
    
    for filename, sheets in state["step1"].items():
        for sheet_name, df in sheets.items():
            if df is None or df.empty:
                continue
                
            preview_df = df.head(MAX_PREVIEW_ROWS).fillna("")
            
            preview_sheets.append({
                "name": f"{filename}::{sheet_name}",
                "columns": list(preview_df.columns),
                "rows": preview_df.to_dict(orient="records")
            })
            if len(preview_sheets) >= 5: break
        if len(preview_sheets) >= 5: break
            
    register_preview("performance-1", {"sheets": preview_sheets})
    
    JobLogger.log("Finished Step 1 (In-Memory).")

if __name__ == "__main__":
    run_step1()
