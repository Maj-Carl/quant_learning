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

    # 策略参数
    RUN_strategy = "GoldenCrossStrategy"
    FAST_PERIOD = 6
    SLOW_PERIOD = 20

    # 文件路径
    DATA_DIR = "data"
    STRATEGIES_DIR = "strategies"
    REPORTS_DIR = "reports"  # 新增报告目录
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    REPORT_FILENAME = f"{RUN_strategy}_{timestamp}.html"

    @classmethod
    def get_report_path(cls):
        return os.path.join(cls.REPORTS_DIR, cls.REPORT_FILENAME)