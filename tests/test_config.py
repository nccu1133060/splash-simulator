import pytest


def test_default_config_values():
    from splash_sim.config import default_config

    config = default_config()
    assert config.liquid.density_kg_m3 == 998.0
    assert config.air.drag_enabled is True
    assert config.seed == 0


def test_load_config_utf8_comments(tmp_path):
    from splash_sim.config import load_config

    path = tmp_path / "中文設定.yaml"
    path.write_text("# 液體密度\nliquid: {density_kg_m3: 1000}\n", encoding="utf-8")
    assert load_config(path).liquid.density_kg_m3 == 1000.0


@pytest.mark.parametrize(
    "content, field, reason",
    [
        ("air: {density_kg_m3: -1}", "air.density_kg_m3", "大於"),
        ("liquid: {colour: red}", "liquid.colour", "不認得"),
        ('liquid: {density_kg_m3: "998"}', "liquid.density_kg_m3", "數字"),
    ],
)
def test_load_config_rejects_bad_values(tmp_path, content, field, reason):
    from splash_sim.config import ConfigError, load_config

    path = tmp_path / "錯誤設定.yaml"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(ConfigError) as error:
        load_config(path)
    message = str(error.value)
    assert str(path) in message
    assert field in message
    assert reason in message
    assert "合理範圍" in message


def test_default_yaml_matches_defaults():
    from splash_sim.config import default_config, load_config

    assert load_config("configs/default.yaml") == default_config()


def test_load_config_missing_file(tmp_path):
    from splash_sim.config import ConfigError, load_config

    path = tmp_path / "不存在.yaml"
    with pytest.raises(ConfigError) as error:
        load_config(path)
    assert str(path) in str(error.value)
    assert "讀取" in str(error.value)


def test_load_config_invalid_yaml(tmp_path):
    from splash_sim.config import ConfigError, load_config

    path = tmp_path / "語法錯誤.yaml"
    path.write_text("liquid: [\n", encoding="utf-8")
    with pytest.raises(ConfigError) as error:
        load_config(path)
    assert str(path) in str(error.value)
    assert "語法" in str(error.value)


@pytest.mark.parametrize("content,field", [
    ("augment: {noise: {std: [4.0, 1.0]}}", "augment.noise.std"),
    ("augment: {blur: {sigma_px: [-1.0, 1.0]}}", "augment.blur.sigma_px"),
    ("augment: {jpeg: {quality: [0, 101]}}", "augment.jpeg.quality"),
    ("render: {dye_opacity: [0.9, 0.6]}", "render.dye_opacity"),
    ("render: {paper_rgb: [256, 0, 0]}", "render.paper_rgb"),
    ("impact: {bleed_mm: {copy: 0.4}}", "impact.bleed_mm"),
    ("impact: {bleed_mm: {coated: -1.0, copy: 0.4}}", "impact.bleed_mm"),
    ("impact: {spine_front_kappa: .inf}", "impact.spine_front_kappa"),
])
def test_rendering_settings_rejected_before_simulation(tmp_path, content, field):
    from splash_sim.config import ConfigError, load_config
    path = tmp_path / "範圍錯誤.yaml"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(ConfigError, match=field):
        load_config(path)
