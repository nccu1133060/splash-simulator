# 交接

## 目前狀態（2026-10-21）
- 專案剛建立，尚無程式碼。
- 設計文件草稿：`docs/superpowers/specs/2026-10-21-simulator-design.md`，**待使用者核可**。
- 預設實作方式：**① 半自動協作（Codex 實作、Claude 審查）**（使用者 2026-11-04 選定）。實際交派仍需使用者明確啟動（`/semi-auto-collab` 或「半自動執行 Task N」）。

## 下一步
1. 使用者核可設計文件。
2. 撰寫實作計畫 `docs/superpowers/plans/`，每個 Task 標明負責人（預設 Codex）與檔案範圍。
3. 使用者啟動半自動協作後交派 Codex。

## Task 分派
（計畫完成後填寫：負責人、檔案範圍）

## 環境
- 開發機：Windows 11、Python 3.14.4、uv 0.11.9、git 2.51。
- 目標支援 Python ≥ 3.11，Windows／macOS，不需 GPU。
- 安裝、測試指令：實作後補上。
