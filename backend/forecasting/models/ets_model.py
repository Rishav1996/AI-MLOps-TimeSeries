from sktime.forecasting.all import ExponentialSmoothing
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
        sp = 2
    data['value'] = data['value'] + 1
    model = ExponentialSmoothing(trend='add', seasonal='add', sp=sp, use_boxcox=True)
    model.fit(data['value'])
    forecast = model.predict(fh=forecast_length)
    return forecast
