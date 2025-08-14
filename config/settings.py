"""
猫池短信系统基础设置管理 - tkinter版
Settings management for SMS Pool System - tkinter version
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
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
            print(f"✅ 已加载环境配置文件: {env_path}")
        else:
            print(f"⚠️ 环境配置文件不存在: {env_path}")

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

    # ========== 辅助方法 ==========
    @staticmethod
    def get_env(key: str, default: str = '') -> str:
        """获取字符串类型的环境变量"""
        return os.getenv(key, default)

    @staticmethod
    def get_env_int(key: str, default: int = 0) -> int:
        """获取整数类型的环境变量"""
        value = os.getenv(key)
        if value:
            try:
                return int(value)
            except ValueError:
                print(f"⚠️ 配置 {key} 的值 '{value}' 不是有效的整数，使用默认值 {default}")
        return default

    @staticmethod
    def get_env_float(key: str, default: float = 0.0) -> float:
        """获取浮点数类型的环境变量"""
        value = os.getenv(key)
        if value:
            try:
                return float(value)
            except ValueError:
                print(f"⚠️ 配置 {key} 的值 '{value}' 不是有效的浮点数，使用默认值 {default}")
        return default

    @staticmethod
    def get_env_bool(key: str, default: bool = False) -> bool:
        """获取布尔类型的环境变量"""
        value = os.getenv(key)
        if value:
            return value.lower() in ('true', '1', 'yes', 'on')
        return default

    def _init_app_config(self):
        """应用基础配置"""
        self.APP_NAME = self.get_env('APP_NAME', '猫池短信系统')
        self.APP_VERSION = self.get_env('APP_VERSION', '1.0.0')
        self.APP_ENV = self.get_env('APP_ENV', 'development')
        self.DEBUG = self.get_env_bool('DEBUG', True)

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
        self.DB_HOST = self.get_env('DB_HOST', 'localhost')
        self.DB_PORT = self.get_env_int('DB_PORT', 5432)
        self.DB_NAME = self.get_env('DB_NAME', 'sms_pool_db')
        self.DB_USER = self.get_env('DB_USER', 'postgres')
        self.DB_PASSWORD = self.get_env('DB_PASSWORD', 'password')
        self.DB_CHARSET = self.get_env('DB_CHARSET', 'utf8')

        # 连接池配置
        self.DB_POOL_SIZE = self.get_env_int('DB_POOL_SIZE', 5)
        self.DB_POOL_TIMEOUT = self.get_env_int('DB_POOL_TIMEOUT', 30)
        self.CONNECTION_RETRY_COUNT = self.get_env_int('CONNECTION_RETRY_COUNT', 3)
        self.CONNECTION_RETRY_DELAY = self.get_env_float('CONNECTION_RETRY_DELAY', 1.0)

    def _init_auth_config(self):
        """认证配置"""
        self.PASSWORD_SALT = self.get_env('PASSWORD_SALT', 'sms_pool_salt_2024')
        self.MAC_VERIFICATION = self.get_env_bool('MAC_VERIFICATION', True)
        self.AUTO_LOGIN = self.get_env_bool('AUTO_LOGIN', False)
        self.SESSION_TIMEOUT = self.get_env_int('SESSION_TIMEOUT', 28800)  # 8小时
        self.MAX_LOGIN_ATTEMPTS = self.get_env_int('MAX_LOGIN_ATTEMPTS', 5)
        self.LOGIN_LOCKOUT_TIME = self.get_env_int('LOGIN_LOCKOUT_TIME', 15)  # 分钟
        self.MIN_PASSWORD_LENGTH = self.get_env_int('MIN_PASSWORD_LENGTH', 6)

        # 开发模式配置
        self.SKIP_MAC_VERIFICATION = self.get_env_bool('SKIP_MAC_VERIFICATION', False)

    def _init_sms_config(self):
        """短信发送配置"""
        self.DEFAULT_SEND_INTERVAL = self.get_env_int('DEFAULT_SEND_INTERVAL', 1000)  # 毫秒
        self.DEFAULT_RETRY_COUNT = self.get_env_int('DEFAULT_RETRY_COUNT', 3)
        self.DEFAULT_TIMEOUT = self.get_env_int('DEFAULT_TIMEOUT', 30)  # 秒
        self.MAX_CONCURRENT_TASKS = self.get_env_int('MAX_CONCURRENT_TASKS', 3)
        self.SMS_RATE = self.get_env_float('SMS_RATE', 1.0)  # 短信费率
        self.MMS_RATE = self.get_env_float('MMS_RATE', 3.0)  # 彩信费率

        # 发送控制配置
        self.CARD_SWITCH_INTERVAL = self.get_env_int('CARD_SWITCH_INTERVAL', 60)  # 卡片更换间隔
        self.MONITOR_ALERT_INTERVAL = self.get_env_int('MONITOR_ALERT_INTERVAL', 1000)  # 监测提醒间隔
        self.DEFAULT_MONITOR_PHONE = self.get_env('DEFAULT_MONITOR_PHONE', '')  # 默认监测号码

    def _init_port_config(self):
        """端口管理配置"""
        self.PORT_SCAN_TIMEOUT = self.get_env_int('PORT_SCAN_TIMEOUT', 5)
        self.PORT_SCAN_INTERVAL = self.get_env_int('PORT_SCAN_INTERVAL', 5)  # 添加缺失的配置
        self.PORT_CHECK_INTERVAL = self.get_env_int('PORT_CHECK_INTERVAL', 10)
        self.AUTO_PORT_SCAN = self.get_env_bool('AUTO_PORT_SCAN', True)

        # 串口通信参数
        self.PORT_BAUD_RATE = self.get_env_int('PORT_BAUD_RATE', 115200)
        self.PORT_DATA_BITS = self.get_env_int('PORT_DATA_BITS', 8)
        self.PORT_STOP_BITS = self.get_env_int('PORT_STOP_BITS', 1)
        self.PORT_PARITY = self.get_env('PORT_PARITY', 'N')  # N, E, O

    def _init_file_config(self):
        """文件处理配置"""
        self.MAX_UPLOAD_SIZE = self.get_env_int('MAX_UPLOAD_SIZE', 10) * 1024 * 1024  # MB转字节
        self.SUPPORTED_FILE_FORMATS = self.get_env('SUPPORTED_FILE_FORMATS', 'xlsx,xls,csv,txt').split(',')
        self.MAX_PHONE_COUNT = self.get_env_int('MAX_PHONE_COUNT', 10000)  # 单次最大号码数

    def _init_log_config(self):
        """日志配置"""
        self.LOG_LEVEL = self.get_env('LOG_LEVEL', 'INFO')
        self.LOG_MAX_SIZE = self.get_env_int('LOG_MAX_SIZE', 50) * 1024 * 1024  # MB转字节
        self.LOG_BACKUP_COUNT = self.get_env_int('LOG_BACKUP_COUNT', 3)
        self.LOG_TO_CONSOLE = self.get_env_bool('LOG_TO_CONSOLE', True)
        self.SQL_DEBUG = self.get_env_bool('SQL_DEBUG', False)

    def _init_ui_config(self):
        """tkinter UI配置"""
        self.UI_THEME = self.get_env('UI_THEME', 'orange')

        # 窗口配置
        self.WINDOW_DEFAULT_WIDTH = self.get_env_int('WINDOW_DEFAULT_WIDTH', 1200)
        self.WINDOW_DEFAULT_HEIGHT = self.get_env_int('WINDOW_DEFAULT_HEIGHT', 800)
        self.WINDOW_MIN_WIDTH = self.get_env_int('WINDOW_MIN_WIDTH', 800)
        self.WINDOW_MIN_HEIGHT = self.get_env_int('WINDOW_MIN_HEIGHT', 600)
        self.WINDOW_RESIZABLE = self.get_env_bool('WINDOW_RESIZABLE', True)
        self.WINDOW_FULLSCREEN = self.get_env_bool('WINDOW_FULLSCREEN', False)
        self.WINDOW_CENTER = self.get_env_bool('WINDOW_CENTER', True)

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
        self.CREDIT_REFRESH_INTERVAL = self.get_env_int('CREDIT_REFRESH_INTERVAL', 300)  # 5分钟
        self.CREDIT_UPDATE_INTERVAL = self.get_env_int('CREDIT_UPDATE_INTERVAL', 300)  # 兼容旧配置
        self.PORT_STATUS_INTERVAL = self.get_env_int('PORT_STATUS_INTERVAL', 5)  # 5秒
        self.TASK_PROGRESS_INTERVAL = self.get_env_int('TASK_PROGRESS_INTERVAL', 2)  # 2秒

    def _init_task_config(self):
        """任务管理配置"""
        self.TASK_PAGE_SIZE = self.get_env_int('TASK_PAGE_SIZE', 20)
        self.TASK_BATCH_SIZE = self.get_env_int('TASK_BATCH_SIZE', 100)  # 添加缺失的配置
        self.MESSAGE_PAGE_SIZE = self.get_env_int('MESSAGE_PAGE_SIZE', 50)
        self.TASK_AUTO_CLEANUP_DAYS = self.get_env_int('TASK_AUTO_CLEANUP_DAYS', 30)

    def _init_performance_config(self):
        """性能监控配置"""
        self.PERFORMANCE_MONITORING = self.get_env_bool('PERFORMANCE_MONITORING', True)
        self.MEMORY_WARNING_THRESHOLD = self.get_env_int('MEMORY_WARNING_THRESHOLD', 500)  # MB
        self.CPU_WARNING_THRESHOLD = self.get_env_int('CPU_WARNING_THRESHOLD', 80)  # %
        self.CACHE_EXPIRE_TIME = self.get_env_int('CACHE_EXPIRE_TIME', 24)  # 小时

    def _init_security_config(self):
        """安全配置"""
        self.SECRET_KEY = self.get_env('SECRET_KEY', 'your-secret-key-change-this')
        self.REQUEST_TIMEOUT = self.get_env_int('REQUEST_TIMEOUT', 30)
        self.HTTP_PROXY = self.get_env('HTTP_PROXY', '')
        self.HTTPS_PROXY = self.get_env('HTTPS_PROXY', '')

        # 开发模式配置
        self.SIMULATION_MODE = self.get_env_bool('SIMULATION_MODE', False)
        self.TEST_DB_NAME = self.get_env('TEST_DB_NAME', 'sms_pool_test')

    def _init_export_config(self):
        """导出配置"""
        self.DEFAULT_EXPORT_FORMAT = self.get_env('DEFAULT_EXPORT_FORMAT', 'xlsx')
        self.EXPORT_DIR = self.BASE_DIR / self.get_env('EXPORT_DIR', 'temp/exports')
        self.EXPORT_FILENAME_TEMPLATE = self.get_env('EXPORT_FILENAME_TEMPLATE', '{task_name}_{status}_{timestamp}')

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
            try:
                directory.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                print(f"⚠️ 创建目录 {directory} 失败: {e}")

    def get_database_url(self) -> str:
        """获取数据库连接URL"""
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    def get_log_file_path(self, log_type: str = 'app') -> Path:
        """获取日志文件路径"""
        return self.LOGS_DIR / f"{log_type}.log"

    def get_icon_path(self, icon_name: str) -> Path:
        """获取图标文件路径"""
        icon_file = self.ICONS_DIR / f"{icon_name}.png"
        if not icon_file.exists():
            # 如果图标不存在，返回默认图标路径
            default_icon = self.ICONS_DIR / "default.png"
            return default_icon if default_icon.exists() else self.ICONS_DIR / "logo.png"
        return icon_file

    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.APP_ENV.lower() in ('development', 'dev')

    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.APP_ENV.lower() in ('production', 'prod')

    def get_window_geometry(self) -> str:
        """获取窗口几何配置"""
        return f"{self.WINDOW_DEFAULT_WIDTH}x{self.WINDOW_DEFAULT_HEIGHT}"

    def get_window_center_position(self) -> Tuple[int, int]:
        """获取窗口居中位置"""
        try:
            import tkinter as tk
            # 获取屏幕尺寸
            root = tk.Tk()
            root.withdraw()  # 隐藏窗口
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()
            root.destroy()

            # 计算居中位置
            x = (screen_width - self.WINDOW_DEFAULT_WIDTH) // 2
            y = (screen_height - self.WINDOW_DEFAULT_HEIGHT) // 2

            return max(0, x), max(0, y)
        except:
            return 100, 100  # 默认位置

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
            'scan_interval': self.PORT_SCAN_INTERVAL,
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
            'max_phone_count': self.MAX_PHONE_COUNT,
            'upload_dir': str(self.UPLOADS_DIR),
            'export_dir': str(self.EXPORTS_DIR)
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
        if self.DB_PASSWORD == 'password':
            warnings.append("使用默认密码不安全，请修改数据库密码")

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

        # 验证安全配置
        if self.SECRET_KEY == 'your-secret-key-change-this':
            warnings.append("请修改默认的 SECRET_KEY 以提高安全性")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

    def display_config(self):
        """显示当前配置（用于调试）"""
        print("=" * 60)
        print("当前系统配置")
        print("=" * 60)

        configs = [
            ("应用配置", [
                ("应用名称", self.APP_NAME),
                ("应用版本", self.APP_VERSION),
                ("运行环境", self.APP_ENV),
                ("调试模式", self.DEBUG),
            ]),
            ("数据库配置", [
                ("主机", self.DB_HOST),
                ("端口", self.DB_PORT),
                ("数据库", self.DB_NAME),
                ("用户", self.DB_USER),
                ("密码", "***" if self.DB_PASSWORD else "未设置"),
                ("连接池大小", self.DB_POOL_SIZE),
                ("连接超时", f"{self.DB_POOL_TIMEOUT}秒"),
                ("重试次数", self.CONNECTION_RETRY_COUNT),
                ("重试延迟", f"{self.CONNECTION_RETRY_DELAY}秒"),
            ]),
            ("任务配置", [
                ("进度更新间隔", f"{self.TASK_PROGRESS_INTERVAL}秒"),
                ("最大并发任务", self.MAX_CONCURRENT_TASKS),
                ("批处理大小", self.TASK_BATCH_SIZE),
            ]),
            ("费率配置", [
                ("短信费率", f"{self.SMS_RATE}积分/条"),
                ("彩信费率", f"{self.MMS_RATE}积分/条"),
            ]),
        ]

        for section_name, section_items in configs:
            print(f"\n{section_name}:")
            for key, value in section_items:
                print(f"  {key}: {value}")

        print("=" * 60)


# 全局设置实例
settings = Settings()

# 如果直接运行此模块，显示配置信息
if __name__ == "__main__":
    # 显示配置
    settings.display_config()

    # 验证配置
    validation = settings.validate_config()
    if validation['valid']:
        print("\n✅ 配置验证通过")
    else:
        print("\n❌ 配置验证失败")
        for error in validation['errors']:
            print(f"  错误: {error}")

    if validation['warnings']:
        print("\n⚠️ 配置警告:")
        for warning in validation['warnings']:
            print(f"  警告: {warning}")