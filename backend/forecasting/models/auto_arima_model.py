import pandas as pd
from sktime.forecasting.all import AutoARIMA


def model(data, forecast_length):
    data = pd.DataFrame(data.values, columns=data.columns)
    model = AutoARIMA(maxiter=20)
    model.fit(data['value'])
    forecast = model.predict(fh=forecast_length)
    return forecast
