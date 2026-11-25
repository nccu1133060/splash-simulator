import numpy as np
import pandas as pd
import pytest


def test_split_disjoint_by_scene():
    from splash_model.split import apply_split, split_scenes
    ids = np.repeat(np.arange(100), 3)
    df = pd.DataFrame({"scene_index": ids, "drop_id": np.tile([1, 2, 3], 100)},
                      index=np.arange(300) + 1000)
    split = split_scenes(ids, seed=42)
    assert set(split) == {"train", "val", "test"}
    groups = [set(split[key]) for key in ("train", "val", "test")]
    assert set.union(*groups) == set(range(100))
    for i, group in enumerate(groups):
        assert all(group.isdisjoint(other) for other in groups[i+1:])
    parts = apply_split(df, split)
    for key, expected in zip(("train", "val", "test"), (70, 15, 15)):
        assert abs(len(split[key]) - expected) <= 1
        assert split[key] == sorted(split[key])
        pd.testing.assert_frame_equal(parts[key], df[df.scene_index.isin(split[key])])
    assert sum(map(len, parts.values())) == len(df)


def test_split_deterministic_and_seeded():
    from splash_model.split import split_scenes
    first = split_scenes(range(100), seed=42)
    assert first == split_scenes(range(100), seed=42)
    assert first == split_scenes(list(reversed(range(100))), seed=42)
    assert first != split_scenes(range(100), seed=43)


@pytest.mark.parametrize("ids,fractions", [
    ([0, 1], (0.7, 0.15, 0.15)),
    ([], (0.7, 0.15, 0.15)),
    (list(range(100)), (0.7, 0.3)),
    (list(range(100)), (0.7, -0.1, 0.4)),
    (list(range(100)), (0.7, 0.2, 0.2)),
    (list(range(100)), (0.7, np.nan, 0.3)),
    (list(range(100)), (0.7, 0.3, 0)),
])
def test_split_too_few_scenes(ids, fractions):
    from splash_model.split import split_scenes
    with pytest.raises(ValueError, match="fractions") as error:
        split_scenes(ids, fractions=fractions, seed=42)
    assert any("\u4e00" <= char <= "\u9fff" for char in str(error.value))
