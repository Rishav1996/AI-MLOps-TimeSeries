"""Data-processing stage: per-series outlier detection then imputation via Celery.

``main`` orchestrates the stage for a train_id — it reads the ingested rows, fans the
work out to ``outlier_wrapper`` and ``impute_wrapper`` Celery tasks (one per series),
writes the cleaned rows under a new data_id, and advances the run's status flags.
"""
from data_processing.imputers import linear_imputer, mean_imputer, median_imputer, nearest_imputer
from data_processing.outliers import isolation_forest_detector, local_outlier_factor_detector, zscore_detector

from data_processing.data_processing_helper import get_time_now, db_engine, get_default_parameters_in_dict, \
    get_train_parameters_in_dict, wait_for_tasks
from data_processing.data_processing_config import data_processing_stages, database_utils, data_processing_parameters
import pandas as pd
import warnings
from sqlalchemy import text
from celery_app import celery_client


warnings.filterwarnings("ignore")


def get_ingest_id(train_id):
    """Return the ingested data_id (data_ing_id) for a run."""
    engine = db_engine()
    conn = engine.connect()
    data_id = conn.execute(
        text("select data_ing_id from train_history_table where train_id=:train_id"),
        {"train_id": train_id}).fetchone()[0]
    conn.close()
    return int(data_id)


def get_user_id(train_id):
    """Return the owning user_id for a run."""
    engine = db_engine()
    conn = engine.connect()
    user_id = conn.execute(
        text("select user_id from data_history_table where data_id in (select data_ing_id from train_history_table where train_id=:train_id)"),
        {"train_id": train_id}).fetchone()[0]
    conn.close()
    return int(user_id)


def insert_data_id(data_id, user_id, data_proc_flag):
    """Register a new processed-output data_id in data_history_table."""
    engine = db_engine()
    conn = engine.connect()
    conn.execute(
        text("insert into data_history_table (data_id, user_id, status, data_create_time) "
             "values (:data_id, :user_id, :data_proc_flag, :create_time)"),
        {"data_id": data_id, "user_id": user_id, "data_proc_flag": data_proc_flag, "create_time": get_time_now()})
    conn.commit()
    conn.close()


def generate_dp_id():
    """Allocate the next data_id (max + 1) for the processed output."""
    engine = db_engine()
    conn = engine.connect()
    data_id = conn.execute(text("select ifnull(max(data_id), 0) from data_history_table")).fetchone()[0] + 1
    conn.close()
    return int(data_id)


def set_dp_start_time(train_id):
    """Stamp the data-processing start time for a run."""
    engine = db_engine()
    conn = engine.connect()
    conn.execute(text("update train_history_table set dp_start_time=:now where train_id=:train_id"),
                 {"now": get_time_now(), "train_id": train_id})
    conn.commit()
    conn.close()


def set_dp_end_time(train_id):
    """Stamp the data-processing end time for a run."""
    engine = db_engine()
    conn = engine.connect()
    conn.execute(text("update train_history_table set dp_end_time=:now where train_id=:train_id"),
                 {"now": get_time_now(), "train_id": train_id})
    conn.commit()
    conn.close()


def get_data(data_id):
    """Load (period, ts_id, value) rows for a data_id as a DataFrame."""
    engine = db_engine()
    conn = engine.connect()
    data = conn.execute(text("select period, ts_id, value from data_table where data_id=:data_id"),
                        {"data_id": data_id}).fetchall()
    data = pd.DataFrame(data)
    data.columns = ['period', 'ts_id', 'value']
    conn.close()
    return data


def set_dp_flag(train_id, flag):
    """Set a run's status flag (e.g. DP_S/DP_P1/DP_E/DP_F)."""
    engine = db_engine()
    conn = engine.connect()
    conn.execute(text("update train_history_table set status=:flag where train_id=:train_id"),
                 {"flag": flag, "train_id": train_id})
    conn.commit()
    conn.close()


def set_dp_id(train_id, data_id):
    """Link the processed-output data_id (data_dp_id) to a run."""
    engine = db_engine()
    conn = engine.connect()
    conn.execute(text("update train_history_table set data_dp_id=:data_id where train_id=:train_id"),
                 {"data_id": data_id, "train_id": train_id})
    conn.commit()
    conn.close()


