"""MAPE (mean absolute percentage error) performance metric, capped at 1.0."""
from sktime.performance_metrics.forecasting import mean_absolute_percentage_error


def metric_loss(y_true, y_pred):
    """Return the (non-symmetric) MAPE, clamped to a maximum of 1.0."""
    metric_result = mean_absolute_percentage_error(y_true, y_pred, symmetric=False)
    if metric_result > 1.0:
        return 1.0
    else:
        return metric_result
