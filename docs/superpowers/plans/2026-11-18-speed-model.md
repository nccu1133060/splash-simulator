# 速度估計模型與回推比較 實作計畫

> **給執行者：** 本階段預設實作方式為「半自動協作」（使用者 2026-11-18 選定）：Codex 依 `~/.claude/skills/semi-auto-collab/BUILDER.md` 施工，Claude 審查與提交。一次一個 Task，每個 Task 一個分支，合併 `main` 後才開下一個。啟動方式：使用者說「半自動執行 Task N」。步驟使用 `- [ ]` 勾選。Codex 不提交，「提交」步驟由 Claude 在審查通過後執行。

**Goal：** 從模擬水漬的遮罩量測特徵，訓練「形狀 → 撞擊速度」模型（含不確定度），與物理公式基準線比較；再用估出的速度做含重力回推，完成直線法／真實速度／AI 速度三方法源頭比較。

**Architecture：** 新套件 `splash_model` 與 `splash_sim` 同倉庫，只單向依賴 `splash_sim`（飛行、特徵量測、設定）。管線：特徵表（只讀遮罩）→ 切分（以場景為單位）→ 基準線／XGBoost 分位數模型 → 評估 → 回推交會 → 報告。模組之間傳 `pandas.DataFrame` 與 dataclass。

**Tech Stack：** 既有（NumPy、SciPy、OpenCV、Pydantic、PyYAML、pytest）＋選用群組 `train`：`xgboost`、`pandas`。

**Spec：** `docs/superpowers/specs/2026-11-18-speed-model-design.md`

## Global Constraints

- 沿用前一份計畫的全部限制（中文路徑影像讀寫用 `splash_sim.imageio`、UTF-8、錯誤訊息繁中並指出參數名稱、單位後綴、不寫時間戳記到可重現輸出）。
- **防洩漏**：特徵欄位一律以 `meas_` 開頭，且必須列在 `splash_model.features.FEATURE_COLUMNS` 白名單。答案欄位只可作為目標（`speed_m_s`）或分組／回推比較用（`TRUTH_COLUMNS`），不得進入模型輸入。
- **切分**：以 `scene_index` 為單位；同一場景只能在一個集合。
- `splash_model` 不得被 `splash_sim` 匯入（單向依賴）。
- 訓練相依只放 `[dependency-groups] train`，`splash_sim` 的執行期相依不變。
- 可重現：同設定、同種子，`metrics.json` 逐位元組相同；XGBoost 固定 `random_state`、`n_jobs=1`、`tree_method="hist"`。
- 不需要 GPU；全流程在一般筆電 10 分鐘內。

## Review Focus

1. **答案欄位混入特徵**：在特徵表加入 `width_mm` 時，白名單測試必須失敗。→ Task 1 `test_feature_columns_whitelisted`。
2. **同場景液滴跨集合**：→ Task 2 `test_split_disjoint_by_scene`。
3. **W/L 量測略大於 1 或公式無解**：`arcsin` 前夾到 ≤ 1；反解超出範圍回傳 `nan` 並在評估中計數，不可丟例外中斷整批。→ Task 2 `test_invert_out_of_range_is_nan`。
4. **方向接近平行或只有 1–2 滴的交會**：不可回傳看似正常的座標；回傳 `ok=False` 與原因。→ Task 4 `test_degenerate_lines_flagged`。
5. **中文路徑**：資料集與輸出資料夾含中文時 CLI 正常。→ Task 5 `test_cli_end_to_end`（`tmp_path/"中文"`）。

---

## 檔案結構

```
configs/model/provisional_train.yaml     訓練資料集的設定快照（seed 20261112，來源見檔頭註解）
configs/model/independent_test.yaml      同規則、新種子 20261118、30 張
configs/model/rule_perturbed.yaml        規則擾動、新種子 20261119、30 張
src/splash_sim/features.py               擴充：周長、實心度、粗糙度
src/splash_model/__init__.py
src/splash_model/features.py             每滴量測、特徵表、白名單
src/splash_model/baseline.py             Laan 2014 正算／反解、物理基準線 B0、常數基準線 B1
src/splash_model/split.py                以場景切分
src/splash_model/model.py                XGBoost 分位數模型、存讀檔
src/splash_model/metrics.py              速度指標、分組
src/splash_model/backtrack.py            撞擊速度向量、直線交會、軌跡交會
src/splash_model/report.py               metrics.json → report.md
src/splash_model/cli.py                  splash-model 指令
tests/test_model_*.py
```

