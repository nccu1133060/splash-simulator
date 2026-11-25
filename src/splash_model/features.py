"""只由遮罩量測模型特徵，答案另存供評估使用。"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import ndimage

from splash_sim.features import measure_body, measure_stain
from splash_sim.geometry import PX_PER_MM, px_to_mm
from splash_sim.imageio import read_png


FEATURE_COLUMNS = (
    "meas_area_mm2", "meas_width_mm", "meas_length_mm", "meas_aspect_ratio",
    "meas_impact_angle_deg", "meas_outer_width_mm", "meas_outer_length_mm",
    "meas_spine_count", "meas_perimeter_mm",
    "meas_solidity", "meas_roughness", "meas_satellite_count",
    "meas_satellite_area_mm2", "meas_satellite_max_dist_mm",
)
OBSERVED_COLUMNS = ("obs_direction_deg", "obs_center_mm_x", "obs_center_mm_y")
KEY_COLUMNS = ("scene_index", "drop_id")
TARGET_COLUMN = "speed_m_s"
TRUTH_COLUMNS = (
    "impact_angle_deg", "direction_deg", "center_mm_x", "center_mm_y",
    "impact_velocity_m_s_x", "impact_velocity_m_s_y", "impact_velocity_m_s_z",
    "diameter_mm",
)


def measure_drop(instance_mask, satellite_mask, instance_id: int,
                 bbox_px: tuple[int, int, int, int], *, margin_px: int = 60,
                 satellite_slice: tuple[slice, slice] | None = None) -> dict[str, float]:
    """主體裁切量測；衛星使用整張同編號遮罩，距離以重心計。"""
    x0, y0, x1, y1 = bbox_px
    height, width = instance_mask.shape
    left, top = max(0, x0-margin_px), max(0, y0-margin_px)
    body = instance_mask[top:min(height, y1+margin_px), left:min(width, x1+margin_px)] == instance_id
    features = measure_stain(body)
    core = measure_body(body)
    yy, xx = np.nonzero(body)
    center_x, center_y = float(xx.mean()+left), float(yy.mean()+top)
    center_mm = px_to_mm(center_x, center_y)
    if satellite_slice is None:
        satellite_slice = (slice(0, height), slice(0, width))
    satellites = satellite_mask[satellite_slice] == instance_id
    labels, count = ndimage.label(satellites, structure=np.ones((3, 3)))
    max_distance = 0.0
    if count:
        indices = range(1, count+1)
        areas = ndimage.sum_labels(satellites, labels, indices)
        # 先加回全圖座標再求和／相除，保持舊版浮點結果逐值相同。
        sy, sx = satellite_slice
        ys, xs = np.indices(satellites.shape)
        centers = np.column_stack([
            ndimage.sum_labels(ys + sy.start, labels, indices) / areas,
            ndimage.sum_labels(xs + sx.start, labels, indices) / areas,
        ])
        max_distance = float(np.linalg.norm(centers - (center_y, center_x), axis=1).max()/PX_PER_MM)
    result = {f"meas_{field}": float(getattr(features, field)) for field in (
        "area_mm2", "width_mm", "length_mm", "aspect_ratio", "spine_count",
        "perimeter_mm", "solidity", "roughness",
    )}
    result.update(
        meas_width_mm=core.width_mm, meas_length_mm=core.length_mm,
        meas_aspect_ratio=core.aspect_ratio,
        meas_outer_width_mm=features.width_mm, meas_outer_length_mm=features.length_mm,
        meas_impact_angle_deg=float(np.degrees(np.arcsin(min(core.aspect_ratio, 1)))),
        meas_satellite_count=float(count),
        meas_satellite_area_mm2=float(np.count_nonzero(satellites)/PX_PER_MM**2),
        meas_satellite_max_dist_mm=max_distance,
        obs_direction_deg=core.direction_deg,
        obs_center_mm_x=center_mm[0], obs_center_mm_y=center_mm[1],
    )
    return result


def build_feature_table(dataset_dir: Path) -> pd.DataFrame:
    """由場景遮罩建表；答案僅保留為目標與比較欄位。"""
    dataset_dir = Path(dataset_dir)
    rows = []
    excluded = {"truncated": 0, "occluded": 0, "unmeasurable": 0}
    for path in sorted((dataset_dir / "labels").glob("*.json")):
        scene = json.loads(path.read_text(encoding="utf-8"))
        mask = read_png(dataset_dir / "masks" / f"{path.stem}.png")
        satellites = read_png(dataset_dir / "satellite_masks" / f"{path.stem}.png")
        boxes = ndimage.find_objects(mask)
        satellite_boxes = ndimage.find_objects(satellites)
        for drop in scene["drops"]:
            instance_id = drop["instance_id"]
            if drop["truncated"]:
                excluded["truncated"] += 1
                continue
            if instance_id > len(boxes) or boxes[instance_id-1] is None:
                excluded["occluded"] += 1
                continue
            try:
                satellite_box = (satellite_boxes[instance_id-1]
                                 if instance_id <= len(satellite_boxes) else None)
                measured = measure_drop(
                    mask, satellites, instance_id, tuple(drop["bbox_px"]),
                    satellite_slice=(satellite_box if satellite_box is not None
                                     else (slice(0, 0), slice(0, 0))),
                )
            except ValueError:
                excluded["unmeasurable"] += 1
                continue
            row = {"scene_index": scene["scene_index"], "drop_id": drop["drop_id"],
                   **measured, TARGET_COLUMN: drop[TARGET_COLUMN]}
            for field in ("impact_angle_deg", "direction_deg", "diameter_mm"):
                row[field] = drop[field]
            row.update({f"center_mm_{axis}": value
                        for axis, value in zip("xy", drop["center_mm"])})
            row.update({f"impact_velocity_m_s_{axis}": value
                        for axis, value in zip("xyz", drop["impact_velocity_m_s"])})
            rows.append(row)
    columns = KEY_COLUMNS + FEATURE_COLUMNS + OBSERVED_COLUMNS + (TARGET_COLUMN,) + TRUTH_COLUMNS
    table = pd.DataFrame(rows, columns=columns).sort_values(list(KEY_COLUMNS)).reset_index(drop=True)
    table.attrs["excluded"] = excluded
    return table


def assert_no_leakage(X: pd.DataFrame) -> None:
    """訓練前只准使用核可的遮罩量測欄位。"""
    invalid = [column for column in X.columns
               if not isinstance(column, str) or not column.startswith("meas_")
               or column not in FEATURE_COLUMNS]
    if invalid:
        raise ValueError(f"X 含不允許的模型輸入欄位：{', '.join(map(str, invalid))}")
