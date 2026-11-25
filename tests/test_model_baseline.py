import numpy as np
import pandas as pd
import pytest

from splash_sim.config import ImpactConfig, LiquidConfig
from splash_sim.impact import literature_v1


@pytest.mark.parametrize("speed", [1, 2, 4])
@pytest.mark.parametrize("diameter,spread_a,liquid", [
    (3.0, 1.24, LiquidConfig()),
    (2.0, 1.05, LiquidConfig(density_kg_m3=900.0, viscosity_pa_s=0.002,
                           surface_tension_n_m=0.06)),
])
def test_spread_matches_simulator(speed, diameter, spread_a, liquid):
    from splash_model.baseline import laan_spread_factor
    impact = ImpactConfig(jitter_frac=0.0, spread_a=spread_a)
    stain = literature_v1((0, 0), np.array([0, 0, -speed]), diameter,
                          liquid, impact, np.random.default_rng(0))
    assert laan_spread_factor(speed, diameter, liquid, impact.spread_a) == pytest.approx(
        stain.spread_factor, rel=1e-9)


@pytest.mark.parametrize("speed", [0.01, 1, 2, 4, 30])
def test_invert_roundtrip(speed):
    from splash_model.baseline import invert_normal_speed, laan_spread_factor
    liquid = LiquidConfig()
    spread = laan_spread_factor(speed, 3.0, liquid, 1.24)
    assert invert_normal_speed(spread, 3.0, liquid, 1.24) == pytest.approx(speed, abs=1e-6)


@pytest.mark.parametrize("spread", [0.01, 100, np.nan, np.inf, -np.inf])
def test_invert_out_of_range_is_nan(spread):
    from splash_model.baseline import invert_normal_speed
    assert np.isnan(invert_normal_speed(spread, 3.0, LiquidConfig(), 1.24))


@pytest.mark.parametrize("speed", [2, 4])
@pytest.mark.parametrize("alpha", [30, 60, 90])
def test_physics_baseline_on_clean_single_drops(speed, alpha):
    from pathlib import Path
    from splash_model.baseline import physics_baseline
    from splash_model.features import measure_drop
    from splash_sim.config import SimConfig, load_config
    from splash_sim.dataset import simulate_single_drop

    data = load_config(Path("configs/model/provisional_train.yaml")).model_dump()
    for augmentation in data["augment"].values():
        augmentation["enabled"] = False
    data["impact"]["jitter_frac"] = 0.0
    cfg = SimConfig.model_validate(data)
    radians = np.radians(alpha)
    output = simulate_single_drop([speed*np.cos(radians), 0, -speed*np.sin(radians)], 3.0, cfg)
    yy, xx = (output.rendered.instance_mask == 1).nonzero()
    measured = measure_drop(output.rendered.instance_mask, output.rendered.satellite_mask,
                            1, (xx.min(), yy.min(), xx.max()+1, yy.max()+1))
    prediction = physics_baseline(pd.DataFrame([measured]), diameter_mm=3.0,
                                  liquid=cfg.liquid, spread_a=cfg.impact.spread_a)
    assert prediction.shape == (1,)
    assert prediction[0] == pytest.approx(speed, rel=0.05), measured


def test_aspect_above_one_clipped():
    from splash_model.baseline import physics_baseline
    df = pd.DataFrame({"meas_width_mm": [10, 10, 10, 0, np.nan, np.inf, -1, 10, 10],
                       "meas_aspect_ratio": [1.02, 1, 0, 1, 1, 1, 1, np.nan, np.inf]})
    result = physics_baseline(df, diameter_mm=3.0, liquid=LiquidConfig(), spread_a=1.24)
    assert result.shape == (9,)
    assert np.isfinite(result[0])
    assert result[0] == result[1]
    assert np.isnan(result[2:]).all()


def test_constant_baseline_uses_only_training_mean():
    from splash_model.baseline import constant_baseline
    speeds = np.array([2.0, 4.0, 9.0])
    predict = constant_baseline(speeds)
    speeds[:] = 100
    df = pd.DataFrame({"speed_m_s": [-100, 999]}, index=[8, 3])
    np.testing.assert_allclose(predict(df), [5.0, 5.0])
    assert predict(df.iloc[:0]).shape == (0,)


def test_physics_baseline_ignores_truth_and_preserves_row_order():
    from splash_model.baseline import physics_baseline
    from splash_model.features import TRUTH_COLUMNS
    kwargs = dict(diameter_mm=3.0, liquid=LiquidConfig(), spread_a=1.24)
    df = pd.DataFrame({"meas_width_mm": [10.0, 10.0],
                       "meas_aspect_ratio": [1.0, 0.5]}, index=[9, 2])
    expected = physics_baseline(df, **kwargs)
    assert expected[1] == pytest.approx(2 * expected[0])
    poisoned = df.assign(**{field: -9999 for field in (*TRUTH_COLUMNS, "speed_m_s")})
    np.testing.assert_array_equal(physics_baseline(poisoned, **kwargs), expected)
    assert physics_baseline(df.iloc[:0], **kwargs).shape == (0,)


@pytest.mark.parametrize("diameter,spread_a,bounds", [
    (np.nan, 1.24, (0.01, 30)), (0, 1.24, (0.01, 30)),
    (3, np.inf, (0.01, 30)), (3, -1, (0.01, 30)),
    (3, 1.24, (np.nan, 30)), (3, 1.24, (30, 0.01)),
])
def test_invert_invalid_parameters_are_nan(diameter, spread_a, bounds):
    from splash_model.baseline import invert_normal_speed
    assert np.isnan(invert_normal_speed(3, diameter, LiquidConfig(), spread_a,
                                        bounds_m_s=bounds))
