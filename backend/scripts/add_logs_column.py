import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.core.db import engine

def add_logs_column():
    print("Attempting to add 'logs' column to pipeline_jobs table...")
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE pipeline_jobs ADD COLUMN logs TEXT"))
            conn.commit()
            print("Successfully added 'logs' column.")
        except Exception as e:
            print(f"Error (might already exist): {e}")

if __name__ == "__main__":
    add_logs_column()
