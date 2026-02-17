import pandas as pd

def apply_pipeline_filter(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    """
    Applies strict filtering based on the pipeline configuration.
    
    If config["use_all"] is True, returns a copy of the dataframe.
    Otherwise, filters rows based on "SchoolName" (or "School Name") 
    and checks if "Grade" column (if present) is within range.
    
    Note: This function assumes the dataframe is in a format where:
    1. There is a column for School Name (case-insensitive check).
    2. There MAY be a column for "Grade".
    
    If the dataframe is WIDE (grades are columns), this function might need 
    adaptation or distinct handling. This implementation follows the 
    Long-Format logic typically used in the pipeline.
    """
    
    use_all = config.get("use_all", True)
    if use_all:
        return df.copy()

    schools = config.get("schools", [])
    if not schools:
        # Config says "don't use all" but no schools provided -> return empty?
        # Or return everything? Usually implies strict filtering -> empty.
        return df.iloc[0:0]

    filtered_frames = []
    
    # Normalize school column name
    school_col = "SchoolName"
    if "School Name" in df.columns:
        school_col = "School Name"
    elif "SchoolName" in df.columns:
        school_col = "SchoolName"
    else:
        # Cannot filter by school if column missing
        print("Warning: School column not found for filtering.")
        return df

    for school in schools:
        # Handle dict or Pydantic model
        if hasattr(school, "school_name"):
            s_name = school.school_name
            f_grade = school.from_grade
            t_grade = school.to_grade
        else:
            s_name = school.get("school_name", "")
            f_grade = school.get("from_grade", 0)
            t_grade = school.get("to_grade", 100)

        s_name = s_name.strip().lower()

        # mask for school
        mask = df[school_col].astype(str).str.strip().str.lower() == s_name
        
        # If "Grade" column exists, filter by grade range
        if "Grade" in df.columns:
            mask = mask & (df["Grade"] >= f_grade) & (df["Grade"] <= t_grade)
            
        temp = df[mask]
        filtered_frames.append(temp)

    if not filtered_frames:
        return df.iloc[0:0]

    return pd.concat(filtered_frames, ignore_index=True)
