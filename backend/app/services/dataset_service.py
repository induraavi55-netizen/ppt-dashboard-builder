def detect_dataset_type_from_name(name: str) -> str:
    name = name.lower()
    
    if "sub_wise" in name or "subwise" in name:
        return "subwise"
    
    if name.endswith("_lo"):
        return "lo"
    
    if name.endswith("_qlvl"):
        return "qlvl"
    
    if "reg_vs_part_grade" in name:
        return "reg_vs_part_grade"
    
    if "reg_vs_part_schl" in name:
        return "reg_vs_part_school"
    
    if "perf_summary" in name or "summary" in name:
        return "perf_summary"
    
    return "generic"
