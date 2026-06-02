"""Control-layer helpers: DB access, auth, parameter lookup, and run bookkeeping.

Shared by the API endpoints (in app.py) and the ingestion orchestration in
control_modal.py. All SQL uses bound parameters; writes commit before closing.
"""
import json
import re
from sqlalchemy import create_engine, text
from datetime import datetime
from control.control_config import database_utils, data_processing_parameters, ingestion_stages, data_processing_stages, \
    forecasting_parameters
import hashlib
import pandas as pd


def get_time_now():
    """Current timestamp as a 'YYYY-MM-DD HH:MM:SS' string for DB columns."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def db_engine():
    """Build a SQLAlchemy engine for the configured MySQL database."""
    conn_url = f'{database_utils["DRIVER"]}://{database_utils["USER"]}:{database_utils["PASSWORD"]}@' \
               f'{database_utils["HOST"]}:{database_utils["PORT"]}/{database_utils["DATABASE"]}'
    engine = create_engine(conn_url, echo=False)
    return engine


def password_hashing(text: str):
    """Return the MD5 hex digest of a password for storage/comparison."""
    return str(hashlib.md5(text.encode()).hexdigest())


_ISO_DATE_RE = re.compile(r'^\s*\d{4}[-/]\d{1,2}[-/]\d{1,2}')


def normalize_period(period_series):
    """Normalize a period column to canonical 'YYYY-MM-DD' strings.

    Detects format per value: year-first (YYYY-MM-DD) is parsed as ISO, otherwise it
    is treated as day-first (DD-MM-YYYY). This accepts the documented canonical format
    and the day-first form without one corrupting the other, and keeps the stored
    value consistent with the forecast output (and the 10-char column).
    """
    def _parse(value):
        value = str(value).strip()
        return pd.to_datetime(value, dayfirst=not bool(_ISO_DATE_RE.match(value)))

    return pd.to_datetime(period_series.map(_parse)).dt.strftime('%Y-%m-%d')


def get_default_parameters_in_dict():
    """Return all parameter_table rows as a {parameter_id: value} dict."""
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
    """Return parameter_table (id, name, value, allowed ranges) as a DataFrame."""
    engine = db_engine()
    conn = engine.connect()
    parameters = conn.execute(
        text("select parameter_id, parameter_name, parameter_value, parameter_range_values from parameter_table")).fetchall()
    parameters = pd.DataFrame(parameters)
    parameters.columns = ['parameter_id', 'parameter_name', 'parameter_value', 'parameter_range_values']
    conn.close()
    return parameters


def get_user_id(user_name):
    """Return the user_id for a username, or 0 if it does not exist."""
    engine = db_engine()
    conn = engine.connect()
    user_id = conn.execute(
        text("SELECT ifnull(max(user_id), 0) FROM user_table WHERE user_name = :user_name"),
        {"user_name": user_name}).fetchone()[0]
    conn.close()
    return user_id


def insert_user(user_name, user_password):
    """Insert a new user with an MD5-hashed password."""
    engine = db_engine()
    conn = engine.connect()
    conn.execute(
        text("INSERT INTO user_table (user_name, user_password) VALUES (:user_name, :user_password)"),
        {"user_name": user_name, "user_password": password_hashing(user_password)})
    conn.commit()
    conn.close()
    return


def verify_user(user_name, user_password):
    """Return True if the username exists and the password hash matches."""
    engine = db_engine()
    conn = engine.connect()
    if get_user_id(user_name) > 0:
        user_password_hash = conn.execute(
            text("SELECT ifnull(user_password, '') FROM user_table WHERE user_name = :user_name"),
            {"user_name": user_name}).fetchone()[0]
        conn.close()
        if user_password_hash == password_hashing(user_password):
            return True
        return False
    conn.close()
    return False


def verify_user_id(user_id):
    """Return True if a user with this id exists."""
    engine = db_engine()
    conn = engine.connect()
    count = conn.execute(
        text("SELECT ifnull(count(*), 0) FROM user_table WHERE user_id = :user_id"),
        {"user_id": user_id}).scalar()
    conn.close()
    return count > 0


def get_dp_train_ids(train_type, user_id):
    """List a user's train_ids ready for data processing.

    'create' = ingested but not yet processed; 'existing' = already processed (re-run).
    """
    engine = db_engine()
    conn = engine.connect()
    train_ids = []
    if train_type == 'create':
        train_ids = conn.execute(
            text("SELECT train_id FROM train_history_table th join data_history_table dh on(th.data_ing_id = dh.data_id) where ifnull(data_dp_id, 0) = 0 and dh.user_id = :user_id and th.status = 'ING_E'"),
            {"user_id": user_id}).fetchall()
        if len(train_ids) > 0:
            train_ids = [train_id[0] for train_id in train_ids]
    elif train_type == 'existing':
        train_ids = conn.execute(
            text("SELECT train_id FROM train_history_table th join data_history_table dh on(th.data_ing_id = dh.data_id) where ifnull(data_dp_id, 0) > 0 and dh.user_id = :user_id and th.status != 'ING_E'"),
            {"user_id": user_id}).fetchall()
        if len(train_ids) > 0:
            train_ids = [train_id[0] for train_id in train_ids]
    conn.close()
    return train_ids


def get_fcst_train_ids(train_type, user_id):
    """List a user's train_ids ready for forecasting.

    'create' = processed but not yet forecast; 'existing' = already forecast (re-run).
    """
    engine = db_engine()
    conn = engine.connect()
    train_ids = []
    if train_type == 'create':
        train_ids = conn.execute(
            text("SELECT train_id FROM train_history_table th join data_history_table dh on(th.data_ing_id = dh.data_id) where ifnull(data_fcst_id, 0) = 0 and dh.user_id = :user_id and th.status = 'DP_E'"),
            {"user_id": user_id}).fetchall()
        if len(train_ids) > 0:
            train_ids = [train_id[0] for train_id in train_ids]
    elif train_type == 'existing':
        train_ids = conn.execute(
            text("SELECT train_id FROM train_history_table th join data_history_table dh on(th.data_ing_id = dh.data_id) where ifnull(data_fcst_id, 0) > 0 and dh.user_id = :user_id and th.status != 'DP_E'"),
            {"user_id": user_id}).fetchall()
        if len(train_ids) > 0:
            train_ids = [train_id[0] for train_id in train_ids]
    conn.close()
    return train_ids


def get_default_dp_parameters():
    """Return only the data-processing parameters (name/value/range) for the UI."""
    parameters = get_default_parameters_in_dataframe()
    parameters = parameters[parameters['parameter_id'].isin(list(data_processing_parameters.values()))]
    parameters = parameters[['parameter_name', 'parameter_value', 'parameter_range_values']]
    parameters = parameters.to_dict(orient='records')
    return parameters


def get_default_fcst_parameters():
    """Return only the forecasting parameters (name/value/range) for the UI."""
    parameters = get_default_parameters_in_dataframe()
    parameters = parameters[parameters['parameter_id'].isin(list(forecasting_parameters.values()))]
    parameters = parameters[['parameter_name', 'parameter_value', 'parameter_range_values']]
    parameters = parameters.to_dict(orient='records')
    return parameters


def copy_existing_dp_data_id(train_id):
    """Clone a run's ingested data into a new train_id for re-processing; return it."""
    engine = db_engine()
    conn = engine.connect()
    data_id = conn.execute(
        text("SELECT data_ing_id FROM train_history_table WHERE train_id = :train_id"),
        {"train_id": train_id}).fetchone()[0]
    new_train_id = conn.execute(text("SELECT max(train_id) FROM train_history_table")).fetchone()[0] + 1
    create_time = get_time_now()
    parameters = get_default_parameters_in_dict()
    ing_end = parameters[ingestion_stages["ing_end"]]
    conn.execute(
        text("insert into train_history_table(train_id, data_ing_id, ing_start_time, ing_end_time, status) "
             "values (:new_train_id, :data_id, :create_time, :create_time, :ing_end)"),
        {"new_train_id": new_train_id, "data_id": data_id, "create_time": create_time, "ing_end": ing_end})
    conn.commit()
    conn.close()
    return new_train_id


