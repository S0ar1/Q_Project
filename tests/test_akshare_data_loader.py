"""
AkShare 数据加载器测试
"""

import pandas as pd
from datetime import datetime

from src.data.akshare_data_loader import AkShareDataLoader


class TestAkShareDataLoader:
    """AkShare 数据加载器测试类"""

    def setup_method(self) -> None:
        """测试前准备"""
        config = {"api_key": "test_key"}
        self.loader = AkShareDataLoader(config)

    def test_init(self) -> None:
        """测试初始化"""
        assert self.loader.config == {"api_key": "test_key"}

    def test_validate_config(self) -> None:
        """测试配置验证"""
        # 测试正常配置
        valid_config = {"api_key": "test_key"}
        loader = AkShareDataLoader(valid_config)
        assert loader.config == valid_config

    def test_load_data(self) -> None:
        """测试数据加载"""
        # 测试数据加载功能
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 10)
        symbol = "000001"
        
        result = self.loader.load_data(symbol, start_date, end_date)
        
        # 验证返回类型
        assert isinstance(result, pd.DataFrame)
        
        # 验证列名
        expected_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        assert all(col in result.columns for col in expected_columns)
        
        # 验证索引类型
        assert isinstance(result.index, pd.DatetimeIndex)

    def test_get_available_symbols(self) -> None:
        """测试获取可用标的"""
        symbols = self.loader.get_available_symbols()
        assert isinstance(symbols, list)
        assert len(symbols) > 0
        assert all(isinstance(symbol, str) for symbol in symbols)

    def test_validate_dataframe(self) -> None:
        """测试DataFrame验证"""
        # 创建测试数据
        dates = pd.date_range('2023-01-01', periods=10, freq='D')
        test_data = pd.DataFrame({
            'Open': [10.0] * 10,
            'High': [11.0] * 10,
            'Low': [9.0] * 10,
            'Close': [10.5] * 10,
            'Volume': [1000] * 10
        }, index=dates)
        
        # 测试验证通过
        result = self.loader.validate_dataframe(test_data)
        assert result is True

    def test_preprocess_data(self) -> None:
        """测试数据预处理"""
        # 创建包含NaN的测试数据
        dates = pd.date_range('2023-01-01', periods=5, freq='D')
        test_data = pd.DataFrame({
            'open': [10.0, None, 10.2, 10.1, 10.3],
            'high': [11.0, 11.1, None, 11.2, 11.3],
            'low': [9.0, 9.1, 9.2, None, 9.3],
            'close': [10.5, 10.6, 10.7, 10.8, None],
            'volume': [1000, 1100, 1200, 1300, 1400]
        }, index=dates)
        
        # 测试预处理
        processed = self.loader.preprocess_data(test_data)
        
        # 验证NaN被删除
        assert not processed.isnull().any().any()
        
        # 验证数据类型
        numeric_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_columns:
            assert pd.api.types.is_numeric_dtype(processed[col])