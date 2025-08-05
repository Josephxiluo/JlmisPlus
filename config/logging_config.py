"""
猫池短信系统日志配置 - tkinter版 (简化版)
Logging configuration for SMS Pool System - tkinter version (Simplified)
"""

import sys
import logging
import logging.handlers
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


class LoggingConfig:
    """日志配置管理类"""

    def __init__(self):
        """初始化日志配置"""
        self.loggers: Dict[str, logging.Logger] = {}
        self.is_setup = False
        self.log_handlers = []

        # 延迟导入设置，避免循环导入
        self.settings = None

    def _get_settings(self):
        """获取设置对象"""
        if self.settings is None:
            try:
                from .settings import settings
                self.settings = settings
            except ImportError:
                # 使用默认设置
                self.settings = self._get_default_settings()
        return self.settings

    def _get_default_settings(self):
        """获取默认设置"""
        class DefaultSettings:
            BASE_DIR = Path(__file__).parent.parent
            LOGS_DIR = BASE_DIR / 'temp' / 'logs'
            LOG_LEVEL = 'INFO'
            LOG_MAX_SIZE = 50 * 1024 * 1024  # 50MB
            LOG_BACKUP_COUNT = 3
            LOG_TO_CONSOLE = True
            SQL_DEBUG = False
            DEBUG = False
            APP_NAME = '猫池短信系统'
            APP_VERSION = '1.0.0'
            APP_ENV = 'development'

            def is_development(self):
                return True

        return DefaultSettings()

    def setup_logging(self) -> bool:
        """配置日志系统"""
        try:
            settings = self._get_settings()

            # 确保日志目录存在
            settings.LOGS_DIR.mkdir(parents=True, exist_ok=True)

            # 创建根日志器
            root_logger = logging.getLogger('sms_pool')
            root_logger.setLevel(getattr(logging, settings.LOG_LEVEL, logging.INFO))
            root_logger.handlers.clear()

            # 创建格式器
            formatter = logging.Formatter(
                fmt='%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )

            # 控制台处理器
            if settings.LOG_TO_CONSOLE or settings.is_development():
                console_handler = logging.StreamHandler(sys.stdout)
                console_handler.setLevel(getattr(logging, settings.LOG_LEVEL, logging.INFO))
                console_handler.setFormatter(formatter)
                root_logger.addHandler(console_handler)
                self.log_handlers.append(console_handler)

            # 应用日志文件处理器
            app_file_handler = logging.handlers.RotatingFileHandler(
                filename=settings.LOGS_DIR / 'app.log',
                maxBytes=settings.LOG_MAX_SIZE,
                backupCount=settings.LOG_BACKUP_COUNT,
                encoding='utf-8'
            )
            app_file_handler.setLevel(getattr(logging, settings.LOG_LEVEL, logging.INFO))
            app_file_handler.setFormatter(formatter)
            root_logger.addHandler(app_file_handler)
            self.log_handlers.append(app_file_handler)

            # 错误日志文件处理器
            error_handler = logging.handlers.RotatingFileHandler(
                filename=settings.LOGS_DIR / 'error.log',
                maxBytes=settings.LOG_MAX_SIZE,
                backupCount=settings.LOG_BACKUP_COUNT,
                encoding='utf-8'
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(formatter)
            root_logger.addHandler(error_handler)
            self.log_handlers.append(error_handler)

            # 任务日志文件处理器
            task_handler = logging.handlers.RotatingFileHandler(
                filename=settings.LOGS_DIR / 'task.log',
                maxBytes=settings.LOG_MAX_SIZE,
                backupCount=settings.LOG_BACKUP_COUNT,
                encoding='utf-8'
            )
            task_handler.setLevel(logging.INFO)
            task_handler.setFormatter(formatter)
            task_handler.addFilter(self._create_task_filter())
            root_logger.addHandler(task_handler)
            self.log_handlers.append(task_handler)

            # 端口日志文件处理器
            port_handler = logging.handlers.RotatingFileHandler(
                filename=settings.LOGS_DIR / 'port.log',
                maxBytes=settings.LOG_MAX_SIZE,
                backupCount=settings.LOG_BACKUP_COUNT,
                encoding='utf-8'
            )
            port_handler.setLevel(logging.INFO)
            port_handler.setFormatter(formatter)
            port_handler.addFilter(self._create_port_filter())
            root_logger.addHandler(port_handler)
            self.log_handlers.append(port_handler)

            self.loggers['root'] = root_logger
            self.is_setup = True

            # 记录系统信息
            self._log_system_info()

            return True

        except Exception as e:
            print(f"日志系统初始化失败: {e}")
            return False

    def _create_task_filter(self):
        """创建任务日志过滤器"""
        def task_filter(record):
            keywords = ["task", "任务", "发送", "send", "message"]
            return any(keyword in record.name.lower() or keyword in record.getMessage().lower()
                      for keyword in keywords)
        return task_filter

    def _create_port_filter(self):
        """创建端口日志过滤器"""
        def port_filter(record):
            keywords = ["port", "端口", "serial", "串口", "device", "设备", "com"]
            return any(keyword in record.name.lower() or keyword in record.getMessage().lower()
                      for keyword in keywords)
        return port_filter

    def _log_system_info(self):
        """记录系统信息"""
        try:
            settings = self._get_settings()
            root_logger = self.loggers.get('root')
            if root_logger:
                root_logger.info("=" * 60)
                root_logger.info(f"应用启动: {settings.APP_NAME} v{settings.APP_VERSION}")
                root_logger.info(f"运行环境: {settings.APP_ENV}")
                root_logger.info(f"调试模式: {settings.DEBUG}")
                root_logger.info(f"日志级别: {settings.LOG_LEVEL}")
                root_logger.info(f"UI框架: tkinter")
                root_logger.info("=" * 60)

                # 系统环境信息
                try:
                    import platform
                    root_logger.info("系统环境信息:")
                    root_logger.info(f"  操作系统: {platform.system()} {platform.release()}")
                    root_logger.info(f"  Python版本: {platform.python_version()}")
                    root_logger.info(f"  工作目录: {settings.BASE_DIR}")
                except Exception as e:
                    root_logger.warning(f"获取系统环境信息失败: {e}")

        except Exception as e:
            print(f"记录系统信息失败: {e}")

    def get_logger(self, name: str = None) -> logging.Logger:
        """获取日志器"""
        if not self.is_setup:
            self.setup_logging()

        if name:
            logger = logging.getLogger(f'sms_pool.{name}')
        else:
            logger = logging.getLogger('sms_pool')

        return logger

    def close_handlers(self):
        """关闭所有日志处理器"""
        for handler in self.log_handlers:
            try:
                handler.close()
            except:
                pass
        self.log_handlers.clear()


# 全局日志配置实例
_logging_config = None


def setup_logging() -> LoggingConfig:
    """设置日志系统"""
    global _logging_config
    if _logging_config is None:
        _logging_config = LoggingConfig()
        _logging_config.setup_logging()
    return _logging_config


def get_logger(name: str = None) -> logging.Logger:
    """获取日志器（便捷函数）"""
    global _logging_config
    if _logging_config is None:
        _logging_config = setup_logging()
    return _logging_config.get_logger(name)


# 便捷的日志记录函数
def log_info(message: str, logger_name: str = None):
    """记录信息日志"""
    logger = get_logger(logger_name)
    logger.info(message)


def log_warning(message: str, logger_name: str = None):
    """记录警告日志"""
    logger = get_logger(logger_name)
    logger.warning(message)


def log_error(message: str, error: Exception = None, logger_name: str = None):
    """记录错误日志"""
    logger = get_logger(logger_name)
    if error:
        logger.error(f"{message}: {str(error)}")
    else:
        logger.error(message)


def log_debug(message: str, logger_name: str = None):
    """记录调试日志"""
    logger = get_logger(logger_name)
    logger.debug(message)


# 特定业务日志函数
def log_user_action(username: str, action: str, details: str = None, success: bool = True):
    """记录用户操作"""
    logger = get_logger('user')
    status = "成功" if success else "失败"
    message = f"[用户操作] {username} {action} {status}"
    if details:
        message += f" - {details}"

    if success:
        logger.info(message)
    else:
        logger.warning(message)


def log_task_action(task_id: int, task_name: str, action: str, details: str = None):
    """记录任务操作"""
    logger = get_logger('task')
    message = f"[任务操作] ID={task_id} 名称={task_name} 操作={action}"
    if details:
        message += f" - {details}"
    logger.info(message)


def log_port_action(port_name: str, action: str, details: str = None, success: bool = True):
    """记录端口操作"""
    logger = get_logger('port')
    status = "成功" if success else "失败"
    message = f"[端口操作] {port_name} {action} {status}"
    if details:
        message += f" - {details}"

    if success:
        logger.info(message)
    else:
        logger.warning(message)


def log_database_action(action: str, table: str = None, details: str = None, success: bool = True):
    """记录数据库操作"""
    logger = get_logger('database')
    status = "成功" if success else "失败"
    message = f"[数据库操作] {action} {status}"
    if table:
        message += f" 表={table}"
    if details:
        message += f" - {details}"

    if success:
        logger.info(message)
    else:
        logger.error(message)


def cleanup_logging():
    """清理日志系统"""
    global _logging_config
    if _logging_config:
        _logging_config.close_handlers()
        _logging_config = None