import json
from sqlalchemy import create_engine, text
from datetime import datetime
from control.control_config import database_utils, data_processing_parameters, ingestion_stages, data_processing_stages, \
    forecasting_parameters
import hashlib
import pandas as pd


def get_time_now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def db_engine():
    conn_url = f'{database_utils["DRIVER"]}://{database_utils["USER"]}:{database_utils["PASSWORD"]}@' \
               f'{database_utils["HOST"]}:{database_utils["PORT"]}/{database_utils["DATABASE"]}'
    engine = create_engine(conn_url, echo=False)
    return engine


def password_hashing(text: str):
    return str(hashlib.md5(text.encode()).hexdigest())


def get_default_parameters_in_dict():
    engine = db_engine()
    conn = engine.connect()
    parameters = conn.execute(text("select parameter_id, parameter_value from parameter_table")).fetchall()
    parameters = pd.DataFrame(parameters)
    parameters.columns = ['parameter_id', 'parameter_value']
    parameters = {parameter['parameter_id']: parameter['parameter_value'] for parameter in
                  parameters.to_dict('records')}
    conn.close()
    return parameters


def get_default_parameters_in_dataframe():
    engine = db_engine()
    conn = engine.connect()
    parameters = conn.execute(
        text("select parameter_id, parameter_name, parameter_value, parameter_range_values from parameter_table")).fetchall()
    parameters = pd.DataFrame(parameters)
    parameters.columns = ['parameter_id', 'parameter_name', 'parameter_value', 'parameter_range_values']
    conn.close()
    return parameters


def get_user_id(user_name):
    engine = db_engine()
    conn = engine.connect()
    user_id = \
        conn.execute(text(f"SELECT ifnull(max(user_id), 0) FROM user_table WHERE user_name = '{user_name}'")).fetchone()[0]
    return user_id


def insert_user(user_name, user_password):
    engine = db_engine()
    conn = engine.connect()
    conn.execute(
        text(f"INSERT INTO user_table (user_name, user_password) VALUES ('{user_name}', '{password_hashing(user_password)}')"))
    return


def verify_user(user_name, user_password):
    engine = db_engine()
    conn = engine.connect()
    if get_user_id(user_name) > 0:
        user_password_hash = \
            conn.execute(
                text(f"SELECT ifnull(user_password, '') FROM user_table WHERE user_name = '{user_name}'")).fetchone()[0]
        if user_password_hash == password_hashing(user_password):
            return True
    return False


def verify_user_id(user_id):
    engine = db_engine()
    conn = engine.connect()
    user = conn.execute(text(f"SELECT ifnull(count(*), 0) FROM user_table WHERE user_id = {user_id}"))
    if user.rowcount > 0:
        return True
    return False


def get_dp_train_ids(train_type, user_id):
    engine = db_engine()
    conn = engine.connect()
    train_ids = []
    if train_type == 'create':
        train_ids = conn.execute(
            text(f"SELECT train_id FROM train_history_table th join data_history_table dh on(th.data_ing_id = dh.data_id) where ifnull(data_dp_id, 0) = 0 and dh.user_id = {user_id} and th.status = 'ING_E'")).fetchall()
        if len(train_ids) > 0:
            train_ids = [train_id[0] for train_id in train_ids]
    elif train_type == 'existing':
        train_ids = conn.execute(
            text(f"SELECT train_id FROM train_history_table th join data_history_table dh on(th.data_ing_id = dh.data_id) where ifnull(data_dp_id, 0) > 0 and dh.user_id = {user_id} and th.status != 'ING_E'")).fetchall()
        if len(train_ids) > 0:
            train_ids = [train_id[0] for train_id in train_ids]
    return train_ids


def get_fcst_train_ids(train_type, user_id):
    engine = db_engine()
    conn = engine.connect()
    train_ids = []
    if train_type == 'create':
        train_ids = conn.execute(
            text(f"SELECT train_id FROM train_history_table th join data_history_table dh on(th.data_ing_id = dh.data_id) where ifnull(data_fcst_id, 0) = 0 and dh.user_id = {user_id} and th.status = 'DP_E'")).fetchall()
        if len(train_ids) > 0:
            train_ids = [train_id[0] for train_id in train_ids]
    elif train_type == 'existing':
        train_ids = conn.execute(
            text(f"SELECT train_id FROM train_history_table th join data_history_table dh on(th.data_ing_id = dh.data_id) where ifnull(data_fcst_id, 0) > 0 and dh.user_id = {user_id} and th.status != 'DP_E'")).fetchall()
        if len(train_ids) > 0:
            train_ids = [train_id[0] for train_id in train_ids]
    return train_ids


def get_default_dp_parameters():
    parameters = get_default_parameters_in_dataframe()
    parameters = parameters[parameters['parameter_id'].isin(list(data_processing_parameters.values()))]
    parameters = parameters[['parameter_name', 'parameter_value', 'parameter_range_values']]
    parameters = parameters.to_dict(orient='records')
    return parameters


