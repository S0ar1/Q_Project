
# 测试dataloader的load_data方法


import sys
import os

# 将项目根目录添加到sys.path，以便能够导入src包
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data.akshare_data_loader import AkShareDataLoader
from datetime import datetime

if __name__ == '__main__':
    # 创建 AkShare 数据加载器实例
    data_loader = AkShareDataLoader(
        config={}
    )

    # 获取股票数据
    data = data_loader.load_data(
        symbol="600519",  # 贵州茅台
        start_date=datetime(2023, 1, 1),
        end_date=datetime(2023, 12, 31),
        period="daily"
    )
    
    # 验证和预处理数据
    data_loader.validate_dataframe(data)
    data = data_loader.preprocess_data(data)
    
    print(f"成功获取 {len(data)} 条数据")
    print(f"数据日期范围: {data.index.min().strftime('%Y-%m-%d')} 到 {data.index.max().strftime('%Y-%m-%d')}")
    print(f"数据示例:\n{data.head()}")
    
    # 获取可用股票代码列表
    symbols = data_loader.get_available_symbols()
    import pdb; pdb.set_trace()