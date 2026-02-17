from typing import Dict, Any

# Global registry for pipeline previews
# Key: preview_id (e.g., "participation-0", "performance-1")
# Value: Dictionary containing preview data (e.g., {"sheets": [...]})
preview_registry: Dict[str, Dict[str, Any]] = {}

def register_preview(preview_id: str, data: Dict[str, Any]):
    """
    Registers in-memory preview data for a specific pipeline step.
    Overwrites existing data for the same ID.
    """
    preview_registry[preview_id] = data
    # print(f"[PreviewRegistry] Registered data for {preview_id}")

def get_preview(preview_id: str) -> Dict[str, Any]:
    """
    Retrieves preview data from memory. Returns None if not found.
    """
    return preview_registry.get(preview_id)

def clear_previews():
    """
    Clears all registered previews.
    """
    preview_registry.clear()
