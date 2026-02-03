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

def detect_percent_metric(series: pd.Series, name: str) -> bool:

    name_l = name.lower()

    header_hint = any(w in name_l for w in PERCENT_HINTS)

    vals = pd.to_numeric(series, errors="coerce").dropna()

    if len(vals) == 0:
        return False

    # true ratios 0–1
    if vals.max() <= 1.0:
        return True

    # classic percent range
    if vals.max() <= 100 and vals.min() >= 0:
        return True

    return header_hint


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
