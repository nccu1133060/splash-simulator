# 交接

## 目前狀態（2026-11-11）
- Task 1 程式已完成，經使用者本輪批准後快轉合併至本機 `main`（`3b2090a`）。
- 設計文件：`docs/superpowers/specs/2026-10-21-simulator-design.md`，**使用者 2026-11-04 核可**。
- 實作計畫：`docs/superpowers/plans/2026-11-04-splash-simulator.md`，使用者 2026-11-04 啟動 Task 1（視為核可）。
- 預設實作方式：**① 半自動協作（Codex 實作、Claude 審查）**（使用者 2026-11-04 選定）。實際交派仍需使用者明確啟動（`/semi-auto-collab` 或「半自動執行 Task N」）。

## 下一步
- Task 1 已合併至本機 `main`，原分支保留。施工與審查紀錄：`docs/handoff-archive/2026-11-04-task-1.md`。
- 下一個：Task 2（建議納入改善提案 P1），尚未啟動。

## Task 分派
詳細檔案範圍見計畫中的「Task 分派總表」。一次一個 Task，合併 main 後才開下一個。

| Task | 名稱 | 負責人 | 分支 | 網路 | 狀態 |
|---|---|---|---|---|---|
| 1 | 骨架、設定與飛行物理 | Codex | task-1-config-flight | 是（uv sync） | 已合併本機 main |
| 2 | 撞擊成形規則 | Codex | task-2-impact | 否 | 未開始 |
| 3 | 繪製、特徵量測、干擾、影像讀寫 | Codex | task-3-render | 否 | 未開始 |
| 4 | 場景取樣與資料集輸出 | Codex | task-4-scene-dataset | 否 | 未開始 |
| 5 | CLI、YOLO 匯出、範例設定、README | Codex | task-5-cli-docs | 否 | 未開始 |

共用檔案注意：`config.py`、`configs/default.yaml` 由 Task 1–4 依序各加自己的段落；`pyproject.toml`／`uv.lock` 只在 Task 1 宣告相依，Task 5 只加 `[project.scripts]`。

## 環境
- 開發機：Windows 11、Python 3.14.4、uv 0.11.9、git 2.51。
- 目標支援 Python ≥ 3.11，Windows／macOS，不需 GPU。
- 安裝：`uv sync`（首次需網路）。
- 全套測試：`uv run pytest -q`。Claude 端若遇 `pytest-of-andyc` PermissionError，加 `-p no:cacheprovider --basetemp=<scratchpad>/pt`（見歸檔 R1）。
- Codex 沙盒內需設 `UV_CACHE_DIR=$env:TEMP\splash-sim-uv-cache`、`UV_PYTHON_INSTALL_DIR=$env:TEMP\splash-sim-uv-python`。
- 尚無 lint／型別檢查關卡。

## 本輪狀態（2026-11-11：合併 Task 1）
- 授權與範圍：使用者明說「合併 TASK1」；僅合併既有成果及更新本交接，不實作 Task 2。開工工作區乾淨。
- 合併結果：`main` 從 `f407549` 快轉至 `3b2090a3c5c51bedb4d271cf831361ca14494752`，與 `task-1-config-flight` 指向相同提交，沒有衝突；原分支保留。
- 驗證：Windows、CPython 3.11.15，沿用上列 uv 暫存環境變數；合併前 `uv run pytest -q -p no:cacheprovider --basetemp="$env:TEMP\splash-merge-task1-pre-20261111"` → 16 passed in 28.20s，exit 0。
- 合併後測試曾因服務重啟遺失程序結果，因此不採用該次未確認結果；恢復後在 `main` 執行 `uv run pytest -q -p no:cacheprovider --basetemp="$env:TEMP\splash-merge-task1-recovery-20261111"` → 16 passed in 2.91s，exit 0。直接讀取 pytest 完整結果及程序退出碼，沒有篩選推算。
- QA：本輪沒有產品行為變更，沿用 Task 1 歸檔的使用者／數值物理 QA；本輪全測重新驗證設定、座標及飛行案例。不屬首次上線、主要發布或敏感功能變更，未追加完整資安模擬。
- 教學：已向使用者說明設定 → 參數檢查 → 飛行 → 撞擊結果的流程；推薦快轉合併以保留既有審查成果，備援為合併提交。沒有新相依、外部服務或費用；球形液滴及未經實拍／macOS 驗證的限制仍在。
- 剩餘限制：`git remote -v` 與 `git config --local --list` 均確認沒有設定遠端，因此未 push、未開 PR，也沒有遠端 CI／部署可追蹤；不宣稱已上線。原有 STATUS.md 仍是 Task 1 待合併舊摘要，本輪未改其負責範圍。
- 本輪局部決定：隔離 pytest 暫存目錄避免歸檔 R1；清理本輪套件建置產生的 `src/splash_sim.egg-info`。本交接更新依專案「只修改檔案、不提交」規則保留未提交，供 Claude 後續提交。

