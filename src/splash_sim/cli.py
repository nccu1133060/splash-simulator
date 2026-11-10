"""供組員使用的繁體中文命令列入口。"""

import argparse
from pathlib import Path
import sys

from splash_sim.config import ConfigError, load_config
from splash_sim.dataset import generate_dataset, simulate_scene
from splash_sim.imageio import write_png
from splash_sim.scene import SceneSamplingError


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ConfigError(f"指令參數錯誤：{message}；請用 --help 查看用法")


def main(argv=None) -> int:
    parser = _Parser(description="飛濺溯源模擬器：產生附標準答案的 A4 水漬資料")
    subparsers = parser.add_subparsers(dest="command", required=True, title="操作")
    generate = subparsers.add_parser("generate", help="產生資料集")
    generate.add_argument("--config", required=True, help="UTF-8 YAML 設定檔")
    generate.add_argument("--out", default="datasets", help="輸出資料夾")
    generate.add_argument("--n", type=int, help="場景數，至少 1")
    generate.add_argument("--name", help="資料集名稱")
    preview = subparsers.add_parser("preview", help="產生一張預覽圖")
    preview.add_argument("--config", required=True, help="UTF-8 YAML 設定檔")
    preview.add_argument("--out", default="preview.png", help="輸出圖片路徑")
    preview.add_argument("--index", type=int, default=0, help="場景編號，從 0 起算")
    preview.add_argument("--open", action="store_true", help="用預設圖片檢視器開啟")
    export = subparsers.add_parser("export-yolo", help="匯出 YOLO 分割標註")
    export.add_argument("--dataset", required=True, help="既有資料集資料夾")
    try:
        args = parser.parse_args(argv)
        if args.command == "export-yolo":
            from splash_sim.yolo import export_yolo
            print(export_yolo(Path(args.dataset)))
            return 0
        cfg = load_config(args.config)
        if args.command == "preview":
            if args.index < 0:
                raise ConfigError("index 必須是大於或等於 0 的整數")
            write_png(Path(args.out), simulate_scene(cfg, args.index).image)
            print(args.out)
            if args.open:
                import webbrowser
                webbrowser.open(Path(args.out).resolve().as_uri())
        else:
            print(generate_dataset(cfg, Path(args.out), n_scenes=args.n, name=args.name))
        return 0
    except (ConfigError, SceneSamplingError) as error:
        print(str(error), file=sys.stderr)
        return 2
    except OSError as error:
        print(f"檔案操作失敗：{error.filename or '輸出路徑'}；請確認權限、磁碟空間或資料夾是否已存在", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
