"""Shared pytest fixtures and path bootstrap for the backend test suite.

Placing this at the backend root puts the package directories (control,
data_processing, forecasting, metrics) on sys.path so tests can import them the
same way the running services do.
"""
import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(__file__))


@pytest.fixture
def monthly_index():
    """48 monthly timestamps (4 years)."""
    return pd.date_range("2018-01-01", periods=48, freq="MS")


@pytest.fixture
def monthly_series(monthly_index):
    """Single-column 'value' DataFrame with a DatetimeIndex (model input shape)."""
    values = 100.0 + np.arange(48) * 2 + np.sin(np.arange(48)) * 5
    return pd.DataFrame({"value": values}, index=monthly_index)


@pytest.fixture
def series_frame(monthly_index):
    """period / ts_id / value frame with a DatetimeIndex (detector & imputer shape)."""
    df = pd.DataFrame({
        "period": monthly_index.astype(str),
        "ts_id": 1,
        "value": 100.0 + np.arange(48) * 2,
    })
    df.index = pd.to_datetime(df["period"])
    return df
