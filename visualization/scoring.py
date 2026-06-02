"""Pure scoring/labeling helpers for the dashboard (no Streamlit/DB dependencies).

Extracted from app.py so they can be imported and unit-tested in isolation.
"""


def ks_metric(val):
    """Map a KS p-value to a drift label ('Yes' if < 0.05 else 'No')."""
    if val < 0.05:
        return 'Yes'
    else:
        return 'No'


def psi_metric(val):
    """Map a PSI value to a drift label ('No' < 0.1, 'Slight' < 0.2, else 'Extreme')."""
    if val < 0.1:
        return 'No'
    elif val < 0.2:
        return 'Slight'
    else:
        return 'Extreme'


def check_improvement(x):
    """Score a model's per-split scores for monotonic improvement.

    Given an ordered sequence of scores, count steps that do not worsen (+1) vs.
    worsen (-1); return the net count when positive, else 0. A single value is
    returned as-is (matching the original groupby.agg behavior).
    """
    values = x.values
    if len(values) > 1:
        calc = [1 if values[k] >= values[k + 1] else -1 for k in range(len(values) - 1)]
        calc = sum(calc)
        if calc > 0:
            return calc
        else:
            return 0
    else:
        return values
