"""
Quant-Framework 数据模块

这个模块提供了统一的数据加载和预处理接口，支持多种数据源。
主要功能包括：
- 抽象数据加载器基类
- 数据验证和清洗
- 多种数据源支持
- 时间序列数据处理
"""

from .base_data_loader import BaseDataLoader

__all__ = ["BaseDataLoader"]

__version__ = "1.0.0"