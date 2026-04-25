import backtrader as bt
import requests
import json
import time
import pandas as pd
import pyfolio as pf
import quantstats as qs
import webbrowser
import os

#self lib
from data import get_st_data as gd #数据
from strategies import GoldenCrossStrategy # 导入策略

def main():
    cerebro = bt.Cerebro()
    cerebro.addstrategy(GoldenCrossStrategy,
                        fast_period=6,  # 短期均线周期
                        slow_period=20,  # 长期均线周期
                        printlog=True)
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
        codes='1.000001',  #上证指数做基线
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