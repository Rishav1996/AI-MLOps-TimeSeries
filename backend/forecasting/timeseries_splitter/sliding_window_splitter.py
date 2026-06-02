"""Sliding-window cross-validation splitter (sktime SlidingWindowSplitter)."""
from sktime.forecasting.all import SlidingWindowSplitter


def splitter(data, window_length, forecast_length):
    """Yield sliding train/test index splits; the fixed-size train window moves forward."""
    data = data.copy()
    splitter_inst = SlidingWindowSplitter(window_length=window_length, step_length=forecast_length, fh=forecast_length)
    return splitter_inst.split(data)
