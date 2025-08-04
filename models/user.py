"""
猫池短信系统用户模型 - tkinter版
User models for SMS Pool System - tkinter version
"""

import re
import sys
import uuid
import hashlib
import platform
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from .base import BaseModel, ModelManager
    from config.settings import settings
    from config.logging_config import get_logger, log_auth_action, log_credit_action, log_error
except ImportError:
    # 简化处理
    from base import BaseModel, ModelManager


    class MockSettings:
        PASSWORD_SALT = 'sms_pool_salt_2024'
        MIN_PASSWORD_LENGTH = 6
        MAX_LOGIN_ATTEMPTS = 5
        LOGIN_LOCKOUT_TIME = 15
        MAC_VERIFICATION = True
        SKIP_MAC_VERIFICATION = False


    settings = MockSettings()

    import logging


    def get_logger(name='models.user'):
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


    def log_credit_action(user_id, action, amount, balance, details=None):
        logger = get_logger()
        message = f"[积分操作] 用户ID={user_id} {action} 金额={amount} 余额={balance}"
        if details:
            message += f" - {details}"
        logger.info(message)


    def log_error(message, error=None):
        logger = get_logger()
        logger.error(f"{message}: {error}" if error else message)

logger = get_logger('models.user')


def get_mac_address() -> str:
    """获取MAC地址"""
    try:
        import uuid
        mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
        return ":".join([mac[e:e + 2] for e in range(0, 11, 2)]).upper()
    except Exception as e:
        log_error("获取MAC地址失败", error=e)
        return ""


def hash_password(password: str, salt: str = None) -> str:
    """密码哈希"""
    if salt is None:
        salt = settings.PASSWORD_SALT

    combined = f"{password}{salt}".encode('utf-8')
    return hashlib.sha256(combined).hexdigest()


def validate_phone_number(phone: str) -> bool:
    """验证手机号码格式"""
    # 国内手机号：1开头，11位数字
    domestic_pattern = r'^1[3-9]\d{9}'

    # 国际手机号：以+开头，8-15位数字
    international_pattern = r'^\+\d{8,15}'

    return bool(re.match(domestic_pattern, phone) or re.match(international_pattern, phone))


def validate_username(username: str) -> bool:
    """验证用户名格式"""
    # 用户名：4-20位，字母数字下划线
    pattern = r'^[a-zA-Z0-9_]{4,20}'
    return bool(re.match(pattern, username))


