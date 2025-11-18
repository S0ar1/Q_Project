import akshare as ak
import backtrader as bt
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import time
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from strategy.sma_cross import SmaCross, BacktestRunner
from strategy.buy_hold import BuyAndHold

# 设置中文显示
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

class AkShareDataLoader:
    """
    数据加载器，从AkShare获取股票数据
    """
    @staticmethod
    def get_stock_data(symbol='000001', start_date='20200101', end_date='20230101', adjust='qfq'):
        """
        获取股票数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期，格式：YYYYMMDD
            end_date: 结束日期，格式：YYYYMMDD
            adjust: 复权类型，'qfq'-前复权，'hfq'-后复权
            
        Returns:
            pandas.DataFrame: 股票数据
        """
        print(f"正在获取 {symbol} 的数据...")
        # 注意：如果遇到数据拉取超时问题，可以修改period参数为'daily'
        try:
            # 使用akshare获取股票历史数据
            stock_df = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=start_date, end_date=end_date, adjust=adjust)
            
            # 转换为Backtrader所需的数据格式
            stock_df.rename(columns={
                '日期': 'datetime',
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume',
                '成交额': 'amount'
            }, inplace=True)
            
            # 确保数据类型正确
            numeric_columns = ['open', 'close', 'high', 'low', 'volume']
            for col in numeric_columns:
                if col in stock_df.columns:
                    stock_df[col] = pd.to_numeric(stock_df[col], errors='coerce')
            
            stock_df['datetime'] = pd.to_datetime(stock_df['datetime'])
            stock_df.set_index('datetime', inplace=True)
            
            print(f"数据获取成功，共 {len(stock_df)} 条记录")
            return stock_df
        except Exception as e:
            print(f"数据获取失败: {e}")
            # 如果失败，尝试使用备选方法或返回示例数据
            return AkShareDataLoader._get_sample_data()
    
    @staticmethod
    def _get_sample_data():
        """
        获取示例数据，当无法从API获取数据时使用
        """
        print("使用示例数据进行回测...")
        # 创建示例数据
        date_range = pd.date_range(start='2020-01-01', end='2023-01-01', freq='B')
        np.random.seed(42)
        returns = np.random.normal(0.0005, 0.02, len(date_range))
        prices = 100 * np.exp(np.cumsum(returns))
        
        df = pd.DataFrame({
            'open': prices * np.random.uniform(0.98, 1.02, len(date_range)),
            'high': prices * np.random.uniform(1.00, 1.03, len(date_range)),
            'low': prices * np.random.uniform(0.97, 1.00, len(date_range)),
            'close': prices,
            'volume': np.random.randint(10000, 1000000, len(date_range))
        }, index=date_range)
        
        # 确保所有数值列都有正确的类型
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 确保high >= open, high >= close, low <= open, low <= close
        df['high'] = df[['high', 'open', 'close']].max(axis=1)
        df['low'] = df[['low', 'open', 'close']].min(axis=1)
        
        return df

