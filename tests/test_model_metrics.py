import json

import numpy as np


def test_speed_metrics_hand_computed():
    from splash_model.metrics import speed_metrics

    result = speed_metrics([2, 2.5, 4, 5], [1, 2, 3, 4],
                           [1, 3, np.nan, 7], [2, 3, 5, 6], [75, 60, 90, 30])
    assert result == {
        "n": 4, "n_nan": 1, "mae_m_s": 1.166667,
        "median_rel_err": 0.4, "coverage_80": 1.0,
        "groups": {
            "vertical": {"n": 2, "mae_m_s": 1.0, "median_rel_err": 0.5},
            "oblique": {"n": 2, "mae_m_s": 1.25, "median_rel_err": 0.3},
            "speed_low": {"n": 1, "mae_m_s": 1.0, "median_rel_err": 0.5},
            "speed_mid": {"n": 1, "mae_m_s": 0.5, "median_rel_err": 0.2},
            "speed_high": {"n": 2, "mae_m_s": 2.0, "median_rel_err": 0.4},
        },
    }
    json.dumps(result, allow_nan=False)


def test_speed_metrics_without_interval():
    from splash_model.metrics import speed_metrics

    result = speed_metrics([2, 4], None, [2, np.inf], None, [90, 30])
    assert result["coverage_80"] is None
    assert result["n_nan"] == 1
    assert result["mae_m_s"] == 0.0
    assert result["groups"]["speed_high"] == {
        "n": 1, "mae_m_s": None, "median_rel_err": None}
    for y, pred, angles in [([], [], []), ([2], [np.nan], [90])]:
        empty = speed_metrics(y, None, pred, None, angles)
        assert empty["mae_m_s"] is None
        assert empty["median_rel_err"] is None
        assert empty["coverage_80"] is None
        json.dumps(empty, allow_nan=False)
