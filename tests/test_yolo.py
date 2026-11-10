import json

import cv2
import numpy as np
import yaml


def test_export_polygons_normalized(tmp_path):
    from splash_sim.config import SimConfig
    from splash_sim.dataset import generate_dataset
    from splash_sim.imageio import read_png
    from splash_sim.yolo import export_yolo
    cfg = SimConfig(scene={"mode": "vertical_drop"}, impact={"spine_a": 0., "satellite_max": 0, "tail_coeff": 0.})
    root = generate_dataset(cfg, tmp_path, n_scenes=1, folder_suffix="yolo")
    yolo = export_yolo(root)
    lines = (yolo / "labels" / "scene_00001.txt").read_text(encoding="utf-8").splitlines()
    drops = json.loads((root / "labels" / "scene_00001.json").read_text(encoding="utf-8"))["drops"]
    mask = read_png(root / "masks" / "scene_00001.png")
    assert len(lines) == len(drops)
    for line, drop in zip(lines, drops):
        values = np.array([float(v) for v in line.split()])
        assert values[0] == 0
        points = values[1:].reshape(-1, 2)
        assert len(points) >= 3
        assert np.all((points >= 0) & (points <= 1))
        restored = np.zeros(mask.shape, dtype=np.uint8)
        cv2.fillPoly(restored, [np.rint(points*[2100, 2970]).astype(np.int32)], 1)
        target = mask == drop["instance_id"]
        assert np.count_nonzero((restored > 0) & target) / np.count_nonzero((restored > 0) | target) >= 0.9
    assert yaml.safe_load((yolo / "data.yaml").read_text(encoding="utf-8"))["names"] == {0: "stain"}


def test_export_preserves_disconnected_visible_parts(tmp_path):
    from dataclasses import replace
    from test_render import geometry
    from splash_sim.config import RenderConfig
    from splash_sim.render import render_stains
    from splash_sim.imageio import write_png
    from splash_sim.yolo import export_yolo
    a = geometry()
    b = replace(a, width_mm=2., length_mm=20., direction_deg=90.)
    rendered = render_stains([a, b], RenderConfig(), np.random.default_rng(0))
    (tmp_path / "labels").mkdir()
    (tmp_path / "labels" / "scene_00001.json").write_text(json.dumps({"drops": [{"instance_id": 1}, {"instance_id": 2}]}), encoding="utf-8")
    write_png(tmp_path / "masks" / "scene_00001.png", rendered.instance_mask)
    write_png(tmp_path / "scenes" / "scene_00001.png", rendered.image)
    root = export_yolo(tmp_path)
    line = (root / "labels" / "scene_00001.txt").read_text(encoding="utf-8").splitlines()[0]
    points = np.array([float(v) for v in line.split()[1:]]).reshape(-1, 2)
    restored = np.zeros(rendered.instance_mask.shape, dtype=np.uint8)
    cv2.fillPoly(restored, [np.rint(points*[2100, 2970]).astype(np.int32)], 1)
    target = rendered.instance_mask == 1
    iou = np.count_nonzero((restored > 0) & target) / np.count_nonzero((restored > 0) | target)
    assert iou >= 0.9


def test_export_preserves_holes():
    from splash_sim.yolo import _instance_polygon
    mask = np.zeros((200, 200), dtype=np.uint8)
    cv2.circle(mask, (100, 100), 80, 1, -1)
    cv2.circle(mask, (100, 100), 45, 0, -1)
    polygon = _instance_polygon(mask)
    restored = np.zeros_like(mask)
    cv2.fillPoly(restored, [np.rint(polygon).astype(np.int32)], 1)
    assert restored[100, 100] == 0
    assert np.count_nonzero((restored > 0) & (mask > 0)) / np.count_nonzero((restored > 0) | (mask > 0)) >= 0.9
