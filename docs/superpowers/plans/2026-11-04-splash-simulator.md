# 飛濺溯源模擬器 實作計畫

> **給執行者：** 本專案預設實作方式為「半自動協作」：Codex 依 `~/.claude/skills/semi-auto-collab/BUILDER.md` 施工，Claude 審查與提交。一次一個 Task，每個 Task 一個分支，合併 `main` 後才開下一個。步驟使用 `- [ ]` 勾選。Codex 不提交，下列「提交」步驟由 Claude 在審查通過後執行。

**Goal：** 做出可由組員調參數、可重現的 Python 模擬器，產生帶標準答案的 A4 水漬影像資料集（場景圖、實例遮罩、單滴切片、JSON 答案、CSV 總表）。

**Architecture：** 管線分成六個獨立模組：設定 → 場景取樣 → 飛行（ODE 積分）→ 撞擊成形（經驗公式，輸出幾何描述）→ 繪製（幾何 → 像素與遮罩）→ 影像干擾；最後由資料集模組寫檔，CLI 與 Python API 是兩個入口。模組之間只傳 dataclass，不傳像素以外的隱含狀態。

**Tech Stack：** Python ≥ 3.11、uv、NumPy、SciPy（`solve_ivp`）、OpenCV（`opencv-python-headless`）、Pydantic v2、PyYAML、pytest。

**Spec：** `docs/superpowers/specs/2026-10-21-simulator-design.md`

## Global Constraints

- Python `>=3.11`；Windows 與 macOS 都要能跑；不需要 GPU。
- 執行期相依只有：`numpy`、`scipy`、`opencv-python-headless`、`pydantic>=2`、`pyyaml`。開發相依：`pytest`。全部在 Task 1 一次宣告並鎖定 `uv.lock`，之後的 Task 不改相依。
- 座標：A4 左下角為原點，x ∈ [0, 210] mm（短邊），y ∈ [0, 297] mm（長邊），z 垂直紙面向上。內部計算用 SI 單位。
- 影像：2100 × 2970 px（寬 × 高），10 px = 1 mm。像素換算統一透過 `splash_sim/geometry.py`。
- 設定欄位名稱帶單位後綴：`_m`、`_mm`、`_m_s`、`_deg`、`_s`、`_px`。
- 方向角 γ：撞擊速度在紙面的投影方向，從 +x 軸逆時針量，範圍 [0, 360)。撞擊角 α：速度與紙面的夾角，範圍 (0, 90]°。
- 所有面向使用者的錯誤訊息用繁體中文，並指出欄位或參數名稱。
- 每條形狀規則在程式 docstring 和 `default.yaml` 註解中都要註明出處，以及狀態「已有文獻」「待核對原文」或「待實拍校正」。
- 讀寫檔案一律明確指定 UTF-8；影像讀寫一律用 `cv2.imencode`／`cv2.imdecode` 搭配 `Path.write_bytes`／`read_bytes`（`cv2.imwrite` 在 Windows 的中文路徑會失敗，專案路徑本身就含中文）。
- 可重現：同一份設定與同一程式版本產生的檔案逐位元組相同；輸出檔案內不得寫入時間戳記。

## Review Focus

1. **專案路徑含中文（Windows）**：寫 PNG 到 `tmp_path / "中文資料夾"` 要成功，讀回來內容相同。→ Task 3 `test_png_roundtrip_non_ascii_path`。
2. **YAML 含中文註解、系統編碼為 cp950**：`load_config` 用 UTF-8 讀，含中文註解的檔案能正常載入。→ Task 1 `test_load_config_utf8_comments`。
3. **源頭太遠，落在紙上的液滴始終不足 9 滴**：要在重抽上限內停止，丟出中文的 `SceneSamplingError` 並建議調整的欄位，不能無限迴圈。→ Task 4 `test_spray_gives_up_with_chinese_error`。
4. **水漬靠近或超出紙邊**：繪製時裁到畫布內不報錯；切片超出畫布的部分用紙色補齊；水漬超出切片時 `truncated=True`。→ Task 3 `test_render_stain_partly_off_canvas`、Task 4 `test_crop_near_edge_padded_and_flagged`。
5. **撞擊角非常淺（< `min_impact_angle_deg`）**：長度會暴增，不能產生這種水漬，而是記入 `discarded["too_shallow"]`。→ Task 4 `test_spray_discards_shallow_impacts`。

---

## 檔案結構

```
pyproject.toml / uv.lock / README.md
configs/default.yaml                       完整預設設定（中文註解、出處）
configs/vertical_drop_calibration.yaml     垂直滴落校正範例
configs/single_drop_training.yaml          單滴訓練切片範例
configs/variable_droplet.yaml              液滴大小隨機範例
src/splash_sim/__init__.py                 公開 API 與 __version__
src/splash_sim/config.py                   Pydantic 設定模型、load_config、ConfigError
src/splash_sim/geometry.py                 A4 常數、mm↔px 換算、角度工具
src/splash_sim/flight.py                   飛行 ODE、阻力係數
src/splash_sim/impact.py                   StainGeometry、規則組註冊、literature_v1
src/splash_sim/render.py                   幾何 → 影像與實例遮罩
src/splash_sim/features.py                 單滴特徵量測（測試與日後比對工具共用）
src/splash_sim/augment.py                  影像干擾
src/splash_sim/imageio.py                  支援中文路徑的 PNG 讀寫
src/splash_sim/scene.py                    場景取樣（三種模式）
src/splash_sim/dataset.py                  simulate_scene、裁切、寫出資料集
src/splash_sim/yolo.py                     YOLOv8-seg 標註匯出
src/splash_sim/cli.py                      splash-sim 指令
tests/test_*.py                            每個模組一個測試檔
```

## Task 分派總表

