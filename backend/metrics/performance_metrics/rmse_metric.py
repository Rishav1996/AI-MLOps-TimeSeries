from statsmodels.tools.eval_measures import rmse


def metric_loss(y_true, y_pred):
    return rmse(y_true, y_pred)
