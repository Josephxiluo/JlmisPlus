"""
猫池短信系统用户模型 - tkinter版 (增强版)
User models for SMS Pool System - tkinter version (Enhanced)
"""

import sys
import uuid
import hashlib
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from models.base import BaseModel, BaseEntity, ModelValidationError
    from config.logging_config import get_logger
    from database.connection import execute_query, execute_update

    logger = get_logger('models.user')
    DATABASE_AVAILABLE = True

except ImportError as e:
    print(f"警告: 依赖模块导入失败: {e}")
    DATABASE_AVAILABLE = False

    # 创建模拟的基础类
    from dataclasses import dataclass

    class BaseModel:
        def to_dict(self) -> Dict[str, Any]:
            result = {}
            for field_name, value in self.__dict__.items():
                if not field_name.startswith('_'):
                    result[field_name] = value
            return result

    class BaseEntity(BaseModel):
        pass

    class ModelValidationError(Exception):
        pass

    def execute_query(query, params=None, fetch_one=False, dict_cursor=False):
        return None

    def execute_update(query, params=None):
        return 0

    import logging
    logger = logging.getLogger('models.user')


def get_mac_address() -> str:
    """获取当前机器的MAC地址"""
    try:
        mac = uuid.getnode()
        mac_hex = '%012X' % mac
        return ':'.join(mac_hex[i:i+2] for i in range(0, 12, 2))
    except Exception as e:
        logger.error(f"获取MAC地址失败: {e}")
        return "00:00:00:00:00:00"


def normalize_mac_address(mac_address: str) -> str:
    """标准化MAC地址格式"""
    if not mac_address:
        return ""

    # 移除所有非十六进制字符
    clean_mac = ''.join(c for c in mac_address.upper() if c in '0123456789ABCDEF')

    # 确保长度为12位
    if len(clean_mac) != 12:
        return mac_address.upper()

    # 返回标准格式: XX:XX:XX:XX:XX:XX
    return ':'.join(clean_mac[i:i+2] for i in range(0, 12, 2))


def generate_password_hash(password: str, salt: str = 'sms_pool_salt_2024') -> str:
    """生成密码哈希"""
    try:
        password_with_salt = password + salt
        return hashlib.md5(password_with_salt.encode('utf-8')).hexdigest()
    except Exception as e:
        logger.error(f"生成密码哈希失败: {e}")
        return ""


def verify_password_hash(password: str, stored_hash: str, salt: str = 'sms_pool_salt_2024') -> bool:
    """验证密码哈希"""
    try:
        # 如果是明文密码（开发环境）
        if stored_hash == password:
            return True

        # 验证哈希密码
        computed_hash = generate_password_hash(password, salt)
        return computed_hash == stored_hash
    except Exception as e:
        logger.error(f"验证密码哈希失败: {e}")
        return False


@dataclass
class UserAuth:
    """用户认证信息类"""
    username: str = ""
    password_hash: str = ""
    mac_address: str = ""
    last_login_time: Optional[datetime] = None
    last_login_ip: str = ""
    login_attempts: int = 0

    def validate_credentials(self, username: str, password: str) -> bool:
        """验证用户凭据"""
        try:
            if self.username != username:
                return False

            return verify_password_hash(password, self.password_hash)
        except Exception as e:
            logger.error(f"验证用户凭据失败: {e}")
            return False

    def validate_mac_address(self, mac_address: str) -> bool:
        """验证MAC地址"""
        try:
            if not self.mac_address:
                return True  # 如果没有绑定MAC地址，允许访问

            normalized_stored = normalize_mac_address(self.mac_address)
            normalized_current = normalize_mac_address(mac_address)

            return normalized_stored == normalized_current
        except Exception as e:
            logger.error(f"验证MAC地址失败: {e}")
            return False

    def update_login_info(self, ip_address: str = "127.0.0.1"):
        """更新登录信息"""
        try:
            self.last_login_time = datetime.now()
            self.last_login_ip = ip_address
            self.login_attempts = 0
        except Exception as e:
            logger.error(f"更新登录信息失败: {e}")

    def increment_login_attempts(self):
        """增加登录尝试次数"""
        self.login_attempts += 1

    def reset_login_attempts(self):
        """重置登录尝试次数"""
        self.login_attempts = 0


