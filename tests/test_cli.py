from pathlib import Path
import pytest


def test_cli_generate_and_exit_codes(tmp_path, capsys):
    from splash_sim.cli import main
    assert main(["generate", "--config", "configs/default.yaml", "--out", str(tmp_path), "--n", "1"]) == 0
    root = Path(capsys.readouterr().out.strip())
    assert (root / "scenes" / "scene_00001.png").is_file()
    bad = tmp_path / "錯誤.yaml"
    bad.write_text("liquid: {density_kg_m3: -1}", encoding="utf-8")
    assert main(["generate", "--config", str(bad)]) == 2
    error = capsys.readouterr().err
    assert "liquid.density_kg_m3" in error
    assert "Traceback" not in error


def test_cli_preview_writes_png(tmp_path):
    from splash_sim.cli import main
    from splash_sim.imageio import read_png
    path = tmp_path / "預覽.png"
    assert main(["preview", "--config", "configs/default.yaml", "--out", str(path)]) == 0
    assert read_png(path).shape == (2970, 2100, 3)


def test_cli_export_yolo(tmp_path):
    from splash_sim.cli import main
    from splash_sim.config import SimConfig
    from splash_sim.dataset import generate_dataset
    root = generate_dataset(SimConfig(scene={"mode": "single"}), tmp_path, n_scenes=1, folder_suffix="export")
    assert main(["export-yolo", "--dataset", str(root)]) == 0
    assert (root / "yolo" / "labels" / "scene_00001.txt").is_file()


def test_example_configs_load():
    from splash_sim.config import load_config
    assert load_config("configs/vertical_drop_calibration.yaml").scene.mode == "vertical_drop"
    assert load_config("configs/single_drop_training.yaml").output.n_scenes == 5000
    assert load_config("configs/variable_droplet.yaml").scene.diameter.mode == "log_uniform"
    for path in Path("configs").glob("*.yaml"):
        load_config(path)


@pytest.mark.parametrize("content, field", [
    ("augment: {noise: {std: [4.0, 1.0]}}", "augment.noise.std"),
    ("render: {dye_opacity: [0.9, 0.6]}", "render.dye_opacity"),
    ("impact: {bleed_mm: {copy: 0.4}}", "impact.bleed_mm"),
    ("scene: {mode: single, single: {impact_angle_deg: [10.0, 10.0]}}\nimpact: {angle_bias_deg: -20.0}", "angle_bias_deg"),
])
def test_cli_invalid_render_settings_report_chinese(tmp_path, capsys, content, field):
    from splash_sim.cli import main
    path = tmp_path / "設定錯誤.yaml"
    path.write_text(content, encoding="utf-8")
    assert main(["preview", "--config", str(path), "--out", str(tmp_path / "never.png")]) == 2
    message = capsys.readouterr().err
    assert field in message and "Traceback" not in message
    assert any("\u4e00" <= character <= "\u9fff" for character in message)
    assert not (tmp_path / "never.png").exists()


def test_cli_subprocess_invalid_settings(tmp_path):
    import os
    import subprocess
    import sys
    path = tmp_path / "跨程序.yaml"
    path.write_text("augment: {noise: {std: [4.0, 1.0]}}", encoding="utf-8")
    process = subprocess.run([sys.executable, "-m", "splash_sim.cli", "preview", "--config", str(path)],
                             capture_output=True, text=True, encoding="utf-8",
                             env={**os.environ, "PYTHONIOENCODING": "utf-8"}, timeout=30)
    assert process.returncode == 2
    assert "augment.noise.std" in process.stderr
    assert "Traceback" not in process.stderr
