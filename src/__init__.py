"""
Quant-Framework 量化交易框架
"""

__version__ = "1.0.0"
__author__ = "Quant-Framework Team"

# 导入核心模块
from .data.base_data_loader import BaseDataLoader
from .strategies.base_strategy import BaseStrategy
from .execution.base_executor import BaseExecutor
from .risk_management.base_risk_manager import BaseRiskManager
from .config.base_config import BaseConfig

# 导出公共接口
__all__ = [
    "BaseDataLoader",
    "BaseStrategy", 
    "BaseExecutor",
    "BaseRiskManager",
    "BaseConfig"
]