def copy_existing_fcst_data_id(train_id):
    """Clone a run's ingested+processed data into a new train_id for re-forecasting."""
    engine = db_engine()
    conn = engine.connect()
    data_ing_id = conn.execute(
        text("SELECT data_ing_id FROM train_history_table WHERE train_id = :train_id"),
        {"train_id": train_id}).fetchone()[0]
    data_dp_id = conn.execute(
        text("SELECT data_dp_id FROM train_history_table WHERE train_id = :train_id"),
        {"train_id": train_id}).fetchone()[0]
    new_train_id = conn.execute(text("SELECT max(train_id) FROM train_history_table")).fetchone()[0] + 1
    create_time = get_time_now()
    parameters = get_default_parameters_in_dict()
    data_proc_end = parameters[data_processing_stages["data_proc_end"]]
    conn.execute(
        text("insert into train_history_table(train_id, data_ing_id, data_dp_id, ing_start_time, ing_end_time, dp_start_time, dp_end_time, status) "
             "values (:new_train_id, :data_ing_id, :data_dp_id, :create_time, :create_time, :create_time, :create_time, :data_proc_end)"),
        {"new_train_id": new_train_id, "data_ing_id": data_ing_id, "data_dp_id": data_dp_id,
         "create_time": create_time, "data_proc_end": data_proc_end})
    conn.commit()
    conn.close()
    return new_train_id


