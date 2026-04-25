import backtrader as bt
import requests
import json
import time
import pandas as pd
import get_st_data as gd
import pyfolio as pf
import quantstats as qs
import webbrowser
import os

class TestStrategy(bt.Strategy):
    params = (
        ('maperiod', 15),
        ('printlog', True),
    )

    def log(self, txt, dt=None, doprint=False):
        if self.params.printlog or doprint:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt}, {txt}')
            # print('%s, %s' % (dt.isoformat(), txt))

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
        # self.log('Close, %.2f' % self.dataclose[0])

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
    #cerebro.optstrategy(TestStrategy, maperiod=range(10, 31))

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
    # print(df.to_string(max_cols=None))

    data = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(data)
    cerebro.broker.setcash(100000.0)
    cerebro.addsizer(bt.sizers.FixedSize, stake=10)
    # 设置交易佣金为万分之三（0.03%）
    cerebro.broker.setcommission(commission=0.0003)
    cerebro.broker.set_slippage_perc(0.001)
    # cerebro.run(maxcpus=1)
    print(f'初始资金: {cerebro.broker.getvalue():.2f}')

    cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name='AnnualReturn')
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, riskfreerate=0.003, annualize=True, _name='SharpeRatio')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='DrawDown')

    # 添加 PyFolio 分析器
    cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')  # 这里添加了

    strats = cerebro.run()
    strat = strats[0]

    benchmark_df = gd.get_stock_data(
        codes='1.000300',  # 沪深300
        period='1d',
        start_date='2025-04-15',
        end_date='2026-04-15',
        adjust='0',
        ty='指数',
        use_local=True,
        verbose=False
    )

    # 获取 PyFolio 数据
    pyfolio_analyzer = strat.analyzers.pyfolio
    returns, positions, transactions, gross_lev = pyfolio_analyzer.get_pf_items()

    # 移除时区信息
    returns.index = returns.index.tz_convert(None)

    # 计算基准收益率
    benchmark_returns = benchmark_df['close'].pct_change().dropna()
    benchmark_returns.index = pd.to_datetime(benchmark_returns.index)

    # 移除基准的时区信息
    if benchmark_returns.index.tz is not None:
        benchmark_returns.index = benchmark_returns.index.tz_localize(None)

    # 对齐索引
    benchmark_returns = benchmark_returns.reindex(returns.index, method='ffill').fillna(0)

    # 方法1：使用 QuantStats 生成 HTML 报告（推荐）
    print("正在生成 QuantStats HTML 报告...")

    # 生成完整的 HTML 报告
    qs.reports.html(returns,
                    benchmark=benchmark_returns,
                    output='quantstats_report.html',
                    title='移动平均策略回测报告',
                    benchmark_title="benchmark",  # 设置基准标题
                    download_filename='quantstats_report.html')

    # 在浏览器中打开报告
    report_path = os.path.abspath('quantstats_report.html')
    webbrowser.open(f'file://{report_path}')
    print(f"HTML 报告已生成: {report_path}")

    print(f'最终资金: {cerebro.broker.getvalue():.2f}')
    # cerebro.plot(style='bar')


if __name__ == '__main__':
    main()