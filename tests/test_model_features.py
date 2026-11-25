from pathlib import Path
import json

import numpy as np
import pytest

from splash_sim.config import SimConfig, default_config, load_config
from splash_sim.dataset import simulate_single_drop


@pytest.mark.parametrize("config_path", [None, "configs/model/provisional_train.yaml"])
@pytest.mark.parametrize("speed", [2, 4])
@pytest.mark.parametrize("alpha", [30, 60, 90])
def test_measure_drop_matches_geometry(config_path, speed, alpha):
    from splash_model.features import FEATURE_COLUMNS, OBSERVED_COLUMNS, measure_drop
    cfg = load_config(Path(config_path)) if config_path else default_config()
    data = cfg.model_dump()
    for augmentation in data["augment"].values():
        augmentation["enabled"] = False
    data["impact"]["jitter_frac"] = 0.0
    cfg = SimConfig.model_validate(data)
    radians = np.radians(alpha)
    output = simulate_single_drop([speed*np.cos(radians), 0, -speed*np.sin(radians)], 3.0, cfg)
    stain = output.scene.drops[0].stain
    yy, xx = (output.rendered.instance_mask == 1).nonzero()
    measured = measure_drop(output.rendered.instance_mask, output.rendered.satellite_mask,
                            1, (xx.min(), yy.min(), xx.max()+1, yy.max()+1))
    assert set(measured) == set(FEATURE_COLUMNS + OBSERVED_COLUMNS)
    assert measured["meas_width_mm"] == pytest.approx(stain.width_mm, rel=0.03)
    assert measured["meas_aspect_ratio"] == pytest.approx(np.sin(radians), abs=0.03)
    for field in ("meas_outer_width_mm", "meas_outer_length_mm"):
        assert np.isfinite(measured[field]) and measured[field] > 0
    if config_path is None:
        assert measured["meas_outer_width_mm"] > measured["meas_width_mm"]
    if stain.satellites:
        assert 1 <= measured["meas_satellite_count"] <= len(stain.satellites)


def test_model_configs_load():
    root = Path("configs/model")
    configs = {}
    for name in ("provisional_train", "independent_test", "rule_perturbed"):
        path = root / f"{name}.yaml"
        text = path.read_text(encoding="utf-8")
        assert "暫定" in text or "規則擾動" in text
        configs[name] = load_config(path).model_dump()

    def changed_values(before, after, prefix=""):
        changes = {}
        for key in before:
            name = f"{prefix}{key}"
            if isinstance(before[key], dict):
                changes.update(changed_values(before[key], after[key], name + "."))
            elif before[key] != after[key]:
                changes[name] = after[key]
        return changes

    assert changed_values(configs["provisional_train"], configs["independent_test"]) == {
        "seed": 20261118, "output.n_scenes": 30, "output.name": "independent_test",
    }
    assert changed_values(configs["provisional_train"], configs["rule_perturbed"]) == {
        "seed": 20261119, "output.n_scenes": 30, "output.name": "rule_perturbed",
        "impact.spread_a": 1.05, "impact.angle_bias_deg": 3.0,
        "impact.spine_a": 0.1443, "impact.spine_length_frac": (0.1, 0.35),
    }


def test_satellites_separable_exact():
    from test_render import geometry, render
    from splash_sim.impact import Satellite
    from splash_model.features import measure_drop

    output = render(geometry(satellites=(
        Satellite((20., 0.), 1.), Satellite((0., 30.), 1.),
        Satellite((-40., 0.), 1.),
    )))
    measured = measure_drop(output.instance_mask, output.satellite_mask,
                            1, (1000, 1435, 1101, 1536), margin_px=0)
    assert measured["meas_satellite_count"] == 3
    assert measured["meas_satellite_max_dist_mm"] == pytest.approx(40., abs=0.5)
    assert measured["meas_satellite_area_mm2"] > 0


