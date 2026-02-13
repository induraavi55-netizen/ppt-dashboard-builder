import pandas as pd


# --------------------------------------------------
# HINT LISTS
# --------------------------------------------------

PERCENT_HINTS = [
    "%",
    "percent",
    "percentage",
    "avg",
    "average",
    "performance",
    "accuracy",
    "rate",
    "score",
]

TEXT_DIM_HINTS = [
    "question",
    "questions",
    "learning outcome",
    "learning_outcome",
    "lo",
    "description",
    "statement",
    "indicator",
    "remarks",
]


# --------------------------------------------------
# HELPERS
# --------------------------------------------------

def _looks_textual(name: str) -> bool:
    n = name.lower()
    return any(h in n for h in TEXT_DIM_HINTS)


# --------------------------------------------------
# PERCENT DETECTOR
# --------------------------------------------------

from app.services.metric_classifier import classify_metric

def detect_percent_metric(series: pd.Series, name: str) -> bool:
    n = name.lower()

    if "%" in n or "percent" in n or "percentage" in n:
        return True

    s = pd.to_numeric(series, errors="coerce").dropna()

    if not s.empty and s.max() <= 1.0 and s.min() >= 0.0:
        return True

    return False




# --------------------------------------------------
# SCHEMA DETECTOR
# --------------------------------------------------

def detect_schema(df: pd.DataFrame) -> dict:

    dims = []
    metrics = []

    for col in df.columns:

        series = df[col]
        col_l = col.lower()

        # narrative columns are always dimensions
        if _looks_textual(col):
            dims.append(col)
            continue

        # numeric → metric candidate
        if pd.api.types.is_numeric_dtype(series):

            is_percent = detect_percent_metric(series, col)

            metrics.append(
                {
                    "name": col,
                    "is_percent": is_percent,
                }
            )

        else:
            dims.append(col)

    return {
        "dimensions": dims,
        "metrics": metrics,
    }
