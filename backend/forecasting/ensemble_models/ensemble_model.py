"""Ensemble forecaster wrapper (sktime EnsembleForecaster, mean aggregation)."""
import pandas as pd
from sktime.forecasting.compose import EnsembleForecaster



def model(data, forecast_length, n_models):
    """Fit a mean-aggregated ensemble of the given forecasters and forecast the horizon.

    n_models is a list of (name, sktime-forecaster) tuples.
    """
    data = pd.DataFrame(data.values, columns=data.columns)
    data['value'] = data['value'] + 1
    model = EnsembleForecaster(forecasters=n_models, aggfunc='mean')
    model.fit(data['value'], fh=forecast_length)
    forecast = model.predict()
    return forecast
