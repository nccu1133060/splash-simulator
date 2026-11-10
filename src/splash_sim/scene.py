"""依設計 §5.2 取樣液滴與源頭；每個場景獨立衍生亂數。"""

from dataclasses import dataclass

import numpy as np

from splash_sim.flight import fly_to_plane
from splash_sim.geometry import on_paper
from splash_sim.impact import StainGeometry, compute_stain


@dataclass
class Drop:
    drop_id: int
    diameter_mm: float
    launch_velocity_m_s: np.ndarray | None
    impact_velocity_m_s: np.ndarray
    stain: StainGeometry


@dataclass
class Scene:
    index: int
    seed_seq: tuple[int, int]
    mode: str
    source_m: np.ndarray | None
    drops: list[Drop]
    discarded: dict[str, int]


class SceneSamplingError(RuntimeError):
    """重抽次數內無法取得足夠有效液滴。"""


def _diameter(cfg, rng):
    if cfg.mode == "fixed":
        return cfg.fixed_mm
    return float(np.exp(rng.uniform(*np.log(cfg.range_mm))))


def _drop(cfg, rng, index, center, velocity, diameter, launch=None):
    stain = compute_stain(center, velocity, diameter, cfg.liquid, cfg.impact, rng)
    return Drop(index, diameter, launch, velocity, stain)


def _sample_scene(cfg, index, rng):
    if cfg.scene.mode == "single":
        speed = rng.uniform(*cfg.scene.single.speed_m_s)
        alpha = np.radians(rng.uniform(*cfg.scene.single.impact_angle_deg))
        direction = rng.uniform(0, 2*np.pi)
        velocity = speed*np.array([np.cos(alpha)*np.cos(direction), np.cos(alpha)*np.sin(direction), -np.sin(alpha)])
        drop = _drop(cfg, rng, 0, (105., 148.5), velocity, _diameter(cfg.scene.diameter, rng))
        return Scene(index, (cfg.seed, index), "single", None, [drop], {"off_paper": 0, "too_shallow": 0})
    if cfg.scene.mode == "vertical_drop":
        settings = cfg.scene.vertical_drop
        height = settings.heights_m[index % len(settings.heights_m)]
        drops = []
        for x in np.linspace(0, 210, settings.grid[0]+2)[1:-1]:
            for y in np.linspace(0, 297, settings.grid[1]+2)[1:-1]:
                diameter = _diameter(cfg.scene.diameter, rng)
                hit = fly_to_plane([x/1000, y/1000, height], [0, 0, 0], diameter/1000, cfg.liquid, cfg.air)
                drops.append(_drop(cfg, rng, len(drops), (float(x), float(y)), hit.impact_velocity_m_s,
                                   diameter, np.zeros(3)))
        return Scene(index, (cfg.seed, index), "vertical_drop", None, drops, {"off_paper": 0, "too_shallow": 0})
    spray = cfg.scene.spray
    for _ in range(spray.max_resample):
        source = np.array([*rng.uniform(np.array([0.105, 0.1485])-spray.source_offset_m,
                                       np.array([0.105, 0.1485])+spray.source_offset_m),
                           rng.uniform(*spray.source_height_m)])
        axis = np.array([0.105, 0.1485, 0.]) - source
        axis /= np.linalg.norm(axis)
        perpendicular = np.cross(axis, [0., 1., 0.])
        perpendicular /= np.linalg.norm(perpendicular)
        other = np.cross(axis, perpendicular)
        drops = []
        discarded = {"off_paper": 0, "too_shallow": 0}
        for _ in range(int(rng.integers(spray.drops_launched[0], spray.drops_launched[1]+1))):
            cosine = rng.uniform(np.cos(np.radians(spray.cone_half_angle_deg)), 1)
            phi = rng.uniform(0, 2*np.pi)
            direction = cosine*axis + np.sqrt(1-cosine**2)*(np.cos(phi)*perpendicular+np.sin(phi)*other)
            launch = direction * rng.uniform(*spray.launch_speed_m_s)
            diameter = _diameter(cfg.scene.diameter, rng)
            hit = fly_to_plane(source, launch, diameter/1000, cfg.liquid, cfg.air)
            center = tuple(hit.impact_position_m[:2]*1000)
            if not on_paper(*center):
                discarded["off_paper"] += 1
                continue
            alpha = np.degrees(np.arctan2(abs(hit.impact_velocity_m_s[2]), np.linalg.norm(hit.impact_velocity_m_s[:2])))
            if alpha < spray.min_impact_angle_deg:
                discarded["too_shallow"] += 1
                continue
            drops.append(_drop(cfg, rng, len(drops), center, hit.impact_velocity_m_s, diameter, launch.copy()))
        if len(drops) >= spray.min_drops_on_paper:
            return Scene(index, (cfg.seed, index), "spray", source, drops, discarded)
    raise SceneSamplingError("scene.spray.max_resample 次數內有效液滴不足；請減少 source_offset_m、調整發射速度或增加 max_resample")


def sample_scene(cfg, index: int) -> Scene:
    return _sample_scene(cfg, index, np.random.default_rng([cfg.seed, index]))
