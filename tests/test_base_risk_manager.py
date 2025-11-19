"""
BaseRiskManager 单元测试
"""

from datetime import datetime
from unittest.mock import Mock, patch
import pytest

import pandas as pd
import numpy as np

from risk_management.base_risk_manager import BaseRiskManager


class MockRiskManager(BaseRiskManager):
    """测试用Mock风险管理器"""
    
    def _validate_config(self) -> None:
        """验证配置"""
        if 'name' not in self.config:
            raise ValueError("配置中必须包含name")
    
    def check_risk(
        self, 
        signal: float, 
        current_position: float, 
        portfolio_value: float,
        current_price: float
    ) -> tuple[bool, dict[str, Any]]:
        """检查风险"""
        # 简单的风险检查：不允许超过组合价值的90%
        max_position_pct = 0.9
        position_pct = abs(current_position) / portfolio_value
        
        allowed = position_pct <= max_position_pct
        result = {
            'allowed': allowed,
            'position_pct': position_pct,
            'max_allowed_pct': max_position_pct
        }
        
        return allowed, result
    
    def calculate_position_size(
        self, 
        signal: float, 
        portfolio_value: float, 
        current_price: float,
        volatility: float | None = None
    ) -> float:
        """计算仓位大小"""
        if signal == 0:
            return 0.0
        
        # 简单的仓位计算：使用40%的资金
        position_value = portfolio_value * 0.4
        return (position_value / current_price) * signal