| Task | 名稱 | 負責人 | 分支 | 檔案範圍 | 網路 |
|---|---|---|---|---|---|
| 1 | 骨架、設定與飛行物理 | Codex | `task-1-config-flight` | `pyproject.toml`、`uv.lock`、`.python-version`、`src/splash_sim/{__init__,config,geometry,flight}.py`、`configs/default.yaml`、`tests/test_{config,geometry,flight}.py` | 是（`uv sync` 安裝相依） |
| 2 | 撞擊成形規則 | Codex | `task-2-impact` | `src/splash_sim/impact.py`、`src/splash_sim/config.py`（只加 `ImpactConfig`）、`configs/default.yaml`（只加 `impact:` 段）、`tests/test_impact.py` | 否 |
| 3 | 繪製、特徵量測、干擾、影像讀寫 | Codex | `task-3-render` | `src/splash_sim/{render,features,augment,imageio}.py`、`config.py`（只加 `RenderConfig`、`AugmentConfig`）、`default.yaml`（只加 `render:`、`augment:` 段）、`tests/test_{render,features,augment,imageio}.py` | 否 |
| 4 | 場景取樣與資料集輸出 | Codex | `task-4-scene-dataset` | `src/splash_sim/{scene,dataset}.py`、`__init__.py`、`config.py`（只加 `SceneConfig`、`OutputConfig`）、`default.yaml`（只加 `scene:`、`output:` 段）、`tests/test_{scene,dataset}.py` | 否 |
| 5 | CLI、YOLO 匯出、範例設定、README | Codex | `task-5-cli-docs` | `src/splash_sim/{cli,yolo}.py`、`pyproject.toml`（只加 `[project.scripts]`）、`configs/*.yaml`（新增三份範例）、`README.md`、`tests/test_{cli,yolo,perf}.py` | 否 |

測試指令：局部 `uv run pytest tests/<檔名> -q`｜全套 `uv run pytest -q`（本專案沒有 lint 與型別檢查關卡）。

---

### Task 1：骨架、設定與飛行物理

**Files：**
- Create：`pyproject.toml`、`.python-version`（內容 `3.11`）、`src/splash_sim/__init__.py`、`src/splash_sim/config.py`、`src/splash_sim/geometry.py`、`src/splash_sim/flight.py`、`configs/default.yaml`
- Test：`tests/test_config.py`、`tests/test_geometry.py`、`tests/test_flight.py`

**Interfaces：**
- Produces：
  - `splash_sim.__version__: str = "0.1.0"`
  - `class ConfigError(ValueError)`，訊息為中文，包含點號路徑的欄位名稱（例：`air.density_kg_m3`）。
  - Pydantic 模型都設 `model_config = ConfigDict(extra="forbid", frozen=True, strict=True)`（嚴格型別：字串不轉數字，整數可填浮點數欄位）：
    - `LiquidConfig(density_kg_m3: float = 998.0 (>0), surface_tension_n_m: float = 0.072 (>0), viscosity_pa_s: float = 1.0e-3 (>0))`
    - `AirConfig(density_kg_m3: float = 1.204 (>0), viscosity_pa_s: float = 1.81e-5 (>0), drag_enabled: bool = True)`
    - `SimConfig(seed: int = 0 (>=0), liquid: LiquidConfig, air: AirConfig)`。之後的 Task 會在這裡加 `impact`、`render`、`augment`、`scene`、`output` 欄位，每個都有預設值。
  - `default_config() -> SimConfig`
  - `load_config(path: str | Path) -> SimConfig`：用 UTF-8 讀 YAML。檔案不存在、YAML 語法錯誤、驗證失敗都轉成 `ConfigError`。
  - `geometry.py`：`PX_PER_MM = 10`、`A4_WIDTH_MM = 210.0`、`A4_HEIGHT_MM = 297.0`、`CANVAS_SHAPE = (2970, 2100)`（rows, cols）、`mm_to_px(x_mm, y_mm) -> tuple[float, float]`（回傳 (col, row)；col = x·10、row = (297 − y)·10）、`px_to_mm(col, row) -> tuple[float, float]`、`on_paper(x_mm, y_mm) -> bool`。
  - `flight.py`：`GRAVITY_M_S2 = 9.81`
    - `drag_coefficient(reynolds: float) -> float`：Re < 1000 時為 `24/Re·(1+0.15·Re**0.687)`，否則為 `0.44`。Re ≤ 0 時丟出 `ValueError`。
    - `@dataclass(frozen=True) class FlightResult: impact_position_m: np.ndarray (3,)；impact_velocity_m_s: np.ndarray (3,)；flight_time_s: float`
    - `fly_to_plane(position_m, velocity_m_s, diameter_m: float, liquid: LiquidConfig, air: AirConfig, *, max_time_s: float = 5.0) -> FlightResult`：往前積分到 z = 0（`solve_ivp` 的 event，`rtol=1e-10`、`atol=1e-12`）。起點 z ≤ 0 或 max_time 內沒落地時，丟出中文 `ValueError`。
    - `propagate(position_m, velocity_m_s, diameter_m: float, liquid, air, duration_s: float) -> tuple[np.ndarray, np.ndarray]`：積分固定時長，`duration_s` 可為負（往回推）。這是日後回推流程要共用的函式。
    - 阻力：`a = g − (3·ρ_air·C_d)/(4·ρ_liquid·d)·|v|·v`；`Re_air = ρ_air·|v|·d/μ_air`；|v| = 0 時阻力為 0。

- [ ] **Step 1：建立 `pyproject.toml`**（src layout、`requires-python = ">=3.11"`，宣告上方 Global Constraints 的全部相依，`[tool.pytest.ini_options] testpaths=["tests"]`，並登記 marker `perf`），執行 `uv sync`。預期：產生 `uv.lock`，`uv run python -c "import cv2, scipy, pydantic"` 無錯誤。

- [ ] **Step 2：寫失敗測試 `test_default_config_values`**：`default_config().liquid.density_kg_m3 == 998.0`、`.air.drag_enabled is True`、`.seed == 0`。
- [ ] **Step 3：執行** `uv run pytest tests/test_config.py -q`，預期 FAIL（找不到模組）。
- [ ] **Step 4：實作 `config.py` 的模型與 `default_config()`**，以及 `__init__.py` 的 `__version__`。
- [ ] **Step 5：執行同一指令**，預期 PASS。

