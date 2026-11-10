# 飛濺溯源模擬器

產生附有撞擊速度、角度與液滴編號的 A4 合成水漬資料，供形狀估速、影像分割及溯源流程驗證。這是本機 Python 工具，沒有圖形介面，不需 GPU 或付費服務。

```text
設定 → 場景取樣 → 飛行 → 撞擊幾何 → 圖片／遮罩 → 影像干擾 → 資料集
```

幾何是每滴的尺寸圖；遮罩是每滴的編號剪影。答案來自幾何，影像干擾只改彩圖，不改遮罩與速度答案。

## 安裝與三個指令起步

需要 Python ≥3.11 與 [uv](https://docs.astral.sh/uv/)。在專案資料夾開終端機，依序執行：

```powershell
uv sync
uv run splash-sim preview --config configs/default.yaml --open
uv run splash-sim generate --config configs/default.yaml --n 10
```

第二步產生並開啟 `preview.png`；第三步把十張場景與答案寫進 `datasets/dataset_<時間>/`。已存在的資料夾不覆寫；同一秒重跑可用 `--name` 換名稱，或等下一秒。

也可使用 `pip install -e .`，再執行 `splash-sim ...`。首次安裝需網路，之後產圖在本機進行。Windows 已測 Python 3.11；macOS 與其他 Python 版本尚未實機驗證。

## 操作

```powershell
# 指定輸出位置與資料集名稱
uv run splash-sim generate --config configs/default.yaml --out datasets --n 10 --name experiment
# 重產第 6 張場景；場景編號從 0 起算
uv run splash-sim preview --config configs/default.yaml --index 5 --out datasets/preview_6.png
# 匯出既有資料集的 YOLO 分割標註；請換成實際資料夾名稱
uv run splash-sim export-yolo --dataset datasets/experiment_YYYYmmdd-HHMMSS
```

成功回傳代碼 0；設定或場景取樣失敗回傳 2，終端機顯示中文原因及欄位。參數說明使用 `uv run splash-sim --help`。

## 設定怎麼改

YAML 是用縮排表示欄位的文字設定，像可編輯的實驗紀錄表。使用 UTF-8 存檔；`configs/default.yaml` 有完整欄位與單位註解，範例只寫需要修改的欄位，其餘使用預設。

| 範例 | 用途 |
|---|---|
| `configs/default.yaml` | 點源錐形噴射，直徑固定 3 mm |
| `configs/vertical_drop_calibration.yaml` | 各高度垂直滴落格點；關閉模糊與 JPEG |
| `configs/single_drop_training.yaml` | 跳過飛行，直接取樣撞擊狀態；預設 5000 張，可先用 `--n 10` |
| `configs/variable_droplet.yaml` | 噴射，直徑採 0.3–4 mm 對數均勻分布 |

- `seed` 控制重現；每張圖用種子與場景編號共同衍生亂數。
- `scene.mode`：`spray`、`vertical_drop`、`single`。
- `scene.spray`：高度、源頭水平範圍、錐角、速度、滴數、最少有效滴數與重抽上限。
- `impact`：成形係數、紙種與幾何尺度擾動。`jitter_frac: 0.0` 關閉尺度擾動。
- `render`：紙色、染料色與是否繪製毛刺、尾巴、衛星。
- `augment`：紙紋、光線、模糊、雜訊、JPEG；各有 `enabled` 開關。
- `output.crop_size_px`：切片邊長，至少 64；預設 384。切片不縮放、不旋轉。

數值不可加引號，未知欄位會拒絕；範圍須由小到大。噴射重抽仍失敗時，依錯誤提示檢查源頭範圍、發射條件與 `max_resample`，不要把失敗當成沒有水漬的正常資料。

## 座標與輸出

A4 左下角為原點，x=0–210 mm，y=0–297 mm，z 向上；內部飛行採公尺，答案位置用毫米。圖片寬 2100、高 2970 px，10 px/mm；圖片列座標向下，與紙面 y 方向相反。

```text
dataset_<時間>/
  config_snapshot.yaml         完整可讀回設定
  meta.json                    程式版本、場景數與簡化假設
  scenes/scene_00001.png        RGB 彩圖
  masks/scene_00001.png         uint16：0=背景，drop_id+1=液滴
  satellite_masks/...           uint16：衛星使用母滴編號
  crops/scene_00001_d000.png    固定尺度單滴切片
  labels/scene_00001.json       場景與每滴標準答案
  index.csv                    每滴一列，向量拆成 x/y/z 等欄位
```

場景檔名從 1 起算，對應內部場景編號 0；`drop_id` 從 0 起算。JSON 有源頭、發射／撞擊速度、撞擊角、方向、滴徑、無因次數、尺寸、毛刺與衛星數、外框、切片檔名、`truncated`。

`bbox_px=[x0,y0,x1,y1]` 使用右／下邊界不包含的像素範圍。後畫的水漬遮住先畫的水漬；外框是可見主體的外框。`truncated: true` 表示切片跨紙邊，或可見主體超出切片。紙外區域補紙色。

場景真值保留所有模擬滴；完全被其他水漬遮住的滴，外框為 `[0,0,0,0]`。形狀估速訓練時須排除這些零面積外框，不能把看不見的水漬當成有形狀線索的樣本。

同一份設定、場景編號、程式版本及相同套件環境會得到相同輸出。資料夾名稱可含時間，檔案內容不含時間戳記；跨平台／不同套件版本不保證逐位元組相同。

YOLO 匯出建立 `yolo/images/`、`yolo/labels/` 與 `yolo/data.yaml`，圖片與文字檔同名；圖片會另複製一份，占用額外磁碟。每個可見液滴一行、類別 0、座標正規化到 0–1；衛星不匯出，完全遮蔽的液滴不捏造輪廓。這是標註匯出，不包含模型或訓練；實驗前需自行劃分互不重複的訓練／驗證／測試資料。

同一滴的分離可見區塊及孔洞，用往返同一路徑的細連線保留在同一列多邊形中；回畫遮罩有一致性測試。資料夾安排依 [Ultralytics 官方分割資料格式](https://docs.ultralytics.com/datasets/segment/)。`data.yaml` 尚未含 `val`，是待完成資料分割的匯出設定，不能直接視為完整訓練設定。

## Python 使用

```python
from splash_sim import load_config, simulate_scene, simulate_single_drop, generate_dataset

cfg = load_config("configs/default.yaml")
scene = simulate_scene(cfg, index=0)
single = simulate_single_drop([1.0, 0.0, -2.0], diameter_mm=3.0, cfg=cfg, seed=42)
near_edge = simulate_single_drop([0.0, 0.0, -2.0], 3.0, cfg, center_mm=(2.0, 2.0))
folder = generate_dataset(cfg, "datasets", n_scenes=2, name="python_example")
```

自訂規則透過 Python 註冊；回傳同一種幾何資料，後續模組就能沿用。以下示範替換規則的接法，不是新物理定律：

```python
from dataclasses import replace
from splash_sim.impact import literature_v1, register_ruleset
def calibrated(center, velocity, diameter, liquid, impact, rng):
    stain = literature_v1(center, velocity, diameter, liquid, impact, rng)
    return replace(stain, ruleset="calibrated")
register_ruleset("calibrated", calibrated)
cfg = cfg.model_copy(update={"impact": cfg.impact.model_copy(update={"ruleset": "calibrated"})})
```

註冊只對目前 Python 程序有效；獨立 CLI 程序不會自動載入自訂函式。

## 形狀規則與證據狀態

| 規則 | 計畫採用的出處 | 狀態 |
|---|---|---|
| 球形飛行、重力、球體阻力 | Schiller–Naumann；設計 §5.1 | 已有文獻關係，未經水＋紙實拍驗證 |
| We、Re 的法向速度定義 | 標準無因次數定義；設計 §5.3 | 已有文獻 |
| 最大攤開內插式、A=1.24 | Laan et al., Physical Review Applied, 2014 | 待核對原文 |
| W/L 與撞擊角、可選偏差 | 經典橢圓關係；Joris 2017 | 幾何關係；偏差待實拍校正 |
| 毛刺冪次形式及係數 | Bhola & Chandra 1999／Mehdizadeh 2004 | 待核對原文，不當作已校準的水滴紙面定律 |
| 前緣集中、毛刺長度、尾巴、衛星 | 專題統整第十一節／設計 §5.3 定性關係 | 待實拍校正 |
| 暈染與兩種紙種寬度 | 設計 §5.3 | 影像近似，待實拍校正 |

主要限制：球形液滴不分裂、不蒸發、不互撞；未模擬紙張吸水；形狀公式部分來自其他液體或表面。合成資料的可重現與答案一致性不等於實驗正確性，最終估速效果須另用實拍測試集驗證。模擬與實拍比對工具屬第二里程碑，尚未建置。

## 驗證

```powershell
uv run pytest -q
# 若 Windows 暫存權限衝突，改用獨立目錄
uv run pytest -q -p no:cacheprovider --basetemp="$env:TEMP/splash-local-tests"
# 效能驗收（20 滴，含干擾及切片，三次取最快，門檻 2 秒）
uv run pytest tests/test_perf.py -q -s
```

沒有既有 lint、型別檢查、遠端 CI 或部署流程；本工具產生本機檔案，沒有正式網站。
