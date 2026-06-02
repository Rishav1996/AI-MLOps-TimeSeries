"""RMSPE (root mean squared percentage error) performance metric."""
import numpy as np


def metric_loss(y_true, y_pred):
    """Return RMSPE, skipping points whose actual is zero (percentage undefined).

    Equals ``sqrt(mean(((y_true - y_pred) / y_true) ** 2))`` when no actual is
    zero. Zero-actual points are dropped rather than producing inf/nan (statsmodels'
    ``rmspe`` returns nan there by default), so the result stays finite --
    train_metric_table.metric_value is NOT NULL. Returns 0.0 if every actual is zero.
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    mask = y_true != 0
    if not mask.any():
        return 0.0
    pct_error = (y_true[mask] - y_pred[mask]) / y_true[mask]
    return float(np.sqrt(np.mean(pct_error ** 2)))
