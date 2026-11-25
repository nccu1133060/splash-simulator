import numpy as np
import pandas as pd
import pytest

from splash_model.features import FEATURE_COLUMNS


@pytest.fixture(scope="module")
def synthetic():
    rng = np.random.default_rng(12)
    X = pd.DataFrame(rng.normal(size=(1100, len(FEATURE_COLUMNS))),
                     columns=FEATURE_COLUMNS, index=np.arange(1100) * 3)
    X["meas_width_mm"] = rng.uniform(0, 12, len(X))
    y = 2 + 0.3 * X["meas_width_mm"].to_numpy() + rng.normal(0, 0.3, len(X))
    return X.iloc[:600], y[:600], X.iloc[600:800], y[600:800], X.iloc[800:], y[800:]


@pytest.fixture(scope="module")
def trained(synthetic):
    from splash_model.model import SpeedModel
    return SpeedModel(seed=7).fit(*synthetic[:4])


def test_model_beats_constant_on_synthetic(synthetic, trained):
    _, y_train, _, _, X_test, y_test = synthetic
    prediction = trained.predict(X_test)
    assert list(prediction.columns) == ["q10", "q50", "q90"]
    assert prediction.index.equals(X_test.index)
    mae = np.mean(np.abs(prediction.q50 - y_test))
    constant_mae = np.mean(np.abs(y_train.mean() - y_test))
    assert mae < 0.5 * constant_mae


def test_quantiles_monotone_and_cover(synthetic, trained):
    X_test, y_test = synthetic[4:]
    prediction = trained.predict(X_test)
    assert (prediction.q10 <= prediction.q50).all()
    assert (prediction.q50 <= prediction.q90).all()
    coverage = np.mean((prediction.q10 <= y_test) & (y_test <= prediction.q90))
    assert 0.6 <= coverage <= 0.95


def test_save_load_identical(synthetic, trained, tmp_path):
    import json
    from splash_model.model import SpeedModel

    directory = tmp_path / "中文"
    trained.save(directory)
    assert {p.name for p in directory.iterdir()} == {
        "q10.json", "q50.json", "q90.json", "meta.json"}
    meta = json.loads((directory / "meta.json").read_text(encoding="utf-8"))
    assert meta["feature_columns"] == list(FEATURE_COLUMNS)
    assert meta["seed"] == 7
    assert meta["params"] == trained.params
    assert set(meta["best_iteration"]) == {"q10", "q50", "q90"}
    restored = SpeedModel.load(directory)
    np.testing.assert_array_equal(trained.predict(synthetic[4]), restored.predict(synthetic[4]))


def test_fit_deterministic(synthetic, trained):
    from splash_model.model import SpeedModel

    repeated = SpeedModel(seed=7).fit(*synthetic[:4])
    np.testing.assert_array_equal(trained.predict(synthetic[4]), repeated.predict(synthetic[4]))


@pytest.mark.parametrize("change", ["truth", "missing", "reordered"])
def test_fit_rejects_wrong_columns(synthetic, trained, change):
    from splash_model.model import SpeedModel

    X_train, y_train, X_val, y_val = synthetic[:4]
    def wrong(X):
        if change == "truth":
            return X.assign(width_mm=123)
        if change == "missing":
            return X.drop(columns=[FEATURE_COLUMNS[0]])
        return X.loc[:, list(reversed(FEATURE_COLUMNS))]

    for train, val in [(wrong(X_train), X_val), (X_train, wrong(X_val))]:
        with pytest.raises(ValueError, match="X.*[\u4e00-\u9fff]"):
            SpeedModel().fit(train, y_train, val, y_val)
    with pytest.raises(ValueError, match="X.*[\u4e00-\u9fff]"):
        trained.predict(wrong(synthetic[4]))


def test_tune_returns_grid_member(synthetic):
    from splash_model.model import tune

    grid = {"max_depth": [2, 3], "learning_rate": [0.05, 0.1], "n_estimators": [200]}
    best = tune(*synthetic[:4], grid=grid, seed=7)
    assert set(best) == set(grid)
    assert all(best[key] in grid[key] for key in grid)
    # Independently score native median Boosters: tuning must use validation MAE,
    # without sorting against the other quantiles or evaluating on held-out data.
    import itertools
    import xgboost as xgb
    train = xgb.DMatrix(synthetic[0], label=synthetic[1], nthread=1)
    val = xgb.DMatrix(synthetic[2], label=synthetic[3], nthread=1)
    scored = []
    for depth, rate in itertools.product(grid["max_depth"], grid["learning_rate"]):
        candidate = {"max_depth": depth, "learning_rate": rate, "n_estimators": 200}
        booster = xgb.train(
            {"max_depth": depth, "learning_rate": rate, "objective": "reg:quantileerror",
             "quantile_alpha": 0.5, "seed": 7, "nthread": 1, "tree_method": "hist"},
            train, num_boost_round=200, evals=[(val, "val")],
            early_stopping_rounds=50, verbose_eval=False)
        pred = booster.predict(val, iteration_range=(0, booster.best_iteration + 1))
        scored.append((np.mean(np.abs(pred - synthetic[3])), candidate))
    assert best == min(scored, key=lambda item: item[0])[1]
