from config import database_utils
from sqlalchemy import create_engine, text
import pandas as pd


def db_engine():
    conn_url = f'{database_utils["DRIVER"]}://{database_utils["USER"]}:{database_utils["PASSWORD"]}@' \
               f'{database_utils["HOST"]}:{database_utils["PORT"]}/{database_utils["DATABASE"]}'
    engine = create_engine(conn_url, echo=False)
    return engine


def get_list_of_train_data_id(user_id):
    engine = db_engine()
    conn = engine.connect()
    query = (f"SELECT \n"
             f"	th.train_id, th.data_ing_id, th.data_dp_id,\n"
             f"	th.data_fcst_id \n"
             f"FROM mlops_ts_fcst.train_history_table th inner join mlops_ts_fcst.data_history_table dh on (th.data_ing_id = dh.data_id) \n"
             f"where dh.user_id = {user_id} and th.status = 'FCST_E'")
    result = conn.execute(text(query)).fetchall()
    result = pd.DataFrame(result, columns=['train_id', 'data_ing_id', 'data_dp_id', 'data_fcst_id'])
    result = {'train_id': result['train_id'].tolist(),
              'data_ing_id': result['data_ing_id'].tolist(),
              'data_dp_id': result['data_dp_id'].tolist(),
              'data_fcst_id': result['data_fcst_id'].tolist()}
    conn.close()
    return result


def get_data(data_ing_id, data_dp_id):
    engine = db_engine()
    conn = engine.connect()
    query = f"select period, ts_id, value from data_table where data_id = {data_ing_id}"
    result_ing = conn.execute(text(query)).fetchall()
    result_ing = pd.DataFrame(result_ing, columns=['period', 'ts_id', 'raw_history'])
    query = f"select period, ts_id, value from data_table where data_id = {data_dp_id}"
    result_dp = conn.execute(text(query)).fetchall()
    result_dp = pd.DataFrame(result_dp, columns=['period', 'ts_id', 'processed_history'])
    conn.close()
    result = pd.merge(result_ing, result_dp, on=['period', 'ts_id'], how='outer')
    result['period'] = pd.to_datetime(result['period'])
    return result


def get_forecast_data(train_id):
    engine = db_engine()
    conn = engine.connect()
    data_ing_id = conn.execute(text(f"select data_ing_id from train_history_table where train_id = {train_id}")).fetchone()[0]
    data_fcst_id = conn.execute(text(f"select data_fcst_id from train_history_table where train_id = {train_id}")).fetchone()[0]
    actual_data = conn.execute(text(f"select period, ts_id, value from data_table where data_id = {data_ing_id}")).fetchall()
    actual_data = pd.DataFrame(actual_data, columns=['period', 'ts_id', 'raw_history'])
    forecast_data = conn.execute(text(f"select period, ts_id, value, split_window, split_no + 1 as split_no, m.model_name\n"
                                 f"from data_table d inner join model_table m on(d.model_id = m.model_id) where data_id = {data_fcst_id}")).fetchall()
    forecast_data = pd.DataFrame(forecast_data, columns=['period', 'ts_id', 'forecast', 'split_window', 'split_no', 'model_name'])
    forecast_data['split_no'] = forecast_data['split_no'].astype(str)
    result = pd.merge(actual_data, forecast_data, on=['period', 'ts_id'], how='inner')
    result['period'] = pd.to_datetime(result['period'])
    conn.close()
    return result


def get_metric_data(train_id):
    engine = db_engine()
    conn = engine.connect()
    query = (f"\n"
             f"SELECT ts_id, m.model_name, split_window, split_no + 1 as split_no, me.metric_name, metric_value FROM mlops_ts_fcst.train_metric_table tm \n"
             f"inner join model_table m on(m.model_id = tm.model_id)\n"
             f"inner join metric_table me on(me.metric_id = tm.metric_id) where train_id = {train_id};")
    result = conn.execute(text(query)).fetchall()
    result = pd.DataFrame(result, columns=['ts_id', 'model_name', 'split_window', 'split_no', 'metric_name', 'metric_value'])
    result['split_no'] = result['split_no'].astype(str)
    result['metric_value'] = result['metric_value'].astype(float)
    conn.close()
    return result
