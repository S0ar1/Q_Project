# Quant-Framework 量化交易框架

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Test](https://img.shields.io/badge/coverage-80%25-brightgreen.svg)]()

## 📊 项目简介

Quant-Framework 是一个专业的量化交易框架，专注于算法交易策略的开发和执行。本框架提供了完整的基础设施，包括数据管理、策略开发、风险控制和交易执行。

## ✨ 核心特性

- **模块化设计**: 基于抽象类的高度模块化架构
- **类型安全**: 100% 类型注解支持
- **高测试覆盖率**: 内置测试框架，目标覆盖率 ≥ 80%
- **现代化配置**: 支持 pyproject.toml 配置
- **数据驱动**: 内置多种数据源支持
- **风险控制**: 内置风险管理模块
- **性能优化**: 优化的执行引擎

## 🚀 快速开始

### 安装依赖

```bash
pip install -e .[dev]
```

或者直接安装 requirements.txt 中的依赖：

```bash
pip install -r requirements.txt
```

### 依赖说明

- **核心依赖**: pandas, numpy, PyYAML, pydantic
- **数据获取**: yfinance, akshare (新增)
- **可视化**: matplotlib
- **开发工具**: pytest, mypy, black, isort

### 运行测试

```bash
pytest
```

### 代码质量检查

```bash
# 类型检查
mypy src/

# 代码格式化
black src/ tests/ scripts/

# 导入排序
isort src/ tests/ scripts/
```

## 📁 项目结构

```
Q_Project/
├── src/                    # 源代码根目录
│   ├── __init__.py
│   ├── data/              # 数据管理模块
│   │   ├── __init__.py
│   │   ├── base_data_loader.py
│   │   └── akshare_data_loader.py
│   ├── strategies/        # 策略模块
│   │   ├── __init__.py
│   │   └── base_strategy.py
│   ├── execution/         # 执行引擎
│   │   ├── __init__.py
│   │   └── base_executor.py
│   └── risk_management/   # 风险管理
│       ├── __init__.py
│       └── base_risk_manager.py
├── tests/                 # 测试文件
│   ├── __init__.py
│   ├── test_base_data_loader.py
│   ├── test_base_strategy.py
│   ├── test_base_executor.py
│   └── test_base_risk_manager.py
├── scripts/              # 脚本工具
│   ├── __init__.py
│   ├── scaffold.py       # 项目脚手架
│   ├── check_dep.py      # 依赖检查
│   └── plot_template.py  # 绘图模板
├── requirements.txt       # 依赖列表
├── pyproject.toml        # 项目配置
├── AI_RULES.md           # AI 规则文件
├── manifest.json         # 依赖管理清单
└── .trae_instructions    # Trae 指令配置
```

## 🎯 核心模块

### 数据加载器 (BaseDataLoader)
- 抽象基类定义数据获取接口
- 支持多种数据源
- 数据验证和预处理

#### AkShare 数据加载器 (AkShareDataLoader)
- 基于 AkShare 库实现的A股数据获取
- 支持获取日K线 OHLCV 数据
- 提供标准格式的数据输出
- 内置常用股票代码列表

```python
from quant_framework.data import AkShareDataLoader
from datetime import datetime

# 创建 AkShare 数据加载器实例
data_loader = AkShareDataLoader()

# 获取股票数据
data = data_loader.load_data(
    symbol="600519",  # 贵州茅台
    start_date=datetime(2023, 1, 1),
    end_date=datetime(2023, 12, 31)
)

# 获取可用股票代码列表
symbols = data_loader.get_available_symbols()
```

### 策略引擎 (BaseStrategy)
- 策略基础架构
- 信号生成机制
- 仓位计算逻辑

### 执行引擎 (BaseExecutor)
- 交易执行管理
- 订单处理
- 投资组合状态跟踪

### 风险管理 (BaseRiskManager)
- 风险检查和限制
- 止损止盈控制
- 风险指标计算

## 🛠️ 开发工具

### 脚手架脚本
```bash
# 创建新的策略模块
python scripts/scaffold.py strategy MyStrategy

# 检查依赖
python scripts/check_dep.py

# 生成可视化图表
python scripts/plot_template.py
```

### 代码质量
- **Black**: 代码格式化
- **isort**: 导入排序
- **MyPy**: 类型检查
- **pytest**: 测试框架
- **radon**: 代码复杂度分析

## 📋 开发规范

### 函数长度
- 单个函数 ≤ 30 行
- 复杂逻辑拆分为多个函数

### 类型注解
- 所有函数必须有类型注解
- 变量声明需要类型标注

### 测试覆盖
- 核心功能测试覆盖 ≥ 80%
- 单元测试 + 集成测试

### 代码风格
- 遵循 PEP 8
- 使用 Black 格式化
- isort 统一导入排序

## 📚 API 文档

### 基础数据加载器

```python
from quant_framework.data import BaseDataLoader

class CustomDataLoader(BaseDataLoader):
    def load_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        # 实现数据加载逻辑
        pass
```

### 策略开发

```python
from quant_framework.strategies import BaseStrategy

class MyStrategy(BaseStrategy):
    def generate_signals(self, data: pd.DataFrame) -> Dict[str, float]:
        # 实现策略信号生成
        pass
```

## 🤝 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目基于 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 📞 联系方式

- 项目主页: [GitHub Repository](https://github.com/quant-framework/quant-framework)
- 问题报告: [GitHub Issues](https://github.com/quant-framework/quant-framework/issues)
- 文档: [Documentation](https://quant-framework.readthedocs.io)

---

**⚠️ 重要提醒**: 本框架仅供教育和研究目的。使用前请确保您了解相关风险，并遵守当地的法律法规。