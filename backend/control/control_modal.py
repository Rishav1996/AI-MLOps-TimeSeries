"""Ingestion orchestration: ID generation, CSV load, and pipeline entrypoints.

``ingest_data`` is the ingestion stage itself (run as a background task); the
``*_pipeline`` wrappers hand off to the data-processing and forecasting packages.
"""
import os

import pandas as pd

from sqlalchemy import text

from control.control_config import ingestion_stages, database_utils
from control.control_helper import get_time_now, db_engine, get_default_parameters_in_dict, normalize_period
from data_processing import data_processing_pipeline as dpp
from forecasting import forecasting_pipeline as fp


def generate_ingest_id():
    """Allocate the next train_id and data_id (max + 1) for a new ingestion."""
    engine = db_engine()
    conn = engine.connect()
    train_id = conn.execute(text("select ifnull(max(train_id), 0) from train_history_table")).fetchone()[0] + 1
    data_id = conn.execute(text("select ifnull(max(data_id), 0) from data_history_table")).fetchone()[0] + 1
    conn.close()
    return int(train_id), int(data_id)


def ingest_parameters(train_id, parameters):
    """Insert a {parameter_id: value} mapping into train_history_table for a run."""
    engine = db_engine()
    conn = engine.connect()
    for parameter_id, parameter_value in parameters.items():
        conn.execute(text("insert into train_history_table (train_id, parameter_id, parameter_value) "
                          "values (:train_id, :parameter_id, :parameter_value)"),
                     {"train_id": train_id, "parameter_id": parameter_id, "parameter_value": parameter_value})
    conn.commit()
    conn.close()


def ingest_data(train_id, data_id, file_name, user_id):
    """Load an uploaded CSV into data_table, advancing status flags as it goes.

    Writes the rows under a new data_id, records timings in train_history_table, and
    archives the source CSV to control/ingested (or control/failed on error).
    """
    try:
        os.makedirs("./control/ingested", exist_ok=True)
        os.makedirs("./control/failed", exist_ok=True)
        create_time = get_time_now()
        engine = db_engine()
        conn = engine.connect()
        dataset = pd.read_csv("./control/raw_data/" + file_name)
        dataset = pd.DataFrame(data=dataset.values, columns=dataset.columns)
        # Normalize the period to canonical YYYY-MM-DD (accepts DD-MM-YYYY and ISO).
        dataset['period'] = normalize_period(dataset['period'])
        parameters = get_default_parameters_in_dict()
        ing_flag = parameters[ingestion_stages["ing_flag"]]
        ing_start = parameters[ingestion_stages["ing_start"]]
        ing_processing = parameters[ingestion_stages["ing_processing"]]
        ing_end = parameters[ingestion_stages["ing_end"]]
        ing_failed = parameters[ingestion_stages["ing_failed"]]
        dataset['data_id'] = data_id
        dataset['status'] = ing_flag
        ingestion = False
        try:
            conn.execute(
                text("insert into train_history_table(train_id, data_ing_id, ing_start_time, status) "
                     "values (:train_id, :data_id, :create_time, :ing_start)"),
                {"train_id": train_id, "data_id": data_id, "create_time": create_time, "ing_start": ing_start})
            conn.commit()
            conn.close()

            engine = db_engine()
            conn = engine.connect()
            conn.execute(text("update train_history_table set status = :ing_processing where train_id = :train_id"),
                         {"ing_processing": ing_processing, "train_id": train_id})
            conn.commit()
            conn.close()

            engine = db_engine()
            conn = engine.connect()
            conn.execute(text("insert into data_history_table values (:data_id, :ing_flag, :user_id, :create_time)"),
                         {"data_id": data_id, "ing_flag": ing_flag, "user_id": user_id, "create_time": create_time})
            conn.commit()
            conn.close()

            engine = db_engine()
            dataset.to_sql('data_table', engine, schema=database_utils["DATABASE"], if_exists='append',
                                        index=False)

            engine = db_engine()
            conn = engine.connect()
            end_time = get_time_now()
            conn.execute(
                text("update train_history_table set ing_end_time = :end_time , status = :ing_end where train_id = :train_id"),
                {"end_time": end_time, "ing_end": ing_end, "train_id": train_id})
            conn.commit()
            conn.close()

            os.remove("./control/raw_data/" + file_name)

            file_name = f'ingested_{data_id}.csv'
            dataset.to_csv("./control/ingested/" + file_name, index=False)
            ingestion = True
        except Exception as e:
            print(e)
            engine = db_engine()
            conn = engine.connect()
            end_time = get_time_now()
            conn.execute(
                text("update train_history_table set ing_end_time = :end_time , status = :ing_failed where train_id = :train_id"),
                {"end_time": end_time, "ing_failed": ing_failed, "train_id": train_id})
            conn.commit()
            conn.close()

            engine = db_engine()
            conn = engine.connect()
            conn.execute(text("delete from data_history_table where data_id = :data_id"), {"data_id": data_id})
            conn.commit()
            conn.close()

            os.remove("./control/raw_data/" + file_name)
            file_name = f'failed_{data_id}.csv'
            dataset.to_csv("./control/failed/" + file_name, index=False)
            ingestion = False
        finally:
            if ingestion:
                return 1, 1
            else:
                return -1, -1
    except Exception as e:
        print(e)
        return 0, 0


def data_processing_pipeline(train_id):
    """Background-task entrypoint that runs the data-processing stage for a run."""
    dpp.main(train_id)


def forecasting_pipeline(train_id):
    """Background-task entrypoint that runs the forecasting stage for a run."""
    fp.main(train_id)