@dataclass
class ChannelOperator(BaseModel):
    """渠道操作用户模型"""

    # 表名
    _table_name: str = "channel_operators"

    # 字段映射（模型字段名 -> 数据库字段名）
    _field_mappings: Dict[str, str] = field(default_factory=lambda: {
        'id': 'operators_id',
        'username': 'operators_username',
        'password': 'operators_password',
        'mac_address': 'operators_mac_address',
        'status': 'operators_status',
        'available_credits': 'operators_available_credits',
        'used_credits': 'operators_used_credits',
        'total_credits': 'operators_total_credits',
        'channel_id': 'operators_channel_id',
        'last_login_time': 'operators_last_login_time',
        'last_login_ip': 'operators_last_login_ip',
        'login_count': 'operators_login_count',
        'failed_login_count': 'operators_failed_login_count',
        'locked_until': 'operators_locked_until',
        'remark': 'operators_remark',
        'created_at': 'operators_created_at',
        'updated_at': 'operators_updated_at'
    })

    # 验证规则
    _validation_rules: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        'username': {
            'required': True,
            'type': str,
            'min_length': 4,
            'max_length': 50,
            'pattern': r'^[a-zA-Z0-9_]{4,50}',
            'message': '用户名必须是4-50位字母、数字或下划线'
    },
    'password': {
        'required': True,
        'type': str,
        'min_length': 6,
        'max_length': 128,
        'message': '密码长度必须在6-128位之间'
    },
    'status': {
        'required': True,
        'type': str,
        'choices': ['active', 'disabled', 'locked'],
        'message': '状态必须是 active, disabled 或 locked'
    },
    'available_credits': {
        'type': int,
        'min_value': 0,
        'message': '可用积分不能为负数'
    },
    'used_credits': {
        'type': int,
        'min_value': 0,
        'message': '已用积分不能为负数'
    },
    'total_credits': {
        'type': int,
        'min_value': 0,
        'message': '总积分不能为负数'
    }
    })

    # 用户字段
    username: str = ""
    password: str = ""
    mac_address: Optional[str] = field(default=None)
    status: str = "active"

    # 积分字段
    available_credits: int = 0
    used_credits: int = 0
    total_credits: int = 0

    # 关联字段
    channel_id: Optional[int] = field(default=None)

    # 登录统计字段
    last_login_time: Optional[datetime] = field(default=None)
    last_login_ip: Optional[str] = field(default=None)
    login_count: int = 0
    failed_login_count: int = 0
    locked_until: Optional[datetime] = field(default=None)

    # 备注字段
    remark: Optional[str] = field(default=None)

    def set_password(self, raw_password: str):
        """设置密码（自动哈希）"""
        if len(raw_password) < settings.MIN_PASSWORD_LENGTH:
            raise ValueError(f"密码长度不能少于{settings.MIN_PASSWORD_LENGTH}位")

        self.password = hash_password(raw_password)

    def check_password(self, raw_password: str) -> bool:
        """检查密码"""
        return self.password == hash_password(raw_password)

    def is_active(self) -> bool:
        """检查用户是否激活"""
        return self.status == 'active'

    def is_locked(self) -> bool:
        """检查用户是否被锁定"""
        if self.status == 'locked':
            return True

        # 检查临时锁定
        if self.locked_until and self.locked_until > datetime.now():
            return True

        return False

    def can_login(self) -> bool:
        """检查是否可以登录"""
        return self.is_active() and not self.is_locked()

    def check_mac_address(self, current_mac: str = None) -> bool:
        """检查MAC地址"""
        # 如果配置跳过MAC验证，直接返回True
        if getattr(settings, 'SKIP_MAC_VERIFICATION', False):
            return True

        # 如果未启用MAC验证，直接返回True
        if not getattr(settings, 'MAC_VERIFICATION', True):
            return True

        # 如果用户未绑定MAC地址，允许登录（首次登录）
        if not self.mac_address:
            return True

        # 获取当前MAC地址
        if current_mac is None:
            current_mac = get_mac_address()

        # 比较MAC地址
        return self.mac_address.upper() == current_mac.upper()

    def bind_mac_address(self, mac_address: str = None):
        """绑定MAC地址"""
        if mac_address is None:
            mac_address = get_mac_address()

        self.mac_address = mac_address.upper()

    def has_sufficient_credits(self, required_credits: int) -> bool:
        """检查积分是否充足"""
        return self.available_credits >= required_credits

    def consume_credits(self, amount: int, description: str = None) -> bool:
        """消费积分"""
        if not self.has_sufficient_credits(amount):
            return False

        try:
            # 更新积分
            self.available_credits -= amount
            self.used_credits += amount

            # 保存更改
            if self.save():
                # 记录积分日志
                log_credit_action(
                    user_id=self.id,
                    action="消费积分",
                    amount=-amount,
                    balance=self.available_credits,
                    details=description
                )
                return True

            return False

        except Exception as e:
            log_error("消费积分失败", error=e)
            return False

    def refresh_credits_from_db(self) -> bool:
        """从数据库刷新积分信息（积分由后台管理员充值）"""
        try:
            # 重新从数据库加载当前用户信息
            fresh_user = self.__class__.find_by_id(self.id)
            if fresh_user:
                # 更新积分信息
                old_credits = self.available_credits
                self.available_credits = fresh_user.available_credits
                self.used_credits = fresh_user.used_credits
                self.total_credits = fresh_user.total_credits

                # 如果积分有变化，记录日志
                if old_credits != self.available_credits:
                    log_credit_action(
                        user_id=self.id,
                        action="积分刷新",
                        amount=self.available_credits - old_credits,
                        balance=self.available_credits,
                        details="从数据库刷新积分信息"
                    )

                return True

            return False

        except Exception as e:
            log_error("刷新积分信息失败", error=e)
            return False

    def record_login_attempt(self, success: bool, ip_address: str = None):
        """记录登录尝试"""
        try:
            current_time = datetime.now()

            if success:
                # 成功登录
                self.last_login_time = current_time
                self.last_login_ip = ip_address
                self.login_count += 1
                self.failed_login_count = 0  # 重置失败次数
                self.locked_until = None  # 解除临时锁定

                log_auth_action(
                    username=self.username,
                    action="登录",
                    success=True,
                    details=f"IP={ip_address}, 总登录次数={self.login_count}"
                )
            else:
                # 失败登录
                self.failed_login_count += 1

                # 检查是否需要临时锁定
                if self.failed_login_count >= settings.MAX_LOGIN_ATTEMPTS:
                    from datetime import timedelta
                    self.locked_until = current_time + timedelta(minutes=settings.LOGIN_LOCKOUT_TIME)

                    log_auth_action(
                        username=self.username,
                        action="登录失败",
                        success=False,
                        details=f"连续失败{self.failed_login_count}次，临时锁定至{self.locked_until}"
                    )
                else:
                    log_auth_action(
                        username=self.username,
                        action="登录失败",
                        success=False,
                        details=f"失败次数={self.failed_login_count}"
                    )

            # 保存更改
            self.save()

        except Exception as e:
            log_error("记录登录尝试失败", error=e)

    def get_credit_summary(self) -> Dict[str, Any]:
        """获取积分摘要"""
        return {
            'available': self.available_credits,
            'used': self.used_credits,
            'total': self.total_credits,
            'usage_rate': round(self.used_credits / self.total_credits * 100, 2) if self.total_credits > 0 else 0,
            'can_send_sms': self.available_credits >= 1,  # 短信1积分
            'can_send_mms': self.available_credits >= 3  # 彩信3积分
        }

    def get_login_summary(self) -> Dict[str, Any]:
        """获取登录摘要"""
        return {
            'total_logins': self.login_count,
            'failed_attempts': self.failed_login_count,
            'last_login': self.last_login_time.isoformat() if self.last_login_time else None,
            'last_ip': self.last_login_ip,
            'is_locked': self.is_locked(),
            'locked_until': self.locked_until.isoformat() if self.locked_until else None
        }

    @classmethod
    def find_by_username(cls, username: str) -> Optional['ChannelOperator']:
        """根据用户名查找用户"""
        return cls.find_one("operators_username = %s", (username,))

    @classmethod
    def authenticate(cls, username: str, password: str, mac_address: str = None) -> Optional['ChannelOperator']:
        """用户认证"""
        try:
            # 查找用户
            user = cls.find_by_username(username)
            if not user:
                log_auth_action(username, "认证失败", False, "用户不存在")
                return None

            # 检查用户状态
            if not user.can_login():
                if user.is_locked():
                    log_auth_action(username, "认证失败", False, "用户被锁定")
                else:
                    log_auth_action(username, "认证失败", False, "用户未激活")
                return None

            # 检查密码
            if not user.check_password(password):
                log_auth_action(username, "认证失败", False, "密码错误")
                user.record_login_attempt(False)
                return None

            # 检查MAC地址
            if not user.check_mac_address(mac_address):
                log_auth_action(username, "认证失败", False, "MAC地址不匹配")
                return None

            # 认证成功
            log_auth_action(username, "认证成功", True)
            return user

        except Exception as e:
            log_error("用户认证异常", error=e)
            return None

    @classmethod
    def create_user(cls, username: str, password: str, **kwargs) -> Optional['ChannelOperator']:
        """创建新用户"""
        try:
            # 检查用户名是否已存在
            if cls.find_by_username(username):
                raise ValueError(f"用户名 '{username}' 已存在")

            # 创建用户实例
            user = cls(username=username, **kwargs)
            user.set_password(password)

            # 保存用户
            if user.save():
                log_auth_action(username, "创建用户", True)
                return user

            return None

        except Exception as e:
            log_error("创建用户失败", error=e)
            return None

    def to_dict(self, include_sensitive: bool = False, **kwargs) -> Dict[str, Any]:
        """转换为字典（可选择是否包含敏感信息）"""
        data = super().to_dict(**kwargs)

        # 默认不包含敏感信息
        if not include_sensitive:
            data.pop('password', None)

        return data


