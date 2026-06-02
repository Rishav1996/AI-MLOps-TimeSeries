"""Naive (last-value / seasonal-naive) forecaster wrapper (sktime NaiveForecaster)."""
import pandas as pd
from sktime.forecasting.all import NaiveForecaster
from forecasting.forecasting_helper import seasonal_period


def model(data, forecast_length):
    """Fit a seasonal-naive model on 'value' and forecast over the horizon."""
    sp = seasonal_period(data.index, default=1)
    data = pd.DataFrame(data.values, columns=data.columns)
    if data.shape[0] < (2 * sp):
        sp = 1
    model = NaiveForecaster(sp=sp)
    model.fit(data['value'])
    forecast = model.predict(fh=forecast_length)
    return forecast
