from app.services.metric_classifier import classify_metric


# --------------------------------------------------
# helpers
# --------------------------------------------------

TEXT_METRIC_BLACKLIST = {
    "question",
    "questions",
    "learning outcome",
    "learning_outcome",
    "lo",
    "description",
    "desc",
    "indicator",
    "statement",
}


def _norm(x):
    if isinstance(x, dict):
        return x.get("name")
    return str(x)


def _is_blacklisted_metric(name: str) -> bool:
    n = name.lower()
    return any(b in n for b in TEXT_METRIC_BLACKLIST)


# --------------------------------------------------
# ENTITY DETECTION
# --------------------------------------------------

def detect_entity(dimensions):

    dims = [d.lower() for d in dimensions]

    if any("school" in d or "gurukulam" in d for d in dims):
        return "school"

    if any("grade" in d or "class" in d for d in dims):
        return "grade"

    return "generic"


# --------------------------------------------------
# FAMILY DETECTION
# --------------------------------------------------

def detect_family(name: str):

    n = name.lower()

    if n.endswith("_lo"):
        return "lo"

    if n.endswith("_qlvl"):
        return "qlvl"

    if "perf_summary" in n:
        return "perf_summary"

    if "sub_wise" in n or "summary" in n:
        return "summary"

    return "generic"


# --------------------------------------------------
# MAIN PROFILER
# --------------------------------------------------

def profile_dataset(dataset: dict):

    schema = dataset.get("schema") or {}

    dims = [_norm(d) for d in schema.get("dimensions", [])]
    metrics = [_norm(m) for m in schema.get("metrics", [])]

    # --------------------------------------------------
    # Move obvious dimensions wrongly marked as metrics
    # --------------------------------------------------

    for accidental in ("Grade", "grade", "Class", "class"):
        if accidental in metrics:
            metrics.remove(accidental)
            dims.append(accidental)

    # --------------------------------------------------
    # Drop textual garbage from metrics
    # --------------------------------------------------

    metrics = [m for m in metrics if not _is_blacklisted_metric(m)]

    # --------------------------------------------------
    # Classify metrics
    # --------------------------------------------------

    metric_types = {m: classify_metric(m) for m in metrics}

    # --------------------------------------------------
    # Special cases
    # --------------------------------------------------

    special_case = None

    if (
        "registered" in metric_types.values()
        and "participated" in metric_types.values()
    ):
        special_case = "reg_vs_part"

    # --------------------------------------------------
    # Dataset family overrides
    # --------------------------------------------------

    family = detect_family(dataset["name"])

    # LO / QLVL MUST be percent based
    if family in ("lo", "qlvl"):
        metrics = [
            m for m in metrics
            if metric_types.get(m) == "percent"
            or "%" in m
            or "percent" in m.lower()
        ]

        metric_types = {m: "percent" for m in metrics}

    # perf summary is percent by definition
    if family == "perf_summary":
        metric_types = {m: "percent" for m in metrics}

    # --------------------------------------------------
    # Dataset type
    # --------------------------------------------------

    dataset_type = (
        "percent"
        if any(t == "percent" for t in metric_types.values())
        else "count"
    )

    return {
        "type": dataset_type,
        "series_count": len(metrics),
        "dimensions": dims,
        "metrics": metrics,
        "metric_types": metric_types,
        "entity": detect_entity(dims),
        "special_case": special_case,
        "dataset_family": family,
    }