## Task 分派總表

| Task | 名稱 | 負責人 | 分支 | 檔案範圍 | 網路 |
|---|---|---|---|---|---|
| 1 | 套件骨架與特徵表 | Codex | `task-m1-features` | `pyproject.toml`（只加 `train` 群組）、`uv.lock`、`.gitignore`（加 `runs/`）、`configs/model/*.yaml`、`src/splash_sim/features.py`、`tests/test_features.py`（只新增測試）、`src/splash_model/{__init__,features}.py`、`tests/test_model_features.py` | 是（`uv sync --group train`） |
| 2 | 物理基準線與切分 | Codex | `task-m2-baseline-split` | `src/splash_model/{baseline,split}.py`、`tests/test_model_{baseline,split}.py` | 否 |
| 3 | 速度模型與指標 | Codex | `task-m3-model` | `src/splash_model/{model,metrics}.py`、`tests/test_model_{model,metrics}.py` | 否 |
| 4 | 回推與交會 | Codex | `task-m4-backtrack` | `src/splash_model/backtrack.py`、`tests/test_model_backtrack.py` | 否 |
| 5 | CLI、報告、README | Codex | `task-m5-cli-report` | `src/splash_model/{cli,report}.py`、`pyproject.toml`（只加 `[project.scripts]` 一行）、`README.md`（新增「速度模型」段）、`tests/test_model_cli.py` | 否 |
| 6 | 實際實驗與結果報告 | Claude | `main`（只產生 ignored 資料與 HANDOFF） | `datasets/`、`runs/`（皆忽略）、`HANDOFF.md` | 否 |

測試指令：局部 `uv run --group train pytest tests/<檔名> -q`｜全套 `uv run --group train pytest -q`。無 lint／型別關卡。
環境注意：本機 `.venv` 指向的暫存 Python 已被清除，Task 1 先 `uv sync --group train` 重建（Codex 沙盒沿用 HANDOFF 的 `UV_CACHE_DIR`／`UV_PYTHON_INSTALL_DIR`）。

---

### Task 1：套件骨架與特徵表

**Files：**
- Create：`src/splash_model/__init__.py`、`src/splash_model/features.py`、`configs/model/{provisional_train,independent_test,rule_perturbed}.yaml`、`tests/test_model_features.py`
- Modify：`src/splash_sim/features.py`、`tests/test_features.py`（只新增）、`pyproject.toml`、`uv.lock`、`.gitignore`