@dataclass
class UserAuth:
    """用户认证辅助类"""

    user: Optional[ChannelOperator] = field(default=None)
    is_authenticated: bool = field(default=False)
    login_time: Optional[datetime] = field(default=None)
    session_id: Optional[str] = field(default=None)

    def __post_init__(self):
        """初始化后处理"""
        if self.is_authenticated and self.session_id is None:
            self.session_id = self._generate_session_id()

        if self.is_authenticated and self.login_time is None:
            self.login_time = datetime.now()

    def _generate_session_id(self) -> str:
        """生成会话ID"""
        return str(uuid.uuid4())

    @classmethod
    def login(cls, username: str, password: str, mac_address: str = None, ip_address: str = None) -> 'UserAuth':
        """用户登录"""
        try:
            # 尝试认证
            user = ChannelOperator.authenticate(username, password, mac_address)

            if user:
                # 绑定MAC地址（如果需要）
                if mac_address and not user.mac_address:
                    user.bind_mac_address(mac_address)
                    user.save()

                # 记录登录成功
                user.record_login_attempt(True, ip_address)

                # 创建认证对象
                auth = cls(
                    user=user,
                    is_authenticated=True,
                    login_time=datetime.now()
                )

                return auth
            else:
                # 如果用户存在但认证失败，记录失败尝试
                existing_user = ChannelOperator.find_by_username(username)
                if existing_user:
                    existing_user.record_login_attempt(False, ip_address)

                return cls(is_authenticated=False)

        except Exception as e:
            log_error("用户登录异常", error=e)
            return cls(is_authenticated=False)

    def logout(self):
        """用户登出"""
        if self.is_authenticated and self.user:
            log_auth_action(self.user.username, "登出", True)

        self.user = None
        self.is_authenticated = False
        self.login_time = None
        self.session_id = None

    def is_session_valid(self, max_age_hours: int = 8) -> bool:
        """检查会话是否有效"""
        if not self.is_authenticated or not self.login_time:
            return False

        # 检查会话时长
        from datetime import timedelta
        max_age = timedelta(hours=max_age_hours)

        if datetime.now() - self.login_time > max_age:
            return False

        # 检查用户状态
        if self.user and not self.user.can_login():
            return False

        return True

    def refresh_user_data(self) -> bool:
        """刷新用户数据"""
        if not self.is_authenticated or not self.user:
            return False

        try:
            # 从数据库重新加载用户数据
            fresh_user = ChannelOperator.find_by_id(self.user.id)
            if fresh_user:
                self.user = fresh_user
                return True

            return False

        except Exception as e:
            log_error("刷新用户数据失败", error=e)
            return False

    def get_user_info(self) -> Dict[str, Any]:
        """获取用户信息"""
        if not self.is_authenticated or not self.user:
            return {}

        return {
            'user_id': self.user.id,
            'username': self.user.username,
            'status': self.user.status,
            'credits': self.user.get_credit_summary(),
            'login_info': self.user.get_login_summary(),
            'session_id': self.session_id,
            'login_time': self.login_time.isoformat() if self.login_time else None
        }


