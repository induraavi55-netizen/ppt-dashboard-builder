from pydantic import BaseModel
from typing import List

class PipelineConfig(BaseModel):
    exam_grades: List[int]
    participating_schools: List[str]
