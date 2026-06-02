# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is an MLOps platform for time series forecasting. Users upload CSV data, run it through configurable outlier detection and imputation pipelines, run forecasting models, then visualize results and metrics in a Streamlit dashboard.

## Toolchain

Both Python services (`backend`, `visualization`) are **uv** projects on **Python
3.12** — each has a `pyproject.toml` (`[project]` table) and a committed `uv.lock`.
The Dockerfiles export the lock and install into the image's system interpreter
(see "Docker volume gotcha" below). There is no Poetry and no `requirements.txt`.

## Running the Full Stack

Everything runs via Docker Compose (v2):

```bash
# Build + start all services
docker compose up --build

# Rebuild a single service
docker compose up --build backend

# Reset seeded volumes so new code/deps propagate (see gotcha below)
docker compose down -v && docker compose up --build
```

Service endpoints once running:
- **API**: http://localhost:8000 (health: `/test`)
- **Frontend**: http://localhost:8001
- **Streamlit dashboard**: http://localhost:8501
- **Flower (Celery monitor)**: http://localhost:5555
- **MySQL**: localhost:8306 (user: `mlops_user`, password: `MLOPS1234`, db: `mlops_ts_fcst`)

### Docker volume gotcha
The Python services share code via the `api_data` named volume mounted at `/app`,
which Docker seeds from the image **only when the volume is empty**. Dependencies are
therefore installed into the system interpreter (`/usr/local`, outside `/app`) so the
mount can't shadow them, and code changes require `docker compose down -v` to refresh
the seeded volume.

## Running Services Locally (without Docker)

**Backend** (requires MySQL and Redis running):
```bash
cd backend
uv sync                 # add --extra dev for the test dependencies
uv run uvicorn app:app --port 8000 --reload --host 0.0.0.0
```

**Celery workers** (run from `backend/` directory):
```bash
uv run celery -A data_processing.data_processing_pipeline worker --loglevel=INFO -Q data-processing-pipeline -E
uv run celery -A forecasting.forecasting_pipeline worker --loglevel=INFO -Q forecasting-pipeline -E
```

**Visualization**:
```bash
cd visualization
uv sync
uv run streamlit run app.py
```

**Frontend**:
```bash
cd frontend
npm install
npm start   # dev server
npm run build  # production build
```

## Testing

```bash
cd backend
uv sync --extra dev
uv run pytest tests/unit -q          # hermetic: detectors, imputers, models, metrics

# end-to-end (stack must be up); gated by RUN_INTEGRATION
docker compose up --build -d
./tests/run_integration.sh           # tests\run_integration.ps1 on Windows
```

Unit tests import the packages directly via `backend/conftest.py` (which puts the
backend dir on `sys.path`). `tests/unit/test_models.py` is the guard that catches
sktime/pandas API regressions.

## Architecture

### Service Map

```
frontend (React, :8001)
    └── backend (FastAPI, :8000)
            ├── celery_data_processing (queue: data-processing-pipeline)
            ├── celery_forecasting     (queue: forecasting-pipeline, 2 replicas)
            ├── Redis (:6379)          — Celery broker/backend
            └── MySQL (:8306)          — all persistent state

visualization (Streamlit, :8501) — reads MySQL directly
flower_web (:5555)               — Celery task monitoring
```

### Three-Stage Pipeline

All state is tracked by `train_id`. Each stage creates a new `data_id` in `data_history_table` and stores data rows in `data_table` with that `data_id`.

1. **Ingestion** (`control/control_modal.py:ingest_data`) — FastAPI background task; reads uploaded CSV, writes raw rows to `data_table`, sets status to `ING_E` on success.

2. **Data Processing** (`data_processing/data_processing_pipeline.py:main`) — Dispatches per-series Celery tasks for outlier detection then imputation; writes cleaned rows to `data_table` with a new `data_id`; sets status `DP_E`.

