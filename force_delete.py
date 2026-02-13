import shutil
import os
import time

path = r"backend\data"
if os.path.exists(path):
    print(f"Deleting {path}...")
    try:
        shutil.rmtree(path)
        print("Deleted.")
    except Exception as e:
        print(f"Failed to delete: {e}")
        # Try waiting and retrying
        time.sleep(1)
        try:
            shutil.rmtree(path)
            print("Deleted on 2nd try.")
        except Exception as e2:
            print(f"Permanently failed: {e2}")
else:
    print("Path does not exist.")
