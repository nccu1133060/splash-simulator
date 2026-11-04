# 交接

## 目前狀態（2026-11-04）
- 尚無程式碼。
- 設計文件：`docs/superpowers/specs/2026-10-21-simulator-design.md`，**使用者 2026-11-04 核可**。
- 實作計畫：`docs/superpowers/plans/2026-11-04-splash-simulator.md`，**待使用者審閱**。
- 預設實作方式：**① 半自動協作（Codex 實作、Claude 審查）**（使用者 2026-11-04 選定）。實際交派仍需使用者明確啟動（`/semi-auto-collab` 或「半自動執行 Task N」）。

## 下一步
1. 使用者審閱實作計畫。
2. 使用者說「半自動執行 Task 1」後交派 Codex。

## Task 分派
詳細檔案範圍見計畫中的「Task 分派總表」。一次一個 Task，合併 main 後才開下一個。

| Task | 名稱 | 負責人 | 分支 | 網路 | 狀態 |
|---|---|---|---|---|---|
| 1 | 骨架、設定與飛行物理 | Codex | task-1-config-flight | 是（uv sync） | 未開始 |
| 2 | 撞擊成形規則 | Codex | task-2-impact | 否 | 未開始 |
| 3 | 繪製、特徵量測、干擾、影像讀寫 | Codex | task-3-render | 否 | 未開始 |
| 4 | 場景取樣與資料集輸出 | Codex | task-4-scene-dataset | 否 | 未開始 |
| 5 | CLI、YOLO 匯出、範例設定、README | Codex | task-5-cli-docs | 否 | 未開始 |

共用檔案注意：`config.py`、`configs/default.yaml` 由 Task 1–4 依序各加自己的段落；`pyproject.toml`／`uv.lock` 只在 Task 1 宣告相依，Task 5 只加 `[project.scripts]`。

## 環境
- 開發機：Windows 11、Python 3.14.4、uv 0.11.9、git 2.51。
- 目標支援 Python ≥ 3.11，Windows／macOS，不需 GPU。
- 安裝、測試指令：實作後補上。
