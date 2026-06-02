"""RMSPE (root mean squared percentage error) performance metric."""
from statsmodels.tools.eval_measures import rmspe


def metric_loss(y_true, y_pred):
    """Return the root mean squared percentage error between actuals and forecasts."""
    return rmspe(y_true, y_pred)
