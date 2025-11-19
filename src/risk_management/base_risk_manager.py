"""
基础风险管理器类
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd


class BaseRiskManager(ABC):
    """基础风险管理器抽象类
    
    所有风险管理器必须继承此类并实现必要的方法。
    负责监控和控制交易风险。
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        """初始化风险管理器
        
        Args:
            config: 配置字典，包含风险控制参数
        """
        self.config = config
        self._validate_config()
        self._position_limits = config.get('position_limits', {})
        self._stop_loss = config.get('stop_loss', 0.05)  # 默认5%止损
        self._take_profit = config.get('take_profit', 0.15)  # 默认15%止盈
        self._max_daily_loss = config.get('max_daily_loss', 0.02)  # 默认2%最大日损失

    @abstractmethod
    def _validate_config(self) -> None:
        """验证配置参数
        
        Raises:
            ValueError: 配置参数无效时抛出
        """
        pass

    @abstractmethod
    def check_risk(
        self, 
        signal: float, 
        current_position: float, 
        portfolio_value: float,
        current_price: float
    ) -> Tuple[bool, Dict[str, Any]]:
        """检查交易风险
        
        Args:
            signal: 交易信号 (-1, 0, 1)
            current_position: 当前持仓
            portfolio_value: 投资组合价值
            current_price: 当前价格
            
        Returns:
            (是否通过风险检查, 风险检查结果)
            
        Raises:
            RiskManagerError: 风险检查失败时抛出
        """
        pass

    @abstractmethod
    def calculate_position_size(
        self, 
        signal: float, 
        portfolio_value: float, 
        current_price: float,
        volatility: Optional[float] = None
    ) -> float:
        """计算风险调整后的仓位大小
        
        Args:
            signal: 交易信号 (-1, 0, 1)
            portfolio_value: 投资组合价值
            current_price: 当前价格
            volatility: 波动率（可选）
            
        Returns:
            调整后的仓位大小
        """
        pass

    def check_stop_loss_take_profit(
        self, 
        entry_price: float, 
        current_price: float, 
        position: float
    ) -> Dict[str, Any]:
        """检查止损止盈条件
        
        Args:
            entry_price: 入场价格
            current_price: 当前价格
            position: 当前持仓
            
        Returns:
            止损止盈检查结果
        """
        if position == 0:
            return {'action': 'none', 'reason': 'no_position'}
        
        # 计算收益率
        if position > 0:  # 多头仓位
            return_rate = (current_price - entry_price) / entry_price
        else:  # 空头仓位
            return_rate = (entry_price - current_price) / entry_price
        
        result = {
            'action': 'none',
            'reason': 'conditions_not_met',
            'return_rate': return_rate,
            'stop_loss_threshold': -self._stop_loss,
            'take_profit_threshold': self._take_profit
        }
        
        # 检查止损
        if return_rate <= -self._stop_loss:
            result['action'] = 'stop_loss'
            result['reason'] = f'触发止损，收益率: {return_rate:.2%}'
        
        # 检查止盈
        elif return_rate >= self._take_profit:
            result['action'] = 'take_profit'
            result['reason'] = f'触发止盈，收益率: {return_rate:.2%}'
        
        return result

    def check_position_limits(
        self, 
        proposed_position: float, 
        portfolio_value: float
    ) -> Tuple[bool, Dict[str, Any]]:
        """检查仓位限制
        
        Args:
            proposed_position: 拟建仓位
            portfolio_value: 投资组合价值
            
        Returns:
            (是否通过检查, 检查结果)
        """
        result = {
            'allowed': True,
            'reason': 'position_within_limits',
            'max_position': self._position_limits.get('max_position', portfolio_value),
            'max_position_pct': self._position_limits.get('max_position_pct', 1.0),
            'current_position_value': proposed_position
        }
        
        # 检查绝对金额限制
        max_position_value = result['max_position']
        if abs(proposed_position) > max_position_value:
            result['allowed'] = False
            result['reason'] = f'超过最大仓位金额限制: {max_position_value}'
        
        # 检查百分比限制
        max_position_pct = result['max_position_pct']
        position_pct = abs(proposed_position) / portfolio_value
        if position_pct > max_position_pct:
            result['allowed'] = False
            result['reason'] = f'超过最大仓位比例限制: {max_position_pct:.1%}'
            result['current_position_pct'] = position_pct
        
        return result['allowed'], result

    def calculate_var(
        self, 
        returns: pd.Series, 
        confidence_level: float = 0.05
    ) -> float:
        """计算风险价值(VaR)
        
        Args:
            returns: 收益率序列
            confidence_level: 置信水平
            
        Returns:
            VaR值
        """
        if returns.empty:
            return 0.0
        
        return abs(returns.quantile(confidence_level))

    def calculate_sharpe_ratio(
        returns: pd.Series, 
        risk_free_rate: float = 0.02
    ) -> float:
        """计算夏普比率
        
        Args:
            returns: 收益率序列
            risk_free_rate: 无风险利率
            
        Returns:
            夏普比率
        """
        if returns.empty or returns.std() == 0:
            return 0.0
        
        excess_returns = returns - risk_free_rate / 252  # 假设252个交易日
        return excess_returns.mean() / returns.std() * (252 ** 0.5)

    def get_risk_metrics(self, portfolio_history: pd.DataFrame) -> Dict[str, float]:
        """获取风险指标
        
        Args:
            portfolio_history: 投资组合历史数据
            
        Returns:
            风险指标字典
        """
        if portfolio_history.empty:
            return {}
        
        returns = portfolio_history['value'].pct_change().dropna()
        
        return {
            'volatility': returns.std() * (252 ** 0.5),
            'max_drawdown': self._calculate_max_drawdown(portfolio_history['value']),
            'var_95': self.calculate_var(returns, 0.05),
            'var_99': self.calculate_var(returns, 0.01),
            'sharpe_ratio': self.calculate_sharpe_ratio(returns)
        }

    def _calculate_max_drawdown(self, values: pd.Series) -> float:
        """计算最大回撤
        
        Args:
            values: 价值序列
            
        Returns:
            最大回撤值
        """
        if values.empty:
            return 0.0
        
        peak = values.expanding().max()
        drawdown = (values - peak) / peak
        return abs(drawdown.min())

    def validate_risk_config(self) -> bool:
        """验证风险配置
        
        Returns:
            配置是否有效
        """
        if self._stop_loss < 0 or self._stop_loss > 1:
            raise ValueError("止损比例必须在0-1之间")
        
        if self._take_profit < 0 or self._take_profit > 1:
            raise ValueError("止盈比例必须在0-1之间")
        
        if self._max_daily_loss < 0 or self._max_daily_loss > 1:
            raise ValueError("最大日损失比例必须在0-1之间")
        
        return True