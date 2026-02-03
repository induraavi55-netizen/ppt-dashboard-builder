import uuid
from sqlalchemy import Column, String, Integer, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.db import Base


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)

    name = Column(String, nullable=False)

    schema = Column(JSON, nullable=False)

    columns = Column(JSON, nullable=False)

    row_count = Column(Integer, nullable=False)

    preview = Column(JSON, nullable=False)

    project = relationship("Project", back_populates="datasets")
