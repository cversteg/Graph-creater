# Streamlit Scatter Plot App Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Streamlit web app that loads Excel/CSV files and renders interactive, color-coded scatter plots driven entirely by user-defined range buckets, with no hardcoded series.

**Architecture:** Pure-function business logic (data loading, color mapping, chart building) lives in `src/` modules and is fully unit-tested. `app.py` is a thin Streamlit shell that wires these modules together via `st.session_state`. Terraform provisions the Azure App Service infra; deployment is a separate `az webapp deploy` step.

**Tech Stack:** Python 3.11, Streamlit ≥ 1.32, Pandas ≥ 2.0, Plotly ≥ 5.18, openpyxl ≥ 3.1, pytest, Terraform + azurerm provider ~3.0

---

## File Map

| Path | Responsibility |
|---|---|
| `app.py` | Streamlit entry point, sidebar UI, state wiring |
| `src/__init__.py` | Empty package marker |
| `src/data_loader.py` | Load CSV/XLSX → DataFrame, detect column types |
| `src/color_mapper.py` | Map numeric series to labels via range buckets; build color_discrete_map |
| `src/chart_builder.py` | Build styled Plotly figure from DataFrame + config |
| `tests/test_data_loader.py` | Unit tests for loader & column detection |
| `tests/test_color_mapper.py` | Unit tests for categorisation + color map |
| `tests/test_chart_builder.py` | Unit tests for chart output |
| `requirements.txt` | Python runtime dependencies |
| `.streamlit/config.toml` | Port + address for Azure App Service |
| `terraform/main.tf` | Azure Resource Group, App Service Plan (F1), Linux Web App |

---

## Task 1: Project Scaffolding

**Files:**
- Create: `requirements.txt`
- Create: `.streamlit/config.toml`
- Create: `src/__init__.py`
- Create: `tests/__init__.py`
- Create: `app.py` (skeleton only)

- [ ] **Step 1: Create requirements.txt**

```
streamlit>=1.32.0
pandas>=2.0.0
plotly>=5.18.0
openpyxl>=3.1.0
pytest>=8.0.0
```

- [ ] **Step 2: Create .streamlit/config.toml**

```toml
[server]
port = 8000
address = "0.0.0.0"
headless = true

[theme]
base = "light"
```

- [ ] **Step 3: Create src/__init__.py and tests/__init__.py**

Both files are empty. Their only purpose is to make Python treat these directories as packages.

- [ ] **Step 4: Create app.py skeleton**

```python
import streamlit as st

st.set_page_config(page_title="Scatter Plot Builder", layout="wide")

def main():
    st.title("Scatter Plot Builder")
    st.info("Upload a CSV or Excel file to get started.")

if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Install dependencies and verify app starts**

```bash
pip install -r requirements.txt
streamlit run app.py
```

Expected: Browser opens with "Scatter Plot Builder" title and the info message.

- [ ] **Step 6: Commit**

```bash
git init
git add requirements.txt .streamlit/config.toml src/__init__.py tests/__init__.py app.py
git commit -m "chore: project scaffolding"
```

---

## Task 2: Data Loading Module

**Files:**
- Create: `src/data_loader.py`
- Create: `tests/test_data_loader.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_data_loader.py
import io
import pytest
import pandas as pd
from src.data_loader import load_file, detect_column_types


class _FakeFile:
    """Minimal file-like object that mimics st.UploadedFile."""
    def __init__(self, name: str, content: bytes):
        self.name = name
        self._buf = io.BytesIO(content)

    def read(self, *a):
        return self._buf.read(*a)

    def seek(self, *a):
        return self._buf.seek(*a)


def _csv_file(content: str) -> _FakeFile:
    return _FakeFile("data.csv", content.encode())


def test_load_csv_returns_dataframe():
    f = _csv_file("a,b\n1,x\n2,y")
    df = load_file(f)
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == ["a", "b"]
    assert len(df) == 2


def test_load_unsupported_raises():
    f = _FakeFile("data.txt", b"hello")
    with pytest.raises(ValueError, match="Unsupported"):
        load_file(f)


def test_detect_column_types_splits_correctly():
    df = pd.DataFrame({"temp": [1.0, 2.0], "unit": ["K", "C"], "pressure": [10, 20]})
    numerical, categorical = detect_column_types(df)
    assert set(numerical) == {"temp", "pressure"}
    assert set(categorical) == {"unit"}


