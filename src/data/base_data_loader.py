"""
基础数据加载器类
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd


class BaseDataLoader(ABC):
    """基础数据加载器抽象类
    
    所有数据加载器必须继承此类并实现必要的方法。
    确保所有返回的DataFrame都包含timestamp索引。
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        """初始化数据加载器
        
        Args:
            config: 配置字典，包含数据源相关参数
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
    def load_data(
        self, 
        symbol: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> pd.DataFrame:
        """加载数据
        
        Args:
            symbol: 交易标的代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            包含timestamp索引的DataFrame
            
        Raises:
            DataLoaderError: 数据加载失败时抛出
        """
        pass

    @abstractmethod
    def get_available_symbols(self) -> List[str]:
        """获取可用的交易标的列表
        
        Returns:
            可用的交易标的代码列表
        """
        pass

    def validate_dataframe(self, df: pd.DataFrame) -> bool:
        """验证DataFrame是否符合规范
        
        Args:
            df: 要验证的DataFrame
            
        Returns:
            是否符合规范
            
        Raises:
            ValueError: DataFrame格式不正确时抛出
        """
        if df.empty:
            raise ValueError("DataFrame不能为空")
        
        if not isinstance(df.index, pd.DatetimeIndex):
            raise ValueError("DataFrame必须包含timestamp索引")
        
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise ValueError(f"DataFrame缺少必要列: {missing_columns}")
        
        return True

    def preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """预处理数据
        
        Args:
            df: 原始数据DataFrame
            
        Returns:
            预处理后的DataFrame
        """
        # 确保数据类型正确
        numeric_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 删除包含NaN的行
        df = df.dropna()
        
        # 按时间排序
        df = df.sort_index()
        
        return df