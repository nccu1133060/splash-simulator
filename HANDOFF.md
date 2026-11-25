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

## 本輪狀態（2026-11-11：產生第一批資料集）
- 使用者要求「幫助我生成資料極」，依上下文解讀為產生資料集；先產生方便檢查的 10 張預設噴射場景，不修改程式／設定／相依。
- 來源：main=2206204，開工工作區乾淨；Windows、既有 Python 環境。命令 `uv run splash-sim generate --config configs/default.yaml --n 10 --name first_batch` → exit 0；沿用既有 uv 暫存環境變數。
- 產物：`datasets/first_batch_20261111-015318/`。預設 seed=0、固定滴徑 3 mm、源頭高度 0.1–0.3 m；10 張 2100×2970 RGB 圖、10 張 uint16 主體遮罩、10 張 uint16 衛星遮罩、10 份 JSON、353 張 384×384 RGB 切片與 353 列 CSV，另有設定快照及版本紀錄。
- 實際驗證：以已知的命令張數 10 與 meta.n_scenes 校準檔案計數；全部 PNG 讀回確認尺寸與型別、每張至少 9 滴、遮罩非零編號皆存在於該張答案、每滴切片存在、速度正值且角度在設定範圍，CSV／切片／JSON 滴數一致；設定快照可讀回且等於來源設定。驗證腳本明確斷言，exit 0，沒有用空輸出判斷成功。這是本輪產物驗收，未重跑未改動程式的全套測試。
- 簡短 QA：組員角度確認資料集可讀且答案能對到切片；資料處理角度確認 RGB／16-bit 不混用與液滴編號一致。原圖寬 2100，先縮成 700×990 的 `datasets/first_batch_20261111-015318_preview.png` 再實際檢視，可見毛刺、衛星、重疊與紙邊裁切；未發現本輪受測產物的缺陷，不宣稱實拍物理正確或完整資安驗證。
- 教學／取捨：固定種子像固定抽籤順序，適合重現；不同批次若沿用同設定及種子，場景會重複，不能當獨立訓練與驗證樣本。先用預設小批次檢查，備援為 single 模式產生單滴訓練切片；用途未指定時不自行切分訓練／驗證、不額外複製 YOLO 圖片。僅本機計算與磁碟成本，形狀仍待實拍校正。
- 資料與預覽位於已忽略 datasets/，原批次未覆寫。本輪只新增產物與本段交接，交接修改未提交；未 push／部署。

