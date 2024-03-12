from sktime.forecasting.compose import AutoEnsembleForecaster



def model(data, forecast_length, n_models):
    data = pd.DataFrame(data.values, columns=data.columns)
    data['value'] = data['value'] + 1
    model = AutoEnsembleForecaster(forecasters=n_models)
    model.fit(data['value'], fh=forecast_length)
    forecast = model.predict()
    return forecast
