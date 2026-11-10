from dataclasses import replace

import numpy as np
import pytest

from splash_sim.impact import StainGeometry, Spine, Satellite


def geometry(**kwargs):
    return replace(StainGeometry((105., 148.5), 10., 10., 0., 90., (), (), 0., 0.,
                                 3., 2., 166., 5988., 10/3, "literature_v1"), **kwargs)


def render(s, **kwargs):
    from splash_sim.config import RenderConfig
    from splash_sim.render import render_stains
    return render_stains([s], RenderConfig(**kwargs), np.random.default_rng(42))


def test_render_single_round_stain_mask():
    out = render(geometry())
    y, x = np.where(out.instance_mask == 1)
    assert len(x) == pytest.approx(np.pi*50**2, rel=0.03)
    assert (x.mean(), y.mean()) == pytest.approx((1050, 1485), abs=2)
    assert out.image.dtype == np.uint8
    assert out.instance_mask.dtype == np.uint16
    assert tuple(out.image[0, 0]) == (245, 245, 240)
    assert np.linalg.norm(out.image[1485, 1050].astype(float) - [190, 30, 45]) < 100


def test_tail_and_satellites_rendered():
    out = render(geometry(tail_length_mm=5., satellites=(Satellite((20., 0.), 2.),)))
    assert np.where(out.instance_mask == 1)[1].max() > 1125
    assert out.satellite_mask[1485, 1250] == 1
    assert out.instance_mask[1485, 1250] == 0


def test_render_stain_partly_off_canvas():
    out = render(geometry(center_mm=(1., 1.)))
    assert out.instance_mask.shape == (2970, 2100)
    assert out.instance_mask[2960, 10] == 1
    assert np.count_nonzero(out.instance_mask) > 0


def test_bleed_widens_edge():
    a = render(geometry(bleed_mm=0.05), dye_opacity=(1., 1.))
    b = render(geometry(bleed_mm=0.4), dye_opacity=(1., 1.))
    assert np.array_equal(a.instance_mask, b.instance_mask)
    def transitional(out):
        return np.count_nonzero((out.image[:, :, 1] > 30) & (out.image[:, :, 1] < 245))
    assert transitional(b) > transitional(a)


def test_render_augment_yaml_loads(tmp_path):
    from splash_sim.config import load_config
    path = tmp_path / "圖像.yaml"
    path.write_text("render: {paper_rgb: [245, 245, 240], dye_opacity: [0.6, 0.9]}\naugment: {blur: {sigma_px: [0.0, 1.2]}, noise: {std: [1.0, 4.0]}, jpeg: {quality: [75, 95]}}", encoding="utf-8")
    cfg = load_config(path)
    assert cfg.render.paper_rgb == (245, 245, 240)
    assert cfg.augment.jpeg.quality == (75, 95)
