import backtrader as bt

class SmaCross(bt.Strategy):
    """
    双均线交叉策略
    当短期均线上穿长期均线时买入，下穿时卖出
    """
    # 策略参数
    params = (
        ('fast', 5),    # 短期均线周期
        ('slow', 60),    # 长期均线周期
        ('printlog', True),  # 是否打印日志
    )

    def __init__(self):
        # 跟踪订单和持仓
        self.order = None
        self.buyprice = None
        self.buycomm = None
        
        # 添加移动均线指标
        self.fast_ma = bt.indicators.SMA(
            self.data.close, period=self.params.fast, plotname='10日均线')
        self.slow_ma = bt.indicators.SMA(
            self.data.close, period=self.params.slow, plotname='60日均线')
        
        # 交叉信号指标
        self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)
    
    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # 订单已提交或已接受，不需要操作
            return

        # 检查订单是否已完成
        if order.status in [order.Completed]:
            if order.isbuy():  # 如果是买入订单
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
                if self.params.printlog:
                    self.log(f'买入: 价格={order.executed.price:.2f}, 成本={order.executed.value:.2f}, 佣金={order.executed.comm:.2f}')
            elif order.issell():  # 如果是卖出订单
                if self.params.printlog:
                    self.log(f'卖出: 价格={order.executed.price:.2f}, 收入={order.executed.value:.2f}, 佣金={order.executed.comm:.2f}')
            # 设置订单为None，表示没有待处理的订单
            self.order = None
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            # 订单被取消、保证金不足或被拒绝
            self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        if self.params.printlog:
            self.log(f'交易利润: 毛利={trade.pnl:.2f}, 净利={trade.pnlcomm:.2f}')

    def log(self, txt, dt=None, doprint=False):
        """
        记录日志
        """
        if self.params.printlog or doprint:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()}, {txt}')

    def next(self):
        # 检查是否有待处理的订单
        if self.order:
            return

        # 检查是否已持仓
        if not self.position:
            # 如果没有持仓且短期均线上穿长期均线，则买入
            if self.crossover > 0:
                self.order = self.buy()
        else:
            # 如果已持仓且短期均线下穿长期均线，则卖出
            if self.crossover < 0:
                self.order = self.sell()

    def stop(self):
        """
        策略结束时执行
        """
        if self.params.printlog:
            self.log(f'{self.params.fast}/{self.params.slow} 均线策略 - 最终价值: {self.broker.getvalue():.2f}', doprint=True)

class BacktestRunner:
    """
    回测运行器，封装Backtrader的回测逻辑
    """
    def __init__(self, data, strategy_class=SmaCross, **strategy_params):
        self.data = data
        self.strategy_class = strategy_class
        self.strategy_params = strategy_params
        self.cerebro = bt.Cerebro()
        
    def setup(self):
        # 添加数据到回测引擎
        self.cerebro.adddata(self.data)
        
        # 添加策略到回测引擎
        self.cerebro.addstrategy(self.strategy_class, **self.strategy_params)
        
        # 设置初始资金
        self.cerebro.broker.setcash(100000.0)
        
        # 设置佣金
        self.cerebro.broker.setcommission(commission=0.001)  # 0.1% 佣金
        
        # 添加分析器
        self.cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name='annual_return')
        self.cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe_ratio', riskfreerate=0.0, annualize=True, timeframe=bt.TimeFrame.Days)
        self.cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        
        # 添加观察者
        self.cerebro.addobserver(bt.observers.Value)
        self.cerebro.addobserver(bt.observers.BuySell)
        self.cerebro.addobserver(bt.observers.DrawDown)
    
    def run(self):
        """
        运行回测
        """
        self.setup()
        print(f'初始资金: {self.cerebro.broker.getvalue():.2f}')
        
        # 运行回测
        thestrats = self.cerebro.run()
        thestrat = thestrats[0]
        
        print(f'最终资金: {self.cerebro.broker.getvalue():.2f}')
        
        # 获取分析结果
        annual_return = thestrat.analyzers.annual_return.get_analysis()
        sharpe_ratio = thestrat.analyzers.sharpe_ratio.get_analysis()
        drawdown = thestrat.analyzers.drawdown.get_analysis()
        
        # 计算年化收益率
        total_return = (self.cerebro.broker.getvalue() - 100000.0) / 100000.0
        print(f'总收益率: {total_return * 100:.2f}%')
        
        # 打印夏普比率和最大回撤
        if 'sharperatio' in sharpe_ratio and sharpe_ratio['sharperatio'] is not None:
            print(f'夏普比率: {sharpe_ratio["sharperatio"]:.2f}')
        else:
            print('夏普比率: N/A')
        
        if 'max' in drawdown and drawdown['max']:
            print(f'最大回撤: {drawdown["max"]["drawdown"]:.2f}%')
        else:
            print('最大回撤: N/A')
        
        # 返回分析结果
        result = {
            'annual_return': annual_return,
            'sharpe_ratio': sharpe_ratio,
            'drawdown': drawdown,
            'final_value': self.cerebro.broker.getvalue(),
            'total_return': total_return
        }
        
        return result
    
    def plot(self, filename=None):
        """
        绘制回测结果
        """
        if filename:
            self.cerebro.plot(style='candlestick', savefig=filename)
        else:
            self.cerebro.plot(style='candlestick')
