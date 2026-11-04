import numpy as np
import pytest

from splash_sim.config import AirConfig, LiquidConfig


def test_drag_coefficient_regimes():
    from splash_sim.flight import drag_coefficient

    assert drag_coefficient(0.5) == pytest.approx(48 * (1 + 0.15 * 0.5**0.687))
    assert drag_coefficient(999) == pytest.approx(24 / 999 * (1 + 0.15 * 999**0.687))
    assert drag_coefficient(1000) == 0.44
    assert drag_coefficient(2000) == 0.44
    for reynolds in (0, -1):
        with pytest.raises(ValueError, match="reynolds") as error:
            drag_coefficient(reynolds)
        assert any("\u4e00" <= char <= "\u9fff" for char in str(error.value))


def test_no_drag_matches_projectile():
    from splash_sim.flight import fly_to_plane

    position = np.array([0.10, 0.15, 0.20])
    velocity = np.array([1.0, 0.0, 0.0])
    result = fly_to_plane(position, velocity, 0.003, LiquidConfig(), AirConfig(drag_enabled=False))
    time_s = np.sqrt(2 * 0.20 / 9.81)
    assert result.flight_time_s == pytest.approx(time_s, abs=1e-10)
    np.testing.assert_allclose(result.impact_position_m, [0.10 + time_s, 0.15, 0], rtol=0, atol=1e-5)
    np.testing.assert_allclose(result.impact_velocity_m_s, [1, 0, -9.81 * time_s], rtol=0, atol=1e-8)
    np.testing.assert_array_equal(position, [0.10, 0.15, 0.20])
    np.testing.assert_array_equal(velocity, [1.0, 0.0, 0.0])


def test_drag_shortens_range():
    from splash_sim.flight import fly_to_plane

    position = np.array([0.05, 0.10, 0.25])
    velocity = np.array([2.0, 1.0, 0.5])
    liquid = LiquidConfig()
    with_drag = fly_to_plane(position, velocity, 0.001, liquid, AirConfig())
    without_drag = fly_to_plane(position, velocity, 0.001, liquid, AirConfig(drag_enabled=False))
    assert np.linalg.norm(with_drag.impact_position_m[:2] - position[:2]) < np.linalg.norm(
        without_drag.impact_position_m[:2] - position[:2]
    )


def test_backward_propagation_returns_to_source():
    from splash_sim.flight import fly_to_plane, propagate

    position = np.array([0.05, 0.10, 0.25])
    velocity = np.array([2.0, 1.0, 0.5])
    liquid, air = LiquidConfig(), AirConfig()
    impact = fly_to_plane(position, velocity, 0.001, liquid, air)
    recovered_position, recovered_velocity = propagate(
        impact.impact_position_m, impact.impact_velocity_m_s, 0.001,
        liquid, air, -impact.flight_time_s,
    )
    assert np.linalg.norm(recovered_position - position) < 1e-5
    np.testing.assert_allclose(recovered_velocity, velocity, rtol=0, atol=1e-5)


@pytest.mark.parametrize("height_m", [0.0, -0.01])
def test_fly_rejects_start_below_plane(height_m):
    from splash_sim.flight import fly_to_plane

    with pytest.raises(ValueError, match="position_m") as error:
        fly_to_plane([0.1, 0.15, height_m], [0, 0, -1], 0.003, LiquidConfig(), AirConfig())
    assert any("\u4e00" <= char <= "\u9fff" for char in str(error.value))


def test_fly_rejects_no_impact_within_max_time():
    from splash_sim.flight import fly_to_plane

    with pytest.raises(ValueError, match="max_time_s") as error:
        fly_to_plane([0.1, 0.15, 0.2], [1, 0, 0], 0.003,
                     LiquidConfig(), AirConfig(), max_time_s=0.01)
    assert any("\u4e00" <= char <= "\u9fff" for char in str(error.value))
