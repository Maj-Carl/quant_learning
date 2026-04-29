# rsi_strategy.py
import backtrader as bt
from utils.logger import setup_logger, get_trade_logger, get_optimize_logger

class RSIStrategy(bt.Strategy):
    params = (
        ("rsi_period", 12),
        ("oversold", 34),
        ("overbought", 83),
    )

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None
        self.buyprice = None
        self.buycomm = None

        self.logger = setup_logger(self.__class__.__name__)
        self.trade_logger = get_trade_logger()
        self.opt_logger = get_optimize_logger()

        self.rsi = bt.indicators.RSI(
            self.datas[0],
            period=self.params.rsi_period
        )

        self.logger.info(
            "RSI策略初始化完成: rsi_period=%s, oversold=%s, overbought=%s",
            self.params.rsi_period,
            self.params.oversold,
            self.params.overbought,
        )

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.logger.info(
                    "买入执行，价格：%.2f，成本：%.2f，佣金：%.2f",
                    order.executed.price,
                    order.executed.value,
                    order.executed.comm,
                )
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:
                self.logger.info(
                    "卖出执行，价格：%.2f，成本：%.2f，佣金：%.2f",
                    order.executed.price,
                    order.executed.value,
                    order.executed.comm,
                )

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.logger.info("订单取消/保证金不足/拒绝")

        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.logger.info(
            "利润记录，毛利润 %.2f，净利润 %.2f",
            trade.pnl,
            trade.pnlcomm
        )

    def next(self):
        self.logger.info("收盘价: %.2f, RSI: %.2f", self.dataclose[0], self.rsi[0])

        if self.order:
            return

        if not self.position:
            if self.rsi[0] < self.params.oversold:
                self.trade_logger.info(
                    "RSI超卖买入信号, 收盘价: %.2f, RSI: %.2f",
                    self.dataclose[0],
                    self.rsi[0],
                )
                self.order = self.buy()
        else:
            if self.rsi[0] > self.params.overbought:
                self.trade_logger.info(
                    "RSI超买卖出信号, 收盘价: %.2f, RSI: %.2f",
                    self.dataclose[0],
                    self.rsi[0],
                )
                self.order = self.sell()

    def stop(self):
        self.opt_logger.info(
            "RSI Period：%s Oversold：%s Overbought：%s Ending Value：%s",
            self.params.rsi_period,
            self.params.oversold,
            self.params.overbought,
            self.broker.getvalue(),
        )
