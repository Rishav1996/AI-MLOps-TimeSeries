"""Unit tests for the cross-validation window splitters."""
import numpy as np
import pandas as pd

from forecasting.timeseries_splitter import expanding_window_splitter, sliding_window_splitter


def _frame(n=24):
    idx = pd.date_range("2020-01-01", periods=n, freq="MS")
    return pd.DataFrame({"value": np.arange(n, dtype=float)}, index=idx)


def test_expanding_window_train_grows():
    splits = list(expanding_window_splitter.splitter(_frame(), initial_window=12, forecast_length=3))
    assert len(splits) >= 2
    train_lengths = [len(train) for train, _ in splits]
    # each successive training window is at least as large as the previous
    assert train_lengths == sorted(train_lengths)
    assert train_lengths[-1] > train_lengths[0]
    # sktime's fh here is a single horizon point, so each test window is non-empty
    assert all(len(test) >= 1 for _, test in splits)


def test_sliding_window_train_constant():
    splits = list(sliding_window_splitter.splitter(_frame(), window_length=12, forecast_length=3))
    assert len(splits) >= 2
    train_lengths = {len(train) for train, _ in splits}
    assert train_lengths == {12}
    assert all(len(test) >= 1 for _, test in splits)
