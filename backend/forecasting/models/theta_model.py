import pandas as pd
from sktime.forecasting.all import ThetaForecaster
from forecasting.forecasting_helper import seasonal_period


def model(data, forecast_length):
    sp = seasonal_period(data.index, default=1)
    data = pd.DataFrame(data.values, columns=data.columns)
    if data.shape[0] < (2 * sp):
        sp = 1
    data['value'] = data['value'] + 1
    model = ThetaForecaster(sp=sp)
    model.fit(data['value'])
    forecast = model.predict(fh=forecast_length)
    return forecast
