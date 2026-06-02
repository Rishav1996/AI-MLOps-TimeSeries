"""Prophet forecaster wrapper (sktime Prophet)."""
import pandas as pd
from sktime.forecasting.all import Prophet
from forecasting.forecasting_helper import freq_string


def model(data, forecast_length):
    """Fit Prophet on 'value' over a regularized date range and forecast the horizon."""
    freq = freq_string(data.index)
    range_time = pd.date_range(start=data.index[0], end=data.index[-1], freq=freq)
    data = pd.DataFrame(data.values, columns=data.columns, index=range_time[:data.shape[0]])
    model = Prophet()
    model.fit(data['value'])
    forecast = model.predict(fh=forecast_length)
    return forecast
