"""Unit tests for the dashboard's pure scoring/labeling helpers (visualization/scoring.py)."""
import os
import sys

import pandas as pd
import pytest

# scoring.py lives in the sibling visualization project; add it to the path.
_VIS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "visualization"))
sys.path.insert(0, _VIS_DIR)

import scoring  # noqa: E402


@pytest.mark.parametrize("val,expected", [(0.01, "Yes"), (0.05, "No"), (0.5, "No")])
def test_ks_metric_label(val, expected):
    assert scoring.ks_metric(val) == expected


@pytest.mark.parametrize("val,expected", [
    (0.05, "No"),
    (0.15, "Slight"),
    (0.5, "Extreme"),
])
def test_psi_metric_label(val, expected):
    assert scoring.psi_metric(val) == expected


def test_check_improvement_monotonic_non_worsening():
    # scores never worsen across splits -> positive net count
    assert scoring.check_improvement(pd.Series([0.5, 0.4, 0.3])) == 2


def test_check_improvement_worsening_returns_zero():
    # net worsening -> 0
    assert scoring.check_improvement(pd.Series([0.1, 0.2, 0.3])) == 0


def test_check_improvement_single_value():
    out = scoring.check_improvement(pd.Series([0.42]))
    assert list(out) == [0.42]