@dataclass
class ChannelOperator(BaseEntity):
    """渠道操作用户模型类"""

    # 数据库字段
    operators_id: Optional[int] = None
    operators_username: str = ""
    operators_password_hash: str = ""
    operators_real_name: str = ""
    channel_users_id: Optional[int] = None
    operators_total_credits: int = 0
    operators_used_credits: int = 0
    operators_daily_limit: int = 0
    operators_mac_address: str = ""
    operators_device_info: Optional[Dict[str, Any]] = None
    operators_status: str = "active"
    operators_last_login_time: Optional[datetime] = None
    operators_last_login_ip: str = ""
    created_by: Optional[int] = None

    # 计算属性不需要存储到数据库
    _table_name: str = field(default="channel_operators", init=False, repr=False)
    _primary_key: str = field(default="operators_id", init=False, repr=False)

    def __post_init__(self):
        """初始化后处理"""
        super().__post_init__()
        self._setup_field_mappings()

        # 初始化设备信息
        if self.operators_device_info is None:
            self.operators_device_info = {}

    def _setup_field_mappings(self):
        """设置字段映射关系"""
        self._field_mappings = {
            'operators_id': 'operators_id',
            'operators_username': 'operators_username',
            'operators_password_hash': 'operators_password_hash',
            'operators_real_name': 'operators_real_name',
            'channel_users_id': 'channel_users_id',
            'operators_total_credits': 'operators_total_credits',
            'operators_used_credits': 'operators_used_credits',
            'operators_daily_limit': 'operators_daily_limit',
            'operators_mac_address': 'operators_mac_address',
            'operators_device_info': 'operators_device_info',
            'operators_status': 'operators_status',
            'operators_last_login_time': 'operators_last_login_time',
            'operators_last_login_ip': 'operators_last_login_ip',
            'created_by': 'created_by',
            'created_time': 'created_time',
            'updated_time': 'updated_time'
        }

    @property
    def operators_available_credits(self) -> int:
        """可用积分（计算属性）"""
        return max(0, self.operators_total_credits - self.operators_used_credits)

    @property
    def id(self) -> Optional[int]:
        """ID别名"""
        return self.operators_id

    @property
    def username(self) -> str:
        """用户名别名"""
        return self.operators_username

    @property
    def real_name(self) -> str:
        """真实姓名别名"""
        return self.operators_real_name

    @property
    def available_credits(self) -> int:
        """可用积分别名"""
        return self.operators_available_credits

    @property
    def total_credits(self) -> int:
        """总积分别名"""
        return self.operators_total_credits

    @property
    def used_credits(self) -> int:
        """已用积分别名"""
        return self.operators_used_credits

    def validate(self) -> bool:
        """验证模型数据"""
        try:
            errors = []

            # 验证用户名
            if not self.operators_username or len(self.operators_username) < 3:
                errors.append("用户名长度不能少于3个字符")

            if len(self.operators_username) > 50:
                errors.append("用户名长度不能超过50个字符")

            # 验证密码哈希
            if not self.operators_password_hash:
                errors.append("密码哈希不能为空")

            # 验证积分
            if self.operators_total_credits < 0:
                errors.append("总积分不能为负数")

            if self.operators_used_credits < 0:
                errors.append("已使用积分不能为负数")

            if self.operators_used_credits > self.operators_total_credits:
                errors.append("已使用积分不能超过总积分")

            # 验证状态
            valid_statuses = ['active', 'inactive', 'suspended']
            if self.operators_status not in valid_statuses:
                errors.append(f"用户状态必须是 {valid_statuses} 之一")

            # 验证MAC地址格式
            if self.operators_mac_address:
                normalized_mac = normalize_mac_address(self.operators_mac_address)
                if len(normalized_mac) != 17:  # XX:XX:XX:XX:XX:XX
                    errors.append("MAC地址格式不正确")

            if errors:
                raise ModelValidationError("; ".join(errors))

            return True

        except Exception as e:
            logger.error(f"用户模型验证失败: {e}")
            raise ModelValidationError(f"用户模型验证失败: {str(e)}")

    def refresh_credits_from_db(self) -> bool:
        """从数据库刷新积分信息"""
        try:
            if not DATABASE_AVAILABLE or not self.operators_id:
                return False

            query = """
            SELECT operators_total_credits, operators_used_credits 
            FROM channel_operators 
            WHERE operators_id = %s
            """

            result = execute_query(query, (self.operators_id,), fetch_one=True)

            if result:
                self.operators_total_credits = result[0]
                self.operators_used_credits = result[1]
                logger.debug(f"用户 {self.operators_username} 积分刷新成功")
                return True

            return False

        except Exception as e:
            logger.error(f"从数据库刷新积分失败: {e}")
            return False

    def consume_credits(self, amount: int, description: str = None) -> bool:
        """消费积分"""
        try:
            if amount <= 0:
                logger.warning("消费积分数量必须大于0")
                return False

            if self.operators_available_credits < amount:
                logger.warning(f"积分不足: 需要{amount}, 可用{self.operators_available_credits}")
                return False

            # 更新本地数据
            old_used = self.operators_used_credits
            self.operators_used_credits += amount

            # 更新数据库
            if DATABASE_AVAILABLE and self.operators_id:
                try:
                    update_query = """
                    UPDATE channel_operators 
                    SET operators_used_credits = %s
                    WHERE operators_id = %s
                    """

                    execute_update(update_query, (self.operators_used_credits, self.operators_id))

                    # 记录积分消费日志
                    self._log_credit_consumption(amount, description)

                except Exception as db_error:
                    # 数据库更新失败，回滚本地更改
                    self.operators_used_credits = old_used
                    logger.error(f"数据库更新失败，积分消费回滚: {db_error}")
                    return False

            logger.info(f"用户 {self.operators_username} 消费积分 {amount}，余额: {self.operators_available_credits}")
            return True

        except Exception as e:
            logger.error(f"消费积分失败: {e}")
            return False

    def has_sufficient_credits(self, amount: int) -> bool:
        """检查积分是否充足"""
        return self.operators_available_credits >= amount

    # 注意：渠道操作用户端不包含充值功能，充值由渠道管理员或总管理员处理

    def _log_credit_consumption(self, amount: int, description: str = None):
        """记录积分消费日志"""
        try:
            if not DATABASE_AVAILABLE:
                return

            log_query = """
            INSERT INTO operator_credit_logs 
            (operators_id, channel_users_id, change_type, change_amount, 
             before_balance, after_balance, operator_type, description)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """

            before_balance = self.operators_available_credits + amount
            after_balance = self.operators_available_credits

            execute_update(log_query, (
                self.operators_id,
                self.channel_users_id,
                'consume',
                -amount,
                before_balance,
                after_balance,
                'system',
                description or '系统消费'
            ))

        except Exception as e:
            logger.warning(f"记录积分消费日志失败: {e}")

    # 注意：渠道操作用户端不包含充值日志功能

    def get_credit_summary(self) -> Dict[str, Any]:
        """获取积分汇总信息"""
        return {
            'total': self.operators_total_credits,
            'used': self.operators_used_credits,
            'available': self.operators_available_credits,
            'usage_rate': round(self.operators_used_credits / max(self.operators_total_credits, 1) * 100, 2),
            'can_send_sms': self.operators_available_credits >= 1,
            'can_send_mms': self.operators_available_credits >= 3
        }

    def update_mac_address(self, mac_address: str) -> bool:
        """更新MAC地址"""
        try:
            normalized_mac = normalize_mac_address(mac_address)
            if not normalized_mac:
                logger.warning("MAC地址格式不正确")
                return False

            old_mac = self.operators_mac_address
            self.operators_mac_address = normalized_mac

            # 更新数据库
            if DATABASE_AVAILABLE and self.operators_id:
                try:
                    update_query = """
                    UPDATE channel_operators 
                    SET operators_mac_address = %s
                    WHERE operators_id = %s
                    """

                    execute_update(update_query, (normalized_mac, self.operators_id))

                except Exception as db_error:
                    # 数据库更新失败，回滚本地更改
                    self.operators_mac_address = old_mac
                    logger.error(f"数据库更新失败，MAC地址更新回滚: {db_error}")
                    return False

            logger.info(f"用户 {self.operators_username} MAC地址更新: {old_mac} -> {normalized_mac}")
            return True

        except Exception as e:
            logger.error(f"更新MAC地址失败: {e}")
            return False

    def update_device_info(self, device_info: Dict[str, Any]) -> bool:
        """更新设备信息"""
        try:
            import json

            old_info = self.operators_device_info.copy() if self.operators_device_info else {}
            self.operators_device_info = device_info

            # 更新数据库
            if DATABASE_AVAILABLE and self.operators_id:
                try:
                    update_query = """
                    UPDATE channel_operators 
                    SET operators_device_info = %s
                    WHERE operators_id = %s
                    """

                    execute_update(update_query, (json.dumps(device_info, ensure_ascii=False), self.operators_id))

                except Exception as db_error:
                    # 数据库更新失败，回滚本地更改
                    self.operators_device_info = old_info
                    logger.error(f"数据库更新失败，设备信息更新回滚: {db_error}")
                    return False

            logger.info(f"用户 {self.operators_username} 设备信息已更新")
            return True

        except Exception as e:
            logger.error(f"更新设备信息失败: {e}")
            return False

    def update_last_login(self, ip_address: str = "127.0.0.1") -> bool:
        """更新最后登录信息"""
        try:
            self.operators_last_login_time = datetime.now()
            self.operators_last_login_ip = ip_address

            # 更新数据库
            if DATABASE_AVAILABLE and self.operators_id:
                try:
                    update_query = """
                    UPDATE channel_operators 
                    SET operators_last_login_time = CURRENT_TIMESTAMP,
                        operators_last_login_ip = %s
                    WHERE operators_id = %s
                    """

                    execute_update(update_query, (ip_address, self.operators_id))

                except Exception as db_error:
                    logger.error(f"更新最后登录信息失败: {db_error}")
                    return False

            logger.debug(f"用户 {self.operators_username} 登录信息已更新")
            return True

        except Exception as e:
            logger.error(f"更新最后登录信息失败: {e}")
            return False

    def is_active(self) -> bool:
        """检查用户是否为活跃状态"""
        return self.operators_status.lower() == 'active'

    def is_mac_authorized(self, mac_address: str) -> bool:
        """检查MAC地址是否已授权"""
        try:
            if not self.operators_mac_address:
                return True  # 没有绑定MAC地址，允许访问

            normalized_stored = normalize_mac_address(self.operators_mac_address)
            normalized_current = normalize_mac_address(mac_address)

            return normalized_stored == normalized_current
        except Exception as e:
            logger.error(f"检查MAC地址授权失败: {e}")
            return False

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典，包含计算属性"""
        result = super().to_dict()
        result['operators_available_credits'] = self.operators_available_credits
        return result

    @classmethod
    def get_by_username(cls, username: str) -> Optional['ChannelOperator']:
        """根据用户名获取用户"""
        try:
            if not DATABASE_AVAILABLE:
                return None

            query = """
            SELECT * FROM channel_operators 
            WHERE operators_username = %s
            """

            result = execute_query(query, (username,), fetch_one=True, dict_cursor=True)

            if result:
                operator = cls()
                return operator.from_db_dict(dict(result))

            return None

        except Exception as e:
            logger.error(f"根据用户名获取用户失败: {e}")
            return None

    @classmethod
    def get_by_id(cls, operator_id: int) -> Optional['ChannelOperator']:
        """根据ID获取用户"""
        try:
            if not DATABASE_AVAILABLE:
                return None

            query = """
            SELECT * FROM channel_operators 
            WHERE operators_id = %s
            """

            result = execute_query(query, (operator_id,), fetch_one=True, dict_cursor=True)

            if result:
                operator = cls()
                return operator.from_db_dict(dict(result))

            return None

        except Exception as e:
            logger.error(f"根据ID获取用户失败: {e}")
            return None

    @classmethod
    def create_new_user(cls, username: str, password: str, real_name: str,
                       channel_users_id: int, created_by: int) -> Optional['ChannelOperator']:
        """创建新用户"""
        try:
            if not DATABASE_AVAILABLE:
                return None

            # 生成密码哈希
            password_hash = generate_password_hash(password)

            # 创建用户对象
            operator = cls(
                operators_username=username,
                operators_password_hash=password_hash,
                operators_real_name=real_name,
                channel_users_id=channel_users_id,
                created_by=created_by
            )

            # 验证数据
            operator.validate()

            # 保存到数据库
            create_sql, create_params = operator.get_create_sql()
            result = execute_query(create_sql, create_params, fetch_one=True)

            if result and result[0]:
                operator.operators_id = result[0]
                logger.info(f"新用户 {username} 创建成功，ID: {operator.operators_id}")
                return operator

            return None

        except Exception as e:
            logger.error(f"创建新用户失败: {e}")
            return None


# 便捷函数
def get_current_mac_address() -> str:
    """获取当前机器MAC地址的便捷函数"""
    return get_mac_address()


def normalize_mac(mac_address: str) -> str:
    """标准化MAC地址的便捷函数"""
    return normalize_mac_address(mac_address)


def hash_password(password: str, salt: str = 'sms_pool_salt_2024') -> str:
    """密码哈希的便捷函数"""
    return generate_password_hash(password, salt)


def verify_password(password: str, stored_hash: str, salt: str = 'sms_pool_salt_2024') -> bool:
    """密码验证的便捷函数"""
    return verify_password_hash(password, stored_hash, salt)


def authenticate_operator(username: str, password: str, mac_address: str = None) -> Optional[ChannelOperator]:
    """操作用户认证的便捷函数"""
    try:
        # 获取当前MAC地址
        if not mac_address:
            mac_address = get_mac_address()

        # 从数据库获取用户
        operator = ChannelOperator.get_by_username(username)
        if not operator:
            logger.warning(f"用户 {username} 不存在")
            return None

        # 验证密码
        if not verify_password_hash(password, operator.operators_password_hash):
            logger.warning(f"用户 {username} 密码验证失败")
            return None

        # 验证用户状态
        if not operator.is_active():
            logger.warning(f"用户 {username} 状态不活跃: {operator.operators_status}")
            return None

        # 验证MAC地址
        if not operator.is_mac_authorized(mac_address):
            logger.warning(f"用户 {username} MAC地址未授权: {mac_address}")
            return None

        # 更新登录信息
        operator.update_last_login()

        logger.info(f"用户 {username} 认证成功")
        return operator

    except Exception as e:
        logger.error(f"操作用户认证失败: {e}")
        return None