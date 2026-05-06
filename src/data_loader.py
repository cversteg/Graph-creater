import pandas as pd
from typing import Tuple, List


def load_file(file) -> pd.DataFrame:
    name = file.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(file)
    if name.endswith((".xlsx", ".xls")):
        return pd.read_excel(file, engine="openpyxl")
    raise ValueError(f"Unsupported file type: {file.name}")


def detect_column_types(df: pd.DataFrame) -> Tuple[List[str], List[str]]:
    numerical = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    categorical = [c for c in df.columns if not pd.api.types.is_numeric_dtype(df[c])]
    return numerical, categorical
