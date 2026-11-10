"""依設計 §5.4 將毫米幾何繪製為 RGB 圖與編號遮罩。"""

from dataclasses import dataclass

import cv2
import numpy as np

from splash_sim.geometry import CANVAS_SHAPE, mm_to_px


@dataclass
class RenderedScene:
    image: np.ndarray
    instance_mask: np.ndarray
    satellite_mask: np.ndarray


def _polygons(stain, cfg):
    theta = np.linspace(0, 2*np.pi, 128, endpoint=False)
    local = np.column_stack((stain.length_mm/2*np.cos(theta), stain.width_mm/2*np.sin(theta)))
    angle = np.radians(stain.direction_deg)
    rotation = np.array([[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]])
    polygons = [local]
    if cfg.draw_tail and stain.tail_length_mm > 0:
        tip = stain.length_mm/2 + stain.tail_length_mm
        polygons.append(np.array([[stain.length_mm*0.4, -stain.width_mm*0.12],
                                  [tip, 0], [stain.length_mm*0.4, stain.width_mm*0.12]]))
    if cfg.draw_spines:
        for spine in stain.spines:
            phi = np.radians(spine.angle_deg)
            unit = np.array([np.cos(phi), np.sin(phi)])
            normal = np.array([-unit[1], unit[0]])
            radius = 1 / np.sqrt((unit[0]/(stain.length_mm/2))**2 + (unit[1]/(stain.width_mm/2))**2)
            base = unit * (radius - 0.05)
            polygons.append(np.array([base-normal*spine.width_mm/2,
                                      unit*(radius+spine.length_mm), base+normal*spine.width_mm/2]))
    return [poly @ rotation.T + stain.center_mm for poly in polygons]


def render_stains(stains, cfg, rng) -> RenderedScene:
    image = np.empty((*CANVAS_SHAPE, 3), dtype=np.uint8)
    image[:] = cfg.paper_rgb
    instance = np.zeros(CANVAS_SHAPE, dtype=np.uint16)
    satellite = np.zeros_like(instance)
    for index, stain in enumerate(stains, 1):
        polygons = [np.rint(np.column_stack(mm_to_px(poly[:, 0], poly[:, 1]))).astype(np.int32)
                    for poly in _polygons(stain, cfg)]
        satellite_polygons = []
        if cfg.draw_satellites:
            theta = np.linspace(0, 2*np.pi, 32, endpoint=False)
            for drop in stain.satellites:
                center = np.asarray(stain.center_mm) + drop.offset_mm
                poly = center + drop.diameter_mm/2*np.column_stack((np.cos(theta), np.sin(theta)))
                satellite_polygons.append(np.rint(np.column_stack(mm_to_px(poly[:, 0], poly[:, 1]))).astype(np.int32))
        all_points = np.concatenate(polygons + satellite_polygons)
        sigma = stain.bleed_mm * 10
        padding = int(np.ceil(sigma*4))+1
        x0, y0 = np.maximum(all_points.min(axis=0)-padding, 0)
        x1, y1 = np.minimum(all_points.max(axis=0)+padding+1, CANVAS_SHAPE[::-1])
        if x1 <= x0 or y1 <= y0:
            continue
        mask = np.zeros((y1-y0, x1-x0), dtype=np.uint8)
        for polygon in polygons:
            cv2.fillPoly(mask, [polygon - [x0, y0]], 1)
        instance[y0:y1, x0:x1][mask != 0] = index
        sat_mask = np.zeros_like(mask)
        for polygon in satellite_polygons:
            cv2.fillPoly(sat_mask, [polygon - [x0, y0]], 1)
        satellite[y0:y1, x0:x1][sat_mask != 0] = index
        opacity = rng.uniform(*cfg.dye_opacity)
        # 設計 §5.3：暈染為待實拍校正的影像效果，不改真值遮罩。
        alpha = np.maximum(mask, sat_mask).astype(np.float32)
        if sigma > 0:
            alpha = cv2.GaussianBlur(alpha, (0, 0), sigma, borderType=cv2.BORDER_CONSTANT)
        alpha = (alpha*opacity)[..., None]
        region = image[y0:y1, x0:x1]
        region[:] = np.rint(region*(1-alpha) + np.asarray(cfg.dye_rgb)*alpha).astype(np.uint8)
    return RenderedScene(image, instance, satellite)
