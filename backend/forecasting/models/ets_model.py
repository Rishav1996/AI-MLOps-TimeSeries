"""ETS / exponential-smoothing forecaster wrapper (sktime ExponentialSmoothing)."""
from sktime.forecasting.all import ExponentialSmoothing
import pandas as pd
from forecasting.forecasting_helper import seasonal_period


def model(data, forecast_length):
    """Fit additive ExponentialSmoothing on 'value' (shifted +1) and forecast."""
    sp = seasonal_period(data.index, default=2)
    data = pd.DataFrame(data.values, columns=data.columns)
    if data.shape[0] < (2 * sp):
        sp = 2
    data['value'] = data['value'] + 1
    model = ExponentialSmoothing(trend='add', seasonal='add', sp=sp, use_boxcox=True)
    model.fit(data['value'])
    forecast = model.predict(fh=forecast_length)
    return forecast
