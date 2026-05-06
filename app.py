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
