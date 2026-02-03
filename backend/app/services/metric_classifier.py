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

def classify_metric(name: str) -> str:

    n = name.lower().strip()

    for p in REG_PATTERNS:
        if p in n:
            return "registered"

    for p in NOT_REG_PATTERNS:
        if p in n:
            return "not_registered"

    for p in PART_PATTERNS:
        if p in n:
            return "participated"

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
