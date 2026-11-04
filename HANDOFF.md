# 交接

## 目前狀態（2026-11-04）
- 尚無程式碼。
- 設計文件：`docs/superpowers/specs/2026-10-21-simulator-design.md`，**使用者 2026-11-04 核可**。
- 實作計畫：`docs/superpowers/plans/2026-11-04-splash-simulator.md`，使用者 2026-11-04 啟動 Task 1（視為核可）。
- 預設實作方式：**① 半自動協作（Codex 實作、Claude 審查）**（使用者 2026-11-04 選定）。實際交派仍需使用者明確啟動（`/semi-auto-collab` 或「半自動執行 Task N」）。

## 下一步
- Task 1 進行中（分支 `task-1-config-flight`）：B3 規格檢查 → 1a → 1b → 審查。

## Task 分派
詳細檔案範圍見計畫中的「Task 分派總表」。一次一個 Task，合併 main 後才開下一個。

| Task | 名稱 | 負責人 | 分支 | 網路 | 狀態 |
|---|---|---|---|---|---|
| 1 | 骨架、設定與飛行物理 | Codex | task-1-config-flight | 是（uv sync） | 進行中 |
| 2 | 撞擊成形規則 | Codex | task-2-impact | 否 | 未開始 |
| 3 | 繪製、特徵量測、干擾、影像讀寫 | Codex | task-3-render | 否 | 未開始 |
| 4 | 場景取樣與資料集輸出 | Codex | task-4-scene-dataset | 否 | 未開始 |
| 5 | CLI、YOLO 匯出、範例設定、README | Codex | task-5-cli-docs | 否 | 未開始 |

共用檔案注意：`config.py`、`configs/default.yaml` 由 Task 1–4 依序各加自己的段落；`pyproject.toml`／`uv.lock` 只在 Task 1 宣告相依，Task 5 只加 `[project.scripts]`。

## 環境
- 開發機：Windows 11、Python 3.14.4、uv 0.11.9、git 2.51。
- 目標支援 Python ≥ 3.11，Windows／macOS，不需 GPU。
- 安裝、測試指令：實作後補上。

---

## Task 1：骨架、設定與飛行物理

### Claude 填寫（交派與審查）

- 負責人：Codex（實作）｜審查：Claude
- 分支：task-1-config-flight
- 風險等級：一般（不涉及登入、權限、付費、個資、對外輸入；設定檔是本機組員自己編輯的檔案）
- 推理強度：中等
- 需要網路：是（原因：Step 1 需 `uv sync` 下載 numpy、scipy、opencv-python-headless、pydantic、pyyaml、pytest 並產生 `uv.lock`）
- 檔案範圍：
  - `pyproject.toml`、`uv.lock`、`.python-version`
  - `src/splash_sim/__init__.py`、`src/splash_sim/config.py`、`src/splash_sim/geometry.py`、`src/splash_sim/flight.py`
  - `configs/default.yaml`
  - `tests/test_config.py`、`tests/test_geometry.py`、`tests/test_flight.py`
  - `HANDOFF.md`（只寫本區塊「Codex 填寫」欄）
- 必讀檔案：
  - `docs/superpowers/plans/2026-11-04-splash-simulator.md` 第 1–35 行（Global Constraints、Review Focus）與第 74–135 行（Task 1 全文）
  - `docs/superpowers/specs/2026-10-21-simulator-design.md` 第 39–47 行（限制）、第 71–78 行（5.1 飛行）、第 142–148 行（5.6 設定檢查）、第 160–163 行（驗收 1）
  - `~/.claude/policies/testing-policy.md`（TDD 原則）
- 設計約束摘要（索引；原文仍以上列檔案為準）：
  - TDD 垂直切片：一次一個失敗測試 → 最小實作 → 綠，禁止先寫完所有測試（來源：testing-policy.md:11-16）。
  - 相依只能是 numpy、scipy、opencv-python-headless、pydantic>=2、pyyaml，dev 為 pytest；本 Task 一次宣告完，`requires-python = ">=3.11"`（來源：plan:15-16）。
  - 座標：A4 左下角原點，x∈[0,210] mm、y∈[0,297] mm、z 向上；內部用 SI；畫布 2970×2100（rows, cols），10 px/mm，row = (297 − y)·10（來源：plan:17-18、plan:86）。
  - 設定欄位名帶單位後綴（`_m`、`_mm`、`_m_s`、`_deg`、`_s`、`_px`、`_kg_m3`、`_n_m`、`_pa_s`）（來源：plan:19）。
  - 所有 Pydantic 模型 `extra="forbid", frozen=True`；錯誤轉成中文 `ConfigError`，訊息含點號欄位路徑；未知欄位寫「不認得這個欄位」（來源：plan:80-85、plan:99-101）。
  - YAML 一律 UTF-8 讀寫；`default.yaml` 每欄有中文註解（意義、單位、出處），且必須與 `default_config()` 相等（來源：plan:23、plan:103-106）。
  - 飛行：重力 9.81；阻力 a = g − (3·ρ_air·C_d)/(4·ρ_liq·d)·|v|·v；C_d 為 Schiller–Naumann（Re<1000）或 0.44；`solve_ivp` 的 rtol=1e-10、atol=1e-12；`propagate` 允許負時長往回推（來源：plan:87-92）。
  - 精度：無阻力落點與解析解誤差 < 1e-5 m；往回積分回到起點的誤差 < 1e-5 m（來源：plan:115、plan:119；spec:161）。
  - 錯誤訊息一律繁體中文（來源：plan:20）。
- 參考段落：無大型參考檔。
- 施工階段：
  - 1a：plan Step 1–15（pyproject／uv sync、config.py、load_config、default.yaml、geometry.py）
  - 1b：plan Step 16–25（drag_coefficient、fly_to_plane、propagate、錯誤檢查、全套測試）
- 驗收標準：
  1. `uv sync` 成功並產生 `uv.lock`；`uv run pytest -q` 全綠。
  2. plan 中 Task 1 列出的每個測試名稱都存在且通過：test_default_config_values、test_load_config_rejects_bad_values、test_load_config_utf8_comments、test_default_yaml_matches_defaults、test_mm_px_roundtrip、test_drag_coefficient_regimes、test_no_drag_matches_projectile、test_backward_propagation_returns_to_source、test_drag_shortens_range、test_fly_rejects_start_below_plane。
  3. 設定錯誤訊息為中文且指出欄位路徑；含中文註解的 YAML 可正確載入。
  4. 修改只在檔案範圍內。
- 測試指令：局部 `uv run pytest tests/<檔名> -q`｜全套 `uv run pytest -q`｜lint：無｜型別檢查：無
- Claude 檢查紀錄：
  - 開工：已讀 testing-policy.md — 一次一個失敗測試、垂直切片，不為全綠放寬斷言。
  - 開工：frontend-codex.md／impeccable 不適用 — Task 1 沒有畫面或終端機介面（CLI 在 Task 5）。
  - 開工：review-animations 不適用 — 無動畫。
  - 開工：product-security-qa.md 不適用 — 風險等級一般。
  - 收尾：
- 審查輪次：0 / 2
- 累計 token：0
- 審查結果：

### Codex 填寫（施工）

狀態：
- 已完成階段：
- 修改內容：
- 測試指令與結果摘要：
- 簡短 QA：
- 教學重點：設計理由／替代方案／剩餘限制
- 範圍外需求：
- 退件回覆：