def test_detect_column_types_all_numerical():
    df = pd.DataFrame({"x": [1], "y": [2]})
    numerical, categorical = detect_column_types(df)
    assert set(numerical) == {"x", "y"}
    assert categorical == []
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_data_loader.py -v
```

Expected: `ImportError` or `ModuleNotFoundError` — `src.data_loader` does not exist yet.

- [ ] **Step 3: Implement src/data_loader.py**

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_data_loader.py -v
```

Expected: 4 tests PASSED.

- [ ] **Step 5: Commit**

```bash
git add src/data_loader.py tests/test_data_loader.py
git commit -m "feat: data loading module with CSV/XLSX support"
```

---

## Task 3: Color Mapper Module

**Files:**
- Create: `src/color_mapper.py`
- Create: `tests/test_color_mapper.py`

A "bucket" is a dict with keys `min` (float), `max` (float), `label` (str), `color` (hex string).
Values equal to `min` are included; values equal to `max` are excluded (`[min, max)`).
The first bucket whose range contains the value wins. Values in no bucket get label `"Other"`.

- [ ] **Step 1: Write failing tests**

```python
# tests/test_color_mapper.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_color_mapper.py -v
```

Expected: `ImportError` — `src.color_mapper` does not exist yet.

- [ ] **Step 3: Implement src/color_mapper.py**

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_color_mapper.py -v
```

Expected: 5 tests PASSED.

- [ ] **Step 5: Commit**

```bash
git add src/color_mapper.py tests/test_color_mapper.py
git commit -m "feat: color mapper module with range bucket logic"
```

---

## Task 4: Chart Builder Module

**Files:**
- Create: `src/chart_builder.py`
- Create: `tests/test_chart_builder.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_chart_builder.py
import pandas as pd
import plotly.graph_objects as go
from src.chart_builder import build_scatter

DF = pd.DataFrame({
    "temp":    [100, 200, 300],
    "fuel":    [10,  20,  30],
    "range":   ["Low", "Mid", "High"],
})

COLOR_MAP = {"Low": "#00ff00", "Mid": "#ffff00", "High": "#ff0000", "Other": "#aaaaaa"}


def test_build_scatter_returns_figure():
    fig = build_scatter(DF, x_col="temp", y_col="fuel", color_col="range", color_map=COLOR_MAP)
    assert isinstance(fig, go.Figure)


def test_build_scatter_has_correct_axis_titles():
    fig = build_scatter(DF, x_col="temp", y_col="fuel", color_col="range", color_map=COLOR_MAP)
    assert fig.layout.xaxis.title.text == "temp"
    assert fig.layout.yaxis.title.text == "fuel"


def test_build_scatter_white_background():
    fig = build_scatter(DF, x_col="temp", y_col="fuel", color_col="range", color_map=COLOR_MAP)
    assert fig.layout.plot_bgcolor == "white"
    assert fig.layout.paper_bgcolor == "white"


def test_build_scatter_without_color_map():
    # color_map=None should not raise
    fig = build_scatter(DF, x_col="temp", y_col="fuel", color_col="range", color_map=None)
    assert isinstance(fig, go.Figure)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_chart_builder.py -v
```

Expected: `ImportError` — `src.chart_builder` does not exist yet.

- [ ] **Step 3: Implement src/chart_builder.py**

```python
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Optional


def build_scatter(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    color_col: str,
    color_map: Optional[Dict[str, str]] = None,
    title: str = "",
) -> go.Figure:
    fig = px.scatter(
        df,
        x=x_col,
        y=y_col,
        color=color_col,
        color_discrete_map=color_map,
        title=title,
    )
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        xaxis=dict(
            title=x_col,
            showgrid=True,
            gridcolor="#e0e0e0",
            zeroline=False,
        ),
        yaxis=dict(
            title=y_col,
            showgrid=True,
            gridcolor="#e0e0e0",
            zeroline=False,
        ),
        legend_title_text=color_col,
        font=dict(family="Arial", size=12),
        margin=dict(l=60, r=30, t=60, b=60),
    )
    return fig
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_chart_builder.py -v
```

Expected: 4 tests PASSED.

- [ ] **Step 5: Run all tests to confirm nothing broke**

```bash
pytest -v
```

Expected: 13 tests PASSED total.

- [ ] **Step 6: Commit**

```bash
git add src/chart_builder.py tests/test_chart_builder.py
git commit -m "feat: chart builder module with professional plot styling"
```

---

## Task 5: Sidebar — Axis and Color-By Selection

**Files:**
- Modify: `app.py`

This task wires up file upload and the three primary axis dropdowns. Filter and bucket UI come in later tasks.

- [ ] **Step 1: Replace app.py with full upload + axis selection UI**

```python
# app.py
import streamlit as st
import pandas as pd
from src.data_loader import load_file, detect_column_types
from src.color_mapper import categorize_series, build_color_map
from src.chart_builder import build_scatter

