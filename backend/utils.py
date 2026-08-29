"""
Deprecated module: NeuroDebug utility module.
Please import from `utils.config` and `utils.logging` instead.
"""

from utils.config import Config
from utils.logging import configure_logging, get_logger

__all__ = ["Config", "configure_logging", "get_logger"]
