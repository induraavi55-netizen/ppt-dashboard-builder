import os
from pathlib import Path
from contextlib import contextmanager
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.core.db import SessionLocal
from app.models.pipeline_job import PipelineJob, JobStatus
from app.models.pipeline_state import PipelineState
import json
from datetime import datetime
import pandas as pd
import numpy as np
from app.core.logging_utils import job_context_var, active_job_logs

BASE_DIR = Path(__file__).parent.parent.parent

@contextmanager
def working_directory(path: Path):
    """Context manager to temporarily change working directory"""
    original_cwd = Path.cwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(original_cwd)

class PipelineOrchestrator:
    def __init__(self):
        self.base_dir = BASE_DIR
    
    def create_job(self, step_name: str, db: Session) -> str:
        job = PipelineJob(step_name=step_name, status=JobStatus.PENDING)
        db.add(job)
        db.commit()
        db.refresh(job)
        return job.id
    
    def get_job_status(self, job_id: str, db: Session) -> dict:
        job = db.query(PipelineJob).filter(PipelineJob.id == job_id).first()
        if not job:
            return None
            
        data = job.to_dict()
        
        # If running, merge with active in-memory logs
        if job.status == JobStatus.RUNNING and job_id in active_job_logs:
            # We don't save to DB until end, so just use memory
            data["logs"] = active_job_logs[job_id]
            
        return data
    
    def update_job_status(self, job_id: str, status: JobStatus, db: Session, **kwargs):
        job = db.query(PipelineJob).filter(PipelineJob.id == job_id).first()
        if job:
            job.status = status
            if status == JobStatus.RUNNING:
                job.started_at = datetime.utcnow()
            elif status in (JobStatus.COMPLETED, JobStatus.FAILED):
                job.completed_at = datetime.utcnow()
            
            for key, value in kwargs.items():
                if key == "output_files":
                    job.output_files = json.dumps(value)
                elif key == "error_message":
                    job.error_message = value
            
            # Persist logs if finishing
            if status in (JobStatus.COMPLETED, JobStatus.FAILED):
                if job_id in active_job_logs:
                    job.logs = json.dumps(active_job_logs[job_id])
                    # Clean up memory
                    del active_job_logs[job_id]
            
            db.commit()
    
    def update_pipeline_state(self, key: str, value: str, db: Session):
        try:
            state = db.query(PipelineState).filter(PipelineState.key == key).first()
            if state:
                state.value = value
                state.updated_at = datetime.utcnow()
            else:
                state = PipelineState(key=key, value=value)
                db.add(state)
            db.commit()
        except IntegrityError:
            db.rollback()
            # Race condition: duplicate key likely inserted by another thread/process
            # Retry update
            state = db.query(PipelineState).filter(PipelineState.key == key).first()
            if state:
                state.value = value
                state.updated_at = datetime.utcnow()
                db.commit()
            else:
                # Should not happen, but log if it does
                print(f"Error updating pipeline_state for key {key}: IntegrityError but not found on retry.")

    def reset_pipeline_state(self, db: Session):
        """
        Clears all pipeline state entries. 
        Used on server startup or new upload to ensure a fresh session.
        """
        try:
            # 1. Clear DB State
            db.query(PipelineState).delete()
            db.commit()
            
            # 2. Clear In-Memory State
            from app.services.pipeline_state import reset_pipeline_state as reset_in_memory_state
            reset_in_memory_state()
            print("In-Memory pipeline state reset.")
            
        except Exception as e:
            db.rollback()
            print(f"Error resetting pipeline state: {e}")

    def get_pipeline_state_value(self, key: str, db: Session) -> str:
        state = db.query(PipelineState).filter(PipelineState.key == key).first()
        return state.value if state else None
    
    def get_pipeline_state(self, db: Session) -> dict:
        states = db.query(PipelineState).all()
        result = {
            "participation": {},
            "performance": {},
            "final_file_ready": False
        }
        
        for state in states:
            if state.key.startswith("participation."):
                step = state.key.split(".")[1]
                result["participation"][step] = state.value
            elif state.key.startswith("performance."):
                step = state.key.split(".")[1]
                result["performance"][step] = state.value
            elif state.key == "final_file_ready":
                result["final_file_ready"] = state.value == "true"
        
        return result
    
    def run_participation_step0(self, job_id: str):
        # Set context for logging
        token = job_context_var.set(job_id)
        # Initialize log storage
        active_job_logs[job_id] = []
        
        db = SessionLocal()
        try:
            self.update_job_status(job_id, JobStatus.RUNNING, db)
            
            with working_directory(self.base_dir):
                from app.services.analysis_pipeline.participation_analysis import step0_summarizing
            
            self.update_job_status(
                job_id, JobStatus.COMPLETED, db,
                output_files=["data/REG VS PART.xlsx"]
            )
            self.update_pipeline_state("participation.step0", "completed", db)
            
        except Exception as e:
            self.update_job_status(job_id, JobStatus.FAILED, db, error_message=str(e))
            self.update_pipeline_state("participation.step0", "failed", db)
        finally:
            db.close()
            # Reset context
            job_context_var.reset(token)
    
    def run_performance_step(self, step_num: int, job_id: str):
        # Set context for logging
        token = job_context_var.set(job_id)
        active_job_logs[job_id] = []

        db = SessionLocal()
        try:
            self.update_job_status(job_id, JobStatus.RUNNING, db)
            
            # Import new in-memory steps
            from app.services.analysis_pipeline.performance_analysis.step0_formatting import run_step0
            from app.services.analysis_pipeline.performance_analysis.step1_percentage_calc_pivot import run_step1
            from app.services.analysis_pipeline.performance_analysis.step2_lo_wise_perf_w_qtns_pivot import run_step2
            from app.services.analysis_pipeline.performance_analysis.step3_diff_lvl_wise_w_qtns_pivot import run_step3
            from app.services.analysis_pipeline.performance_analysis.step4_clustering import run_step4
            from app.services.analysis_pipeline.performance_analysis.step5_uploadable_data import run_step5

            step_functions = {
                0: run_step0,
                1: run_step1,
                2: run_step2,
                3: run_step3,
                4: run_step4,
                5: run_step5,
            }
            
            if step_num not in step_functions:
                raise ValueError(f"Unknown step number: {step_num}")
            
            # Execute in-memory function
            # We still use working_directory logic if the functions rely on relative paths (e.g. data/)
            with working_directory(self.base_dir):
                step_functions[step_num]()
            
            output_files = self._get_output_files_for_step(step_num)
            
            self.update_job_status(job_id, JobStatus.COMPLETED, db, output_files=output_files)
            self.update_pipeline_state(f"performance.step{step_num}", "completed", db)
            
            if step_num == 5:
                self.update_pipeline_state("final_file_ready", "true", db)
            
        except Exception as e:
            self.update_job_status(job_id, JobStatus.FAILED, db, error_message=str(e))
            self.update_pipeline_state(f"performance.step{step_num}", "failed", db)
        finally:
            db.close()
            job_context_var.reset(token)
    
    def _get_output_files_for_step(self, step_num: int) -> list:
        # User requirement: "All outputs go to /outputs folder."
        # The new export_snapshot saves as:
        # step0_formatted.xlsx
        # step1_performance.xlsx
        # step2_lo.xlsx
        # step3_difficulty.xlsx
        # step4_clustered.xlsx
        # step5_uploadable.xlsx
        
        outputs_dir = self.base_dir / "outputs"
        
        file_map = {
            0: "step0_formatted.xlsx",
            1: "step1_performance.xlsx",
            2: "step2_lo.xlsx",
            3: "step3_difficulty.xlsx",
            4: "step4_clustered.xlsx",
            5: "step5_uploadable.xlsx",
        }
        
        filename = file_map.get(step_num)
        if filename:
            f = outputs_dir / filename
            if f.exists():
                return [str(f.relative_to(self.base_dir))]
        
        return []
    
    def get_step_preview(self, step_name: str) -> dict:
        # Define mappings for fixed cases if any
        # Participation Step 0 is still using data/REG VS PART.xlsx
        output_map = {
            "participation-0": ("data/REG VS PART.xlsx", ["schl_wise", "grade_wise"]),
        }
        
        # Check static map first
        file_path, sheets = output_map.get(step_name, (None, None))
        
        target_files = []
        target_sheets = sheets  # Specific sheets if requested, else all
        
        if file_path:
             target_files = [str(self.base_dir / file_path)]
        
        # Dynamic handling for performance steps
        if not target_files and step_name.startswith("performance-"):
            try:
                step_num = int(step_name.split("-")[1])
                # Uses internal method to get relevant output files for this step (now points to outputs/)
                relative_files = self._get_output_files_for_step(step_num)
                target_files = [str(self.base_dir / f) for f in relative_files]
            except ValueError:
                pass

        if not target_files:
            return {"error": "No preview available or file not found"}

        result = {"sheets": []}
        
        for file_abs_path in target_files:
            full_path = Path(file_abs_path)
            if not full_path.exists():
                continue
                
            try:
                import gc
                with pd.ExcelFile(full_path) as xls:
                    # If specific sheets weren't requested, use all sheets in the file
                    current_file_sheets = target_sheets or xls.sheet_names
                    
                    for sheet in current_file_sheets:
                        if sheet not in xls.sheet_names:
                            continue
                            
                        df = pd.read_excel(xls, sheet_name=sheet, nrows=10)
                        
                        # Create a friendly name if there are multiple files
                        display_name = sheet
                        if len(target_files) > 1:
                            display_name = f"{full_path.name} - {sheet}"
                        
                        # Sanitize float values (NaN, Inf) for JSON compliance
                        # use to_json -> json.loads to ensure strict JSON validity (NaN/Inf -> null)
                        import json
                        records_json = df.to_json(orient="records", date_format="iso")
                        records = json.loads(records_json)
                            
                        result["sheets"].append({
                            "name": display_name,
                            "columns": df.columns.tolist(),
                            "rows": records
                        })
                # Explicit GC after file close
                gc.collect()
            except Exception as e:
                # Log error or continue
                print(f"Error reading file {full_path}: {e}")
                continue
        
        if not result["sheets"]:
            return {"error": "Output file(s) found but could not be read or empty"}
            
        return result

    def get_step_output_files(self, step_name: str) -> list[Path]:
        """
        Returns list of absolute Paths to output files for a given step.
        """
        # Define mappings for fixed cases
        output_map = {
            "participation-0": ("data/REG VS PART.xlsx", None),
        }
        
        target_files = []
        
        # Check static map first
        file_path, _ = output_map.get(step_name, (None, None))
        
        if file_path:
             target_files = [self.base_dir / file_path]
        
        # Dynamic handling for performance steps
        if not target_files and step_name.startswith("performance-"):
            try:
                step_num = int(step_name.split("-")[1])
                # Uses internal method to get relative paths
                relative_files = self._get_output_files_for_step(step_num)
                target_files = [self.base_dir / f for f in relative_files]
            except ValueError:
                pass
                
        # Filter for existence
        return [f for f in target_files if f.exists()]
