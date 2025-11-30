"""
简单移动平均线(SMA)交易策略模块

本模块实现了基于简单移动平均线(SMA)交叉的交易策略。
该策略通过比较短期和长期移动平均线的关系来生成交易信号：
- 金叉(Golden Cross)：当短期SMA向上穿越长期SMA时，生成买入信号
- 死叉(Dead Cross)：当短期SMA向下穿越长期SMA时，生成卖出信号

策略特点：
- 遵循系统统一的策略接口规范，继承自BaseStrategy
- 支持灵活的参数配置，可调整SMA周期
- 提供完整的信号验证和标准化仓位建议功能
- 预留了与风险控制模块集成的接口

使用示例：
```python
from src.strategies.sma_strategy import SMAStrategy
from src.strategies.output_manager import StrategyOutputManager

# 配置策略参数
config = {
    'short_period': 20,      # 短期移动平均线周期
    'long_period': 50,       # 长期移动平均线周期
    'position_weight': 0.1   # 仓位权重系数
}

# 创建策略实例
strategy = SMAStrategy(config=config)
output_manager = StrategyOutputManager()

# 生成交易信号
signals = strategy.generate_signals(market_data)

# 计算仓位大小
position_size = strategy.calculate_position_size(signal=1, current_price=100)

# 创建标准化的仓位建议
suggestion = output_manager.create_position_suggestion(
    signal=1, 
    position_size=position_size,
    confidence=0.8
)
```
"""

import logging
from typing import Dict, Any
import pandas as pd
import numpy as np

from .base_strategy import BaseStrategy
from .output_manager import StrategyOutputManager

