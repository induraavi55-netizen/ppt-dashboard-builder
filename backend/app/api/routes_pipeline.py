from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.services.pipeline_orchestrator import PipelineOrchestrator
from app.services.excel_parser import parse_excel
from app.models.project import Project
from app.models.dataset import Dataset
from app.models.slide import Slide
from app.services.slide_generator import generate_slides
from pathlib import Path
import shutil
import zipfile
import os
import time
from fastapi import UploadFile, File


router = APIRouter(prefix="/pipeline", tags=["pipeline"])
orchestrator = PipelineOrchestrator()


# RE-IMPORT NEEDED MODULES AT TOP LEVEL IF NOT ALREADY THERE, BUT WE ARE EDITING END-OF-FILE AREA OR SPECIFIC FUNCTIONS
# The user asked to modify scan_pipeline_data and add debug endpoint.

# We need `re` for regex validation.

from app.schemas.pipeline_config import PipelineConfig
from app.core.pipeline_config import PIPELINE_CONFIG

@router.post("/config")
def update_pipeline_config(config: PipelineConfig):
    PIPELINE_CONFIG["exam_grades"] = config.exam_grades
    PIPELINE_CONFIG["participating_schools"] = config.participating_schools
    return {"status": "ok", "config": PIPELINE_CONFIG}


@router.get("/config")
def get_pipeline_config():
    return PIPELINE_CONFIG

# We need `re` for regex validation.
import re

def scan_pipeline_data(data_dir: Path):
    """
    Scans directory for required pipeline files.
    Returns (reg_file, grade_files, all_files)
    Scans ONLY the root data_dir (non-recursive).
    """
    reg_file = None
    grade_files = []
    all_files = []

    if not data_dir.exists():
        return None, [], []

    # Use iterdir() for non-recursive scan
    for full in data_dir.iterdir():
        if not full.is_file():
            continue
            
        f = full.name
        # Store relative paths for API response
        rel_path = f # Since it's root, rel_path is just filename
        all_files.append(rel_path)

        if f == "REG VS PART.xlsx":
            reg_file = rel_path

        # Regex for Grade files: Grade 5.xlsx, Grade_5.xlsx, Grade-5.xlsx
        # Case insensitive match
        if re.match(r"^Grade[_\s-]?\d+\.xlsx$", f, re.IGNORECASE):
            grade_files.append(rel_path)

    return reg_file, grade_files, all_files

@router.get("/data-files")
async def list_data_files(db: Session = Depends(get_db)):
    """
    Source of truth for data files. 
    Returns uploaded=True ONLY if:
    1. 'dataset_uploaded' flag in DB is 'true'
    2. Required files actually exist on disk (double verification)
    """
    # 1. Check DB State
    state_entry = orchestrator.get_pipeline_state_value("dataset_uploaded", db)
    if state_entry != "true":
        return {
            "uploaded": False,
            "files": [],
            "debug_info": {"reason": "db_flag_false", "flag_value": state_entry}
        }

    data_dir = orchestrator.base_dir / "data"
    
    # 2. Scan disk using shared helper
    reg_file, grade_files, all_files = scan_pipeline_data(data_dir)
    
    # 3. Strict Validation Rule
    is_valid = (reg_file is not None) and (len(grade_files) > 0)
    
    return {
        "uploaded": is_valid,
        "files": all_files,
        "debug_info": {
            "reg_found": reg_file is not None,
            "grades_found": len(grade_files)
        }
    }


def safe_rmtree(path: Path):
    """
    Robustly delete directory with retries.
    Handles Windows file locking issues.
    """
    if not path.exists():
        return
        
    # Retry 3 times as requested
    for i in range(3):
        try:
            shutil.rmtree(path)
            return
        except PermissionError:
            time.sleep(0.5)
        except Exception as e:
            print(f"Error checking/deleting {path}: {e}")
            time.sleep(0.5)
            
    # Final attempt or raise with clear error
    try:
        shutil.rmtree(path)
    except Exception as e:
         raise HTTPException(409, f"Data directory is locked. Close Excel files and retry upload. Error: {e}")

