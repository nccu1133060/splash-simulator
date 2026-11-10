"""飛濺溯源模擬器。"""

__version__ = "0.1.0"

from splash_sim.config import ConfigError, SimConfig, default_config, load_config
from splash_sim.dataset import generate_dataset, simulate_scene, simulate_single_drop

__all__ = ["__version__", "ConfigError", "SimConfig", "default_config", "load_config",
           "generate_dataset", "simulate_scene", "simulate_single_drop"]
