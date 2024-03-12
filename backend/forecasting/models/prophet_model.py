from sktime.forecasting.all import Prophet



def model(data, forecast_length):
    freq = data.index.inferred_freq
    if data.index[1] - data.index[0] == pd.Timedelta('1D'):
        freq = 'D'
    elif data.index[1] - data.index[0] == pd.Timedelta('1H'):
        freq = 'H'
    elif data.index[1] - data.index[0] == pd.Timedelta('1M'):
        freq = 'M'
    elif data.index[1] - data.index[0] == pd.Timedelta('1S'):
        freq = 'S'
    elif data.index[1] - data.index[0] == pd.Timedelta('1W'):
        freq = 'W'
    elif data.index[1] - data.index[0] == pd.Timedelta('1Y'):
        freq = 'Y'
    range_time = pd.date_range(start=data.index[0], end=data.index[-1], freq=freq)
    data = pd.DataFrame(data.values, columns=data.columns, index=range_time[:data.shape[0]])
    model = Prophet()
    model.fit(data['value'])
    forecast = model.predict(fh=forecast_length)
    return forecast
