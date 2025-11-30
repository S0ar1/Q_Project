"""
策略输出管理模块

本模块提供了一个独立的输出管理类，负责标准化和管理所有策略输出的结构格式，
确保输出内容的一致性和可维护性。
"""

import json
from typing import Dict, Any, Optional, Union, List
import pandas as pd
import numpy as np


class StrategyOutputManager:
    """
    策略输出管理类
    
    负责标准化、验证和转换策略输出的数据格式，确保不同策略输出的一致性。
    """
    
    # 标准信号列名
    STANDARD_SIGNAL_COLUMNS = ['signal']
    
    # 标准仓位建议结构
    POSITION_SUGGESTION_SCHEMA = {
        'signal': float,
        'position_size': float,
        'confidence': Optional[float],
        'timestamp': Optional[str],
        'metadata': Optional[Dict[str, Any]]
    }
    
    def __init__(self):
        """初始化输出管理器"""
        pass
    
    def standardize_signals(self, signals: pd.DataFrame) -> pd.DataFrame:
        """
        标准化信号DataFrame格式
        
        Args:
            signals: 原始信号DataFrame
            
        Returns:
            标准化后的信号DataFrame
            
        Raises:
            ValueError: 当输入格式不正确时抛出
        """
        # 验证输入是否为DataFrame
        if not isinstance(signals, pd.DataFrame):
            raise ValueError("输入必须是pandas DataFrame")
        
        # 验证索引是否为DatetimeIndex
        if not isinstance(signals.index, pd.DatetimeIndex):
            raise ValueError("信号DataFrame必须包含timestamp索引")
        
        # 确保必需的列存在
        if 'signal' not in signals.columns:
            raise ValueError("信号DataFrame必须包含'signal'列")
        
        # 验证信号值
        valid_signals = {-1, 0, 1}
        invalid_signals = set(signals['signal'].unique()) - valid_signals
        
        if invalid_signals:
            raise ValueError(f"信号值必须在 {-1, 0, 1} 中，检测到无效值: {invalid_signals}")
        
        # 创建标准化的DataFrame（只包含必需的列）
        standardized = pd.DataFrame(index=signals.index)
        standardized['signal'] = signals['signal'].astype(float)
        
        # 保留原始DataFrame中的其他列作为扩展信息
        additional_columns = [col for col in signals.columns if col not in self.STANDARD_SIGNAL_COLUMNS]
        for col in additional_columns:
            standardized[col] = signals[col]
        
        return standardized
    
    def create_position_suggestion(
        self,
        signal: float,
        position_size: float,
        confidence: Optional[float] = None,
        timestamp: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        创建标准化的仓位建议
        
        Args:
            signal: 交易信号 (-1, 0, 1)
            position_size: 标准化的仓位大小建议
            confidence: 信号置信度（0-1之间的浮点数）
            timestamp: 时间戳
            metadata: 附加元数据
            
        Returns:
            标准化的仓位建议字典
            
        Raises:
            ValueError: 当输入参数无效时抛出
        """
        # 验证信号值
        if signal not in [-1, 0, 1]:
            raise ValueError(f"信号值必须是 -1, 0 或 1，当前值: {signal}")
        
        # 验证仓位大小
        if position_size < 0:
            raise ValueError(f"仓位大小不能为负数，当前值: {position_size}")
        
        # 验证置信度
        if confidence is not None and (confidence < 0 or confidence > 1):
            raise ValueError(f"置信度必须在 0-1 之间，当前值: {confidence}")
        
        # 创建标准化的仓位建议
        suggestion = {
            'signal': float(signal),
            'position_size': float(position_size),
            'confidence': confidence,
            'timestamp': timestamp,
            'metadata': metadata or {}
        }
        
        return suggestion
    
    def convert_to_json(self, data: Union[pd.DataFrame, Dict], indent: int = 2) -> str:
        """
        将数据转换为JSON格式
        
        Args:
            data: 要转换的数据（DataFrame或字典）
            indent: JSON缩进空格数
            
        Returns:
            JSON格式的字符串
        """
        if isinstance(data, pd.DataFrame):
            # 对于DataFrame，将索引转换为列
            df_copy = data.reset_index()
            if 'index' in df_copy.columns:
                df_copy = df_copy.rename(columns={'index': 'timestamp'})
            
            # 转换为字典列表
            data_dict = df_copy.to_dict('records')
            return json.dumps(data_dict, indent=indent, ensure_ascii=False)
        elif isinstance(data, dict):
            return json.dumps(data, indent=indent, ensure_ascii=False)
        else:
            raise ValueError("只支持DataFrame或字典格式的数据")
    
    def validate_output_format(self, output: Any) -> bool:
        """
        验证输出格式是否符合规范
        
        Args:
            output: 要验证的输出数据
            
        Returns:
            是否符合规范
            
        Raises:
            ValueError: 当输出格式不符合规范时抛出
        """
        if isinstance(output, pd.DataFrame):
            return self._validate_dataframe_format(output)
        elif isinstance(output, dict):
            return self._validate_dict_format(output)
        else:
            raise ValueError(f"不支持的输出格式: {type(output).__name__}")
    
    def _validate_dataframe_format(self, df: pd.DataFrame) -> bool:
        """验证DataFrame格式"""
        # 验证索引是否为DatetimeIndex
        if not isinstance(df.index, pd.DatetimeIndex):
            raise ValueError("DataFrame必须包含timestamp索引")
        
        # 验证必需的列是否存在
        if 'signal' not in df.columns:
            raise ValueError("DataFrame必须包含'signal'列")
        
        return True
    
    def _validate_dict_format(self, data: Dict) -> bool:
        """验证字典格式"""
        # 检查是否包含必需的键
        if 'signal' not in data:
            raise ValueError("字典必须包含'signal'键")
        
        # 检查是否为仓位建议格式
        if all(key in data for key in ['signal', 'position_size']):
            # 验证信号值
            if data['signal'] not in [-1, 0, 1]:
                raise ValueError(f"信号值必须是 -1, 0 或 1，当前值: {data['signal']}")
            
            # 验证仓位大小
            if data['position_size'] < 0:
                raise ValueError(f"仓位大小不能为负数，当前值: {data['position_size']}")
        
        return True
    
    def batch_process_signals(self, signals_list: List[pd.DataFrame]) -> pd.DataFrame:
        """
        批量处理多个信号DataFrame
        
        Args:
            signals_list: 信号DataFrame列表
            
        Returns:
            合并后的标准化信号DataFrame
        """
        standardized_signals = []
        
        for i, signals in enumerate(signals_list):
            # 标准化每个信号DataFrame
            standardized = self.standardize_signals(signals)
            # 添加策略ID标识
            standardized['strategy_id'] = i
            standardized_signals.append(standardized)
        
        # 合并所有信号DataFrame
        combined = pd.concat(standardized_signals, axis=0)
        # 按时间戳排序
        combined = combined.sort_index()
        
        return combined
    
    def calculate_aggregated_position(self, suggestions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        计算多个策略的聚合仓位建议
        
        Args:
            suggestions: 仓位建议字典列表
            
        Returns:
            聚合后的仓位建议
        """
        if not suggestions:
            raise ValueError("建议列表不能为空")
        
        # 计算信号和仓位的加权平均
        total_confidence = sum(s.get('confidence', 1.0) for s in suggestions)
        if total_confidence == 0:
            total_confidence = 1.0  # 避免除零错误
        
        weighted_signal = sum(s['signal'] * s.get('confidence', 1.0) for s in suggestions) / total_confidence
        weighted_position = sum(s['position_size'] * s.get('confidence', 1.0) for s in suggestions) / total_confidence
        
        # 确定最终信号（基于加权平均的符号）
        final_signal = 0
        if weighted_signal > 0.5:
            final_signal = 1
        elif weighted_signal < -0.5:
            final_signal = -1
        
        # 构建聚合结果
        aggregated = {
            'signal': final_signal,
            'position_size': weighted_position,
            'confidence': min(1.0, abs(weighted_signal)),
            'strategy_count': len(suggestions),
            'individual_suggestions': suggestions
        }
        
        return aggregated