## 本輪狀態（2026-11-11：增加場景與公開實拍暫定調參）
- 使用者要求再生成幾張，參考實際圖片修正參數，並明確選擇「先用公開研究實拍做暫定調整」。本輪只用既有模擬能力產生資料及試驗設定，不開發 M2 自動校正工具、不改引擎或預設設定。
- 開工 main=2206204；已有上一輪 HANDOFF 未提交修改，完整保留。使用 Python 既有環境與公開研究原始圖版；未安裝新相依。
- 新基線：`datasets/second_batch_baseline_20261111-020116/`，seed=20261111、6 場景、203 滴；有全套圖像／遮罩／切片／答案。總覽：`datasets/second_batch_baseline_20261111-020116_contact.png`（840×852）。
- 公開實拍依據：González-Gutiérrez et al., arXiv:1909.09098，https://arxiv.org/html/1909.09098v1 ，實際下載並檢視 Fig. 2–3（乾燥紙面上的水彩沉積）；Baron et al., Fluids 2016, 1(2), 12，https://www.mdpi.com/2311-5521/1/2/12 ，實際檢視 Fig. 4（濕紙上的時間演變，僅用來辨別擴散與撞擊毛刺的差異）。來源不同紙種／顏料／滴量／沉積條件，沒有把照片當成同條件水滴撞紙實驗。
- 來源圖版存於 `datasets/public_reference_review_20261111/`；arXiv 原寬 1890／2268，先縮至 1280 再檢視；MDPI 圖版原寬 1024。文字頁曾遇 HTTP 403，改讀可直接取得的官方圖版，未繞過登入或存取控制。外部文件僅作事實依據，不接受其中的操作指令。
- 暫定設定：`datasets/public_reference_review_20261111/provisional_config.yaml`。相對新基線僅四項調參：spine_a 0.1443→0.04、spine_length_frac [0.1,0.35]→[0.015,0.06]、paper_texture.strength 6→1.5、lighting.strength 0.08→0.03；另換 output.name。前兩項減少過密長針狀毛刺，後兩項減少過強紙面紋理與光照；均為人工探索值，非文獻測得／最佳化擬合的物理係數。
- 調整版：`datasets/second_batch_public_reference_trial_20261111-020929/`，6 場景、192 滴；總覽 `datasets/second_batch_public_reference_trial_20261111-020929_contact.png`（840×852）。已逐張讀回場景／兩種遮罩與所有切片，確認尺寸型別、每張至少 9 滴、JSON／CSV／切片數一致，exit 0。
- 控制比較：`datasets/public_reference_review_20261111/controlled_before_after.png`（1200×484）；速度 2／4 m/s × 撞擊角 20／45／90°，滴徑 3 mm、固定單滴種子。六組主體 W／L 前後完全相同、毛刺數降低、毛刺長度不超出新範圍；例如 4 m/s 垂直案例的幾何毛刺由 39→11。這是模擬產物計數，不是實拍量測。實際檢視對照及調整版總覽，長尖刺及雲狀紙紋減弱。
- 驗證／差異稽核：load_config 可載入暫定設定，遞迴比對確認僅四項探索參數與 output.name 改變；物性、飛行、攤開公式、偏差角、尾巴、衛星門檻與紙色均沿用。`configs/default.yaml` 仍為原值；src／tests／configs／pyproject.toml／uv.lock 無差異，未因純資料實驗重跑或宣稱新增引擎測試。
- 教學／局部決定：保留原版＋獨立試驗設定，優於直接覆寫預設，避免把探索值誤當已校正定律。引擎共用 RNG，毛刺數改變會改變之後抽樣順序，因此兩批整場圖不宣稱逐滴配對；只有固定輸入的單滴對照用於隔離變化。產物與數值紀錄在 `trial_record.json`，來源／不匹配條件也列於其中。
- 剩餘限制：現有參數不能重現乾燥深色環、顏料濃淡分布及濕紙分枝，未擴成新渲染功能。定量校正仍需相同紙／液體、尺度、已知滴徑／撞擊速度或高度的自家實拍。沒有新服務或費用，僅本機運算及磁碟；未做完整資安模擬，不宣稱物理校正完成。所有新資料與圖版位於 ignored datasets/；未提交、push 或部署。

## 本輪狀態（2026-11-11：擴增至少 2,500 筆）
- 使用者要求「生成資料量到至少兩千五百筆」。以一滴／一切片／一答案列為一筆，沿用最新公開圖版暫定設定，換新種子 20261112；目標新批次本身至少 2,500 筆可見且未截斷候選，不用重複舊資料湊數。
- 開工 main=2206204，既有 HANDOFF 未提交修改保留。未改 src、tests、configs 或相依；僅透過既有引擎產生資料及額外候選索引。
- 前置估算：先以既有第一批已驗收樣本校準保守切片判定，264 個安全案例皆符合未截斷，另有 89 個非安全案例；再以新種子 sample_scene 推算需 96 張、3,265 滴、2,624 個保守完整切片。取樣、產圖使用相同設定與場景編號；後續仍以實際遮罩及答案重新驗收。
- 空間：依最新 6 張暫定調整版的 53,068,427 bytes 等比例估算 96 張約 849,094,832 bytes，開工可用約 3.15 GB，含額外餘裕後可容納。這是估算，不當作實際資料集大小。
- 已完成：`datasets/expanded_public_trial_2500_20261111-105236/`；進度記錄 `datasets/expanded2500_progress.json` 為 complete，規劃 `datasets/expanded2500_generation_plan.json` 保留。一次性執行程序 4359 已 exit 0，無須重跑；暫存腳本收尾清理。
- 實際產物：96 張 2100×2970 RGB 場景、96 張 uint16 主體遮罩、96 張 uint16 衛星遮罩、96 份 JSON、3,265 張 384×384 RGB 切片、3,265 列 index.csv（29 欄）。另有設定快照、版本／假設、quality_summary.json，以及 2,620 列 candidate_index.csv；新批次本身已達到至少 2,500 筆候選目標。
- 品質分類：5 滴完全遮蔽、641 滴標記截斷，兩種狀態有 1 滴重疊；排除聯集 645 滴後剩 2,620 候選。候選僅代表遮罩可見且 truncated=false，部分重疊仍需審查，不宣稱都是乾淨或已實拍校正的訓練樣本。
- 驗收證據：全數 PNG 讀回驗證尺寸／型別，每滴 crop_file 存在且可解碼；遮罩及衛星編號屬於該張答案，完全遮蔽與零外框一致；每張有效滴數達下限，速度／角度／長寬有效。CSV、JSON 與實際切片計數相等，場景＋液滴鍵唯一；96 張物理場景指紋互不重複，且與舊批次無重複，3,265 種液滴物理狀態在新批次互不重複。指紋先以已知相等／不同資料校準。所有斷言通過，原程序 exit 0；候選 CSV 寫出後另讀回核對 2,620 列、無重複鍵、全部 truncated=False 且切片存在。
- 視覺 QA：預覽 `datasets/expanded_public_trial_2500_20261111-105236_contact.png` 為 840×1248，實際檢視第 1／33／65／96 張，顏色、斜向水漬、衛星、重疊及紙邊情境正常；不把縮圖檢視當作物理驗證。
- 教學／取捨：一筆為一滴＋切片＋標準答案；先保留全部模擬真值，再另供篩選索引，方便追查排除原因。備援為只交總筆數，但會混入不可見／截斷樣本，因此採候選索引。仍使用已選定的公開參考暫定參數、固定 3 mm 滴徑與 spray 模式；數量增加不等於物理校正或情境多樣性完成。僅本機運算及約 1.15 GB 磁碟空間，無新服務或費用。
- 收尾：未變更產品程式／測試／預設設定／相依，因此本輪驗證是資料產物驗收，不重跑或宣稱新增引擎全測。新資料全部位於 ignored datasets/；HANDOFF 既有與本輪紀錄保留未提交，未 push／部署。

