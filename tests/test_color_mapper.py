import pandas as pd
import pytest
from src.color_mapper import categorize_series, build_color_map

BUCKETS = [
    {"min": 0.0,   "max": 5.0,  "label": "Low",  "color": "#00ff00"},
    {"min": 5.0,   "max": 10.0, "label": "Mid",  "color": "#ffff00"},
    {"min": 10.0,  "max": 20.0, "label": "High", "color": "#ff0000"},
]


def test_categorize_exact_boundaries():
    s = pd.Series([0.0, 4.9, 5.0, 9.9, 10.0, 19.9])
    result = categorize_series(s, BUCKETS)
    assert list(result) == ["Low", "Low", "Mid", "Mid", "High", "High"]


def test_categorize_out_of_range_is_other():
    s = pd.Series([-1.0, 20.0, 100.0])
    result = categorize_series(s, BUCKETS)
    assert list(result) == ["Other", "Other", "Other"]


def test_categorize_empty_buckets_all_other():
    s = pd.Series([1.0, 2.0])
    result = categorize_series(s, [])
    assert list(result) == ["Other", "Other"]


def test_build_color_map_includes_other():
    cmap = build_color_map(BUCKETS)
    assert cmap["Low"] == "#00ff00"
    assert cmap["Mid"] == "#ffff00"
    assert cmap["High"] == "#ff0000"
    assert "Other" in cmap


def test_build_color_map_empty_buckets():
    cmap = build_color_map([])
    assert cmap == {"Other": "#aaaaaa"}
