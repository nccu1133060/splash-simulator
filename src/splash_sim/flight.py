"""球形液滴在重力與空氣阻力下的飛行，內部單位為 SI。"""

from dataclasses import dataclass

import numpy as np
from scipy.integrate import solve_ivp

from splash_sim.config import AirConfig, LiquidConfig

GRAVITY_M_S2 = 9.81


@dataclass(frozen=True)
class FlightResult:
    impact_position_m: np.ndarray
    impact_velocity_m_s: np.ndarray
    flight_time_s: float


def drag_coefficient(reynolds: float) -> float:
    """依核可設計 §5.1 的 Schiller–Naumann 球體關係式計算阻力係數。"""
    if reynolds <= 0:
        raise ValueError("reynolds 必須大於 0")
    if reynolds < 1000:
        return 24 / reynolds * (1 + 0.15 * reynolds**0.687)
    return 0.44


def _acceleration(velocity_m_s, diameter_m, liquid, air):
    """由球體質量與迎風面積化簡設計 §5.1 的重力及阻力方程。"""
    acceleration = np.array([0.0, 0.0, -GRAVITY_M_S2])
    speed = np.linalg.norm(velocity_m_s)
    if air.drag_enabled and speed > 0:
        reynolds = air.density_kg_m3 * speed * diameter_m / air.viscosity_pa_s
        factor = 3 * air.density_kg_m3 * drag_coefficient(reynolds) / (4 * liquid.density_kg_m3 * diameter_m)
        acceleration -= factor * speed * velocity_m_s
    return acceleration


def _motion(diameter_m, liquid, air):
    def derivative(time_s, state):
        return np.concatenate((state[3:], _acceleration(state[3:], diameter_m, liquid, air)))

    return derivative


def fly_to_plane(
    position_m,
    velocity_m_s,
    diameter_m: float,
    liquid: LiquidConfig,
    air: AirConfig,
    *,
    max_time_s: float = 5.0,
) -> FlightResult:
    """向前積分至水平紙面 z=0，傳回撞擊狀態與經過時間。"""
    if position_m[2] <= 0:
        raise ValueError("position_m 的 z 必須大於 0，起點須在紙面上方")

    def hit_plane(time_s, state):
        return state[2]

    hit_plane.terminal = True
    hit_plane.direction = -1
    solution = solve_ivp(
        _motion(diameter_m, liquid, air),
        (0.0, max_time_s),
        np.concatenate((position_m, velocity_m_s)),
        events=hit_plane,
        rtol=1e-10,
        atol=1e-12,
    )
    if len(solution.t_events[0]) == 0:
        raise ValueError("max_time_s 內未落到紙面，請增加最長飛行時間或檢查發射條件")
    state = solution.y_events[0][0]
    return FlightResult(state[:3].copy(), state[3:].copy(), float(solution.t_events[0][0]))


def propagate(
    position_m,
    velocity_m_s,
    diameter_m: float,
    liquid: LiquidConfig,
    air: AirConfig,
    duration_s: float,
) -> tuple[np.ndarray, np.ndarray]:
    """積分固定時長；負 duration_s 使用同一運動方程往回推。"""
    solution = solve_ivp(
        _motion(diameter_m, liquid, air),
        (0.0, duration_s),
        np.concatenate((position_m, velocity_m_s)),
        rtol=1e-10,
        atol=1e-12,
    )
    state = solution.y[:, -1]
    return state[:3].copy(), state[3:].copy()
