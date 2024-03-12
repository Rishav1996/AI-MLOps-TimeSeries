from sktime.forecasting.all import PolynomialTrendForecaster



def model(data, forecast_length):
    data = pd.DataFrame(data.values, columns=data.columns)
    data['value'] = data['value'] + 1
    model = PolynomialTrendForecaster(degree=3)
    model.fit(data['value'])
    forecast = model.predict(fh=forecast_length)
    return forecast
