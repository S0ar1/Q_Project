"""
基础策略类
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd


class BaseStrategy(ABC):
    """基础策略抽象类
    
    所有交易策略必须继承此类并实现必要的方法。
    确保所有返回的信号DataFrame都包含timestamp索引和与基类同名的列。
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        """初始化策略
        
        Args:
            config: 配置字典，包含策略相关参数
        """
        self.config = config
        self._validate_config()

    @abstractmethod
    def _validate_config(self) -> None:
        """验证配置参数
        
        Raises:
            ValueError: 配置参数无效时抛出
        """
        pass

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """生成交易信号
        
        Args:
            data: 市场数据DataFrame，必须包含timestamp索引
            
        Returns:
            信号DataFrame，包含timestamp索引和必要列
            
        Raises:
            StrategyError: 信号生成失败时抛出
        """
        pass

    @abstractmethod
    def calculate_position_size(
        self, 
        signal: float, 
        current_price: float
    ) -> float:
        """计算仓位大小建议
        
        根据交易信号和当前价格给出标准化的仓位大小建议，不考虑可用资金因素。
        
        Args:
            signal: 交易信号 (-1, 0, 1)
            current_price: 当前价格
            
        Returns:
            标准化的仓位大小建议（可以是百分比或相对值）
        """
        # 基类提供默认实现：直接返回信号的绝对值作为仓位比例
        # 实际策略可以重写此方法以提供更复杂的仓位计算逻辑
        return abs(signal)

    def validate_signals(self, signals: pd.DataFrame) -> bool:
        """验证信号DataFrame是否符合规范
        
        Args:
            signals: 信号DataFrame
            
        Returns:
            是否符合规范
            
        Raises:
            ValueError: 信号格式不正确时抛出
        """
        if signals.empty:
            raise ValueError("信号DataFrame不能为空")
        
        if not isinstance(signals.index, pd.DatetimeIndex):
            raise ValueError("信号DataFrame必须包含timestamp索引")
        
        required_columns = ['signal']
        missing_columns = [col for col in required_columns if col not in signals.columns]
        
        if missing_columns:
            raise ValueError(f"信号DataFrame缺少必要列: {missing_columns}")
        
        # 验证信号值
        valid_signals = {-1, 0, 1}
        invalid_signals = set(signals['signal'].unique()) - valid_signals
        
        if invalid_signals:
            raise ValueError(f"信号值必须在 {-1, 0, 1} 中，检测到无效值: {invalid_signals}")
        
        return True

    def preprocess_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """预处理数据
        
        Args:
            data: 原始数据DataFrame
            
        Returns:
            预处理后的DataFrame
        """
        # 确保数据按时间排序
        data = data.sort_index()
        
        # 确保必要的列存在
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        missing_columns = [col for col in required_columns if col not in data.columns]
        
        if missing_columns:
            raise ValueError(f"数据缺少必要列: {missing_columns}")
        
        return data

    def get_strategy_info(self) -> Dict[str, Any]:
        """获取策略信息
        
        Returns:
            策略信息字典
        """
        return {
            'name': self.__class__.__name__,
            'config': self.config
        }