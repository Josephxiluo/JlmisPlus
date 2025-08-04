"""
猫池短信系统认证服务 - tkinter版
Authentication service for SMS Pool System - tkinter version
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

try:
    from models.user import ChannelOperator, UserAuth, get_mac_address
    from config.settings import settings
    from config.logging_config import get_logger, log_auth_action, log_error, log_info
except ImportError:
    # 简化处理
    class MockChannelOperator:
        @classmethod
        def authenticate(cls, username, password, mac_address=None):
            return None


    class MockUserAuth:
        def __init__(self, **kwargs):
            self.is_authenticated = False
            self.user = None


    ChannelOperator = MockChannelOperator
    UserAuth = MockUserAuth


    def get_mac_address():
        return "00:00:00:00:00:00"


    class MockSettings:
        SESSION_TIMEOUT = 28800
        MAC_VERIFICATION = True
        SKIP_MAC_VERIFICATION = False
        AUTO_LOGIN = False


    settings = MockSettings()

    import logging


    def get_logger(name='services.auth'):
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger


    def log_auth_action(username, action, success, details=None):
        logger = get_logger()
        status = "成功" if success else "失败"
        message = f"[用户认证] {username} {action} {status}"
        if details:
            message += f" - {details}"
        if success:
            logger.info(message)
        else:
            logger.warning(message)


    def log_error(message, error=None):
        logger = get_logger()
        logger.error(f"{message}: {error}" if error else message)


    def log_info(message):
        logger = get_logger()
        logger.info(message)

logger = get_logger('services.auth')


class AuthService:
    """认证服务类"""

    def __init__(self):
        """初始化认证服务"""
        self.current_auth: Optional[UserAuth] = None
        self._lock = threading.Lock()
        self._session_timers: Dict[str, threading.Timer] = {}
        self.login_attempts: Dict[str, int] = {}  # 登录尝试计数
        self.last_attempt_time: Dict[str, datetime] = {}  # 最后尝试时间
        self.is_initialized = False

    def initialize(self) -> bool:
        """初始化服务"""
        try:
            log_info("认证服务初始化开始")

            # 清理过期的登录尝试记录
            self._cleanup_login_attempts()

            # 检查自动登录
            if getattr(settings, 'AUTO_LOGIN', False):
                self._try_auto_login()

            self.is_initialized = True
            log_info("认证服务初始化完成")
            return True

        except Exception as e:
            log_error("认证服务初始化失败", error=e)
            return False

    def shutdown(self):
        """关闭服务"""
        try:
            log_info("认证服务开始关闭")

            # 取消所有定时器
            for timer in self._session_timers.values():
                if timer.is_alive():
                    timer.cancel()
            self._session_timers.clear()

            # 登出当前用户
            if self.current_auth and self.current_auth.is_authenticated:
                self.logout()

            self.is_initialized = False
            log_info("认证服务关闭完成")

        except Exception as e:
            log_error("认证服务关闭失败", error=e)

    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        return {
            'running': self.is_initialized,
            'authenticated': self.is_authenticated(),
            'user_info': self.get_current_user_info(),
            'session_valid': self.is_session_valid(),
            'mac_verification_enabled': getattr(settings, 'MAC_VERIFICATION', True),
            'message': '认证服务正常运行' if self.is_initialized else '认证服务未初始化'
        }

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
                current_mac = get_mac_address()

                # 尝试认证
                user = ChannelOperator.authenticate(
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
                self.current_auth = UserAuth(
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

                log_auth_action(username, "登录", True, f"MAC={current_mac}")

                return {
                    'success': True,
                    'message': '登录成功',
                    'user_info': self.get_current_user_info(),
                    'session_id': self.current_auth.session_id
                }

        except Exception as e:
            log_error("用户登录异常", error=e)
            return {
                'success': False,
                'message': f'登录异常: {str(e)}',
                'error_code': 'SYSTEM_ERROR'
            }

    def logout(self) -> Dict[str, Any]:
        """用户登出"""
        try:
            with self._lock:
                if not self.current_auth or not self.current_auth.is_authenticated:
                    return {
                        'success': False,
                        'message': '用户未登录',
                        'error_code': 'NOT_AUTHENTICATED'
                    }

                username = self.current_auth.user.username if self.current_auth.user else "未知用户"

                # 取消会话定时器
                self._cancel_session_timeout()

                # 执行登出
                self.current_auth.logout()
                self.current_auth = None

                # 清除保存的登录凭据
                self._clear_saved_credentials()

                log_auth_action(username, "登出", True)

                return {
                    'success': True,
                    'message': '登出成功'
                }

        except Exception as e:
            log_error("用户登出异常", error=e)
            return {
                'success': False,
                'message': f'登出异常: {str(e)}',
                'error_code': 'SYSTEM_ERROR'
            }

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
            max_age_hours=getattr(settings, 'SESSION_TIMEOUT', 28800) // 3600
        )

    def get_current_user(self) -> Optional[ChannelOperator]:
        """获取当前用户"""
        if self.is_authenticated():
            return self.current_auth.user
        return None

    def get_current_user_info(self) -> Dict[str, Any]:
        """获取当前用户信息"""
        if not self.is_authenticated():
            return {}

        return self.current_auth.get_user_info()

    def refresh_user_data(self) -> bool:
        """刷新用户数据"""
        try:
            if not self.current_auth or not self.current_auth.is_authenticated:
                return False

            return self.current_auth.refresh_user_data()

        except Exception as e:
            log_error("刷新用户数据失败", error=e)
            return False

    def check_permission(self, action: str) -> bool:
        """检查用户权限"""
        if not self.is_authenticated():
            return False

        user = self.get_current_user()
        if not user:
            return False

        # 基本权限检查
        if not user.can_login():
            return False

        # 根据操作类型检查特定权限
        if action == 'send_sms':
            return user.has_sufficient_credits(1)  # 短信需要1积分
        elif action == 'send_mms':
            return user.has_sufficient_credits(3)  # 彩信需要3积分
        elif action in ['create_task', 'manage_task']:
            return True  # 登录用户都可以创建和管理任务
        elif action == 'use_port':
            return True  # 登录用户都可以使用端口

        return True  # 默认允许

    def validate_mac_address(self, mac_address: str = None) -> bool:
        """验证MAC地址"""
        try:
            if not getattr(settings, 'MAC_VERIFICATION', True):
                return True

            if getattr(settings, 'SKIP_MAC_VERIFICATION', False):
                return True

            user = self.get_current_user()
            if not user:
                return False

            return user.check_mac_address(mac_address)

        except Exception as e:
            log_error("MAC地址验证失败", error=e)
            return False

    def update_session(self) -> bool:
        """更新会话（延长会话时间）"""
        try:
            if not self.is_authenticated():
                return False

            # 重新设置会话超时
            self._setup_session_timeout()

            # 更新最后活动时间
            self.current_auth.login_time = datetime.now()

            return True

        except Exception as e:
            log_error("更新会话失败", error=e)
            return False

    def _check_login_attempts(self, username: str) -> bool:
        """检查登录尝试限制"""
        try:
            max_attempts = getattr(settings, 'MAX_LOGIN_ATTEMPTS', 5)
            lockout_time = getattr(settings, 'LOGIN_LOCKOUT_TIME', 15)  # 分钟

            current_time = datetime.now()

            # 检查是否在锁定期内
            if username in self.last_attempt_time:
                time_diff = current_time - self.last_attempt_time[username]
                if time_diff < timedelta(minutes=lockout_time):
                    attempts = self.login_attempts.get(username, 0)
                    if attempts >= max_attempts:
                        return False
            else:
                # 超过锁定时间，重置计数
                self.login_attempts.pop(username, None)

            return True

        except Exception as e:
            log_error("检查登录尝试限制失败", error=e)
            return True  # 出错时允许登录

    def _record_login_attempt(self, username: str, success: bool):
        """记录登录尝试"""
        try:
            current_time = datetime.now()

            if success:
                # 登录成功，清除失败记录
                self.login_attempts.pop(username, None)
                self.last_attempt_time.pop(username, None)
            else:
                # 登录失败，增加计数
                self.login_attempts[username] = self.login_attempts.get(username, 0) + 1
                self.last_attempt_time[username] = current_time

        except Exception as e:
            log_error("记录登录尝试失败", error=e)

    def _cleanup_login_attempts(self):
        """清理过期的登录尝试记录"""
        try:
            current_time = datetime.now()
            lockout_time = getattr(settings, 'LOGIN_LOCKOUT_TIME', 15)

            expired_users = []
            for username, last_time in self.last_attempt_time.items():
                if current_time - last_time > timedelta(minutes=lockout_time):
                    expired_users.append(username)

            for username in expired_users:
                self.login_attempts.pop(username, None)
                self.last_attempt_time.pop(username, None)

        except Exception as e:
            log_error("清理登录尝试记录失败", error=e)

    def _setup_session_timeout(self):
        """设置会话超时"""
        try:
            if not self.current_auth:
                return

            # 取消现有定时器
            self._cancel_session_timeout()

            # 设置新的定时器
            timeout_seconds = getattr(settings, 'SESSION_TIMEOUT', 28800)  # 8小时

            timer = threading.Timer(timeout_seconds, self._session_timeout_callback)
            timer.daemon = True
            timer.start()

            self._session_timers[self.current_auth.session_id] = timer

        except Exception as e:
            log_error("设置会话超时失败", error=e)

    def _cancel_session_timeout(self):
        """取消会话超时"""
        try:
            if not self.current_auth:
                return

            session_id = self.current_auth.session_id
            if session_id in self._session_timers:
                timer = self._session_timers[session_id]
                if timer.is_alive():
                    timer.cancel()
                del self._session_timers[session_id]

        except Exception as e:
            log_error("取消会话超时失败", error=e)

    def _session_timeout_callback(self):
        """会话超时回调"""
        try:
            if self.current_auth and self.current_auth.is_authenticated:
                username = self.current_auth.user.username if self.current_auth.user else "未知用户"
                log_auth_action(username, "会话超时", False, "自动登出")
                self.logout()

        except Exception as e:
            log_error("会话超时处理失败", error=e)

    def _get_client_ip(self) -> str:
        """获取客户端IP地址"""
        try:
            import socket
            hostname = socket.gethostname()
            return socket.gethostbyname(hostname)
        except Exception:
            return "127.0.0.1"

    def _save_login_credentials(self, username: str, mac_address: str):
        """保存登录凭据（记住登录）"""
        try:
            # 这里可以实现保存到配置文件或注册表的逻辑
            # 出于安全考虑，这里只是示例，实际实现时需要加密存储
            pass

        except Exception as e:
            log_error("保存登录凭据失败", error=e)

    def _clear_saved_credentials(self):
        """清除保存的登录凭据"""
        try:
            # 清除保存的登录信息
            pass

        except Exception as e:
            log_error("清除登录凭据失败", error=e)

    def _try_auto_login(self):
        """尝试自动登录"""
        try:
            # 这里可以实现从保存的凭据自动登录的逻辑
            pass

        except Exception as e:
            log_error("自动登录失败", error=e)

    def get_login_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取登录历史"""
        try:
            user = self.get_current_user()
            if not user:
                return []

            # 这里可以从数据库获取登录历史
            # 暂时返回当前登录信息
            if self.is_authenticated():
                return [{
                    'login_time': self.current_auth.login_time.isoformat(),
                    'ip_address': self._get_client_ip(),
                    'mac_address': get_mac_address(),
                    'status': 'active'
                }]

            return []

        except Exception as e:
            log_error("获取登录历史失败", error=e)
            return []

    def force_logout_all_sessions(self) -> bool:
        """强制登出所有会话"""
        try:
            # 取消所有定时器
            for timer in self._session_timers.values():
                if timer.is_alive():
                    timer.cancel()
            self._session_timers.clear()

            # 登出当前用户
            if self.current_auth:
                self.current_auth.logout()
                self.current_auth = None

            log_info("强制登出所有会话")
            return True

        except Exception as e:
            log_error("强制登出失败", error=e)
            return False


# 全局认证服务实例
auth_service = AuthService()