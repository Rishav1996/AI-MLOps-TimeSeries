"""Polynomial trend forecaster wrapper (sktime PolynomialTrendForecaster, degree 3)."""
import pandas as pd
from sktime.forecasting.all import PolynomialTrendForecaster



def model(data, forecast_length):
    """Fit a degree-3 polynomial trend on 'value' and forecast over the horizon."""
    data = pd.DataFrame(data.values, columns=data.columns)
    data['value'] = data['value'] + 1
    model = PolynomialTrendForecaster(degree=3)
    model.fit(data['value'])
    forecast = model.predict(fh=forecast_length)
    return forecast