def insert_train_parameters_to_db(train_id, parameters):
    """Store a run's chosen parameters (JSON of name->value) in train_parameter_table.

    Parameter names are resolved to their IDs via parameter_table before insert.
    """
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
    """Return True if performance metrics (excluding ensemble ids 7/8) already exist."""
    engine = db_engine()
    conn = engine.connect()
    metrics = conn.execute(
        text("SELECT * FROM train_metric_table WHERE train_id = :train_id and metric_id not in (7,8)"),
        {"train_id": train_id}).fetchall()
    conn.close()
    return len(metrics) > 0


def convert_to_time(seconds):
    """Format a duration in seconds as a 'H h MM m SS s' string."""
    seconds = seconds % (24 * 3600)
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    return "%d h %02d m %02d s" % (hour, minutes, seconds)


def get_train_history(user_id):
    """Return a user's runs as JSON: ids, per-stage durations, and phase/status.

    Each row's status is split into a `phase` (ING/DP/FCST) and `c_status`
    (first letter of the stage state) for the UI; missing values render as '-'.
    """
    engine = db_engine()
    conn = engine.connect()
    # TIMESTAMPDIFF gives true elapsed seconds; plain datetime subtraction in MySQL
    # yields a meaningless packed YYYYMMDDHHMMSS number.
    query = text("""SELECT
                    th.train_id, th.data_ing_id, th.data_dp_id,
                    th.data_fcst_id,
                    TIMESTAMPDIFF(SECOND, th.ing_start_time, th.ing_end_time) as ing_time,
                    TIMESTAMPDIFF(SECOND, th.dp_start_time, th.dp_end_time) as dp_time,
                    TIMESTAMPDIFF(SECOND, th.fcst_start_time, th.fcst_end_time) as fcst_time,
                    th.status
                FROM mlops_ts_fcst.train_history_table th
                inner join mlops_ts_fcst.data_history_table dh on (th.data_ing_id = dh.data_id)
                where dh.user_id = :user_id""")
    train_history = pd.read_sql(query, conn, params={"user_id": user_id})
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