- [ ] **Step 6：寫失敗測試 `test_load_config_utf8_comments`**：用 `encoding="utf-8"` 寫入含中文註解 `# 液體密度` 的 YAML（設 `liquid: {density_kg_m3: 1000}`），`load_config` 讀回的值是 1000.0。執行，預期 FAIL（`load_config` 不存在）。
- [ ] **Step 7：實作 `load_config` 的讀檔部分**（明確用 UTF-8 讀，`yaml.safe_load` 後交給 `SimConfig.model_validate`），執行，預期 PASS。

- [ ] **Step 8：寫失敗測試 `test_load_config_rejects_bad_values`**，含三個案例：
  - `air: {density_kg_m3: -1}`：斷言丟出 `ConfigError`，`"air.density_kg_m3" in str(e)`，且訊息含中文字。
  - 未知欄位 `liquid: {colour: red}`：斷言訊息含 `liquid.colour` 與「不認得」。
  - 型別錯誤 `liquid: {density_kg_m3: "998"}`（字串）：斷言丟出 `ConfigError`，訊息含 `liquid.density_kg_m3`。**型別採嚴格檢查**（Claude 2026-11-04 決定）：模型設 `strict=True`，字串不會自動轉成數字；整數填進浮點數欄位可以接受，例如 `998`。

  執行，預期 FAIL。
- [ ] **Step 9：把 Pydantic 的 `ValidationError` 逐條轉成中文 `ConfigError`**，格式為 `設定檔 <路徑> 的 <欄位> 欄：<原因>（合理範圍：…）`，未知欄位寫「不認得這個欄位」。執行，預期 PASS。

- [ ] **Step 10：寫失敗測試 `test_default_yaml_matches_defaults`**：斷言 `load_config("configs/default.yaml") == default_config()`。
- [ ] **Step 11：執行**，預期 FAIL（`default.yaml` 尚不存在）。
- [ ] **Step 12：建立 `configs/default.yaml`**，包含 `seed`、`liquid`、`air` 三段，每個欄位都有中文註解（意義、單位、出處）。
- [ ] **Step 13：執行**，預期 PASS。

- [ ] **Step 14：寫失敗測試 `tests/test_geometry.py::test_mm_px_roundtrip`**：`mm_to_px(0, 0) == (0, 2970)`、`mm_to_px(210, 297) == (2100, 0)`，`px_to_mm(*mm_to_px(12.3, 45.6))` 回到原值（誤差 1e-9）；`on_paper(-0.1, 10) is False`。
- [ ] **Step 15：執行、實作 `geometry.py`、再執行**，預期先 FAIL 後 PASS。

- [ ] **Step 16：寫失敗測試 `test_drag_coefficient_regimes`**：`drag_coefficient(0.5) == pytest.approx(48*(1+0.15*0.5**0.687))`、`drag_coefficient(2000) == 0.44`、`drag_coefficient(0)` 丟出 `ValueError`。
- [ ] **Step 17：執行、實作、再執行**，預期先 FAIL 後 PASS。

- [ ] **Step 18：寫失敗測試 `test_no_drag_matches_projectile`**：`air` 設 `drag_enabled=False`，從 (0.10, 0.15, 0.20) m 以 (1, 0, 0) m/s 發射，d = 3 mm。斷言 `t = sqrt(2·0.20/9.81)`，撞擊點 x 與 `0.10 + t` 的差 < 1e-5 m（0.01 mm），y 等於 0.15，撞擊速度 z 分量 ≈ `−9.81·t`。
- [ ] **Step 19：執行**，預期 FAIL。
- [ ] **Step 20：實作 `fly_to_plane`**，這一步只含重力；阻力留給 Step 22 的測試驅動。
- [ ] **Step 21：執行**，預期 PASS。

以下三個測試依序各走一次完整的紅綠循環：寫測試 → 看到 FAIL → 實作 → PASS，一次只處理一個。

- [ ] **Step 22：寫失敗測試 `test_drag_shortens_range`**：從 (0.05, 0.10, 0.25) m 以 (2.0, 1.0, 0.5) m/s 發射，d = 1 mm。斷言開阻力時的水平飛行距離 < 不開阻力時的距離。看到 FAIL 後，在共用的加速度函式中加入阻力（使用 `drag_coefficient`），讓測試轉綠。
- [ ] **Step 23：寫失敗測試 `test_backward_propagation_returns_to_source`**：開啟阻力，用 Step 22 的發射條件先執行 `fly_to_plane`，再執行 `propagate(impact_pos, impact_vel, d, …, -flight_time_s)`，回到起點的誤差 < 1e-5 m。看到 FAIL（`propagate` 不存在）後實作 `propagate`。
- [ ] **Step 24：寫失敗測試 `test_fly_rejects_start_below_plane`**：從 z = 0 起飛時丟出 `ValueError`，且訊息含中文。看到 FAIL 後補上檢查。

- [ ] **Step 25：全套** `uv run pytest -q`，預期全部 PASS。
- [ ] **Step 26：提交**（Claude 審查後）：`feat: 專案骨架、設定載入與飛行物理`

---

### Task 2：撞擊成形規則

**Files：**
- Create：`src/splash_sim/impact.py`、`tests/test_impact.py`
- Modify：`src/splash_sim/config.py`（加 `ImpactConfig`，並在 `SimConfig` 加 `impact` 欄位）、`configs/default.yaml`（加 `impact:` 段）

