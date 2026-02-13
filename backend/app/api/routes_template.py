import os
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException

router = APIRouter(prefix="/templates", tags=["template"])

TEMPLATE_DIR = Path("templates")
TEMPLATE_PATH = TEMPLATE_DIR / "current_template.pptx"

@router.post("/upload")
async def upload_template(file: UploadFile = File(...)):
    if not file.filename.endswith(".pptx"):
        raise HTTPException(status_code=400, detail="Only .pptx files are allowed")
    
    TEMPLATE_DIR.mkdir(exist_ok=True)
    
    try:
        content = await file.read()
        with open(TEMPLATE_PATH, "wb") as f:
            f.write(content)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save template: {str(e)}")

@router.get("/check")
def check_template():
    # Priority 1: Env Var
    env_path = os.environ.get("PPT_TEMPLATE_PATH")
    if env_path and os.path.exists(env_path):
        return {"configured": True, "source": "env"}
    
    # Priority 2: Uploaded file
    if TEMPLATE_PATH.exists():
        return {"configured": True, "source": "upload"}
    
    return {"configured": False}
