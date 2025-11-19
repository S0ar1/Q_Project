"""
BaseDataLoader 单元测试
"""

from datetime import datetime
from unittest.mock import Mock, patch
import pytest

import pandas as pd

from data.base_data_loader import BaseDataLoader


class MockDataLoader(BaseDataLoader):
    """测试用Mock数据加载器"""
    
    def _validate_config(self) -> None:
        """验证配置"""
        if 'symbol' not in self.config:
            raise ValueError("配置中必须包含symbol")
    
    def load_data(
        self, 
        symbol: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> pd.DataFrame:
        """加载测试数据"""
        dates = pd.date_range(start_date, end_date, freq='D')
        data = pd.DataFrame({
            'open': range(len(dates)),
            'high': range(1, len(dates) + 1),
            'low': range(-1, len(dates) - 1),
            'close': range(len(dates)),
            'volume': [1000] * len(dates)
        }, index=dates)
        return data
    
    def get_available_symbols(self) -> list[str]:
        """获取可用标的"""
        return ['AAPL', 'GOOGL', 'MSFT']


class TestBaseDataLoader:
    """BaseDataLoader 测试类"""
    
    def test_init_with_valid_config(self) -> None:
        """测试有效配置初始化"""
        config = {'symbol': 'AAPL'}
        loader = MockDataLoader(config)
        assert loader.config == config
    
    def test_init_with_invalid_config(self) -> None:
        """测试无效配置初始化"""
        config = {}
        with pytest.raises(ValueError, match="配置中必须包含symbol"):
            MockDataLoader(config)
    
    def test_validate_dataframe_valid(self) -> None:
        """测试有效DataFrame验证"""
        config = {'symbol': 'AAPL'}
        loader = MockDataLoader(config)
        
        dates = pd.date_range('2023-01-01', '2023-01-10')
        df = pd.DataFrame({
            'open': [100] * len(dates),
            'high': [105] * len(dates),
            'low': [95] * len(dates),
            'close': [102] * len(dates),
            'volume': [1000] * len(dates)
        }, index=dates)
        
        assert loader.validate_dataframe(df) is True
    
    def test_validate_dataframe_empty(self) -> None:
        """测试空DataFrame验证"""
        config = {'symbol': 'AAPL'}
        loader = MockDataLoader(config)
        
        with pytest.raises(ValueError, match="DataFrame不能为空"):
            loader.validate_dataframe(pd.DataFrame())
    
    def test_validate_dataframe_missing_index(self) -> None:
        """测试缺少timestamp索引验证"""
        config = {'symbol': 'AAPL'}
        loader = MockDataLoader(config)
        
        df = pd.DataFrame({
            'open': [100],
            'high': [105],
            'low': [95],
            'close': [102],
            'volume': [1000]
        })
        
        with pytest.raises(ValueError, match="DataFrame必须包含timestamp索引"):
            loader.validate_dataframe(df)
    
    def test_validate_dataframe_missing_columns(self) -> None:
        """测试缺少必要列验证"""
        config = {'symbol': 'AAPL'}
        loader = MockDataLoader(config)
        
        dates = pd.date_range('2023-01-01', '2023-01-10')
        df = pd.DataFrame({
            'open': [100] * len(dates),
            'close': [102] * len(dates)
        }, index=dates)
        
        with pytest.raises(ValueError, match="DataFrame缺少必要列"):
            loader.validate_dataframe(df)
    
    def test_preprocess_data(self) -> None:
        """测试数据预处理"""
        config = {'symbol': 'AAPL'}
        loader = MockDataLoader(config)
        
        dates = pd.date_range('2023-01-01', '2023-01-10')
        df = pd.DataFrame({
            'open': ['100'] * len(dates),  # 字符串类型
            'high': ['105.5'] * len(dates),
            'low': ['95.2'] * len(dates),
            'close': ['102.3'] * len(dates),
            'volume': ['1000'] * len(dates)
        }, index=dates)
        
        processed_df = loader.preprocess_data(df)
        
        # 检查数据类型转换
        assert processed_df['open'].dtype == 'float64'
        assert processed_df['high'].dtype == 'float64'
        assert processed_df['low'].dtype == 'float64'
        assert processed_df['close'].dtype == 'float64'
        assert processed_df['volume'].dtype == 'float64'