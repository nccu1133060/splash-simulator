# 交接

## 目前狀態（2026-11-11）
- Task 1–5 建置成果均已合併至本機 `main`；程式提交 `26e30c1`，合併後全套 101 項測試通過。自動開圖畫面仍受環境限制而未確認。
- 設計文件：`docs/superpowers/specs/2026-10-21-simulator-design.md`，**使用者 2026-11-04 核可**。
- 實作計畫：`docs/superpowers/plans/2026-11-04-splash-simulator.md`，使用者 2026-11-04 啟動 Task 1（視為核可）。
- 本輪實作方式：使用者直接授權 Codex 完成剩餘全部 Task、提交及合併，不逐 Task 再詢問；沿用目前資料夾、各 Task 分支。原半自動協作方式只作歷史紀錄。

## 下一步
- Task 1 已合併至本機 `main`，原分支保留。施工與審查紀錄：`docs/handoff-archive/2026-11-04-task-1.md`。
- 本輪計畫建置與本機合併已收尾；下一階段為以實拍資料校正／比對（M2），需另外啟動，不在本輪範圍。自動開圖畫面需在可用的桌面／瀏覽器環境補驗。

## Task 分派
詳細檔案範圍見計畫中的「Task 分派總表」。一次一個 Task，合併 main 後才開下一個。

