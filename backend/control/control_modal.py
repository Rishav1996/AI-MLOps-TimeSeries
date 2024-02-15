import os

import pandas as pd
import pandas as pnd
from sqlalchemy import text

from control.control_config import ingestion_stages, database_utils
from control.control_helper import get_time_now, db_engine, get_default_parameters_in_dict
from data_processing import data_processing_pipeline as dpp
from forecasting import forecasting_pipeline as fp


def generate_ingest_id():
    engine = db_engine()
    conn = engine.connect()
    train_id = conn.execute(text("select ifnull(max(train_id), 0) from train_history_table")).fetchone()[0] + 1
    data_id = conn.execute(text("select ifnull(max(data_id), 0) from data_history_table")).fetchone()[0] + 1
    conn.close()
    return int(train_id), int(data_id)


def ingest_parameters(train_id, parameters):
    engine = db_engine()
    conn = engine.connect()
    for parameter_id, parameter_value in parameters.items():
        conn.execute(text(f"insert into train_history_table (train_id, parameter_id, parameter_value) "
                     f"values ({train_id}, {parameter_id}, '{parameter_value}')"))
    conn.close()


def ingest_data(train_id, data_id, file_name, user_id):
    try:
        create_time = get_time_now()
        engine = db_engine()
        conn = engine.connect()
        dataset = pnd.read_csv("./control/raw_data/" + file_name)
        dataset = pd.DataFrame(data=dataset.values, columns=dataset.columns)
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
                text(f"insert into train_history_table(train_id, data_ing_id, ing_start_time, status) values ({train_id}, {data_id}, '{create_time}', '{ing_start}')"))
            conn.close()

            engine = db_engine()
            conn = engine.connect()
            conn.execute(text(f"update train_history_table set status = '{ing_processing}' where train_id = {train_id}"))
            conn.close()

            engine = db_engine()
            conn = engine.connect()
            conn.execute(text(f"insert into data_history_table values ({data_id}, '{ing_flag}', {user_id}, '{create_time}')"))
            conn.close()

            engine = db_engine()
            dataset.to_sql('data_table', engine, schema=database_utils["DATABASE"], if_exists='append',
                                        index=False)

            engine = db_engine()
            conn = engine.connect()
            end_time = get_time_now()
            conn.execute(
                text(f"update train_history_table set ing_end_time = '{end_time}' , status = '{ing_end}' where train_id = {train_id}"))
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
                text(f"update train_history_table set ing_end_time = '{end_time}' , status = '{ing_failed}' where train_id = {train_id}"))
            conn.close()

            engine = db_engine()
            conn = engine.connect()
            conn.execute(text(f"delete from data_history_table where data_id = {data_id}"))
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
    dpp.main(train_id)


def forecasting_pipeline(train_id):
    fp.main(train_id)