**Interfaces：**
- Consumes：`LiquidConfig`、`geometry` 角度慣例（Task 1）。
- Produces：
  - `ImpactConfig`（每個欄位的 docstring 或 YAML 註解都要寫出處與狀態）：
    - `ruleset: str = "literature_v1"`
    - `spread_a: float = 1.24`（Laan 2014；待核對原文）
    - `angle_bias_deg: float = 0.0`（Joris 2017 指出的 W/L 偏差；預設關閉）
    - `spine_a: float = 0.1443`、`spine_b: float = 0.5`、`spine_c: float = 0.25`（N = a·We^b·Re^c，Bhola & Chandra 1999／Mehdizadeh 2004；待核對原文）
    - `spine_min_weber: float = 10.0`、`spine_length_frac: tuple[float,float] = (0.1, 0.35)`（相對於 W；待實拍校正）
    - `spine_front_kappa: float = 3.0`（毛刺集中前緣的程度；待實拍校正）
    - `tail_coeff: float = 0.4`（尾巴長度 = tail_coeff·W·cos α；待實拍校正）
    - `satellite_min_weber: float = 150.0`、`satellite_per_weber: float = 0.02`、`satellite_max: int = 8`、`satellite_size_frac: tuple = (0.03, 0.12)`（相對於 W；待實拍校正）
    - `paper: Literal["coated", "copy"] = "coated"`、`bleed_mm: dict = {"coated": 0.05, "copy": 0.4}`（待實拍校正）
    - `jitter_frac: float = 0.05`（隨機擾動比例；0 表示完全決定性）
  - `@dataclass(frozen=True) class Spine: angle_deg: float`（相對於 γ，0 表示正前方）；`length_mm: float`；`width_mm: float`
  - `@dataclass(frozen=True) class Satellite: offset_mm: tuple[float, float]`（紙面座標，相對於水漬中心）；`diameter_mm: float`
  - `@dataclass(frozen=True) class StainGeometry: center_mm: tuple[float,float]；width_mm；length_mm；direction_deg；impact_angle_deg；spines: tuple[Spine,...]；satellites: tuple[Satellite,...]；tail_length_mm；bleed_mm；diameter_mm；speed_m_s；weber；reynolds；spread_factor；ruleset: str`
  - `RuleFn = Callable[[tuple[float,float], np.ndarray, float, LiquidConfig, ImpactConfig, np.random.Generator], StainGeometry]`
  - `register_ruleset(name: str, fn: RuleFn) -> None`、`get_ruleset(name: str) -> RuleFn`（未知名稱時丟出 `ConfigError`，訊息列出可用的名稱）
  - `compute_stain(center_mm, velocity_m_s, diameter_mm, liquid, impact: ImpactConfig, rng) -> StainGeometry`：依 `impact.ruleset` 分派。
  - `literature_v1` 的規則：
    - v_n = |v_z|，v_t = 紙面分量
    - We = ρ·v_n²·d/σ，Re = ρ·v_n·d/μ
    - P = We·Re^(−2/5)，ξ = Re^(1/5)·√P/(A+√P)
    - W = ξ·d
    - α = atan2(v_n, |v_t|)；L = W / sin(α + bias)
    - γ = atan2(v_y, v_x) 轉成 [0, 360)，垂直撞擊時 γ = 0
    - 毛刺數 = round(a·We^b·Re^c)，We < spine_min_weber 時為 0
    - 毛刺角度取自 von Mises(0, κ)，κ = spine_front_kappa·cos α / max(sin α, 0.1)
    - 尾巴長度 = tail_coeff·W·cos α
    - 衛星小滴數 = min(satellite_max, floor(satellite_per_weber·(We − satellite_min_weber)))，只在 We 超過門檻時產生，位置在前方 L/2 到 L 之間
    - W、L、尾巴長度乘上 (1 + U(−jitter, jitter))

- [ ] **Step 1：寫失敗測試 `test_weber_reynolds_definitions`**：v = (0, 0, −2) m/s、d = 3 mm、水的預設物性，斷言 `weber == approx(998*4*0.003/0.072)`、`reynolds == approx(998*2*0.003/1e-3)`。
- [ ] **Step 2：執行** `uv run pytest tests/test_impact.py -q`，預期 FAIL。
- [ ] **Step 3：實作資料類別、`ImpactConfig`、`literature_v1` 的無因次數部分與 `compute_stain`。**
- [ ] **Step 4：執行**，預期 PASS。

- [ ] **Step 5：寫失敗測試 `test_vertical_impact_round_with_laan_spread`**：`jitter_frac=0`，v = (0, 0, −2)，斷言 `width_mm == length_mm`、`impact_angle_deg == approx(90)`、`spread_factor` 等於測試內用公式算出的 ξ（rel 1e-9）、`width_mm == approx(spread_factor*3.0)`。
- [ ] **Step 6：執行 → 實作攤開規則 → 執行**，預期先 FAIL 後 PASS。

- [ ] **Step 7：寫失敗測試 `test_oblique_angle_and_direction`**：`jitter_frac=0`。v = (1, 0, −1) 時 α ≈ 45°、`width/length ≈ sin45°`（1e-9）、γ ≈ 0；v = (0, −1, −1) 時 γ ≈ 270；v = (−1, 1, −√2) 時 γ ≈ 135。
- [ ] **Step 8：執行 → 實作 α、γ、L → 執行。**

- [ ] **Step 9：寫失敗測試 `test_angle_bias_applied`**：`angle_bias_deg=5`，v = (1, 0, −1) 時 `width/length == approx(sin(50°))`。
- [ ] **Step 10：執行 → 實作 → 執行。**

- [ ] **Step 11：寫失敗測試 `test_monotonic_in_speed`**：`jitter_frac=0`，45° 撞擊，速度取 [0.5, 1, 2, 3, 5] m/s，斷言 `width_mm` 與 `len(spines)` 都不遞減，且 5 m/s 的毛刺數 > 0.5 m/s 的毛刺數。
- [ ] **Step 12：執行 → 實作毛刺數規則 → 執行。**

