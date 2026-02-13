import os
from fastapi import FastAPI, Request
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    routes_upload,
    routes_export,
    routes_project,
    routes_template,
    routes_pipeline,
)

from app.core.db import Base, engine
import app.models  # force model registration


# -----------------------------
# Create FastAPI app
# -----------------------------
app = FastAPI(
    title="PPT Dashboard Builder",
)


# -----------------------------
# Root test endpoint
# -----------------------------
@app.get("/")
def root():
    return {"status": "backend working"}


# -----------------------------
# GLOBAL OPTIONS HANDLER (CRITICAL FOR VERCEL CORS)
# This ensures ALL preflight requests return 200
# -----------------------------
@app.options("/{full_path:path}")
async def preflight_handler(request: Request, full_path: str):
    return Response(status_code=200)


# -----------------------------
# CORS Middleware (MUST BE BEFORE ROUTERS)
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://ncp-analysis-pipeline-79jwq21y-doomsworks-projects.vercel.app",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# -----------------------------
# Include routers
# -----------------------------
app.include_router(routes_upload.router)
app.include_router(routes_export.router)
app.include_router(routes_project.router)
app.include_router(routes_template.router)
app.include_router(routes_pipeline.router)


# -----------------------------
# Auto-create tables (temporary)
# -----------------------------
Base.metadata.create_all(bind=engine)


# -----------------------------
# Startup event
# -----------------------------
@app.on_event("startup")
async def startup_event():
    from app.core.db import SessionLocal
    from app.services.pipeline_orchestrator import PipelineOrchestrator

    db = SessionLocal()

    try:
        orchestrator = PipelineOrchestrator()

        # Reset upload state on boot
        orchestrator.reset_pipeline_state(db)
        orchestrator.update_pipeline_state("dataset_uploaded", "false", db)

        print(" [Startup] Pipeline state reset (cleared all steps, uploaded=false)")

    except Exception as e:
        print(f" [Startup] Warning: Failed to reset pipeline state: {e}")

    finally:
        db.close()
