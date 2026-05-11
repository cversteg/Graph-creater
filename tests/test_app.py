import importlib
import sys
import types

import plotly.graph_objects as go


def _load_app_module():
    fake_streamlit = types.SimpleNamespace(set_page_config=lambda **kwargs: None)
    sys.modules["streamlit"] = fake_streamlit
    return importlib.import_module("app")


def test_safe_png_bytes_returns_none_when_export_fails():
    app_module = _load_app_module()
    fig = go.Figure()

    def _raise(*args, **kwargs):
        raise RuntimeError("kaleido export failed")

    fig.to_image = _raise

    assert app_module._safe_png_bytes(fig) is None


def test_figure_for_png_export_converts_scattergl_to_scatter():
    app_module = _load_app_module()
    fig = go.Figure(data=[go.Scattergl(x=[1, 2], y=[3, 4], mode="markers")])

    export_fig = app_module._figure_for_png_export(fig)

    assert export_fig.data[0].type == "scatter"


def test_sorted_unique_values_handles_mixed_types():
    app_module = _load_app_module()
    series = app_module.pd.Series(["A", 1.2, "B", 2.4, None, "A"])

    result = app_module._sorted_unique_values(series)

    assert result == [1.2, 2.4, "A", "B"]


def test_make_arrow_safe_preview_df_stringifies_mixed_object_columns():
    app_module = _load_app_module()
    df = app_module.pd.DataFrame(
        {
            "mixed": [1.5, "bad-data", None],
            "plain_text": ["a", "b", None],
        }
    )

    safe_df = app_module._make_arrow_safe_preview_df(df)

    assert safe_df["mixed"].tolist() == ["1.5", "bad-data", "None"]
    assert safe_df["plain_text"].tolist() == ["a", "b", None]


def test_safe_numeric_bounds_returns_none_for_all_nan():
    app_module = _load_app_module()
    series = app_module.pd.Series([float("nan"), float("nan")], dtype="float64")

    assert app_module._safe_numeric_bounds(series) is None


def test_default_axis_columns_handles_empty_dataframe():
    app_module = _load_app_module()

    assert app_module._default_axis_columns([]) == (None, None, None)


def test_sample_for_plot_returns_same_df_when_small():
    app_module = _load_app_module()
    df = app_module.pd.DataFrame({"x": [1, 2, 3]})

    result = app_module._sample_for_plot(df, max_points=10)

    assert len(result) == 3
    assert result.equals(df)


def test_sample_for_plot_limits_large_df_size():
    app_module = _load_app_module()
    df = app_module.pd.DataFrame({"x": list(range(50_000))})

    result = app_module._sample_for_plot(df, max_points=1000)

    assert len(result) == 1000