- [ ] **Step 13：寫失敗測試 `test_spines_concentrate_forward_when_oblique`**：固定 rng 種子與高速度（4 m/s）。α = 20° 時毛刺角度的平均合成向量長度 > 0.6；α = 90° 時 < 0.4。
- [ ] **Step 14：執行 → 實作毛刺角度與長度 → 執行。**

- [ ] **Step 15：寫失敗測試 `test_satellites_only_above_threshold`**：We < 150 時 `satellites == ()`；5 m/s、d = 3 mm 垂直撞擊時有 1 到 8 個衛星小滴，且每個距中心 ≥ L/2。
- [ ] **Step 16：執行 → 實作衛星小滴與尾巴 → 執行。**

- [ ] **Step 17：寫失敗測試 `test_same_seed_same_stain` 與 `test_custom_ruleset_registration`**：同一個種子產生的 `StainGeometry` 相等；`register_ruleset("test_const", fn)` 之後設 `ruleset="test_const"` 會呼叫到 fn；設 `ruleset="nope"` 時丟出 `ConfigError`，訊息含 `literature_v1`。逐一完成紅綠循環。
- [ ] **Step 18：在 `default.yaml` 加入 `impact:` 段**（每欄附中文註解、出處與狀態），讓 `test_default_yaml_matches_defaults` 維持通過。
- [ ] **Step 19：全套** `uv run pytest -q`，預期全部 PASS。
- [ ] **Step 20：提交**（Claude 審查後）：`feat: 撞擊成形規則 literature_v1`

---

### Task 3：繪製、特徵量測、干擾與影像讀寫

**Files：**
- Create：`src/splash_sim/{imageio,render,features,augment}.py`、`tests/test_{imageio,render,features,augment}.py`
- Modify：`config.py`（加 `RenderConfig`、`AugmentConfig`）、`configs/default.yaml`（加 `render:`、`augment:` 段）

**Interfaces：**
- Consumes：`StainGeometry`、`Spine`、`Satellite`（Task 2）；`mm_to_px`、`CANVAS_SHAPE`（Task 1）。
- Produces：
  - `imageio.write_png(path: Path, array: np.ndarray) -> None`（自動建立上層資料夾）、`imageio.read_png(path: Path, *, unchanged: bool = True) -> np.ndarray`。支援 uint8 RGB 與 uint16 單通道；內部把 RGB 轉成 OpenCV 的 BGR。
  - `RenderConfig(paper_rgb: tuple[int,int,int] = (245,245,240), dye_rgb: tuple = (190,30,45), dye_opacity: tuple[float,float] = (0.6, 0.9), draw_spines: bool = True, draw_tail: bool = True, draw_satellites: bool = True)`
  - `@dataclass class RenderedScene: image: np.ndarray`（2970×2100×3 uint8，乾淨、未加干擾）；`instance_mask: np.ndarray`（uint16，0 = 背景，第 k 滴 = k+1，包含主體、毛刺、尾巴）；`satellite_mask: np.ndarray`（uint16，值為母滴的編號）
  - `render_stains(stains: Sequence[StainGeometry], cfg: RenderConfig, rng: np.random.Generator) -> RenderedScene`：
    - 每滴先組出紙面 mm 座標的多邊形：橢圓取 128 點；毛刺是從橢圓邊緣向外的細三角形；尾巴是沿 γ 方向接在前緣的漸細形狀。
    - 用 `mm_to_px` 轉換後以 `cv2.fillPoly` 畫在遮罩上（不抗鋸齒）。
    - 色彩層的 alpha 用 `bleed_mm·10` 當高斯 σ 模糊後，再與紙色合成。
    - 重疊時後畫的覆蓋先畫的。
    - 超出畫布的部分直接裁掉，不報錯。
  - `@dataclass(frozen=True) class StainFeatures: area_mm2；width_mm；length_mm；aspect_ratio`（W/L）；`direction_deg`（[0,180)，ellipse 無頭尾）；`spine_count: int`
  - `measure_stain(mask: np.ndarray[bool]) -> StainFeatures`：取最大輪廓做 `cv2.fitEllipse`。毛刺數的算法是：輪廓到擬合橢圓的徑向距離超出閾值的連續段數（閾值由實作者決定，以測試為準）。
  - `AugmentConfig`：
    - `paper_texture: {enabled: True, strength: 6.0}`
    - `lighting: {enabled: True, strength: 0.08}`
    - `blur: {enabled: True, sigma_px: (0.0, 1.2)}`
    - `noise: {enabled: True, std: (1.0, 4.0)}`
    - `jpeg: {enabled: True, quality: (75, 95)}`
    - 子模型都是 `extra="forbid"`
  - `apply_augmentations(image: np.ndarray, cfg: AugmentConfig, rng) -> np.ndarray`：回傳新陣列，不修改輸入。

- [ ] **Step 1：寫失敗測試 `test_png_roundtrip_non_ascii_path`**：uint8 RGB 與 uint16 兩種陣列，寫到 `tmp_path/"中文資料夾"/"a.png"` 再讀回，`np.array_equal`。
- [ ] **Step 2：執行 → 實作 `imageio.py` → 執行**，預期先 FAIL 後 PASS。

- [ ] **Step 3：寫失敗測試 `test_render_single_round_stain_mask`**：一滴垂直撞擊、中心 (105, 148.5) mm、W = L = 10 mm、無毛刺。斷言 `instance_mask` 中值為 1 的像素面積 ≈ π·50² px（相對誤差 3%），重心 ≈ (1050, 1485) px（±2 px），影像在中心的顏色接近染料色、角落等於紙色。
- [ ] **Step 4：執行 → 實作 `render_stains` 的橢圓主體與合成 → 執行。**

- [ ] **Step 5：寫失敗測試 `tests/test_features.py::test_measured_ellipse_matches_geometry`**：`draw_spines=False`、`draw_tail=False`，α ∈ {20°, 45°, 70°}、γ ∈ {0°, 30°, 135°}。用 `measure_stain` 量出的 `aspect_ratio` 與 sin α 的差 ≤ 0.02；`direction_deg` 與 γ mod 180 的差 ≤ 2°。（這是 spec 第 6 節驗收第 2 條）
- [ ] **Step 6：執行 → 實作 `measure_stain` 的橢圓部分 → 執行。**

