"""
Quant-Framework 策略模块

这个模块提供了统一的策略开发接口，支持多种交易策略类型。
主要功能包括：
- 抽象策略基类
- 信号生成机制
- 仓位计算逻辑
- 策略回测支持
"""

from .base_strategy import BaseStrategy

__version__ = "1.0.0"
__all__ = ["BaseStrategy"]