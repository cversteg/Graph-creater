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
