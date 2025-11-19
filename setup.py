#!/usr/bin/env python3
"""
Quant-Framework 安装配置
"""

from setuptools import setup, find_packages
from pathlib import Path

# 读取 README 文件
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# 读取 requirements.txt
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    with open(requirements_file, encoding="utf-8") as f:
        requirements = [
            line.strip() 
            for line in f.readlines() 
            if line.strip() and not line.startswith("#")
        ]

setup(
    name="quant-framework",
    version="1.0.0",
    author="Quant-Framework Team",
    author_email="team@quant-framework.com",
    description="量化交易框架 - 专业的算法交易开发平台",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/quant-framework/quant-framework",
    project_urls={
        "Bug Tracker": "https://github.com/quant-framework/quant-framework/issues",
        "Documentation": "https://quant-framework.readthedocs.io",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Office/Business :: Financial :: Investment",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "mypy>=1.0.0",
            "black>=22.0.0",
            "isort>=5.10.0",
            "pip-tools>=6.8.0",
            "radon>=6.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "quant-framework=src.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="quantitative trading framework finance algorithm",
)