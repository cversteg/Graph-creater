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
