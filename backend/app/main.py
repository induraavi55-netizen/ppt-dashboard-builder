import os
from fastapi import FastAPI

from app.api import (
    routes_upload,
    routes_export,
    routes_project,
    routes_template,
)

from app.core.db import Base, engine
import app.models  # force model registration

# Disable docs if env flag is set
disable_docs = os.environ.get("DISABLE_DOCS") == "true"

app = FastAPI(
    title="PPT Dashboard Builder",
    docs_url=None if disable_docs else "/docs",
    redoc_url=None if disable_docs else "/redoc",
)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_upload.router)
app.include_router(routes_export.router)
app.include_router(routes_project.router)
app.include_router(routes_template.router)

# TEMP: auto-create tables on startup
Base.metadata.create_all(bind=engine)



