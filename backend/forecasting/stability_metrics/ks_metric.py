from scipy import stats
import numpy as np


def metric_loss(expected, actual):
    expected = np.array(expected).flatten()
    actual = np.array(actual).flatten()
    return stats.ks_2samp(expected, actual, mode='exact', alternative='two-sided')[1]
