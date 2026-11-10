import numpy as np
import pytest


def test_disabled_is_identity():
    from splash_sim.config import AugmentConfig
    from splash_sim.augment import apply_augmentations
    cfg = AugmentConfig(**{key: {"enabled": False} for key in ("paper_texture", "lighting", "blur", "noise", "jpeg")})
    image = np.full((40, 50, 3), 128, dtype=np.uint8)
    out = apply_augmentations(image, cfg, np.random.default_rng(0))
    assert np.array_equal(out, image)
    assert not np.shares_memory(out, image)


@pytest.mark.parametrize("effect", ["paper_texture", "lighting", "blur", "noise", "jpeg"])
def test_enabled_changes_image(effect):
    from splash_sim.config import AugmentConfig
    from splash_sim.augment import apply_augmentations
    settings = {key: {"enabled": key == effect} for key in ("paper_texture", "lighting", "blur", "noise", "jpeg")}
    image = np.random.default_rng(0).integers(50, 200, (40, 50, 3), dtype=np.uint8)
    out = apply_augmentations(image, AugmentConfig(**settings), np.random.default_rng(1))
    assert not np.array_equal(out, image)


def test_same_rng_same_output():
    from splash_sim.config import AugmentConfig
    from splash_sim.augment import apply_augmentations
    image = np.full((40, 50, 3), 128, dtype=np.uint8)
    a = apply_augmentations(image, AugmentConfig(), np.random.default_rng(0))
    b = apply_augmentations(image, AugmentConfig(), np.random.default_rng(0))
    assert np.array_equal(a, b)


def test_input_not_modified():
    from splash_sim.config import AugmentConfig
    from splash_sim.augment import apply_augmentations
    image = np.full((40, 50, 3), 128, dtype=np.uint8)
    apply_augmentations(image, AugmentConfig(), np.random.default_rng(0))
    assert np.all(image == 128)