def get_default_fcst_parameters():
    parameters = get_default_parameters_in_dataframe()
    parameters = parameters[parameters['parameter_id'].isin(list(forecasting_parameters.values()))]
    parameters = parameters[['parameter_name', 'parameter_value', 'parameter_range_values']]
    parameters = parameters.to_dict(orient='records')
    return parameters


def copy_existing_dp_data_id(train_id):
    engine = db_engine()
    conn = engine.connect()
    data_id = conn.execute(text(f"SELECT data_ing_id FROM train_history_table WHERE train_id = {train_id}")).fetchone()[0]
    new_train_id = conn.execute(text(f"SELECT max(train_id) FROM train_history_table")).fetchone()[0] + 1
    create_time = get_time_now()
    parameters = get_default_parameters_in_dict()
    ing_end = parameters[ingestion_stages["ing_end"]]
    conn.execute(
        text(f"insert into train_history_table(train_id, data_ing_id, ing_start_time, ing_end_time, status) values ({new_train_id}, {data_id}, '{create_time}', '{create_time}', '{ing_end}')"))
    conn.close()
    return new_train_id


def copy_existing_fcst_data_id(train_id):
    engine = db_engine()
    conn = engine.connect()
    data_ing_id = conn.execute(text(f"SELECT data_ing_id FROM train_history_table WHERE train_id = {train_id}")).fetchone()[0]
    data_dp_id = conn.execute(text(f"SELECT data_dp_id FROM train_history_table WHERE train_id = {train_id}")).fetchone()[0]
    new_train_id = conn.execute(text(f"SELECT max(train_id) FROM train_history_table")).fetchone()[0] + 1
    create_time = get_time_now()
    parameters = get_default_parameters_in_dict()
    data_proc_end = parameters[data_processing_stages["data_proc_end"]]
    conn.execute(
        text(f"insert into train_history_table(train_id, data_ing_id, data_dp_id, ing_start_time, ing_end_time, dp_start_time, dp_end_time, status) values ({new_train_id}, {data_ing_id}, {data_dp_id}, '{create_time}', '{create_time}', '{create_time}', '{create_time}', '{data_proc_end}')"))
    conn.close()
    return new_train_id


def insert_train_parameters_to_db(train_id, parameters):
    engine = db_engine()
    parameters = json.loads(parameters)
    parameters = [[i, parameters[i]] for i in parameters.keys()]
    parameters = pd.DataFrame(parameters)
    parameters.columns = ['parameter_name', 'train_value']
    parameters['train_id'] = train_id
    default_params = get_default_parameters_in_dataframe()
    parameters = parameters.merge(default_params[['parameter_id', 'parameter_name']], on='parameter_name', how='left')
    parameters = parameters[['train_id', 'train_value', 'parameter_id']]
    parameters.to_sql('train_parameter_table', engine, if_exists='append', index=False)


def verify_metrics_exists(train_id):
    engine = db_engine()
    conn = engine.connect()
    metrics = conn.execute(
        text(f"SELECT * FROM train_metric_table WHERE train_id = {train_id} and metric_id not in (7,8)")).fetchall()
    conn.close()
    return len(metrics) > 0


def convert_to_time(seconds):
    seconds = seconds % (24 * 3600)
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    return "%d h %02d m %02d s" % (hour, minutes, seconds)


def get_train_history(user_id):
    engine = db_engine()
    conn = engine.connect()
    query = f"""SELECT 
                    th.train_id, th.data_ing_id, th.data_dp_id,
                    th.data_fcst_id, th.ing_end_time - th.ing_start_time as ing_time, 
                    th.dp_end_time - th.dp_start_time as dp_time, 
                    th.fcst_end_time - th.fcst_start_time as fcst_time, th.status 
                FROM mlops_ts_fcst.train_history_table th 
                inner join mlops_ts_fcst.data_history_table dh on (th.data_ing_id = dh.data_id)
                where dh.user_id = {user_id}"""
    train_history = pd.read_sql(query, conn)
    train_history.columns = ['train_id', 'data_ing_id', 'data_dp_id', 'data_fcst_id',
                             'ing_time', 'dp_time', 'fcst_time', 'status']
    train_history[['data_ing_id', 'data_dp_id', 'data_fcst_id']] = train_history[['data_ing_id', 'data_dp_id', 'data_fcst_id']].fillna('-')
    train_history[['ing_time', 'dp_time', 'fcst_time']] = train_history[['ing_time', 'dp_time', 'fcst_time']].fillna(-1)
    train_history['ing_time'] = train_history['ing_time'].apply(lambda x: str('-' if x == -1 else convert_to_time(seconds=x)))
    train_history['dp_time'] = train_history['dp_time'].apply(lambda x: str('-' if x == -1 else convert_to_time(seconds=x)))
    train_history['fcst_time'] = train_history['fcst_time'].apply(lambda x: str('-' if x == -1 else convert_to_time(seconds=x)))
    train_history['phase'] = train_history['status'].apply(lambda x: str(x).split('_')[0])
    train_history['c_status'] = train_history['status'].apply(lambda x: str(x).split('_')[1][0])
    train_history = train_history.sort_values(by=['train_id'], ascending=False)
    train_history = train_history.drop(['status'], axis=1)
    train_history = train_history.to_json(orient='records')
    conn.close()
    return train_history