# 用户管理器
class ChannelOperatorManager(ModelManager):
    """渠道操作用户管理器"""

    def __init__(self):
        super().__init__(ChannelOperator)

    def get_active_users(self) -> List[ChannelOperator]:
        """获取所有激活用户"""
        return self.filter(status='active')

    def get_locked_users(self) -> List[ChannelOperator]:
        """获取所有被锁定用户"""
        return self.filter(status='locked')

    def search_users(self, keyword: str) -> List[ChannelOperator]:
        """搜索用户"""
        users = self.model_class.find_all(
            "operators_username ILIKE %s OR operators_remark ILIKE %s",
            (f"%{keyword}%", f"%{keyword}%")
        )
        return users

    def get_users_by_channel(self, channel_id: int) -> List[ChannelOperator]:
        """获取指定渠道的用户"""
        return self.filter(channel_id=channel_id)

    def get_low_credit_users(self, threshold: int = 100) -> List[ChannelOperator]:
        """获取低积分用户"""
        users = self.model_class.find_all(
            "operators_available_credits < %s AND operators_status = 'active'",
            (threshold,)
        )
        return users

    def batch_update_credits(self, user_updates: List[Dict[str, Any]]) -> bool:
        """批量更新用户积分（仅限消费记录，充值由后台管理）"""
        try:
            # 准备更新数据 - 只处理消费（减少积分）
            updates = []
            for update in user_updates:
                user_id = update['user_id']
                credit_consumption = update.get('credit_consumption', 0)  # 消费的积分数量

                if credit_consumption <= 0:
                    continue  # 跳过无效的消费记录

                # 获取当前用户信息
                user = self.model_class.find_by_id(user_id)
                if not user or not user.has_sufficient_credits(credit_consumption):
                    continue

                # 计算新的积分值（只能减少）
                new_available = user.available_credits - credit_consumption
                new_used = user.used_credits + credit_consumption

                updates.append({
                    'id': user_id,
                    'operators_available_credits': max(0, new_available),
                    'operators_used_credits': new_used
                })

            # 执行批量更新
            return self.model_class.bulk_update(updates)

        except Exception as e:
            log_error("批量更新用户积分失败", error=e)
            return False


# 全局用户管理器实例
channel_operator_manager = ChannelOperatorManager()