# 配置日志记录器
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SMAStrategy(BaseStrategy):
    """
    简单移动平均线(SMA)交易策略类
    
    该类实现了基于SMA交叉的交易信号生成逻辑，是对BaseStrategy的具体实现。
    策略核心逻辑是通过检测短期和长期移动平均线的交叉点来确定买入和卖出时机。
    
    属性:
        config: 策略配置字典，包含周期参数等配置
        output_manager: 输出管理器实例，用于标准化输出格式
    """
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """
        初始化SMA策略实例
        
        Args:
            config: 策略配置字典，必须包含以下键：
                - short_period: 短期移动平均线周期（必须为正整数且小于long_period）
                - long_period: 长期移动平均线周期（必须为正整数且大于short_period）
                - position_weight: 仓位权重系数（可选，默认0.1）
        
        Raises:
            ValueError: 当配置参数无效时抛出异常
        """
        super().__init__(config)
        self.output_manager = StrategyOutputManager()
        logger.info(f"初始化SMA策略，配置: {config}")
    
    def _validate_config(self) -> None:
        """
        验证策略配置参数的有效性
        
        此方法确保配置参数满足策略的基本要求，包括:
        1. 检查必需的参数是否存在
        2. 验证周期参数的类型和取值范围
        3. 设置可选参数的默认值
        
        Raises:
            ValueError: 当配置参数无效时抛出异常
        """
        # 验证必需的配置参数
        required_keys = ['short_period', 'long_period']
        for key in required_keys:
            if key not in self.config:
                raise ValueError(f"缺少必需的配置项: {key}")
        
        # 验证移动平均线周期的有效性
        short_period = self.config['short_period']
        long_period = self.config['long_period']
        
        # 验证周期是否为正整数
        if not isinstance(short_period, int) or short_period <= 0:
            raise ValueError(f"短期周期必须是正整数: {short_period}")
        
        if not isinstance(long_period, int) or long_period <= 0:
            raise ValueError(f"长期周期必须是正整数: {long_period}")
        
        # 验证短期周期必须小于长期周期
        if short_period >= long_period:
            raise ValueError(f"短期周期({short_period})必须小于长期周期({long_period})")
        
        # 设置可选参数的默认值
        if 'position_weight' not in self.config:
            self.config['position_weight'] = 0.1  # 默认仓位权重为10%
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        生成SMA交叉交易信号
        
        核心策略逻辑：通过计算短期和长期移动平均线，并检测它们的交叉点来生成交易信号。
        金叉(买入信号)：短期SMA从下方穿越长期SMA
        死叉(卖出信号)：短期SMA从上方穿越长期SMA
        
        Args:
            data: 市场数据DataFrame，必须包含以下列（大小写不敏感）:
                - 'close'/'Close': 收盘价
                - 'open'/'Open': 开盘价（由preprocess_data方法验证）
                - 'high'/'High': 最高价（由preprocess_data方法验证）
                - 'low'/'Low': 最低价（由preprocess_data方法验证）
                - 'volume'/'Volume': 成交量（由preprocess_data方法验证）
                同时必须包含DatetimeIndex作为索引
            
        Returns:
            标准化的信号DataFrame，包含'signal'列和其他分析数据列
        
        Raises:
            ValueError: 当输入数据格式不正确时抛出
        """
        logger.info(f"开始生成SMA交叉信号，数据长度: {len(data)}")
        
        # 将列名转换为小写，以兼容AkShare数据格式
        data_copy = data.copy()
        data_copy.columns = [col.lower() for col in data_copy.columns]
        
        # 预处理数据
        processed_data = self.preprocess_data(data_copy)
        
        # 创建信号DataFrame
        signals = pd.DataFrame(index=processed_data.index)
        signals['signal'] = 0  # 初始化信号为0
        
        # 计算短期和长期移动平均线
        short_period = self.config['short_period']
        long_period = self.config['long_period']
        
        signals['short_sma'] = processed_data['close'].rolling(window=short_period, min_periods=1).mean()
        signals['long_sma'] = processed_data['close'].rolling(window=long_period, min_periods=1).mean()
        
        # 计算移动平均线差值和变化趋势
        signals['sma_diff'] = signals['short_sma'] - signals['long_sma']
        signals['sma_diff_prev'] = signals['sma_diff'].shift(1)
        
        # 核心逻辑：生成交易信号 - 检测金叉和死叉
        # 金叉：短期SMA从下方穿越长期SMA
        signals['signal'] = np.where(
            (signals['sma_diff_prev'] <= 0) & 
            (signals['sma_diff'] > 0),
            1,  # 买入信号
            signals['signal']
        )
        
        # 死叉：短期SMA从上方穿越长期SMA
        signals['signal'] = np.where(
            (signals['sma_diff_prev'] >= 0) & 
            (signals['sma_diff'] < 0),
            -1,  # 卖出信号
            signals['signal']
        )
        
        # 计算信号强度（基于SMA差值与价格的比例）
        signals['signal_strength'] = np.abs(signals['sma_diff']) / processed_data['close']
        
        # 记录信号生成情况
        buy_signals = signals[signals['signal'] == 1].index
        sell_signals = signals[signals['signal'] == -1].index
        
        logger.info(f"生成了 {len(buy_signals)} 个买入信号和 {len(sell_signals)} 个卖出信号")
        
        # 使用输出管理器标准化信号格式
        standardized_signals = self.output_manager.standardize_signals(signals)
        
        # 验证信号有效性
        self.validate_signals(standardized_signals)
        
        logger.info("信号生成完成并通过验证")
        return standardized_signals
    
    def calculate_position_size(self, signal: float, current_price: float) -> float:
        """
        计算标准化的仓位大小建议
        
        根据交易信号和当前市场条件，计算标准化的仓位大小建议，
        不考虑可用资金因素，仅提供策略本身的仓位建议。
        
        Args:
            signal: 交易信号 (-1, 0, 1)
            current_price: 当前股票价格
            
        Returns:
            标准化的仓位大小建议（0-1之间的浮点数，表示建议仓位比例）
        """
        # 获取配置的仓位权重
        position_weight = self.config.get('position_weight', 0.1)
        
        # 如果信号为0（持有），则返回0
        if signal == 0:
            return 0.0
        
        # 返回基于配置权重的标准化仓位大小
        # 这里返回的是相对仓位大小，可以被上层系统根据资金情况调整
        logger.info(f"计算标准化仓位大小: 信号={signal}, 价格={current_price}, 仓位权重={position_weight}")
        return position_weight
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """
        获取策略详细信息
        
        提供策略的完整元数据，包括策略类型、参数配置、描述等信息。
        这些信息可用于策略管理、性能分析和UI展示。
        
        Returns:
            包含策略详细信息的字典
        """
        # 获取基础策略信息
        info = super().get_strategy_info()
        
        # 添加SMA策略特有的信息
        info.update({
            'type': 'sma_crossover',  # 策略类型标识符
            'description': '简单移动平均线交叉交易策略',  # 策略描述
            'short_period': self.config['short_period'],  # 短期周期
            'long_period': self.config['long_period'],    # 长期周期
            'position_weight': self.config.get('position_weight', 0.1)  # 仓位权重
        })
        
        logger.info(f"获取策略信息: {info}")
        return info
