#!/usr/bin/env python3
"""
绘图模板脚本 - 生成量化分析图表
"""

import sys
import os
from pathlib import Path
from typing import Optional

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime


def setup_matplotlib():
    """设置matplotlib中文显示和样式"""
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
    plt.style.use('seaborn-v0_8' if 'seaborn-v0_8' in plt.style.available else 'default')


def plot_price_data(file_path: str) -> None:
    """绘制价格数据图表"""
    try:
        # 读取数据
        df = pd.read_csv(file_path)
        
        # 检查必需的列
        required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        if not all(col in df.columns for col in required_columns):
            print(f"❌ 数据文件缺少必要列: {required_columns}")
            return
        
        # 转换时间戳
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp')
        
        # 创建图表
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle(f'量化分析图表 - {Path(file_path).stem}', fontsize=16)
        
        # 1. 蜡烛图
        for i, (timestamp, row) in enumerate(df.iterrows()):
            color = 'red' if row['close'] >= row['open'] else 'green'
            # 绘制高低线
            ax1.plot([i, i], [row['low'], row['high']], color='black', linewidth=1)
            # 绘制开收盘线
            ax1.plot([i, i], [row['open'], row['close']], color=color, linewidth=3)
        
        ax1.set_title('价格走势 (蜡烛图)')
        ax1.set_xlabel('时间')
        ax1.set_ylabel('价格')
        ax1.grid(True, alpha=0.3)
        
        # 2. 移动平均线
        if len(df) >= 20:
            df['MA5'] = df['close'].rolling(window=5).mean()
            df['MA10'] = df['close'].rolling(window=10).mean()
            df['MA20'] = df['close'].rolling(window=20).mean()
            
            ax2.plot(df.index, df['close'], label='收盘价', color='blue')
            ax2.plot(df.index, df['MA5'], label='MA5', color='red', alpha=0.7)
            ax2.plot(df.index, df['MA10'], label='MA10', color='green', alpha=0.7)
            ax2.plot(df.index, df['MA20'], label='MA20', color='orange', alpha=0.7)
        
        ax2.set_title('移动平均线')
        ax2.set_xlabel('时间')
        ax2.set_ylabel('价格')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 3. 成交量
        colors = ['red' if df.iloc[i]['close'] >= df.iloc[i]['open'] else 'green' 
                  for i in range(len(df))]
        ax3.bar(df.index, df['volume'], color=colors, alpha=0.7)
        ax3.set_title('成交量')
        ax3.set_xlabel('时间')
        ax3.set_ylabel('成交量')
        ax3.grid(True, alpha=0.3)
        
        # 4. 收益率分布
        returns = df['close'].pct_change().dropna()
        ax4.hist(returns, bins=50, alpha=0.7, color='blue', edgecolor='black')
        ax4.set_title('收益率分布')
        ax4.set_xlabel('收益率')
        ax4.set_ylabel('频率')
        ax4.grid(True, alpha=0.3)
        
        # 添加统计信息
        stats_text = f'统计信息:\n' \
                    f'数据点: {len(df)}\n' \
                    f'平均收益率: {returns.mean():.4f}\n' \
                    f'收益率标准差: {returns.std():.4f}\n' \
                    f'最大收益率: {returns.max():.4f}\n' \
                    f'最小收益率: {returns.min():.4f}'
        
        ax4.text(0.02, 0.98, stats_text, transform=ax4.transAxes, 
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        # 调整布局
        plt.tight_layout()
        
        # 保存图表
        output_path = f"{Path(file_path).stem}_analysis.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✅ 图表已保存到: {output_path}")
        
        # 显示图表
        plt.show()
        
    except Exception as e:
        print(f"❌ 绘制图表时出错: {e}")


