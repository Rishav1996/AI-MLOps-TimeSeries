import getopt, sys
from datetime import datetime
from forecasting.ensemble_models import ensemble_model, auto_ensemble_model
from forecasting.stability_metrics import psi_metric, ks_metric
from forecasting.forecasting_helper import get_time_now, db_engine, get_default_parameters_in_dict, get_train_parameters_in_dict
from forecasting.forecasting_config import forecasting_stages, database_utils, forecasting_parameters
from forecasting.timeseries_splitter import expanding_window_splitter, sliding_window_splitter
from forecasting.models import auto_arima_model, ets_model, polynomial_trend_model, theta_model, prophet_model, naive_model
import pandas as pd
import warnings
from sktime.forecasting.all import ForecastingHorizon, ExponentialSmoothing, AutoARIMA, ThetaForecaster, NaiveForecaster, \
    PolynomialTrendForecaster
from sqlalchemy import text
from celery_app import celery_client
from celery.result import AsyncResult


warnings.filterwarnings("ignore")


def get_data_processing_id(train_id):
    engine = db_engine()
    conn = engine.connect()
    data_id = conn.execute(text(f"select data_dp_id from train_history_table where train_id={train_id}")).fetchone()[0]
    conn.close()
    return int(data_id)


def get_user_id(train_id):
    engine = db_engine()
    conn = engine.connect()
    user_id = conn.execute(
        text(f"select user_id from data_history_table where data_id in (select data_ing_id from train_history_table where train_id={train_id})")).fetchone()[
        0]
    conn.close()
    return int(user_id)


def fetch_models_list():
    engine = db_engine()
    conn = engine.connect()
    models = conn.execute(text(f"select model_id, model_name from model_table")).fetchall()
    models = pd.DataFrame(models, columns=['model_id', 'model_name'])
    models.index = models['model_id']
    models.drop(columns=['model_id'], inplace=True)
    models = models.to_dict()['model_name']
    conn.close()
    return models


def generate_fcst_id():
    engine = db_engine()
    conn = engine.connect()
    data_id = conn.execute(text("select ifnull(max(data_id), 0) from data_history_table")).fetchone()[0] + 1
    conn.close()
    return int(data_id)


def get_data(data_id):
    engine = db_engine()
    conn = engine.connect()
    data = conn.execute(text(f"select period, ts_id, value from data_table where data_id={data_id}")).fetchall()
    data = pd.DataFrame(data)
    data.columns = ['period', 'ts_id', 'value']
    conn.close()
    return data


def get_model(model_id):
    engine = db_engine()
    conn = engine.connect()
    model = conn.execute(text(f"select model_name from model_table where model_id={model_id}")).fetchone()[0]
    conn.close()
    return model


def models_forecasts(train, forecast_length, future_periods, model_name='', model_lists=None, ensemble=False,
                     auto_ensemble=False):
    forecast_length = ForecastingHorizon(list(range(1, forecast_length + 1)))
    if model_name == 'arima':
        forecasts = auto_arima_model.model(train, forecast_length)
        forecasts.index = future_periods
        forecasts = forecasts.to_frame(name='value')
        forecasts.reset_index(inplace=True)
        forecasts.rename(columns={'index': 'period'}, inplace=True)
        return forecasts
    if model_name == 'ets':
        forecasts = ets_model.model(train, forecast_length)
        forecasts.index = future_periods
        forecasts = forecasts.to_frame(name='value')
        forecasts.reset_index(inplace=True)
        forecasts.rename(columns={'index': 'period'}, inplace=True)
        return forecasts
    if model_name == 'naive':
        forecasts = naive_model.model(train, forecast_length)
        forecasts.index = future_periods
        forecasts = forecasts.to_frame(name='value')
        forecasts.reset_index(inplace=True)
        forecasts.rename(columns={'index': 'period'}, inplace=True)
        return forecasts
    if model_name == 'poly_trend':
        forecasts = polynomial_trend_model.model(train, forecast_length)
        forecasts.index = future_periods
        forecasts = forecasts.to_frame(name='value')
        forecasts.reset_index(inplace=True)
        forecasts.rename(columns={'index': 'period'}, inplace=True)
        return forecasts
    if model_name == 'theta':
        forecasts = theta_model.model(train, forecast_length)
        forecasts.index = future_periods
        forecasts = forecasts.to_frame(name='value')
        forecasts.reset_index(inplace=True)
        forecasts.rename(columns={'index': 'period'}, inplace=True)
        return forecasts
    if model_name == 'prophet':
        forecasts = prophet_model.model(train, forecast_length)
        forecasts.index = future_periods
        forecasts = forecasts.to_frame(name='value')
        forecasts.reset_index(inplace=True)
        forecasts.rename(columns={'index': 'period'}, inplace=True)
        return forecasts
    if len(model_lists) > 0 and (auto_ensemble or ensemble):
        if auto_ensemble:
            forecasts = auto_ensemble_model.model(train, forecast_length, n_models=model_lists)
        if ensemble:
            forecasts = ensemble_model.model(train, forecast_length, n_models=model_lists)
        forecasts.index = future_periods
        forecasts = forecasts.to_frame(name='value')
        forecasts.reset_index(inplace=True)
        forecasts.rename(columns={'index': 'period'}, inplace=True)
        return forecasts
    return train


