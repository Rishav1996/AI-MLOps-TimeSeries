# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is an MLOps platform for time series forecasting. Users upload CSV data, run it through configurable outlier detection and imputation pipelines, run forecasting models, then visualize results and metrics in a Streamlit dashboard.

## Running the Full Stack

Everything runs via Docker Compose. The standard workflow:

```bash
# Build images (first time or after code changes)
docker-compose build

# Start all services
docker-compose up

# Rebuild a single service
docker-compose up --build backend
```

Service endpoints once running:
- **API**: http://localhost:8000
- **Frontend**: http://localhost:8001
- **Streamlit dashboard**: http://localhost:8501
- **Flower (Celery monitor)**: http://localhost:5555
- **MySQL**: localhost:8306 (user: `mlops_user`, password: `MLOPS1234`, db: `mlops_ts_fcst`)

## Running Services Locally (without Docker)

**Backend** (requires MySQL and Redis running):
```bash
cd backend
poetry install
poetry run uvicorn app:app --port 8000 --reload --host 0.0.0.0
```

**Celery workers** (run from `backend/` directory):
```bash
poetry run celery -A data_processing.data_processing_pipeline worker --loglevel=INFO -Q data-processing-pipeline -E
poetry run celery -A forecasting.forecasting_pipeline worker --loglevel=INFO -Q forecasting-pipeline -E
```

**Visualization**:
```bash
cd visualization
poetry install
poetry run streamlit run app.py
```

**Frontend**:
```bash
cd frontend
npm install
npm start   # dev server
npm run build  # production build
```

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

Each module (`control`, `data_processing`, `forecasting`, `metrics`, `visualization`) has its own `*_config.py` that duplicates the DB connection dict and maps stage/parameter names to integer IDs in `parameter_table`. When adding a new parameter, add it to `parameter_table` via a MySQL script **and** update the relevant `*_config.py` integer mappings.

> **Known inconsistency**: `control/control_config.py` and `data_processing/data_processing_config.py` use `'stacking': 28` but `forecasting/forecasting_config.py` correctly uses `'ensemble': 28` (matches what `forecasting_pipeline.py` reads).

### Celery Task Parallelism

Data processing and forecasting both split work by `ts_id` (and by model for forecasting) and dispatch async Celery tasks, then busy-wait on `AsyncResult` state. Tasks use autoretry with 3 retries on any exception. The two queues (`data-processing-pipeline`, `forecasting-pipeline`) are routed in `celery_app.py`.

### Input Data Format

CSVs uploaded via `/upload-ingestion-data` must have columns: `period`, `ts_id`, `value`. Periods are parsed with `pd.to_datetime`.

### Forecasting Models

Individual models (via sktime): `arima`, `ets`, `naive`, `poly_trend`, `theta`, `prophet`  
Ensemble modes: `auto_ensemble` (model_id=7, `AutoEnsembleForecaster`), `ensemble` (model_id=8, `EnsembleForecaster`)

The `sp` (seasonal period) is inferred from date frequency: daily→365, weekly→52, monthly→12.

## Dependencies

- Backend: Python ≥3.8,<3.13 managed with Poetry. Key packages: FastAPI, Celery[redis], sktime, pmdarima, SQLAlchemy, pymysql.
- Visualization: Poetry. Key packages: Streamlit, Plotly, SQLAlchemy.
- Frontend: Node/npm. Key packages: React 17, Ant Design 4, Semantic UI React, rsuite.

MySQL schema is initialized from `mysql/scripts/*.sql` via Docker entrypoint.