@pytest.fixture
def feature_dataset(tmp_path):
    from splash_sim.dataset import generate_dataset
    from test_dataset import clean_config

    cfg = clean_config().model_dump()
    cfg["scene"]["mode"] = "vertical_drop"
    cfg["scene"]["vertical_drop"]["grid"] = (2, 2)
    root = generate_dataset(SimConfig.model_validate(cfg), tmp_path / "中文",
                            n_scenes=2, folder_suffix="features")
    for path in (root / "labels").glob("*.json"):
        scene = json.loads(path.read_text(encoding="utf-8"))
        scene["drops"].reverse()
        path.write_text(json.dumps(scene, ensure_ascii=False), encoding="utf-8")
    return root


def test_feature_table_layout(feature_dataset):
    from splash_model.features import (
        FEATURE_COLUMNS, KEY_COLUMNS, OBSERVED_COLUMNS, TARGET_COLUMN,
        TRUTH_COLUMNS, build_feature_table,
    )

    table = build_feature_table(feature_dataset)
    assert tuple(table.columns) == (
        KEY_COLUMNS + FEATURE_COLUMNS + OBSERVED_COLUMNS + (TARGET_COLUMN,) + TRUTH_COLUMNS
    )
    labels = [json.loads(path.read_text(encoding="utf-8"))
              for path in sorted((feature_dataset / "labels").glob("*.json"))]
    total = sum(len(scene["drops"]) for scene in labels)
    assert total == 8
    assert set(table.attrs["excluded"]) == {"truncated", "occluded", "unmeasurable"}
    assert len(table) + sum(table.attrs["excluded"].values()) == total
    assert table.attrs["excluded"]["truncated"] == sum(
        drop["truncated"] for scene in labels for drop in scene["drops"]
    )
    assert len(table) == 8
    assert list(zip(table.scene_index, table.drop_id)) == [
        (scene, drop) for scene in range(2) for drop in range(4)
    ]
    for scene in labels:
        for drop in scene["drops"]:
            row = table[(table.scene_index == scene["scene_index"]) &
                        (table.drop_id == drop["drop_id"])].iloc[0]
            assert (row.obs_center_mm_x, row.obs_center_mm_y) == pytest.approx(
                drop["center_mm"], abs=1.0
            )
            assert row.speed_m_s == drop["speed_m_s"]
            assert row.impact_angle_deg == drop["impact_angle_deg"]
            assert row.direction_deg == drop["direction_deg"]
            assert (row.center_mm_x, row.center_mm_y) == tuple(drop["center_mm"])
            assert tuple(row[f"impact_velocity_m_s_{axis}"] for axis in "xyz") == tuple(
                drop["impact_velocity_m_s"]
            )
            assert row.diameter_mm == drop["diameter_mm"]
            assert row.meas_width_mm == pytest.approx(drop["width_mm"], rel=0.03)
            assert (row.meas_satellite_count, row.meas_satellite_area_mm2,
                    row.meas_satellite_max_dist_mm) == (0., 0., 0.)


def test_feature_columns_whitelisted():
    import pandas as pd
    from splash_model.features import (
        FEATURE_COLUMNS, TARGET_COLUMN, TRUTH_COLUMNS, assert_no_leakage,
    )

    features = pd.DataFrame([[1.] * len(FEATURE_COLUMNS)], columns=FEATURE_COLUMNS)
    assert_no_leakage(features)
    assert not set(FEATURE_COLUMNS) & (set(TRUTH_COLUMNS) | {TARGET_COLUMN})
    for column in ("width_mm", "spine_count", "speed_m_s", "obs_direction_deg", "meas_unknown"):
        with pytest.raises(ValueError) as error:
            assert_no_leakage(features.assign(**{column: 1.}))
        message = str(error.value)
        assert column in message
        assert any("\u4e00" <= char <= "\u9fff" for char in message)


def test_feature_table_deterministic(feature_dataset):
    from splash_model.features import build_feature_table

    first = build_feature_table(feature_dataset)
    second = build_feature_table(feature_dataset)
    assert first.equals(second)
    assert first.attrs == second.attrs


