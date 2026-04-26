# utils/logger.py
import logging
import logging.handlers
import os
from datetime import datetime
from typing import Optional


class LoggerConfig:
    """日志配置类"""
    # 日志级别
    LOG_LEVEL = logging.INFO

    # 日志格式
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

    # 文件路径
    LOG_DIR = "logs"
    LOG_FILE = "backtest.log"

    # 文件大小限制 (10MB)
    MAX_BYTES = 10 * 1024 * 1024
    BACKUP_COUNT = 5  # 保留5个备份文件

    # 是否输出到控制台
    CONSOLE_OUTPUT = True

    @classmethod
    def get_log_path(cls):
        """获取完整日志路径"""
        os.makedirs(cls.LOG_DIR, exist_ok=True)
        return os.path.join(cls.LOG_DIR, cls.LOG_FILE)


def setup_logger(
        name: str = __name__,
        log_level: Optional[int] = None,
        log_file: Optional[str] = None,
        console_output: Optional[bool] = None
) -> logging.Logger:
    """
    设置并返回配置好的logger

    Args:
        name: logger名称，通常使用模块名(__name__)
        log_level: 日志级别，默认使用LoggerConfig.LOG_LEVEL
        log_file: 日志文件路径，默认使用LoggerConfig.get_log_path()
        console_output: 是否输出到控制台，默认使用LoggerConfig.CONSOLE_OUTPUT

    Returns:
        配置好的logger实例
    """
    # 使用配置或传入参数
    level = log_level if log_level is not None else LoggerConfig.LOG_LEVEL
    log_path = log_file if log_file is not None else LoggerConfig.get_log_path()
    console = console_output if console_output is not None else LoggerConfig.CONSOLE_OUTPUT

    # 创建logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 避免重复添加handler
    if logger.handlers:
        return logger

    # 创建formatter
    formatter = logging.Formatter(
        LoggerConfig.LOG_FORMAT,
        datefmt=LoggerConfig.DATE_FORMAT
    )

    # 文件处理器 - 按大小轮转
    file_handler = logging.handlers.RotatingFileHandler(
        log_path,
        maxBytes=LoggerConfig.MAX_BYTES,
        backupCount=LoggerConfig.BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # 控制台处理器
    if console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger


def get_performance_logger():
    """获取性能专用的logger - 不继承根logger的设置"""
    # 创建独立的logger，不继承root logger
    logger = logging.getLogger("performance")
    logger.setLevel(logging.INFO)
    logger.propagate = False  # 重要：不传播到父logger

    # 如果已经有handler，直接返回
    if logger.handlers:
        return logger

    # 性能日志使用单独的文件
    perf_file = os.path.join(LoggerConfig.LOG_DIR, "performance.log")

    # 确保目录存在
    os.makedirs(LoggerConfig.LOG_DIR, exist_ok=True)

    # 文件处理器
    file_handler = logging.handlers.RotatingFileHandler(
        perf_file,
        maxBytes=LoggerConfig.MAX_BYTES,
        backupCount=LoggerConfig.BACKUP_COUNT,
        encoding='utf-8'
    )

    # 性能日志格式（更简洁）
    formatter = logging.Formatter(
        '%(asctime)s - %(message)s',
        datefmt=LoggerConfig.DATE_FORMAT
    )
    file_handler.setFormatter(formatter)

    # 添加handler
    logger.addHandler(file_handler)

    return logger


def get_trade_logger():
    """获取交易专用的logger - 不继承根logger的设置"""
    # 创建独立的logger，不继承root logger
    logger = logging.getLogger("trading")
    logger.setLevel(logging.INFO)
    logger.propagate = False  # 重要：不传播到父logger

    # 如果已经有handler，直接返回
    if logger.handlers:
        return logger

    # 交易日志使用单独的文件
    trade_file = os.path.join(LoggerConfig.LOG_DIR, "trading.log")

    # 确保目录存在
    os.makedirs(LoggerConfig.LOG_DIR, exist_ok=True)

    # 文件处理器
    file_handler = logging.handlers.RotatingFileHandler(
        trade_file,
        maxBytes=LoggerConfig.MAX_BYTES,
        backupCount=LoggerConfig.BACKUP_COUNT,
        encoding='utf-8'
    )

    # 交易日志格式（CSV格式，便于分析）
    formatter = logging.Formatter(
        '%(asctime)s,%(message)s',
        datefmt=LoggerConfig.DATE_FORMAT
    )
    file_handler.setFormatter(formatter)

    # 添加handler
    logger.addHandler(file_handler)

    return logger


def get_optimize_logger():
    """获取优化策略专用的logger - 不继承根logger的设置"""
    # 创建独立的logger，不继承root logger
    logger = logging.getLogger("optimizing")
    logger.setLevel(logging.INFO)
    logger.propagate = False  # 重要：不传播到父logger

    # 如果已经有handler，直接返回
    if logger.handlers:
        return logger

    # 优化日志使用单独的文件
    optimize_file = os.path.join(LoggerConfig.LOG_DIR, "optimizing.log")

    # 确保目录存在
    os.makedirs(LoggerConfig.LOG_DIR, exist_ok=True)

    # 文件处理器
    file_handler = logging.handlers.RotatingFileHandler(
        optimize_file,
        maxBytes=LoggerConfig.MAX_BYTES,
        backupCount=LoggerConfig.BACKUP_COUNT,
        encoding='utf-8'
    )

    # 优化日志格式（CSV格式，便于分析）
    formatter = logging.Formatter(
        '%(asctime)s,%(message)s',
        datefmt=LoggerConfig.DATE_FORMAT
    )
    file_handler.setFormatter(formatter)

    # 添加handler
    logger.addHandler(file_handler)

    return logger


# 创建根logger
root_logger = setup_logger("backtest")