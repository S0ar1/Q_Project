"""
基础配置管理类
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Union

import yaml


class BaseConfig(ABC):
    """基础配置管理抽象类
    
    所有配置管理器必须继承此类并实现必要的方法。
    负责配置文件的管理、加载和验证。
    """

    def __init__(self, config_path: Union[str, Path] = None) -> None:
        """初始化配置管理器
        
        Args:
            config_path: 配置文件路径
        """
        self._config_path = config_path
        self._config_data: Dict[str, Any] = {}
        self._validate_config_class()

    @abstractmethod
    def _validate_config_class(self) -> None:
        """验证配置类的实现
        
        Raises:
            NotImplementedError: 子类未实现必要方法时抛出
        """
        pass

    @abstractmethod
    def _validate_config_data(self) -> None:
        """验证配置数据
        
        Raises:
            ValueError: 配置数据无效时抛出
        """
        pass

    def load_config(self, config_path: Union[str, Path] = None) -> Dict[str, Any]:
        """加载配置文件
        
        Args:
            config_path: 配置文件路径，默认为初始化时指定的路径
            
        Returns:
            配置数据字典
            
        Raises:
            FileNotFoundError: 配置文件不存在时抛出
            ValueError: 配置文件格式错误时抛出
        """
        path = config_path or self._config_path
        
        if path is None:
            raise ValueError("未指定配置文件路径")
        
        path = Path(path)
        
        if not path.exists():
            raise FileNotFoundError(f"配置文件不存在: {path}")
        
        try:
            if path.suffix.lower() in ['.yaml', '.yml']:
                with open(path, 'r', encoding='utf-8') as f:
                    self._config_data = yaml.safe_load(f)
            else:
                raise ValueError(f"不支持的配置文件格式: {path.suffix}")
        except yaml.YAMLError as e:
            raise ValueError(f"配置文件格式错误: {e}")
        
        self._validate_config_data()
        return self._config_data

    def save_config(self, config_data: Dict[str, Any] = None, config_path: Union[str, Path] = None) -> None:
        """保存配置到文件
        
        Args:
            config_data: 配置数据，默认为当前配置
            config_path: 配置文件路径，默认为初始化时指定的路径
            
        Raises:
            ValueError: 保存失败时抛出
        """
        data = config_data or self._config_data
        path = config_path or self._config_path
        
        if path is None:
            raise ValueError("未指定配置文件路径")
        
        path = Path(path)
        
        # 确保目录存在
        path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            if path.suffix.lower() in ['.yaml', '.yml']:
                with open(path, 'w', encoding='utf-8') as f:
                    yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
            else:
                raise ValueError(f"不支持的配置文件格式: {path.suffix}")
        except Exception as e:
            raise ValueError(f"保存配置文件失败: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            key: 配置键，支持点号分隔的嵌套键
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key.split('.')
        value = self._config_data
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any) -> None:
        """设置配置值
        
        Args:
            key: 配置键，支持点号分隔的嵌套键
            value: 配置值
        """
        keys = key.split('.')
        config = self._config_data
        
        # 创建嵌套字典结构
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # 设置最终值
        config[keys[-1]] = value

    def update(self, config_dict: Dict[str, Any]) -> None:
        """批量更新配置
        
        Args:
            config_dict: 配置字典
        """
        self._config_data.update(config_dict)
        self._validate_config_data()

    def to_dict(self) -> Dict[str, Any]:
        """获取完整配置字典
        
        Returns:
            配置字典副本
        """
        return self._config_data.copy()

    def reset(self) -> None:
        """重置配置到默认状态"""
        self._config_data = {}
        self._validate_config_data()

    def validate_config(self) -> bool:
        """验证当前配置
        
        Returns:
            配置是否有效
            
        Raises:
            ValueError: 配置无效时抛出
        """
        self._validate_config_data()
        return True

    def get_data_source_config(self) -> Dict[str, Any]:
        """获取数据源配置
        
        Returns:
            数据源配置字典
        """
        return self.get('data_source', {})

    def get_strategy_config(self) -> Dict[str, Any]:
        """获取策略配置
        
        Returns:
            策略配置字典
        """
        return self.get('strategy', {})

    def get_risk_config(self) -> Dict[str, Any]:
        """获取风险管理配置
        
        Returns:
            风险管理配置字典
        """
        return self.get('risk_management', {})

    def get_execution_config(self) -> Dict[str, Any]:
        """获取执行配置
        
        Returns:
            执行配置字典
        """
        return self.get('execution', {})

    def get_logging_config(self) -> Dict[str, Any]:
        """获取日志配置
        
        Returns:
            日志配置字典
        """
        return self.get('logging', {})

    @property
    def config_path(self) -> Union[str, None]:
        """获取配置文件路径"""
        return str(self._config_path) if self._config_path else None

    @property
    def config_data(self) -> Dict[str, Any]:
        """获取配置数据"""
        return self._config_data.copy()