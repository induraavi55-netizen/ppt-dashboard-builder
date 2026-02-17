from typing import Dict, Any

# Global In-Memory State
# Structure:
# {
#   "raw": { "filename": { "sheetname": pd.DataFrame, ... } },
#   "step0": { "filename": { "formatted": df, "formatted_long": df } },
#   "step1": { ... },
#   ...
#   "logs": []
# }
_pipeline_state: Dict[str, Any] = {
    "raw": {},
    "step0": {},
    "step1": {},
    "step2": {},
    "step3": {},
    "step4": {},
    "step5": {},
    "logs": []
}

def get_pipeline_state() -> Dict[str, Any]:
    """Returns the global pipeline state."""
    return _pipeline_state

def reset_pipeline_state():
    """Resets the pipeline state to empty dicts."""
    global _pipeline_state
    _pipeline_state.clear()
    _pipeline_state.update({
        "raw": {},
        "step0": {},
        "step1": {},
        "step2": {},
        "step3": {},
        "step4": {},
        "step5": {},
        "logs": []
    })

def update_pipeline_state(step_key: str, data: Any):
    """Updates a specific step in the state."""
    if step_key not in _pipeline_state:
        _pipeline_state[step_key] = {}
    _pipeline_state[step_key] = data

def get_step_data(step_key: str) -> Any:
    """Retrieves data for a specific step."""
    return _pipeline_state.get(step_key, {})
