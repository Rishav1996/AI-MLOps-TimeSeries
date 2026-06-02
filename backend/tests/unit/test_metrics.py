"""Performance and stability metrics return finite, sane values."""
import math

import numpy as np
import pytest

from metrics.performance_metrics import (
    rmse_metric,
    rmspe_metric,
    mape_metric,
    aic_metric,
    bic_metric,
    bias_metric,
)
from forecasting.stability_metrics import psi_metric, ks_metric

Y_TRUE = np.array([10.0, 12.0, 13.0, 12.0, 15.0, 16.0, 18.0, 17.0])
Y_PRED = np.array([11.0, 11.5, 13.5, 12.5, 14.0, 16.5, 17.0, 17.5])


@pytest.mark.parametrize("module", [rmse_metric, rmspe_metric, mape_metric,
                                    aic_metric, bic_metric, bias_metric])
def test_performance_metric_is_finite(module):
    value = float(module.metric_loss(Y_TRUE, Y_PRED))
    assert math.isfinite(value)


def test_rmse_zero_for_identical_series():
    assert float(rmse_metric.metric_loss(Y_TRUE, Y_TRUE)) == pytest.approx(0.0, abs=1e-9)


@pytest.mark.parametrize("module", [aic_metric, bic_metric])
def test_aic_bic_handle_perfect_fit(module):
    # mse == 0 must not raise (log(0) guard)
    value = float(module.metric_loss(Y_TRUE, Y_TRUE))
    assert math.isfinite(value)


def test_mape_capped_at_one():
    # mape_metric clamps to 1.0 for large relative errors
    huge_error = mape_metric.metric_loss(np.array([1.0, 1.0]), np.array([100.0, 100.0]))
    assert huge_error == pytest.approx(1.0)


@pytest.mark.parametrize("module", [psi_metric, ks_metric])
def test_stability_metric_is_finite(module):
    value = float(np.asarray(module.metric_loss(Y_TRUE, Y_PRED)).flatten()[0])
    assert math.isfinite(value)


def test_ks_identical_distributions_not_significant():
    # identical samples -> KS p-value high (no drift)
    p_value = float(ks_metric.metric_loss(Y_TRUE, Y_TRUE))
    assert p_value > 0.05
