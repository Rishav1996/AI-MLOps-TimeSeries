"""End-to-end pipeline test driven through the running API.

Gated: only runs when RUN_INTEGRATION=1 and the full docker compose stack is up.
Override the API location with API_BASE_URL (default http://localhost:8000).

Flow: signup -> login -> upload CSV -> (ingest) -> data-processing -> forecasting
-> metrics, polling /status between stages until each phase completes.
"""
import io
import json
import os
import re
import time
from datetime import datetime

import numpy as np
import pandas as pd
import pytest

pytestmark = pytest.mark.integration

RUN = os.environ.get("RUN_INTEGRATION") == "1"
BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
POLL_TIMEOUT = int(os.environ.get("INTEGRATION_TIMEOUT", "600"))
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "8306")
SAMPLE_CSV = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "sample data", "sample.csv"))

httpx = pytest.importorskip("httpx")

skip_unless_enabled = pytest.mark.skipif(
    not RUN, reason="integration test disabled; set RUN_INTEGRATION=1 with the stack running")


def _body(response):
    """Endpoints return a (payload, status_code) tuple -> JSON array [payload, code]."""
    data = response.json()
    return data[0] if isinstance(data, list) else data


def _make_csv():
    periods = pd.date_range("2016-01-01", periods=48, freq="MS")
    rows = []
    for ts_id in (1, 2):
        trend = 50 * ts_id + np.arange(48) * (2 + ts_id)
        season = (10 * ts_id) * np.sin(np.arange(48) * (2 * np.pi / 12))
        values = np.round(trend + season + 5, 0)
        for p, v in zip(periods, values):
            rows.append({"period": p.strftime("%Y-%m-%d"), "ts_id": ts_id, "value": float(v)})
    return pd.DataFrame(rows).to_csv(index=False).encode()


def _status_records(client, user_id):
    resp = client.post(f"{BASE_URL}/status", data={"user_id": user_id})
    return json.loads(_body(resp)["data"])


def _poll_phase(client, user_id, train_id, phase, timeout=POLL_TIMEOUT):
    """Wait until `train_id` reaches terminal status for `phase`; return c_status ('E'/'F')."""
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        match = [r for r in _status_records(client, user_id) if int(r["train_id"]) == int(train_id)]
        if match:
            row = match[0]
            last = row
            if row.get("phase") == phase and row.get("c_status") in ("E", "F"):
                return row["c_status"]
        time.sleep(2)
    raise AssertionError(f"Timed out waiting for phase {phase} on train {train_id}; last seen: {last}")


def _query_periods(data_id):
    """Read the distinct stored period strings for a data_id directly from MySQL."""
    from sqlalchemy import create_engine, text
    engine = create_engine(f"mysql+pymysql://mlops_user:MLOPS1234@{DB_HOST}:{DB_PORT}/mlops_ts_fcst")
    with engine.connect() as conn:
        rows = conn.execute(
            text("select period, ts_id from data_table where data_id = :d"), {"d": int(data_id)}).fetchall()
    return rows


