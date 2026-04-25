import backtrader as bt
import requests
import json
import time
import pandas as pd
import get_st_data as gd


class GoldenCrossStrategy(bt.Strategy):
    params = (
        ('fast_period', 5),  # 短期均线周期
        ('slow_period', 10),  # 长期均线周期
        ('printlog', True)
    )

    def log(self, txt, dt=None, doprint=False):
        if self.params.printlog or doprint:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt}, {txt}')

    def __init__(self):
        # 保存收盘价引用
        self.dataclose = self.datas[0].close

        # 初始化订单状态
        self.order = None
        self.buyprice = None
        self.buycomm = None

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

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('订单取消/保证金不足/拒绝')

        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log('利润记录，毛利润 %.2f，净利润 %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def next(self):
        # 记录收盘价
        self.log(f'收盘价: {self.dataclose[0]:.2f}, '
                 f'快线: {self.sma_fast[0]:.2f}, '
                 f'慢线: {self.sma_slow[0]:.2f}')

        # 如果有未完成的订单，不执行新操作
        if self.order:
            return

        # 检查是否没有持仓
        if not self.position:
            # 金叉买入信号：快速均线上穿慢速均线
            if self.crossover > 0:  # 金叉
                self.log(f'金叉买入信号, 收盘价: {self.dataclose[0]:.2f}')
                self.order = self.buy()

        else:
            # 有持仓时，死叉卖出信号：快速均线下穿慢速均线
            if self.crossover < 0:  # 死叉
                self.log(f'死叉卖出信号, 收盘价: {self.dataclose[0]:.2f}')
                self.order = self.sell()

    def stop(self):
        self.log(f'FAST_MA Period：{self.params.fast_period} SLOW_MA Period：{self.params.slow_period} Ending Value：{self.broker.getvalue()}', doprint=True)


def main(opt=False):
    # 创建Cerebro引擎
    cerebro = bt.Cerebro()

    if not opt:
        # 添加策略
        cerebro.addstrategy(GoldenCrossStrategy,
                            fast_period=5,  # 短期均线周期
                            slow_period=10,  # 长期均线周期
                            printlog=True)
    else:
        cerebro.optstrategy(GoldenCrossStrategy,
                            fast_period=range(3, 7),  # 短期均线周期
                            slow_period=range(12, 25),  # 长期均线周期
                            printlog=False)

    # 获取数据
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

    # 创建数据源
    data = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(data)

    # 设置初始资金
    cerebro.broker.setcash(100000.0)

    # 设置交易数量
    cerebro.addsizer(bt.sizers.FixedSize, stake=10)

    # 设置交易佣金为万分之三（0.03%）
    cerebro.broker.setcommission(commission=0.0003)

    # 设置滑点
    cerebro.broker.set_slippage_perc(0.001)

    # 打印初始资金
    print(f'初始资金: {cerebro.broker.getvalue():.2f}')

    # 运行回测
    if not opt:#回测模式
        cerebro.run()
        print(f'最终资金: {cerebro.broker.getvalue():.2f}')
        #可选：绘制图表
        cerebro.plot(style='bar')

    else:#优化模式
        opt_results = cerebro.run(optreturn=False)
        # 收集优化结果
        results_list = []

        for strategy_runs in opt_results:
            for strategy in strategy_runs:
                # 获取策略参数和最终价值
                fast = strategy.params.fast_period
                slow = strategy.params.slow_period
                final_value = strategy.broker.getvalue()

                results_list.append({
                    '快线周期': fast,
                    '慢线周期': slow,
                    '最终资金': final_value,
                    '收益率': (final_value - 100000) / 100000 * 100
                })

        results_df = pd.DataFrame(results_list)
        print(results_df)
        # 找出最佳结果
        best_result = results_df.loc[results_df['最终资金'].idxmax()]
        print(f"\n最佳参数组合:")
        print(best_result)

if __name__ == '__main__':
    main(opt=True)