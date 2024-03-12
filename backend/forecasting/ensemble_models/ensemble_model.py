from sktime.forecasting.compose import EnsembleForecaster



def model(data, forecast_length, n_models):
    data = pd.DataFrame(data.values, columns=data.columns)
    data['value'] = data['value'] + 1
    model = EnsembleForecaster(forecasters=n_models, aggfunc='mean')
    model.fit(data['value'], fh=forecast_length)
    forecast = model.predict()
    return forecast
