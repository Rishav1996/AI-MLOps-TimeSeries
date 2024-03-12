from sktime.forecasting.all import NaiveForecaster



def model(data, forecast_length):
    sp = 1
    if data.index[1] - data.index[0] == pd.Timedelta('1D'):
        sp = 365
    elif data.index[1] - data.index[0] == pd.Timedelta('1M'):
        sp = 12
    elif data.index[1] - data.index[0] == pd.Timedelta('1W'):
        sp = 52
    data = pd.DataFrame(data.values, columns=data.columns)
    if data.shape[0] < (2 * sp):
        sp = 1
    model = NaiveForecaster(sp=sp)
    model.fit(data['value'])
    forecast = model.predict(fh=forecast_length)
    return forecast
