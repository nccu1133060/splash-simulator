"""匯出 YOLO 分割多邊形；衛星小滴不列入主體訓練標註。"""

import json
from pathlib import Path
import shutil

import cv2
import numpy as np
import yaml

from splash_sim.config import ConfigError
from splash_sim.imageio import read_png


def _instance_polygon(mask):
    # RETR_LIST 保留分離區塊及孔洞；OpenCV 已保留外圈／內圈相反方向。
    contours, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    parts = [cv2.approxPolyDP(contour, 1., True)[:, 0, :].astype(float) for contour in contours]
    parts = [part for part in parts if len(part) >= 3]
    if not parts:
        return None
    polygon = parts.pop(0)
    for part in parts:
        # 最短連線往返同一路徑，不把中間空白區填成染料，也不丟掉小區塊。
        distances = ((polygon[:, None, :] - part[None, :, :])**2).sum(axis=2)
        i, j = np.unravel_index(np.argmin(distances), distances.shape)
        polygon = np.concatenate((polygon[:i+1], part[j:], part[:j+1], polygon[i:]))
    return polygon


def export_yolo(dataset_dir: Path) -> Path:
    dataset_dir = Path(dataset_dir)
    label_paths = sorted((dataset_dir / "labels").glob("scene_*.json"))
    if not label_paths:
        raise ConfigError("dataset 找不到 labels/scene_*.json；請指定已產生的資料集")
    root = dataset_dir / "yolo"
    root.mkdir(exist_ok=False)
    (root / "labels").mkdir()
    (root / "images").mkdir()
    for path in label_paths:
        label = json.loads(path.read_text(encoding="utf-8"))
        mask = read_png(dataset_dir / "masks" / (path.stem + ".png"))
        height, width = mask.shape
        lines = []
        for drop in label["drops"]:
            polygon = _instance_polygon(mask == drop["instance_id"])
            if polygon is None:
                continue  # 完全被遮蔽的液滴沒有可見多邊形，不捏造標註。
            polygon /= [width, height]
            lines.append("0 " + " ".join(f"{value:.8f}" for value in polygon.flat))
        (root / "labels" / (path.stem + ".txt")).write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        shutil.copyfile(dataset_dir / "scenes" / (path.stem + ".png"), root / "images" / (path.stem + ".png"))
    # path 留空使載入器採 YAML 所在目錄，不把絕對路徑寫進可重現產物。
    (root / "data.yaml").write_text(yaml.safe_dump({"path": None, "train": "images", "names": {0: "stain"}}, sort_keys=True), encoding="utf-8")
    return root
