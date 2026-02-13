from pydantic import BaseModel, Field
from typing import List, Dict, Any
from uuid import UUID


class UploadResponse(BaseModel):
    project_id: UUID
    dataset_ids: List[UUID]


class DatasetOut(BaseModel):
    id: UUID
    name: str
    columns: list
    data_schema: Dict[str, Any] = Field(..., alias="schema")
    preview: list


# -----------------------------
# SLIDE PAYLOAD
# -----------------------------

class SlidePayload(BaseModel):
    slideId: str
    position: int
    generated: bool | None = None
    type: str
    title: str | None = None
    dataset_id: str | None = None
    elements: List[Dict[str, Any]]


class SaveProjectRequest(BaseModel):
    project_id: str
    slides: List[SlidePayload]


class RegenerateProjectRequest(BaseModel):
    project_id: str


class MarkManualSlideRequest(BaseModel):
    project_id: str
    slide_id: str
