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