def insert_metric(train_id, ts_id, model_id, split_window, split_no, metric_id, metric_value):
    engine = db_engine()
    conn = engine.connect()
    conn.execute(text(f"insert into train_metric_table values ({train_id}, {ts_id}, {model_id}, '{split_window}', {split_no}, "
                 f"{metric_id}, '{metric_value}')"))
    conn.commit()
    conn.close()


def get_metrics_list():
    engine = db_engine()
    conn = engine.connect()
    metrics_list = conn.execute(text("select metric_id, metric_name from metric_table")).fetchall()
    metrics_list = {metric_name: metric_id for metric_id, metric_name in metrics_list}
    conn.close()
    return metrics_list


@celery_client.task(autoretry_for=(Exception,), default_retry_delay=5, retry_kwargs={'max_retries': 3})
def simple_forecasting(data, test_size, forecast_horizon, data_split, train_id):
    data = pd.DataFrame(data)
    if 'value' not in data.columns or 'period' not in data.columns or 'key' not in data.columns:
        return

    data.index = data['period'].map(pd.to_datetime)
    model_name = get_model(data['key'].drop_duplicates().values[0].split('_')[1])
    splits = {}
    metrics_list = get_metrics_list()

    if data_split == 'expanding' or data_split == 'both':
        initial_window = int(round(data.shape[0] * (1 - test_size), 0))
        forecast_length = int(round(forecast_horizon * (data.shape[0] - initial_window), 0))
        forecast_length = 3 if forecast_length == 0 else forecast_length
        initial_window = initial_window + (data.shape[0] - initial_window) % forecast_length
        data_splitter = expanding_window_splitter.splitter(data['value'], initial_window, forecast_length)
        train_test_split = []
        for i, j in data_splitter:
            train_test_split.append([i, list(range(i[-1] + 1, j[0] + 1))])
        splits['expanding'] = train_test_split

    if data_split == 'sliding' or data_split == 'both':
        window_length = int(round(data.shape[0] * (1 - test_size), 0))
        forecast_length = int(round(forecast_horizon * (data.shape[0] - window_length), 0))
        forecast_length = 3 if forecast_length == 0 else forecast_length
        window_length = window_length + (data.shape[0] - window_length) % forecast_length
        data_splitter = sliding_window_splitter.splitter(data['value'], window_length, forecast_length)
        train_test_split = []
        for i, j in data_splitter:
            train_test_split.append([i, list(range(i[-1] + 1, j[0] + 1))])
        splits['sliding'] = train_test_split

    forecast = pd.DataFrame(columns=['value', 'split_window', 'split_no'])

    for i in splits.keys():
        for split_no, j in enumerate(splits[i]):
            train_index = j[0]
            test_index = j[1]
            train_data = data.iloc[train_index][['value']]
            test_data = data.iloc[test_index][['value']]
            test_periods = data.iloc[test_index].index.values
            sub_forecast = models_forecasts(train=train_data, forecast_length=len(test_periods),
                                            future_periods=test_periods, model_name=model_name)
            sub_forecast['split_window'] = i
            sub_forecast['split_no'] = split_no
            sub_forecast['key'] = data['key'].drop_duplicates().values[0]
            psi = round(psi_metric.metric_loss(train_data.values, test_data.values), 10)
            ks = round(ks_metric.metric_loss(train_data.values, test_data.values), 10)

            insert_metric(train_id=train_id, ts_id=data['key'].drop_duplicates().values[0].split('_')[0],
                          model_id=data['key'].drop_duplicates().values[0].split('_')[1], split_window=i, split_no=split_no,
                          metric_id=metrics_list['psi'], metric_value=psi)

            insert_metric(train_id=train_id, ts_id=data['key'].drop_duplicates().values[0].split('_')[0],
                          model_id=data['key'].drop_duplicates().values[0].split('_')[1], split_window=i,
                          split_no=split_no,
                          metric_id=metrics_list['ks'], metric_value=ks)

            forecast = pd.concat([forecast, sub_forecast], axis=0)

    forecast.reset_index(drop=True, inplace=True)
    return forecast.to_dict()


