import pandas as pd
from typing import Any, Dict, List


def categorize_series(series: pd.Series, buckets: List[Dict[str, Any]]) -> pd.Series:
    result = pd.Series("Other", index=series.index, dtype=object)
    for bucket in buckets:
        mask = (series >= bucket["min"]) & (series < bucket["max"])
        result[mask] = bucket["label"]
    return result


def build_color_map(buckets: List[Dict[str, Any]]) -> Dict[str, str]:
    cmap: Dict[str, str] = {"Other": "#aaaaaa"}
    for bucket in buckets:
        cmap[bucket["label"]] = bucket["color"]
    return cmap
