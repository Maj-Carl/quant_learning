
import backtrader as bt
import requests
import json
import time
import pandas as pd
import get_st_data as gd

class TestStrategy(bt.Strategy):
    params = (
        ('maperiod', 15),
        ('printlog', True),
    )

    def log(self, txt, dt=None, doprint=False):
        if self.params.printlog or doprint:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt}, {txt}')
            #print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None
        self.buyprice = None
        self.buycomm = None
        self.sma = bt.indicators.SimpleMovingAverage(self.datas[0], period=self.params.maperiod)

        # Indicators for the plotting show
        bt.indicators.ExponentialMovingAverage(self.datas[0], period=25)
        bt.indicators.WeightedMovingAverage(self.datas[0], period=25, subplot=True)
        bt.indicators.StochasticSlow(self.datas[0])
        bt.indicators.MACDHisto(self.datas[0])
        rsi = bt.indicators.RSI(self.datas[0])
        bt.indicators.SmoothedMovingAverage(rsi, period=10)
        bt.indicators.ATR(self.datas[0], plot=False)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    '买入执行，价格：%.2f，成本：%.2f，佣金 %.2f' %
                    (order.executed.price, order.executed.value, order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:
                self.log('卖出执行，价格：%.2f，成本：%.2f，佣金 %.2f' %
                         (order.executed.price, order.executed.value, order.executed.comm))
                self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('订单取消/保证金不足/拒绝')

        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('利润记录，毛利润 %.2f，净利润 %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def next(self):
        self.log(f'收盘价, {self.dataclose[0]:.2f}')
        #self.log('Close, %.2f' % self.dataclose[0])

        if self.order:
            return

        if not self.position:
            if self.dataclose[0] > self.sma[0]:
                self.log('创建买入订单, %.2f' % self.dataclose[0])
                self.order = self.buy()

        else:
            if len(self) < self.sma[0]:
                self.log('创建卖出订单, %.2f' % self.dataclose[0])
                self.order = self.sell()

    def stop(self):
        self.log('(MA Period %2d) Ending Value %.2f' % (self.params.maperiod, self.broker.getvalue()), doprint=True)


def main():
    cerebro = bt.Cerebro()
    cerebro.addstrategy(TestStrategy, maperiod=15)
    #cerebro.optstrategy(TestStrategy,maperiod=range(10, 31))

    df = gd.get_stock_data(
        codes='1.000001',
        period='1d',
        start_date='2025-04-15',
        end_date='2026-04-15',
        adjust='0',
        ty='指数',
        use_local=True,
        verbose=True
    )
    #print(df.to_string(max_cols=None))

    data = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(data)
    cerebro.broker.setcash(100000.0)
    cerebro.addsizer(bt.sizers.FixedSize, stake=10)
    # 设置交易佣金为万分之三（0.03%）
    cerebro.broker.setcommission(commission=0.0003)
    cerebro.broker.set_slippage_perc(0.001)
    #cerebro.run(maxcpus=1)
    print(f'初始资金: {cerebro.broker.getvalue():.2f}')

    cerebro.run()

    print(f'最终资金: {cerebro.broker.getvalue():.2f}')
    cerebro.plot(style='bar')

if __name__ == '__main__':
    main()