"""
Quant-Framework 风险管理模块

这个模块提供了统一的风险管理接口，支持多种风险控制策略。
主要功能包括：
- 抽象风险管理基类
- 风险检查和控制
- 风险指标计算
- 止损止盈管理
"""

from .base_risk_manager import BaseRiskManager

__all__ = ["BaseRiskManager"]

__version__ = "1.0.0"