@router.get("/debug-files")
async def debug_pipeline_files(db: Session = Depends(get_db)):
    """
    Temporary debug endpoint to inspect server state.
    """
    from app.models.pipeline_job import PipelineJob, JobStatus
    
    data_dir = orchestrator.base_dir / "data"
    running_jobs = db.query(PipelineJob).filter(PipelineJob.status == JobStatus.RUNNING).all()
    
    files_info = []
    if data_dir.exists():
        for root, _, files in os.walk(data_dir):
            for f in files:
                full = Path(root) / f
                try:
                    size = full.stat().st_size
                    files_info.append({"path": str(full), "size": size})
                except:
                    files_info.append({"path": str(full), "error": "Access Denied"})

    return {
        "cwd": os.getcwd(),
        "data_dir_absolute": str(data_dir.absolute()),
        "data_dir_exists": data_dir.exists(),
        "files": files_info,
        "running_jobs": [j.to_dict() for j in running_jobs]
    }

@router.post("/upload")
async def upload_pipeline_data(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Uploads a ZIP file, clears old data, extracts new data.
    Strictly returns success/failure.
    """
    import traceback
    import time
    import gc
    from app.models.pipeline_job import PipelineJob, JobStatus
    
    print("==== PIPELINE UPLOAD ENDPOINT HIT ====")
    print(f"[Upload] Received file: {file.filename}")
    
    # 0. Check for running jobs
    running_jobs = db.query(PipelineJob).filter(PipelineJob.status == JobStatus.RUNNING).count()
    if running_jobs > 0:
        raise HTTPException(
            status_code=400, # Changed to 400 as per prompt request (previously 409)
            detail="Cannot upload while pipeline is running."
        )
    
    # Reset Session State - dataset is invalid until fully replaced
    orchestrator.reset_pipeline_state(db)
    orchestrator.update_pipeline_state("dataset_uploaded", "false", db)
    
    data_dir = orchestrator.base_dir / "data"
    
    try:
        # 1. Strict Reset: Clear existing data directory
        if data_dir.exists():
            print("[Upload] Clearing existing data directory...")
            # Force GC before delete attempt
            gc.collect()
            safe_rmtree(data_dir)

        data_dir.mkdir(parents=True)
        
        # 2. Save temp zip
        temp_zip = data_dir / "temp.zip"
        try:
            with open(temp_zip, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            print(f"[Upload] ZIP file saved to {temp_zip}")
                
            # 3. Extract
            print(f"[Upload] Extracting to {data_dir}...")
            with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
                zip_ref.extractall(data_dir)
            print("[Upload] Extraction complete.")

            # 3.5 Flatten 'data/' if it was nested in ZIP
            # Often ZIPs created by right-click -> Compress 'data' result in 'data/REG VS PART.xlsx' inside extraction
            items = list(data_dir.iterdir())
            items = [x for x in items if x.name != "temp.zip"] # Ignore temp zip
            
            # If we have exactly one folder named 'data' (or potentially any single folder), flatten it
            if len(items) == 1 and items[0].is_dir():
                nested_dir = items[0]
                print(f"[Upload] Detected nested directory '{nested_dir.name}'. Flattening...")
                
                for nested_item in nested_dir.iterdir():
                    # Move item up to data_dir
                    destination = data_dir / nested_item.name
                    # Handle collision if weirdly exists (shouldn't on clean extract)
                    if not destination.exists():
                        shutil.move(str(nested_item), str(destination))
                
                # Remove the now-empty nested dir
                shutil.rmtree(nested_dir)
                print("[Upload] Flattening complete.")

            # Sanity Log
            print(f"[Upload] DATA DIR CONTENTS: {[x.name for x in data_dir.iterdir()]}")
            
            # 4. VALIDATION: Use shared helper
            reg_file, grade_files, all_files = scan_pipeline_data(data_dir)
            print(f"[Upload] Validation results: reg_file={reg_file}, grade_files={len(grade_files)}")
            
            if not reg_file:
                raise HTTPException(400, "Missing required file: REG VS PART.xlsx")
                
            if not grade_files:
                raise HTTPException(400, "Missing required Grade files (e.g. 'Grade 5.xlsx')")
                
        except zipfile.BadZipFile:
            print("[Upload] Error: Invalid ZIP file")
            if data_dir.exists():
                safe_rmtree(data_dir)
            raise HTTPException(400, "Invalid ZIP file")
        except HTTPException:
            raise # Re-raise known HTTP exceptions
        except Exception as e:
            print(f"[Upload] Error during file processing: {str(e)}")
            if data_dir.exists():
                safe_rmtree(data_dir)
            raise HTTPException(500, f"Processing Error: {str(e)}")
        finally:
            if temp_zip.exists():
                try:
                    os.remove(temp_zip)
                except:
                    pass
        
        # 5. Success State Update
        orchestrator.update_pipeline_state("dataset_uploaded", "true", db)
        print(f"[Upload] Success. Detected files: {all_files}")
        return {"success": True, "files": all_files}

    except HTTPException as he:
        print(f"[Upload] HTTP Exception: {he.detail}")
        raise he
    except Exception as e:
        print("!!!! INTERNAL SERVER ERROR !!!!")
        traceback.print_exc()
        # Do not delete data dir on generic 500 automatically here, 
        # as safe_rmtree might fail. But we should try cleanup if we can.
        if data_dir.exists():
             try:
                 safe_rmtree(data_dir)
             except:
                 pass
        
        # Return structured error via HTTPException so frontend sees .detail
        raise HTTPException(500, f"Upload failed: {str(e)}")

# Need to import JSONResponse for the catch-all return
from fastapi.responses import JSONResponse, FileResponse

@router.post("/participation/step0")
async def run_participation_step0(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    print("==== RUN PARTICIPATION STEP 0 REQUEST RECEIVED ====")

    try:
        # 1. Verify dataset_uploaded flag
        dataset_uploaded = orchestrator.get_pipeline_state_value("dataset_uploaded", db)

        if dataset_uploaded != "true":
            print("Step0 blocked: dataset_uploaded flag is false")
            raise HTTPException(
                status_code=400,
                detail="Dataset not uploaded. Please upload data first."
            )

        # 2. Verify files exist on disk
        data_dir = orchestrator.base_dir / "data"
        reg_file, grade_files, all_files = scan_pipeline_data(data_dir)

        if not reg_file:
            print("Step0 blocked: REG VS PART.xlsx missing")
            raise HTTPException(
                status_code=400,
                detail="REG VS PART.xlsx missing. Please re-upload dataset."
            )

        if not grade_files:
            print("Step0 blocked: Grade files missing")
            raise HTTPException(
                status_code=400,
                detail="Grade files missing. Please re-upload dataset."
            )

        # 3. Prevent overlapping jobs
        from app.models.pipeline_job import PipelineJob, JobStatus

        running_jobs = db.query(PipelineJob).filter(
            PipelineJob.status == JobStatus.RUNNING
        ).count()

        if running_jobs > 0:
            print("Step0 blocked: another pipeline job running")
            raise HTTPException(
                status_code=400,
                detail="Another pipeline step is already running."
            )

        # 4. Start job safely
        job_id = orchestrator.create_job("participation-0", db)

        print(f"Step0 job created: {job_id}")

        background_tasks.add_task(
            orchestrator.run_participation_step0,
            job_id
        )

        return {
            "job_id": job_id,
            "status": "started",
            "message": "Participation analysis started successfully"
        }

    except HTTPException:
        raise

    except Exception as e:
        print(f"Step0 internal failure: {e}")

        import traceback
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=f"Failed to start participation analysis: {str(e)}"
        )


@router.post("/performance/step{step_num}")
async def run_performance_step(step_num: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    if step_num not in range(6):
        raise HTTPException(400, "Invalid step number")
    job_id = orchestrator.create_job(f"performance-{step_num}", db)
    background_tasks.add_task(orchestrator.run_performance_step, step_num, job_id)
    return {"job_id": job_id, "status": "started"}

@router.get("/status/{job_id}")
async def get_job_status(job_id: str, db: Session = Depends(get_db)):
    status = orchestrator.get_job_status(job_id, db)
    if not status:
        raise HTTPException(404, "Job not found")
    return status

@router.get("/preview/{step_name}")
async def get_step_preview(step_name: str):
    result = orchestrator.get_step_preview(step_name)
    if "error" in result:
        # Return 400 (Bad Request) or 404 (Not Found)
        # 400 implies "Step not run yet"
        raise HTTPException(400, result["error"])
    return result

    return result


@router.get("/export/{step_name}")
async def export_step_output(step_name: str):
    """
    Download output files for a given step.
    Returns a single file or a ZIP of multiple files.
    """
    try:
        files = orchestrator.get_step_output_files(step_name)
        
        if not files:
            raise HTTPException(404, "No output files found for this step")
        
        # Single file -> return directly
        if len(files) == 1:
            f = files[0]
            return FileResponse(
                path=f, 
                filename=f.name,
                media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            
        # Multiple files -> ZIP them
        # Create a temp zip in memory? Better to stream or temp file.
        # We can reuse the temp zip approach or simpler: zipfile module
        import zipfile
        import io
        from fastapi.responses import StreamingResponse
        
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in files:
                zf.write(f, arcname=f.name)
        
        zip_buffer.seek(0)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"{step_name}_output_{timestamp}.zip"
        
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={zip_filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Export Error: {e}")
        raise HTTPException(500, f"Export failed: {e}")

@router.get("/state")
async def get_pipeline_state(db: Session = Depends(get_db)):
    """
    Returns the current pipeline state.
    SAFE GUARDED: Always returns a valid JSON structure.
    """
    try:
        state = orchestrator.get_pipeline_state(db)
        # Ensure a minimal safe structure
        safe_response = state if state else {}
        
        # Ensure analysis key exists
        if "analysis" not in safe_response or safe_response["analysis"] is None:
             safe_response["analysis"] = {"steps": [], "status": "unknown"}
             
        # Ensure analysis.steps is a list
        if "steps" not in safe_response["analysis"] or not isinstance(safe_response["analysis"]["steps"], list):
             safe_response["analysis"]["steps"] = []
             
        return safe_response
        
    except Exception as e:
        print(f"Error fetching pipeline state: {e}")
        # Return fallback safe state instead of 500
        return {
            "status": "error",
            "error": str(e),
            "analysis": {
                "steps": [],
                "status": "error"
            }
        }

@router.post("/finalize")
async def finalize_pipeline(db: Session = Depends(get_db)):
    """Forward uploadable data.xlsx to PPT generation flow"""
    print("==== FINALIZATION REQUEST RECEIVED ====")
    try:
        uploadable_file = orchestrator.base_dir / "data" / "uploadable data.xlsx"
        print(f"[Finalize] Looking for file: {uploadable_file}")
        
        if not uploadable_file.exists():
            print("[Finalize] Error: File not found")
            raise HTTPException(404, "Uploadable data file not found")
        
        # Parse Excel (reuse existing logic)
        print("[Finalize] Parsing Excel...")
        with open(uploadable_file, "rb") as f:
            upload_file = UploadFile(filename="uploadable data.xlsx", file=f)
            datasets = await parse_excel(upload_file)
        
        # Create project
        print("[Finalize] Creating Project in DB...")
        project = Project(name="Analysis Pipeline Output")
        db.add(project)
        db.commit()
        db.refresh(project)
        
        # Save datasets
        print(f"[Finalize] Saving {len(datasets)} datasets...")
        dataset_outputs = []
        for d in datasets:
            ds = Dataset(
                project_id=project.id,
                name=d["name"],
                schema=d["schema"],
                columns=d["columns"],
                row_count=d["rows"],
                preview=d["preview"],
            )
            db.add(ds)
            db.flush()
            dataset_outputs.append({
                "id": str(ds.id),
                "name": ds.name,
                "columns": ds.columns,
                "schema": ds.schema,
                "preview": ds.preview,
            })
        
        db.commit()
        
        # Generate slides
        print("[Finalize] Generating Slides...")
        slides = generate_slides(project.id, dataset_outputs)
        for s in slides:
            db.add(Slide(project_id=project.id, slide_json=s, position=s["position"]))
        
        db.commit()
        
        response_payload = {"project_id": str(project.id), "slides_created": len(slides)}
        print(f"FINALIZE RETURNING: {response_payload}")
        return response_payload
        
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"[Finalize] INTERNAL ERROR: {e}")
        traceback.print_exc()
        raise HTTPException(500, f"Finalization failed: {str(e)}")
