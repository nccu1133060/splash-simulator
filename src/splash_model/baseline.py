"""由量測特徵估速的物理及常數基準線。"""

import numpy as np
from scipy.optimize import brentq


def laan_spread_factor(normal_speed_m_s: float, diameter_mm: float,
                       liquid, spread_a: float) -> float:
    """沿用 impact.literature_v1 的 Laan et al. 2014 內插式，不含擾動。

    與模擬器相同：原文與紙張吸水適用性仍待校正。
    """
    diameter_m = diameter_mm / 1000
    weber = liquid.density_kg_m3 * normal_speed_m_s**2 * diameter_m / liquid.surface_tension_n_m
    reynolds = liquid.density_kg_m3 * normal_speed_m_s * diameter_m / liquid.viscosity_pa_s
    p = weber * reynolds**(-0.4)
    return float(reynolds**0.2 * np.sqrt(p) / (spread_a + np.sqrt(p)))


def invert_normal_speed(spread_factor: float, diameter_mm: float, liquid,
                        spread_a: float, *, bounds_m_s=(0.01, 30.0)) -> float:
    """在指定速度範圍反解法向速度，單位 m/s。"""
    values = (spread_factor, diameter_mm, spread_a, liquid.density_kg_m3,
              liquid.surface_tension_n_m, liquid.viscosity_pa_s, *bounds_m_s)
    if not all(np.isfinite(value) and value > 0 for value in values):
        return float("nan")
    if bounds_m_s[0] >= bounds_m_s[1]:
        return float("nan")
    try:
        return float(brentq(lambda speed: laan_spread_factor(
            speed, diameter_mm, liquid, spread_a) - spread_factor, *bounds_m_s))
    except (ValueError, RuntimeError, OverflowError):
        return float("nan")


def physics_baseline(df, *, diameter_mm: float, liquid, spread_a: float) -> np.ndarray:
    """B0：量測寬度反解法向速度，再依橢圓 W/L=sin α 換算速度。

    角度關係來源與 literature_v1 相同；僅讀兩個 meas_ 欄位。
    """
    result = np.full(len(df), np.nan)
    if not np.isfinite(diameter_mm) or diameter_mm <= 0:
        return result
    for index, (width, aspect) in enumerate(zip(df["meas_width_mm"], df["meas_aspect_ratio"])):
        if not (np.isfinite(width) and width > 0 and np.isfinite(aspect) and aspect > 0):
            continue
        normal = invert_normal_speed(width / diameter_mm, diameter_mm, liquid, spread_a)
        result[index] = normal / np.clip(aspect, 0, 1)
    return result


def constant_baseline(train_speeds):
    """B1：固定猜訓練速度的平均，不讀預測資料的答案。"""
    mean_speed = float(np.mean(train_speeds))
    return lambda df: np.full(len(df), mean_speed)
