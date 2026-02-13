
import os
from pptx import Presentation
from pathlib import Path

def load_template():
    # Priority 1: Environment Variable
    path_str = os.environ.get("PPT_TEMPLATE_PATH")
    template_path = None
    
    if path_str:
        template_path = Path(path_str)
        if template_path.exists():
            print(f"[TEMPLATE] Using environment template: {template_path}")
        else:
            print(f"[TEMPLATE] WARNING: PPT_TEMPLATE_PATH set but file not found: {template_path}")
            template_path = None

    # Priority 2: Uploaded Fallback
    if not template_path:
        fallback_path = Path("templates/current_template.pptx")
        if fallback_path.exists():
            template_path = fallback_path
            print(f"[TEMPLATE] Using uploaded template: {template_path}")
    
    if not template_path:
        raise RuntimeError(
            "No PPT template configured. Upload one from UI or set PPT_TEMPLATE_PATH."
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