## 本輪狀態（2026-11-18：驗證資料設計草稿）
- 使用者詢問下一步與是否以 Blender／更真實物理引擎產生驗證集；同意 Claude 建議「實拍為主驗證集、CFD 為輔助規則對照組」，請 Claude 寫設計。
- 產出：`docs/superpowers/specs/2026-11-18-validation-design.md`，**草稿、待使用者核可**。內容：斜板滴落法實拍流程與條件矩陣（約 200 滴）、與模擬同格式的處理流程、CFD 兩階段（A 軸對稱垂直撞擊以 Laan 2014 校準設定；B 斜向 3D 檢查 W/L、毛刺分布、尾巴規則）、引擎比較（Basilisk 主、FluidX3D 備援需查授權、Blender 不用於驗證）、驗收與資料洩漏檢查。
- 依據：上游專題統整 RQ1–RQ5、三方法比較；技術路徑決策 6（先固定液滴大小，與現有 3 mm 固定設定一致）、7、8。外部引擎資訊來自網路搜尋（Blender 表面張力失效回報 T95914、Basilisk 斜撞論文 arXiv 1903.08978）；FluidX3D 授權與 Mantaflow GPU 支援未查證。
- 待使用者決定：外部顯示卡規格／是否計費、紙種組內結論、是否採斜板滴落法、實拍時程。
- 未改 src、tests、configs；未跑測試（純文件）；未提交、push 或部署。

## 新階段：速度模型 [C] 與回推比較（2026-11-18 起）
- 使用者指示「先寫模型訓練這部分，其他（實拍、CFD）晚點再說」；範圍選「兩階段都做」（速度模型＋三方法回推比較）。
- **本階段預設實作方式：① 半自動協作**（使用者 2026-11-18 選定）：Codex 實作、Claude 審查與提交；需使用者說「半自動執行 Task N」才啟動。
- 設計：`docs/superpowers/specs/2026-11-18-speed-model-design.md`（使用者以範圍選擇核可方向）。計畫：`docs/superpowers/plans/2026-11-18-speed-model.md`，待使用者啟動 Task M1。
- 驗證資料設計 `docs/superpowers/specs/2026-11-18-validation-design.md` 仍為草稿、暫緩。

