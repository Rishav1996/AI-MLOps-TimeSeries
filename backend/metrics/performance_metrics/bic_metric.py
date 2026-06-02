"""BIC-style information criterion performance metric (from forecast MSE)."""
from statsmodels.tools.eval_measures import mse
from math import log


def metric_loss(y_true, y_pred):
    """Return a BIC-style score from the forecast MSE; guards against log(0)."""
    # guard against log(0) when the forecast matches the actuals exactly
    error = max(float(mse(y_true, y_pred)), 1e-10)
    return len(y_true) * log(error) + 1 * log(len(y_true))
