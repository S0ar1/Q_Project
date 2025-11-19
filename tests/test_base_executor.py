"""
BaseExecutor 单元测试
"""

from datetime import datetime
from unittest.mock import Mock, patch
import pytest

import pandas as pd

from execution.base_executor import BaseExecutor


class MockExecutor(BaseExecutor):
    """测试用Mock执行器"""
    
    def _validate_config(self) -> None:
        """验证配置"""
        if 'symbol' not in self.config:
            raise ValueError("配置中必须包含symbol")
    
    def execute_order(
        self, 
        symbol: str, 
        side: str, 
        quantity: float, 
        price: float
    ) -> dict[str, Any]:
        """执行模拟订单"""
        return {
            'order_id': f'{symbol}_{side}_{quantity}_{price}',
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'price': price,
            'status': 'filled'
        }
    
    def get_current_price(self, symbol: str) -> float:
        """获取模拟当前价格"""
        return 100.0


class TestBaseExecutor:
    """BaseExecutor 测试类"""
    
    def test_init_with_valid_config(self) -> None:
        """测试有效配置初始化"""
        config = {'symbol': 'AAPL'}
        executor = MockExecutor(config)
        assert executor.config == config
        assert executor._position == 0.0
        assert executor._cash == 100000.0
    
    def test_init_with_invalid_config(self) -> None:
        """测试无效配置初始化"""
        config = {}
        with pytest.raises(ValueError, match="配置中必须包含symbol"):
            MockExecutor(config)
    
    def test_execute_signals(self) -> None:
        """测试信号执行"""
        config = {'symbol': 'AAPL'}
        executor = MockExecutor(config)
        
        # 创建测试信号
        dates = pd.date_range('2023-01-01', '2023-01-10')
        signals = pd.DataFrame({
            'signal': [1, -1, 0, 1, 0],
            'position': [100, -100, 0, 50, 0]
        }, index=dates)
        
        # 创建价格数据
        prices = pd.DataFrame({
            'close': [100 + i for i in range(len(dates))]
        }, index=dates)
        
        execution_results = executor.execute_signals(signals, prices)
        
        # 检查执行结果
        assert len(execution_results) == 3  # 3个非零信号
        
        # 检查第一个买入信号
        first_buy = execution_results[execution_results['side'] == 'buy'].iloc[0]
        assert first_buy['quantity'] == 100
        assert first_buy['status'] == 'executed'
        
        # 检查第一个卖出信号
        first_sell = execution_results[execution_results['side'] == 'sell'].iloc[0]
        assert first_sell['quantity'] == 100
        assert first_sell['status'] == 'executed'
    
    def test_get_portfolio_status(self) -> None:
        """测试获取投资组合状态"""
        config = {'symbol': 'AAPL'}
        executor = MockExecutor(config)
        
        status = executor.get_portfolio_status()
        
        assert status['position'] == 0.0
        assert status['cash'] == 100000.0
        assert 'total_value' in status
    
    def test_validate_execution_valid(self) -> None:
        """测试有效执行结果验证"""
        config = {'symbol': 'AAPL'}
        executor = MockExecutor(config)
        
        execution = {
            'symbol': 'AAPL',
            'side': 'buy',
            'quantity': 100,
            'price': 105.0
        }
        
        assert executor.validate_execution(execution) is True
    
    def test_validate_execution_missing_fields(self) -> None:
        """测试缺少字段的执行结果验证"""
        config = {'symbol': 'AAPL'}
        executor = MockExecutor(config)
        
        # 缺少必要字段
        execution = {
            'symbol': 'AAPL',
            'side': 'buy'
            # 缺少 quantity 和 price
        }
        
        with pytest.raises(ValueError, match="执行结果缺少必要字段"):
            executor.validate_execution(execution)
    
    def test_validate_execution_invalid_quantity(self) -> None:
        """测试无效数量的执行结果验证"""
        config = {'symbol': 'AAPL'}
        executor = MockExecutor(config)
        
        execution = {
            'symbol': 'AAPL',
            'side': 'buy',
            'quantity': 0,  # 无效数量
            'price': 105.0
        }
        
        with pytest.raises(ValueError, match="交易数量必须大于0"):
            executor.validate_execution(execution)
    
    def test_validate_execution_invalid_price(self) -> None:
        """测试无效价格的执行结果验证"""
        config = {'symbol': 'AAPL'}
        executor = MockExecutor(config)
        
        execution = {
            'symbol': 'AAPL',
            'side': 'buy',
            'quantity': 100,
            'price': 0  # 无效价格
        }
        
        with pytest.raises(ValueError, match="交易价格必须大于0"):
            executor.validate_execution(execution)
    
    def test_validate_execution_invalid_side(self) -> None:
        """测试无效交易方向的执行结果验证"""
        config = {'symbol': 'AAPL'}
        executor = MockExecutor(config)
        
        execution = {
            'symbol': 'AAPL',
            'side': 'invalid',  # 无效方向
            'quantity': 100,
            'price': 105.0
        }
        
        with pytest.raises(ValueError, match="交易方向必须是 'buy' 或 'sell'"):
            executor.validate_execution(execution)
    
    def test_position_and_cash_update(self) -> None:
        """测试持仓和现金更新"""
        config = {'symbol': 'AAPL'}
        executor = MockExecutor(config)
        
        # 执行买入订单
        result = executor.execute_order('AAPL', 'buy', 100, 100.0)
        executor._position += 100
        executor._cash -= 100 * 100.0
        
        assert executor._position == 100
        assert executor._cash == 90000.0
        
        # 执行卖出订单
        result = executor.execute_order('AAPL', 'sell', 50, 105.0)
        executor._position -= 50
        executor._cash += 50 * 105.0
        
        assert executor._position == 50
        assert executor._cash == 95250.0