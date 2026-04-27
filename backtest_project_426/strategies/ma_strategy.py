# ma_strategy.py
import backtrader as bt
from utils.logger import setup_logger, get_trade_logger, get_optimize_logger

class GoldenCrossStrategy(bt.Strategy):
    params = (
        ('fast_period', 5),  # 短期均线周期
        ('slow_period', 10),  # 长期均线周期
        #('printlog', True)
    )

    def __init__(self):
        # 保存收盘价引用
        self.dataclose = self.datas[0].close

        # 初始化订单状态
        self.order = None
        self.buyprice = None
        self.buycomm = None

        # 初始化日志
        self.logger = setup_logger(self.__class__.__name__)
        self.trade_logger = get_trade_logger()
        self.opt_logger = get_optimize_logger()

        # 创建移动平均线
        self.sma_fast = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.params.fast_period)
        self.sma_slow = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.params.slow_period)

        # 计算金叉和死叉
        # 金叉：快速均线上穿慢速均线
        # 死叉：快速均线下穿慢速均线
        self.crossover = bt.indicators.CrossOver(self.sma_fast, self.sma_slow)

        # 添加其他技术指标用于图表显示
        #bt.indicators.ExponentialMovingAverage(self.datas[0], period=25)
        #bt.indicators.WeightedMovingAverage(self.datas[0], period=25, subplot=True)
        #bt.indicators.StochasticSlow(self.datas[0])
        bt.indicators.MACDHisto(self.datas[0])
        #rsi = bt.indicators.RSI(self.datas[0])
        #bt.indicators.SmoothedMovingAverage(rsi, period=10)
        #bt.indicators.ATR(self.datas[0], plot=False)

        self.logger.info(f"策略初始化完成: fast_period={self.params.fast_period}, "
                        f"slow_period={self.params.slow_period}")


    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.logger.info(
                    '买入执行，价格：%.2f，成本：%.2f，佣金 %.2f' %
                    (order.executed.price, order.executed.value, order.executed.comm))
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:
                self.logger.info('卖出执行，价格：%.2f，成本：%.2f，佣金 %.2f' %
                         (order.executed.price, order.executed.value, order.executed.comm))

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.logger.info('订单取消/保证金不足/拒绝')

        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.logger.info('利润记录，毛利润 %.2f，净利润 %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def next(self):
        # 记录收盘价
        self.logger.info(f'收盘价: {self.dataclose[0]:.2f}, '
                 f'快线: {self.sma_fast[0]:.2f}, '
                 f'慢线: {self.sma_slow[0]:.2f}')

        # 如果有未完成的订单，不执行新操作
        if self.order:
            return

        # 检查是否没有持仓
        if not self.position:
            # 金叉买入信号：快速均线上穿慢速均线
            if self.crossover > 0:  # 金叉
                self.trade_logger.info(f'金叉买入信号, 收盘价: {self.dataclose[0]:.2f}')
                self.order = self.buy()

        else:
            # 有持仓时，死叉卖出信号：快速均线下穿慢速均线
            if self.crossover < 0:  # 死叉
                self.trade_logger.info(f'死叉卖出信号, 收盘价: {self.dataclose[0]:.2f}')
                self.order = self.sell()

    def stop(self):
        self.opt_logger.info(f'FAST_MA Period：{self.params.fast_period} SLOW_MA Period：{self.params.slow_period} Ending Value：{self.broker.getvalue()}')