- [ ] **Step 7：寫失敗測試 `test_spine_count_measured`**：垂直撞擊、W = 10 mm，毛刺數 N ∈ {0, 6, 12}，等角度分布，長度 0.3·W。斷言量到的 `spine_count == N`。
- [ ] **Step 8：執行 → 實作毛刺繪製與毛刺計數 → 執行。**

- [ ] **Step 9：寫失敗測試 `test_tail_and_satellites_rendered`**：開啟尾巴時，遮罩沿 γ 方向的最遠點超過 L/2 + 0.5·tail_length；衛星小滴只出現在 `satellite_mask`（值為母滴編號），不在 `instance_mask` 中。
- [ ] **Step 10：執行 → 實作尾巴與衛星小滴 → 執行。**

- [ ] **Step 11：寫失敗測試 `test_render_stain_partly_off_canvas`**：中心 (1, 1) mm、W = 10 mm 的水漬不報錯，遮罩中有像素，而且全都在畫布內。
- [ ] **Step 12：寫失敗測試 `test_bleed_widens_edge`**：同一滴分別用 `bleed_mm` 0.05 與 0.4 繪製，後者影像中「介於紙色與染料色之間」的像素較多，但兩者的遮罩完全相同。
- [ ] 以上兩個測試逐一完成紅綠循環。

- [ ] **Step 13：寫失敗測試 `tests/test_augment.py::test_disabled_is_identity`**（全部關閉時輸出與輸入 `array_equal`）、`test_same_rng_same_output`、`test_input_not_modified`、`test_enabled_changes_image`。逐一完成紅綠循環，實作 `apply_augmentations`。
- [ ] **Step 14：在 `default.yaml` 加入 `render:`、`augment:` 段**（中文註解）。
- [ ] **Step 15：全套** `uv run pytest -q`，預期全部 PASS。
- [ ] **Step 16：提交**（Claude 審查後）：`feat: 繪製、特徵量測與影像干擾`

---

### Task 4：場景取樣與資料集輸出

**Files：**
- Create：`src/splash_sim/scene.py`、`src/splash_sim/dataset.py`、`tests/test_scene.py`、`tests/test_dataset.py`
- Modify：`src/splash_sim/__init__.py`（匯出公開 API）、`config.py`（加 `SceneConfig`、`OutputConfig`）、`configs/default.yaml`（加 `scene:`、`output:` 段）

**Interfaces：**
- Consumes：`fly_to_plane`（Task 1）、`compute_stain`（Task 2）、`render_stains`、`apply_augmentations`、`write_png`（Task 3）。
- Produces：
  - `DiameterConfig(mode: Literal["fixed","log_uniform"] = "fixed", fixed_mm: float = 3.0, range_mm: tuple = (0.3, 4.0))`
  - `SprayConfig`：
    - `source_height_m: tuple = (0.10, 0.30)`
    - `source_offset_m: float = 0.30`（源頭水平位置 = 紙中心 ± offset，均勻分布）
    - `cone_half_angle_deg: float = 30.0`
    - `launch_speed_m_s: tuple = (0.5, 5.0)`
    - `drops_launched: tuple[int,int] = (30, 80)`
    - `min_drops_on_paper: int = 9`
    - `max_resample: int = 50`
    - `min_impact_angle_deg: float = 10.0`
  - `VerticalDropConfig(heights_m: tuple = (0.10, 0.20, 0.30), grid: tuple[int,int] = (3, 4))`：每個高度一張場景，同一張場景內 3×4 滴排成格狀（間距由紙面均分）；第 i 張場景使用 `heights_m[i % len]`。
  - `SingleDropConfig(speed_m_s: tuple = (0.5, 5.0), impact_angle_deg: tuple = (10.0, 90.0))`：每張場景一滴，位於紙中心，γ 均勻分布。
  - `SceneConfig(mode: Literal["spray","vertical_drop","single"] = "spray", diameter, spray, vertical_drop, single)`
  - `OutputConfig(n_scenes: int = 100 (>=1), name: str = "dataset", crop_size_px: int = 384 (>=64))`
  - `@dataclass class Drop: drop_id: int；diameter_mm: float；launch_velocity_m_s: np.ndarray | None；impact_velocity_m_s: np.ndarray；stain: StainGeometry`
  - `@dataclass class Scene: index: int；seed_seq: tuple[int,int]；mode: str；source_m: np.ndarray | None；drops: list[Drop]；discarded: dict[str,int]`（鍵為 `off_paper`、`too_shallow`）
  - `class SceneSamplingError(RuntimeError)`
  - `sample_scene(cfg: SimConfig, index: int) -> Scene`：`rng = np.random.default_rng([cfg.seed, index])`，同一個 rng 依序供取樣、成形與繪製使用。
  - `@dataclass class SceneOutput: scene: Scene；rendered: RenderedScene；image: np.ndarray`（已加干擾）；`crops: dict[int, np.ndarray]`；`truncated: dict[int, bool]`
  - `simulate_scene(cfg: SimConfig, index: int = 0) -> SceneOutput`
  - `simulate_single_drop(velocity_m_s, diameter_mm: float, cfg: SimConfig | None = None, seed: int = 0) -> SceneOutput`（不經飛行段）
  - `generate_dataset(cfg: SimConfig, out_dir: Path, *, n_scenes: int | None = None, name: str | None = None, folder_suffix: str | None = None) -> Path`：資料夾名稱為 `<name>_<folder_suffix 或 當下時間 YYYYmmdd-HHMMSS>`；檔案結構同 spec 5.5；`config_snapshot.yaml` 包含完整設定與 `splash_sim_version`。
  - `labels/scene_NNNNN.json`（`json.dumps(..., sort_keys=True, ensure_ascii=False, indent=2)`，浮點數四捨五入到 6 位）：
    - 場景層級：`scene_index`、`mode`、`seed_seq`、`source_mm`（[x,y,z] 或 null）、`discarded`、`ruleset`、`splash_sim_version`
    - `drops: [...]`，每滴包含：`drop_id`、`instance_id`（= drop_id+1）、`center_mm`、`impact_velocity_m_s`、`speed_m_s`、`impact_angle_deg`、`direction_deg`、`diameter_mm`、`weber`、`reynolds`、`spread_factor`、`width_mm`、`length_mm`、`spine_count`、`tail_length_mm`、`satellite_count`、`bbox_px`（[x0,y0,x1,y1]）、`crop_file`、`truncated`
  - `index.csv`：每滴一列，欄位依序為 `scene_index, drop_id` 加上述每滴欄位中的純量，向量欄位拆成 `_x/_y/_z`。
  - 編號格式：場景 5 位數 `scene_00001`（從 1 起算，對應 index 0），切片 `scene_00001_d003.png`（drop_id 3 位數）。
  - 所有 PNG 都透過 `imageio.write_png` 寫出。

