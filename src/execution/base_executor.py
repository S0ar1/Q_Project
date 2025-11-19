"""
基础执行器类
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd


class BaseExecutor(ABC):
    """基础执行器抽象类
    
    所有交易执行器必须继承此类并实现必要的方法。
    负责将策略信号转换为实际交易。
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        """初始化执行器
        
        Args:
            config: 配置字典，包含执行相关参数
        """
        self.config = config
        self._validate_config()
        self._position = 0.0  # 当前持仓
        self._cash = 100000.0  # 可用现金，默认10万

    @abstractmethod
    def _validate_config(self) -> None:
        """验证配置参数
        
        Raises:
            ValueError: 配置参数无效时抛出
        """
        pass

    @abstractmethod
    def execute_order(
        self, 
        symbol: str, 
        side: str, 
        quantity: float, 
        price: float
    ) -> Dict[str, Any]:
        """执行交易订单
        
        Args:
            symbol: 交易标的代码
            side: 交易方向 ('buy' 或 'sell')
            quantity: 交易数量
            price: 交易价格
            
        Returns:
            执行结果字典
            
        Raises:
            ExecutorError: 订单执行失败时抛出
        """
        pass

    @abstractmethod
    def get_current_price(self, symbol: str) -> float:
        """获取当前市场价格
        
        Args:
            symbol: 交易标的代码
            
        Returns:
            当前价格
        """
        pass

    def execute_signals(
        self, 
        signals: pd.DataFrame, 
        prices: pd.DataFrame
    ) -> pd.DataFrame:
        """执行交易信号
        
        Args:
            signals: 策略信号DataFrame
            prices: 价格数据DataFrame
            
        Returns:
            交易执行结果DataFrame
        """
        execution_results = []
        
        for timestamp, row in signals.iterrows():
            signal = row['signal']
            position = row['position']
            
            if signal != 0 and timestamp in prices.index:
                current_price = prices.loc[timestamp, 'close']
                symbol = self.config.get('symbol', 'UNKNOWN')
                
                # 计算交易数量
                quantity = abs(position)
                side = 'buy' if signal > 0 else 'sell'
                
                # 执行订单
                try:
                    result = self.execute_order(symbol, side, quantity, current_price)
                    execution_results.append({
                        'timestamp': timestamp,
                        'symbol': symbol,
                        'side': side,
                        'quantity': quantity,
                        'price': current_price,
                        'signal': signal,
                        'status': 'executed',
                        'order_id': result.get('order_id', 'unknown')
                    })
                    
                    # 更新持仓
                    if side == 'buy':
                        self._position += quantity
                        self._cash -= quantity * current_price
                    else:
                        self._position -= quantity
                        self._cash += quantity * current_price
                        
                except Exception as e:
                    execution_results.append({
                        'timestamp': timestamp,
                        'symbol': symbol,
                        'side': side,
                        'quantity': quantity,
                        'price': current_price,
                        'signal': signal,
                        'status': 'failed',
                        'error': str(e)
                    })
        
        if execution_results:
            return pd.DataFrame(execution_results).set_index('timestamp')
        else:
            return pd.DataFrame()

    def get_portfolio_status(self) -> Dict[str, Any]:
        """获取投资组合状态
        
        Returns:
            投资组合状态字典
        """
        return {
            'position': self._position,
            'cash': self._cash,
            'total_value': self._cash + abs(self._position) * self.get_current_price(
                self.config.get('symbol', 'UNKNOWN')
            )
        }

    def validate_execution(self, execution: Dict[str, Any]) -> bool:
        """验证执行结果
        
        Args:
            execution: 执行结果字典
            
        Returns:
            是否验证通过
        """
        required_fields = ['symbol', 'side', 'quantity', 'price']
        
        for field in required_fields:
            if field not in execution:
                raise ValueError(f"执行结果缺少必要字段: {field}")
        
        if execution['quantity'] <= 0:
            raise ValueError("交易数量必须大于0")
        
        if execution['price'] <= 0:
            raise ValueError("交易价格必须大于0")
        
        if execution['side'] not in ['buy', 'sell']:
            raise ValueError("交易方向必须是 'buy' 或 'sell'")
        
        return True