"""整個場景一起切分，避免同場景液滴跨集合。"""

import numpy as np


def split_scenes(scene_ids, *, fractions=(0.70, 0.15, 0.15), seed: int) -> dict[str, list[int]]:
    """回傳排序的 train／val／test 場景清單。"""
    if (len(fractions) != 3 or not all(np.isfinite(f) and f > 0 for f in fractions)
            or not np.isclose(sum(fractions), 1.0, rtol=0, atol=1e-9)):
        raise ValueError("fractions 必須為三個有限正數且總和為 1")
    scenes = np.unique(scene_ids)
    scenes = np.random.default_rng(seed).permutation(scenes)
    n_train = int(len(scenes) * fractions[0])
    n_val = int(len(scenes) * fractions[1])
    if min(n_train, n_val, len(scenes)-n_train-n_val) < 1:
        raise ValueError("fractions 與場景數無法讓每個集合至少有一個場景")
    return {key: sorted(part.tolist()) for key, part in zip(
        ("train", "val", "test"), np.split(scenes, [n_train, n_train+n_val]))}


def apply_split(df, split):
    """保留原始列序與索引，依 scene_index 選取各集合。"""
    return {key: df.loc[df["scene_index"].isin(ids)].copy() for key, ids in split.items()}
