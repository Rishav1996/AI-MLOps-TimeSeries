"""Imputers fill missing values and honor the impute-if-zero flag."""
import numpy as np
import pytest

from data_processing.imputers import (
    linear_imputer,
    mean_imputer,
    median_imputer,
    nearest_imputer,
)

ALL_IMPUTERS = [linear_imputer, mean_imputer, median_imputer, nearest_imputer]


@pytest.mark.parametrize("module", ALL_IMPUTERS)
def test_imputer_fills_nan(series_frame, module):
    gapped = series_frame.copy()
    gapped.loc[gapped.index[5], "value"] = np.nan
    gapped.loc[gapped.index[20], "value"] = np.nan

    result = module.imputer(gapped, if_zero=False)

    assert result["value"].isna().sum() == 0
    assert result.shape[0] == gapped.shape[0]


@pytest.mark.parametrize("module", ALL_IMPUTERS)
def test_imputer_treats_zero_as_missing_when_flagged(series_frame, module):
    zeroed = series_frame.copy()
    zeroed.loc[zeroed.index[7], "value"] = 0.0

    result = module.imputer(zeroed, if_zero=True)

    # the zero should have been replaced by an imputed (non-zero) value
    assert result.loc[result.index[7], "value"] != 0.0
    assert result["value"].isna().sum() == 0
