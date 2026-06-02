"""Kolmogorov-Smirnov two-sample test: distribution-drift between two samples."""
from scipy import stats
import numpy as np


def metric_loss(expected, actual):
    """Return the two-sample KS p-value (low p = distributions differ / drift)."""
    expected = np.array(expected).flatten()
    actual = np.array(actual).flatten()
    return stats.ks_2samp(expected, actual, mode='exact', alternative='two-sided')[1]
