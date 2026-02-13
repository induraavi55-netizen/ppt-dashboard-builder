import os
from fastapi import FastAPI

from app.api import (
    routes_upload,
    routes_export,
    routes_project,
    routes_template,
    routes_pipeline,
)

from app.core.db import Base, engine
import app.models  # force model registration

app = FastAPI(
    title="PPT Dashboard Builder",
)

@app.get("/")
def root():
    return {"status": "backend working"}

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173","https://ncp-analysis-pipeline-79jwq21y-doomsworks-projects.vercel.app",],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

app.include_router(routes_upload.router)
app.include_router(routes_export.router)
app.include_router(routes_project.router)
app.include_router(routes_template.router)
app.include_router(routes_pipeline.router)

# TEMP: auto-create tables on startup
Base.metadata.create_all(bind=engine)

@app.on_event("startup")
async def startup_event():
    from app.core.db import SessionLocal
    from app.services.pipeline_orchestrator import PipelineOrchestrator
    
    db = SessionLocal()
    try:
        # Reset upload state on boot
        # This prevents "Uploaded Data Detected" from showing stale data after restart
        orchestrator = PipelineOrchestrator()
        orchestrator.reset_pipeline_state(db)
        orchestrator.update_pipeline_state("dataset_uploaded", "false", db)
        print(" [Startup] Pipeline state reset (cleared all steps, uploaded=false)")
    except Exception as e:
        print(f" [Startup] Warning: Failed to reset pipeline state: {e}")
    finally:
        db.close()



