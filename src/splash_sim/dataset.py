"""串接模擬、固定比例切片及可重現資料集輸出。"""

from dataclasses import dataclass
from datetime import datetime
import csv
import json
from pathlib import Path

import numpy as np
import yaml

from splash_sim.augment import apply_augmentations
from splash_sim.config import ConfigError, default_config
from splash_sim.geometry import mm_to_px
from splash_sim.render import RenderedScene, render_stains
from splash_sim.scene import Scene, _drop, _sample_scene
from splash_sim.imageio import write_png


@dataclass
class SceneOutput:
    scene: Scene
    rendered: RenderedScene
    image: np.ndarray
    crops: dict[int, np.ndarray]
    truncated: dict[int, bool]


def _render_scene(scene, cfg, rng):
    rendered = render_stains([drop.stain for drop in scene.drops], cfg.render, rng)
    image = apply_augmentations(rendered.image, cfg.augment, rng)
    crops, truncated = {}, {}
    size = cfg.output.crop_size_px
    height, width = image.shape[:2]
    for drop in scene.drops:
        center = np.rint(mm_to_px(*drop.stain.center_mm)).astype(int)
        x0, y0 = center - size//2
        x1, y1 = x0+size, y0+size
        crop = np.empty((size, size, 3), dtype=np.uint8)
        crop[:] = cfg.render.paper_rgb
        sx0, sy0, sx1, sy1 = max(0, x0), max(0, y0), min(width, x1), min(height, y1)
        if sx1 > sx0 and sy1 > sy0:
            crop[sy0-y0:sy1-y0, sx0-x0:sx1-x0] = image[sy0:sy1, sx0:sx1]
        yy, xx = np.where(rendered.instance_mask == drop.drop_id+1)
        clipped = x0 < 0 or y0 < 0 or x1 > width or y1 > height
        outside = len(xx) > 0 and (xx.min() < x0 or xx.max() >= x1 or yy.min() < y0 or yy.max() >= y1)
        crops[drop.drop_id] = crop
        truncated[drop.drop_id] = bool(clipped or outside)
    return SceneOutput(scene, rendered, image, crops, truncated)


def simulate_single_drop(velocity_m_s, diameter_mm: float, cfg=None, seed: int = 0, *, center_mm=(105., 148.5)) -> SceneOutput:
    cfg = cfg or default_config()
    rng = np.random.default_rng(seed)
    drop = _drop(cfg, rng, 0, center_mm, np.asarray(velocity_m_s, dtype=float), diameter_mm)
    scene = Scene(0, (seed, 0), "single", None, [drop], {"off_paper": 0, "too_shallow": 0})
    return _render_scene(scene, cfg, rng)


def simulate_scene(cfg, index: int = 0) -> SceneOutput:
    rng = np.random.default_rng([cfg.seed, index])
    return _render_scene(_sample_scene(cfg, index, rng), cfg, rng)


def _rounded(value):
    if isinstance(value, dict):
        return {key: _rounded(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, np.ndarray)):
        return [_rounded(item) for item in value]
    if isinstance(value, (float, np.floating)):
        return round(float(value), 6)
    if isinstance(value, np.integer):
        return int(value)
    return value


def _write_json(path, value):
    path.write_text(json.dumps(_rounded(value), sort_keys=True, ensure_ascii=False, indent=2), encoding="utf-8")


def _label_drop(drop, output, scene_name):
    stain = drop.stain
    yy, xx = np.where(output.rendered.instance_mask == drop.drop_id+1)
    bbox = [int(xx.min()), int(yy.min()), int(xx.max()+1), int(yy.max()+1)] if len(xx) else [0, 0, 0, 0]
    return _rounded({
        "drop_id": drop.drop_id, "instance_id": drop.drop_id+1,
        "center_mm": stain.center_mm, "impact_velocity_m_s": drop.impact_velocity_m_s,
        "launch_velocity_m_s": drop.launch_velocity_m_s,
        **{key: getattr(stain, key) for key in ("speed_m_s", "impact_angle_deg", "direction_deg", "diameter_mm",
                                                "weber", "reynolds", "spread_factor", "width_mm", "length_mm", "tail_length_mm")},
        "spine_count": len(stain.spines), "satellite_count": len(stain.satellites),
        "bbox_px": bbox, "crop_file": f"crops/{scene_name}_d{drop.drop_id:03d}.png",
        "truncated": output.truncated[drop.drop_id],
    })


def _csv_row(index, label):
    row = {"scene_index": index}
    for key, value in label.items():
        if key in ("center_mm", "impact_velocity_m_s", "launch_velocity_m_s", "bbox_px"):
            components = ("x0", "y0", "x1", "y1") if key == "bbox_px" else (("x", "y") if key == "center_mm" else ("x", "y", "z"))
            for i, component in enumerate(components):
                row[f"{key}_{component}"] = value[i] if value is not None else None
        else:
            row[key] = value
    return row


def generate_dataset(cfg, out_dir: Path, *, n_scenes=None, name=None, folder_suffix=None) -> Path:
    from splash_sim import __version__

    count = cfg.output.n_scenes if n_scenes is None else n_scenes
    if type(count) is not int or count < 1:
        raise ConfigError("output.n_scenes 必須是大於或等於 1 的整數")
    dataset_name = cfg.output.name if name is None else name
    suffix = datetime.now().strftime('%Y%m%d-%H%M%S') if folder_suffix is None else folder_suffix
    for field, value in (("output.name", dataset_name), ("folder_suffix", suffix)):
        if not isinstance(value, str) or not value.strip() or value in (".", "..") or any(c in value for c in '/\\:*?"<>|\x00') or value.endswith((".", " ")):
            raise ConfigError(f"{field} 必須是單一資料夾名稱，不可含路徑或特殊字元")
    root = Path(out_dir) / f"{dataset_name}_{suffix}"
    root.mkdir(parents=True, exist_ok=False)
    for directory in ("scenes", "masks", "satellite_masks", "labels", "crops"):
        (root / directory).mkdir()
    (root / "config_snapshot.yaml").write_text(yaml.safe_dump(cfg.model_dump(mode="json"), allow_unicode=True, sort_keys=True), encoding="utf-8")
    _write_json(root / "meta.json", {"splash_sim_version": __version__, "n_scenes": count,
                                     "assumptions": ["球形液滴", "飛行不分裂、不蒸發、不互撞", "暈染僅為影像效果"]})
    rows = []
    for index in range(count):
        output = simulate_scene(cfg, index)
        scene_name = f"scene_{index+1:05d}"
        write_png(root / "scenes" / f"{scene_name}.png", output.image)
        write_png(root / "masks" / f"{scene_name}.png", output.rendered.instance_mask)
        write_png(root / "satellite_masks" / f"{scene_name}.png", output.rendered.satellite_mask)
        drops = [_label_drop(drop, output, scene_name) for drop in output.scene.drops]
        for drop in drops:
            write_png(root / drop["crop_file"], output.crops[drop["drop_id"]])
            rows.append(_csv_row(index, drop))
        _write_json(root / "labels" / f"{scene_name}.json", {
            "scene_index": index, "mode": output.scene.mode, "seed_seq": output.scene.seed_seq,
            "source_mm": None if output.scene.source_m is None else output.scene.source_m*1000,
            "discarded": output.scene.discarded, "ruleset": cfg.impact.ruleset,
            "splash_sim_version": __version__, "drops": drops,
        })
    with (root / "index.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return root
