import time
from sqlalchemy import create_engine
from datetime import datetime
from data_processing.data_processing_config import database_utils
from sqlalchemy import text
import pandas as pd


def get_time_now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


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
    conn_url = f'{database_utils["DRIVER"]}://{database_utils["USER"]}:{database_utils["PASSWORD"]}@' \
               f'{database_utils["HOST"]}:{database_utils["PORT"]}/{database_utils["DATABASE"]}'
    engine = create_engine(conn_url, echo=False)
    return engine


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
    parameters = conn.execute(text("select parameter_id, parameter_name, parameter_value, parameter_range_values from parameter_table")).fetchall()
    parameters = pd.DataFrame(parameters)
    parameters.columns = ['parameter_id', 'parameter_name', 'parameter_value', 'parameter_range_values']
    conn.close()
    return parameters


def get_train_parameters_in_dict(train_id):
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
