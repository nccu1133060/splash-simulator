from time import perf_counter

import pytest


@pytest.mark.perf
def test_scene_under_two_seconds():
    from splash_sim import SimConfig, simulate_scene
    cfg = SimConfig(scene={"spray": {"drops_launched": (22, 22)}})
    times = []
    for _ in range(3):
        start = perf_counter()
        out = simulate_scene(cfg)
        times.append(perf_counter()-start)
        assert 15 <= len(out.scene.drops) <= 30
        assert len(out.crops) == len(out.scene.drops)
    print(f"drops={len(out.scene.drops)}, seconds={times}")
    assert min(times) < 2.0
