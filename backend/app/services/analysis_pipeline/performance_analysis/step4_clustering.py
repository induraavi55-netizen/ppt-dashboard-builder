import pandas as pd
from app.services.pipeline_state import get_pipeline_state, update_pipeline_state
from app.utils.excel_export import export_snapshot
from app.core.logging_utils import JobLogger

def run_step4():
    JobLogger.log("Starting Step 4 (In-Memory)...")
    
    state = get_pipeline_state()
    # Input: step1 data (contains updated _formatted sheets with Performance %)
    step1_data = state.get("step1", {})
    
    if not step1_data:
        JobLogger.log("Error: Step 1 data not found for Step 4. Check if Step 1 ran successfully.")
        return

    # Initialize step4 state
    # Structure:
    # {
    #    "SubjectName": { "Grade X": df, "ALL_GRADES": df },
    #    "master": { "all_grades_Subject": df, "Perf_summary": df }
    # }
    state["step4"] = {}
    state["step4"]["master"] = {}

    # --------------------------------------------------
    # STEP 1: COLLECT *_formatted SHEETS
    # --------------------------------------------------
    
    subject_buckets = {}

    for filename, sheets_dict in step1_data.items():
        file_stem = filename.replace(".xlsx", "") # Approximation or use Path(filename).stem logic if strictly needed, but keys are usually filenames

        for sheet_name, df in sheets_dict.items():
            sheet_clean = sheet_name.strip().lower()
            
            if sheet_clean.endswith("_formatted"):
                base_subject = sheet_clean.replace("_formatted", "")
                
                # Check if df is valid
                if df is None or df.empty:
                    continue

                subject_buckets.setdefault(base_subject, []).append(
                    (file_stem, df)
                )

    # --------------------------------------------------
    # STEP 2: BUILD SUBJECT BUCKETS + ALL_GRADES
    # --------------------------------------------------
    
    for subject, items in subject_buckets.items():
        if not items:
            continue
            
        if subject not in state["step4"]:
            state["step4"][subject] = {}
            
        combined_frames = []
        
        for file_stem, df in items:
            # Store individual grade sheet
            # Key: "Grade 5" (or file_stem)
            state["step4"][subject][file_stem] = df
            
            # keep for combined view
            temp = df.copy()
            temp["Source Grade File"] = file_stem
            combined_frames.append(temp)
            
        # ---- create ALL_GRADES sheet ----
        if combined_frames:
            combined_df = pd.concat(combined_frames, ignore_index=True)
            state["step4"][subject]["ALL_GRADES"] = combined_df
            
            # --------------------------------------------------
            # STEP 3: ADD TO MASTER (all_subjects)
            # --------------------------------------------------
            new_sheet = f"all_grades_{subject}"
            state["step4"]["master"][new_sheet] = combined_df

    # --------------------------------------------------
    # STEP 4: BUILD PERFORMANCE SUMMARY IN MASTER
    # --------------------------------------------------
    
    summary_rows = []
    
    for sheet_name, df in state["step4"]["master"].items():
        if not sheet_name.startswith("all_grades_"):
            continue
            
        subject = sheet_name.replace("all_grades_", "")
        
        if "Performance (%)" not in df.columns:
            continue
            
        # force numeric
        perf = pd.to_numeric(df["Performance (%)"], errors="coerce")
        
        avg_perf = perf.mean()
        if pd.isna(avg_perf):
            avg_perf = 0
            
        summary_rows.append({
            "Subject": subject,
            "Avg Performance": round(avg_perf, 0)
        })
        
    if summary_rows:
        summary_df = pd.DataFrame(summary_rows)
        state["step4"]["master"]["Perf_summary"] = summary_df

    # Export Snapshot
    # This will create outputs/step4_clustered.xlsx
    # containing all subjects and master sheets flattened.
    export_snapshot("step4_clustered", state["step4"])
    JobLogger.log("Finished Step 4 (In-Memory).")

if __name__ == "__main__":
    run_step4()

