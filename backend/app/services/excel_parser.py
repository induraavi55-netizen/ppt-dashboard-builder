import pandas as pd
import tempfile
import openpyxl
import re

from app.services.pivot_detector import detect_schema
from app.services.dataset_normalizer import normalize_dataset


# --------------------------------------------------
# CLEANERS
# --------------------------------------------------

TEXT_COL_HINTS = [
    "question",
    "questions",
    "learning outcome",
    "lo",
    "description",
    "statement",
    "indicator",
]


def _clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:

    # Drop fully empty rows/cols
    df = df.dropna(axis=0, how="all").dropna(axis=1, how="all")

    # Strip column names
    df.columns = [str(c).strip() for c in df.columns]

    return df.reset_index(drop=True)


def _coerce_percent_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert columns that look like percentages into floats.
    """

    for col in df.columns:

        cname = col.lower()

        if "%" in cname or "percent" in cname or "avg" in cname:

            df[col] = (
                df[col]
                .astype(str)
                .str.replace("%", "", regex=False)
                .str.replace("(", "", regex=False)
                .str.replace(")", "", regex=False)
            )

            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def _drop_text_metric_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    If a column smells like narrative text, never let it become numeric.
    """

    for col in list(df.columns):

        n = col.lower()

        if any(h in n for h in TEXT_COL_HINTS):
            df[col] = df[col].astype(str)

    return df


def _sanitize_for_json(df: pd.DataFrame) -> pd.DataFrame:
    """
    PostgreSQL JSON cannot store NaN / inf.
    Convert them to None.
    """
    return df.replace(
        {
            float("nan"): None,
            float("inf"): None,
            float("-inf"): None,
        }
    )


# --------------------------------------------------
# STRUCTURAL FILTER
# --------------------------------------------------

def looks_like_pivot(df: pd.DataFrame) -> bool:

    df = df.dropna(axis=1, how="all")

    if df.shape[0] < 2 or df.shape[1] < 2:
        return False

    numeric_cols = df.select_dtypes(include="number").columns
    text_cols = df.select_dtypes(include="object").columns

    if len(numeric_cols) == 0:
        return False

    # admin sheets usually have tons of identifiers
    if len(text_cols) > 8:
        return False

    return True


# --------------------------------------------------
# MERGED CELL DETECTOR
# --------------------------------------------------

def detect_merged_sheets(path: str) -> set[str]:

    wb = openpyxl.load_workbook(path, data_only=True)

    merged = set()

    for ws in wb.worksheets:
        if ws.merged_cells.ranges:
            merged.add(ws.title)

    return merged


# --------------------------------------------------
# MAIN PARSER
# --------------------------------------------------

async def parse_excel(file):

    contents = await file.read()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        tmp.write(contents)
        path = tmp.name

    merged_sheets = detect_merged_sheets(path)

    xls = pd.ExcelFile(path)

    datasets = []

    for sheet in xls.sheet_names:

        # ----------------------------------
        # Skip merged-cell sheets
        # ----------------------------------
        if sheet in merged_sheets:
            continue

        df = xls.parse(sheet, header=0)

        df = _clean_dataframe(df)

        # ----------------------------------
        # Normalize percent-like columns early
        # ----------------------------------
        df = _coerce_percent_columns(df)

        df = _drop_text_metric_columns(df)

        # ----------------------------------
        # Skip admin / non-pivot sheets
        # ----------------------------------
        if not looks_like_pivot(df):
            continue

        schema = detect_schema(df)

        # ----------------------------------
        # REG VS PART MUST STAY WIDE
        # ----------------------------------
        if sheet.startswith("reg_vs_part"):
            normalized = df.copy()
        else:
            normalized = normalize_dataset(df, schema)

        # ----------------------------------
        # JSON-safe
        # ----------------------------------
        normalized = _sanitize_for_json(normalized)

        datasets.append(
            {
                "name": sheet,
                "columns": normalized.columns.tolist(),
                "rows": len(normalized),
                "schema": schema,
                "preview": normalized.to_dict(orient="records"),
            }
        )

    return datasets
