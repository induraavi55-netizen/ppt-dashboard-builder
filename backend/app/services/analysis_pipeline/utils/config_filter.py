import pandas as pd
import logging

def apply_pipeline_config_filter(df: pd.DataFrame, config):
    """
    Applies strict filtering based on the pipeline configuration.
    Filters by SchoolName (case-insensitive, whitespace-safe) and Grade range.
    """
    # Safety guard
    if df is None or df.empty:
        return df

    # Handle both object and dict access for config
    use_all = getattr(config, "use_all", None)
    if use_all is None and isinstance(config, dict):
        use_all = config.get("use_all")
    
    if use_all:
        return df

    schools = getattr(config, "schools", [])
    if not schools and isinstance(config, dict):
        schools = config.get("schools", [])

    if not schools:
        # Config says "don't use all" but no schools provided -> return empty
        return df.iloc[0:0]

    # Normalize column names if needed
    if "School Name" in df.columns and "SchoolName" not in df.columns:
        df["SchoolName"] = df["School Name"]

    if "SchoolName" not in df.columns:
        print("Warning: 'SchoolName' column not found in dataframe. Skipping filter.")
        return df
        
    # User Request: Debug Logging
    print(f"Schools in data (first 10): {df['SchoolName'].unique()[:10]}")
    
    # helper to get school name from config item
    def get_school_name(s):
        return s.school_name if hasattr(s, "school_name") else s.get("school_name")

    print(f"Config schools: {[get_school_name(s) for s in schools]}")

    # Ensure Grade column is numeric if it exists
    if "Grade" in df.columns:
        df["Grade"] = pd.to_numeric(df["Grade"], errors="coerce")

    # CLEAN FILTERING
    # Create temp copy
    df = df.copy()

    # Create Normalized Column
    df["SchoolName_clean"] = (
        df["SchoolName"]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    filtered_parts = []

    for school in schools:
        # Resolve config values
        if hasattr(school, "school_name"):
            school_name = school.school_name
            from_grade = school.from_grade
            to_grade = school.to_grade
        else:
            school_name = school.get("school_name")
            from_grade = school.get("from_grade")
            to_grade = school.get("to_grade")

        school_name_clean = str(school_name).strip().lower()

        # Filter by School Name
        # We use the clean column
        mask = df["SchoolName_clean"] == school_name_clean
        
        # Filter by Grade (If exists)
        if "Grade" in df.columns:
             mask = mask & (df["Grade"] >= from_grade) & (df["Grade"] <= to_grade)
        
        part = df[mask].copy()

        print(f"Matching school '{school_name}' -> rows: {len(part)}")
        filtered_parts.append(part)

    if not filtered_parts:
        return df.iloc[0:0]

    result = pd.concat(filtered_parts, ignore_index=True)

    print(f"Final filtered rows: {len(result)}")

    # Cleanup temp column
    return result.drop(columns=["SchoolName_clean"], errors="ignore")