@pytest.mark.parametrize("all_excluded", [False, True])
def test_feature_table_exclusion_priority(feature_dataset, all_excluded):
    from splash_model.features import (
        FEATURE_COLUMNS, KEY_COLUMNS, OBSERVED_COLUMNS, TARGET_COLUMN,
        TRUTH_COLUMNS, build_feature_table,
    )
    from splash_sim.imageio import read_png, write_png

    path = feature_dataset / "labels" / "scene_00001.json"
    label = json.loads(path.read_text(encoding="utf-8"))
    label["drops"].sort(key=lambda drop: drop["drop_id"])
    mask_path = feature_dataset / "masks" / "scene_00001.png"
    mask = read_png(mask_path)
    # 截斷同時完全遮蔽仍只計截斷；第二滴遮蔽；第三滴僅剩一點不可擬合。
    for drop in label["drops"][:3]:
        mask[mask == drop["instance_id"]] = 0
    label["drops"][0]["truncated"] = True
    drop = label["drops"][2]
    x, y = drop["bbox_px"][:2]
    mask[y, x] = drop["instance_id"]
    drop["bbox_px"] = [x, y, x+1, y+1]
    write_png(mask_path, mask)
    path.write_text(json.dumps(label, ensure_ascii=False), encoding="utf-8")
    if all_excluded:
        for path in (feature_dataset / "labels").glob("*.json"):
            scene = json.loads(path.read_text(encoding="utf-8"))
            for drop in scene["drops"]:
                if scene["scene_index"] == 1 or drop["drop_id"] == 3:
                    drop["truncated"] = True
            path.write_text(json.dumps(scene, ensure_ascii=False), encoding="utf-8")

    table = build_feature_table(feature_dataset)
    assert table.attrs["excluded"] == {
        "truncated": 6 if all_excluded else 1, "occluded": 1, "unmeasurable": 1,
    }
    assert list(zip(table.scene_index, table.drop_id)) == (
        [] if all_excluded else [(0, 3), (1, 0), (1, 1), (1, 2), (1, 3)]
    )
    assert tuple(table.columns) == (
        KEY_COLUMNS + FEATURE_COLUMNS + OBSERVED_COLUMNS + (TARGET_COLUMN,) + TRUTH_COLUMNS
    )


def test_feature_table_satellites_use_local_regions(feature_dataset, monkeypatch):
    from splash_model.features import build_feature_table
    from splash_sim.imageio import read_png, write_png
    from scipy import ndimage

    path = sorted((feature_dataset / "satellite_masks").glob("*.png"))[0]
    mask = read_png(path)
    mask[20:23, 30:33] = 1
    mask[200:205, 300:305] = 1
    mask[60:63, 70:73] = 2
    write_png(path, mask)
    expected = build_feature_table(feature_dataset)
    original_label = ndimage.label

    def local_label(array, *args, **kwargs):
        assert array.size < mask.size, "衛星連通區量測不得逐滴掃描整張遮罩"
        return original_label(array, *args, **kwargs)

    monkeypatch.setattr(ndimage, "label", local_label)
    actual = build_feature_table(feature_dataset)
    assert actual.equals(expected)
    assert actual.attrs == expected.attrs


@pytest.mark.parametrize("diagonal", [False, True])
def test_feature_table_excludes_zero_area_line(feature_dataset, diagonal):
    from splash_model.features import build_feature_table
    from splash_sim.imageio import read_png, write_png

    before = build_feature_table(feature_dataset)
    path = sorted((feature_dataset / "labels").glob("*.json"))[0]
    scene = json.loads(path.read_text(encoding="utf-8"))
    drop = scene["drops"][0]
    mask_path = feature_dataset / "masks" / (path.stem + ".png")
    mask = read_png(mask_path)
    mask[mask == drop["instance_id"]] = 0
    x, y = drop["bbox_px"][:2]
    offsets = np.arange(35)
    mask[y + (offsets if diagonal else 0), x + offsets] = drop["instance_id"]
    write_png(mask_path, mask)
    actual = build_feature_table(feature_dataset)
    expected = before[~((before.scene_index == scene["scene_index"]) &
                        (before.drop_id == drop["drop_id"]))].reset_index(drop=True)
    assert actual.equals(expected)
    exclusions = dict(before.attrs["excluded"])
    exclusions["unmeasurable"] += 1
    assert actual.attrs == {"excluded": exclusions}
