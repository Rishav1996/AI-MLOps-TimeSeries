"""Unit tests for ingestion period normalization (control_helper.normalize_period)."""
import os

import pandas as pd

from control.control_helper import normalize_period

_SAMPLE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "sample data", "sample.csv"))


def test_normalize_ddmmyyyy():
    s = pd.Series(["01-01-2020", "01-02-2020", "15-03-2021"])
    out = normalize_period(s).tolist()
    # 01-02-2020 is day-first -> 1 Feb 2020 (NOT 2 Jan)
    assert out == ["2020-01-01", "2020-02-01", "2021-03-15"]


def test_normalize_iso_passthrough():
    s = pd.Series(["2020-01-01", "2020-02-01"])
    assert normalize_period(s).tolist() == ["2020-01-01", "2020-02-01"]


def test_normalize_real_sample_is_monthly_first_of_month():
    df = pd.read_csv(_SAMPLE)
    norm = normalize_period(df["period"])
    parsed = pd.to_datetime(norm)
    # every period is the first of a month
    assert (parsed.dt.day == 1).all()
    # series 1 spans 24 consecutive months
    s1 = parsed[df["ts_id"] == 1].sort_values()
    deltas = s1.diff().dropna().dt.days
    assert deltas.between(28, 31).all()
    assert len(s1) == 24
