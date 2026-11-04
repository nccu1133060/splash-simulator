"""具明確單位與嚴格型別的模擬設定。"""

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError


class ConfigError(ValueError):
    """設定檔無法讀取或內容不符合規格。"""


class _ConfigModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class LiquidConfig(_ConfigModel):
    density_kg_m3: float = Field(default=998.0, gt=0)
    surface_tension_n_m: float = Field(default=0.072, gt=0)
    viscosity_pa_s: float = Field(default=1.0e-3, gt=0)


class AirConfig(_ConfigModel):
    density_kg_m3: float = Field(default=1.204, gt=0)
    viscosity_pa_s: float = Field(default=1.81e-5, gt=0)
    drag_enabled: bool = True


class SimConfig(_ConfigModel):
    seed: int = Field(default=0, ge=0)
    liquid: LiquidConfig = Field(default_factory=LiquidConfig)
    air: AirConfig = Field(default_factory=AirConfig)


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
