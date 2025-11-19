"""
BaseStrategy 单元测试
"""

from datetime import datetime
from unittest.mock import Mock, patch
import pytest

import pandas as pd

from strategies.base_strategy import BaseStrategy


class MockStrategy(BaseStrategy):
    """测试用Mock策略"""
    
    def _validate_config(self) -> None:
        """验证配置"""
        if 'name' not in self.config:
            raise ValueError("配置中必须包含name")
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """生成测试信号"""
        signals = pd.DataFrame(index=data.index)
        signals['signal'] = 0
        signals['position'] = 0.0
        
        # 简单移动平均策略
        if len(data) >= 5:
            ma5 = data['close'].rolling(window=5).mean()
            ma20 = data['close'].rolling(window=20).mean()
            
            signals.loc[ma5 > ma20, 'signal'] = 1
            signals.loc[ma5 < ma20, 'signal'] = -1
            
            signals['position'] = signals['signal']
        
        return signals
    
    def calculate_position_size(
        self, 
        signal: float, 
        capital: float, 
        current_price: float
    ) -> float:
        """计算仓位大小"""
        if signal == 0:
            return 0.0
        
        # 简单的仓位计算：使用30%的资金
        position_value = capital * 0.3
        return position_value / current_price


class TestBaseStrategy:
    """BaseStrategy 测试类"""
    
    def test_init_with_valid_config(self) -> None:
        """测试有效配置初始化"""
        config = {'name': 'test_strategy'}
        strategy = MockStrategy(config)
        assert strategy.config == config
        assert strategy._position == 0
    
    def test_init_with_invalid_config(self) -> None:
        """测试无效配置初始化"""
        config = {}
        with pytest.raises(ValueError, match="配置中必须包含name"):
            MockStrategy(config)
    
    def test_validate_signals_valid(self) -> None:
        """测试有效信号验证"""
        config = {'name': 'test_strategy'}
        strategy = MockStrategy(config)
        
        dates = pd.date_range('2023-01-01', '2023-01-10')
        signals = pd.DataFrame({
            'signal': [1, -1, 0, 1, -1],
            'position': [1.0, -1.0, 0.0, 1.0, -1.0]
        }, index=dates)
        
        assert strategy.validate_signals(signals) is True
    
    def test_validate_signals_empty(self) -> None:
        """测试空信号验证"""
        config = {'name': 'test_strategy'}
        strategy = MockStrategy(config)
        
        with pytest.raises(ValueError, match="信号DataFrame不能为空"):
            strategy.validate_signals(pd.DataFrame())
    
    def test_validate_signals_missing_index(self) -> None:
        """测试缺少timestamp索引验证"""
        config = {'name': 'test_strategy'}
        strategy = MockStrategy(config)
        
        signals = pd.DataFrame({
            'signal': [1, -1, 0],
            'position': [1.0, -1.0, 0.0]
        })
        
        with pytest.raises(ValueError, match="信号DataFrame必须包含timestamp索引"):
            strategy.validate_signals(signals)
    
    def test_validate_signals_missing_columns(self) -> None:
        """测试缺少必要列验证"""
        config = {'name': 'test_strategy'}
        strategy = MockStrategy(config)
        
        dates = pd.date_range('2023-01-01', '2023-01-10')
        signals = pd.DataFrame({
            'signal': [1, -1, 0, 1, -1]
        }, index=dates)
        
        with pytest.raises(ValueError, match="信号DataFrame缺少必要列"):
            strategy.validate_signals(signals)
    
    def test_validate_signals_invalid_signal_values(self) -> None:
        """测试无效信号值验证"""
        config = {'name': 'test_strategy'}
        strategy = MockStrategy(config)
        
        dates = pd.date_range('2023-01-01', '2023-01-10')
        signals = pd.DataFrame({
            'signal': [1, 2, 0, -2, 1],  # 包含无效值2和-2
            'position': [1.0, 2.0, 0.0, -2.0, 1.0]
        }, index=dates)
        
        with pytest.raises(ValueError, match="信号值必须在"):
            strategy.validate_signals(signals)
    
    def test_preprocess_data(self) -> None:
        """测试数据预处理"""
        config = {'name': 'test_strategy'}
        strategy = MockStrategy(config)
        
        dates = pd.date_range('2023-01-01', '2023-01-10')
        data = pd.DataFrame({
            'open': [100] * len(dates),
            'high': [105] * len(dates),
            'low': [95] * len(dates),
            'close': [102] * len(dates),
            'volume': [1000] * len(dates)
        }, index=dates[::-1])  # 逆序
        
        processed_data = strategy.preprocess_data(data)
        
        # 检查是否按时间排序
        assert processed_data.index.equals(dates)
        
        # 检查必要列是否存在
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        assert all(col in processed_data.columns for col in required_columns)
    
    def test_get_strategy_info(self) -> None:
        """测试获取策略信息"""
        config = {'name': 'test_strategy', 'param1': 'value1'}
        strategy = MockStrategy(config)
        
        info = strategy.get_strategy_info()
        
        assert info['name'] == 'MockStrategy'
        assert info['config'] == config
        assert info['current_position'] == 0
    
    def test_calculate_position_size(self) -> None:
        """测试仓位大小计算"""
        config = {'name': 'test_strategy'}
        strategy = MockStrategy(config)
        
        # 测试中性信号
        position = strategy.calculate_position_size(0, 100000, 100)
        assert position == 0.0
        
        # 测试买入信号
        position = strategy.calculate_position_size(1, 100000, 100)
        expected_position = (100000 * 0.3) / 100  # 30%资金购买
        assert position == expected_position
        
        # 测试卖出信号
        position = strategy.calculate_position_size(-1, 100000, 100)
        assert position == expected_position