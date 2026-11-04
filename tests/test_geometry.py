import pytest


def test_mm_px_roundtrip():
    from splash_sim.geometry import (
        CANVAS_SHAPE,
        mm_to_px,
        on_paper,
        px_to_mm,
    )

    assert CANVAS_SHAPE == (2970, 2100)
    assert mm_to_px(0, 0) == (0, 2970)
    assert mm_to_px(210, 297) == (2100, 0)
    assert px_to_mm(*mm_to_px(12.3, 45.6)) == pytest.approx((12.3, 45.6), abs=1e-9)
    assert on_paper(-0.1, 10) is False
    assert on_paper(0, 0) is True
    assert on_paper(210, 297) is True
    assert on_paper(210.1, 10) is False
    assert on_paper(10, -0.1) is False
    assert on_paper(10, 297.1) is False
