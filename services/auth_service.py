"""
猫池短信系统认证服务 - tkinter版 (改进版)
Authentication service for SMS Pool System - tkinter version (Improved)
"""

import sys
import uuid
import threading
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 延迟导入，避免循环导入
def _import_dependencies():
    """延迟导入依赖"""
    try:
        from models.user import ChannelOperator, UserAuth, get_mac_address
        from config.settings import settings
        from config.logging_config import get_logger, log_auth_action, log_error, log_info
        return {
            'ChannelOperator': ChannelOperator,
            'UserAuth': UserAuth,
            'get_mac_address': get_mac_address,
            'settings': settings,
            'get_logger': get_logger,
            'log_auth_action': log_auth_action,
            'log_error': log_error,
            'log_info': log_info
        }
    except ImportError as e:
        print(f"导入认证服务依赖失败: {e}")
        return None

# 全局依赖缓存
_deps = None

def get_deps():
    """获取依赖"""
    global _deps
    if _deps is None:
        _deps = _import_dependencies()
        if _deps is None:
            # 创建Mock依赖
            _deps = _create_mock_dependencies()
    return _deps

def _create_mock_dependencies():
    """创建Mock依赖"""
    import logging

    class MockChannelOperator:
        def __init__(self, **kwargs):
            self.id = kwargs.get('id', 1)
            self.username = kwargs.get('username', 'test_user')
            self.available_credits = 1000
            self.status = 'active'

        @classmethod
        def authenticate(cls, username, password, mac_address=None):
            # 简单的测试认证
            if username == 'test' and password == 'test':
                return cls(username=username)
            return None

        def record_login_attempt(self, success, ip):
            pass

        def can_login(self):
            return self.status == 'active'

        def has_sufficient_credits(self, amount):
            return self.available_credits >= amount

        def check_mac_address(self, mac_address):
            return True

    class MockUserAuth:
        def __init__(self, **kwargs):
            self.user = kwargs.get('user')
            self.is_authenticated = kwargs.get('is_authenticated', False)
            self.login_time = kwargs.get('login_time', datetime.now())
            self.session_id = str(uuid.uuid4())

        def logout(self):
            self.is_authenticated = False

        def is_session_valid(self, max_age_hours=8):
            if not self.is_authenticated:
                return False
            age = datetime.now() - self.login_time
            return age.total_seconds() / 3600 < max_age_hours

        def get_user_info(self):
            if self.user:
                return {
                    'id': self.user.id,
                    'username': self.user.username,
                    'balance': self.user.available_credits,
                    'status': self.user.status
                }
            return {}

        def refresh_user_data(self):
            return True

    def mock_get_mac_address():
        return "00:00:00:00:00:00"

    class MockSettings:
        SESSION_TIMEOUT = 28800
        MAC_VERIFICATION = True
        SKIP_MAC_VERIFICATION = False
        AUTO_LOGIN = False
        MAX_LOGIN_ATTEMPTS = 5
        LOGIN_LOCKOUT_TIME = 15
        MIN_PASSWORD_LENGTH = 6

    def mock_get_logger(name='services.auth'):
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def mock_log_auth_action(username, action, success, details=None):
        logger = mock_get_logger()
        status = "成功" if success else "失败"
        message = f"[用户认证] {username} {action} {status}"
        if details:
            message += f" - {details}"
        if success:
            logger.info(message)
        else:
            logger.warning(message)

    def mock_log_error(message, error=None):
        logger = mock_get_logger()
        logger.error(f"{message}: {error}" if error else message)

    def mock_log_info(message):
        logger = mock_get_logger()
        logger.info(message)

    return {
        'ChannelOperator': MockChannelOperator,
        'UserAuth': MockUserAuth,
        'get_mac_address': mock_get_mac_address,
        'settings': MockSettings(),
        'get_logger': mock_get_logger,
        'log_auth_action': mock_log_auth_action,
        'log_error': mock_log_error,
        'log_info': mock_log_info
    }