- [ ] **Step 1：寫失敗測試 `test_spray_scene_has_enough_drops_on_paper`**：用預設設定 `sample_scene(cfg, 0)`，斷言 `len(drops) >= 9`、每滴 `on_paper(*stain.center_mm)`、`source_m[2]` 介於 0.10 與 0.30 之間、每滴 `impact_angle_deg >= 10`。
- [ ] **Step 2：執行 → 實作 `SceneConfig` 與 spray 模式 → 執行。** 發射軸指向紙中心。另外量測預設參數下 100 張場景「重抽次數 ≤ 50 就成功」的比例，寫進施工欄。成功率 < 95% 時回報 Claude，不要自行修改預設值（預設值屬已核可的 spec）。

- [ ] **Step 3：寫失敗測試 `test_spray_discards_shallow_impacts`**：設 `min_impact_angle_deg=45`，斷言 `discarded["too_shallow"] > 0`，且留下來的每滴撞擊角都 ≥ 45°。
- [ ] **Step 4：寫失敗測試 `test_spray_gives_up_with_chinese_error`**：設 `source_offset_m=5.0`、`max_resample=3`，斷言丟出 `SceneSamplingError`，訊息含 `source_offset_m` 與 `max_resample`。
- [ ] 以上兩個測試逐一完成紅綠循環。

- [ ] **Step 5：寫失敗測試 `test_vertical_drop_speed_matches_flight`**：mode 設 vertical_drop，場景 0（高度 0.10 m）有 12 滴，每滴撞擊角 ≈ 90°，速度等於 `fly_to_plane` 從靜止落下 0.10 m 的結果（rel 1e-9），且小於 √(2·9.81·0.10)。
- [ ] **Step 6：寫失敗測試 `test_single_mode_ranges`**：mode 設 single，取 20 張場景，每張 1 滴，速度與撞擊角都在設定的範圍內。
- [ ] 以上兩個測試逐一完成紅綠循環。

- [ ] **Step 7：寫失敗測試 `test_scene_reproducible_and_independent`**：`sample_scene(cfg, 5)` 跑兩次結果相同；先跑 0 到 4 再跑 5 的結果，也與直接跑 5 相同。
- [ ] **Step 8：執行 → 修正 rng 衍生方式 → 執行。**

- [ ] **Step 9：寫失敗測試 `tests/test_dataset.py::test_crop_near_edge_padded_and_flagged`**：用 `simulate_single_drop` 放一滴在中心 (2, 2) mm，切片大小為 `crop_size_px`，超出畫布的區域等於紙色（干擾全部關閉時），`truncated[0] is True`；放在紙中心、W = 10 mm 的一滴則 `truncated[0] is False`。
- [ ] **Step 10：執行 → 實作 `simulate_scene`、`simulate_single_drop` 與裁切 → 執行。**

- [ ] **Step 11：寫失敗測試 `test_generate_dataset_layout`**：`n_scenes=2`，資料夾內有 `config_snapshot.yaml`、`index.csv`，以及 `scenes/`、`masks/`、`labels/`、`crops/`。label JSON 的 drop 數等於 crops 數，也等於 `index.csv` 的列數；遮罩中出現的 id 集合等於 `{d.instance_id}`；用 `load_config` 讀 `config_snapshot.yaml` 要能成功（快照只含設定本身；版本另存為 `meta.json`：`{"splash_sim_version": …, "n_scenes": …}`）。
- [ ] **Step 12：執行 → 實作 `generate_dataset` → 執行。**

- [ ] **Step 13：寫失敗測試 `test_dataset_byte_identical`**：同一份設定、`folder_suffix` 分別為 `"a"` 與 `"b"` 產生兩次，兩個資料夾中所有檔案的相對路徑與 SHA-256 完全相同。（spec 驗收第 4 條）
- [ ] **Step 14：執行 → 修正任何非決定性來源 → 執行。**

- [ ] **Step 15：寫失敗測試 `test_labels_consistent_with_image`**：關閉干擾、毛刺與尾巴，對 label 中每滴，以 `bbox_px` 從遮罩取出該滴，用 `measure_stain` 量出的 aspect_ratio 與 sin(impact_angle_deg) 的差 ≤ 0.03。（spec 反目標「答案與圖不一致」）
- [ ] **Step 16：執行 → 修正 → 執行。**
- [ ] **Step 17：在 `default.yaml` 加入 `scene:`、`output:` 段；`__init__.py` 匯出 `load_config, default_config, simulate_scene, simulate_single_drop, generate_dataset, SimConfig, ConfigError, __version__`。**
- [ ] **Step 18：全套** `uv run pytest -q`，預期全部 PASS。
- [ ] **Step 19：提交**（Claude 審查後）：`feat: 場景取樣與資料集輸出`

---

### Task 5：CLI、YOLO 匯出、範例設定、README

