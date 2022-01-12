from statsmodels.tools.eval_measures import rmspe


def metric_loss(y_true, y_pred):
    return rmspe(y_true, y_pred)
