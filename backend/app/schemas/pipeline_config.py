from pydantic import BaseModel
from typing import List, Optional

class SchoolConfig(BaseModel):
    schoolName: str
    fromGrade: int
    toGrade: int

class PipelineConfig(BaseModel):
    useAll: bool
    schools: List[SchoolConfig] = []
    # Legacy fields (optional, to avoid breaking if older client sends them)
    exam_grades: Optional[List[int]] = None
    participating_schools: Optional[List[str]] = None
