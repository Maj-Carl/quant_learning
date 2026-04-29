# reports/report_generator.py
import quantstats as qs
import webbrowser
import os
from config.config import Config
import pandas as pd

class ReportGenerator:
    def __init__(self, returns, benchmark_returns=None):
        self.returns = returns
        self.benchmark_returns = benchmark_returns
        os.makedirs(Config.REPORTS_DIR, exist_ok=True)

    def generate_html_report(self, title='回测报告'):
        report_path = Config.get_report_path()

        # QuantStats 的 html() 即使设置 match_dates=False，也会在内部 metrics()
        # 使用默认 match_dates=True，导致基准再次被截断到策略首个非零收益日。
        # 这里临时包裹 metrics，确保整份报告都按完整日期区间评估。
        original_metrics = qs.reports.metrics

        def _metrics_without_date_matching(*args, **kwargs):
            kwargs["match_dates"] = False
            return original_metrics(*args, **kwargs)

        qs.reports.metrics = _metrics_without_date_matching
        try:
            qs.reports.html(
                self.returns,
                benchmark=self.benchmark_returns,
                output=report_path,
                title=f"{Config.get_strategy_name()}{title}",
                benchmark_title="benchmark",
                download_filename=report_path,
                match_dates=False,
            )
        finally:
            qs.reports.metrics = original_metrics

        return report_path

    def open_in_browser(self, report_path):
        webbrowser.open(f'file://{os.path.abspath(report_path)}')

    @staticmethod
    def prepare_benchmark_data(benchmark_df):
        """准备基准收益率数据（使用数据源完整区间）"""
        benchmark_returns = benchmark_df['close'].pct_change().dropna()
        benchmark_returns.index = pd.to_datetime(benchmark_returns.index)

        if benchmark_returns.index.tz is not None:
            benchmark_returns.index = benchmark_returns.index.tz_localize(None)

        return benchmark_returns

    @staticmethod
    def align_strategy_returns_to_benchmark(returns, benchmark_returns):
        """将策略收益对齐到基准时间轴，缺失交易日按0收益处理。"""
        aligned_returns = returns.reindex(benchmark_returns.index).fillna(0)
        return aligned_returns