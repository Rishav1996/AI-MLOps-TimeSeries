"""Expanding-window cross-validation splitter (sktime ExpandingWindowSplitter)."""
from sktime.forecasting.all import ExpandingWindowSplitter


def splitter(data, initial_window, forecast_length):
    """Yield expanding train/test index splits; train grows by forecast_length each step."""
    data = data.copy()
    splitter_inst = ExpandingWindowSplitter(initial_window=initial_window, step_length=forecast_length, fh=forecast_length)
    return splitter_inst.split(data)
