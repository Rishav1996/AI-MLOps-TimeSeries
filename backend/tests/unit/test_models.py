"""Every forecasting wrapper returns a finite forecast of the requested length.

This is the guard that catches sktime / prophet / pandas API breakage (e.g. the
pandas-2 ``pd.Timedelta('1M')`` regression) without needing the running stack.
"""
import warnings

import numpy as np
import pandas as pd
import pytest
from sktime.forecasting.base import ForecastingHorizon
from sktime.forecasting.all import NaiveForecaster, ThetaForecaster

from forecasting.models import (
    auto_arima_model,
    ets_model,
    naive_model,
    polynomial_trend_model,
    prophet_model,
    theta_model,
)
from forecasting.ensemble_models import ensemble_model, auto_ensemble_model

warnings.filterwarnings("ignore")

HORIZON = 6
SINGLE_MODELS = [
    naive_model,
    polynomial_trend_model,
    theta_model,
    ets_model,
    auto_arima_model,
    prophet_model,
]


@pytest.fixture
def fh():
    return ForecastingHorizon(list(range(1, HORIZON + 1)))


@pytest.mark.parametrize("module", SINGLE_MODELS, ids=lambda m: m.__name__.split(".")[-1])
def test_single_model_forecast(monthly_series, fh, module):
    forecast = module.model(monthly_series.copy(), fh)
    values = np.asarray(forecast, dtype=float).flatten()
    assert len(values) == HORIZON
    assert not np.isnan(values).any()


@pytest.mark.parametrize("module", [ensemble_model, auto_ensemble_model],
                         ids=lambda m: m.__name__.split(".")[-1])
def test_ensemble_model_forecast(monthly_series, fh, module):
    forecasters = [("naive", NaiveForecaster(sp=12)), ("theta", ThetaForecaster(sp=12))]
    forecast = module.model(monthly_series.copy(), fh, forecasters)
    values = np.asarray(forecast, dtype=float).flatten()
    assert len(values) == HORIZON
    assert not np.isnan(values).any()


@pytest.mark.parametrize("model_name", ["naive", "theta", "poly_trend"])
def test_models_forecasts_dispatch(monthly_series, model_name):
    """forecasting_pipeline.models_forecasts dispatches by name and reindexes output."""
    from forecasting.forecasting_pipeline import models_forecasts

    future = pd.date_range("2022-01-01", periods=HORIZON, freq="MS")
    out = models_forecasts(monthly_series.copy(), HORIZON, future, model_name=model_name)
    assert list(out.columns) == ["period", "value"]
    assert len(out) == HORIZON
    assert not out["value"].isna().any()
    assert list(out["period"]) == list(future)


def test_models_forecasts_ensemble_dispatch(monthly_series):
    from forecasting.forecasting_pipeline import models_forecasts

    future = pd.date_range("2022-01-01", periods=HORIZON, freq="MS")
    forecasters = [("naive", NaiveForecaster(sp=12)), ("theta", ThetaForecaster(sp=12))]
    out = models_forecasts(monthly_series.copy(), HORIZON, future, model_lists=forecasters, ensemble=True)
    assert list(out.columns) == ["period", "value"]
    assert len(out) == HORIZON
    assert not out["value"].isna().any()
