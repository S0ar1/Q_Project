import backtrader as bt

class BuyAndHold(bt.Strategy):
    """
    Buy & Hold 策略：买入并持有策略，作为对比基准
    
    策略逻辑：
    1. 在策略开始的第一个交易日用全部资金买入股票
    2. 期间不进行任何买卖操作，持有到策略结束
    3. 作为其他策略的基准对比
    """
    # 策略参数
    params = (
        ('printlog', True),  # 是否打印日志
    )

    def __init__(self):
        # 跟踪订单和买入状态
        self.order = None
        self.buyprice = None
        self.buycomm = None
        self.buy_executed = False
        self.initial_value = None
        
    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # 订单已提交或已接受，不需要操作
            return

        # 检查订单是否已完成
        if order.status in [order.Completed]:
            if order.isbuy():  # 如果是买入订单
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
                self.buy_executed = True
                if self.params.printlog:
                    self.log(f'买入: 价格={order.executed.price:.2f}, 成本={order.executed.value:.2f}, 佣金={order.executed.comm:.2f}')
            # 设置订单为None，表示没有待处理的订单
            self.order = None
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            # 订单被取消、保证金不足或被拒绝
            self.order = None

    def notify_trade(self, trade):
        # Buy & Hold策略在持有期间没有交易，所以通常不会触发此方法
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

    def start(self):
        """
        策略开始时执行，记录初始资金
        """
        self.initial_value = self.broker.getvalue()
        if self.params.printlog:
            self.log(f'初始资金: {self.initial_value:.2f}', doprint=True)

    def next(self):
        # Buy & Hold策略只在第一个交易日买入
        # 检查是否还有待处理的订单
        if self.order:
            return

        # 如果还没有买入且没有持仓，则买入
        if not self.buy_executed and not self.position:
            # 使用全部资金买入
            # 计算可以买入的股份数量
            cash = self.broker.getcash()
            price = self.data.close[0]
            size = int(cash / price)  # 计算可买股数
            
            if size > 0:
                self.order = self.buy(size=size)

    def stop(self):
        """
        策略结束时执行
        """
        if self.params.printlog:
            final_value = self.broker.getvalue()
            if self.initial_value:
                total_return = (final_value - self.initial_value) / self.initial_value * 100
                self.log(f'Buy & Hold策略 - 最终价值: {final_value:.2f}', doprint=True)
                self.log(f'总收益率: {total_return:.2f}%', doprint=True)
            else:
                self.log(f'Buy & Hold策略 - 最终价值: {final_value:.2f}', doprint=True)