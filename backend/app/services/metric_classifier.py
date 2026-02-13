import re

# --------------------------------------------------
# Patterns
# --------------------------------------------------

REG_PATTERNS = [
    "registered",
    "enrolled",
    "reg ",
    "registration",
]

NOT_REG_PATTERNS = [
    "not registered",
    "not_registered",
    "not enrolled",
]

PART_PATTERNS = [
    "participated",
    "appeared",
    "attempted",
    "sat for",
]

PERCENT_PATTERNS = [
    "%",
    "percent",
    "pct",
    "avg",
    "average",
    "score",
    "performance",
    "accuracy",
]

TOTAL_PATTERNS = [
    "total",
    "count",
    "number",
    "students",
]

TEXT_PATTERNS = [
    "question",
    "questions",
    "learning outcome",
    "lo",
    "statement",
    "indicator",
]


# --------------------------------------------------
# CLASSIFIER
# --------------------------------------------------

def classify_metric(name: str, values: list = None) -> str:
    """
    Classifies a metric based on its name and optionally its values.
    """
    n = name.lower().strip()

    # 1. High-confidence name matches
    for p in REG_PATTERNS:
        if p in n:
            return "registered"

    for p in NOT_REG_PATTERNS:
        if p in n:
            return "not_registered"

    for p in PART_PATTERNS:
        if p in n:
            return "participated"

    # 2. Data-driven percent detection
    if values is not None:
        try:
            import pandas as pd
            series = pd.to_numeric(values, errors="coerce").dropna()
            if not series.empty:
                # If explicit % in name, it's a percent
                if "%" in n or "percent" in n:
                    return "percent"
                
                # If values are in 0–1 range (true fractional percent)
                if series.max() <= 1.0 and series.min() >= 0.0:
                    if len(series.unique()) > 2:
                        return "percent"
                
                # If explicit percent cues in name AND numeric range fits
                if series.max() <= 100.0 and series.min() >= 0.0:
                    if any(p in n for p in PERCENT_PATTERNS):
                        return "percent"
        except Exception:
            pass

    # 3. Fallback name-based patterns
    for p in PERCENT_PATTERNS:
        if p in n:
            return "percent"

    for p in TOTAL_PATTERNS:
        if p in n:
            return "count"

    for p in TEXT_PATTERNS:
        if p in n:
            return "text"

    return "generic"


