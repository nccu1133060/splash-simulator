import numpy as np
import pytest


def stain(velocity=(0, 0, -2), **kwargs):
    from splash_sim.config import ImpactConfig, LiquidConfig
    from splash_sim.impact import compute_stain

    return compute_stain((105, 148.5), np.array(velocity, dtype=float), 3.0,
                         LiquidConfig(), ImpactConfig(**kwargs), np.random.default_rng(42))


def test_weber_reynolds_definitions():
    result = stain()
    assert result.weber == pytest.approx(166.33333333333334)
    assert result.reynolds == pytest.approx(5988.0)


def test_vertical_impact_round_with_laan_spread():
    result = stain(jitter_frac=0)
    p = 166.33333333333334 * 5988.0**(-0.4)
    spread = 5988.0**0.2 * np.sqrt(p) / (1.24 + np.sqrt(p))
    assert result.width_mm == result.length_mm
    assert result.impact_angle_deg == pytest.approx(90)
    assert result.spread_factor == pytest.approx(spread, rel=1e-9)
    assert result.width_mm == pytest.approx(spread * 3)


def test_oblique_angle_and_direction():
    for velocity, direction in [((1, 0, -1), 0), ((0, -1, -1), 270), ((-1, 1, -np.sqrt(2)), 135)]:
        result = stain(velocity, jitter_frac=0)
        assert result.impact_angle_deg == pytest.approx(45)
        assert result.width_mm / result.length_mm == pytest.approx(np.sqrt(0.5), abs=1e-9)
        assert result.direction_deg == pytest.approx(direction)


def test_angle_bias_applied():
    result = stain((1, 0, -1), jitter_frac=0, angle_bias_deg=5)
    assert result.width_mm / result.length_mm == pytest.approx(np.sin(np.radians(50)))


def test_monotonic_in_speed():
    results = [stain((v/np.sqrt(2), 0, -v/np.sqrt(2)), jitter_frac=0) for v in (0.5, 1, 2, 3, 5)]
    assert np.all(np.diff([s.width_mm for s in results]) >= 0)
    assert np.all(np.diff([len(s.spines) for s in results]) >= 0)
    assert len(results[-1].spines) > len(results[0].spines)


def test_spines_concentrate_forward_when_oblique():
    def concentration(s):
        return abs(np.mean(np.exp(1j * np.radians([p.angle_deg for p in s.spines]))))
    oblique = stain((4*np.cos(np.radians(20)), 0, -4*np.sin(np.radians(20))), jitter_frac=0)
    assert concentration(oblique) > 0.6
    assert concentration(stain((0, 0, -4), jitter_frac=0)) < 0.4


def test_satellites_only_above_threshold():
    assert stain((0, 0, -1)).satellites == ()
    result = stain((0, 0, -5), jitter_frac=0)
    assert 1 <= len(result.satellites) <= 8
    assert all(np.linalg.norm(s.offset_mm) >= result.length_mm/2 for s in result.satellites)
    oblique = stain((2, 0, -2), jitter_frac=0)
    assert oblique.tail_length_mm == pytest.approx(0.4 * oblique.width_mm / np.sqrt(2))


def test_same_seed_same_stain():
    from splash_sim.config import ImpactConfig, LiquidConfig
    from splash_sim.impact import compute_stain
    a = stain()
    b = stain()
    assert a == b
    c = compute_stain((105, 148.5), np.array([0., 0., -2.]), 3., LiquidConfig(),
                      ImpactConfig(), np.random.default_rng(43))
    assert a.width_mm != c.width_mm


def test_custom_ruleset_registration():
    from dataclasses import replace
    from splash_sim.config import ConfigError
    from splash_sim.impact import register_ruleset
    expected = stain()
    register_ruleset("test_const", lambda *args: replace(expected, ruleset="test_const"))
    assert stain(ruleset="test_const").ruleset == "test_const"
    with pytest.raises(ConfigError, match="literature_v1"):
        stain(ruleset="nope")


def test_impact_config_yaml_ranges(tmp_path):
    from splash_sim.config import load_config, ConfigError
    path = tmp_path / "設定.yaml"
    path.write_text("impact: {spine_length_frac: [0.1, 0.35], satellite_size_frac: [0.03, 0.12]}", encoding="utf-8")
    assert load_config(path).impact.spine_length_frac == (0.1, 0.35)
    path.write_text("impact: {spine_length_frac: [0.4, 0.1]}", encoding="utf-8")
    with pytest.raises(ConfigError, match="impact.spine_length_frac"):
        load_config(path)


@pytest.mark.parametrize("bias", [-20., -10., 85.])
def test_invalid_effective_impact_angle_rejected(bias):
    from splash_sim.config import ConfigError
    velocity = (np.cos(np.radians(10)), 0, -np.sin(np.radians(10)))
    with pytest.raises(ConfigError, match="angle_bias_deg"):
        stain(velocity, angle_bias_deg=bias)


@pytest.mark.parametrize("velocity,diameter", [([0., 0., 0.], 3.), ([0., 0., -2.], 0.), ([0., 0., -2.], -1.), ([float('nan'), 0., -2.], 3.)])
def test_invalid_direct_impact_input_rejected(velocity, diameter):
    from splash_sim.config import ImpactConfig, LiquidConfig, ConfigError
    from splash_sim.impact import compute_stain
    with pytest.raises(ConfigError, match="velocity_m_s|diameter_mm"):
        compute_stain((105., 148.5), np.array(velocity), diameter, LiquidConfig(),
                      ImpactConfig(angle_bias_deg=5.), np.random.default_rng(0))
