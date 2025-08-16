"""
猫池短信系统数据库模块 - tkinter版
Database module for SMS Pool System - tkinter version
"""

from .connection import (
    DatabaseConnectionWrapper,
    get_db_connection,
    execute_query,
    execute_update,
    execute_many,
    test_connection,
    close_database,
    init_database
)

__all__ = [
    # 核心数据库类
    'DatabaseConnectionWrapper',

    # 便捷函数
    'get_db_connection',
    'execute_query',
    'execute_update',
    'execute_many',

    # 管理函数
    'test_connection',
    'close_database',
    'init_database'
]

__version__ = '1.0.0'
__author__ = 'SMS Pool System Team'
__description__ = '猫池短信系统数据库连接管理模块'