@celery_client.task(autoretry_for=(Exception,), default_retry_delay=5, retry_kwargs={'max_retries': 3})
def outlier_wrapper(dataset, outlier_choice, outlier_cnt, zscore_cutoff):
    """Celery task: run the chosen outlier detector on one series; returns a dict."""
    dataset = pd.DataFrame(dataset)
    dataset.index = dataset['period'].map(pd.to_datetime)
    dataset.sort_index(inplace=True)
    if outlier_choice == 'if':
        dataset = isolation_forest_detector.detector(dataset, outlier_cnt)
    elif outlier_choice == 'lof':
        dataset = local_outlier_factor_detector.detector(dataset, outlier_cnt)
    elif outlier_choice == 'zscore':
        dataset = zscore_detector.detector(dataset, zscore_cutoff)
    dataset.reset_index(inplace=True, drop=True)
    return dataset.to_dict()


@celery_client.task(autoretry_for=(Exception,), default_retry_delay=5, retry_kwargs={'max_retries': 3})
def impute_wrapper(dataset, impute_choice, impute_if_zero):
    """Celery task: run the chosen imputer on one series; returns a dict."""
    dataset = pd.DataFrame(dataset)
    dataset.index = dataset['period'].map(pd.to_datetime)
    dataset.sort_index(inplace=True)
    if impute_choice == 'linear':
        dataset = linear_imputer.imputer(dataset, impute_if_zero)
    elif impute_choice == 'mean':
        dataset = mean_imputer.imputer(dataset, impute_if_zero)
    elif impute_choice == 'median':
        dataset = median_imputer.imputer(dataset, impute_if_zero)
    elif impute_choice == 'nearest':
        dataset = nearest_imputer.imputer(dataset, impute_if_zero)
    dataset.reset_index(inplace=True, drop=True)
    return dataset.to_dict()


def main(train_id):
    """Run the full data-processing stage for a run.

    Reads the ingested series, dispatches outlier-detection then imputation Celery
    tasks per ts_id, writes the cleaned rows under a new data_id, and sets the
    run status to DP_E (or DP_F on failure).
    """
    data_id = get_ingest_id(train_id)
    user_id = get_user_id(train_id)
    parameters = get_default_parameters_in_dict()
    data_proc_start = parameters[data_processing_stages["data_proc_start"]]
    data_proc_processing = parameters[data_processing_stages['data_proc_processing']]
    data_proc_end = parameters[data_processing_stages['data_proc_end']]
    data_proc_failed = parameters[data_processing_stages['data_proc_failed']]
    data_proc_flag = parameters[data_processing_stages['data_proc_flag']]

    train_parameters = get_train_parameters_in_dict(train_id)
    impute_choice = train_parameters[data_processing_parameters['impute_choice']]
    impute_if_zero = True if train_parameters[data_processing_parameters['impute_if_zero']] == 'True' else False
    outlier_choice = train_parameters[data_processing_parameters['outlier_choice']]
    outlier_cnt = train_parameters[data_processing_parameters['outlier_cnt']]
    zscore_cutoff = int(train_parameters[data_processing_parameters['zscore_cutoff']])

    new_data_id = generate_dp_id()

    set_dp_flag(train_id, data_proc_start)
    set_dp_start_time(train_id)

    try:
        dataset = get_data(data_id)

        set_dp_flag(train_id, data_proc_processing)
        set_dp_id(train_id, new_data_id)
        insert_data_id(new_data_id, user_id, data_proc_flag)

        dataset_map = [dataset[dataset['ts_id'] == i].copy() for i in dataset['ts_id'].unique()]
        dataset_ids = [outlier_wrapper.apply_async((i.to_dict(), outlier_choice,
                                                    outlier_cnt, zscore_cutoff), queue='data-processing-pipeline').id for i in dataset_map]
        dataset_results = [pd.DataFrame(result) for result in wait_for_tasks(dataset_ids)]
        dataset = pd.concat(dataset_results, axis=0)

        dataset_map = [dataset[dataset['ts_id'] == i].copy() for i in dataset['ts_id'].unique()]
        dataset_ids = [impute_wrapper.apply_async((i.to_dict(), impute_choice, impute_if_zero), queue='data-processing-pipeline').id for i in dataset_map]
        dataset_results = [pd.DataFrame(result) for result in wait_for_tasks(dataset_ids)]
        dataset = pd.concat(dataset_results, axis=0)

        dataset['data_id'] = new_data_id
        dataset['status'] = data_proc_flag
        dataset['value'] = dataset['value'].fillna(0)
        dataset['value'] = dataset['value'].astype(int)

        engine = db_engine()
        dataset.to_sql('data_table', engine, schema=database_utils["DATABASE"], if_exists='append',
                                    index=False)


        set_dp_flag(train_id, data_proc_end)
    except Exception as e:
        print(e)
        set_dp_flag(train_id, data_proc_failed)
    finally:
        set_dp_end_time(train_id)
