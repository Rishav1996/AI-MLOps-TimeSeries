from sktime.forecasting.all import SlidingWindowSplitter


def splitter(data, window_length, forecast_length):
    data = data.copy()
    splitter_inst = SlidingWindowSplitter(window_length=window_length, step_length=forecast_length, fh=forecast_length)
    return splitter_inst.split(data)
