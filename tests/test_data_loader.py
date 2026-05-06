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
