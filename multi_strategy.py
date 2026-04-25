import backtrader as bt
import requests
import json
import time
import pandas as pd
import get_st_data as gd


# 策略1: 简单均线交叉策略
class SMA_CrossStrategy(bt.Strategy):
    params = (
        ('fast_period', 10),  # 快线周期
        ('slow_period', 30),  # 慢线周期
    )

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()} {txt}')

    def __init__(self):
        # 保存对数据的引用
        self.data_close = self.datas[0].close

        # 跟踪订单和持仓
        self.order = None
        self.position_size = 0

        # 创建指标
        self.sma_fast = bt.ind.SMA(self.datas[0], period=self.params.fast_period)
        self.sma_slow = bt.ind.SMA(self.datas[0], period=self.params.slow_period)

        # 交叉信号
        self.crossover = bt.ind.CrossOver(self.sma_fast, self.sma_slow)

        # 策略名称
        self.name = "SMA_Cross"

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'{self.name} 买入执行, 价格: {order.executed.price:.2f}, 数量: {order.executed.size}')
            elif order.issell():
                self.log(f'{self.name} 卖出执行, 价格: {order.executed.price:.2f}, 数量: {order.executed.size}')

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('订单取消/保证金不足/拒绝')

        self.order = None

    def next(self):
        # 如果有订单未完成，跳过
        if self.order:
            return

        # 检查是否有持仓
        if not self.position:
            # 金叉买入
            if self.crossover > 0:
                self.order = self.buy(size=100)

        else:
            # 死叉卖出
            if self.crossover < 0:
                self.order = self.sell(size=100)


# 策略2: RSI超买超卖策略
class RSI_Strategy(bt.Strategy):
    params = (
        ('rsi_period', 14),
        ('rsi_overbought', 70),
        ('rsi_oversold', 30),
    )

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()} {txt}')

    def __init__(self):
        self.data_close = self.datas[0].close
        self.order = None
        self.position_size = 0

        # RSI指标
        self.rsi = bt.ind.RSI(self.datas[0], period=self.params.rsi_period)

        # 策略名称
        self.name = "RSI"

        # 跟踪买入信号
        self.last_rsi = 0

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'{self.name} 买入执行, 价格: {order.executed.price:.2f}, 数量: {order.executed.size}')
            elif order.issell():
                self.log(f'{self.name} 卖出执行, 价格: {order.executed.price:.2f}, 数量: {order.executed.size}')

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('订单取消/保证金不足/拒绝')

        self.order = None

    def next(self):
        if self.order:
            return

        # 检查RSI信号
        current_rsi = self.rsi[0]

        if not self.position:
            # RSI超卖，买入
            if current_rsi < self.params.rsi_oversold and self.last_rsi >= self.params.rsi_oversold:
                self.order = self.buy(size=50)

        else:
            # RSI超买，卖出
            if current_rsi > self.params.rsi_overbought and self.last_rsi <= self.params.rsi_overbought:
                self.order = self.sell(size=50)

        self.last_rsi = current_rsi


# 策略4: 组合策略（将前两个策略组合起来）
class CombinedStrategy(bt.Strategy):
    """真正的组合策略，在内部协调两个子策略"""
    params = (
        ('sma_fast', 10),
        ('sma_slow', 30),
        ('rsi_period', 14),
        ('rsi_overbought', 70),
        ('rsi_oversold', 30),
    )

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()} {txt}')

    def __init__(self):
        # 创建指标
        self.sma_fast = bt.ind.SMA(self.datas[0], period=self.params.sma_fast)
        self.sma_slow = bt.ind.SMA(self.datas[0], period=self.params.sma_slow)
        self.rsi = bt.ind.RSI(self.datas[0], period=self.params.rsi_period)

        # 交叉信号
        self.sma_crossover = bt.ind.CrossOver(self.sma_fast, self.sma_slow)

        # 跟踪RSI值
        self.last_rsi = 0

        # 跟踪两个策略的虚拟仓位
        self.sma_position = 0
        self.rsi_position = 0

        # 总仓位
        self.total_position = 0

        # 策略名称
        self.name = "RealCombined"

        # 跟踪订单
        self.order = None

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'{self.name} 买入执行, 价格: {order.executed.price:.2f}, 数量: {order.executed.size}')
                if self.sma_position == 0 and self.rsi_position == 0:
                    # 这是SMA策略的买入
                    self.sma_position = 100
                elif self.sma_position > 0 and self.rsi_position == 0:
                    # 这是RSI策略的买入
                    self.rsi_position = 50
                self.total_position = self.sma_position + self.rsi_position
            elif order.issell():
                self.log(f'{self.name} 卖出执行, 价格: {order.executed.price:.2f}, 数量: {order.executed.size}')
                if self.sma_position > 0 and self.total_position == 100:
                    # 这是SMA策略的卖出
                    self.sma_position = 0
                elif self.rsi_position > 0 and self.total_position == 50:
                    # 这是RSI策略的卖出
                    self.rsi_position = 0
                elif self.total_position == 150:
                    # 同时持有两个策略的仓位
                    if order.executed.size == 100:
                        self.sma_position = 0
                    elif order.executed.size == 50:
                        self.rsi_position = 0
                self.total_position = self.sma_position + self.rsi_position

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('订单取消/保证金不足/拒绝')

        self.order = None

    def next(self):
        if self.order:
            return

        # 获取当前RSI值
        current_rsi = self.rsi[0]

        # SMA策略逻辑
        if self.sma_crossover > 0 and self.sma_position == 0:
            # SMA金叉，买入100股
            self.order = self.buy(size=100)
        elif self.sma_crossover < 0 and self.sma_position > 0:
            # SMA死叉，卖出SMA持仓
            self.order = self.sell(size=self.sma_position)

        # RSI策略逻辑
        if current_rsi < self.params.rsi_oversold and self.last_rsi >= self.params.rsi_oversold and self.rsi_position == 0:
            # RSI超卖，买入50股
            self.order = self.buy(size=50)
        elif current_rsi > self.params.rsi_overbought and self.last_rsi <= self.params.rsi_overbought and self.rsi_position > 0:
            # RSI超买，卖出RSI持仓
            self.order = self.sell(size=self.rsi_position)

        self.last_rsi = current_rsi


