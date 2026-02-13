
import asyncio
import os
import sys
from pathlib import Path
import pandas as pd

# Add app to path
sys.path.append(os.getcwd())

from app.services.excel_parser import looks_like_pivot, detect_schema, _clean_dataframe, _coerce_percent_columns

# Mock UploadFile
class MockFile:
    def __init__(self, path):
        self.path = path
    
    async def read(self):
        with open(self.path, "rb") as f:
            return f.read()

async def debug_parse():
    file_path = Path("data/uploadable data.xlsx")
    if not file_path.exists():
        print(f"ERROR: {file_path} does not exist!")
        return

    print(f"Scanning {file_path}...")
    xls = pd.ExcelFile(file_path)
    
    for sheet in xls.sheet_names:
        print(f"\n--- SHEET: {sheet} ---")
        df = pd.read_excel(xls, sheet_name=sheet)
        print(f"Shape: {df.shape}")
        print(f"Columns: {df.columns.tolist()}")
        
        # 1. Clean
        df = _clean_dataframe(df)
        print(f"Cleaned Shape: {df.shape}")
        
        # 2. Pivot Check
        is_pivot = looks_like_pivot(df)
        print(f"looks_like_pivot: {is_pivot}")
        
        if not is_pivot:
            print("REASON: Rejected by looks_like_pivot")
            # Replicating logic from looks_like_pivot to see specific fail
            df_drop = df.dropna(axis=1, how="all")
            if df_drop.shape[0] < 1 or df_drop.shape[1] < 2:
                print(f"  -> Too small: {df_drop.shape}")
            
            numeric_cols = df_drop.select_dtypes(include="number").columns
            if len(numeric_cols) == 0:
                print(f"  -> No numeric columns")
                
            text_cols = df_drop.select_dtypes(include="object").columns
            if len(text_cols) > 8:
                print(f"  -> Too many text cols: {len(text_cols)}")
            continue
            
        # 3. Schema
        schema = detect_schema(df)
        print(f"Schema: {schema}")
        
        # 4. Success
        print("RESULT: ACCEPTED")

if __name__ == "__main__":
    asyncio.run(debug_parse())
