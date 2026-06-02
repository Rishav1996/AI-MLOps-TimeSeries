"""Read-only DB access for the Streamlit dashboard (history, forecasts, metrics).

The query functions fetch rows from MySQL; the pure transform helpers
(``merge_history``, ``merge_forecast``, ``normalize_metric``) shape, parse and
sort the frames. The transforms take no DB connection so they can be imported
and unit-tested in isolation.
"""
from config import database_utils
from sqlalchemy import create_engine, text
import pandas as pd


def db_engine():
    """Build a SQLAlchemy engine for the configured MySQL database."""
    conn_url = f'{database_utils["DRIVER"]}://{database_utils["USER"]}:{database_utils["PASSWORD"]}@' \
               f'{database_utils["HOST"]}:{database_utils["PORT"]}/{database_utils["DATABASE"]}'
    engine = create_engine(conn_url, echo=False)
    return engine


# --- pure transforms (no DB; unit-testable) --------------------------------

def merge_history(result_ing, result_dp):
    """Merge raw and processed history on (period, ts_id).

    Periods are stored as canonical ``YYYY-MM-DD`` strings; they are parsed to
    datetime and the frame is sorted chronologically within each series so line
    charts connect points in time order rather than DB-return order.
    """
    result = pd.merge(result_ing, result_dp, on=['period', 'ts_id'], how='outer')
    result['period'] = pd.to_datetime(result['period'])
    return result.sort_values(by=['ts_id', 'period']).reset_index(drop=True)


def merge_forecast(actual_data, forecast_data):
    """Merge actuals with forecast rows on (period, ts_id).

    Parses periods to datetime and sorts each (series, model, split) group
    chronologically. ``split_no`` is stored as a string, so it is sorted on a
    numeric key (fold 10 follows fold 9, not fold 1).
    """
    result = pd.merge(actual_data, forecast_data, on=['period', 'ts_id'], how='inner')
    result['period'] = pd.to_datetime(result['period'])
    sort_cols = ['ts_id']
    for col in ('model_name', 'split_window'):
        if col in result.columns:
            sort_cols.append(col)
    if 'split_no' in result.columns:
        result = result.assign(_split_no=pd.to_numeric(result['split_no'], errors='coerce'))
        sort_cols.append('_split_no')
    sort_cols.append('period')
    result = result.sort_values(by=sort_cols).reset_index(drop=True)
    return result.drop(columns='_split_no', errors='ignore')


def normalize_metric(result):
    """Coerce ``split_no`` to str and ``metric_value`` to float for the metric frame."""
    result = result.copy()
    result['split_no'] = result['split_no'].astype(str)
    result['metric_value'] = result['metric_value'].astype(float)
    return result


def get_list_of_train_data_id(user_id):
    """Return a user's completed (FCST_E) runs and their ingest/dp/fcst data_ids."""
    engine = db_engine()
    conn = engine.connect()
    query = text(
        "SELECT th.train_id, th.data_ing_id, th.data_dp_id, th.data_fcst_id "
        "FROM mlops_ts_fcst.train_history_table th "
        "inner join mlops_ts_fcst.data_history_table dh on (th.data_ing_id = dh.data_id) "
        "where dh.user_id = :user_id and th.status = 'FCST_E'")
    result = conn.execute(query, {"user_id": user_id}).fetchall()
    result = pd.DataFrame(result, columns=['train_id', 'data_ing_id', 'data_dp_id', 'data_fcst_id'])
    result = {'train_id': result['train_id'].tolist(),
              'data_ing_id': result['data_ing_id'].tolist(),
              'data_dp_id': result['data_dp_id'].tolist(),
              'data_fcst_id': result['data_fcst_id'].tolist()}
    conn.close()
    return result


def get_data(data_ing_id, data_dp_id):
    """Return raw vs. processed history per period/ts_id for a run (merged, time-sorted)."""
    engine = db_engine()
    conn = engine.connect()
    query = text("select period, ts_id, value from data_table where data_id = :data_id")
    result_ing = conn.execute(query, {"data_id": data_ing_id}).fetchall()
    result_ing = pd.DataFrame(result_ing, columns=['period', 'ts_id', 'raw_history'])
    result_dp = conn.execute(query, {"data_id": data_dp_id}).fetchall()
    result_dp = pd.DataFrame(result_dp, columns=['period', 'ts_id', 'processed_history'])
    conn.close()
    return merge_history(result_ing, result_dp)


def get_forecast_data(train_id):
    """Return actuals joined with forecast rows (per split/model) for a run."""
    engine = db_engine()
    conn = engine.connect()
    data_ing_id = conn.execute(
        text("select data_ing_id from train_history_table where train_id = :train_id"),
        {"train_id": train_id}).fetchone()[0]
    data_fcst_id = conn.execute(
        text("select data_fcst_id from train_history_table where train_id = :train_id"),
        {"train_id": train_id}).fetchone()[0]
    actual_data = conn.execute(
        text("select period, ts_id, value from data_table where data_id = :data_id"),
        {"data_id": data_ing_id}).fetchall()
    actual_data = pd.DataFrame(actual_data, columns=['period', 'ts_id', 'raw_history'])
    forecast_data = conn.execute(
        text("select period, ts_id, value, split_window, split_no + 1 as split_no, m.model_name "
             "from data_table d inner join model_table m on(d.model_id = m.model_id) where data_id = :data_id"),
        {"data_id": data_fcst_id}).fetchall()
    forecast_data = pd.DataFrame(forecast_data, columns=['period', 'ts_id', 'forecast', 'split_window', 'split_no', 'model_name'])
    forecast_data['split_no'] = forecast_data['split_no'].astype(str)
    conn.close()
    return merge_forecast(actual_data, forecast_data)


def get_metric_data(train_id):
    """Return per-ts/model/split metric values (with names) for a run."""
    engine = db_engine()
    conn = engine.connect()
    query = text(
        "SELECT ts_id, m.model_name, split_window, split_no + 1 as split_no, me.metric_name, metric_value "
        "FROM mlops_ts_fcst.train_metric_table tm "
        "inner join model_table m on(m.model_id = tm.model_id) "
        "inner join metric_table me on(me.metric_id = tm.metric_id) where train_id = :train_id")
    result = conn.execute(query, {"train_id": train_id}).fetchall()
    result = pd.DataFrame(result, columns=['ts_id', 'model_name', 'split_window', 'split_no', 'metric_name', 'metric_value'])
    conn.close()
    return normalize_metric(result)
