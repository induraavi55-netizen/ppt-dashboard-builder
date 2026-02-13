import pandas as pd


# --------------------------------------------------
# helpers
# --------------------------------------------------

TEXT_DIM_HINTS = [
    "question",
    "questions",
    "learning outcome",
    "learning_outcome",
    "lo",
    "description",
    "statement",
    "indicator",
]


def _extract_names(items):
    cleaned = []
    for x in items:
        if isinstance(x, dict):
            cleaned.append(x.get("name"))
        else:
            cleaned.append(x)
    return cleaned


def _looks_textual(name: str) -> bool:
    n = name.lower()
    return any(h in n for h in TEXT_DIM_HINTS)


# --------------------------------------------------
# NORMALIZER
# --------------------------------------------------

def normalize_dataset(df: pd.DataFrame, schema: dict) -> pd.DataFrame:

    dims_raw = schema.get("dimensions", [])
    metrics_raw = schema.get("metrics", [])

    dims = _extract_names(dims_raw)
    metrics = _extract_names(metrics_raw)

    # ---------------------------------------------
    # Only use columns that actually exist
    # ---------------------------------------------

    dims = [c for c in dims if c in df.columns]
    metrics = [c for c in metrics if c in df.columns]

    # ---------------------------------------------
    # Never melt narrative-heavy datasets
    # ---------------------------------------------

    if any(_looks_textual(d) for d in dims):
        return df

    # ---------------------------------------------
    # Detect and clean percent metric sets
    # ---------------------------------------------

    percent_metrics = []

    for m in metrics:
        meta = next(
            (x for x in metrics_raw if isinstance(x, dict) and x.get("name") == m),
            {},
        )
        if meta.get("is_percent"):
            percent_metrics.append(m)
            
            # Implementation: Strip % and coerce to float
            if m in df.columns:
                df[m] = (
                    df[m]
                    .astype(str)
                    .str.replace("%", "", regex=False)
                    .str.replace("(", "", regex=False)
                    .str.replace(")", "", regex=False)
                )
                df[m] = pd.to_numeric(df[m], errors="coerce")


    # ---------------------------------------------
    # Conservative melting rules
    # ---------------------------------------------

    # If only one metric, keep wide
    if len(metrics) <= 1:
        return df

    # If ALL metrics are percent, keep wide (perf summaries etc)
    if percent_metrics and len(percent_metrics) == len(metrics):
        return df

    # ---------------------------------------------
    # Melt only when truly multi-series
    # ---------------------------------------------

    return df.melt(
        id_vars=dims,
        value_vars=metrics,
        var_name="metric",
        value_name="value",
    )
