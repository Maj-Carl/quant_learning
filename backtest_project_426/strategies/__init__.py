# strategies/__init__.py
# 策略包初始化文件
from .ma_strategy import GoldenCrossStrategy
from .rsi_strategy import RSIStrategy

__all__ = ['GoldenCrossStrategy', 'RSIStrategy']