"""設計 §5.4 的可重現影像干擾；不接觸幾何與遮罩。"""

import cv2
import numpy as np


def apply_augmentations(image, cfg, rng):
    out = image.astype(np.float32)
    height, width = image.shape[:2]
    if cfg.paper_texture.enabled:
        texture = rng.normal(0, cfg.paper_texture.strength, (max(2, height//32), max(2, width//32))).astype(np.float32)
        out += cv2.resize(texture, (width, height), interpolation=cv2.INTER_LINEAR)[..., None]
    if cfg.lighting.enabled:
        dx, dy = rng.uniform(-1, 1, 2) * cfg.lighting.strength
        field = 1 + np.linspace(-dx, dx, width, dtype=np.float32)[None, :] + np.linspace(-dy, dy, height, dtype=np.float32)[:, None]
        out *= field[..., None]
    if cfg.blur.enabled:
        sigma = rng.uniform(*cfg.blur.sigma_px)
        if sigma > 0:
            out = cv2.GaussianBlur(out, (0, 0), sigma)
    if cfg.noise.enabled:
        # 每個感光位置共用亮度雜訊，減少全尺寸 RGB 暫存記憶體。
        out += rng.normal(0, rng.uniform(*cfg.noise.std), (height, width)).astype(np.float32)[..., None]
    out = np.clip(np.rint(out), 0, 255).astype(np.uint8)
    if cfg.jpeg.enabled:
        quality = int(rng.integers(cfg.jpeg.quality[0], cfg.jpeg.quality[1]+1))
        success, data = cv2.imencode(".jpg", cv2.cvtColor(out, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, quality])
        if not success:
            raise ValueError("augment.jpeg 無法編碼影像")
        out = cv2.cvtColor(cv2.imdecode(data, cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)
    return out