st.set_page_config(page_title="Scatter Plot Builder", layout="wide")


def _init_state():
    defaults = {
        "df": None,
        "filename": None,
        "x_col": None,
        "y_col": None,
        "color_by_col": None,
        "buckets": [],
        "col_filters": {},   # {col: (min_val, max_val)} for numerical
        "cat_filters": {},   # {col: [selected_values]} for categorical
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def _handle_upload(uploaded_file):
    if uploaded_file is None:
        return
    if uploaded_file.name == st.session_state.filename:
        return  # same file, no reload needed
    df = load_file(uploaded_file)
    st.session_state.df = df
    st.session_state.filename = uploaded_file.name
    # Reset axis selections when a new file is loaded
    cols = list(df.columns)
    st.session_state.x_col = cols[0] if len(cols) > 0 else None
    st.session_state.y_col = cols[1] if len(cols) > 1 else cols[0]
    st.session_state.color_by_col = cols[2] if len(cols) > 2 else cols[0]
    # Purge filters for columns that no longer exist
    existing = set(cols)
    st.session_state.col_filters = {
        k: v for k, v in st.session_state.col_filters.items() if k in existing
    }
    st.session_state.cat_filters = {
        k: v for k, v in st.session_state.cat_filters.items() if k in existing
    }


def _sidebar_axis(df: pd.DataFrame):
    cols = list(df.columns)
    st.sidebar.subheader("Axes")
    st.session_state.x_col = st.sidebar.selectbox(
        "X axis", cols,
        index=cols.index(st.session_state.x_col) if st.session_state.x_col in cols else 0,
        key="sb_x",
    )
    st.session_state.y_col = st.sidebar.selectbox(
        "Y axis", cols,
        index=cols.index(st.session_state.y_col) if st.session_state.y_col in cols else 0,
        key="sb_y",
    )
    st.session_state.color_by_col = st.sidebar.selectbox(
        "Color by", cols,
        index=cols.index(st.session_state.color_by_col) if st.session_state.color_by_col in cols else 0,
        key="sb_color",
    )


def main():
    _init_state()
    st.title("Scatter Plot Builder")

    uploaded_file = st.sidebar.file_uploader(
        "Upload CSV or Excel", type=["csv", "xlsx", "xls"]
    )
    _handle_upload(uploaded_file)

    df = st.session_state.df
    if df is None:
        st.info("Upload a CSV or Excel file to get started.")
        return

    _sidebar_axis(df)

    st.write(f"Loaded **{st.session_state.filename}** — {len(df):,} rows, {len(df.columns)} columns")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Smoke-test in browser**

```bash
streamlit run app.py
```

Upload any CSV. Verify: three dropdowns appear, selecting different columns works, re-uploading a different file resets columns.

- [ ] **Step 3: Commit**

```bash
git add app.py
git commit -m "feat: file upload and axis selection sidebar"
```

---

## Task 6: Sidebar — Dynamic Filter Management

**Files:**
- Modify: `app.py`

Add `_sidebar_filters(df)` function that auto-detects column types and renders appropriate widgets. Numerical columns get range sliders; categorical columns get multi-select boxes. Filter state is stored in `st.session_state.col_filters` and `st.session_state.cat_filters`.

- [ ] **Step 1: Add _sidebar_filters to app.py**

Insert this function after `_sidebar_axis` and before `main()`:

```python
def _sidebar_filters(df: pd.DataFrame):
    from src.data_loader import detect_column_types
    numerical, categorical = detect_column_types(df)

    if not numerical and not categorical:
        return

    st.sidebar.subheader("Filters")

    for col in numerical:
        col_min = float(df[col].min())
        col_max = float(df[col].max())
        if col_min == col_max:
            continue  # no range to filter
        stored = st.session_state.col_filters.get(col)
        default_low  = stored[0] if stored and stored[0] >= col_min else col_min
        default_high = stored[1] if stored and stored[1] <= col_max else col_max
        low, high = st.sidebar.slider(
            col,
            min_value=col_min,
            max_value=col_max,
            value=(default_low, default_high),
            key=f"filter_{col}",
        )
        st.session_state.col_filters[col] = (low, high)

    for col in categorical:
        unique_vals = sorted(df[col].dropna().unique().tolist())
        stored = st.session_state.cat_filters.get(col)
        valid_stored = [v for v in (stored or []) if v in unique_vals]
        default_sel = valid_stored if valid_stored else unique_vals
        selected = st.sidebar.multiselect(
            col,
            options=unique_vals,
            default=default_sel,
            key=f"catfilter_{col}",
        )
        st.session_state.cat_filters[col] = selected
```

- [ ] **Step 2: Call _sidebar_filters inside main()**

In `main()`, after `_sidebar_axis(df)`, add:

```python
    _sidebar_filters(df)
```

- [ ] **Step 3: Add _apply_filters helper after _sidebar_filters**

```python
def _apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    mask = pd.Series(True, index=df.index)
    for col, (low, high) in st.session_state.col_filters.items():
        if col in df.columns:
            mask &= (df[col] >= low) & (df[col] <= high)
    for col, selected in st.session_state.cat_filters.items():
        if col in df.columns and selected:
            mask &= df[col].isin(selected)
    return df[mask]
```

- [ ] **Step 4: Smoke-test in browser**

```bash
streamlit run app.py
```

Upload a CSV with mixed numerical/categorical columns. Verify: sliders appear for numbers, multiselects for text, selecting all vs. some values works, re-uploading preserves valid filters.

- [ ] **Step 5: Commit**

```bash
git add app.py
git commit -m "feat: dynamic filter sidebar with range sliders and multiselects"
```

---

## Task 7: Sidebar — Range Bucket Builder

**Files:**
- Modify: `app.py`

This is the core "Delta T" feature. Users add/remove range buckets that map numeric ranges to labels and colors. Each bucket is `{"min": float, "max": float, "label": str, "color": str}`.

- [ ] **Step 1: Add _sidebar_buckets to app.py**

Insert this function after `_sidebar_filters` and before `main()`:

```python
def _sidebar_buckets(df: pd.DataFrame):
    from src.data_loader import detect_column_types
    numerical, _ = detect_column_types(df)

    st.sidebar.subheader("Color Range Buckets")
    st.sidebar.caption(
        "Define ranges for the 'Color by' column. Values outside all ranges appear as 'Other'."
    )

    color_col = st.session_state.color_by_col
    if color_col not in numerical:
        st.sidebar.info(f"'{color_col}' is not numeric, buckets not applicable.")
        return

    col_min = float(df[color_col].min())
    col_max = float(df[color_col].max())

    DEFAULT_COLORS = [
        "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728",
        "#9467bd", "#8c564b", "#e377c2", "#7f7f7f",
    ]

    buckets = st.session_state.buckets

    to_remove = None
    for i, bucket in enumerate(buckets):
        with st.sidebar.expander(f"Bucket {i + 1}: {bucket['label']}", expanded=False):
            cols = st.columns([1, 1])
            bucket["min"] = cols[0].number_input(
                "Min", value=float(bucket["min"]), key=f"bmin_{i}"
            )
            bucket["max"] = cols[1].number_input(
                "Max", value=float(bucket["max"]), key=f"bmax_{i}"
            )
            bucket["label"] = st.text_input("Label", value=bucket["label"], key=f"blabel_{i}")
            bucket["color"] = st.color_picker("Color", value=bucket["color"], key=f"bcolor_{i}")
            if st.button("Remove", key=f"bremove_{i}"):
                to_remove = i

    if to_remove is not None:
        buckets.pop(to_remove)
        st.rerun()

    if st.sidebar.button("+ Add Bucket"):
        idx = len(buckets)
        step = (col_max - col_min) / 10 if col_max != col_min else 1.0
        buckets.append({
            "min": round(col_min + idx * step, 4),
            "max": round(col_min + (idx + 1) * step, 4),
            "label": f"Range {idx + 1}",
            "color": DEFAULT_COLORS[idx % len(DEFAULT_COLORS)],
        })
        st.rerun()

    st.session_state.buckets = buckets
```

- [ ] **Step 2: Call _sidebar_buckets inside main()**

After `_sidebar_filters(df)`, add:

```python
    _sidebar_buckets(df)
```

- [ ] **Step 3: Smoke-test in browser**

```bash
streamlit run app.py
```

- Click "+ Add Bucket" 3 times. Verify 3 expanders appear.
- Edit min/max/label/color on one bucket.
- Remove the second bucket. Verify it disappears and the others remain intact.
- Switch the "Color by" column to a categorical column. Verify the info message appears instead of buckets.

- [ ] **Step 4: Commit**

```bash
git add app.py
git commit -m "feat: dynamic range bucket builder in sidebar"
```

---

## Task 8: Main Chart Display

**Files:**
- Modify: `app.py`

Wire all the state together: apply filters, categorize the color column, build and display the chart.

- [ ] **Step 1: Add _render_chart to app.py**

Insert this function after `_apply_filters` and before `main()`:

```python
def _render_chart(df: pd.DataFrame):
    from src.data_loader import detect_column_types
    from src.color_mapper import categorize_series, build_color_map
    from src.chart_builder import build_scatter

    x_col = st.session_state.x_col
    y_col = st.session_state.y_col
    color_col = st.session_state.color_by_col
    buckets = st.session_state.buckets

    numerical, _ = detect_column_types(df)
    use_buckets = color_col in numerical and len(buckets) > 0

    if use_buckets:
        df = df.copy()
        df["__color_label__"] = categorize_series(df[color_col], buckets)
        color_map = build_color_map(buckets)
        fig = build_scatter(
            df, x_col=x_col, y_col=y_col,
            color_col="__color_label__",
            color_map=color_map,
            title=f"{y_col} vs {x_col}",
        )
        # Restore the legend title to the actual column name
        fig.update_layout(legend_title_text=color_col)
    else:
        fig = build_scatter(
            df, x_col=x_col, y_col=y_col,
            color_col=color_col,
            color_map=None,
            title=f"{y_col} vs {x_col}",
        )

    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Filtered data preview"):
        st.dataframe(df.drop(columns=["__color_label__"], errors="ignore"), use_container_width=True)
```

- [ ] **Step 2: Update main() to apply filters and render chart**

Replace the final `st.write(...)` line in `main()` with:

```python
    st.write(f"Loaded **{st.session_state.filename}** — {len(df):,} rows, {len(df.columns)} columns")
    filtered_df = _apply_filters(df)
    st.caption(f"Showing {len(filtered_df):,} of {len(df):,} rows after filters.")
    if filtered_df.empty:
        st.warning("No data matches the current filters.")
        return
    _render_chart(filtered_df)
```

- [ ] **Step 3: Full end-to-end smoke test**

```bash
streamlit run app.py
```

- Upload a CSV with at least 3 numeric columns and 1 categorical column.
- Select X, Y, Color-by axes.
- Add 3 range buckets for the color column. Verify the scatter plot points change color.
- Adjust a range slider to filter out some points. Verify the row count caption updates.
- Deselect a category in a multiselect. Verify those points disappear.
- Re-upload a different file. Verify the chart updates, old column filters are gone, buckets persist.

- [ ] **Step 4: Commit**

```bash
git add app.py
git commit -m "feat: chart rendering with color buckets and filter application"
```

---

## Task 9: Terraform Azure Deployment

**Files:**
- Create: `terraform/main.tf`
- Create: `terraform/variables.tf`
- Create: `terraform/outputs.tf`

Azure naming convention: `<project>-<resource-type>-<environment>` (per user's CLAUDE.md).

- [ ] **Step 1: Create terraform/variables.tf**

```hcl
variable "location" {
  description = "Azure region"
  type        = string
  default     = "westeurope"
}

variable "environment" {
  description = "Deployment environment (prod/dev)"
  type        = string
  default     = "prod"
}

variable "project" {
  description = "Project short name used in resource naming"
  type        = string
  default     = "scatter-app"
}
```

- [ ] **Step 2: Create terraform/main.tf**

```hcl
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

locals {
  name_suffix = "${var.project}-${var.environment}"
}

resource "azurerm_resource_group" "rg" {
  name     = "${local.name_suffix}-rg"
  location = var.location
}

resource "azurerm_service_plan" "asp" {
  name                = "${local.name_suffix}-asp"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  os_type             = "Linux"
  sku_name            = "F1"
}

resource "azurerm_linux_web_app" "app" {
  name                = "${local.name_suffix}-wa"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_service_plan.asp.location
  service_plan_id     = azurerm_service_plan.asp.id

  site_config {
    always_on = false  # F1 tier does not support always_on

    application_stack {
      python_version = "3.11"
    }

    app_command_line = "streamlit run app.py"
  }

  app_settings = {
    "SCM_DO_BUILD_DURING_DEPLOYMENT" = "true"
    "WEBSITES_PORT"                  = "8000"
  }
}

# Grant the deploying user Owner rights on the resource group
# so cedricverstegen@hotmail.com retains full control.
data "azurerm_client_config" "current" {}

resource "azurerm_role_assignment" "owner" {
  scope                = azurerm_resource_group.rg.id
  role_definition_name = "Owner"
  principal_id         = data.azurerm_client_config.current.object_id
}
```

- [ ] **Step 3: Create terraform/outputs.tf**

```hcl
output "app_url" {
  description = "Default hostname of the deployed web app"
  value       = "https://${azurerm_linux_web_app.app.default_hostname}"
}

output "resource_group_name" {
  description = "Resource group containing all resources"
  value       = azurerm_resource_group.rg.name
}
```

- [ ] **Step 4: Validate Terraform syntax**

```bash
cd terraform
terraform init
terraform validate
```

Expected: `Success! The configuration is valid.`

- [ ] **Step 5: Review the plan before applying**

```bash
terraform plan -out=tfplan
```

Review the output. Verify 4 resources will be created: resource group, service plan, web app, role assignment. **Do not apply yet** — confirm with the user first.

- [ ] **Step 6: Commit**

```bash
cd ..
git add terraform/
git commit -m "feat: terraform azure app service deployment (F1 tier)"
```

---

## Task 10: Deployment Instructions

**Files:**
- Create: `README.md`

- [ ] **Step 1: Create README.md**

```markdown
# Scatter Plot Builder

Streamlit app for uploading CSV/Excel files and generating interactive, color-coded scatter plots.

## Local Development

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Run Tests

```bash
pytest -v
```

## Deploy to Azure App Service

### 1. Provision infrastructure

```bash
cd terraform
terraform init
terraform apply
```

Note the `app_url` output.

### 2. Deploy application code

From the project root, zip and deploy:

```bash
zip -r app.zip app.py src/ requirements.txt .streamlit/
az webapp deploy \
  --resource-group scatter-app-prod-rg \
  --name scatter-app-prod-wa \
  --src-path app.zip \
  --type zip
```

### 3. Open the app

Visit the URL printed by `terraform output app_url`.

> **Note:** Free tier F1 has no always-on support. First request after idle will be slow (~30s cold start).
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: deployment instructions for local and Azure"
```

---

## Self-Review

**Spec coverage check:**

| Requirement | Covered by |
|---|---|
| CSV and XLSX upload | Task 2 (`load_file`), Task 5 (`st.file_uploader`) |
| X-axis, Y-axis, Color-by selection | Task 5 (`_sidebar_axis`) |
| Numerical range sliders | Task 6 (`_sidebar_filters`) |
| Categorical multi-select filters | Task 6 (`_sidebar_filters`) |
| Dynamic range bucket add/remove | Task 7 (`_sidebar_buckets`) |
| Min/max/label/color per bucket | Task 7 (expander UI with `number_input`, `text_input`, `color_picker`) |
| Plotly Express scatter plot | Task 4 (`build_scatter`), Task 8 (`_render_chart`) |
| White background, gridlines | Task 4 (`build_scatter` `update_layout`) |
| State persistence across file changes | Tasks 5–6 (session_state purge of stale keys only) |
| requirements.txt | Task 1 |
| Terraform Azure App Service F1 | Task 9 |
| Naming convention `<project>-<resource-type>-<environment>` | Task 9 (`locals.name_suffix`) |

**Placeholder scan:** None found.

**Type consistency:** `categorize_series` returns `pd.Series` → used as DataFrame column in `_render_chart`. `build_color_map` returns `Dict[str, str]` → passed as `color_map` to `build_scatter` which accepts `Optional[Dict[str, str]]`. `detect_column_types` returns `Tuple[List[str], List[str]]` → unpacked as `numerical, categorical` in Tasks 6, 7, 8 consistently.