**Interfaces：**
- Consumes：`splash_sim.features.measure_stain`、`splash_sim.imageio.read_png`、`splash_sim.dataset.generate_dataset`／`simulate_single_drop`、`splash_sim.config.load_config`。
- Produces：
  - `StainFeatures` 新增欄位（加在既有欄位之後）：`perimeter_mm: float`、`solidity: float`（輪廓面積／凸包面積）、`roughness: float`（輪廓周長／擬合橢圓周長，Ramanujan 近似）。三者都用 `cv2.approxPolyDP(contour, 1.0, True)` 拉直像素階梯後的輪廓計算（使用者 2026-11-18 核可；Claude 試算：10 mm 圓周長誤差 6.4%→0.6%、實心度 0.989→1.000，0.3 mm 短毛刺粗糙度仍為 1.13）；橢圓擬合仍用原始輪廓。既有欄位與行為不變。
  - `splash_sim.features.measure_body(mask, *, kernel_frac: float = 0.25) -> StainFeatures`（新增，使用者 2026-11-18 核可）：先以原始輪廓 `fitEllipse` 量出外框寬度 w_raw（px），再以直徑 `k = max(3, round(kernel_frac·w_raw) 取奇數)` 的橢圓結構元素做 `cv2.MORPH_OPEN`，削去細長毛刺與尾巴，對結果呼叫 `measure_stain`。開運算後為空或量測失敗時丟 `ValueError`（由呼叫端歸為 unmeasurable）。Claude 試算（default 與暫定設定，v ∈ {2, 4} m/s × α ∈ {30, 60, 90}°，無干擾、jitter 0）：主體寬度誤差 ≤ 0.6%、W/L 對 sin α 誤差 ≤ 1.3%；原始輪廓則寬度最多 +28%、W/L 最多 −9.5%。已知限制：α < 約 15° 的極扁水漬兩端會被輕微削去。
  - `splash_model.features.FEATURE_COLUMNS: tuple[str, ...]`＝`meas_area_mm2, meas_width_mm, meas_length_mm, meas_aspect_ratio, meas_impact_angle_deg, meas_outer_width_mm, meas_outer_length_mm, meas_spine_count, meas_perimeter_mm, meas_solidity, meas_roughness, meas_satellite_count, meas_satellite_area_mm2, meas_satellite_max_dist_mm`。`meas_width_mm`、`meas_length_mm`、`meas_aspect_ratio` 取自 `measure_body`（主體）；`meas_impact_angle_deg = degrees(arcsin(min(主體 aspect, 1)))`；`meas_outer_width_mm`／`meas_outer_length_mm` 取自原始 `measure_stain`（含毛刺尾巴的外框，毛刺長度本身是速度線索）；面積、毛刺數、周長、實心度、粗糙度取自原始 `measure_stain`。
  - `OBSERVED_COLUMNS = ("obs_direction_deg", "obs_center_mm_x", "obs_center_mm_y")`：同樣只由遮罩量測（主體 `measure_body.direction_deg`、主體遮罩重心換算 mm，經 `splash_sim.geometry.px_to_mm`），**不送進速度模型**，供 M4／M5 回推使用。
  - `KEY_COLUMNS = ("scene_index", "drop_id")`；`TARGET_COLUMN = "speed_m_s"`；`TRUTH_COLUMNS = ("impact_angle_deg", "direction_deg", "center_mm_x", "center_mm_y", "impact_velocity_m_s_x", "impact_velocity_m_s_y", "impact_velocity_m_s_z", "diameter_mm")`。
  - `measure_drop(instance_mask, satellite_mask, instance_id: int, bbox_px: tuple[int,int,int,int], *, margin_px: int = 60) -> dict[str, float]`：只用遮罩。主體：在 `bbox_px` 往外擴 `margin_px`（裁到畫布內）的範圍取 `instance_mask == instance_id` 量測。衛星：取**整張** `satellite_mask == instance_id` 的全部連通區塊（衛星可能在主體外框之外；可用 `scipy.ndimage.find_objects` 先取該編號外框加速），計數、總面積，距離為區塊重心到主體重心的最大值；無衛星時三者皆為 0。回傳 `FEATURE_COLUMNS` 與 `OBSERVED_COLUMNS` 的全部鍵。
  - `build_feature_table(dataset_dir: Path) -> pandas.DataFrame`：欄位依序為 `KEY_COLUMNS + FEATURE_COLUMNS + OBSERVED_COLUMNS + (TARGET_COLUMN,) + TRUTH_COLUMNS`，依 `(scene_index, drop_id)` 排序。排除規則直接讀答案 JSON 的 `truncated` 與遮罩（不讀 `candidate_index.csv`），每滴只歸入一類，優先序 `truncated` → `occluded`（遮罩為空）→ `unmeasurable`（輪廓不足 5 點等 `measure_stain` 的 `ValueError`）；計數於 `df.attrs["excluded"]`（dict 三鍵皆必有）。表中同時保存答案欄，防洩漏只檢查實際送進模型的 `X`（Step 10）。
- 設定檔：`provisional_train.yaml` 內容等於 `datasets/expanded_public_trial_2500_20261111-105236/config_snapshot.yaml`，檔頭加中文註解說明來源與「暫定、非實拍校正」。另兩份以它為底，只改：`independent_test.yaml` → `seed: 20261118`、`output.n_scenes: 30`、`output.name: independent_test`；`rule_perturbed.yaml` → `seed: 20261119`、`n_scenes: 30`、`name: rule_perturbed`、`impact.spread_a: 1.05`、`impact.angle_bias_deg: 3.0`、`impact.spine_a: 0.1443`、`impact.spine_length_frac: [0.1, 0.35]`；每個改動加註「規則擾動，Claude 判斷，非文獻值」。

