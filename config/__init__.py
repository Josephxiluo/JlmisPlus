"""
猫池短信系统配置模块 - tkinter版
Configuration module for SMS Pool System - tkinter version
"""

from .settings import Settings, settings
from .logging_config import setup_logging, get_logger, log_info, log_error, log_warning

__all__ = [
    # 设置管理
    'Settings',
    'settings',

    # 日志管理
    'setup_logging',
    'get_logger',
    'log_info',
    'log_error',
    'log_warning'
]

__version__ = '1.0.0'
__author__ = 'SMS Pool System Team'
__description__ = '猫池短信系统配置模块'