## 連續建置紀錄（計畫：docs/superpowers/plans/2026-11-04-splash-simulator.md）
- 使用者本輪授權：完成既有計畫所有 Task，預先批准各 Task 合併，不再逐次詢問。此次為使用者直接交辦，取代先前 Claude 提交／合併限制；Codex 自行實作，最後按 executing-plans 進行獨立審查。
- 工作區選擇：使用者選擇沿用目前資料夾、各 Task 分支。開工 main=3b2090a，只有上一輪 HANDOFF 修改，完整保留。
- 基線：2026-11-11 Windows／Python 3.11.15；uv run pytest -q -p no:cacheprovider --basetemp="$env:TEMP\splash-all-baseline" → 16 passed，exit 0。
- Pre-flight：Task 2→3 的幾何與毫米座標相容；Task 1→4 的飛行介面相容；Task 3→4 共用影像／遮罩及 RNG；Task 4→5 共用資料集結構與入口。待處理的計畫矛盾如下。
- Ruling：採用 Task 4 測試明定的 config_snapshot.yaml 僅含設定、版本放 meta.json；避免嚴格設定載入拒絕版本欄位。代價：與 spec 早期示例的版本位置不同，README 明示。
- Ruling：Task 4 切片測試要求指定中心，而 simulate_single_drop 原簽名缺該入口；增加可選 keyword-only center_mm（預設紙中心），原呼叫相容。代價：公開介面增加一個有測試的參數。
- Ruling：Windows 無直接執行 shell 輔助腳本的必要；以本 HANDOFF 作持久進度帳本，按原計畫逐 Task 分支／驗證／提交／合併，不另加套件或腳本相依。
- 前端詳規已讀：本計畫沒有 UI，輸出為依物理幾何定義的資料集影像，不新增網頁／HTML／圖形介面，故不適用 UI 設計及雙尺寸版面檢查。
- Task 2：完成；計畫指定 9 個測試及 YAML 範圍入口測試，各自紅→綠；全套 `.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider --basetemp=<TEMP>/splash-task2-full` → 26 passed，exit 0。P1 僅為建議，未擴大檔案範圍，沿用命令列隔離暫存。
- Task 2 QA／教學：真實 compute_stain 入口的垂直、斜撞、偏差、速度單調、毛刺集中、衛星門檻、自訂規則與可重現均經測試；YAML 正常範圍與反向範圍分別成功／中文拒絕。幾何先於像素，避免答案與圖使用不同公式；備援寫死規則不利校正。未發現本輪受測範圍未修復缺陷；實拍與跨平台未驗證，不觸發完整資安模擬。
- Ruling：W、L、尾巴共用同一隨機尺度，保留長寬比與撞擊角的一致性；代價是三者的尺寸擾動相關，不是獨立噪聲。
- Ruling：嚴格模型僅將 YAML 序列容器轉為 tuple，數值元素仍嚴格驗證；這是 YAML 清單與程式不可變序列的格式轉接，不將字串轉數字。
- Task 2 main 驗證：26 passed，exit 0；main=59f46cc。Task 3 基線沿用該次結果，程式未改。
- Task 3：PNG 中文路徑／RGB／uint16、橢圓繪製、九組角度量測、毛刺繪製及計數、尾巴／衛星分開遮罩、暈染、干擾啟閉均已測試；全套（splash-task3-full）53 passed，exit 0。對應計畫的首次缺少功能均見紅→綠。
- Task 3 QA：影像讀回與原陣列完全相同；實際繪製再量測九組角度與長寬比、0/6/12 毛刺。圖片與遮罩隔離，干擾不修改輸入。沒有 UI、實拍與跨平台驗證，未觸發完整資安模擬。
- Task 3 教學：幾何→局部像素→清楚遮罩及彩圖→僅彩圖加干擾；暈染與紙紋是影像近似。局部處理較整張圖逐滴模糊節省時間；無新相依／費用。
- Ruling：紙邊裁切、同種子相同干擾、不修改輸入在既有最小實作下已通過，保留為驗收測試，不為製造紅燈而故意破壞實作。新增毛刺／暈染／干擾效果曾各自失敗後實作。
