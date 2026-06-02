"""Auto-ensemble forecaster wrapper (sktime AutoEnsembleForecaster, learned weights)."""
import pandas as pd
from sktime.forecasting.compose import AutoEnsembleForecaster



def model(data, forecast_length, n_models):
    """Fit an auto-weighted ensemble of the given forecasters and forecast the horizon.

    n_models is a list of (name, sktime-forecaster) tuples.
    """
    data = pd.DataFrame(data.values, columns=data.columns)
    data['value'] = data['value'] + 1
    model = AutoEnsembleForecaster(forecasters=n_models)
    model.fit(data['value'], fh=forecast_length)
    forecast = model.predict()
    return forecast
