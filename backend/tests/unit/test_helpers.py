"""Unit tests for pure helper functions (no DB / Redis required).

Covers the pandas-2-safe frequency/seasonality inference, time/auth helpers, and the
Celery wait_for_tasks helper (with AsyncResult mocked).
"""
import hashlib

import pandas as pd
import pytest

from forecasting.forecasting_helper import (
    _delta_days,
    seasonal_period,
    freq_string,
    wait_for_tasks,
)
from control.control_helper import convert_to_time, password_hashing


# --- seasonal_period --------------------------------------------------------

@pytest.mark.parametrize("freq,expected", [
    ("D", 365),    # daily
    ("W", 52),     # weekly
    ("MS", 12),    # monthly
])
def test_seasonal_period_known_cadences(freq, expected):
    idx = pd.date_range("2020-01-01", periods=40, freq=freq)
    assert seasonal_period(idx) == expected


def test_seasonal_period_yearly_falls_back_to_default():
    idx = pd.date_range("2000-01-01", periods=10, freq="YS")
    assert seasonal_period(idx, default=7) == 7


def test_seasonal_period_subdaily_and_short_use_default():
    hourly = pd.date_range("2020-01-01", periods=10, freq="h")
    assert seasonal_period(hourly, default=2) == 2
    assert seasonal_period(pd.DatetimeIndex(["2020-01-01"]), default=3) == 3


# --- freq_string ------------------------------------------------------------

@pytest.mark.parametrize("freq,expected", [
    ("s", "S"),
    ("h", "H"),
    ("D", "D"),
    ("W", "W"),
    ("MS", "MS"),
    ("YS", "YS"),
])
def test_freq_string(freq, expected):
    idx = pd.date_range("2020-01-01", periods=6, freq=freq)
    assert freq_string(idx) == expected


# --- _delta_days ------------------------------------------------------------

def test_delta_days():
    idx = pd.date_range("2020-01-01", periods=3, freq="D")
    assert _delta_days(idx) == 1
    assert _delta_days(pd.DatetimeIndex(["2020-01-01"])) is None


# --- convert_to_time --------------------------------------------------------

@pytest.mark.parametrize("seconds,expected", [
    (0, "0 h 00 m 00 s"),
    (30, "0 h 00 m 30 s"),
    (3661, "1 h 01 m 01 s"),
])
def test_convert_to_time(seconds, expected):
    assert convert_to_time(seconds) == expected


# --- password_hashing -------------------------------------------------------

def test_password_hashing_matches_md5():
    assert password_hashing("secret") == hashlib.md5(b"secret").hexdigest()
    # deterministic
    assert password_hashing("secret") == password_hashing("secret")


# --- wait_for_tasks (Celery mocked) ----------------------------------------

class _FakeAsyncResult:
    registry = {}

    def __init__(self, task_id, app=None):
        self.id = task_id

    @property
    def state(self):
        return _FakeAsyncResult.registry[self.id][0]

    def get(self):
        return _FakeAsyncResult.registry[self.id][1]


def test_wait_for_tasks_returns_results_in_order(monkeypatch):
    import celery.result as cr
    _FakeAsyncResult.registry = {"a": ("SUCCESS", {"v": 1}), "b": ("SUCCESS", {"v": 2})}
    monkeypatch.setattr(cr, "AsyncResult", _FakeAsyncResult)
    assert wait_for_tasks(["a", "b"]) == [{"v": 1}, {"v": 2}]


def test_wait_for_tasks_raises_on_failure(monkeypatch):
    import celery.result as cr
    _FakeAsyncResult.registry = {"a": ("SUCCESS", {"v": 1}), "b": ("FAILURE", None)}
    monkeypatch.setattr(cr, "AsyncResult", _FakeAsyncResult)
    with pytest.raises(Exception):
        wait_for_tasks(["a", "b"])
