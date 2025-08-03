"""
猫池短信系统日志配置 - tkinter版
Logging configuration for SMS Pool System - tkinter version
"""

import sys
import logging
import logging.handlers
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from loguru import logger
from .settings import settings


class LoggingConfig:
    """日志配置管理类"""

    def __init__(self):
        """初始化日志配置"""
        self.loggers: Dict[str, logging.Logger] = {}
        self.is_setup = False
        self.log_handlers = []

    def setup_loguru_logger(self) -> bool:
        """配置loguru日志器"""
        try:
            # 移除默认的处理器
            logger.remove()

            # 控制台输出（开发环境或配置启用）
            if settings.LOG_TO_CONSOLE or settings.is_development():
                logger.add(
                    sys.stderr,
                    format="<green>{time:HH:mm:ss}</green> | "
                           "<level>{level: <8}</level> | "
                           "<cyan>{name}</cyan>:<cyan>{line}</cyan> | "
                           "<level>{message}</level>",
                    level=settings.LOG_LEVEL,
                    colorize=True,
                    enqueue=True
                )

            # 应用日志文件
            logger.add(
                settings.get_log_file_path('app'),
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{line} | {message}",
                level=settings.LOG_LEVEL,
                rotation=f"{settings.LOG_MAX_SIZE // (1024*1024)}MB",
                retention=f"{settings.LOG_BACKUP_COUNT} files",
                compression="zip",
                encoding="utf-8",
                enqueue=True
            )

            # 错误日志文件
            logger.add(
                settings.get_log_file_path('error'),
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{line} | {message}",
                level="ERROR",
                rotation=f"{settings.LOG_MAX_SIZE // (1024*1024)}MB",
                retention=f"{settings.LOG_BACKUP_COUNT} files",
                compression="zip",
                encoding="utf-8",
                enqueue=True
            )

            # 任务日志文件
            logger.add(
                settings.get_log_file_path('task'),
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{line} | {message}",
                level="INFO",
                rotation=f"{settings.LOG_MAX_SIZE // (1024*1024)}MB",
                retention=f"{settings.LOG_BACKUP_COUNT} files",
                compression="zip",
                encoding="utf-8",
                filter=lambda record: self._is_task_log(record),
                enqueue=True
            )

            # 端口日志文件
            logger.add(
                settings.get_log_file_path('port'),
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{line} | {message}",
                level="INFO",
                rotation=f"{settings.LOG_MAX_SIZE // (1024*1024)}MB",
                retention=f"{settings.LOG_BACKUP_COUNT} files",
                compression="zip",
                encoding="utf-8",
                filter=lambda record: self._is_port_log(record),
                enqueue=True
            )

            # 数据库日志文件（仅在SQL调试模式开启）
            if settings.SQL_DEBUG:
                logger.add(
                    settings.get_log_file_path('database'),
                    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{line} | {message}",
                    level="DEBUG",
                    rotation=f"{settings.LOG_MAX_SIZE // (1024*1024)}MB",
                    retention=f"{settings.LOG_BACKUP_COUNT} files",
                    compression="zip",
                    encoding="utf-8",
                    filter=lambda record: self._is_database_log(record),
                    enqueue=True
                )

            self.is_setup = True
            return True

        except Exception as e:
            print(f"Loguru日志系统初始化失败: {e}")
            return False

    def _is_task_log(self, record) -> bool:
        """判断是否为任务相关日志"""
        keywords = ["task", "任务", "发送", "send", "message"]
        return any(keyword in record["name"].lower() or keyword in record["message"].lower()
                  for keyword in keywords)

    def _is_port_log(self, record) -> bool:
        """判断是否为端口相关日志"""
        keywords = ["port", "端口", "serial", "串口", "device", "设备", "com"]
        return any(keyword in record["name"].lower() or keyword in record["message"].lower()
                  for keyword in keywords)

    def _is_database_log(self, record) -> bool:
        """判断是否为数据库相关日志"""
        keywords = ["database", "数据库", "sql", "dao", "query", "查询"]
        return any(keyword in record["name"].lower() or keyword in record["message"].lower()
                  for keyword in keywords)

    def setup_standard_logger(self) -> bool:
        """配置标准Python日志器（备用方案）"""
        try:
            # 创建根日志器
            root_logger = logging.getLogger('sms_pool')
            root_logger.setLevel(getattr(logging, settings.LOG_LEVEL))
            root_logger.handlers.clear()

            # 创建格式器
            formatter = logging.Formatter(
                fmt='%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )

            # 控制台处理器
            if settings.LOG_TO_CONSOLE or settings.is_development():
                console_handler = logging.StreamHandler(sys.stdout)
                console_handler.setLevel(getattr(logging, settings.LOG_LEVEL))
                console_handler.setFormatter(formatter)
                root_logger.addHandler(console_handler)
                self.log_handlers.append(console_handler)

            # 文件处理器
            file_handler = logging.handlers.RotatingFileHandler(
                filename=settings.get_log_file_path('app'),
                maxBytes=settings.LOG_MAX_SIZE,
                backupCount=settings.LOG_BACKUP_COUNT,
                encoding='utf-8'
            )
            file_handler.setLevel(getattr(logging, settings.LOG_LEVEL))
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
            self.log_handlers.append(file_handler)

            # 错误文件处理器
            error_handler = logging.handlers.RotatingFileHandler(
                filename=settings.get_log_file_path('error'),
                maxBytes=settings.LOG_MAX_SIZE,
                backupCount=settings.LOG_BACKUP_COUNT,
                encoding='utf-8'
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(formatter)
            root_logger.addHandler(error_handler)
            self.log_handlers.append(error_handler)

            self.loggers['root'] = root_logger
            self.is_setup = True
            return True

        except Exception as e:
            print(f"标准日志系统初始化失败: {e}")
            return False

    def log_system_info(self):
        """记录系统信息"""
        try:
            logger.info("=" * 60)
            logger.info(f"应用启动: {settings.APP_NAME} v{settings.APP_VERSION}")
            logger.info(f"运行环境: {settings.APP_ENV}")
            logger.info(f"调试模式: {settings.DEBUG}")
            logger.info(f"日志级别: {settings.LOG_LEVEL}")
            logger.info(f"数据库: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
            logger.info(f"UI框架: tkinter")
            logger.info(f"窗口大小: {settings.WINDOW_DEFAULT_WIDTH}x{settings.WINDOW_DEFAULT_HEIGHT}")
            logger.info("=" * 60)
        except Exception as e:
            print(f"记录系统信息失败: {e}")

    def log_application_start(self):
        """记录应用启动信息"""
        try:
            import platform
            import psutil

            logger.info("系统环境信息:")
            logger.info(f"  操作系统: {platform.system()} {platform.release()}")
            logger.info(f"  Python版本: {platform.python_version()}")
            logger.info(f"  CPU核心数: {psutil.cpu_count()}")
            logger.info(f"  内存大小: {psutil.virtual_memory().total // (1024**3)}GB")
            logger.info(f"  工作目录: {settings.BASE_DIR}")

            # tkinter环境检查
            try:
                import tkinter as tk
                root = tk.Tk()
                logger.info(f"  屏幕分辨率: {root.winfo_screenwidth()}x{root.winfo_screenheight()}")
                logger.info(f"  tkinter版本: {tk.TkVersion}")
                root.destroy()
            except Exception as e:
                logger.warning(f"  tkinter环境检查失败: {e}")

        except Exception as e:
            logger.warning(f"获取系统环境信息失败: {e}")

    def get_log_stats(self) -> Dict[str, Any]:
        """获取日志统计信息"""
        stats = {
            'log_dir': str(settings.LOGS_DIR),
            'log_level': settings.LOG_LEVEL,
            'files': []
        }

        try:
            for log_file in settings.LOGS_DIR.glob("*.log"):
                if log_file.is_file():
                    file_stats = log_file.stat()
                    stats['files'].append({
                        'name': log_file.name,
                        'size': file_stats.st_size,
                        'size_mb': round(file_stats.st_size / (1024*1024), 2),
                        'modified': datetime.fromtimestamp(file_stats.st_mtime).isoformat()
                    })
        except Exception as e:
            logger.error(f"获取日志统计信息失败: {e}")

        return stats


def setup_logging() -> LoggingConfig:
    """设置日志系统"""
    logging_config = LoggingConfig()

    # 优先使用loguru
    if logging_config.setup_loguru_logger():
        logger.info("Loguru日志系统初始化成功")
    else:
        # 备用标准日志系统
        if logging_config.setup_standard_logger():
            logger.info("标准日志系统初始化成功")
        else:
            print("所有日志系统初始化失败，使用基本输出")
            return logging_config

    # 记录系统信息
    logging_config.log_system_info()
    logging_config.log_application_start()

    return logging_config


def get_logger(name: str = None):
    """获取日志器（便捷函数）"""
    if name:
        return logger.bind(name=name)
    return logger


# 便捷的日志记录函数
def log_info(message: str, **kwargs):
    """记录信息日志"""
    logger.info(message, **kwargs)


def log_warning(message: str, **kwargs):
    """记录警告日志"""
    logger.warning(message, **kwargs)


def log_error(message: str, error: Exception = None, **kwargs):
    """记录错误日志"""
    if error:
        logger.error(f"{message}: {str(error)}", **kwargs)
    else:
        logger.error(message, **kwargs)


def log_debug(message: str, **kwargs):
    """记录调试日志"""
    logger.debug(message, **kwargs)


def log_success(message: str, **kwargs):
    """记录成功日志"""
    logger.success(message, **kwargs)


# 特定业务日志函数
def log_user_action(username: str, action: str, details: str = None, success: bool = True):
    """记录用户操作"""
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
    message = f"[任务操作] ID={task_id} 名称={task_name} 操作={action}"
    if details:
        message += f" - {details}"
    logger.info(message)


def log_port_action(port_name: str, action: str, details: str = None, success: bool = True):
    """记录端口操作"""
    status = "成功" if success else "失败"
    message = f"[端口操作] {port_name} {action} {status}"
    if details:
        message += f" - {details}"

    if success:
        logger.info(message)
    else:
        logger.warning(message)


def log_message_send(task_id: int, recipient: str, port: str, status: str, details: str = None):
    """记录消息发送"""
    message = f"[消息发送] 任务ID={task_id} 接收号码={recipient} 端口={port} 状态={status}"
    if details:
        message += f" - {details}"

    if status == 'success':
        logger.info(message)
    elif status in ['failed', 'timeout']:
        logger.warning(message)
    else:
        logger.debug(message)


def log_auth_action(username: str, action: str, success: bool, details: str = None):
    """记录认证操作"""
    status = "成功" if success else "失败"
    message = f"[用户认证] {username} {action} {status}"
    if details:
        message += f" - {details}"

    if success:
        logger.info(message)
    else:
        logger.warning(message)


def log_database_action(action: str, table: str = None, details: str = None, success: bool = True):
    """记录数据库操作"""
    status = "成功" if success else "失败"
    message = f"[数据库操作] {action} {status}"
    if table:
        message += f" 表={table}"
    if details:
        message += f" - {details}"

    if success:
        logger.debug(message) if settings.SQL_DEBUG else logger.info(message)
    else:
        logger.error(message)


def log_ui_action(window: str, action: str, details: str = None):
    """记录UI操作"""
    message = f"[界面操作] {window} {action}"
    if details:
        message += f" - {details}"
    logger.debug(message)


def log_file_action(action: str, filename: str, details: str = None, success: bool = True):
    """记录文件操作"""
    status = "成功" if success else "失败"
    message = f"[文件操作] {action} 文件={filename} {status}"
    if details:
        message += f" - {details}"

    if success:
        logger.info(message)
    else:
        logger.error(message)


def log_performance(operation: str, duration: float, details: str = None):
    """记录性能信息"""
    message = f"[性能监控] {operation} 耗时={duration:.3f}s"
    if details:
        message += f" - {details}"

    # 根据耗时判断日志级别
    if duration > 5.0:
        logger.warning(message)
    elif duration > 2.0:
        logger.info(message)
    else:
        logger.debug(message)


def log_timer_action(timer_name: str, action: str, interval: int = None):
    """记录定时器操作"""
    message = f"[定时器] {timer_name} {action}"
    if interval:
        message += f" 间隔={interval}秒"
    logger.debug(message)


def log_credit_action(user_id: int, action: str, amount: int, balance: int, details: str = None):
    """记录积分操作"""
    message = f"[积分操作] 用户ID={user_id} {action} 金额={amount} 余额={balance}"
    if details:
        message += f" - {details}"
    logger.info(message)


def log_config_action(action: str, key: str = None, value: Any = None, success: bool = True):
    """记录配置操作"""
    status = "成功" if success else "失败"
    message = f"[配置操作] {action} {status}"
    if key:
        message += f" 配置项={key}"
    if value is not None:
        message += f" 值={value}"

    if success:
        logger.info(message)
    else:
        logger.error(message)


# 异常处理装饰器
def log_exception(func):
    """日志异常装饰器"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            log_error(f"函数 {func.__name__} 执行异常", error=e)
            raise
    return wrapper


# 全局日志配置实例
_logging_config = None


def get_logging_config() -> LoggingConfig:
    """获取日志配置实例"""
    global _logging_config
    if _logging_config is None:
        _logging_config = setup_logging()
    return _logging_config


def cleanup_old_logs(days: int = 30):
    """清理旧日志文件"""
    try:
        import time
        current_time = time.time()
        retention_seconds = days * 24 * 3600

        for log_file in settings.LOGS_DIR.glob("*.log*"):
            if log_file.stat().st_mtime < current_time - retention_seconds:
                log_file.unlink()
                logger.info(f"清理旧日志文件: {log_file}")
    except Exception as e:
        logger.error(f"清理日志文件失败: {e}")