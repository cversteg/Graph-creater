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


def _apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    mask = pd.Series(True, index=df.index)
    for col, (low, high) in st.session_state.col_filters.items():
        if col in df.columns:
            mask &= (df[col] >= low) & (df[col] <= high)
    for col, selected in st.session_state.cat_filters.items():
        if col in df.columns and selected:
            mask &= df[col].isin(selected)
    return df[mask]


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
    _sidebar_filters(df)
    _sidebar_buckets(df)

    st.write(f"Loaded **{st.session_state.filename}** — {len(df):,} rows, {len(df.columns)} columns")
    filtered_df = _apply_filters(df)
    st.caption(f"Showing {len(filtered_df):,} of {len(df):,} rows after filters.")
    if filtered_df.empty:
        st.warning("No data matches the current filters.")
        return
    _render_chart(filtered_df)


if __name__ == "__main__":
    main()
