"""RMSE (root mean squared error) performance metric."""
from statsmodels.tools.eval_measures import rmse


def metric_loss(y_true, y_pred):
    """Return the root mean squared error between actuals and forecasts."""
    return rmse(y_true, y_pred)
