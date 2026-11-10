"""具明確單位與嚴格型別的模擬設定。"""

from pathlib import Path
from typing import Literal, get_origin

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator


class ConfigError(ValueError):
    """設定檔無法讀取或內容不符合規格。"""


class _ConfigModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    @field_validator("*", mode="before")
    @classmethod
    def yaml_sequences(cls, value, info):
        if get_origin(cls.model_fields[info.field_name].annotation) is tuple and isinstance(value, list):
            return tuple(value)
        return value


class LiquidConfig(_ConfigModel):
    density_kg_m3: float = Field(default=998.0, gt=0)
    surface_tension_n_m: float = Field(default=0.072, gt=0)
    viscosity_pa_s: float = Field(default=1.0e-3, gt=0)


class AirConfig(_ConfigModel):
    density_kg_m3: float = Field(default=1.204, gt=0)
    viscosity_pa_s: float = Field(default=1.81e-5, gt=0)
    drag_enabled: bool = True


class ImpactConfig(_ConfigModel):
    """成形係數出處與校正狀態詳見 configs/default.yaml。"""

    ruleset: str = "literature_v1"
    spread_a: float = Field(default=1.24, gt=0)
    angle_bias_deg: float = Field(default=0.0, gt=-90, lt=90)
    spine_a: float = Field(default=0.1443, ge=0)
    spine_b: float = Field(default=0.5, ge=0)
    spine_c: float = Field(default=0.25, ge=0)
    spine_min_weber: float = Field(default=10.0, ge=0)
    spine_length_frac: tuple[float, float] = (0.1, 0.35)
    spine_front_kappa: float = Field(default=3.0, ge=0)
    tail_coeff: float = Field(default=0.4, ge=0)
    satellite_min_weber: float = Field(default=150.0, ge=0)
    satellite_per_weber: float = Field(default=0.02, ge=0)
    satellite_max: int = Field(default=8, ge=0)
    satellite_size_frac: tuple[float, float] = (0.03, 0.12)
    paper: Literal["coated", "copy"] = "coated"
    bleed_mm: dict[str, float] = Field(default_factory=lambda: {"coated": 0.05, "copy": 0.4})
    jitter_frac: float = Field(default=0.05, ge=0, lt=1)

    @field_validator("spine_length_frac", "satellite_size_frac", mode="before")
    @classmethod
    def yaml_ranges(cls, value):
        return tuple(value) if isinstance(value, list) else value

    @field_validator("spine_length_frac", "satellite_size_frac")
    @classmethod
    def ordered_ranges(cls, value):
        if not 0 <= value[0] <= value[1]:
            raise ValueError("範圍必須由小到大且不得為負")
        return value


class RenderConfig(_ConfigModel):
    paper_rgb: tuple[int, int, int] = (245, 245, 240)
    dye_rgb: tuple[int, int, int] = (190, 30, 45)
    dye_opacity: tuple[float, float] = (0.6, 0.9)
    draw_spines: bool = True
    draw_tail: bool = True
    draw_satellites: bool = True


class StrengthEffect(_ConfigModel):
    enabled: bool = True
    strength: float = Field(default=6.0, ge=0)


class BlurEffect(_ConfigModel):
    enabled: bool = True
    sigma_px: tuple[float, float] = (0.0, 1.2)


class NoiseEffect(_ConfigModel):
    enabled: bool = True
    std: tuple[float, float] = (1.0, 4.0)


class JpegEffect(_ConfigModel):
    enabled: bool = True
    quality: tuple[int, int] = (75, 95)


class AugmentConfig(_ConfigModel):
    paper_texture: StrengthEffect = Field(default_factory=StrengthEffect)
    lighting: StrengthEffect = Field(default_factory=lambda: StrengthEffect(strength=0.08))
    blur: BlurEffect = Field(default_factory=BlurEffect)
    noise: NoiseEffect = Field(default_factory=NoiseEffect)
    jpeg: JpegEffect = Field(default_factory=JpegEffect)


class SimConfig(_ConfigModel):
    seed: int = Field(default=0, ge=0)
    liquid: LiquidConfig = Field(default_factory=LiquidConfig)
    air: AirConfig = Field(default_factory=AirConfig)
    impact: ImpactConfig = Field(default_factory=ImpactConfig)
    render: RenderConfig = Field(default_factory=RenderConfig)
    augment: AugmentConfig = Field(default_factory=AugmentConfig)


def default_config() -> SimConfig:
    return SimConfig()


def load_config(path: str | Path) -> SimConfig:
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise ConfigError(f"設定檔 {path} 無法讀取：請確認檔案存在、讀取權限與 UTF-8 編碼") from error
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as error:
        mark = getattr(error, "problem_mark", None)
        location = f"（第 {mark.line + 1} 行、第 {mark.column + 1} 欄）" if mark else ""
        raise ConfigError(f"設定檔 {path} 的 YAML 語法錯誤{location}：請檢查縮排、括號與冒號") from error
    try:
        return SimConfig.model_validate(data)
    except ValidationError as error:
        reasons = {
            "extra_forbidden": ("不認得這個欄位", "僅允許已定義的欄位"),
            "greater_than": ("數值必須大於 0", "大於 0"),
            "greater_than_equal": ("數值必須大於或等於 0", "大於或等於 0"),
            "float_type": ("必須填入數字，不能使用字串或其他型別", "數字"),
            "int_type": ("必須填入整數", "整數"),
            "bool_type": ("必須填入布林值", "true 或 false"),
            "model_type": ("必須填入設定物件", "欄位名稱與值的對應表"),
        }
        messages = []
        for detail in error.errors():
            field = ".".join(str(part) for part in detail["loc"]) or "根節點"
            reason, allowed = reasons.get(detail["type"], ("設定值不符合要求", "符合欄位的型別與限制"))
            messages.append(f"設定檔 {path} 的 {field} 欄：{reason}（合理範圍：{allowed}）")
        raise ConfigError("\n".join(messages)) from error