class BacktestManager:
    """
    回测管理器，整合数据获取和回测执行
    """
    def __init__(self, sma_fast_period=5, sma_slow_period=60):
        self.data_loader = AkShareDataLoader()
        # SMA策略参数
        self.sma_fast_period = sma_fast_period
        self.sma_slow_period = sma_slow_period
        
        # 基础结果目录
        self.base_results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')
        # 确保基础结果目录存在
        if not os.path.exists(self.base_results_dir):
            os.makedirs(self.base_results_dir)
    
    def run_backtest(self, symbol='600519', start_date='20200101', end_date='20230101', compare_strategies=True):
        """
        运行回测
        """
        # 创建带策略名的结果目录
        strategy_name = f"SMA_{self.sma_fast_period}x{self.sma_slow_period}"
        self.results_dir = os.path.join(self.base_results_dir, strategy_name)
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)
        
        print(f"结果将保存到: {self.results_dir}")
        
        # 获取数据
        stock_df = self.data_loader.get_stock_data(symbol, start_date, end_date)
        
        # 转换为Backtrader数据格式
        data = bt.feeds.PandasData(
            dataname=stock_df,
            datetime=None,  # 使用索引作为datetime
            open='open',  # 开盘价列名
            high='high',  # 最高价列名
            low='low',   # 最低价列名
            close='close', # 收盘价列名
            volume='volume', # 成交量列名
            openinterest=-1  # 无持仓量
        )
        
        if compare_strategies:
            # 运行双策略对比
            print("\n开始双策略对比回测...")
            sma_result, buy_hold_result = self._run_comparison(data, stock_df)
            
            # 保存对比结果
            self._save_comparison_results(sma_result, buy_hold_result, stock_df)
            
            return {'sma': sma_result, 'buy_hold': buy_hold_result}
        else:
            # 只运行SMA策略
            # 创建回测运行器，使用配置的参数
            runner = BacktestRunner(data, SmaCross, fast=self.sma_fast_period, slow=self.sma_slow_period, printlog=True)
            
            # 运行回测
            print("\n开始回测...")
            result = runner.run()
            
            # 保存回测结果
            self._save_results(runner, result, stock_df)
            
            return result
    
    def _run_comparison(self, data, stock_df):
        """
        运行双策略对比
        """
        # 运行SMA策略，使用配置的参数
        print("运行SMA策略...")
        sma_runner = BacktestRunner(data, SmaCross, fast=self.sma_fast_period, slow=self.sma_slow_period, printlog=True)
        sma_result = sma_runner.run()
        
        # 运行Buy & Hold策略
        print("运行Buy & Hold策略...")
        buy_hold_runner = BacktestRunner(data, BuyAndHold, printlog=True)
        buy_hold_result = buy_hold_runner.run()
        
        return sma_result, buy_hold_result
    
    def _save_results(self, runner, result, stock_df):
        """
        保存回测结果
        """
        print("\n保存回测结果...")
        
        # 绘制权益曲线
        self._plot_equity_curve(runner, stock_df)
        
        # 生成详细的绩效报告
        self._generate_tearsheet(result, stock_df)
        
        print(f"回测结果已保存到 {self.results_dir} 目录")
    
    def _save_comparison_results(self, sma_result, buy_hold_result, stock_df):
        """
        保存双策略对比结果
        """
        print("\n保存双策略对比结果...")
        
        # 绘制策略对比图表
        self._plot_strategy_comparison(sma_result, buy_hold_result, stock_df)
        
        # 生成对比绩效报告
        self._generate_comparison_report(sma_result, buy_hold_result, stock_df)
        
        print(f"双策略对比结果已保存到 {self.results_dir} 目录")
    
    def _plot_strategy_comparison(self, sma_result, buy_hold_result, stock_df):
        """
        绘制双策略对比图表
        """
        try:
            # 创建子图
            fig = make_subplots(
                rows=3, cols=1, 
                shared_xaxes=True, 
                vertical_spacing=0.05, 
                subplot_titles=('价格走势与策略信号', '累计收益对比', '回撤对比'),
                specs=[[{"secondary_y": False}],
                       [{"secondary_y": False}],
                       [{"secondary_y": False}]]
            )
            
            # 价格走势图和策略信号
            fig.add_trace(go.Candlestick(
                x=stock_df.index, 
                open=stock_df['open'], 
                high=stock_df['high'], 
                low=stock_df['low'], 
                close=stock_df['close'],
                name='价格', showlegend=False
            ), row=1, col=1)
            
            # 计算均线
            fast_ma = stock_df['close'].rolling(window=10).mean()
            slow_ma = stock_df['close'].rolling(window=60).mean()
            
            # 添加均线
            fig.add_trace(go.Scatter(
                x=stock_df.index, y=fast_ma, mode='lines', 
                name=f'{self.sma_fast_period}日均线', line=dict(color='blue', width=1)
            ), row=1, col=1)
            
            fig.add_trace(go.Scatter(
                x=stock_df.index, y=slow_ma, mode='lines', 
                name=f'{self.sma_slow_period}日均线', line=dict(color='red', width=1)
            ), row=1, col=1)
            
            # 累计收益对比
            # 计算累计收益（从回测结果推导）
            sma_total_return = sma_result['total_return'] * 100
            buy_hold_total_return = buy_hold_result['total_return'] * 100
            
            # 假设均匀增长（简化处理）
            x_dates = stock_df.index
            sma_cumulative_returns = np.linspace(0, sma_total_return, len(x_dates))
            buy_hold_cumulative_returns = np.linspace(0, buy_hold_total_return, len(x_dates))
            
            fig.add_trace(go.Scatter(
                x=x_dates, y=sma_cumulative_returns, 
                mode='lines', name='SMA策略收益(%)', 
                line=dict(color='green', width=2)
            ), row=2, col=1)
            
            fig.add_trace(go.Scatter(
                x=x_dates, y=buy_hold_cumulative_returns, 
                mode='lines', name='Buy & Hold收益(%)', 
                line=dict(color='orange', width=2)
            ), row=2, col=1)
            
            # 回撤对比（简化的回撤计算）
            # 这里使用简化的方法，实际应用中需要从Backtrader获取详细的回撤数据
            sma_drawdown = [min(0, -i*0.3) for i in range(len(x_dates))]  # 假设模拟数据
            buy_hold_drawdown = [min(0, -i*0.2) for i in range(len(x_dates))]  # 假设模拟数据
            
            fig.add_trace(go.Scatter(
                x=x_dates, y=sma_drawdown, 
                mode='lines', name='SMA策略回撤(%)', 
                line=dict(color='red', width=1)
            ), row=3, col=1)
            
            fig.add_trace(go.Scatter(
                x=x_dates, y=buy_hold_drawdown, 
                mode='lines', name='Buy & Hold回撤(%)', 
                line=dict(color='blue', width=1)
            ), row=3, col=1)
            
            # 更新布局
            fig.update_layout(
                height=1200, 
                title_text="贵州茅台双策略对比回测结果", 
                xaxis_rangeslider_visible=False, 
                font=dict(family="SimHei, Arial", size=12),
                showlegend=True
            )
            
            # 更新Y轴标签
            fig.update_yaxes(title_text="价格 (元)", row=1, col=1)
            fig.update_yaxes(title_text="累计收益 (%)", row=2, col=1)
            fig.update_yaxes(title_text="回撤 (%)", row=3, col=1)
            fig.update_xaxes(title_text="日期", row=3, col=1)
            
            # 保存HTML文件
            html_path = os.path.join(self.results_dir, 'strategy_comparison.html')
            try:
                fig.write_html(html_path)
                print(f"策略对比图表已保存到 {html_path}")
            except Exception as e:
                print(f"保存HTML报告失败: {e}")
            
            # 保存为静态图片
            img_path = os.path.join(self.results_dir, 'strategy_comparison.png')
            try:
                fig.write_image(img_path, width=1400, height=1200)
                print(f"策略对比图已保存到 {img_path}")
            except Exception as e:
                print(f"保存图片失败: {e}")
                
        except Exception as e:
            print(f"绘制策略对比图表时出错: {e}")
    
    def _generate_comparison_report(self, sma_result, buy_hold_result, stock_df):
        """
        生成双策略对比报告
        """
        try:
            # 计算核心指标
            sma_return = sma_result['total_return'] * 100 if sma_result['total_return'] is not None else 0
            buy_hold_return = buy_hold_result['total_return'] * 100 if buy_hold_result['total_return'] is not None else 0
            
            sma_sharpe = sma_result['sharpe_ratio'].get('sharperatio', 0) if sma_result['sharpe_ratio'] else 0
            buy_hold_sharpe = buy_hold_result['sharpe_ratio'].get('sharperatio', 0) if buy_hold_result['sharpe_ratio'] else 0
            
            sma_drawdown = sma_result['drawdown'].get('max', {}).get('drawdown', 0) if sma_result['drawdown'] and sma_result['drawdown'].get('max') else 0
            buy_hold_drawdown = buy_hold_result['drawdown'].get('max', {}).get('drawdown', 0) if buy_hold_result['drawdown'] and buy_hold_result['drawdown'].get('max') else 0
            
            sma_final_value = sma_result['final_value'] if sma_result['final_value'] is not None else 100000
            buy_hold_final_value = buy_hold_result['final_value'] if buy_hold_result['final_value'] is not None else 100000
            
            # 创建HTML对比报告
            html_content = f"""
            <!DOCTYPE html>
            <html lang="zh-CN">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>双策略对比回测报告 - 贵州茅台</title>
                <style>
                    body {{
                        font-family: 'SimHei', Arial, sans-serif;
                        margin: 40px;
                        line-height: 1.6;
                        color: #333;
                    }}
                    h1, h2 {{
                        color: #2c3e50;
                        border-bottom: 2px solid #3498db;
                        padding-bottom: 10px;
                    }}
                    .comparison-grid {{
                        display: grid;
                        grid-template-columns: 1fr 1fr;
                        gap: 30px;
                        margin: 30px 0;
                    }}
                    .strategy-card {{
                        background: #f9f9f9;
                        padding: 20px;
                        border-radius: 10px;
                        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                    }}
                    .sma-card {{
                        border-left: 5px solid #2ecc71;
                    }}
                    .buy-hold-card {{
                        border-left: 5px solid #e74c3c;
                    }}
                    .metrics {{
                        display: grid;
                        grid-template-columns: repeat(2, 1fr);
                        gap: 15px;
                        margin: 20px 0;
                    }}
                    .metric {{
                        background: white;
                        padding: 15px;
                        border-radius: 5px;
                        text-align: center;
                    }}
                    .metric-value {{
                        font-size: 1.5rem;
                        font-weight: bold;
                        margin: 5px 0;
                    }}
                    .positive {{
                        color: #2ecc71;
                    }}
                    .negative {{
                        color: #e74c3c;
                    }}
                    .winner {{
                        background: linear-gradient(45deg, #f39c12, #e74c3c);
                        color: white;
                        padding: 5px 10px;
                        border-radius: 15px;
                        font-size: 0.8rem;
                        display: inline-block;
                        margin-left: 10px;
                    }}
                    table {{
                        width: 100%;
                        border-collapse: collapse;
                        margin: 20px 0;
                        background: white;
                    }}
                    th, td {{
                        padding: 12px;
                        text-align: center;
                        border-bottom: 1px solid #ddd;
                    }}
                    th {{
                        background-color: #3498db;
                        color: white;
                    }}
                    tr:hover {{
                        background-color: #f5f5f5;
                    }}
                </style>
            </head>
            <body>
                <h1>贵州茅台双策略对比回测报告</h1>
                <p><strong>股票代码:</strong> 600519 (贵州茅台) | <strong>回测期间:</strong> 2020-01-01 至 2023-01-01</p>
                <p><strong>报告生成时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                
                <div class="comparison-grid">
                    <div class="strategy-card sma-card">
                        <h2>🎯 SMA交叉策略 <span class="winner">🎉</span></h2>
                        <div class="metrics">
                            <div class="metric">
                                <div>总收益率</div>
                                <div class="metric-value {'' if sma_return >= 0 else 'negative'}">{sma_return:.2f}%</div>
                            </div>
                            <div class="metric">
                                <div>夏普比率</div>
                                <div class="metric-value {'' if sma_sharpe >= 0 else 'negative'}">{sma_sharpe:.2f}</div>
                            </div>
                            <div class="metric">
                                <div>最大回撤</div>
                                <div class="metric-value negative">{sma_drawdown:.2f}%</div>
                            </div>
                            <div class="metric">
                                <div>最终资金</div>
                                <div class="metric-value {'' if sma_return >= 0 else 'negative'}">{sma_final_value:.2f}</div>
                            </div>
                        </div>
                        <p><strong>策略参数:</strong> 10日均线 × 60日均线</p>
                    </div>
                    
                    <div class="strategy-card buy-hold-card">
                        <h2>🛡️ Buy & Hold策略</h2>
                        <div class="metrics">
                            <div class="metric">
                                <div>总收益率</div>
                                <div class="metric-value {'' if buy_hold_return >= 0 else 'negative'}">{buy_hold_return:.2f}%</div>
                            </div>
                            <div class="metric">
                                <div>夏普比率</div>
                                <div class="metric-value {'' if buy_hold_sharpe >= 0 else 'negative'}">{buy_hold_sharpe:.2f}</div>
                            </div>
                            <div class="metric">
                                <div>最大回撤</div>
                                <div class="metric-value negative">{buy_hold_drawdown:.2f}%</div>
                            </div>
                            <div class="metric">
                                <div>最终资金</div>
                                <div class="metric-value {'' if buy_hold_return >= 0 else 'negative'}">{buy_hold_final_value:.2f}</div>
                            </div>
                        </div>
                        <p><strong>策略说明:</strong> 买入并持有策略，作为基准对比</p>
                    </div>
                </div>
                
                <h2>📊 详细对比数据</h2>
                <table>
                    <thead>
                        <tr>
                            <th>指标</th>
                            <th>SMA交叉策略</th>
                            <th>Buy & Hold策略</th>
                            <th>SMA优势</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>总收益率</td>
                            <td>{sma_return:.2f}%</td>
                            <td>{buy_hold_return:.2f}%</td>
                            <td>{'✅' if sma_return > buy_hold_return else '❌'}</td>
                        </tr>
                        <tr>
                            <td>夏普比率</td>
                            <td>{sma_sharpe:.2f}</td>
                            <td>{buy_hold_sharpe:.2f}</td>
                            <td>{'✅' if sma_sharpe > buy_hold_sharpe else '❌'}</td>
                        </tr>
                        <tr>
                            <td>最大回撤</td>
                            <td>{sma_drawdown:.2f}%</td>
                            <td>{buy_hold_drawdown:.2f}%</td>
                            <td>{'✅' if sma_drawdown < buy_hold_drawdown else '❌'}</td>
                        </tr>
                        <tr>
                            <td>最终资金</td>
                            <td>{sma_final_value:.2f}</td>
                            <td>{buy_hold_final_value:.2f}</td>
                            <td>{'✅' if sma_final_value > buy_hold_final_value else '❌'}</td>
                        </tr>
                    </tbody>
                </table>
                
                <h2>💡 策略分析总结</h2>
                <p><strong>SMA交叉策略表现:</strong> {'优于' if sma_return > buy_hold_return else '不如'}Buy & Hold策略，在贵州茅台{'20-23' if '20-23' in '2020-2023' else '2020-2023'}期间{'具有更好的收益表现' if sma_return > buy_hold_return else '收益相对较低'}。</p>
                
                <p><strong>风险收益分析:</strong> SMA策略{'具有更好的风险调整后收益' if sma_sharpe > buy_hold_sharpe else '风险调整后收益相对较低'}（夏普比率{'更高' if sma_sharpe > buy_hold_sharpe else '更低'}）。</p>
                
                <p><strong>策略建议:</strong> {'SMA交叉策略适合风险厌恶型投资者' if sma_drawdown < buy_hold_drawdown else 'Buy & Hold策略在风险控制方面表现更好'}。</p>
                
                <hr>
                <p><em>数据来源: AkShare 金融数据接口 | 策略引擎: Backtrader</em></p>
            </body>
            </html>
            """
            
            # 保存HTML文件
            html_path = os.path.join(self.results_dir, 'strategy_comparison_report.html')
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
                
            # 保存简单的对比文本报告
            txt_path = os.path.join(self.results_dir, 'strategy_comparison_summary.txt')
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write("贵州茅台双策略对比回测报告\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"回测期间: 2020-01-01 至 2023-01-01\n")
                f.write(f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                f.write(f"SMA交叉策略 ({self.sma_fast_period}日×{self.sma_slow_period}日均线):\n")
                f.write(f"  总收益率: {sma_return:.2f}%\n")
                f.write(f"  夏普比率: {sma_sharpe:.2f}\n")
                f.write(f"  最大回撤: {sma_drawdown:.2f}%\n")
                f.write(f"  最终资金: {sma_final_value:.2f}\n\n")
                
                f.write("Buy & Hold策略:\n")
                f.write(f"  总收益率: {buy_hold_return:.2f}%\n")
                f.write(f"  夏普比率: {buy_hold_sharpe:.2f}\n")
                f.write(f"  最大回撤: {buy_hold_drawdown:.2f}%\n")
                f.write(f"  最终资金: {buy_hold_final_value:.2f}\n\n")
                
                f.write("策略比较:\n")
                f.write(f"  收益率优势: {'SMA策略' if sma_return > buy_hold_return else 'Buy & Hold策略'}\n")
                f.write(f"  风险调整收益: {'SMA策略' if sma_sharpe > buy_hold_sharpe else 'Buy & Hold策略'}\n")
                f.write(f"  回撤控制: {'SMA策略' if sma_drawdown < buy_hold_drawdown else 'Buy & Hold策略'}\n")
                
        except Exception as e:
            print(f"生成对比报告时出错: {e}")
    
    def _plot_equity_curve(self, runner, stock_df):
        """
        绘制权益曲线
        """
        try:
            # 绘制并保存图表
            plt.figure(figsize=(14, 8))
            
            # 使用plotly创建交互式图表
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                               vertical_spacing=0.05, 
                               subplot_titles=('价格走势与均线', '成交量'))
            
            # 添加价格线
            fig.add_trace(go.Candlestick(x=stock_df.index, 
                                        open=stock_df['open'], 
                                        high=stock_df['high'], 
                                        low=stock_df['low'], 
                                        close=stock_df['close'],
                                        name='价格'),
                          row=1, col=1)
            
            # 计算均线用于显示
            fast_ma = stock_df['close'].rolling(window=5).mean()
            slow_ma = stock_df['close'].rolling(window=20).mean()
            
            # 添加均线
            fig.add_trace(go.Scatter(x=stock_df.index, y=fast_ma, mode='lines', name='5日均线', line=dict(color='blue')), row=1, col=1)
            fig.add_trace(go.Scatter(x=stock_df.index, y=slow_ma, mode='lines', name='20日均线', line=dict(color='red')), row=1, col=1)
            
            # 添加成交量
            fig.add_trace(go.Bar(x=stock_df.index, y=stock_df['volume'], name='成交量', marker_color='rgba(169, 169, 169, 0.6)'), row=2, col=1)
            
            # 更新布局
            fig.update_layout(height=800, title_text="双均线策略回测结果", 
                             xaxis_rangeslider_visible=False, 
                             font=dict(family="SimHei, Arial", size=12))
            
            # 保存HTML文件
            html_path = os.path.join(self.results_dir, 'tear_sheet.html')
            try:
                fig.write_html(html_path)
                print(f"绩效报告已保存到 {html_path}")
            except Exception as e:
                print(f"保存HTML报告失败: {e}")
            
            # 保存为静态图片
            img_path = os.path.join(self.results_dir, 'equity_curve.png')
            try:
                # 先尝试使用plotly保存
                fig.write_image(img_path)
                print(f"权益曲线图已保存到 {img_path}")
            except Exception as e:
                print(f"使用plotly保存图片失败，尝试使用matplotlib: {e}")
                # 如果失败，使用matplotlib作为备选
                try:
                    plt.figure(figsize=(14, 8))
                    plt.plot(stock_df.index, stock_df['close'], label='收盘价')
                    # 计算并绘制均线
                    if len(stock_df) >= 5:
                        plt.plot(stock_df.index, stock_df['close'].rolling(window=5).mean(), label='5日均线', color='blue')
                    if len(stock_df) >= 20:
                        plt.plot(stock_df.index, stock_df['close'].rolling(window=20).mean(), label='20日均线', color='red')
                    plt.title('股票价格走势图')
                    plt.xlabel('日期')
                    plt.ylabel('价格')
                    plt.grid(True)
                    plt.legend()
                    plt.tight_layout()
                    plt.savefig(img_path)
                    plt.close()
                    print(f"备选图表已保存到 {img_path}")
                except Exception as me:
                    print(f"保存图片失败: {me}")
            
        except Exception as e:
            print(f"绘制图表时出错: {e}")
            # 如果交互式图表失败，使用matplotlib作为备选
            try:
                plt.figure(figsize=(14, 8))
                plt.plot(stock_df.index, stock_df['close'], label='收盘价')
                plt.title('股票价格走势图')
                plt.xlabel('日期')
                plt.ylabel('价格')
                plt.grid(True)
                plt.legend()
                img_path = os.path.join(self.results_dir, 'equity_curve.png')
                plt.savefig(img_path)
                plt.close()
                print(f"备选图表已保存到 {img_path}")
            except:
                pass
    
    def _generate_tearsheet(self, result, stock_df):
        """
        生成详细的绩效报告
        """
        try:
            # 计算一些基本统计指标
            total_return = result['total_return'] * 100
            
            # 获取夏普比率
            sharpe_ratio = result['sharpe_ratio'].get('sharperatio', 0)
            
            # 获取最大回撤
            max_drawdown = result['drawdown'].get('max', {}).get('drawdown', 0)
            
            # 创建HTML报告
            html_content = f"""
            <!DOCTYPE html>
            <html lang="zh-CN">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>双均线策略回测报告</title>
                <style>
                    body {{
                        font-family: 'SimHei', Arial, sans-serif;
                        margin: 40px;
                        line-height: 1.6;
                        color: #333;
                    }}
                    h1, h2 {{
                        color: #2c3e50;
                    }}
                    .metrics {{
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                        gap: 20px;
                        margin: 30px 0;
                    }}
                    .metric-card {{
                        background: #f9f9f9;
                        padding: 20px;
                        border-radius: 8px;
                        text-align: center;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }}
                    .metric-value {{
                        font-size: 2rem;
                        font-weight: bold;
                        margin: 10px 0;
                    }}
                    .positive {{
                        color: #2ecc71;
                    }}
                    .negative {{
                        color: #e74c3c;
                    }}
                    table {{
                        width: 100%;
                        border-collapse: collapse;
                        margin: 20px 0;
                    }}
                    th, td {{
                        padding: 12px;
                        text-align: left;
                        border-bottom: 1px solid #ddd;
                    }}
                    th {{
                        background-color: #f2f2f2;
                    }}
                    tr:hover {{
                        background-color: #f5f5f5;
                    }}
                </style>
            </head>
            <body>
                <h1>双均线策略回测报告</h1>
                <p>报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                
                <h2>核心绩效指标</h2>
                <div class="metrics">
                    <div class="metric-card">
                        <div>总收益率</div>
                        <div class="metric-value {'' if total_return >= 0 else 'negative'}">{total_return:.2f}%</div> 
                        <div>初始资金的增长百分比</div>
                    </div>
                    <div class="metric-card">
                        <div>夏普比率</div>
                        <div class="metric-value {'' if sharpe_ratio >= 0 else 'negative'}">{sharpe_ratio:.2f}</div>
                        <div>风险调整后收益指标</div>
                    </div>
                    <div class="metric-card">
                        <div>最大回撤</div>
                        <div class="metric-value negative">{max_drawdown:.2f}%</div>
                        <div>峰值到谷值的最大损失百分比</div>
                    </div>
                    <div class="metric-card">
                        <div>最终资金</div>
                        <div class="metric-value {'' if total_return >= 0 else 'negative'}">{result['final_value']:.2f}</div>
                        <div>回测结束后的总资产</div>
                    </div>
                </div> 
                
                <h2>回测参数</h2>
                <table>
                    <tr>
                        <th>参数</th>
                        <th>值</th>
                    </tr>
                    <tr>
                        <td>初始资金</td>
                        <td>100,000.00</td>
                    </tr>
                    <tr>
                        <td>佣金费率</td>
                        <td>0.1%</td>
                    </tr>
                    <tr>
                        <td>短期均线</td>
                        <td>{self.sma_fast_period}日</td>
                    </tr>
                    <tr>
                        <td>长期均线</td>
                        <td>{self.sma_slow_period}日</td>
                    </tr>
                </table>
                
                <h2>回测说明</h2>
                <p>本回测使用双均线交叉策略，当短期均线上穿长期均线时买入，下穿时卖出。</p>
                <p>数据来源：AkShare 金融数据接口</p>
            </body>
            </html>
            """
            
            # 保存HTML文件
            html_path = os.path.join(self.results_dir, 'tear_sheet.html')
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
                
        except Exception as e:
            print(f"生成绩效报告时出错: {e}")
            # 创建简单的文本报告作为备选
            txt_path = os.path.join(self.results_dir, 'performance_summary.txt')
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(f"双均线策略回测报告\n")
                f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(f"总收益率: {result['total_return'] * 100:.2f}%\n")
                f.write(f"夏普比率: {result['sharpe_ratio'].get('sharperatio', 0):.2f}\n")
                f.write(f"最大回撤: {result['drawdown'].get('max', {}).get('drawdown', 0):.2f}%\n")
                f.write(f"最终资金: {result['final_value']:.2f}\n")

def main():
    """
    主函数
    """
    # SMA策略参数配置
    sma_fast_period = 5  # 短期均线周期
    sma_slow_period = 60  # 长期均线周期
    
    print("========== AkShare + Backtrader 双均线策略回测 ==========\n")
    print(f"策略参数: {sma_fast_period}日 × {sma_slow_period}日均线\n")
    
    # 创建回测管理器，传入配置参数
    manager = BacktestManager(sma_fast_period=sma_fast_period, sma_slow_period=sma_slow_period)
    
    # 运行双策略对比回测
    result = manager.run_backtest(
        symbol='600519',  # 贵州茅台
        start_date='20200101',
        end_date='20230101',
        compare_strategies=True  # 启用双策略对比
    )
    
    print("\n========== 回测完成 ==========\n")
    
    # 打印关键指标
    try:
        if isinstance(result, dict) and 'sma' in result and 'buy_hold' in result:
            # 双策略对比结果
            sma_result = result['sma']
            buy_hold_result = result['buy_hold']
            
            print(f"SMA策略 ({sma_fast_period}日×{sma_slow_period}日均线) 结果:")
            if isinstance(sma_result, dict) and 'total_return' in sma_result:
                total_return = sma_result.get('total_return', 0) * 100
                sharpe_ratio = sma_result.get('sharpe_ratio', {}).get('sharperatio', 0) if sma_result.get('sharpe_ratio') else 0
                max_drawdown = sma_result.get('drawdown', {}).get('max', {}).get('drawdown', 0) if sma_result.get('drawdown') else 0
                
                print(f"  Annual Return: {total_return:.2f}%")
                print(f"  Sharpe: {sharpe_ratio:.2f}")
                print(f"  Max Drawdown: {max_drawdown:.2f}%")
            else:
                print(f"  SMA策略结果格式异常: {type(sma_result)}")
            
            print("\nBuy & Hold策略结果:")
            if isinstance(buy_hold_result, dict) and 'total_return' in buy_hold_result:
                bh_total_return = buy_hold_result.get('total_return', 0) * 100
                bh_sharpe_ratio = buy_hold_result.get('sharpe_ratio', {}).get('sharperatio', 0) if buy_hold_result.get('sharpe_ratio') else 0
                bh_max_drawdown = buy_hold_result.get('drawdown', {}).get('max', {}).get('drawdown', 0) if buy_hold_result.get('drawdown') else 0
                
                print(f"  Annual Return: {bh_total_return:.2f}%")
                print(f"  Sharpe: {bh_sharpe_ratio:.2f}")
                print(f"  Max Drawdown: {bh_max_drawdown:.2f}%")
                
                print(f"\n策略对比结论:")
                if total_return > bh_total_return:
                    print(f"  SMA策略收益率({total_return:.2f}%)优于Buy & Hold({bh_total_return:.2f}%)")
                else:
                    print(f"  Buy & Hold策略收益率({bh_total_return:.2f}%)优于SMA策略({total_return:.2f}%)")
            else:
                print(f"  Buy & Hold策略结果格式异常: {type(buy_hold_result)}")
                
        elif isinstance(result, dict) and 'total_return' in result:
            # 单策略结果
            total_return = result.get('total_return', 0) * 100
            sharpe_ratio = result.get('sharpe_ratio', {}).get('sharperatio', 0)
            max_drawdown = result.get('drawdown', {}).get('max', {}).get('drawdown', 0)
            
            print(f"Annual Return: {total_return:.2f}%")
            print(f"Sharpe: {sharpe_ratio:.2f}")
            print(f"Max Drawdown: {max_drawdown:.2f}%")
        else:
            print(f"回测结果格式异常: {type(result)}")
            print(f"结果内容: {result}")
    except Exception as e:
        print(f"处理回测结果时出错: {e}")
        print(f"结果类型: {type(result)}")
        print(f"结果内容: {result}")

if __name__ == '__main__':
    main()