@celery_client.task(autoretry_for=(Exception,), default_retry_delay=5, retry_kwargs={'max_retries': 3})
def ensemble_forecasts(data, test_size, forecast_horizon, data_split, model_ids, train_id, ensemble=False, auto_ensemble=False):
    data = pd.DataFrame(data)
    if 'value' not in data.columns or 'period' not in data.columns or 'ts_id' not in data.columns:
        return

    data.index = data['period'].map(pd.to_datetime)
    model_names = [get_model(i) for i in model_ids]
    metrics_list = get_metrics_list()
    splits = {}

    forecast_length = 1
    date_diff = pd.Timedelta('1M')

    if data_split == 'expanding' or data_split == 'both':
        initial_window = int(round(data.shape[0] * (1 - test_size), 0))
        forecast_length = int(round(forecast_horizon * (data.shape[0] - initial_window), 0))
        forecast_length = 3 if forecast_length == 0 else forecast_length
        initial_window = initial_window + (data.shape[0] - initial_window) % forecast_length
        date_diff = data.index[1] - data.index[0]
        data_splitter = expanding_window_splitter.splitter(data[['value']], initial_window, forecast_length)

        train_test_split = []
        for i, j in data_splitter:
            train_test_split.append([i, list(range(i[-1] + 1, j[0] + 1))])
        splits['expanding'] = train_test_split

    if data_split == 'sliding' or data_split == 'both':
        window_length = int(round(data.shape[0] * (1 - test_size), 0))
        forecast_length = int(round(forecast_horizon * (data.shape[0] - window_length), 0))
        forecast_length = 3 if forecast_length == 0 else forecast_length
        window_length = window_length + (data.shape[0] - window_length) % forecast_length
        date_diff = data.index[1] - data.index[0]
        data_splitter = sliding_window_splitter.splitter(data[['value']], window_length, forecast_length)

        train_test_split = []
        for i, j in data_splitter:
            train_test_split.append([i, list(range(i[-1] + 1, j[0] + 1))])
        splits['sliding'] = train_test_split

    sp = 1
    if date_diff == pd.Timedelta('1D'):
        sp = 365
    elif date_diff == pd.Timedelta('1M'):
        sp = 12
    elif date_diff == pd.Timedelta('1W'):
        sp = 52
    if data.shape[0] < (2 * sp):
        sp = 2

    model_list = []

    for i in model_names:
        if i == 'arima':
            model_list.append((i, AutoARIMA(maxiter=20)))
        if i == 'poly_trend':
            model_list.append((i, PolynomialTrendForecaster(degree=3)))
        if i == 'theta':
            model_list.append((i, ThetaForecaster(sp=sp)))
        if i == 'naive':
            model_list.append((i, NaiveForecaster(sp=sp)))

    forecast = pd.DataFrame(columns=['value', 'split_window', 'split_no'])

    for i in splits.keys():
        for split_no, j in enumerate(splits[i]):
            train_index = j[0]
            test_index = j[1]
            train_data = data.iloc[train_index][['value']]
            test_data = data.iloc[test_index][['value']]
            test_periods = data.iloc[test_index].index.values
            sub_forecast = models_forecasts(train=train_data, forecast_length=len(test_periods),
                                            future_periods=test_periods, model_lists=model_list,
                                            ensemble=ensemble, auto_ensemble=auto_ensemble)
            sub_forecast['split_window'] = i
            sub_forecast['split_no'] = split_no
            sub_forecast['ts_id'] = int(data['ts_id'].drop_duplicates().values[0])

            psi = round(psi_metric.metric_loss(train_data.values, test_data.values), 10)
            ks = round(ks_metric.metric_loss(train_data.values, test_data.values), 10)

            insert_metric(train_id=train_id, ts_id=data['ts_id'].drop_duplicates().values[0],
                          model_id=8 if ensemble else 7, split_window=i,
                          split_no=split_no,
                          metric_id=metrics_list['psi'], metric_value=psi)
            insert_metric(train_id=train_id, ts_id=data['ts_id'].drop_duplicates().values[0],
                          model_id=8 if ensemble else 7, split_window=i,
                          split_no=split_no,
                          metric_id=metrics_list['ks'], metric_value=ks)

            forecast = pd.concat([forecast, sub_forecast], axis=0)

    forecast.reset_index(drop=True, inplace=True)
    return forecast.to_dict()


