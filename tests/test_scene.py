import numpy as np
import pytest

from splash_sim.config import default_config


def configured(**kwargs):
    from splash_sim.config import SceneConfig
    return default_config().model_copy(update={"scene": SceneConfig(**kwargs)})


def test_spray_scene_has_enough_drops_on_paper():
    from splash_sim.scene import sample_scene
    from splash_sim.geometry import on_paper
    scene = sample_scene(default_config(), 0)
    assert len(scene.drops) >= 9
    assert 0.1 <= scene.source_m[2] <= 0.3
    assert all(on_paper(*d.stain.center_mm) and d.stain.impact_angle_deg >= 10 for d in scene.drops)


def test_spray_discards_shallow_impacts():
    from splash_sim.scene import sample_scene
    scene = sample_scene(configured(spray={"min_impact_angle_deg": 45.}), 0)
    assert scene.discarded["too_shallow"] > 0
    assert all(d.stain.impact_angle_deg >= 45 for d in scene.drops)


def test_spray_gives_up_with_chinese_error():
    from splash_sim.scene import sample_scene, SceneSamplingError
    with pytest.raises(SceneSamplingError) as error:
        sample_scene(configured(spray={"source_offset_m": 5., "max_resample": 3}), 0)
    assert "source_offset_m" in str(error.value)
    assert "max_resample" in str(error.value)


def test_vertical_drop_speed_matches_flight():
    from splash_sim.scene import sample_scene
    from splash_sim.flight import fly_to_plane
    cfg = configured(mode="vertical_drop")
    scene = sample_scene(cfg, 0)
    expected = fly_to_plane([0, 0, 0.1], [0, 0, 0], 0.003, cfg.liquid, cfg.air)
    assert len(scene.drops) == 12
    for drop in scene.drops:
        assert drop.stain.impact_angle_deg == pytest.approx(90)
        assert drop.stain.speed_m_s == pytest.approx(abs(expected.impact_velocity_m_s[2]), rel=1e-9)
        assert drop.stain.speed_m_s < np.sqrt(2*9.81*0.1)


def test_single_mode_ranges():
    from splash_sim.scene import sample_scene
    cfg = configured(mode="single")
    for index in range(20):
        scene = sample_scene(cfg, index)
        assert len(scene.drops) == 1
        assert 0.5 <= scene.drops[0].stain.speed_m_s <= 5
        assert 10 <= scene.drops[0].stain.impact_angle_deg <= 90


def test_scene_reproducible_and_independent():
    from splash_sim.scene import sample_scene
    cfg = default_config()
    a = sample_scene(cfg, 5)
    for index in range(5):
        sample_scene(cfg, index)
    b = sample_scene(cfg, 5)
    assert np.array_equal(a.source_m, b.source_m)
    assert [d.stain for d in a.drops] == [d.stain for d in b.drops]
    assert a.discarded == b.discarded


@pytest.mark.parametrize("content,field", [
    ("scene: {spray: {source_height_m: [-0.1, 0.3]}}", "scene.spray.source_height_m"),
    ("scene: {spray: {launch_speed_m_s: [5, 1]}}", "scene.spray.launch_speed_m_s"),
    ("scene: {spray: {drops_launched: [0, 30]}}", "scene.spray.drops_launched"),
    ("scene: {vertical_drop: {heights_m: []}}", "scene.vertical_drop.heights_m"),
    ("scene: {vertical_drop: {grid: [0, 4]}}", "scene.vertical_drop.grid"),
    ("scene: {diameter: {range_mm: [0, 4]}}", "scene.diameter.range_mm"),
    ("scene: {single: {impact_angle_deg: [0, 100]}}", "scene.single.impact_angle_deg"),
])
def test_scene_rejects_invalid_ranges(tmp_path, content, field):
    from splash_sim.config import load_config, ConfigError
    path = tmp_path / "錯誤.yaml"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(ConfigError, match=field):
        load_config(path)
