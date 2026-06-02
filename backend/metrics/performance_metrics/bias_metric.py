"""Bias (mean forecast error) performance metric."""
from statsmodels.tools.eval_measures import bias


def metric_loss(y_true, y_pred):
    """Return the mean signed error (bias) between actuals and forecasts."""
    return bias(y_true, y_pred)
