import pandas as pd
from pathlib import Path
import re
from app.services.pipeline_state import get_pipeline_state, update_pipeline_state
from app.utils.excel_export import export_snapshot
from app.core.logging_utils import JobLogger

# ----------------------------
# PATHS
# ----------------------------
DATA_DIR = Path("data")
# We still write to "uploadable data.xlsx" in data/ for backward compatibility/Finalize step
OUTPUT_FILE = DATA_DIR / "uploadable data.xlsx"

# ----------------------------
# NORMALIZATION
# ----------------------------
def normalize_name(name: str) -> str:
    name = name.strip().lower()
    name = re.sub(r"\s+", "_", name)
    name = re.sub(r"_+", "_", name)
    return name

def safe_sheet_name(name: str) -> str:
    invalid = r'[]:*?/\\'
    for ch in invalid:
        name = name.replace(ch, "")
    return name[:31]

def run_step5():
    JobLogger.log("Starting Step 5 (In-Memory)...")
    
    state = get_pipeline_state()
    
    # Initialize step5 state
    state["step5"] = {}
    
    sheets_to_write = {}

    # ======================================================
    # 1) REG VS PART FIRST (From Disk or State if available)
    # ======================================================
    # Assuming REG VS PART is still a file output from Participation Pipeline
    reg_file = None
    for file_path in DATA_DIR.glob("*.xlsx"):
        if normalize_name(file_path.stem) == "reg_vs_part":
            reg_file = file_path
            break
            
    if reg_file:
        prefix = normalize_name(reg_file.stem)
        JobLogger.log(f"Scanning {reg_file.name}")
        try:
            xls = pd.ExcelFile(reg_file)
            for sheet in xls.sheet_names:
                norm_sheet = normalize_name(sheet)
                if norm_sheet in ["schl_wise", "grade_wise"]:
                    df = pd.read_excel(reg_file, sheet_name=sheet)
                    new_name = safe_sheet_name(f"{prefix}_{norm_sheet}")
                    sheets_to_write[new_name] = df
                    JobLogger.log(f"  → grabbed {sheet} → {new_name}")
        except Exception as e:
            JobLogger.log(f"Error reading REG VS PART: {e}")
            
    # ======================================================
    # 2) clustered/all_subjects (From Step 4 State)
    # ======================================================
    # State path: state["step4"]["master"]["Perf_summary"]
    
    step4_master = state.get("step4", {}).get("master", {})
    if "Perf_summary" in step4_master:
        df = step4_master["Perf_summary"]
        if df is not None and not df.empty:
            prefix = "all_subjects" # Hardcoded proxy for filename
            new_name = safe_sheet_name(f"{prefix}_perf_summary")
            sheets_to_write[new_name] = df
            JobLogger.log(f"  → grabbed Perf_summary from State")

    # ======================================================
    # 3) GRADE FILES (From Steps 1, 2, 3)
    # ======================================================
    # We need to iterate "Files" present in Step 1 (or 0).
    # Step 1 keys are filenames.
    
    step1_data = state.get("step1", {})
    step2_data = state.get("step2", {})
    step3_data = state.get("step3", {})
    
    # helper for sorting
    def extract_grade_num(filename: str):
        # filename like "Grade 5.xlsx"
        m = re.search(r"grade[_\s-]?(\d+)", normalize_name(filename))
        return int(m.group(1)) if m else 999

    sorted_files = sorted(step1_data.keys(), key=extract_grade_num)
    
    for filename in sorted_files:
        prefix = normalize_name(Path(filename).stem)
        JobLogger.log(f"Scanning State for {filename}")
        
        # 3a. Sub_wise_avg_perf (Step 1)
        if filename in step1_data and "Sub_wise_avg_perf" in step1_data[filename]:
             df = step1_data[filename]["Sub_wise_avg_perf"]
             new_name = safe_sheet_name(f"{prefix}_sub_wise_avg_perf")
             sheets_to_write[new_name] = df
             JobLogger.log(f"  → grabbed Sub_wise_avg_perf")

        # 3b. LO sheets (Step 2)
        if filename in step2_data:
            for sheet_name, df in step2_data[filename].items():
                if sheet_name.endswith("_lo"):
                    new_name = safe_sheet_name(f"{prefix}_{sheet_name}")
                    sheets_to_write[new_name] = df
                    JobLogger.log(f"  → grabbed {sheet_name}")

        # 3c. Qlvl sheets (Step 3)
        if filename in step3_data:
            for sheet_name, df in step3_data[filename].items():
                if sheet_name.endswith("_qlvl"):
                     new_name = safe_sheet_name(f"{prefix}_{sheet_name}")
                     sheets_to_write[new_name] = df
                     JobLogger.log(f"  → grabbed {sheet_name}")

    # Store result in state
    state["step5"] = sheets_to_write
    
    # Export Snapshot (This is the uploadable data)
    export_snapshot("step5_uploadable", state["step5"])
    
    # ----------------------------
    # WRITE FINAL OUTPUT TO DATA DIR
    # ----------------------------
    # Using export logic or manual write to ensure exact location
    JobLogger.log("\nWriting consolidated workbook to data/uploadable data.xlsx...")
    try:
        with pd.ExcelWriter(OUTPUT_FILE, engine="xlsxwriter") as writer:
            for sheet_name, df in sheets_to_write.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        JobLogger.log("Finished. uploadable data.xlsx created.")
    except Exception as e:
        JobLogger.log(f"Error writing final file: {e}")

if __name__ == "__main__":
    run_step5()