| Task | 名稱 | 負責人 | 分支 | 網路 | 狀態 |
|---|---|---|---|---|---|
| 1 | 骨架、設定與飛行物理 | Codex | task-1-config-flight | 是（uv sync） | 已合併本機 main |
| 2 | 撞擊成形規則 | Codex | task-2-impact | 否 | 已合併 main（59f46cc） |
| 3 | 繪製、特徵量測、干擾、影像讀寫 | Codex | task-3-render | 否 | 已合併 main（8869a8a） |
| 4 | 場景取樣與資料集輸出 | Codex | task-4-scene-dataset | 否 | 已合併 main（1556e9c） |
| 5 | CLI、YOLO 匯出、範例設定、README | Codex | task-5-cli-docs | 否 | 已合併 main（26e30c1），開圖畫面驗收未確認 |

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
- Task 3 main 驗證：53 passed，exit 0；main=8869a8a。
- Task 4：完成三種場景、設定檢查、固定比例裁切、彩圖／uint16 主體與衛星遮罩、JSON／CSV／設定快照／版本與假設。全套（splash-task4-full）73 passed in 8.64s，exit 0。
- Task 4 QA：Python 真實入口驗證三種模式、源頭過遠有上限且中文提示、負高度／反向範圍拒絕、紙邊補色與 truncated；每滴圖片重新量測符合答案；相同設定含干擾的兩份資料集逐檔 SHA-256 相同。取樣 0–99 號預設場景，逐次記錄成功／SceneSamplingError，100/100 在 max_resample=50 內成功；已用正常案例與 source_offset_m=5/max_resample=3 的必失敗案例校準判定方式。未宣稱涵蓋所有種子。
- Task 4 教學：設定→抽樣／飛行／成形→圖片與遮罩→干擾→切片及答案；JSON 是詳細答題卡，CSV 是每滴一列。推薦版本與設定分存以便快照重讀，備援混存會破壞嚴格檢查。沒有新服務或費用；實拍／macOS 未測，重疊會遮住前滴。未觸發完整資安模擬。
- Task 4 安全檢查：非法張數與含 ../ 的名稱、suffix 在寫檔前拒絕，既有資料夾不覆寫。測試初版誤沿用預設 100 張已中斷，改為安全的一張合成資料後確認預期紅燈及修復綠燈；不影響產品設定。
- Ruling：為使衛星小滴母滴歸屬在檔案中保留，依 spec §5.4 另輸出 satellite_masks/（uint16）；不混入主體遮罩。代價：每張場景多一個遮罩檔。
- Ruling：場景獨立 RNG、序列化無時間戳記、圖片答案一致性在正確的最小實作下已通過；保留驗收證據，不故意先引入錯誤。
- Task 4 main 驗證：73 passed in 8.71s，exit 0；main=1556e9c。
- Task 5：CLI 三個入口、三份範例設定、YOLO 匯出、效能及 README 已建置。分支全套 `uv run pytest -q -p no:cacheprovider --basetemp=<TEMP>/splash-task5-final` → 101 passed in 39.48s，exit 0；git diff --check 通過。環境 Windows／CPython 3.11.15，沿用既有 uv cache/python 暫存變數。
- Final review：依 executing-plans／requesting-code-review，獨立唯讀 reviewer 檢查 Task 2–5 整體及計畫 Review Focus。無 Critical；三項 Important 已各自回歸紅→綠修復：反向範圍／無效 RGB／缺紙種暈染／無限數在設定入口拒絕；無效偏差角及無效直接撞擊參數拒絕；YOLO 分離可見區塊及孔洞保留。各修復後局部測試與上述全測通過，未用重複審查取代回歸驗證。
- Task 5 審查修正範圍：除原計畫檔案外，修復本輪產生的 config.py、impact.py、dataset.py、augment.py 與既有對應測試；未新增相依。這些均是本輪已授權建置的局部修復。
- Task 5 效能：第一次獨立 20 滴約 1.03–1.12 秒；首次全測遇到 3.80 秒而失敗（100 passed、1 failed），未忽略。cProfile 確認逐滴重掃全幅遮罩與干擾運算成本；改用一次找出外框、OpenCV 原地運算及減少浮點暫存後，局部三次 1.326／1.306／1.299 秒，且最終 101 項全測包含相同 <2 秒關卡通過。未放寬門檻，沒有宣稱適用所有硬體。
- Task 5 真實操作 QA：在新 PowerShell 程序依序 uv sync → uv run splash-sim preview --config configs/default.yaml --out datasets/preview.png --open → uv run splash-sim generate --config configs/default.yaml --n 10 --name acceptance，皆 exit 0。產物 datasets/acceptance_20261111-011330 有 10 scenes、10 主體遮罩、10 衛星遮罩、10 JSON、353 crops；再用真實 CLI export-yolo 產生 10 對 images/labels，所有複製圖片 SHA-256 等於原圖。
- Task 5 圖像 QA：確認原圖 2100×2970，縮至 700×990 的 datasets/preview_review.png 後實際檢視，包含斜向橢圓、毛刺、衛星、重疊、紙邊裁切及紙紋。只驗證影像管線外觀，非實拍物理認證。
- Task 5 開圖限制：--open 指令成功，但原生視窗觀察未能確認圖片，瀏覽器工具回報 browser access host unavailable；不把 exit 0 當成看見畫面，不宣稱 GUI 開圖驗收通過。PNG 產生及讀回、縮圖檢視已確認。此環境限制不改 CLI 的計畫介面。
- Task 5 教學：CLI→設定檢查→同一模擬管線→資料集／YOLO；雙入口比只留 Python 更方便組員，無新服務、GPU 或費用。YOLO 額外複製圖片有磁碟成本；物理／實拍、macOS 與開圖限制如上。設定錯誤已有真實檔案與跨 Python 程序測試，中文提示且無 traceback。
- Ruling：YOLO 原計畫 train=../scenes 無法對到 yolo/labels；改成 yolo/images 與 labels 同層，path 留空使載入器採 YAML 所在目錄。依 Ultralytics 官方 https://docs.ultralytics.com/datasets/segment/；代價為圖片額外磁碟空間。
- Ruling：保留所有模擬滴的場景真值，不新增 visibility 欄位；完全遮蔽者 bbox=[0,0,0,0]，README 明示估速訓練須排除。代價是訓練端需要篩選，不能把真值列數等同可見實例數。
- Ruling：YOLO 僅依計畫匯出，不自動決定訓練／驗證切分；README 明示 data.yaml 尚缺 val，非完整訓練設定。代價是組員需自行切分後補 val，未安裝或執行 Ultralytics 訓練（非核可相依）。
- Final review 未驗證事項裁定：以本輪完整全測／安裝／CLI 實際操作補足 reviewer 未跑項；開圖、實拍、文獻原文、macOS、跨平台 byte-identical 不在已驗證範圍，保持明示；既有 Ruling 保留；全遮蔽資料按上列規則處理；大規模種子掃描、資源上限與第三方漏洞掃描不擴增，本輪只對預設 100 種子及局部輸入做證據驗收。代價是這些未測範圍不能保證。
- Deferred minors：沒有新增 visibility 欄位、自動訓練分割／val 或大規模資源測試；本輪以文件明示限制，後續按實驗需求另議。HANDOFF 摘要已同步，STATUS 舊摘要未改。
- 尚無遠端／遠端 CI／部署流程；本輪僅本機建置與合併，無正式網站，不另建服務。全測後只更新文件並清理本輪產生的套件 metadata／測試暫存，不再改程式。
- 最終 main 驗證：2026-11-11，`uv run pytest -q -p no:cacheprovider --basetemp=<TEMP>/splash-main-final` → 101 passed in 19.28s，exit 0；來源 main=26e30c1，uv 重建本機套件後執行。之後僅本交接完成狀態更新及暫存清理，程式／相依／設定／測試不變。
- 分支均保留；最終交接補記由本輪直接授權的 Codex 提交。預覽 datasets/preview.png、縮圖 datasets/preview_review.png、十張資料集 datasets/acceptance_20261111-011330 與其 yolo/ 保留在已忽略的 datasets/ 下，不納入 Git。沒有 push／PR／部署。
