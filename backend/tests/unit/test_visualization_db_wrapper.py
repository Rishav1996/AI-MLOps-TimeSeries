"""Unit tests for the dashboard's pure data-transform helpers (visualization/db_wrapper.py).

These cover merge/parse/sort behaviour without a database: the chronological
sort that keeps line charts in time order, numeric split ordering, the
inner/outer join semantics, and the metric dtype coercion.
"""
import os
import sys

import pandas as pd

# db_wrapper lives in the sibling visualization project; add it to the path.
_VIS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "visualization"))
sys.path.insert(0, _VIS_DIR)

import db_wrapper  # noqa: E402


# --- merge_history ----------------------------------------------------------

def test_merge_history_sorts_chronologically():
    # rows arrive out of order; the merged frame must come back sorted by period
    ing = pd.DataFrame({
        "period": ["2020-03-01", "2020-01-01", "2020-02-01"],
        "ts_id": [1, 1, 1],
        "raw_history": [35, 23, 20],
    })
    dp = pd.DataFrame({
        "period": ["2020-03-01", "2020-01-01", "2020-02-01"],
        "ts_id": [1, 1, 1],
        "processed_history": [35, 23, 20],
    })
    out = db_wrapper.merge_history(ing, dp)
    assert out["period"].is_monotonic_increasing
    assert list(out["raw_history"]) == [23, 20, 35]
    assert out["period"].tolist() == [
        pd.Timestamp("2020-01-01"), pd.Timestamp("2020-02-01"), pd.Timestamp("2020-03-01")
    ]


def test_merge_history_sorts_within_each_series():
    ing = pd.DataFrame({
        "period": ["2020-02-01", "2020-01-01", "2020-02-01", "2020-01-01"],
        "ts_id": [2, 2, 1, 1],
        "raw_history": [1, 2, 3, 4],
    })
    dp = ing.rename(columns={"raw_history": "processed_history"})
    out = db_wrapper.merge_history(ing, dp)
    # series ordered ascending, and chronological within each series
    assert list(out["ts_id"]) == [1, 1, 2, 2]
    for _, group in out.groupby("ts_id"):
        assert group["period"].is_monotonic_increasing


def test_merge_history_outer_keeps_unmatched_periods():
    # processed history may be missing a period present in the raw history
    ing = pd.DataFrame({
        "period": ["2020-01-01", "2020-02-01"],
        "ts_id": [1, 1],
        "raw_history": [10, 20],
    })
    dp = pd.DataFrame({
        "period": ["2020-01-01"],
        "ts_id": [1],
        "processed_history": [11],
    })
    out = db_wrapper.merge_history(ing, dp)
    assert len(out) == 2
    assert out["processed_history"].isna().sum() == 1


def test_merge_history_parses_iso_dates_not_dayfirst():
    # canonical YYYY-MM-DD must parse as ISO (2020-02-01 == 1 Feb, not 2 Jan)
    ing = pd.DataFrame({"period": ["2020-02-01"], "ts_id": [1], "raw_history": [1]})
    dp = pd.DataFrame({"period": ["2020-02-01"], "ts_id": [1], "processed_history": [1]})
    out = db_wrapper.merge_history(ing, dp)
    assert out["period"].iloc[0] == pd.Timestamp("2020-02-01")


# --- merge_forecast ---------------------------------------------------------

def _actual(periods, ts_id=1):
    return pd.DataFrame({
        "period": periods,
        "ts_id": [ts_id] * len(periods),
        "raw_history": list(range(len(periods))),
    })


def test_merge_forecast_sorts_by_time_within_split():
    actual = _actual(["2020-01-01", "2020-02-01", "2020-03-01"])
    forecast = pd.DataFrame({
        "period": ["2020-03-01", "2020-01-01", "2020-02-01"],
        "ts_id": [1, 1, 1],
        "forecast": [33.0, 11.0, 22.0],
        "split_window": ["expanding"] * 3,
        "split_no": ["1", "1", "1"],
        "model_name": ["arima"] * 3,
    })
    out = db_wrapper.merge_forecast(actual, forecast)
    assert out["period"].is_monotonic_increasing
    assert list(out["forecast"]) == [11.0, 22.0, 33.0]
    # the numeric sort helper column must not leak into the result
    assert "_split_no" not in out.columns


def test_merge_forecast_orders_splits_numerically():
    # split_no is a string; a naive lexicographic sort would put '10' before '2'
    actual = _actual(["2020-01-01"])
    forecast = pd.DataFrame({
        "period": ["2020-01-01"] * 3,
        "ts_id": [1, 1, 1],
        "forecast": [2.0, 10.0, 1.0],
        "split_window": ["expanding"] * 3,
        "split_no": ["2", "10", "1"],
        "model_name": ["arima"] * 3,
    })
    out = db_wrapper.merge_forecast(actual, forecast)
    assert list(out["split_no"]) == ["1", "2", "10"]


def test_merge_forecast_inner_join_drops_unmatched():
    actual = _actual(["2020-01-01"])
    forecast = pd.DataFrame({
        "period": ["2020-02-01"],
        "ts_id": [1],
        "forecast": [99.0],
        "split_window": ["expanding"],
        "split_no": ["1"],
        "model_name": ["arima"],
    })
    out = db_wrapper.merge_forecast(actual, forecast)
    assert out.empty


# --- normalize_metric -------------------------------------------------------

def test_normalize_metric_coerces_dtypes():
    raw = pd.DataFrame({
        "ts_id": [1, 1],
        "model_name": ["arima", "ets"],
        "split_window": ["expanding", "expanding"],
        "split_no": [1, 2],            # ints out of the DB (split_no + 1)
        "metric_name": ["rmse", "rmse"],
        "metric_value": ["1.5", "2.5"],  # strings out of the DB
    })
    out = db_wrapper.normalize_metric(raw)
    assert out["split_no"].tolist() == ["1", "2"]
    assert out["metric_value"].tolist() == [1.5, 2.5]
    assert out["metric_value"].dtype == float


def test_normalize_metric_does_not_mutate_input():
    raw = pd.DataFrame({
        "ts_id": [1],
        "model_name": ["arima"],
        "split_window": ["expanding"],
        "split_no": [1],
        "metric_name": ["rmse"],
        "metric_value": ["1.5"],
    })
    db_wrapper.normalize_metric(raw)
    # original frame is untouched (still int / str)
    assert raw["split_no"].tolist() == [1]
    assert raw["metric_value"].tolist() == ["1.5"]
