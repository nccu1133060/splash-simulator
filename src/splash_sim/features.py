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
    perimeter_mm: float
    solidity: float
    roughness: float


def measure_body(mask, *, kernel_frac: float = 0.25) -> StainFeatures:
    """依 Task M1 核可規則以 25% 寬的開運算削去毛刺；非文獻校正值。"""
    outer = measure_stain(mask)
    diameter = max(3, round(kernel_frac * outer.width_mm * 10))
    diameter += 1 - diameter % 2
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (diameter, diameter))
    opened = cv2.morphologyEx(mask.astype(np.uint8), cv2.MORPH_OPEN, kernel)
    return measure_stain(opened)


def measure_stain(mask) -> StainFeatures:
    contours, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not contours:
        raise ValueError("mask 沒有可量測的水漬")
    contour = max(contours, key=cv2.contourArea)
    if len(contour) < 5:
        raise ValueError("mask 輪廓不足 5 點，無法擬合橢圓")
    # Task M1 核可的 1 px 拉直輪廓；退化細線不可作面積比值。
    shape_contour = cv2.approxPolyDP(contour, 1.0, True)
    shape_area = cv2.contourArea(shape_contour)
    hull_area = cv2.contourArea(cv2.convexHull(shape_contour))
    if cv2.contourArea(contour) <= 0 or shape_area <= 0 or hull_area <= 0:
        raise ValueError("mask 輪廓或凸包面積為零，無法量測水漬")
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
    # Task M1 2026-11-18 核可：僅新增形狀特徵拉直 1 px 階梯，非實拍校正。
    perimeter = cv2.arcLength(shape_contour, True)
    solidity = shape_area / hull_area
    # Ramanujan 第二近似式：以擬合橢圓半軸估算周長。
    a, b = length / 2, width / 2
    h = ((a-b)/(a+b))**2
    ellipse_perimeter = np.pi*(a+b)*(1+3*h/(10+np.sqrt(4-3*h)))
    return StainFeatures(float(np.count_nonzero(mask))/100, width/10, length/10,
                         width/length, float(-major_angle % 180), spine_count,
                         perimeter/10, solidity, perimeter/ellipse_perimeter)