# 策略绩效分析器
def analyze_results(strats, cerebro=None):
    for i, strat in enumerate(strats):
        if hasattr(strat, 'name'):
            print(f"\n{'=' * 50}")
            print(f"策略 {i + 1}: {strat.name} 绩效分析")
        else:
            print(f"\n{'=' * 50}")
            print(f"策略 {i + 1} 绩效分析")

        # 打印最终价值
        if cerebro:
            print(f"初始资金: {cerebro.broker.startingcash:.2f}")
            print(f"最终价值: {cerebro.broker.getvalue():.2f}")
            print(f"总收益率: {(cerebro.broker.getvalue() / cerebro.broker.startingcash - 1) * 100:.2f}%")
        else:
            print(f"初始资金: {strat.broker.startingcash:.2f}")
            print(f"最终价值: {strat.broker.getvalue():.2f}")
            print(f"总收益率: {(strat.broker.getvalue() / strat.broker.startingcash - 1) * 100:.2f}%")

        # 如果有analyzer结果
        if hasattr(strat, 'analyzers'):
            if 'SharpeRatio' in strat.analyzers:
                try:
                    sharpe = strat.analyzers.SharpeRatio.get_analysis()
                    if 'sharperatio' in sharpe:
                        print(f"夏普比率: {sharpe['sharperatio']:.4f}")
                except:
                    pass

            if 'AnnualReturn' in strat.analyzers:
                try:
                    annual_return = strat.analyzers.AnnualReturn.get_analysis()
                    print(f"年化收益率: {annual_return}")
                except:
                    pass

            if 'returns' in strat.analyzers:
                try:
                    returns = strat.analyzers.returns.get_analysis()
                    if 'rtot' in returns:
                        print(f"总收益率: {returns['rtot'] * 100:.2f}%")
                except:
                    pass

            if 'DrawDown' in strat.analyzers:
                try:
                    drawdown = strat.analyzers.DrawDown.get_analysis()
                    print(f"最大回撤: {drawdown.get('max', {}).get('drawdown', 0):.2f}%")
                except:
                    pass


def main():
    cerebro = bt.Cerebro()

    # 添加多个策略
    # 方法1: 使用addstrategy
    #cerebro.addstrategy(SMA_CrossStrategy)
    #cerebro.addstrategy(RSI_Strategy)
    cerebro.addstrategy(CombinedStrategy)
    # 方法2: 添加优化策略参数
    # cerebro.optstrategy(
    #     SMA_CrossStrategy,
    #     fast_period=range(5, 15, 5),  # 5, 10
    #     slow_period=range(20, 40, 10)  # 20, 30
    # )


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
    cerebro.broker.setcash(1000000.0)
    cerebro.addsizer(bt.sizers.FixedSize, stake=10)
    # 设置交易佣金为万分之三（0.03%）
    cerebro.broker.setcommission(commission=0.0003)
    cerebro.broker.set_slippage_perc(0.001)
    # cerebro.run(maxcpus=1)
    print(f'初始资金: {cerebro.broker.getvalue():.2f}')

    # 添加分析器
    cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name='AnnualReturn')
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, riskfreerate=0.003, annualize=True, _name='SharpeRatio')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='DrawDown')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')

    # 添加观察者
    cerebro.addobserver(bt.observers.Value)
    cerebro.addobserver(bt.observers.DrawDown)

    results = cerebro.run()

    # 遍历所有参数组合的结果
#    for i, run in enumerate(strats):
#        # 每个参数组合的返回结果是一个列表，包含一个策略实例
#        strat = run[0]
#
#        print(f"\n=============== 参数组合 {i + 1} (MA Period: {strat.params.maperiod}) ===============")
#        print("--------------- AnnualReturn -----------------")
#        print(strat.analyzers.AnnualReturn.get_analysis())
#        print("--------------- SharpeRatio -----------------")
#        print(strat.analyzers.SharpeRatio.get_analysis())
#        print("--------------- DrawDown -----------------")
#        print(strat.analyzers.DrawDown.get_analysis())
#        print(f'最终资金: {strat.broker.getvalue():.2f}')

    #    # 第一个策略
    #    strat = strats[0][0]
    #
    #    print("--------------- AnnualReturn -----------------")
    #    print(strat.analyzers.AnnualReturn.get_analysis())
    #    print("--------------- SharpeRatio -----------------")
    #    print(strat.analyzers.SharpeRatio.get_analysis())
    #    print("--------------- DrawDown -----------------")
    #    print(strat.analyzers.DrawDown.get_analysis())

    print(f'最终资金: {cerebro.broker.getvalue():.2f}')
    # cerebro.plot(style='bar')

    # 分析结果
    if len(results) > 0:
        if isinstance(results[0], list):
            # 多个策略的结果
            for i, strats in enumerate(results):
                print(f"\n=============== 策略组合 {i+1} ===============")
                analyze_results(strats, cerebro)
        else:
            # 单个策略的结果
            analyze_results(results, cerebro)

    # 绘制图表
    # 注意：多策略情况下，图表会显示所有策略的信号
    cerebro.plot(style='candlestick', volume=False)


if __name__ == '__main__':
    main()