**Files：**
- Create：`src/splash_sim/cli.py`、`src/splash_sim/yolo.py`、`configs/vertical_drop_calibration.yaml`、`configs/single_drop_training.yaml`、`configs/variable_droplet.yaml`、`README.md`、`tests/test_cli.py`、`tests/test_yolo.py`、`tests/test_perf.py`
- Modify：`pyproject.toml`（加 `[project.scripts] splash-sim = "splash_sim.cli:main"`）

**Interfaces：**
- Consumes：`load_config`、`generate_dataset`、`simulate_scene`（Task 4）；`read_png`（Task 3）。
- Produces：
  - `cli.main(argv: list[str] | None = None) -> int`（argparse）：
    - `generate --config PATH [--out DIR=datasets] [--n N] [--name NAME]`：印出輸出資料夾路徑。
    - `preview --config PATH [--out FILE=preview.png] [--index 0] [--open]`：`--open` 時用 `webbrowser.open(Path.as_uri())` 開啟圖片。
    - `export-yolo --dataset DIR`
    - `ConfigError`、`SceneSamplingError` 只印中文訊息（不印 traceback），回傳 2；成功回傳 0。
  - `yolo.export_yolo(dataset_dir: Path) -> Path`：產生 `<dataset>/yolo/labels/scene_NNNNN.txt`，每滴一行 `0 x1 y1 x2 y2 …`（輪廓多邊形，座標除以影像寬高做正規化，用 `cv2.findContours` 加 `approxPolyDP`，ε = 1 px）；另產生 `<dataset>/yolo/data.yaml`（`path`、`train: ../scenes`、`names: {0: stain}`）。衛星小滴不匯出。
  - 範例設定：
    - `vertical_drop_calibration.yaml`：mode 設 vertical_drop、液滴直徑固定 3 mm、`augment` 中的模糊與 JPEG 關閉。
    - `single_drop_training.yaml`：mode 設 single、`n_scenes: 5000`。
    - `variable_droplet.yaml`：spray 模式、直徑設 log_uniform。
    - 三份都要能通過 `load_config`。

- [ ] **Step 1：寫失敗測試 `test_cli_generate_and_exit_codes`**：用 `main(["generate","--config","configs/default.yaml","--out",str(tmp),"--n","1"])`，斷言回傳 0、資料夾存在。設定檔的密度設成負數時回傳 2，且 capsys 擷取的 stderr 含 `liquid.density_kg_m3`、不含 `Traceback`。
- [ ] **Step 2：執行 → 實作 `generate` 子指令與錯誤處理 → 執行。**
- [ ] **Step 3：寫失敗測試 `test_cli_preview_writes_png`**（不帶 `--open`），然後執行 → 實作 → 執行。
- [ ] **Step 4：寫失敗測試 `tests/test_yolo.py::test_export_polygons_normalized`**：產生 1 張場景後匯出，txt 行數等於滴數，每行第一個值是 `0`、座標成對且都在 [0, 1] 範圍內。把多邊形畫回 2100×2970 畫布後，與該滴遮罩的 IoU ≥ 0.9。執行 → 實作 `export_yolo` 與 `export-yolo` 子指令 → 執行。
- [ ] **Step 5：寫失敗測試 `test_example_configs_load`**：`configs/*.yaml` 全部都能通過 `load_config`；`vertical_drop_calibration.yaml` 的 `scene.mode == "vertical_drop"`。執行 → 建立三份範例設定 → 執行。
- [ ] **Step 6：寫測試 `tests/test_perf.py::test_scene_under_two_seconds`**（`@pytest.mark.perf`）：用 spray 模式並把 `drops_launched` 固定為能產生約 20 滴的設定，`simulate_scene` 的牆鐘時間取 3 次中最快的一次，要 < 2.0 秒。（spec 驗收第 6 條）若未通過，屬於 Task 3／4 程式的效能問題，在本 Task 內修正繪製（例如只在水漬外框的局部區域做模糊），不放寬門檻。
- [ ] **Step 7：撰寫 `README.md`（繁體中文）**，內容包括：
  - 這是什麼
  - 安裝：`uv sync`；pip 替代方式 `pip install -e .`
  - 三個指令就能產生預覽：`uv sync` → `uv run splash-sim preview --config configs/default.yaml --open` → `uv run splash-sim generate --config configs/default.yaml --n 10`
  - 設定檔怎麼改
  - 輸出格式
  - 如何註冊自己的規則組（附 10 行以內的範例）
  - 形狀規則的出處與狀態表
  - 已知限制（暈染只是影像效果、毛刺係數待核對、不模擬紙張吸水）
- [ ] **Step 8：手動驗收**：在新的終端機依 README 照做三個指令，確認產生預覽圖並能開啟；把結果寫進 HANDOFF。
- [ ] **Step 9：全套** `uv run pytest -q`，預期全部 PASS（包含 perf）。
- [ ] **Step 10：提交**（Claude 審查後）：`feat: CLI、YOLO 匯出與使用說明`

---

## Spec 對照

| Spec 段落 | Task |
|---|---|
| 5.1 飛行、時間可逆 | 1 |
| 5.2 三種場景模式、預設範圍 | 4 |
| 5.3 撞擊成形、出處標示、可替換規則組 | 2 |
| 5.4 繪製、實例遮罩、干擾、切片 | 3、4 |
| 5.5 輸出格式、YOLO 匯出 | 4、5 |
| 5.6 指令、Python API、設定檢查、範例設定 | 1、4、5 |
| 5.7 可重現 | 4 |
| 5.8 特徵擷取（第一里程碑只做函式） | 3 |
| 第 6 節驗收 1–7 | 1（1）、3／4（2）、2（3）、4（4）、1／5（5）、5（6、7） |

與 spec 的小差異（Claude 判斷）：spec 預設已經是「固定液滴大小 3 mm」，所以另一份範例設定改成「液滴大小隨機」與「單滴訓練切片」，共三份範例。
