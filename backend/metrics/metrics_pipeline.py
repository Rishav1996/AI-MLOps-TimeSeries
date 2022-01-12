from metrics.metrics_config import database_utils
from metrics.metrics_helper import db_engine
from metrics.performance_metrics import rmse_metric, rmspe_metric, mape_metric, aic_metric, bic_metric, bias_metric
import pandas as pd


def get_data(train_id):
    engine = db_engine()
    conn = engine.connect()
    ing_id, fcst_id = conn.execute(
        f"select data_ing_id, data_fcst_id from train_history_table where train_id={train_id}").fetchone()

    ing_data = conn.execute(f"select ts_id, period, value from data_table where data_id={ing_id}").fetchall()
    ing_data = pd.DataFrame(ing_data, columns=['ts_id', 'period', 'historical'])

    fcst_data = conn.execute(
        f"select ts_id, period, value, split_window, split_no, model_id from data_table where data_id={fcst_id}").fetchall()
    fcst_data = pd.DataFrame(fcst_data, columns=['ts_id', 'period', 'forecast', 'split_window', 'split_no', 'model_id'])

    data = pd.merge(ing_data, fcst_data, on=['ts_id', 'period'], how='outer')
    data = data.sort_values(by=['ts_id', 'period'])
    conn.close()
    return data


def get_metrics_list():
    engine = db_engine()
    conn = engine.connect()
    metrics_list = conn.execute("select metric_id, metric_name from metric_table").fetchall()
    metrics_list = {metric_name: metric_id for metric_id, metric_name in metrics_list}
    conn.close()
    return metrics_list


def generate_metrics(data):
    if 'period' not in data.columns or 'historical' not in data.columns or 'forecast' not in data.columns:
        return

    data.sort_values('period', inplace=True)

    y_pred = data.forecast.values
    y_true = data.historical.values

    metrics_list = get_metrics_list()
    metric_table = pd.DataFrame(columns=['metric_id', 'metric_value'])

    if 'rmse' in list(metrics_list.keys()):
        rmse = round(rmse_metric.metric_loss(y_true, y_pred), 10)
        metric_table = metric_table.append({'metric_id': metrics_list['rmse'], 'metric_value': rmse}, ignore_index=True)

    if 'rmspe' in list(metrics_list.keys()):
        rmspe = round(rmspe_metric.metric_loss(y_true, y_pred), 10)
        metric_table = metric_table.append({'metric_id': metrics_list['rmspe'], 'metric_value': rmspe},
                                           ignore_index=True)

    if 'mape' in list(metrics_list.keys()):
        mape = round(mape_metric.metric_loss(y_true, y_pred), 10)
        metric_table = metric_table.append({'metric_id': metrics_list['mape'], 'metric_value': mape}, ignore_index=True)

    if 'aic' in list(metrics_list.keys()):
        aic = round(aic_metric.metric_loss(y_true, y_pred), 10)
        metric_table = metric_table.append({'metric_id': metrics_list['aic'], 'metric_value': aic}, ignore_index=True)

    if 'bic' in list(metrics_list.keys()):
        bic = round(bic_metric.metric_loss(y_true, y_pred), 10)
        metric_table = metric_table.append({'metric_id': metrics_list['bic'], 'metric_value': bic}, ignore_index=True)

    if 'bias' in list(metrics_list.keys()):
        bias = round(bias_metric.metric_loss(y_true, y_pred), 10)
        metric_table = metric_table.append({'metric_id': metrics_list['bias'], 'metric_value': bias}, ignore_index=True)

    return metric_table


def calculate_metric(train_id):
    data = get_data(train_id)

    test_data = data[~data['forecast'].isna()].copy()
    test_data['key'] = test_data['ts_id'].map(str) + '_' + test_data['model_id'].map(str) + '_' + test_data[
        'split_window'].map(str) + '_' + test_data['split_no'].map(str)
    metric_result = test_data.groupby('key')[['period', 'historical', 'forecast']].apply(generate_metrics).reset_index(
        level=0)
    metric_result['train_id'] = train_id
    metric_result['ts_id'] = metric_result['key'].str.split('_').str[0]
    metric_result['model_id'] = metric_result['key'].str.split('_').str[1]
    metric_result['split_window'] = metric_result['key'].str.split('_').str[2]
    metric_result['split_no'] = metric_result['key'].str.split('_').str[3]

    actual_data = data.drop_duplicates(subset=['ts_id', 'period'], keep='first').copy()
    actual_data.sort_values(by=['ts_id', 'period'], inplace=True)

    metric_result.drop(columns=['key'], inplace=True)

    engine = db_engine()
    metric_result.to_sql('train_metric_table', engine, schema=database_utils["DATABASE"],
                                      if_exists='append',
                                      index=False)

    return
