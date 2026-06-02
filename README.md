# AI-MLOps-TimeSeries

A self-hosted MLOps platform for **time-series forecasting**. Upload a CSV of one
or more series, clean it (outlier detection + imputation), run a battery of
forecasting models with cross-validation, and explore the forecasts and accuracy
metrics in an interactive dashboard.

---

## 1. What it does

The platform runs every dataset through four sequential stages, each tracked by a
`train_id`:

1. **Ingestion** — a CSV is uploaded and its rows are loaded into the database.
2. **Data processing** — per series, outliers are detected (Isolation Forest, Local
   Outlier Factor, or Z-score) and the resulting gaps are imputed (linear, mean,
   median, or nearest).
3. **Forecasting** — each series is forecast with the selected models over expanding
   and/or sliding cross-validation windows. Single models: ARIMA, ETS, Naive,
   Polynomial Trend, Prophet, Theta. Plus an ensemble and an auto-ensemble.
4. **Metrics** — accuracy (RMSE, RMSPE, MAPE, AIC, BIC, Bias) and stability/drift
   (PSI, KS) metrics are computed and stored.

Results are served through a Streamlit dashboard and a React front end.

## 2. Architecture

```
frontend (React, :8001)
    └── backend (FastAPI, :8000)
            ├── celery_data_processing   (queue: data-processing-pipeline)
            ├── celery_forecasting        (queue: forecasting-pipeline, 2 replicas)
            ├── Redis (:6379)             — Celery broker / result backend
            └── MySQL (:8306 -> 3306)     — all persistent state

visualization (Streamlit, :8501)  — reads MySQL directly
flower_web (:5555)                 — Celery task monitoring
```

**Data model.** Each pipeline stage writes a new `data_id` worth of rows into
`data_table`, and the `train_history_table` row for a `train_id` links the ingestion
(`data_ing_id`), processed (`data_dp_id`) and forecast (`data_fcst_id`) outputs along
with status and timing. Stage status codes (`ING_E`, `DP_E`, `FCST_E`, …) come from
`parameter_table`. See [CLAUDE.md](CLAUDE.md) for the full table reference.

**Parallelism.** Data processing and forecasting fan work out across Celery tasks
(one per series, or per series×model) and wait for completion via a shared
`wait_for_tasks` helper.

## 3. Prerequisites

- **Docker** and **Docker Compose v2** — the only requirement to run the full stack.
- **[uv](https://docs.astral.sh/uv/)** and **Python 3.12** — only for local
  development / running tests outside Docker.

## 4. Quick start (Docker)

```bash
docker compose up --build
```

First run seeds the MySQL schema from `mysql/scripts/*.sql`. Once healthy:

| Service           | URL                       |
| ----------------- | ------------------------- |
| API (FastAPI)     | http://localhost:8000     |
| API health check  | http://localhost:8000/test |
| Front end (React) | http://localhost:8001     |
| Dashboard         | http://localhost:8501     |
| Flower (Celery)   | http://localhost:5555     |
| MySQL             | localhost:8306            |

> **Picking up code/dependency changes:** the Python services share code through a
> seeded named volume (`api_data`). After changing dependencies or rebuilding images,
> reset the volumes so the new content propagates:
> ```bash
> docker compose down -v && docker compose up --build
> ```

## 5. Local development (without Docker)

Each Python service is an independent **uv** project (`pyproject.toml` + `uv.lock`).
You need MySQL and Redis reachable at the hosts in `backend/global_config.py`
(defaults assume the Docker network).

**Backend (API):**
```bash
cd backend
uv sync                       # add --extra dev for tests
uv run uvicorn app:app --port 8000 --reload --host 0.0.0.0
```

**Celery workers** (run from `backend/`):
```bash
uv run celery -A data_processing.data_processing_pipeline worker -Q data-processing-pipeline -E --loglevel=INFO
uv run celery -A forecasting.forecasting_pipeline worker -Q forecasting-pipeline -E --loglevel=INFO
```

**Dashboard:**
```bash
cd visualization
uv sync
uv run streamlit run app.py
```

**Front end:**
```bash
cd frontend
npm install
npm start          # dev server; `npm run build` for production
```

## 6. Testing

**Unit tests** (hermetic — no DB or Redis needed) cover the outlier detectors,
imputers, every forecasting model wrapper, and the metric functions:

```bash
cd backend
uv sync --extra dev
uv run pytest tests/unit -q
```

**End-to-end integration test** drives ingest → process → forecast → metrics through
the API. It is skipped unless `RUN_INTEGRATION=1` and requires the stack to be up:

```bash
docker compose up --build -d          # ensure the API is healthy on :8000
./tests/run_integration.sh            # or: tests\run_integration.ps1 on Windows
```

The runner sets `RUN_INTEGRATION=1` and executes `backend/tests/integration`.
Override the target with `API_BASE_URL`.

## 7. Input data format

Uploaded CSVs must have exactly these columns:

| Column   | Description                                      |
| -------- | ------------------------------------------------ |
| `period` | Date string, `YYYY-MM-DD` (stored as `VARCHAR(10)`) |
| `ts_id`  | Integer series identifier                        |
| `value`  | Numeric observation                              |

Multiple series share one file, distinguished by `ts_id`.

## 8. Project layout

```
backend/            FastAPI app, Celery pipelines, models & metrics (uv project)
  control/          API helpers, ingestion, DB access
  data_processing/  outlier detectors, imputers, processing pipeline
  forecasting/      model wrappers, ensembles, CV splitters, forecasting pipeline
  metrics/          performance-metric calculation
  tests/            unit/ (hermetic) and integration/ (gated) tests
visualization/      Streamlit dashboard (uv project)
frontend/           React application
mysql/              Dockerfile + schema/seed scripts
docker-compose.yml  full-stack orchestration
```

## 9. Tech stack

Python 3.12 · FastAPI · Celery + Redis · MySQL 8 · SQLAlchemy 2 · pandas 2 ·
sktime · pmdarima · Prophet · scikit-learn · statsmodels · Streamlit · Plotly ·
React · packaged and locked with **uv**.
