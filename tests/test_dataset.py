import csv
import hashlib
import json

import numpy as np
import pytest

from splash_sim.config import SimConfig, load_config


def clean_config(**kwargs):
    settings = {key: {"enabled": False} for key in ("paper_texture", "lighting", "blur", "noise", "jpeg")}
    return SimConfig(scene={"mode": "single"}, augment=settings,
                     impact={"jitter_frac": 0., "spine_a": 0., "tail_coeff": 0., "satellite_max": 0}, **kwargs)


def test_crop_near_edge_padded_and_flagged():
    from splash_sim.dataset import simulate_single_drop
    cfg = clean_config()
    edge = simulate_single_drop([0., 0., -2.], 3., cfg, center_mm=(2., 2.))
    assert edge.crops[0].shape == (384, 384, 3)
    assert tuple(edge.crops[0][-1, 0]) == cfg.render.paper_rgb
    assert edge.truncated[0] is True
    center = simulate_single_drop([0., 0., -2.], 3., cfg)
    assert center.truncated[0] is False


def test_generate_dataset_layout(tmp_path):
    from splash_sim.dataset import generate_dataset
    from splash_sim.imageio import read_png
    cfg = clean_config()
    root = generate_dataset(cfg, tmp_path, n_scenes=2, folder_suffix="layout")
    assert load_config(root / "config_snapshot.yaml") == cfg
    assert json.loads((root / "meta.json").read_text(encoding="utf-8"))["n_scenes"] == 2
    rows = list(csv.DictReader((root / "index.csv").open(encoding="utf-8", newline="")))
    labels = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((root / "labels").glob("*.json"))]
    assert sum(len(label["drops"]) for label in labels) == len(rows) == len(list((root / "crops").glob("*.png"))) == 2
    for i, label in enumerate(labels, 1):
        mask = read_png(root / "masks" / f"scene_{i:05d}.png")
        assert set(np.unique(mask)) - {0} == {d["instance_id"] for d in label["drops"]}
        assert (root / "scenes" / f"scene_{i:05d}.png").exists()
        assert "impact_velocity_m_s_x" in rows[i-1]
        assert (root / label["drops"][0]["crop_file"]).is_file()


def test_dataset_byte_identical(tmp_path):
    from splash_sim.dataset import generate_dataset
    cfg = SimConfig(scene={"mode": "single"})
    a = generate_dataset(cfg, tmp_path, n_scenes=1, folder_suffix="a")
    b = generate_dataset(cfg, tmp_path, n_scenes=1, folder_suffix="b")
    def hashes(root):
        return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob("*") if p.is_file()}
    assert hashes(a) == hashes(b)


def test_labels_consistent_with_image(tmp_path):
    from splash_sim.dataset import generate_dataset
    from splash_sim.imageio import read_png
    from splash_sim.features import measure_stain
    root = generate_dataset(clean_config(), tmp_path, n_scenes=3, folder_suffix="consistent")
    for path in (root / "labels").glob("*.json"):
        label = json.loads(path.read_text(encoding="utf-8"))
        mask = read_png(root / "masks" / (path.stem + ".png"))
        for drop in label["drops"]:
            x0, y0, x1, y1 = drop["bbox_px"]
            measured = measure_stain(mask[y0:y1, x0:x1] == drop["instance_id"])
            assert abs(measured.aspect_ratio - np.sin(np.radians(drop["impact_angle_deg"]))) <= 0.03


@pytest.mark.parametrize("overrides", [{"n_scenes": 0}, {"name": "../escape"}, {"folder_suffix": "../escape"}])
def test_dataset_rejects_invalid_output_before_writing(tmp_path, overrides):
    from splash_sim.dataset import generate_dataset
    from splash_sim.config import ConfigError
    with pytest.raises(ConfigError):
        generate_dataset(clean_config(), tmp_path, **({"n_scenes": 1} | overrides))
    assert list(tmp_path.iterdir()) == []
