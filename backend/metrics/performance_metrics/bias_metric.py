from statsmodels.tools.eval_measures import bias


def metric_loss(y_true, y_pred):
    return bias(y_true, y_pred)