- [ ] **Step 1：相依**：`pyproject.toml` 加 `[dependency-groups] train = ["xgboost", "pandas"]`；`uv sync --group train`；`.gitignore` 加 `runs/`。執行既有全套確認仍全綠（基準）。
- [ ] **Step 2：寫失敗測試 `tests/test_features.py::test_new_shape_fields_on_circle`**：直徑 10 mm 的實心圓遮罩 → `solidity ≥ 0.99`、`|roughness − 1| ≤ 0.03`、`perimeter_mm` 與 π·10 相對誤差 ≤ 3%。
- [ ] **Step 3：執行 → 實作新欄位 → 執行**，先 FAIL 後 PASS；再跑 `tests/test_features.py` 全檔確認既有測試不變。
- [ ] **Step 3b：寫失敗測試 `test_shape_fields_size_invariant`**：直徑 5、10、15 mm 圓的 `roughness` 皆在 1 ± 0.03、`solidity ≥ 0.99`。執行 → 調整（若需要）→ 執行。
- [ ] **Step 4：寫失敗測試 `test_spines_raise_roughness`**：沿用 `test_render.geometry`，12 根毛刺的水漬 `roughness` 大於無毛刺者。
- [ ] **Step 5：執行 → 調整（若需要）→ 執行。**
- [ ] **Step 6：寫失敗測試 `tests/test_features.py::test_measure_body_matches_clean_ellipse`**：無毛刺無尾巴的橢圓（α ∈ {30, 60, 90}°），`measure_body` 與 `measure_stain` 的寬、長差 ≤ 1%（削毛刺不傷乾淨主體）。執行 → 實作 `measure_body` → 執行。
- [ ] **Step 6a：寫失敗測試 `tests/test_model_features.py::test_measure_drop_matches_geometry`**：設定分別用 `default_config()` 與 `configs/model/provisional_train.yaml` 的內容（可先建立該設定檔再寫此測試；兩者皆關閉全部 augment、`impact.jitter_frac=0`，以 `model_dump`→`SimConfig.model_validate` 修改），速度 {2, 4} m/s × 撞擊角 {30, 60, 90}°，`simulate_single_drop`；`meas_width_mm` 與答案 `width_mm` 相對誤差 ≤ 3%；`|meas_aspect_ratio − sin α| ≤ 0.03`；外框兩欄皆為有限正值，且只在 `default_config()`（長毛刺）案例斷言 `meas_outer_width_mm > meas_width_mm`（2026-11-18 Claude 修正：暫定設定下尾巴使原始擬合變窄，外框寬度可小於主體約 2%，原「一律 ≥」不成立）。答案衛星數 > 0 時 `1 ≤ meas_satellite_count ≤ 答案衛星數`（可見連通區塊；衛星互相重疊時會少於生成顆數，此為定義而非缺陷）。
- [ ] **Step 6b：寫失敗測試 `test_satellites_separable_exact`**：以 `test_render.geometry` 放 3 顆彼此相距 ≥ 3 mm、離主體 ≥ 3 mm 的衛星，`meas_satellite_count == 3`、`meas_satellite_max_dist_mm` 與設定距離差 ≤ 0.5 mm、總面積 > 0。
- [ ] **Step 7：執行 → 實作 `measure_drop`（主體用 `measure_body`、外框與形狀細節用 `measure_stain`；`obs_direction_deg` 取主體方向）→ 執行 6a、6b。**
- [ ] **Step 8：寫失敗測試 `test_feature_table_layout`**：`generate_dataset` 於 `tmp_path/"中文"` 產 2 張場景 → `build_feature_table` 欄位順序等於規格；列數 + `excluded` 三類加總 = 答案總滴數；`excluded["truncated"]` 等於答案中 `truncated=True` 的滴數；`obs_center_mm_*` 與答案 `center_mm` 差 ≤ 1 mm（無遮蔽液滴）。
- [ ] **Step 9：執行 → 實作 `build_feature_table` → 執行。**
- [ ] **Step 10：寫失敗測試 `test_feature_columns_whitelisted`**：公開函式 `assert_no_leakage(X: DataFrame)` 檢查模型輸入：欄位必須全部以 `meas_` 開頭且屬於 `FEATURE_COLUMNS`，否則丟中文 `ValueError` 並列出違規欄名。測試：正常特徵通過；加入 `width_mm`、`spine_count`、`speed_m_s` 或 `obs_direction_deg` 任一欄都失敗。另斷言 `FEATURE_COLUMNS` 與 `TRUTH_COLUMNS ∪ {TARGET_COLUMN}` 交集為空。Task 3 訓練前呼叫此函式。
- [ ] **Step 11：執行 → 實作 `assert_no_leakage` → 執行。**
- [ ] **Step 12：寫失敗測試 `test_feature_table_deterministic`**：同一資料集建兩次，`DataFrame.equals` 為真。執行 → 修正（若需要）→ 執行。
- [ ] **Step 13：寫失敗測試 `test_model_configs_load`**：三份 `configs/model/*.yaml` 皆可 `load_config`；`independent_test` 與 `provisional_train` 只差 seed／n_scenes／name；`rule_perturbed` 只差規格列出的欄位（遞迴比對）。執行 → 新增設定檔 → 執行。
- [ ] **Step 14：全套** `uv run --group train pytest -q`，預期全部 PASS。
- [ ] **Step 15：提交**（Claude 審查後）：`feat: 速度模型特徵表與防洩漏白名單`

