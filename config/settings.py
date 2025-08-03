"""
猫池短信系统基础设置管理 - tkinter版
Settings management for SMS Pool System - tkinter version
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Tuple
from dotenv import load_dotenv


class Settings:
    """系统设置管理类"""

    def __init__(self):
        """初始化设置"""
        # 获取项目根目录
        self.BASE_DIR = Path(__file__).resolve().parent.parent

        # 加载环境变量
        env_path = self.BASE_DIR / '.env'
        if env_path.exists():
            load_dotenv(env_path)

        # 初始化各项配置
        self._init_app_config()
        self._init_database_config()
        self._init_auth_config()
        self._init_sms_config()
        self._init_port_config()
        self._init_file_config()
        self._init_log_config()
        self._init_ui_config()
        self._init_timer_config()
        self._init_task_config()
        self._init_performance_config()
        self._init_security_config()
        self._init_export_config()

        # 确保目录存在
        self._ensure_directories()

    def _init_app_config(self):
        """应用基础配置"""
        self.APP_NAME = os.getenv('APP_NAME', '猫池短信系统')
        self.APP_VERSION = os.getenv('APP_VERSION', '1.0.0')
        self.APP_ENV = os.getenv('APP_ENV', 'development')
        self.DEBUG = os.getenv('DEBUG', 'true').lower() == 'true'

        # 路径配置
        self.TEMP_DIR = self.BASE_DIR / 'temp'
        self.LOGS_DIR = self.TEMP_DIR / 'logs'
        self.UPLOADS_DIR = self.TEMP_DIR / 'uploads'
        self.EXPORTS_DIR = self.TEMP_DIR / 'exports'
        self.CACHE_DIR = self.TEMP_DIR / 'cache'
        self.STATIC_DIR = self.BASE_DIR / 'static'
        self.ICONS_DIR = self.STATIC_DIR / 'icons'

    def _init_database_config(self):
        """数据库配置"""
        self.DB_HOST = os.getenv('DB_HOST', 'localhost')
        self.DB_PORT = int(os.getenv('DB_PORT', '5432'))
        self.DB_NAME = os.getenv('DB_NAME', 'sms_pool_system')
        self.DB_USER = os.getenv('DB_USER', 'postgres')
        self.DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')
        self.DB_CHARSET = os.getenv('DB_CHARSET', 'utf8')

        # 连接池配置
        self.DB_POOL_SIZE = int(os.getenv('DB_POOL_SIZE', '5'))
        self.DB_POOL_TIMEOUT = int(os.getenv('DB_POOL_TIMEOUT', '30'))
        self.CONNECTION_RETRY_COUNT = int(os.getenv('CONNECTION_RETRY_COUNT', '3'))

    def _init_auth_config(self):
        """认证配置"""
        self.PASSWORD_SALT = os.getenv('PASSWORD_SALT', 'sms_pool_salt_2024')
        self.MAC_VERIFICATION = os.getenv('MAC_VERIFICATION', 'true').lower() == 'true'
        self.AUTO_LOGIN = os.getenv('AUTO_LOGIN', 'false').lower() == 'true'
        self.SESSION_TIMEOUT = int(os.getenv('SESSION_TIMEOUT', '28800'))  # 8小时
        self.MAX_LOGIN_ATTEMPTS = int(os.getenv('MAX_LOGIN_ATTEMPTS', '5'))
        self.LOGIN_LOCKOUT_TIME = int(os.getenv('LOGIN_LOCKOUT_TIME', '15'))  # 分钟
        self.MIN_PASSWORD_LENGTH = int(os.getenv('MIN_PASSWORD_LENGTH', '6'))

        # 开发模式配置
        self.SKIP_MAC_VERIFICATION = os.getenv('SKIP_MAC_VERIFICATION', 'false').lower() == 'true'

    def _init_sms_config(self):
        """短信发送配置"""
        self.DEFAULT_SEND_INTERVAL = int(os.getenv('DEFAULT_SEND_INTERVAL', '1000'))  # 毫秒
        self.DEFAULT_RETRY_COUNT = int(os.getenv('DEFAULT_RETRY_COUNT', '3'))
        self.DEFAULT_TIMEOUT = int(os.getenv('DEFAULT_TIMEOUT', '30'))  # 秒
        self.MAX_CONCURRENT_TASKS = int(os.getenv('MAX_CONCURRENT_TASKS', '3'))
        self.SMS_RATE = float(os.getenv('SMS_RATE', '1.0'))  # 短信费率
        self.MMS_RATE = float(os.getenv('MMS_RATE', '3.0'))  # 彩信费率

        # 发送控制配置
        self.CARD_SWITCH_INTERVAL = int(os.getenv('CARD_SWITCH_INTERVAL', '60'))  # 卡片更换间隔
        self.MONITOR_ALERT_INTERVAL = int(os.getenv('MONITOR_ALERT_INTERVAL', '1000'))  # 监测提醒间隔
        self.DEFAULT_MONITOR_PHONE = os.getenv('DEFAULT_MONITOR_PHONE', '')  # 默认监测号码

    def _init_port_config(self):
        """端口管理配置"""
        self.PORT_SCAN_TIMEOUT = int(os.getenv('PORT_SCAN_TIMEOUT', '5'))
        self.PORT_CHECK_INTERVAL = int(os.getenv('PORT_CHECK_INTERVAL', '10'))
        self.AUTO_PORT_SCAN = os.getenv('AUTO_PORT_SCAN', 'true').lower() == 'true'

        # 串口通信参数
        self.PORT_BAUD_RATE = int(os.getenv('PORT_BAUD_RATE', '115200'))
        self.PORT_DATA_BITS = int(os.getenv('PORT_DATA_BITS', '8'))
        self.PORT_STOP_BITS = int(os.getenv('PORT_STOP_BITS', '1'))
        self.PORT_PARITY = os.getenv('PORT_PARITY', 'N')  # N, E, O

    def _init_file_config(self):
        """文件处理配置"""
        self.MAX_UPLOAD_SIZE = int(os.getenv('MAX_UPLOAD_SIZE', '10')) * 1024 * 1024  # MB转字节
        self.SUPPORTED_FILE_FORMATS = os.getenv('SUPPORTED_FILE_FORMATS', 'xlsx,xls,csv,txt').split(',')
        self.MAX_PHONE_COUNT = int(os.getenv('MAX_PHONE_COUNT', '10000'))  # 单次最大号码数

    def _init_log_config(self):
        """日志配置"""
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
        self.LOG_MAX_SIZE = int(os.getenv('LOG_MAX_SIZE', '50')) * 1024 * 1024  # MB转字节
        self.LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', '3'))
        self.LOG_TO_CONSOLE = os.getenv('LOG_TO_CONSOLE', 'true').lower() == 'true'
        self.SQL_DEBUG = os.getenv('SQL_DEBUG', 'false').lower() == 'true'

    def _init_ui_config(self):
        """tkinter UI配置"""
        self.UI_THEME = os.getenv('UI_THEME', 'orange')

        # 窗口配置
        self.WINDOW_DEFAULT_WIDTH = int(os.getenv('WINDOW_DEFAULT_WIDTH', '1200'))
        self.WINDOW_DEFAULT_HEIGHT = int(os.getenv('WINDOW_DEFAULT_HEIGHT', '800'))
        self.WINDOW_MIN_WIDTH = int(os.getenv('WINDOW_MIN_WIDTH', '800'))
        self.WINDOW_MIN_HEIGHT = int(os.getenv('WINDOW_MIN_HEIGHT', '600'))
        self.WINDOW_RESIZABLE = os.getenv('WINDOW_RESIZABLE', 'true').lower() == 'true'
        self.WINDOW_FULLSCREEN = os.getenv('WINDOW_FULLSCREEN', 'false').lower() == 'true'
        self.WINDOW_CENTER = os.getenv('WINDOW_CENTER', 'true').lower() == 'true'

        # UI颜色配置（橙色主题）
        self.UI_COLORS = {
            'primary': '#FF8C00',      # 深橙色
            'primary_light': '#FFA500', # 橙色
            'primary_dark': '#FF6600',  # 深橙红
            'secondary': '#F0F0F0',     # 浅灰色
            'background': '#FFFFFF',    # 白色
            'text': '#333333',          # 深灰色文字
            'text_light': '#666666',    # 浅灰色文字
            'success': '#28A745',       # 绿色
            'warning': '#FFC107',       # 黄色
            'danger': '#DC3545',        # 红色
            'info': '#17A2B8'          # 蓝色
        }

        # UI字体配置
        self.UI_FONTS = {
            'default': ('Microsoft YaHei', 9),
            'title': ('Microsoft YaHei', 12, 'bold'),
            'button': ('Microsoft YaHei', 9),
            'label': ('Microsoft YaHei', 9),
            'small': ('Microsoft YaHei', 8)
        }

    def _init_timer_config(self):
        """定时器配置"""
        self.CREDIT_REFRESH_INTERVAL = int(os.getenv('CREDIT_REFRESH_INTERVAL', '300'))  # 5分钟
        self.PORT_STATUS_INTERVAL = int(os.getenv('PORT_STATUS_INTERVAL', '5'))  # 5秒
        self.TASK_PROGRESS_INTERVAL = int(os.getenv('TASK_PROGRESS_INTERVAL', '2'))  # 2秒

    def _init_task_config(self):
        """任务管理配置"""
        self.TASK_PAGE_SIZE = int(os.getenv('TASK_PAGE_SIZE', '20'))
        self.MESSAGE_PAGE_SIZE = int(os.getenv('MESSAGE_PAGE_SIZE', '50'))
        self.TASK_AUTO_CLEANUP_DAYS = int(os.getenv('TASK_AUTO_CLEANUP_DAYS', '30'))

    def _init_performance_config(self):
        """性能监控配置"""
        self.PERFORMANCE_MONITORING = os.getenv('PERFORMANCE_MONITORING', 'true').lower() == 'true'
        self.MEMORY_WARNING_THRESHOLD = int(os.getenv('MEMORY_WARNING_THRESHOLD', '500'))  # MB
        self.CPU_WARNING_THRESHOLD = int(os.getenv('CPU_WARNING_THRESHOLD', '80'))  # %
        self.CACHE_EXPIRE_TIME = int(os.getenv('CACHE_EXPIRE_TIME', '24'))  # 小时

    def _init_security_config(self):
        """安全配置"""
        self.REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '30'))
        self.HTTP_PROXY = os.getenv('HTTP_PROXY')
        self.HTTPS_PROXY = os.getenv('HTTPS_PROXY')

        # 开发模式配置
        self.SIMULATION_MODE = os.getenv('SIMULATION_MODE', 'false').lower() == 'true'
        self.TEST_DB_NAME = os.getenv('TEST_DB_NAME', 'sms_pool_test')

    def _init_export_config(self):
        """导出配置"""
        self.DEFAULT_EXPORT_FORMAT = os.getenv('DEFAULT_EXPORT_FORMAT', 'xlsx')
        self.EXPORT_DIR = self.BASE_DIR / os.getenv('EXPORT_DIR', 'temp/exports')
        self.EXPORT_FILENAME_TEMPLATE = os.getenv('EXPORT_FILENAME_TEMPLATE', '{task_name}_{status}_{timestamp}')

    def _ensure_directories(self):
        """确保必要的目录存在"""
        directories = [
            self.TEMP_DIR,
            self.LOGS_DIR,
            self.UPLOADS_DIR,
            self.EXPORTS_DIR,
            self.CACHE_DIR
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def get_database_url(self) -> str:
        """获取数据库连接URL"""
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    def get_log_file_path(self, log_type: str = 'app') -> Path:
        """获取日志文件路径"""
        return self.LOGS_DIR / f"{log_type}.log"

    def get_icon_path(self, icon_name: str) -> Path:
        """获取图标文件路径"""
        return self.ICONS_DIR / f"{icon_name}.png"

    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.APP_ENV.lower() == 'development'

    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.APP_ENV.lower() == 'production'

    def get_window_geometry(self) -> str:
        """获取窗口几何配置"""
        return f"{self.WINDOW_DEFAULT_WIDTH}x{self.WINDOW_DEFAULT_HEIGHT}"

    def get_window_center_position(self) -> Tuple[int, int]:
        """获取窗口居中位置"""
        import tkinter as tk

        # 获取屏幕尺寸
        root = tk.Tk()
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        root.destroy()

        # 计算居中位置
        x = (screen_width - self.WINDOW_DEFAULT_WIDTH) // 2
        y = (screen_height - self.WINDOW_DEFAULT_HEIGHT) // 2

        return x, y

    def get_send_config(self) -> Dict[str, Any]:
        """获取发送配置"""
        return {
            'send_interval': self.DEFAULT_SEND_INTERVAL,
            'retry_count': self.DEFAULT_RETRY_COUNT,
            'timeout': self.DEFAULT_TIMEOUT,
            'max_concurrent': self.MAX_CONCURRENT_TASKS,
            'card_switch_interval': self.CARD_SWITCH_INTERVAL,
            'monitor_alert_interval': self.MONITOR_ALERT_INTERVAL,
            'default_monitor_phone': self.DEFAULT_MONITOR_PHONE
        }

    def get_port_config(self) -> Dict[str, Any]:
        """获取端口配置"""
        return {
            'scan_timeout': self.PORT_SCAN_TIMEOUT,
            'check_interval': self.PORT_CHECK_INTERVAL,
            'auto_scan': self.AUTO_PORT_SCAN,
            'baud_rate': self.PORT_BAUD_RATE,
            'data_bits': self.PORT_DATA_BITS,
            'stop_bits': self.PORT_STOP_BITS,
            'parity': self.PORT_PARITY
        }

    def get_ui_config(self) -> Dict[str, Any]:
        """获取UI配置"""
        return {
            'theme': self.UI_THEME,
            'colors': self.UI_COLORS,
            'fonts': self.UI_FONTS,
            'window_size': (self.WINDOW_DEFAULT_WIDTH, self.WINDOW_DEFAULT_HEIGHT),
            'min_size': (self.WINDOW_MIN_WIDTH, self.WINDOW_MIN_HEIGHT),
            'resizable': self.WINDOW_RESIZABLE,
            'fullscreen': self.WINDOW_FULLSCREEN,
            'center': self.WINDOW_CENTER
        }

    def get_timer_config(self) -> Dict[str, Any]:
        """获取定时器配置"""
        return {
            'credit_refresh': self.CREDIT_REFRESH_INTERVAL,
            'port_status': self.PORT_STATUS_INTERVAL,
            'task_progress': self.TASK_PROGRESS_INTERVAL
        }

    def get_file_config(self) -> Dict[str, Any]:
        """获取文件配置"""
        return {
            'max_upload_size': self.MAX_UPLOAD_SIZE,
            'supported_formats': self.SUPPORTED_FILE_FORMATS,
            'max_phone_count': self.MAX_PHONE_COUNT
        }

    def get_export_config(self) -> Dict[str, Any]:
        """获取导出配置"""
        return {
            'default_format': self.DEFAULT_EXPORT_FORMAT,
            'export_dir': str(self.EXPORT_DIR),
            'filename_template': self.EXPORT_FILENAME_TEMPLATE
        }

    def update_config(self, key: str, value: Any) -> bool:
        """动态更新配置"""
        try:
            if hasattr(self, key):
                setattr(self, key, value)
                return True
            return False
        except Exception:
            return False

    def get_all_config(self) -> Dict[str, Any]:
        """获取所有配置的字典形式"""
        config = {}
        for attr_name in dir(self):
            if not attr_name.startswith('_') and not callable(getattr(self, attr_name)):
                value = getattr(self, attr_name)
                # 转换Path对象为字符串
                if isinstance(value, Path):
                    value = str(value)
                config[attr_name] = value
        return config

    def validate_config(self) -> Dict[str, Any]:
        """验证配置有效性"""
        errors = []
        warnings = []

        # 验证数据库配置
        if not self.DB_HOST:
            errors.append("数据库主机地址不能为空")
        if not self.DB_NAME:
            errors.append("数据库名称不能为空")
        if not self.DB_USER:
            errors.append("数据库用户名不能为空")

        # 验证端口配置
        if self.PORT_BAUD_RATE <= 0:
            errors.append("串口波特率必须大于0")
        if self.PORT_SCAN_TIMEOUT <= 0:
            errors.append("端口扫描超时时间必须大于0")

        # 验证UI配置
        if self.WINDOW_DEFAULT_WIDTH < 600:
            warnings.append("窗口宽度小于600可能影响显示效果")
        if self.WINDOW_DEFAULT_HEIGHT < 400:
            warnings.append("窗口高度小于400可能影响显示效果")

        # 验证发送配置
        if self.DEFAULT_SEND_INTERVAL < 100:
            warnings.append("发送间隔小于100毫秒可能导致发送过快")
        if self.SMS_RATE <= 0 or self.MMS_RATE <= 0:
            errors.append("短信和彩信费率必须大于0")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }


# 全局设置实例
settings = Settings()