3. **Forecasting** (`forecasting/forecasting_pipeline.py:main`) — Dispatches per-series×model Celery tasks; supports expanding/sliding window CV splits; writes forecast rows with `model_id`; sets status `FCST_E`.

Status codes are string abbreviations (`ING_E`, `DP_S`, `DP_P`, `DP_F`, `FCST_E`, etc.) sourced from `parameter_table` via integer IDs defined in `*_config.py` files.

### Key Database Tables

| Table | Purpose |
|---|---|
| `train_history_table` | One row per `train_id`; links `data_ing_id`, `data_dp_id`, `data_fcst_id`; tracks status and timestamps |
| `data_history_table` | One row per `data_id` (each pipeline stage output) |
| `data_table` | All data rows (raw, processed, forecast) keyed by `data_id` |
| `parameter_table` | Default pipeline parameters; IDs map to constants in `*_config.py` |
| `train_parameter_table` | Per-run parameter overrides |
| `train_metric_table` | Per-run, per-ts, per-model, per-split metrics |
| `model_table` | Model registry; IDs 1-6 = individual models, 7 = auto-ensemble, 8 = ensemble |

### Config Pattern

Each module (`control`, `data_processing`, `forecasting`, `metrics`, `visualization`) has its own `*_config.py` that duplicates the DB connection dict and maps stage/parameter names to integer IDs in `parameter_table`. When adding a new parameter, add it to `parameter_table` via a MySQL script **and** update the relevant `*_config.py` integer mappings (all copies — they are kept in sync; e.g. `'ensemble': 28`).

### SQL access

All DB access uses parameterized `text(...)` queries with bound parameters (e.g.
`conn.execute(text("... where x = :x"), {"x": x})`) — never f-string interpolation.
Writes must `conn.commit()` before `conn.close()` (SQLAlchemy 2.0 rolls back otherwise).

### Celery Task Parallelism

Data processing and forecasting both split work by `ts_id` (and by model for forecasting) and dispatch async Celery tasks, then wait via the `wait_for_tasks(ids)` helper (in each package's `*_helper.py`), which polls with a sleep and raises if any task fails. Tasks use autoretry with 3 retries on any exception. The two queues (`data-processing-pipeline`, `forecasting-pipeline`) are routed in `celery_app.py`.

### Input Data Format

CSVs uploaded via `/upload-ingestion-data` must have columns: `period`, `ts_id`, `value`. `ingest_data` normalizes `period` to `YYYY-MM-DD` via `pd.to_datetime(..., dayfirst=True)`, so `DD-MM-YYYY` inputs also work. A sample is committed at `sample data/sample.csv`.

### Forecasting Models

Individual models (via sktime): `arima`, `ets`, `naive`, `poly_trend`, `theta`, `prophet`  
Ensemble modes: `auto_ensemble` (model_id=7, `AutoEnsembleForecaster`), `ensemble` (model_id=8, `EnsembleForecaster`)

Seasonal period (`sp`) and frequency are derived from the index via `forecasting_helper.seasonal_period()` / `freq_string()` — day-delta based, since pandas 2 rejects `pd.Timedelta('1M'/'1Y')`. Do **not** reintroduce month/year `pd.Timedelta` comparisons.

### Outlier detection

`isolation_forest_detector` and `local_outlier_factor_detector` call scikit-learn
directly (`fit_predict(...) == -1` marks outliers). The unmaintained `adtk` dependency
was removed — do not reintroduce it.

## Dependencies

- Backend & Visualization: **Python 3.12**, managed with **uv** (`pyproject.toml` + `uv.lock`). Key backend packages: FastAPI, Celery[redis], sktime, pmdarima, prophet, scikit-learn, statsmodels, SQLAlchemy 2, pymysql, pandas 2, numpy<2 (pmdarima constraint). Dev extras: pytest, httpx.
- Frontend: Node/npm. Key packages: React 17, Ant Design 4, Semantic UI React, rsuite.

MySQL schema is initialized from `mysql/scripts/*.sql` via Docker entrypoint.
