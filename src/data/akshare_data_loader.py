"""
AkShare 数据加载器
"""

from datetime import datetime
from typing import Any, Dict, List

import akshare as ak
import pandas as pd

from .base_data_loader import BaseDataLoader


class AkShareDataLoader(BaseDataLoader):
    """AkShare 数据加载器
    
    使用 AkShare 库获取股票数据，返回标准格式的 OHLCV 数据。
    """

    def _validate_config(self) -> None:
        """验证配置参数
        
        验证必要的配置参数是否存在。
        
        Raises:
            ValueError: 配置参数无效时抛出
        """
        if not isinstance(self.config, dict):
            raise ValueError("配置必须是字典类型")

    def load_data(self, symbol: str, start_date: datetime, end_date: datetime, period="daily") -> pd.DataFrame:
        """加载股票数据
        
        从 AkShare 获取指定股票在指定时间段内的OHLCV数据。
        
        Args:
            symbol: 股票代码，如 "000001"
            start_date: 开始日期 datetime(2023, 1, 1)
            end_date: 结束日期 datetime(2023, 1, 10)
            period: 数据周期，可选值："daily"(日线)、"weekly"(周线)、"monthly"(月线)
        
        Returns:
            包含 [Open, High, Low, Close, Volume] 列的数据，索引为日期
        """
        # 验证 period 参数
        valid_periods = ["daily", "weekly", "monthly"]
        if period not in valid_periods:
            raise ValueError(f"无效的周期类型: {period}。支持的周期类型: {', '.join(valid_periods)}")
            
        stock_data = ak.stock_zh_a_hist(symbol=symbol, period=period, start_date=start_date.strftime("%Y%m%d"), end_date=end_date.strftime("%Y%m%d"))
        stock_data = stock_data.rename(columns={'日期': 'Date', '开盘': 'Open', '最高': 'High', '最低': 'Low', '收盘': 'Close', '成交量': 'Volume'})[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
        return stock_data.assign(Date=pd.to_datetime(stock_data['Date'])).set_index('Date')

    def get_available_symbols(self) -> List[str]:
        """获取可用的股票代码列表
        
        Returns:
            常用股票代码列表
        """
        return [
            "000001",  # 平安银行
            "000002",  # 万科A
            "600036",  # 招商银行
            "600519",  # 贵州茅台
            "600887",  # 伊利股份
            "000858",  # 五粮液
            "002415",  # 海康威视
            "000725"   # 京东方A
        ]