def plot_strategy_results(file_path: str) -> None:
    """绘制策略结果图表"""
    try:
        # 读取策略结果数据
        df = pd.read_csv(file_path)
        
        # 检查必需的列
        required_columns = ['timestamp', 'signal', 'position', 'portfolio_value']
        if not all(col in df.columns for col in required_columns):
            print(f"❌ 策略结果文件缺少必要列: {required_columns}")
            return
        
        # 转换时间戳
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp')
        
        # 创建图表
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle(f'策略分析结果 - {Path(file_path).stem}', fontsize=16)
        
        # 1. 投资组合价值
        ax1.plot(df.index, df['portfolio_value'], color='blue', linewidth=2)
        ax1.set_title('投资组合价值变化')
        ax1.set_xlabel('时间')
        ax1.set_ylabel('价值')
        ax1.grid(True, alpha=0.3)
        
        # 2. 信号分布
        signal_counts = df['signal'].value_counts()
        colors = ['green' if x > 0 else 'red' if x < 0 else 'gray' for x in signal_counts.index]
        ax2.bar(signal_counts.index, signal_counts.values, color=colors, alpha=0.7)
        ax2.set_title('交易信号分布')
        ax2.set_xlabel('信号')
        ax2.set_ylabel('次数')
        ax2.grid(True, alpha=0.3)
        
        # 3. 持仓变化
        ax3.plot(df.index, df['position'], color='orange', linewidth=2)
        ax3.set_title('持仓变化')
        ax3.set_xlabel('时间')
        ax3.set_ylabel('持仓')
        ax3.grid(True, alpha=0.3)
        ax3.axhline(y=0, color='black', linestyle='--', alpha=0.5)
        
        # 4. 收益率
        portfolio_returns = df['portfolio_value'].pct_change().dropna()
        ax4.plot(df.index[1:], portfolio_returns, color='purple', alpha=0.7)
        ax4.set_title('投资组合收益率')
        ax4.set_xlabel('时间')
        ax4.set_ylabel('收益率')
        ax4.grid(True, alpha=0.3)
        ax4.axhline(y=0, color='black', linestyle='--', alpha=0.5)
        
        # 添加策略统计信息
        if len(portfolio_returns) > 0:
            total_return = (df['portfolio_value'].iloc[-1] / df['portfolio_value'].iloc[0] - 1) * 100
            volatility = portfolio_returns.std() * (252 ** 0.5) * 100  # 年化波动率
            sharpe_ratio = portfolio_returns.mean() / portfolio_returns.std() * (252 ** 0.5) if portfolio_returns.std() > 0 else 0
            
            stats_text = f'策略统计:\n' \
                        f'总收益率: {total_return:.2f}%\n' \
                        f'年化波动率: {volatility:.2f}%\n' \
                        f'夏普比率: {sharpe_ratio:.2f}\n' \
                        f'最大回撤: {((df["portfolio_value"] / df["portfolio_value"].expanding().max() - 1).min() * 100):.2f}%'
            
            ax4.text(0.02, 0.98, stats_text, transform=ax4.transAxes,
                    verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        # 调整布局
        plt.tight_layout()
        
        # 保存图表
        output_path = f"{Path(file_path).stem}_strategy_analysis.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✅ 策略分析图表已保存到: {output_path}")
        
        # 显示图表
        plt.show()
        
    except Exception as e:
        print(f"❌ 绘制策略图表时出错: {e}")


def main() -> None:
    """主函数"""
    setup_matplotlib()
    
    if len(sys.argv) < 2:
        print("使用方法: python scripts/plot_template.py <data_file>")
        print("\n支持的图表类型:")
        print("  - 价格数据图表 (CSV文件，包含 timestamp, open, high, low, close, volume 列)")
        print("  - 策略结果图表 (CSV文件，包含 timestamp, signal, position, portfolio_value 列)")
        print("\n示例:")
        print("  python scripts/plot_template.py price_data.csv")
        print("  python scripts/plot_template.py strategy_results.csv")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        sys.exit(1)
    
    print(f"📊 开始生成图表: {file_path}")
    
    # 根据文件内容自动判断图表类型
    try:
        # 读取文件前几行来检测类型
        df_sample = pd.read_csv(file_path, nrows=5)
        
        if 'signal' in df_sample.columns and 'position' in df_sample.columns:
            print("🔍 检测到策略结果数据，生成策略分析图表...")
            plot_strategy_results(file_path)
        else:
            print("🔍 检测到价格数据，生成价格分析图表...")
            plot_price_data(file_path)
            
    except Exception as e:
        print(f"❌ 读取文件时出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()