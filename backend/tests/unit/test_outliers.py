"""Outlier detectors flag injected spikes as NaN and preserve the frame shape."""
import numpy as np
import pytest

from data_processing.outliers import (
    isolation_forest_detector,
    local_outlier_factor_detector,
    zscore_detector,
)


@pytest.mark.parametrize("module,contamination", [
    (isolation_forest_detector, 0.05),
    (local_outlier_factor_detector, 0.05),
    (zscore_detector, 3),
])
def test_detector_flags_spike(series_frame, module, contamination):
    spiked = series_frame.copy()
    spiked.loc[spiked.index[10], "value"] = 999999.0

    result = module.detector(spiked, contamination)

    # columns preserved, row count unchanged
    assert list(result.columns) == list(spiked.columns)
    assert result.shape[0] == spiked.shape[0]
    # at least the injected spike is detected and blanked
    assert result["value"].isna().sum() >= 1


def test_detector_keeps_clean_series_mostly_intact(series_frame):
    # zscore on a smooth series should flag nothing
    result = zscore_detector.detector(series_frame.copy(), 3)
    assert result["value"].isna().sum() == 0
