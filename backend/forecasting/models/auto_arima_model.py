from sktime.forecasting.all import AutoARIMA
import pandas as pnd


def model(data, forecast_length):
    data = pnd.DataFrame(data.values, columns=data.columns)
    model = AutoARIMA(maxiter=20)
    model.fit(data['value'])
    forecast = model.predict(fh=forecast_length)
    return forecast
