"""MAPE (mean absolute percentage error) performance metric, capped at 1.0."""
import math

from sktime.performance_metrics.forecasting import mean_absolute_percentage_error


def metric_loss(y_true, y_pred):
    """Return the (non-symmetric) MAPE, clamped to a maximum of 1.0.

    A zero actual makes the percentage error undefined (x/0 -> inf, 0/0 -> nan).
    Such non-finite results are treated as the 1.0 ceiling so the metric stays
    finite -- train_metric_table.metric_value is NOT NULL, and a nan would abort
    the whole write with an IntegrityError.
    """
    metric_result = mean_absolute_percentage_error(y_true, y_pred, symmetric=False)
    if not math.isfinite(metric_result) or metric_result > 1.0:
        return 1.0
    return metric_result