---

### Task 2：物理基準線與切分

**Interfaces：**
- Consumes：`splash_sim.config.LiquidConfig`、Task 1 特徵表。
- Produces：
  - `laan_spread_factor(normal_speed_m_s: float, diameter_mm: float, liquid, spread_a: float) -> float`：與 `splash_sim.impact.literature_v1` 同一公式（不含 jitter）。
  - `invert_normal_speed(spread_factor: float, diameter_mm: float, liquid, spread_a: float, *, bounds_m_s=(0.01, 30.0)) -> float`：`scipy.optimize.brentq`；無解回傳 `nan`。
  - `physics_baseline(df, *, diameter_mm: float, liquid, spread_a: float) -> numpy.ndarray`：`ξ = meas_width_mm / diameter_mm` → `v_n`（`invert_normal_speed`）；`sin α = clip(meas_aspect_ratio, 0, 1)`（Review Focus 3，略大於 1 當 90°）→ `v = v_n / sin α`。`sin α ≤ 0`、寬度非正或非有限、反解無解時該列為 `nan`，不丟例外；回傳長度等於 `len(df)`。（2026-11-25 Claude 修訂：原寫用 `meas_impact_angle_deg`，與 Step 5 測長寬比夾值不一致；兩者數學上等價。）
  - `constant_baseline(train_speeds) -> Callable[[DataFrame], ndarray]`（訓練集平均）。
  - `split_scenes(scene_ids, *, fractions=(0.70, 0.15, 0.15), seed: int) -> dict[str, list[int]]`，鍵 `train`／`val`／`test`，各集合排序；每集合至少 1 個場景，否則丟中文 `ValueError`。
  - `apply_split(df, split) -> dict[str, DataFrame]`。

- [ ] **Step 1：寫失敗測試 `test_spread_matches_simulator`**：v_n ∈ {1, 2, 4} m/s，`laan_spread_factor` 與 `literature_v1`（`jitter_frac=0`）回傳的 `spread_factor` 相對誤差 < 1e-9。執行 → 實作 → 執行。
- [ ] **Step 2：寫失敗測試 `test_invert_roundtrip`**：正算後反解，誤差 < 1e-6 m/s。執行 → 實作 → 執行。
- [ ] **Step 3：寫失敗測試 `test_invert_out_of_range_is_nan`**：ξ = 0.01 與 ξ = 100 回傳 `nan`（2026-11-25 修訂：原 0.1 對應約 0.020 m/s，仍在範圍內有解；範圍 0.01–30 m/s 對應 ξ 約 0.0507–9.21），不丟例外。執行 → 實作 → 執行。
- [ ] **Step 4：寫失敗測試 `test_physics_baseline_on_clean_single_drops`**（spec 驗收 3）：速度 {2, 4} m/s × 撞擊角 {30, 60, 90}°，augment 關閉、`jitter_frac=0`、毛刺依暫定設定；`simulate_single_drop` → Task 1 `measure_drop` → B0，相對誤差 < 5%。**若因毛刺使量測 W 偏大而不通過，停下回報量測數字，不放寬門檻。**執行 → 實作 → 執行。
- [ ] **Step 5：寫失敗測試 `test_aspect_above_one_clipped`**：其餘欄位正常、`meas_aspect_ratio = 1.02` 時 B0 回傳有限值且等於同列 `meas_aspect_ratio = 1.0` 的結果（當作 90°）；另一列 `meas_aspect_ratio = 0` 或 `meas_width_mm = 0` 回傳 `nan`，整批不丟例外。執行 → 實作 → 執行。
- [ ] **Step 6：寫失敗測試 `test_split_disjoint_by_scene`**：100 個場景編號 → 三集合互斥、聯集完整、比例誤差 ≤ 1 個場景；`apply_split` 後每個 DataFrame 的 `scene_index` 只屬於該集合。執行 → 實作 → 執行。
- [ ] **Step 7：寫失敗測試 `test_split_deterministic_and_seeded`**：同種子相同、不同種子不同。執行 → 實作 → 執行。
- [ ] **Step 8：寫失敗測試 `test_split_too_few_scenes`**：2 個場景 → 中文 `ValueError` 提到 `fractions`。執行 → 實作 → 執行。
- [ ] **Step 9：全套**，預期 PASS。
- [ ] **Step 10：提交**：`feat: 物理反解基準線與場景切分`

