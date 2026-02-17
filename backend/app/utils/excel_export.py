from pathlib import Path
import pandas as pd
from app.core.logging_utils import JobLogger

# Define output directory relative to backend root (assuming CWD is backend/app/..)
# Actually, the pipeline runs with CWD = e:\ppt-dashboard-builder\backend
# So outputs should be in e:\ppt-dashboard-builder\backend\outputs
OUTPUT_DIR = Path("outputs") 

def export_snapshot(step_name: str, data: dict):
    """
    Exports a dictionary of DataFrames to an Excel file.
    data structure: { "sheet_name": pd.DataFrame }
    """
    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        output_file = OUTPUT_DIR / f"{step_name}.xlsx"
        
        # Check if data is empty
        if not data:
            JobLogger.log(f"Warning: No data to export for {step_name}")
            return

        with pd.ExcelWriter(output_file, engine="xlsxwriter") as writer:
            for sheet_name, content in data.items():
                # Handle nested dicts (e.g. step0 has filename -> sheetname -> df)
                # If content is a DataFrame, write it.
                # If content is a dict, we might need to flatten or skip?
                # The prompt implies: pipeline_state["step1"] = processed_data
                # export_snapshot("step1_performance", pipeline_state["step1"])
                
                # CASE 1: Content is DataFrame
                if isinstance(content, pd.DataFrame):
                    safe_name = str(sheet_name)[:31]
                    content.to_excel(writer, sheet_name=safe_name, index=False)
                
                # CASE 2: Content is Dict (e.g. step0 structure: filename -> { formatted: df, ... })
                # We can't write a dict to a sheet.
                # We likely need to export separate files or merge sheets?
                # For Step 0, we might want to iterate file keys?
                # "pipeline_state['step0'][file.name] = { 'formatted': ..., ... }"
                # If we pass all of pipeline_state['step0'] to this function, it's a dict of dicts.
                # That won't fit "sheet_name, df in data.items()".
                # Loop needs to handle this.
                
                # Special handling for Step 0 nested loading?
                # Or maybe Step 0 calls export for each file?
                # The user prompt: "Call: export_snapshot('step0_formatted', pipeline_state['step0'])"
                # This implies the custom exporter logic needs to handle the nesting OR flatten it.
                # If I flatten: "Filename_Sheetname"
                elif isinstance(content, dict):
                     for sub_sheet, sub_df in content.items():
                        if isinstance(sub_df, pd.DataFrame):
                            # Construct a name: "Key_SubSheet"
                            # E.g. "Grade5_formatted"
                            safe_name = f"{sheet_name}_{sub_sheet}"[:31]
                            sub_df.to_excel(writer, sheet_name=safe_name, index=False)
                        else:
                            # Too deep?
                            pass

        JobLogger.log(f"Exported snapshot: {output_file}")
        
    except Exception as e:
        JobLogger.log(f"Failed to export snapshot {step_name}: {e}")
        print(f"Export Error: {e}")