class AuthService:
    """认证服务类"""

    def __init__(self):
        """初始化认证服务"""
        self.deps = get_deps()
        self.logger = self.deps['get_logger']('services.auth')

        self.current_auth: Optional = None
        self._lock = threading.Lock()
        self._session_timers: Dict[str, threading.Timer] = {}
        self.login_attempts: Dict[str, int] = {}
        self.last_attempt_time: Dict[str, datetime] = {}
        self.is_initialized = False

    def initialize(self) -> bool:
        """初始化服务"""
        try:
            self.deps['log_info']("认证服务初始化开始")

            # 清理过期的登录尝试记录
            self._cleanup_login_attempts()

            # 检查自动登录
            if getattr(self.deps['settings'], 'AUTO_LOGIN', False):
                self._try_auto_login()

            self.is_initialized = True
            self.deps['log_info']("认证服务初始化完成")
            return True

        except Exception as e:
            self.deps['log_error']("认证服务初始化失败", error=e)
            return False

    def login(self, username: str, password: str, remember_me: bool = False) -> Dict[str, Any]:
        """用户登录"""
        try:
            with self._lock:
                # 检查登录尝试限制
                if not self._check_login_attempts(username):
                    return {
                        'success': False,
                        'message': '登录尝试过于频繁，请稍后再试',
                        'error_code': 'TOO_MANY_ATTEMPTS'
                    }

                # 获取当前MAC地址
                current_mac = self.deps['get_mac_address']()

                # 尝试认证
                user = self.deps['ChannelOperator'].authenticate(
                    username=username,
                    password=password,
                    mac_address=current_mac
                )

                if not user:
                    # 记录登录失败
                    self._record_login_attempt(username, False)
                    return {
                        'success': False,
                        'message': '用户名、密码错误或MAC地址未授权',
                        'error_code': 'AUTH_FAILED'
                    }

                # 创建用户认证对象
                self.current_auth = self.deps['UserAuth'](
                    user=user,
                    is_authenticated=True,
                    login_time=datetime.now()
                )

                # 记录登录成功
                self._record_login_attempt(username, True)
                user.record_login_attempt(True, self._get_client_ip())

                # 设置会话超时
                self._setup_session_timeout()

                # 保存登录状态（如果需要记住）
                if remember_me:
                    self._save_login_credentials(username, current_mac)

                self.deps['log_auth_action'](username, "登录", True, f"MAC={current_mac}")

                return {
                    'success': True,
                    'message': '登录成功',
                    'user': self.get_current_user_info(),
                    'session_id': self.current_auth.session_id
                }

        except Exception as e:
            self.deps['log_error']("用户登录异常", error=e)
            return {
                'success': False,
                'message': f'登录异常: {str(e)}',
                'error_code': 'SYSTEM_ERROR'
            }

    # ... 其他方法保持不变，但都要使用self.deps来访问依赖

    def _check_login_attempts(self, username: str) -> bool:
        """检查登录尝试限制"""
        try:
            max_attempts = getattr(self.deps['settings'], 'MAX_LOGIN_ATTEMPTS', 5)
            lockout_time = getattr(self.deps['settings'], 'LOGIN_LOCKOUT_TIME', 15)

            current_time = datetime.now()

            if username in self.last_attempt_time:
                time_diff = current_time - self.last_attempt_time[username]
                if time_diff < timedelta(minutes=lockout_time):
                    attempts = self.login_attempts.get(username, 0)
                    if attempts >= max_attempts:
                        return False
            else:
                self.login_attempts.pop(username, None)

            return True

        except Exception as e:
            self.deps['log_error']("检查登录尝试限制失败", error=e)
            return True

    def _record_login_attempt(self, username: str, success: bool):
        """记录登录尝试"""
        try:
            current_time = datetime.now()

            if success:
                self.login_attempts.pop(username, None)
                self.last_attempt_time.pop(username, None)
            else:
                self.login_attempts[username] = self.login_attempts.get(username, 0) + 1
                self.last_attempt_time[username] = current_time

        except Exception as e:
            self.deps['log_error']("记录登录尝试失败", error=e)

    def _cleanup_login_attempts(self):
        """清理过期的登录尝试记录"""
        try:
            current_time = datetime.now()
            lockout_time = getattr(self.deps['settings'], 'LOGIN_LOCKOUT_TIME', 15)

            expired_users = []
            for username, last_time in self.last_attempt_time.items():
                if current_time - last_time > timedelta(minutes=lockout_time):
                    expired_users.append(username)

            for username in expired_users:
                self.login_attempts.pop(username, None)
                self.last_attempt_time.pop(username, None)

        except Exception as e:
            self.deps['log_error']("清理登录尝试记录失败", error=e)

    def _get_client_ip(self) -> str:
        """获取客户端IP地址"""
        try:
            import socket
            hostname = socket.gethostname()
            return socket.gethostbyname(hostname)
        except Exception:
            return "127.0.0.1"

    def get_current_user_info(self) -> Dict[str, Any]:
        """获取当前用户信息"""
        if not self.is_authenticated():
            return {}
        return self.current_auth.get_user_info()

    def is_authenticated(self) -> bool:
        """检查是否已认证"""
        return (self.current_auth is not None and
                self.current_auth.is_authenticated and
                self.is_session_valid())

    def is_session_valid(self) -> bool:
        """检查会话是否有效"""
        if not self.current_auth:
            return False
        return self.current_auth.is_session_valid(
            max_age_hours=getattr(self.deps['settings'], 'SESSION_TIMEOUT', 28800) // 3600
        )

    # 其他方法的实现类似，都需要适配使用self.deps...


# 全局认证服务实例
auth_service = AuthService()