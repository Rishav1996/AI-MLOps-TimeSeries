from statsmodels.tools.eval_measures import mse
from math import log


def metric_loss(y_true, y_pred):
    return len(y_true) * log(mse(y_true, y_pred)) + 1 * log(len(y_true))
