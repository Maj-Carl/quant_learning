# backtest_main.py
import pandas as pd
import backtrader as bt
import sys
import time
# 自定义模块
from data import get_st_data as gd
from strategies import GoldenCrossStrategy
from config.config import Config
from backtest.backtest_engine import BacktestEngine
from reports.report_generator import ReportGenerator
from utils.logger import setup_logger, get_trade_logger, get_performance_logger

def get_data():
    """获取回测数据"""
    df = gd.get_stock_data(
        codes=Config.DEFAULT_SYMBOL,
        period=Config.DEFAULT_PERIOD,
        start_date=Config.DEFAULT_START_DATE,
        end_date=Config.DEFAULT_END_DATE,
        adjust='0',
        ty='指数',
        use_local=True,
        verbose=True
    )
    return bt.feeds.PandasData(dataname=df)


def get_benchmark_data():
    """获取基准数据"""
    benchmark_df = gd.get_stock_data(
        codes=Config.DEFAULT_SYMBOL,
        period=Config.DEFAULT_PERIOD,
        start_date=Config.DEFAULT_START_DATE,
        end_date=Config.DEFAULT_END_DATE,
        adjust='0',
        ty='指数',
        use_local=True,
        verbose=False
    )
    return benchmark_df

# 初始化日志
logger = setup_logger(__name__)
trade_logger = get_trade_logger()
perf_logger = get_performance_logger()


def main():
    try:
        logger.info("=" * 50)
        logger.info("开始回测程序")
        # 记录性能开始
        perf_logger.info("回测开始")
        start_time = time.perf_counter()

        # 1. 初始化回测引擎
        engine = BacktestEngine()

        # 2. 添加策略
        engine.add_strategy(
            GoldenCrossStrategy,
            fast_period=Config.FAST_PERIOD,
            slow_period=Config.SLOW_PERIOD,
            #printlog=True
        )

        # 记录数据接口性能
        perf_logger.info("调取数据开始")
        # 3. 添加数据
        data_feed = get_data()

        elapsed_time = time.perf_counter() - start_time
        perf_logger.info(f"调取数据耗时{elapsed_time:.4f}秒")

        engine.add_data(data_feed)


        # 4. 添加仓位管理
        engine.add_sizer(bt.sizers.FixedSize, stake=Config.STAKE_SIZE)

        # 5. 添加分析器
        engine.add_analyzers()

        # 6. 运行回测
        #print(f'初始资金: {engine.cerebro.broker.getvalue():.2f}')

        logger.info(f"初始资金: {Config.INITIAL_CASH}")
        logger.info(f"回测期间: {Config.DEFAULT_START_DATE} 到 {Config.DEFAULT_END_DATE}")
        logger.info("=" * 50)

        strats = engine.run_backtest()
        strat = strats[0]

        # 7. 生成报告
        pyfolio_analyzer = strat.analyzers.pyfolio
        returns, positions, transactions, gross_lev = pyfolio_analyzer.get_pf_items()
        returns.index = returns.index.tz_convert(None)

        # 获取基准数据
        benchmark_df = get_benchmark_data()

        # 生成报告
        report_gen = ReportGenerator(returns)
        benchmark_returns = report_gen.prepare_benchmark_data(benchmark_df, returns)
        report_gen.benchmark_returns = benchmark_returns

        report_path = report_gen.generate_html_report()
        report_gen.open_in_browser(report_path)

        logger.info("回测完成")

        print(f'最终资金: {engine.cerebro.broker.getvalue():.2f}')
        print(f"HTML 报告已生成: {report_path}")

        # 可选：绘图
        # engine.cerebro.plot(style='bar')

        elapsed_time = time.perf_counter() - start_time
        perf_logger.info("回测结束")
        perf_logger.info(f"执行耗时{elapsed_time:.4f}秒")

    except Exception as e:
        logger.error(f"程序出错: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()