from statsmodels.tools.eval_measures import mse
from math import log


def metric_loss(y_true, y_pred):
    # guard against log(0) when the forecast matches the actuals exactly
    error = max(float(mse(y_true, y_pred)), 1e-10)
    return len(y_pred) * log(error) + 2 * 1
