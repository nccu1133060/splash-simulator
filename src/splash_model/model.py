"""使用本機 XGBoost 原生介面的分位數速度模型。"""

import json
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb

from splash_model.features import FEATURE_COLUMNS, assert_no_leakage


DEFAULT_PARAMS = {"max_depth": 3, "learning_rate": 0.05, "n_estimators": 2000}


def _check_columns(X):
    assert_no_leakage(X)
    if tuple(X.columns) != FEATURE_COLUMNS:
        raise ValueError("X 欄位與順序必須等於 FEATURE_COLUMNS")


def _train_quantile(train, val, params, seed, quantile):
    parameters = dict(params)
    rounds = parameters.pop("n_estimators")
    parameters.update(objective="reg:quantileerror", quantile_alpha=quantile,
                      seed=seed, nthread=1, tree_method="hist")
    return xgb.train(parameters, train, num_boost_round=rounds,
                     evals=[(val, "val")], early_stopping_rounds=50, verbose_eval=False)


class SpeedModel:
    def __init__(self, params: dict | None = None, seed: int = 0):
        self.params = {**DEFAULT_PARAMS, **(params or {})}
        self.seed = seed
        self.boosters = {}

    def fit(self, X_train, y_train, X_val, y_val):
        """僅以驗證集監控早停；不使用測試集。"""
        _check_columns(X_train)
        _check_columns(X_val)
        train = xgb.DMatrix(X_train, label=y_train, nthread=1)
        val = xgb.DMatrix(X_val, label=y_val, nthread=1)
        for name, quantile in (("q10", 0.1), ("q50", 0.5), ("q90", 0.9)):
            self.boosters[name] = _train_quantile(train, val, self.params, self.seed, quantile)
        return self

    def predict(self, X):
        _check_columns(X)
        matrix = xgb.DMatrix(X, nthread=1)
        values = [self.boosters[name].predict(
            matrix, iteration_range=(0, self.boosters[name].best_iteration + 1))
            for name in ("q10", "q50", "q90")]
        return pd.DataFrame(np.sort(np.column_stack(values), axis=1),
                            columns=["q10", "q50", "q90"], index=X.index)

    def save(self, directory):
        """以 JSON 儲存三個 Booster 與可重現訓練資訊。"""
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        for name, booster in self.boosters.items():
            booster.save_model(directory / f"{name}.json")
        meta = {"feature_columns": list(FEATURE_COLUMNS), "params": self.params,
                "seed": self.seed, "best_iteration": {
                    name: booster.best_iteration for name, booster in self.boosters.items()}}
        (directory / "meta.json").write_text(
            json.dumps(meta, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8")

    @classmethod
    def load(cls, directory):
        directory = Path(directory)
        meta = json.loads((directory / "meta.json").read_text(encoding="utf-8"))
        model = cls(meta["params"], meta["seed"])
        for name in ("q10", "q50", "q90"):
            booster = xgb.Booster(params={"nthread": 1})
            booster.load_model(directory / f"{name}.json")
            booster.set_attr(best_iteration=str(meta["best_iteration"][name]))
            model.boosters[name] = booster
        return model


def tune(X_train, y_train, X_val, y_val, *, grid=None, seed=0) -> dict:
    """只依中位數 Booster 的驗證 MAE 選參數；同分保留先列候選。"""
    _check_columns(X_train)
    _check_columns(X_val)
    if grid is None:
        grid = {"max_depth": [3, 5], "learning_rate": [0.05, 0.1],
                "n_estimators": [2000]}
    train = xgb.DMatrix(X_train, label=y_train, nthread=1)
    val = xgb.DMatrix(X_val, label=y_val, nthread=1)
    best, best_mae = None, float("inf")
    for values in product(*grid.values()):
        candidate = dict(zip(grid, values))
        booster = _train_quantile(train, val, {**DEFAULT_PARAMS, **candidate}, seed, 0.5)
        prediction = booster.predict(val, iteration_range=(0, booster.best_iteration + 1))
        mae = float(np.mean(np.abs(prediction - np.asarray(y_val))))
        if mae < best_mae:
            best, best_mae = candidate, mae
    if best is None:
        raise ValueError("grid 必須包含可評估的參數組合，y_val 必須可計算誤差")
    return best
