from sqlalchemy import Column, String, DateTime, Text, Enum
import uuid
from datetime import datetime
import enum
import json

from app.core.db import Base

class JobStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class PipelineJob(Base):
    __tablename__ = "pipeline_jobs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    step_name = Column(String(50), nullable=False, index=True)
    status = Column(Enum(JobStatus), nullable=False, default=JobStatus.PENDING, index=True)
    output_files = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    logs = Column(Text, nullable=True)  # Storing as JSON string or text blob for simplicity
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    def to_dict(self):
        return {
            "id": self.id,
            "step_name": self.step_name,
            "status": self.status.value,
            "output_files": json.loads(self.output_files) if self.output_files else [],
            "error_message": self.error_message,
            "logs": json.loads(self.logs) if self.logs else [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