def set_fcst_flag(train_id, flag):
    engine = db_engine()
    conn = engine.connect()
    conn.execute(text(f"update train_history_table set status='{flag}' where train_id={train_id}"))
    conn.commit()
    conn.close()


def set_fcst_start_time(train_id):
    engine = db_engine()
    conn = engine.connect()
    conn.execute(text(f"update train_history_table set fcst_start_time='{get_time_now()}' where train_id={train_id}"))
    conn.commit()
    conn.close()


def set_fcst_end_time(train_id):
    engine = db_engine()
    conn = engine.connect()
    conn.execute(text(f"update train_history_table set fcst_end_time='{get_time_now()}' where train_id={train_id}"))
    conn.commit()
    conn.close()


def set_fcst_id(train_id, data_id):
    engine = db_engine()
    conn = engine.connect()
    conn.execute(text(f"update train_history_table set data_fcst_id={data_id} where train_id={train_id}"))
    conn.commit()
    conn.close()


def insert_data_id(data_id, user_id, data_proc_flag):
    engine = db_engine()
    conn = engine.connect()
    conn.execute(
        text(f"insert into data_history_table (data_id, user_id, status, data_create_time) values ({data_id}, {user_id}, '{data_proc_flag}', '{get_time_now()}')"))
    conn.commit()
    conn.close()


def delete_objects(dataset_ids):
    for i in dataset_ids:
        del i


