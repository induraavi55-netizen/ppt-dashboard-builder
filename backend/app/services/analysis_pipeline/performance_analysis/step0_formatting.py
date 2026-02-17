import pandas as pd
from pathlib import Path
from app.services.pipeline_state import get_pipeline_state, update_pipeline_state
from app.utils.excel_export import export_snapshot
from app.core.logging_utils import JobLogger

# Folder containing your Excel files
DATA_DIR = Path("data") 

def run_step0():
    JobLogger.log("Starting Step 0 (In-Memory)...")
    
    state = get_pipeline_state()
    state["step0"] = {} # Initialize/Reset
    
    # All Excel files in that folder
    excel_files = [
        f for f in DATA_DIR.glob("*.xlsx")
        if f.name.lower().startswith("grade_") or f.name.lower().startswith("grade ") or f.name.lower().startswith("grade-")
    ]
    
    if not excel_files:
        JobLogger.log("No Grade files found.")
        return

    for input_file in excel_files:
        JobLogger.log(f"Processing {input_file.name}...")
        
        # Load Raw Data
        try:
            xls = pd.ExcelFile(input_file)
            
            # Store raw in state (optional, if needed by other steps or just for record)
            if input_file.name not in state["raw"]:
                state["raw"][input_file.name] = {}
                
            for sheet in xls.sheet_names:
                # Skip processed sheets if they exist in source (legacy artifact check)
                if sheet.endswith("_formatted") or sheet.endswith("_formatted_long"):
                    continue
                
                df = pd.read_excel(xls, sheet_name=sheet)
                
                # Store raw
                state["raw"][input_file.name][sheet] = df

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
                if "Student LoginId" in formatted_df.columns:
                    formatted_df["school id"] = (
                        formatted_df["Student LoginId"]
                        .astype(str)
                        .str[:6]
                    )
                    
                    # Reorder
                    cols = formatted_df.columns.tolist()
                    if "Student LoginId" in cols and "school id" in cols:
                        idx = cols.index("Student LoginId") + 1
                        cols.insert(idx, cols.pop(cols.index("school id")))
                        formatted_df = formatted_df[cols]
                
                # Store Formatted
                # Key: "Grade 5.xlsx" -> "Sheet1_formatted"
                # Initialize file dict if not exists
                if input_file.name not in state["step0"]:
                    state["step0"][input_file.name] = {}

                sheet_key_fmt = f"{sheet}_formatted"
                state["step0"][input_file.name][sheet_key_fmt] = formatted_df

                # ---------- STEP 2: CREATE _formatted_long ----------

                base_cols_long = [
                    "District",
                    "SchoolName",
                    "Student LoginId",
                    "school id",
                    "Subject",
                ]
                
                # Verify base columns exist
                current_base_long = [c for c in base_cols_long if c in formatted_df.columns]

                records = []

                for i in range(1, 101): # Arbitrary reasonable limit for questions
                    lo = f"Q{i}_LO"
                    diff = f"Q{i}_difficulty_level"
                    credit = f"Q{i}_credit"

                    if all(c in formatted_df.columns for c in [lo, diff, credit]):
                        temp = formatted_df[current_base_long + [lo, diff, credit]].copy()
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
                    # Store Long
                    sheet_key_long = f"{sheet}_formatted_long"
                    state["step0"][input_file.name][sheet_key_long] = long_df
                    
        except Exception as e:
            JobLogger.log(f"Error processing file {input_file.name}: {e}")
            raise e

    # Export Snapshot
    # Export Snapshot
    export_snapshot("step0_formatted", state["step0"])
    
    # --------------------------------------------------
    # REGISTER PREVIEW (In-Memory)
    # --------------------------------------------------
    from app.core.preview_registry import register_preview
    
    preview_sheets = []
    
    # We want to show a few representative sheets
    # "step0" is a dict of filename -> {sheetname -> df}
    # We can flatten this or just show the first file's sheets
    
    MAX_PREVIEW_ROWS = 100
    
    for filename, sheets in state["step0"].items():
        for sheet_name, df in sheets.items():
            if df is None or df.empty:
                continue
                
            # Convert to frontend-friendly format
            # Handle NaN/Inf for JSON serialization safety
            preview_df = df.head(MAX_PREVIEW_ROWS).fillna("")
            
            preview_sheets.append({
                "name": f"{filename}::{sheet_name}", # Unique name
                "columns": list(preview_df.columns),
                "rows": preview_df.to_dict(orient="records")
            })
            
            # Limit to a reasonable number of sheets for preview to avoid payload bloat
            if len(preview_sheets) >= 5:
                break
        if len(preview_sheets) >= 5:
            break
            
    register_preview("performance-0", {"sheets": preview_sheets})
    
    JobLogger.log("Finished Step 0 (In-Memory).")

if __name__ == "__main__":
    run_step0()
