"""速度評估：答案欄位只在評估時使用，不作模型輸入。"""

import numpy as np


def speed_metrics(y_true, q10, q50, q90, impact_angle_deg) -> dict:
    """計算整體與答案分組指標；無有限點估計的列仍計入總數。"""
    y, pred, angle = (np.asarray(values, dtype=float)
                      for values in (y_true, q50, impact_angle_deg))
    valid = np.isfinite(pred)

    def errors(mask):
        usable = mask & valid
        if not usable.any():
            return {"n": int(mask.sum()), "mae_m_s": None, "median_rel_err": None}
        error = np.abs(pred[usable] - y[usable])
        return {"n": int(mask.sum()), "mae_m_s": round(float(error.mean()), 6),
                "median_rel_err": round(float(np.median(error / y[usable])), 6)}

    result = errors(np.ones(y.shape, dtype=bool))
    result["n_nan"] = int((~valid).sum())
    low, high = np.asarray(q10), np.asarray(q90)
    result["coverage_80"] = (round(float(np.mean(
        (low[valid] <= y[valid]) & (y[valid] <= high[valid]))), 6)
        if q10 is not None and q90 is not None and valid.any() else None)
    result["groups"] = {name: errors(mask) for name, mask in {
        "vertical": angle >= 75, "oblique": angle < 75,
        "speed_low": (y >= 0) & (y < 2.5),
        "speed_mid": (y >= 2.5) & (y < 4), "speed_high": y >= 4,
    }.items()}
    return result
