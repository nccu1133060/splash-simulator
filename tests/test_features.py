import numpy as np
import pytest

from test_render import geometry, render


@pytest.mark.parametrize("alpha", [20, 45, 70])
@pytest.mark.parametrize("direction", [0, 30, 135])
def test_measured_ellipse_matches_geometry(alpha, direction):
    from splash_sim.features import measure_stain
    mask = render(geometry(length_mm=10/np.sin(np.radians(alpha)), direction_deg=direction),
                  draw_spines=False, draw_tail=False).instance_mask == 1
    result = measure_stain(mask)
    assert abs(result.aspect_ratio - np.sin(np.radians(alpha))) <= 0.02
    assert abs((result.direction_deg-direction+90) % 180-90) <= 2


@pytest.mark.parametrize("count", [0, 6, 12])
def test_spine_count_measured(count):
    from splash_sim.features import measure_stain
    from splash_sim.impact import Spine
    s = geometry(spines=tuple(Spine(i*360/count, 3., 0.5) for i in range(count)))
    out = render(s)
    assert out.instance_mask[1485, 1125] == (1 if count else 0)
    assert measure_stain(out.instance_mask == 1).spine_count == count


def test_new_shape_fields_on_circle():
    from splash_sim.features import measure_stain
    mask = render(geometry(), draw_spines=False, draw_tail=False).instance_mask == 1
    result = measure_stain(mask)
    assert result.solidity >= 0.99
    assert abs(result.roughness - 1) <= 0.03
    assert result.perimeter_mm == pytest.approx(np.pi * 10, rel=0.03)


@pytest.mark.parametrize("alpha", [30, 60, 90])
def test_measure_body_matches_clean_ellipse(alpha):
    from splash_sim.features import measure_body, measure_stain
    mask = render(geometry(length_mm=10/np.sin(np.radians(alpha))),
                  draw_spines=False, draw_tail=False).instance_mask == 1
    original = measure_stain(mask)
    body = measure_body(mask)
    assert body.width_mm == pytest.approx(original.width_mm, rel=0.01)
    assert body.length_mm == pytest.approx(original.length_mm, rel=0.01)


def test_spines_raise_roughness():
    from splash_sim.features import measure_stain
    from splash_sim.impact import Spine
    plain = render(geometry(), draw_tail=False).instance_mask == 1
    spiny = render(geometry(spines=tuple(Spine(i*30, 0.3, 0.5) for i in range(12))),
                   draw_tail=False).instance_mask == 1
    assert measure_stain(spiny).roughness > measure_stain(plain).roughness


@pytest.mark.parametrize("diameter", [5, 10, 15])
def test_shape_fields_size_invariant(diameter):
    from splash_sim.features import measure_stain
    mask = render(geometry(width_mm=diameter, length_mm=diameter),
                  draw_spines=False, draw_tail=False).instance_mask == 1
    result = measure_stain(mask)
    assert result.roughness == pytest.approx(1, abs=0.03)
    assert result.solidity >= 0.99


@pytest.mark.parametrize("diagonal", [False, True])
def test_measure_stain_rejects_zero_area_lines(diagonal):
    from splash_sim.features import measure_stain

    line = np.eye(35, dtype=bool) if diagonal else np.ones((1, 35), dtype=bool)
    with pytest.raises(ValueError, match="mask.*面積"):
        measure_stain(np.pad(line, 10))
