import pandas as pd
import logging

def apply_pipeline_config_filter(df: pd.DataFrame, config):
    """
    Applies strict filtering based on the pipeline configuration.
    Filters by SchoolName and Grade range.
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

    # Ensure Grade column is numeric
    if "Grade" in df.columns:
        df["Grade"] = pd.to_numeric(df["Grade"], errors="coerce")
    else:
        # If no Grade column, we can only filter by school
        # But user requirement implies we should be filtering by grade.
        # If the file is REG VS PART, it might be wide format (grades as columns)
        # The user provided code assumes "Grade" column exists. 
        # We will proceed with the user's logic but add a check.
        pass

    filtered_parts = []

    for school in schools:
        # Handle Pydantic model or dict
        if hasattr(school, "school_name"):
            school_name = school.school_name
            from_grade = school.from_grade
            to_grade = school.to_grade
        else:
            school_name = school.get("school_name")
            from_grade = school.get("from_grade")
            to_grade = school.get("to_grade")

        # Case insensitive matching for school name
        # We will normalize both side to lower case and strip
        
        # Create a mask for the school
        # Using string methods on the series
        school_mask = df["SchoolName"].astype(str).str.strip().str.lower() == str(school_name).strip().lower()

        if "Grade" in df.columns:
            part = df[
                (school_mask)
                &
                (df["Grade"] >= from_grade)
                &
                (df["Grade"] <= to_grade)
            ].copy()
        else:
            # If no Grade column, we can only filter by school
            part = df[school_mask].copy()
        
        filtered_parts.append(part)

    if not filtered_parts:
        return df.iloc[0:0]

    filtered_df = pd.concat(filtered_parts, ignore_index=True)

    print(f"Config filter applied: {len(df)} -> {len(filtered_df)} rows")

    return filtered_df