@skip_unless_enabled
def test_sample_dataset_pipeline():
    """Drive the bundled sample dataset (DD-MM-YYYY) end-to-end and verify normalization."""
    user = f"sample_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    password = "sample-pass"
    assert os.path.exists(SAMPLE_CSV), f"sample dataset missing at {SAMPLE_CSV}"

    with httpx.Client(timeout=60) as client:
        client.post(f"{BASE_URL}/signup", json={"user_name": user, "user_password": password})
        login = _body(client.post(f"{BASE_URL}/login", json={"user_name": user, "user_password": password}))
        assert login["status"] == "SUCCESS", login
        user_id = login["user_id"]

        with open(SAMPLE_CSV, "rb") as fh:
            content = fh.read()
        upload = _body(client.post(
            f"{BASE_URL}/upload-ingestion-data",
            data={"user_id": user_id},
            files={"file": ("sample.csv", content, "text/csv")}))
        assert upload["status"] == "SUCCESS", upload
        train_id = upload["train_id"]
        assert _poll_phase(client, user_id, train_id, "ING") == "E"

        # DB correctness check: periods normalized to YYYY-MM-DD; 2 series x 24 months
        rec = [r for r in _status_records(client, user_id) if int(r["train_id"]) == int(train_id)][0]
        rows = _query_periods(rec["data_ing_id"])
        periods = [r[0] for r in rows]
        ts_ids = {r[1] for r in rows}
        assert len(periods) == 48, f"expected 48 rows, got {len(periods)}"
        assert ts_ids == {1, 2}, ts_ids
        assert all(re.fullmatch(r"\d{4}-\d{2}-\d{2}", p) for p in periods), "periods not normalized to YYYY-MM-DD"
        assert all(p.endswith("-01") for p in periods), "monthly periods should be first-of-month"

        dp_params = json.dumps({
            "impute_choice": "linear", "impute_if_zero": "False",
            "outlier_choice": "if", "outlier_cnt": "auto", "zscore_cutoff": "3"})
        assert _body(client.post(f"{BASE_URL}/trigger-data-processing", data={
            "user_id": user_id, "train_id": train_id,
            "parameters": dp_params, "train_type": "create"}))["status"] == "SUCCESS"
        assert _poll_phase(client, user_id, train_id, "DP") == "E"

        # exercise every single model (incl. ETS Box-Cox path) on the real sample
        fcst_params = json.dumps({
            "test_size": "0.5", "forecast_horizon": "0.2", "model_choice": "single",
            "model_types": "1,2,3,4,5,6", "auto_ensemble": "0", "ensemble": "0", "data_split": "expanding"})
        assert _body(client.post(f"{BASE_URL}/trigger-forecasting", data={
            "user_id": user_id, "train_id": train_id,
            "parameters": fcst_params, "train_type": "create"}))["status"] == "SUCCESS"
        assert _poll_phase(client, user_id, train_id, "FCST") == "E"

        assert _body(client.post(f"{BASE_URL}/trigger-metrics-calculation",
                                 data={"user_id": user_id, "train_id": train_id}))["status"] == "SUCCESS"


@skip_unless_enabled
def test_full_pipeline():
    user = f"itest_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    password = "itest-pass"

    with httpx.Client(timeout=60) as client:
        # signup + login
        client.post(f"{BASE_URL}/signup", json={"user_name": user, "user_password": password})
        login = _body(client.post(f"{BASE_URL}/login",
                                  json={"user_name": user, "user_password": password}))
        assert login["status"] == "SUCCESS", login
        user_id = login["user_id"]

        # upload -> ingestion
        upload = _body(client.post(
            f"{BASE_URL}/upload-ingestion-data",
            data={"user_id": user_id},
            files={"file": ("itest.csv", _make_csv(), "text/csv")}))
        assert upload["status"] == "SUCCESS", upload
        train_id = upload["train_id"]
        assert _poll_phase(client, user_id, train_id, "ING") == "E"

        # data processing
        dp_params = json.dumps({
            "impute_choice": "linear", "impute_if_zero": "False",
            "outlier_choice": "if", "outlier_cnt": "auto", "zscore_cutoff": "3"})
        dp = _body(client.post(f"{BASE_URL}/trigger-data-processing", data={
            "user_id": user_id, "train_id": train_id,
            "parameters": dp_params, "train_type": "create"}))
        assert dp["status"] == "SUCCESS", dp
        assert _poll_phase(client, user_id, train_id, "DP") == "E"

        # forecasting (naive + theta, single expanding window)
        fcst_params = json.dumps({
            "test_size": "0.5", "forecast_horizon": "0.1", "model_choice": "single",
            "model_types": "3,6", "auto_ensemble": "0", "ensemble": "0",
            "data_split": "expanding"})
        fcst = _body(client.post(f"{BASE_URL}/trigger-forecasting", data={
            "user_id": user_id, "train_id": train_id,
            "parameters": fcst_params, "train_type": "create"}))
        assert fcst["status"] == "SUCCESS", fcst
        assert _poll_phase(client, user_id, train_id, "FCST") == "E"

        # metrics
        metrics = _body(client.post(f"{BASE_URL}/trigger-metrics-calculation",
                                    data={"user_id": user_id, "train_id": train_id}))
        assert metrics["status"] == "SUCCESS", metrics
