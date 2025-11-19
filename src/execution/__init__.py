"""
Quant-Framework 执行模块

这个模块提供了统一的交易执行接口，支持多种执行策略。
主要功能包括：
- 抽象执行器基类
- 订单执行管理
- 交易执行跟踪
- 投资组合状态管理
"""

from .base_executor import BaseExecutor

__all__ = ["BaseExecutor"]

__version__ = "1.0.0"