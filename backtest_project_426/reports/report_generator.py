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

        qs.reports.html(
            self.returns,
            benchmark=self.benchmark_returns,
            output=report_path,
            title=f"{Config.RUN_strategy}{title}",
            benchmark_title="benchmark",
            download_filename=report_path
        )

        return report_path

    def open_in_browser(self, report_path):
        webbrowser.open(f'file://{os.path.abspath(report_path)}')

    @staticmethod
    def prepare_benchmark_data(benchmark_df, returns):
        """准备基准收益率数据"""
        benchmark_returns = benchmark_df['close'].pct_change().dropna()
        benchmark_returns.index = pd.to_datetime(benchmark_returns.index)

        if benchmark_returns.index.tz is not None:
            benchmark_returns.index = benchmark_returns.index.tz_localize(None)

        # 对齐索引
        benchmark_returns = benchmark_returns.reindex(
            returns.index,
            method='ffill'
        ).fillna(0)

        return benchmark_returns