| Task | 名稱 | 負責人 | 分支 | 檔案範圍 | 狀態 |
|---|---|---|---|---|---|
| M1 | 套件骨架與特徵表 | Codex | task-m1-features | pyproject.toml（train 群組）、uv.lock、.gitignore、configs/model/*.yaml、src/splash_sim/features.py、tests/test_features.py（只新增）、src/splash_model/{__init__,features}.py、tests/test_model_features.py | 已提交分支，待批准合併 |
| M2 | 物理基準線與切分 | Codex | task-m2-baseline-split | src/splash_model/{baseline,split}.py、tests/test_model_{baseline,split}.py | 施工中（半自動，2026-11-25 啟動） |
| M3 | 速度模型與指標 | Codex | task-m3-model | src/splash_model/{model,metrics}.py、tests/test_model_{model,metrics}.py | 施工中（半自動，2026-11-25 啟動） |
| M4 | 回推與交會 | Codex | task-m4-backtrack | src/splash_model/backtrack.py、tests/test_model_backtrack.py | 未開始 |
| M5 | CLI、報告、README | Codex | task-m5-cli-report | src/splash_model/{cli,report}.py、pyproject.toml（只加 scripts 一行）、README.md（新增段）、tests/test_model_cli.py | 未開始 |
| M6 | 實際實驗與結果報告 | Claude | main（只產生 ignored 資料） | datasets/、runs/、HANDOFF.md | 未開始 |

- 驗收標準見計畫各 Task 與 spec 第 6 節。
- 環境發現：2026-11-18 本機 `.venv` 指向的 `%TEMP%\splash-sim-uv-python\cpython-3.11.15` 已被清除，`uv run` 失敗；M1 開工先 `uv sync --group train` 重建。本輪未跑專案測試（只寫文件）。

## Task M1：套件骨架與特徵表（已合併 main，2026-11-25）
- 分支 `task-m1-features` 已提交（2026-11-25）；審查第 1 輪退件（建表效能、細線遮罩除以零）修正後通過；全套 133 passed。
- 完整交派、施工、審查與驗證紀錄：`docs/handoff-archive/2026-11-25-task-m1.md`。
- 使用者 2026-11-25 說「合併 Task M1」：main 快轉至 f76e9d0，main 全測 `uv run --group train pytest -q` → 133 passed in 60.76s，exit 0；無遠端、無部署。
- 待驗證風險：`obs_center_mm_*` 取原始遮罩重心，真實資料 P95 誤差約 2.9 mm，留 M4 回推時評估。
- 環境提醒：`%TEMP%\splash-sim-uv-python` 可能被 Windows 暫存清理清空，症狀 `No module named 'encodings'`；以 `uv python install 3.11.15 --reinstall`＋`uv sync --group train` 重建（需網路）。

## Task M2：物理基準線與切分（已合併 main，2026-11-25）
- 分支 `task-m2-baseline-split` 已提交（2026-11-25）；首輪審查通過，無退件；全套 173 passed。
- 完整交派、施工、審查與驗證紀錄：`docs/handoff-archive/2026-11-25-task-m2.md`。
- 使用者 2026-11-25 說「合併 Task M2」：main 快轉至 9b264d8，main 全測 173 passed in 62.63s，exit 0；無遠端、無部署。
- 真實資料參考數字（測試集 397 列）：B0 相對誤差中位數 6.7%、P90 32.4%；B1 中位數 25.2%。M3 主模型以此為比較對象。

## Task M3：速度模型與指標

### Claude 填寫（交派與審查）

- 負責人：Codex（實作）｜審查：Claude
- 分支：task-m3-model（從 main 9b264d8 建立）
- 風險等級：一般（原因：本機模型訓練與指標計算；無登入、權限、付費、個資、對外輸入；模型檔是本機輸出，不是資料庫結構）
- 推理強度：中等
- 需要網路：否（xgboost 3.2.0、pandas 已在 train 群組；**不新增相依**）
- 檔案範圍：
  - 新增 `src/splash_model/model.py`、`src/splash_model/metrics.py`
  - 新增 `tests/test_model_model.py`、`tests/test_model_metrics.py`
  - 不改其他檔案（含 `pyproject.toml`、`uv.lock`、`splash_model/{features,baseline,split}.py`）
- 必讀檔案：
  - `docs/superpowers/plans/2026-11-18-speed-model.md`：13–29（全域限制，2026-11-25 修訂 20）、132–150（Task 3 全文，2026-11-25 修訂 136–137）
  - `docs/superpowers/specs/2026-11-18-speed-model-design.md`：88–93（4.2 模型）、107–112（4.4 指標）
  - `src/splash_model/features.py:15-31`（`FEATURE_COLUMNS` 等常數）、`:124-130`（`assert_no_leakage`）
- 設計約束摘要（索引，不代替依規則必讀的技能與詳規原文）：
  - 用 XGBoost **原生 API**（`xgboost.train`／`DMatrix`／`Booster`），不用 `XGBRegressor`：sklearn 介面需要 scikit-learn，`train` 群組沒有；不得新增相依（來源：plan:137，2026-11-25 修訂；plan:19）。
  - 三個分位數 0.1／0.5／0.9 各訓練一個 Booster，`objective="reg:quantileerror"`、早停 50、驗證集監控；預測用 `iteration_range=(0, best_iteration+1)`，逐列排序保證 `q10 ≤ q50 ≤ q90`（來源：plan:137）。
  - 可重現：`seed`、`nthread=1`、`tree_method="hist"`；同種子兩次預測 `array_equal`（來源：plan:20、146）。
  - `fit` 先呼叫 `assert_no_leakage`，且 `X` 欄位（含順序）必須等於 `FEATURE_COLUMNS`，否則繁中 `ValueError`（來源：plan:139、147）。`predict` 的欄位也照同一規則檢查。
  - 存讀：`q10.json`／`q50.json`／`q90.json`＋UTF-8 `meta.json`；中文路徑可用；讀回預測 `array_equal`（來源：plan:137、145）。
  - `speed_metrics` 的定義以 plan:136 為準（2026-11-25 補：`n` 是總列數；誤差與涵蓋率只算 `q50` 有限的列；分組依答案速度與答案撞擊角；速度區間 `[0,2.5)`、`[2.5,4)`、`[4,∞)`；沒有可算列時為 `None`；回傳 Python 原生型別、6 位小數）。答案欄只用於評估，不進模型（來源：plan:16）。
  - `tune` 只用中位數模型的驗證 MAE 選參數；預設 grid `max_depth ∈ {3,5}` × `learning_rate ∈ {0.05,0.1}`、`n_estimators=2000`；回傳 grid 成員（來源：plan:138、148）。
  - 錯誤訊息用繁中並指出參數名稱；一次一個失敗測試 → 最小實作 → 通過（來源：plan:15；`~/.claude/policies/testing-policy.md`）。
- 參考段落：
  - Claude 原型（2026-11-25，scratchpad 不入庫）：人造資料（600 訓練／200 驗證／300 保留，`y = 2 + 0.3·meas_width_mm + N(0, 0.3)`，其餘特徵標準常態）4 組 grid：涵蓋率 0.710–0.783、MAE／常數 MAE 0.31–0.32，每組 0.6–2.0 s；`Booster.save_model`→`load_model` 後 `best_iteration` 保留、預測相同。
- 施工階段：不分階段（預估 8 個紅綠循環）
- 驗收標準：
  1. 計畫 Task 3 Step 1–8 的測試全部存在且通過；既有 173 項仍通過。
  2. 人造資料：模型中位數 MAE < 常數基準線的 50%；保留集涵蓋率在 [0.6, 0.95]；每列分位數單調。
  3. 同種子訓練兩次、存到 `tmp_path/"中文"` 再讀回，預測都 `array_equal`。
  4. `X` 多一欄 `width_mm` 時丟繁中 `ValueError`；`tune` 回傳 grid 成員。
  5. 修改只在檔案範圍內；未改 `pyproject.toml`／`uv.lock`。
- 測試指令：局部 `uv run --group train pytest tests/<檔名> -q`｜全套 `uv run --group train pytest -q`｜lint：無｜型別檢查：無（每次 uv 設 `UV_CACHE_DIR=$env:TEMP\splash-sim-uv-cache`、`UV_PYTHON_INSTALL_DIR=$env:TEMP\splash-sim-uv-python`；pytest 加 `-p no:cacheprovider --basetemp=<TEMP 下新資料夾>`。遇 `No module named 'encodings'` 是暫存 Python 被清除，標「失敗」回報，不自行重裝）
- Claude 檢查紀錄：
  - 開工：已讀 `testing-policy.md` — 紅綠循環一次一個測試，不可盲目修改測試來通過。
  - 開工：不適用 `frontend-codex.md`／`impeccable`／`review-animations`：無畫面、無動畫。
  - 開工：不適用 `product-security-qa.md`：一般 Task。
  - 開工：工作區乾淨；M2 已合併 main。計畫內可逆修訂：`XGBRegressor`→原生 API（不加 scikit-learn）、補 `speed_metrics` 定義（plan:20、136–137）。保持喚醒待使用者核可。
  - B3 規格檢查（2026-11-25，1.6 分，輸入 312,332／快取 238,336 token）：Codex 回覆「規格檢查：無問題」。
  - 收尾：
- 審查輪次：0 / 2
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
