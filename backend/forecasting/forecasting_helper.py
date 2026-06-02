"""Forecasting helpers: DB access, parameter lookup, frequency/seasonality inference,
and Celery task waiting."""
import time
from sqlalchemy import create_engine
from datetime import datetime
from forecasting.forecasting_config import database_utils
import pandas as pd
from sqlalchemy import text


def get_time_now():
    """Current timestamp as a 'YYYY-MM-DD HH:MM:SS' string for DB columns."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _delta_days(index):
    """Whole-day gap between the first two timestamps, or None if < 2 points."""
    if len(index) < 2:
        return None
    return (index[1] - index[0]).days


def seasonal_period(index, default=1):
    """Map a DatetimeIndex sampling cadence to a seasonal period (sp).

    Robust under pandas 2, where ``pd.Timedelta('1M')`` / ``'1Y'`` raise because
    months/years are not unambiguous fixed durations.
    """
    days = _delta_days(index)
    if days is None or days <= 0:
        return default
    if days == 1:
        return 365      # daily
    if 6 <= days <= 8:
        return 52       # weekly
    if 27 <= days <= 31:
        return 12       # monthly
    return default


def freq_string(index):
    """Pandas offset alias for a DatetimeIndex cadence (for Prophet / date_range)."""
    if len(index) < 2:
        return index.inferred_freq
    delta = index[1] - index[0]
    seconds = delta.total_seconds()
    if seconds == 1:
        return 'S'
    if seconds == 3600:
        return 'H'
    days = delta.days
    if days == 1:
        return 'D'
    if 6 <= days <= 8:
        return 'W'
    if 27 <= days <= 31:
        return 'MS'
    if days >= 360:
        return 'YS'
    return index.inferred_freq


def wait_for_tasks(task_ids, poll_interval=0.5):
    """Block until every Celery task id reaches a terminal state.

    Replaces busy-wait ``while ...: pass`` loops (which peg a CPU core). Raises if
    any task ends in FAILURE; otherwise returns the results in the given id order.
    """
    from celery.result import AsyncResult
    from celery_app import celery_client

    results = [AsyncResult(task_id, app=celery_client) for task_id in task_ids]
    while any(r.state not in ('SUCCESS', 'FAILURE') for r in results):
        time.sleep(poll_interval)
    failed = [r.id for r in results if r.state == 'FAILURE']
    if failed:
        raise Exception(f"Celery tasks failed: {failed}")
    return [r.get() for r in results]


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
