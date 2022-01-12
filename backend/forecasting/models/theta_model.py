from sktime.forecasting.all import ThetaForecaster
import pandas as pnd


def model(data, forecast_length):
    sp = 1
    if data.index[1] - data.index[0] == pnd.Timedelta('1D'):
        sp = 365
    elif data.index[1] - data.index[0] == pnd.Timedelta('1M'):
        sp = 12
    elif data.index[1] - data.index[0] == pnd.Timedelta('1W'):
        sp = 52
    data = pnd.DataFrame(data.values, columns=data.columns)
    if data.shape[0] < (2 * sp):
        sp = 1
    data['value'] = data['value'] + 1
    model = ThetaForecaster(sp=sp)
    model.fit(data['value'])
    forecast = model.predict(fh=forecast_length)
    return forecast
