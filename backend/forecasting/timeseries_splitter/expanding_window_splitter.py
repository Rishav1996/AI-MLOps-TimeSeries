from sktime.forecasting.all import ExpandingWindowSplitter


def splitter(data, initial_window, forecast_length):
    data = data.copy()
    splitter_inst = ExpandingWindowSplitter(initial_window=initial_window, step_length=forecast_length, fh=forecast_length)
    return splitter_inst.split(data)
