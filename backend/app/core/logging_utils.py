import contextvars
from datetime import datetime
import sys

# Context variable to hold the current job ID
job_context_var = contextvars.ContextVar("job_ids", default=None)

# Global store for active job logs (in-memory)
# key: job_id, value: list of log strings
active_job_logs = {}

class JobLogger:
    """
    A logger that writes to the active job's log storage if a job context is active.
    Falls back to stdout/print if no job context is found.
    """
    
    @staticmethod
    def log(message: str):
        job_id = job_context_var.get()
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        
        if job_id:
            # Append to the in-memory log store for this job
            if job_id in active_job_logs:
                active_job_logs[job_id].append(formatted_message)
            else:
                # Should not happen if orchestrator initialized it, but safe fallback
                active_job_logs[job_id] = [formatted_message]
            
            # Also print to stdout for server logs
            print(f"[JOB-{job_id}] {message}")
        else:
            # Fallback for manual script runs
            print(message)

    @staticmethod
    def error(message: str):
        JobLogger.log(f"ERROR: {message}")

# Helper to easily print without importing the class everywhere if prefered
# But usually importing the class is cleaner.
logger = JobLogger()