---

### Task 3：速度模型與指標

**Interfaces：**
- Produces：
  - `metrics.speed_metrics(y_true, q10, q50, q90, impact_angle_deg) -> dict`：鍵 `n`、`n_nan`、`mae_m_s`、`median_rel_err`、`coverage_80`（`q10 ≤ y ≤ q90` 比例）、`groups`：`vertical`（α ≥ 75°）、`oblique`（α < 75°）、`speed_low`（< 2.5）、`speed_mid`（2.5–4）、`speed_high`（≥ 4），各含 `n`、`mae_m_s`、`median_rel_err`。點估計為 `nan` 的列不計入誤差、計入 `n_nan`。無區間的方法（B0、B1）傳 `q10 = q90 = None`，`coverage_80` 為 `None`。數值四捨五入至 6 位。
  - `model.SpeedModel(params: dict | None = None, seed: int = 0)`：`fit(X_train, y_train, X_val, y_val) -> SpeedModel`（三個 `XGBRegressor(objective="reg:quantileerror", quantile_alpha=q)`，`early_stopping_rounds=50`，驗證集監控）；`predict(X) -> DataFrame[q10, q50, q90]`（逐列排序保證單調）；`save(dir)`／`classmethod load(dir)`（每個分位數一個 `.json` ＋ `meta.json` 存特徵欄位順序與參數）。
  - `model.tune(X_train, y_train, X_val, y_val, *, grid, seed) -> dict`：在 `grid`（預設 `max_depth ∈ {3, 5}`、`learning_rate ∈ {0.05, 0.1}`、`n_estimators=2000` 配早停）以中位數模型驗證 MAE 選最佳。
  - `fit` 前呼叫 Task 1 `assert_no_leakage`；`X` 欄位必須等於 `FEATURE_COLUMNS`，否則中文 `ValueError`。

- [ ] **Step 1：寫失敗測試 `test_speed_metrics_hand_computed`**：4 筆手算例（含 1 筆 `nan`、垂直與斜向各半），斷言每個鍵。執行 → 實作 → 執行。
- [ ] **Step 2：寫失敗測試 `test_speed_metrics_without_interval`**：`coverage_80 is None`。執行 → 實作 → 執行。
- [ ] **Step 3：寫失敗測試 `test_model_beats_constant_on_synthetic`**：人造特徵 `y = 2 + 0.3·meas_width_mm + 雜訊`（其餘欄位為雜訊）600 列，模型中位數 MAE < 常數基準線 MAE 的 50%。執行 → 實作 `SpeedModel` → 執行。
- [ ] **Step 4：寫失敗測試 `test_quantiles_monotone_and_cover`**：同人造資料，每列 `q10 ≤ q50 ≤ q90`；保留集 `coverage_80 ∈ [0.6, 0.95]`。執行 → 調整 → 執行。
- [ ] **Step 5：寫失敗測試 `test_save_load_identical`**：存到 `tmp_path/"中文"`，讀回預測 `array_equal`。執行 → 實作 → 執行。
- [ ] **Step 6：寫失敗測試 `test_fit_deterministic`**：同種子訓練兩次預測 `array_equal`。執行 → 調整 → 執行。
- [ ] **Step 7：寫失敗測試 `test_fit_rejects_wrong_columns`**：多一欄 `width_mm` → 中文 `ValueError`。執行 → 實作 → 執行。
- [ ] **Step 8：寫失敗測試 `test_tune_returns_grid_member`**：回傳參數屬於 grid。執行 → 實作 → 執行。
- [ ] **Step 9：全套**，預期 PASS。
- [ ] **Step 10：提交**：`feat: XGBoost 分位數速度模型與評估指標`

---

### Task 4：回推與交會

