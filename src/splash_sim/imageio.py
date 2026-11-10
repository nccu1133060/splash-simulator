"""透過位元組讀寫 PNG，支援 Windows 中文路徑與 16-bit 遮罩。"""

from pathlib import Path

import cv2
import numpy as np


def write_png(path: Path, array: np.ndarray) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded_array = cv2.cvtColor(array, cv2.COLOR_RGB2BGR) if array.ndim == 3 else array
    success, data = cv2.imencode(".png", encoded_array)
    if not success:
        raise ValueError(f"影像 {path} 無法編碼 PNG")
    path.write_bytes(data.tobytes())


def read_png(path: Path, *, unchanged: bool = True) -> np.ndarray:
    data = np.frombuffer(Path(path).read_bytes(), dtype=np.uint8)
    array = cv2.imdecode(data, cv2.IMREAD_UNCHANGED if unchanged else cv2.IMREAD_COLOR)
    if array is None:
        raise ValueError(f"影像 {path} 無法解碼 PNG")
    return cv2.cvtColor(array, cv2.COLOR_BGR2RGB) if array.ndim == 3 else array
