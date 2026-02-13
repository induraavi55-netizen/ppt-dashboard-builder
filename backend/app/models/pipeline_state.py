from sqlalchemy import Column, String, DateTime
from datetime import datetime

from app.core.db import Base

class PipelineState(Base):
    __tablename__ = "pipeline_state"
    
    key = Column(String(100), primary_key=True)
    value = Column(String(20), nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
