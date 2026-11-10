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
