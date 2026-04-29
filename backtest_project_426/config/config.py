# config/config.py
import os
import datetime


class Config:
    # 回测参数
    INITIAL_CASH = 100000.0
    COMMISSION = 0.0003
    SLIPPAGE = 0.001
    STAKE_SIZE = 10

    # 数据参数
    DEFAULT_SYMBOL = '1.000001'
    DEFAULT_START_DATE = '2025-04-15'
    DEFAULT_END_DATE = '2026-04-15'
    DEFAULT_PERIOD = '1d'

    # 策略配置（后续只改这里即可切换策略）
    #STRATEGY_NAME = "GoldenCrossStrategy"
    STRATEGY_NAME = "RSIStrategy"

    STRATEGY_PARAMS = {
        "GoldenCrossStrategy": {
            "fast_period": 6,
            "slow_period": 20,
        },
        "RSIStrategy": {
            "rsi_period": 14,
            "oversold": 30,
            "overbought": 70,
        },
    }

    # 文件路径
    DATA_DIR = "data"
    STRATEGIES_DIR = "strategies"
    REPORTS_DIR = "reports"  # 新增报告目录

    @classmethod
    def get_report_path(cls):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"{cls.get_strategy_name()}_{timestamp}.html"
        return os.path.join(cls.REPORTS_DIR, report_filename)

    @classmethod
    def get_strategy_name(cls):
        return cls.STRATEGY_NAME

    @classmethod
    def get_strategy_params(cls):
        return cls.STRATEGY_PARAMS.get(cls.STRATEGY_NAME, {})