**Interfaces：**
- Consumes：`splash_sim.flight.propagate`、`fly_to_plane`、`AirConfig`、`LiquidConfig`。
- Produces（座標 mm 輸入輸出，內部 SI）：
  - `impact_velocity(direction_deg, impact_angle_deg, speed_m_s) -> ndarray(3)`：水平分量指向 γ，`z < 0`。
  - `@dataclass(frozen=True) class SourceEstimate: xyz_mm: tuple[float,float,float] | None; ok: bool; reason: str; condition_number: float; n_drops: int`。
  - `straight_line_source(points_mm, direction_deg, impact_angle_deg, weights=None) -> SourceEstimate`：每滴自撞擊點沿 −速度方向（向上）的直線，加權最小平方最近點（Joris 2015 形式）。`n < 3` 或正規方程條件數 > 1e8 → `ok=False`，`reason` 為中文。
  - `trajectory_source(points_mm, velocities_m_s, *, diameter_mm, liquid, air, weights=None, max_back_time_s=1.0, max_height_mm=2000.0) -> SourceEstimate`：每滴以 `propagate` 負時長往回取樣（0.5 ms 間隔，到 `max_back_time_s` 或高於 `max_height_mm` 為止）成折線；以 `scipy.optimize.least_squares` 最小化加權「點到各折線最近距離」平方和，初值為直線法結果（直線法失敗時用撞擊點平均上方 200 mm）。`air.drag_enabled=False` 即「只含重力」版本（決策 1B）。
  - `uncertainty_weights(q10, q90) -> ndarray`：`1 / max(q90 − q10, 0.05)²`，再正規化為平均 1。

- [ ] **Step 1：寫失敗測試 `test_impact_velocity_components`**：γ = 90°、α = 30°、v = 2 → (0, 1.732, −1.0)，誤差 < 1e-9。執行 → 實作 → 執行。
- [ ] **Step 2：寫失敗測試 `test_straight_lines_exact_intersection`**：由已知點 (100, 150, 250) mm 反向造 6 條直線，回推誤差 < 1e-6 mm。執行 → 實作 → 執行。
- [ ] **Step 3：寫失敗測試 `test_degenerate_lines_flagged`**：只有 2 滴 → `ok=False`；6 條平行線 → `ok=False`，`reason` 非空。執行 → 實作 → 執行。
- [ ] **Step 4：寫失敗測試 `test_trajectory_source_recovers_truth`**（spec 驗收 4）：源頭 (105, 148, 200) mm，6 個不同發射速度，用 `fly_to_plane` 得撞擊點與撞擊速度，含阻力 → `trajectory_source` 誤差 < 1 mm。執行 → 實作 → 執行。
- [ ] **Step 5：寫失敗測試 `test_gravity_only_variant`**：同上但 `drag_enabled=False` 造資料與回推，誤差 < 1 mm。執行 → 調整 → 執行。
- [ ] **Step 6：寫失敗測試 `test_straight_line_overestimates_height`**：同 Step 4 資料改用直線法，Z 誤差 > 10 mm 且 Z 偏高（重現上游「直線法高估高度」；若不偏高，停下回報數字）。執行 → 確認 → 執行。
- [ ] **Step 7：寫失敗測試 `test_low_weight_outlier_has_less_effect`**：加入一滴速度錯誤 50% 的液滴；權重 0.01 時的源頭誤差小於權重 1 時。執行 → 實作權重 → 執行。
- [ ] **Step 8：寫失敗測試 `test_uncertainty_weights`**：區間越寬權重越小、平均為 1、零寬區間不爆掉。執行 → 實作 → 執行。
- [ ] **Step 9：全套**，預期 PASS。
- [ ] **Step 10：提交**：`feat: 含重力回推與多滴交會`

---

### Task 5：CLI、報告、README

**Interfaces：**
- 指令（`splash-model = "splash_model.cli:main"`）：
  - `splash-model features --dataset D --out F.csv`
  - `splash-model fit --dataset D --out RUN_DIR [--seed 0] [--config C]`：建特徵表 → `split_scenes` → `tune` → 訓練 → 寫 `RUN_DIR/{model/, split.json, features_train.csv, metrics.json}`；`metrics.json["internal"]` 含 val／test 上 `model`、`b0`、`b1` 三法的 `speed_metrics`。`--config` 預設讀資料集內 `config_snapshot.yaml`，取得滴徑、物性與 `spread_a` 供 B0。
  - `splash-model evaluate --run RUN_DIR --dataset D --label NAME`：整個資料集當測試，結果寫入 `metrics.json["datasets"][NAME]`，同時寫 `predictions_NAME.csv`。
  - `splash-model backtrack --run RUN_DIR --dataset D --label NAME`：每場景以候選液滴跑四種：`line`（直線法）、`true_speed`、`model_speed`（含不確定度權重）、`model_speed_gravity_only`；撞擊點取 `obs_center_mm_*`、方向 γ 取 `obs_direction_deg`、α 取 `meas_impact_angle_deg`，**γ 的 180° 正負號以答案 `direction_deg` 決定**（spec 非目標）；寫 `metrics.json["backtrack"][NAME]`：各法 `n_ok`、`n_failed`、XY／Z 誤差中位數與 P90（mm）、Z 偏差中位數；逐場景結果寫 `backtrack_NAME.csv`。
  - `splash-model report --run RUN_DIR`：由 `metrics.json` 產 `report.md`，含表格與 spec 1.1 的限制說明原文。