class TestBaseRiskManager:
    """BaseRiskManager 测试类"""
    
    def test_init_with_valid_config(self) -> None:
        """测试有效配置初始化"""
        config = {
            'name': 'test_risk_manager',
            'stop_loss': 0.05,
            'take_profit': 0.15,
            'max_daily_loss': 0.02,
            'position_limits': {'max_position': 100000, 'max_position_pct': 0.8}
        }
        risk_manager = MockRiskManager(config)
        assert risk_manager.config == config
        assert risk_manager._stop_loss == 0.05
        assert risk_manager._take_profit == 0.15
        assert risk_manager._max_daily_loss == 0.02
    
    def test_init_with_invalid_config(self) -> None:
        """测试无效配置初始化"""
        config = {}
        with pytest.raises(ValueError, match="配置中必须包含name"):
            MockRiskManager(config)
    
    def test_check_risk_allowed(self) -> None:
        """测试允许的风险检查"""
        config = {'name': 'test_risk_manager'}
        risk_manager = MockRiskManager(config)
        
        allowed, result = risk_manager.check_risk(1, 50000, 100000, 100)
        
        assert allowed is True
        assert result['position_pct'] == 0.5
        assert result['max_allowed_pct'] == 0.9
    
    def test_check_risk_not_allowed(self) -> None:
        """测试不允许的风险检查"""
        config = {'name': 'test_risk_manager'}
        risk_manager = MockRiskManager(config)
        
        # 95%的仓位应该被拒绝
        allowed, result = risk_manager.check_risk(1, 95000, 100000, 100)
        
        assert allowed is False
        assert result['position_pct'] == 0.95
        assert result['max_allowed_pct'] == 0.9
    
    def test_calculate_position_size(self) -> None:
        """测试仓位大小计算"""
        config = {'name': 'test_risk_manager'}
        risk_manager = MockRiskManager(config)
        
        # 测试中性信号
        position = risk_manager.calculate_position_size(0, 100000, 100)
        assert position == 0.0
        
        # 测试买入信号
        position = risk_manager.calculate_position_size(1, 100000, 100)
        expected_position = (100000 * 0.4) / 100  # 40%资金购买
        assert position == expected_position
        
        # 测试卖出信号
        position = risk_manager.calculate_position_size(-1, 100000, 100)
        assert position == -expected_position
    
    def test_check_stop_loss_take_profit_stop_loss(self) -> None:
        """测试止损触发"""
        config = {'name': 'test_risk_manager', 'stop_loss': 0.05, 'take_profit': 0.15}
        risk_manager = MockRiskManager(config)
        
        result = risk_manager.check_stop_loss_take_profit(100, 94, 100)  # -6%损失
        
        assert result['action'] == 'stop_loss'
        assert '触发止损' in result['reason']
        assert result['return_rate'] == -0.06
    
    def test_check_stop_loss_take_profit_take_profit(self) -> None:
        """测试止盈触发"""
        config = {'name': 'test_risk_manager', 'stop_loss': 0.05, 'take_profit': 0.15}
        risk_manager = MockRiskManager(config)
        
        result = risk_manager.check_stop_loss_take_profit(100, 120, 100)  # +20%收益
        
        assert result['action'] == 'take_profit'
        assert '触发止盈' in result['reason']
        assert result['return_rate'] == 0.20
    
    def test_check_stop_loss_take_profit_none(self) -> None:
        """测试无触发条件"""
        config = {'name': 'test_risk_manager', 'stop_loss': 0.05, 'take_profit': 0.15}
        risk_manager = MockRiskManager(config)
        
        result = risk_manager.check_stop_loss_take_profit(100, 102, 100)  # +2%收益
        
        assert result['action'] == 'none'
        assert result['reason'] == 'conditions_not_met'
    
    def test_check_stop_loss_take_profit_no_position(self) -> None:
        """测试无持仓情况"""
        config = {'name': 'test_risk_manager', 'stop_loss': 0.05, 'take_profit': 0.15}
        risk_manager = MockRiskManager(config)
        
        result = risk_manager.check_stop_loss_take_profit(100, 102, 0)  # 无持仓
        
        assert result['action'] == 'none'
        assert result['reason'] == 'no_position'
    
    def test_check_position_limits_within_limits(self) -> None:
        """测试仓位在限制内"""
        config = {
            'name': 'test_risk_manager',
            'position_limits': {'max_position': 100000, 'max_position_pct': 0.8}
        }
        risk_manager = MockRiskManager(config)
        
        allowed, result = risk_manager.check_position_limits(50000, 100000)
        
        assert allowed is True
        assert result['allowed'] is True
        assert 'within_limits' in result['reason']
    
    def test_check_position_limits_exceed_amount(self) -> None:
        """测试超过金额限制"""
        config = {
            'name': 'test_risk_manager',
            'position_limits': {'max_position': 50000, 'max_position_pct': 0.8}
        }
        risk_manager = MockRiskManager(config)
        
        allowed, result = risk_manager.check_position_limits(60000, 100000)
        
        assert allowed is False
        assert result['allowed'] is False
        assert '超过最大仓位金额限制' in result['reason']
    
    def test_check_position_limits_exceed_percentage(self) -> None:
        """测试超过百分比限制"""
        config = {
            'name': 'test_risk_manager',
            'position_limits': {'max_position': 100000, 'max_position_pct': 0.5}
        }
        risk_manager = MockRiskManager(config)
        
        allowed, result = risk_manager.check_position_limits(60000, 100000)  # 60%
        
        assert allowed is False
        assert result['allowed'] is False
        assert '超过最大仓位比例限制' in result['reason']
    
    def test_calculate_var(self) -> None:
        """测试VaR计算"""
        config = {'name': 'test_risk_manager'}
        risk_manager = MockRiskManager(config)
        
        # 创建测试收益率数据
        returns = pd.Series([-0.05, -0.02, 0.01, 0.03, -0.01])
        var_95 = risk_manager.calculate_var(returns, 0.05)
        
        # 95%置信水平下，VaR应该是-0.05（5%分位数）
        assert abs(var_95 - 0.05) < 0.001
    
    def test_calculate_var_empty_series(self) -> None:
        """测试空序列VaR计算"""
        config = {'name': 'test_risk_manager'}
        risk_manager = MockRiskManager(config)
        
        var_95 = risk_manager.calculate_var(pd.Series(), 0.05)
        assert var_95 == 0.0
    
    def test_calculate_sharpe_ratio(self) -> None:
        """测试夏普比率计算"""
        config = {'name': 'test_risk_manager'}
        risk_manager = MockRiskManager(config)
        
        # 创建测试收益率数据
        returns = pd.Series([0.01, 0.02, -0.01, 0.03, 0.00])
        sharpe = risk_manager.calculate_sharpe_ratio(returns)
        
        # 夏普比率应该是一个数值
        assert isinstance(sharpe, float)
        assert not np.isnan(sharpe)
    
    def test_calculate_sharpe_ratio_empty_series(self) -> None:
        """测试空序列夏普比率计算"""
        config = {'name': 'test_risk_manager'}
        risk_manager = MockRiskManager(config)
        
        sharpe = risk_manager.calculate_sharpe_ratio(pd.Series())
        assert sharpe == 0.0
    
    def test_get_risk_metrics(self) -> None:
        """测试风险指标计算"""
        config = {'name': 'test_risk_manager'}
        risk_manager = MockRiskManager(config)
        
        # 创建测试投资组合历史数据
        dates = pd.date_range('2023-01-01', '2023-12-31', freq='D')
        portfolio_history = pd.DataFrame({
            'value': [100000 + i * 100 + np.random.normal(0, 1000) for i in range(len(dates))]
        }, index=dates)
        
        metrics = risk_manager.get_risk_metrics(portfolio_history)
        
        # 检查返回的指标
        expected_keys = ['volatility', 'max_drawdown', 'var_95', 'var_99', 'sharpe_ratio']
        for key in expected_keys:
            assert key in metrics
            assert isinstance(metrics[key], float)
    
    def test_validate_risk_config_valid(self) -> None:
        """测试有效风险配置验证"""
        config = {
            'name': 'test_risk_manager',
            'stop_loss': 0.05,
            'take_profit': 0.15,
            'max_daily_loss': 0.02
        }
        risk_manager = MockRiskManager(config)
        
        assert risk_manager.validate_risk_config() is True
    
    def test_validate_risk_config_invalid_stop_loss(self) -> None:
        """测试无效止损配置验证"""
        config = {
            'name': 'test_risk_manager',
            'stop_loss': 1.5,  # 超过1
            'take_profit': 0.15,
            'max_daily_loss': 0.02
        }
        risk_manager = MockRiskManager(config)
        
        with pytest.raises(ValueError, match="止损比例必须在0-1之间"):
            risk_manager.validate_risk_config()
    
    def test_validate_risk_config_negative_values(self) -> None:
        """测试负值配置验证"""
        config = {
            'name': 'test_risk_manager',
            'stop_loss': -0.05,
            'take_profit': 0.15,
            'max_daily_loss': 0.02
        }
        risk_manager = MockRiskManager(config)
        
        with pytest.raises(ValueError, match="止损比例必须在0-1之间"):
            risk_manager.validate_risk_config()