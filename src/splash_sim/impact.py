"""速度轉幾何；文獻經驗關係與待校正參數分開標示。"""

from dataclasses import dataclass
from typing import Callable

import numpy as np

from splash_sim.config import ConfigError, ImpactConfig, LiquidConfig


@dataclass(frozen=True)
class Spine:
    angle_deg: float
    length_mm: float
    width_mm: float


@dataclass(frozen=True)
class Satellite:
    offset_mm: tuple[float, float]
    diameter_mm: float


@dataclass(frozen=True)
class StainGeometry:
    center_mm: tuple[float, float]
    width_mm: float
    length_mm: float
    direction_deg: float
    impact_angle_deg: float
    spines: tuple[Spine, ...]
    satellites: tuple[Satellite, ...]
    tail_length_mm: float
    bleed_mm: float
    diameter_mm: float
    speed_m_s: float
    weber: float
    reynolds: float
    spread_factor: float
    ruleset: str


RuleFn = Callable[[tuple[float, float], np.ndarray, float, LiquidConfig, ImpactConfig,
                   np.random.Generator], StainGeometry]


def literature_v1(center_mm, velocity_m_s, diameter_mm, liquid, impact, rng):
    """We、Re：標準定義（已有文獻），採法向速度及 SI 直徑。"""
    normal = abs(velocity_m_s[2])
    diameter_m = diameter_mm / 1000
    weber = liquid.density_kg_m3 * normal**2 * diameter_m / liquid.surface_tension_n_m
    reynolds = liquid.density_kg_m3 * normal * diameter_m / liquid.viscosity_pa_s
    # Laan et al. 2014 內插式；待核對原文，並非紙張吸水模型。
    p = weber * reynolds**(-0.4)
    spread = reynolds**0.2 * np.sqrt(p) / (impact.spread_a + np.sqrt(p))
    # 設計 §5.3 隨機擾動，待實拍校正；共用尺度保留 W/L 的角度關係。
    width = float(spread * diameter_mm * (1 + rng.uniform(-impact.jitter_frac, impact.jitter_frac)))
    # 經典橢圓 W/L=sin(alpha)：已有文獻；方向為紙面幾何。
    tangent = np.linalg.norm(velocity_m_s[:2])
    alpha = np.arctan2(normal, tangent)
    direction = float(np.degrees(np.arctan2(velocity_m_s[1], velocity_m_s[0])) % 360) if tangent else 0.0
    # Joris 2017 的系統偏差方向；偏差值待實拍校正，預設關閉。
    length = float(width / np.sin(alpha + np.radians(impact.angle_bias_deg)))
    # Bhola & Chandra 1999／Mehdizadeh 2004 冪次形式，係數待核對原文。
    count = round(impact.spine_a * weber**impact.spine_b * reynolds**impact.spine_c) if weber >= impact.spine_min_weber else 0
    # 斜撞前緣集中：專題統整第十一節定性關係；分布參數待實拍校正。
    kappa = impact.spine_front_kappa * np.cos(alpha) / max(np.sin(alpha), 0.1)
    angles = rng.vonmises(0, kappa, count)
    spines = tuple(Spine(float(np.degrees(angle)), float(width * rng.uniform(*impact.spine_length_frac)),
                         width * 0.03) for angle in angles)
    # 尾巴／衛星為定性近似：設計 §5.3，待實拍校正。
    tail = float(impact.tail_coeff * width * np.cos(alpha))
    satellite_count = min(impact.satellite_max, max(0, int(np.floor(impact.satellite_per_weber * (weber - impact.satellite_min_weber)))))
    satellites = []
    for _ in range(satellite_count):
        angle = np.radians(direction) + rng.uniform(-np.pi/2, np.pi/2)
        distance = rng.uniform(length/2, length)
        satellites.append(Satellite((float(distance*np.cos(angle)), float(distance*np.sin(angle))),
                                    float(width*rng.uniform(*impact.satellite_size_frac))))
    return StainGeometry(tuple(center_mm), width, length, direction, float(np.degrees(alpha)), spines, tuple(satellites), tail,
                         impact.bleed_mm[impact.paper], diameter_mm,
                         float(np.linalg.norm(velocity_m_s)), weber, reynolds, float(spread), impact.ruleset)


_RULESETS: dict[str, RuleFn] = {"literature_v1": literature_v1}


def register_ruleset(name: str, fn: RuleFn) -> None:
    _RULESETS[name] = fn


def get_ruleset(name: str) -> RuleFn:
    if name not in _RULESETS:
        raise ConfigError(f"impact.ruleset 不認得 {name}；可用規則：{', '.join(sorted(_RULESETS))}")
    return _RULESETS[name]


def compute_stain(center_mm, velocity_m_s, diameter_mm, liquid, impact, rng):
    return get_ruleset(impact.ruleset)(center_mm, velocity_m_s, diameter_mm, liquid, impact, rng)