- 錯誤：資料集不存在、缺 `index.csv`、模型資料夾不完整 → 中文訊息、exit 2。
- 寫 `metrics.json` 用 `json.dumps(sort_keys=True, ensure_ascii=False, indent=2)`；不寫時間與絕對路徑。

- [ ] **Step 1：寫失敗測試 `test_cli_features`**：小資料集（`generate_dataset` 4 張，`tmp_path/"中文"`）→ 輸出 CSV 欄位等於 Task 1 規格。執行 → 實作 → 執行。
- [ ] **Step 2：寫失敗測試 `test_cli_fit_writes_run`**：`fit` 後檔案齊全，`metrics.json["internal"]` 具 val／test × 三法；切分可讀回且互斥。執行 → 實作（測試可用 `--fractions 0.5,0.25,0.25` 與小 grid 參數加速）→ 執行。
- [ ] **Step 3：寫失敗測試 `test_cli_evaluate_and_backtrack`**：另產 2 張場景當獨立集，`evaluate`、`backtrack` 後 `metrics.json` 具對應鍵；`true_speed` 的 Z 誤差中位數小於 `line`（在模擬資料上應成立；若不成立停下回報）。執行 → 實作 → 執行。
- [ ] **Step 4：寫失敗測試 `test_cli_deterministic`**：同設定跑兩次 `fit`＋`evaluate`，`metrics.json` 位元組相同。執行 → 修正 → 執行。
- [ ] **Step 5：寫失敗測試 `test_cli_missing_dataset_chinese_error`**：exit 2，stderr 含「資料集」與路徑參數名稱。執行 → 實作 → 執行。
- [ ] **Step 6：寫失敗測試 `test_report_contains_sections`**：`report.md` 含「速度估計」「回推比較」「限制」三節與每個資料集名稱。執行 → 實作 → 執行。
- [ ] **Step 7：README**：新增「速度模型」段：安裝 `uv sync --group train`、四個指令範例、輸出說明、限制（模擬成績≠實拍成績、180° 用答案）。
- [ ] **Step 8：全套**，預期 PASS。
- [ ] **Step 9：提交**：`feat: splash-model 指令與實驗報告`

---

### Task 6：實際實驗與結果報告（Claude）

不改程式；所有產物在 ignored 的 `datasets/`、`runs/`。

- [ ] **Step 1**：`uv run splash-sim generate --config configs/model/independent_test.yaml`、`--config configs/model/rule_perturbed.yaml`，驗收張數、滴數、答案一致性（同前輪方法）。
- [ ] **Step 2**：`splash-model fit --dataset datasets/expanded_public_trial_2500_20261111-105236 --out runs/speed_v1 --seed 0`。
- [ ] **Step 3**：對兩個新資料集 `evaluate` 與 `backtrack`，標籤 `independent`、`perturbed`；再 `report`。
- [ ] **Step 4**：重跑一次 `fit`＋`evaluate` 到另一資料夾，比對 `metrics.json` 雜湊（可重現驗收 5）；記錄總耗時（驗收 7）。
- [ ] **Step 5**：抽查 10 筆預測誤差最大的切片，實際看圖判斷原因（重疊、量測失敗、規則極端）。
- [ ] **Step 6**：向使用者報告：三法速度誤差、垂直／斜向、規則擾動退化幅度、三方法回推 XY／Z 誤差，並標明「模擬成績」。更新 `HANDOFF.md`。

## Spec 對照

| Spec 段落 | Task |
|---|---|
| 4.1 特徵（只量遮罩） | 1 |
| 4.2 B0、B1、主模型 | 2、3 |
| 4.3 切分與三種測試集 | 1（設定檔）、2、6 |
| 4.4 指標與分組 | 3、5 |
| 第 5 節 回推比較 | 4、5 |
| 第 6 節驗收 1–7 | 1（1）、2（2、3）、4（4）、5（5、6）、6（5、7 實測） |
