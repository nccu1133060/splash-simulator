import numpy as np
import pytest


@pytest.mark.parametrize("array", [np.arange(36, dtype=np.uint8).reshape(3, 4, 3), np.array([[0, 256, 65535]], dtype=np.uint16)])
def test_png_roundtrip_non_ascii_path(tmp_path, array):
    from splash_sim.imageio import write_png, read_png
    path = tmp_path / "中文資料夾" / "a.png"
    write_png(path, array)
    assert np.array_equal(read_png(path), array)