def main(train_id):
    data_id = get_data_processing_id(train_id)
    user_id = get_user_id(train_id)
    parameters = get_default_parameters_in_dict()
    fcst_start = parameters[forecasting_stages["fcst_start"]]
    fcst_processing = parameters[forecasting_stages['fcst_processing']]
    fcst_end = parameters[forecasting_stages['fcst_end']]
    fcst_failed = parameters[forecasting_stages['fcst_failed']]
    fcst_flag = parameters[forecasting_stages['fcst_flag']]

    train_parameters = get_train_parameters_in_dict(train_id)

    test_size = float(train_parameters[forecasting_parameters['test_size']])
    forecast_horizon = float(train_parameters[forecasting_parameters['forecast_horizon']])
    model_types = list(map(int, train_parameters[forecasting_parameters['model_types']].split(',')))
    auto_ensemble = True if train_parameters[forecasting_parameters['auto_ensemble']] == '1' else False
    ensemble = True if train_parameters[forecasting_parameters['ensemble']] == '1' else False
    data_split = train_parameters[forecasting_parameters['data_split']]

    new_data_id = generate_fcst_id()

    set_fcst_flag(train_id, fcst_start)
    set_fcst_start_time(train_id)

    try:
        set_fcst_flag(train_id, fcst_processing)
        set_fcst_id(train_id, new_data_id)
        insert_data_id(new_data_id, user_id, fcst_flag)

        dataset = get_data(data_id)
        auto_ensemble_dataset = dataset.copy()
        ensemble_dataset = dataset.copy()
        dataset['model_id'] = ','.join(list(map(str, model_types)))
        dataset['model_id'] = dataset['model_id'].map(lambda x: x.split(','))
        dataset = dataset.explode('model_id').reset_index(drop=True)
        dataset['key'] = dataset['ts_id'].map(str) + '_' + dataset['model_id']

        dataset_map = [dataset[dataset['key'] == i].copy() for i in dataset['key'].unique()]
        dataset_ids = [simple_forecasting.apply_async((i.to_dict(), test_size, forecast_horizon,
                                                       data_split, train_id), queue='forecasting-pipeline').id for i in dataset_map]
        while sum([1 for i in dataset_ids if AsyncResult(i, app=celery_client).state != 'SUCCESS' and AsyncResult(i, app=celery_client).state != 'FAILURE']) > 0:
            pass
        if sum([1 for i in dataset_ids if AsyncResult(i, app=celery_client).state == 'SUCCESS']) < len(dataset_ids):
            raise Exception('Some tasks failed')
        dataset_results = [pd.DataFrame(AsyncResult(i, app=celery_client).get()) for i in dataset_ids]
        dataset_return = pd.concat(dataset_results, axis=0)
        dataset_return.reset_index(drop=True, inplace=True)
        if auto_ensemble:
            dataset_map = [auto_ensemble_dataset[auto_ensemble_dataset['ts_id'] == i].copy() for i in auto_ensemble_dataset['ts_id'].unique()]
            dataset_ids = [ensemble_forecasts.apply_async((i.to_dict(), test_size, forecast_horizon,
                                                           data_split, model_types, train_id,
                                                           False, True), queue='forecasting-pipeline').id for i in
                           dataset_map]
            while sum([1 for i in dataset_ids if AsyncResult(i, app=celery_client).state != 'SUCCESS' and AsyncResult(i, app=celery_client).state != 'FAILURE']) > 0:
                pass
            if sum([1 for i in dataset_ids if AsyncResult(i, app=celery_client).state == 'SUCCESS']) < len(
                    dataset_ids):
                raise Exception('Some tasks failed')
            auto_ensemble_dataset_return = [pd.DataFrame(AsyncResult(i, app=celery_client).get()) for i in dataset_ids]
            auto_ensemble_dataset_return = pd.concat(auto_ensemble_dataset_return, axis=0)
            auto_ensemble_dataset_return.reset_index(drop=True, inplace=True)
            auto_ensemble_dataset_return['model_id'] = '7'
            auto_ensemble_dataset_return['key'] = auto_ensemble_dataset_return['ts_id'].map(lambda x: str(int(x))) + '_' + auto_ensemble_dataset_return[
                'model_id']
            dataset_return = pd.concat([dataset_return, auto_ensemble_dataset_return], axis=0)

        if ensemble:
            dataset_map = [ensemble_dataset[ensemble_dataset['ts_id'] == i].copy() for i in ensemble_dataset['ts_id'].unique()]
            dataset_ids = [ensemble_forecasts.apply_async((i.to_dict(), test_size, forecast_horizon,
                                                           data_split, model_types, train_id,
                                                           True, False), queue='forecasting-pipeline').id for i in
                           dataset_map]
            while sum([1 for i in dataset_ids if AsyncResult(i, app=celery_client).state != 'SUCCESS' and AsyncResult(i,
                                                                                                                      app=celery_client).state != 'FAILURE']) > 0:
                pass
            if sum([1 for i in dataset_ids if AsyncResult(i, app=celery_client).state == 'SUCCESS']) < len(
                    dataset_ids):
                raise Exception('Some tasks failed')
            ensemble_dataset_return = [pd.DataFrame(AsyncResult(i, app=celery_client).get()) for i in dataset_ids]
            ensemble_dataset_return = pd.concat(ensemble_dataset_return, axis=0)
            ensemble_dataset_return.reset_index(drop=True, inplace=True)
            ensemble_dataset_return['model_id'] = '8'
            ensemble_dataset_return['key'] = ensemble_dataset_return['ts_id'].map(lambda x: str(int(x))) + '_' + ensemble_dataset_return[
                'model_id']
            dataset_return = pd.concat([dataset_return, ensemble_dataset_return], axis=0)

        dataset_return['ts_id'] = dataset_return['key'].map(lambda x: int(x.split('_')[0]))
        dataset_return['period'] = dataset_return['period'].map(lambda x: x.strftime('%d-%m-%Y'))
        dataset_return['model_id'] = dataset_return['key'].map(lambda x: int(x.split('_')[1]))
        dataset_return['data_id'] = new_data_id
        dataset_return['status'] = fcst_flag
        dataset_return['value'] = dataset_return['value'].fillna(0)
        dataset_return['value'] = dataset_return['value'].map(lambda x: int(x))
        dataset_return['value'] = dataset_return['value'].map(lambda x: 0 if x < 0 else x)

        if 'key' in dataset_return.columns:
            dataset_return.drop(columns={'key'}, inplace=True)
        engine = db_engine()
        dataset_return.to_sql('data_table', engine, schema=database_utils["DATABASE"], if_exists='append', index=False)


        set_fcst_flag(train_id, fcst_end)
    except Exception as e:
        print(e)
        set_fcst_flag(train_id, fcst_failed)
    finally:
        set_fcst_end_time(train_id)
