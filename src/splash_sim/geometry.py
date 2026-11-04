"""A4 左下角毫米座標與影像左上角像素座標的換算。"""

PX_PER_MM = 10
A4_WIDTH_MM = 210.0
A4_HEIGHT_MM = 297.0
CANVAS_SHAPE = (2970, 2100)


def mm_to_px(x_mm: float, y_mm: float) -> tuple[float, float]:
    """回傳 (col, row) 連續座標，不取整數也不裁切紙外座標。"""
    return x_mm * PX_PER_MM, (A4_HEIGHT_MM - y_mm) * PX_PER_MM


def px_to_mm(col: float, row: float) -> tuple[float, float]:
    return col / PX_PER_MM, A4_HEIGHT_MM - row / PX_PER_MM


def on_paper(x_mm: float, y_mm: float) -> bool:
    return 0 <= x_mm <= A4_WIDTH_MM and 0 <= y_mm <= A4_HEIGHT_MM
