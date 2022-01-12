from statsmodels.tools.eval_measures import mse
from math import log


def metric_loss(y_true, y_pred):
    return len(y_pred) * log(mse(y_true, y_pred)) + 2 * 1
