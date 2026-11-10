"""從實際遮罩量測水漬，不直接讀取生成答案。"""

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(frozen=True)
class StainFeatures:
    area_mm2: float
    width_mm: float
    length_mm: float
    aspect_ratio: float
    direction_deg: float
    spine_count: int


def measure_stain(mask) -> StainFeatures:
    contours, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not contours:
        raise ValueError("mask 沒有可量測的水漬")
    contour = max(contours, key=cv2.contourArea)
    if len(contour) < 5:
        raise ValueError("mask 輪廓不足 5 點，無法擬合橢圓")
    center, axes, angle = cv2.fitEllipse(contour)
    width, length = sorted(axes)
    major_angle = angle + (90 if axes[0] < axes[1] else 0)
    points = contour[:, 0, :].astype(float) - center
    radians = np.radians(angle)
    along = points[:, 0]*np.cos(radians) + points[:, 1]*np.sin(radians)
    across = -points[:, 0]*np.sin(radians) + points[:, 1]*np.cos(radians)
    # 徑向超出擬合橢圓 12% 的連續區段，依設計 Task 3；非實拍校正值。
    excess = np.sqrt((along/(axes[0]/2))**2 + (across/(axes[1]/2))**2) > 1.12
    spine_count = int(np.count_nonzero(excess & ~np.roll(excess, 1)))
    return StainFeatures(float(np.count_nonzero(mask))/100, width/10, length/10,
                         width/length, float(-major_angle % 180), spine_count)
