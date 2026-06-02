"""Metrics helpers: DB access and parameter lookup for metric calculation."""
from sqlalchemy import create_engine
from datetime import datetime
from metrics.metrics_config import database_utils
import pandas as pd
from sqlalchemy import text


def get_time_now():
    """Current timestamp as a 'YYYY-MM-DD HH:MM:SS' string for DB columns."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def db_engine():
    """Build a SQLAlchemy engine for the configured MySQL database."""
    conn_url = f'{database_utils["DRIVER"]}://{database_utils["USER"]}:{database_utils["PASSWORD"]}@' \
               f'{database_utils["HOST"]}:{database_utils["PORT"]}/{database_utils["DATABASE"]}'
    engine = create_engine(conn_url, echo=False)
    return engine


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
    parameters = conn.execute(text("select parameter_id, parameter_name, parameter_value, parameter_range_values from parameter_table")).fetchall()
    parameters = pd.DataFrame(parameters)
    parameters.columns = ['parameter_id', 'parameter_name', 'parameter_value', 'parameter_range_values']
    conn.close()
    return parameters


def get_train_parameters_in_dict(train_id):
    """Return a run's chosen parameters as a {parameter_id: value} dict."""
    engine = db_engine()
    conn = engine.connect()
    parameters = conn.execute(
        text("select parameter_id, train_value from train_parameter_table where train_id = :train_id"),
        {"train_id": train_id}).fetchall()
    parameters = pd.DataFrame(parameters)
    parameters.columns = ['parameter_id', 'parameter_value']
    parameters = {parameter['parameter_id']: parameter['parameter_value'] for parameter in
                  parameters.to_dict('records')}
    conn.close()
    return parameters
