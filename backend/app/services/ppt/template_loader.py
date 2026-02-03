
import os
from pptx import Presentation
from pathlib import Path

def load_template():
    
    path_str = os.environ.get("PPT_TEMPLATE_PATH")
    
    if not path_str:
        raise RuntimeError(
            "Configuration Error: PPT_TEMPLATE_PATH environment variable is not set. "
            "Please configure this to point to the valid PowerPoint template file."
        )

    template_path = Path(path_str)

    if not template_path.exists():
        raise FileNotFoundError(
            f"Template Error: The file specified in PPT_TEMPLATE_PATH does not exist.\n"
            f"Path: {template_path}"
        )

    try:
        prs = Presentation(str(template_path))
    except Exception as e:
        raise RuntimeError(
            f"Template Error: Failed to load PowerPoint template at {template_path}.\n"
            f"Details: {str(e)}"
        ) from e

    # Freeze slide size from template
    prs.slide_width = prs.slide_width
    prs.slide_height = prs.slide_height

    return prs
