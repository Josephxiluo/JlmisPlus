"""
猫池短信系统认证服务 - tkinter版 (完整版)
Authentication service for SMS Pool System - tkinter version (Complete)
"""

import sys
import hashlib
import uuid
import threading
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from database.connection import get_db_connection, execute_query
    from config.settings import settings
    from config.logging_config import get_logger, log_user_action
    from models.user import ChannelOperator, UserAuth, get_mac_address
except ImportError as e:
    print(f"导入模块失败: {e}")
    # 创建模拟的依赖项
    def get_db_connection():
        return None

    def execute_query(query, params=None, fetch_one=False, dict_cursor=False):
        return None

    class MockSettings:
        SKIP_MAC_VERIFICATION = True
        DEBUG = True
        PASSWORD_SALT = 'sms_pool_salt_2024'

    settings = MockSettings()

    import logging
    def get_logger(name='auth'):
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    def log_user_action(username, action, details=None, success=True):
        logger = get_logger()
        status = "成功" if success else "失败"
        message = f"[用户操作] {username} {action} {status}"
        if details:
            message += f" - {details}"
        logger.info(message)

    class ChannelOperator:
        def __init__(self):
            self.operators_id = None
            self.operators_username = ""
            self.operators_password_hash = ""
            self.operators_real_name = ""
            self.channel_users_id = None
            self.operators_total_credits = 0
            self.operators_used_credits = 0
            self.operators_mac_address = ""
            self.operators_status = "active"

    def get_mac_address():
        try:
            mac = uuid.getnode()
            return ':'.join(('%012X' % mac)[i:i+2] for i in range(0, 12, 2))
        except:
            return "00:00:00:00:00:00"

logger = get_logger('services.auth')


class AuthService:
    """认证服务类 - 处理用户登录验证和MAC地址验证"""

    def __init__(self):
        """初始化认证服务"""
        self._lock = threading.Lock()
        self.current_user: Optional[ChannelOperator] = None
        self.is_initialized = False

        # 从配置获取设置
        self.skip_mac_verification = getattr(settings, 'SKIP_MAC_VERIFICATION', False)
        self.debug_mode = getattr(settings, 'DEBUG', False)
        self.password_salt = getattr(settings, 'PASSWORD_SALT', 'sms_pool_salt_2024')

    def initialize(self) -> bool:
        """初始化认证服务"""
        try:
            logger.info("认证服务初始化开始")

            # 测试数据库连接
            db = get_db_connection()
            if db and db.test_connection():
                logger.info("数据库连接测试成功")
            else:
                logger.warning("数据库连接测试失败，认证服务将以模拟模式运行")

            self.is_initialized = True
            logger.info("认证服务初始化完成")
            return True

        except Exception as e:
            logger.error(f"认证服务初始化失败: {e}")
            return False

    def shutdown(self):
        """关闭认证服务"""
        try:
            logger.info("认证服务开始关闭")
            self.current_user = None
            self.is_initialized = False
            logger.info("认证服务关闭完成")
        except Exception as e:
            logger.error(f"认证服务关闭失败: {e}")

    def get_status(self) -> Dict[str, Any]:
        """获取认证服务状态"""
        return {
            'running': self.is_initialized,
            'current_user': self.current_user.operators_username if self.current_user else None,
            'skip_mac_verification': self.skip_mac_verification,
            'debug_mode': self.debug_mode,
            'message': '认证服务正常运行' if self.is_initialized else '认证服务未初始化'
        }

    def authenticate_user(self, username: str, password: str, mac_address: str = None) -> Dict[str, Any]:
        """
        用户认证主函数

        Args:
            username: 用户名
            password: 密码
            mac_address: MAC地址（可选，如果不提供会自动获取）

        Returns:
            Dict containing authentication result
        """
        try:
            with self._lock:
                # 参数验证
                if not username or not password:
                    return self._create_auth_result(False, "用户名或密码不能为空", "EMPTY_CREDENTIALS")

                # 获取MAC地址
                if not mac_address:
                    mac_address = get_mac_address()

                logger.info(f"当前机器MAC地址: {mac_address}")

                # 第一步：验证用户名和密码
                user_result = self._verify_user_credentials(username, password)
                if not user_result['success']:
                    log_user_action(username, "登录验证", user_result['message'], False)
                    return user_result

                user_data = user_result['user_data']

                # 第二步：验证MAC地址（如果启用）
                if not self.skip_mac_verification and not self.debug_mode:
                    mac_result = self._verify_mac_address(user_data, mac_address)
                    if not mac_result['success']:
                        log_user_action(username, "MAC地址验证", mac_result['message'], False)
                        return mac_result
                else:
                    logger.info("MAC地址验证已跳过（开发模式或已禁用）")

                # 第三步：检查用户状态
                status_result = self._check_user_status(user_data)
                if not status_result['success']:
                    log_user_action(username, "用户状态检查", status_result['message'], False)
                    return status_result

                # 认证成功，创建用户对象
                channel_operator = self._create_channel_operator_from_data(user_data)
                self.current_user = channel_operator

                # 更新最后登录信息
                self._update_last_login_info(user_data['operators_id'], mac_address)

                # 记录成功日志
                log_user_action(
                    username,
                    "登录成功",
                    f"MAC: {mac_address}, 余额: {channel_operator.operators_available_credits}",
                    True
                )

                logger.info(f"用户 {username} 认证成功")

                return self._create_auth_result(
                    True,
                    "登录成功",
                    "SUCCESS",
                    channel_operator.to_dict()
                )

        except Exception as e:
            logger.error(f"用户认证过程中发生异常: {e}")
            log_user_action(username, "登录异常", str(e), False)
            return self._create_auth_result(False, f"认证过程发生异常: {str(e)}", "SYSTEM_ERROR")

    def _verify_user_credentials(self, username: str, password: str) -> Dict[str, Any]:
        """验证用户名和密码"""
        try:
            # 查询用户信息
            query = """
            SELECT 
                operators_id,
                operators_username,
                operators_password_hash,
                operators_real_name,
                channel_users_id,
                operators_total_credits,
                operators_used_credits,
                operators_mac_address,
                operators_status,
                created_time,
                updated_time
            FROM channel_operators 
            WHERE operators_username = %s
            """

            result = execute_query(query, (username,), fetch_one=True, dict_cursor=True)

            if not result:
                logger.warning(f"用户 {username} 不存在")
                return self._create_auth_result(False, "用户名不存在", "INVALID_CREDENTIALS")

            # 验证密码
            stored_password_hash = result['operators_password_hash']
            if not self._verify_password(password, stored_password_hash):
                logger.warning(f"用户 {username} 密码验证失败")
                return self._create_auth_result(False, "用户名或密码错误", "INVALID_CREDENTIALS")

            logger.info(f"用户 {username} 密码验证成功")
            return {
                'success': True,
                'message': '用户名密码验证成功',
                'user_data': dict(result)
            }

        except Exception as e:
            logger.error(f"验证用户凭据时发生异常: {e}")
            return self._create_auth_result(False, f"数据库查询失败: {str(e)}", "DATABASE_ERROR")

    def _verify_mac_address(self, user_data: Dict[str, Any], current_mac: str) -> Dict[str, Any]:
        """验证MAC地址"""
        try:
            stored_mac = user_data.get('operators_mac_address')

            # 如果数据库中没有存储MAC地址，则允许登录并更新
            if not stored_mac:
                logger.info(f"用户 {user_data['operators_username']} 首次登录，自动绑定MAC地址: {current_mac}")
                self._update_user_mac_address(user_data['operators_id'], current_mac)
                return {'success': True, 'message': 'MAC地址已自动绑定'}

            # 比较MAC地址（忽略大小写和分隔符）
            if self._normalize_mac_address(stored_mac) == self._normalize_mac_address(current_mac):
                logger.info(f"用户 {user_data['operators_username']} MAC地址验证成功")
                return {'success': True, 'message': 'MAC地址验证成功'}
            else:
                logger.warning(f"用户 {user_data['operators_username']} MAC地址验证失败: 存储={stored_mac}, 当前={current_mac}")
                return self._create_auth_result(
                    False,
                    f"设备未授权，请联系管理员\n当前设备MAC: {current_mac}\n授权设备MAC: {stored_mac}",
                    "MAC_ADDRESS_NOT_AUTHORIZED"
                )

        except Exception as e:
            logger.error(f"验证MAC地址时发生异常: {e}")
            return self._create_auth_result(False, f"MAC地址验证失败: {str(e)}", "MAC_VERIFICATION_ERROR")

    def _check_user_status(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """检查用户状态"""
        try:
            status = user_data.get('operators_status', '').lower()
            username = user_data.get('operators_username', '')

            if status == 'active':
                return {'success': True, 'message': '用户状态正常'}
            elif status == 'inactive':
                return self._create_auth_result(False, "账户已被禁用，请联系管理员", "ACCOUNT_DISABLED")
            elif status == 'suspended':
                return self._create_auth_result(False, "账户已被暂停，请联系管理员", "ACCOUNT_SUSPENDED")
            else:
                return self._create_auth_result(False, f"账户状态异常: {status}", "INVALID_STATUS")

        except Exception as e:
            logger.error(f"检查用户状态时发生异常: {e}")
            return self._create_auth_result(False, f"用户状态检查失败: {str(e)}", "STATUS_CHECK_ERROR")

    def _create_channel_operator_from_data(self, user_data: Dict[str, Any]) -> ChannelOperator:
        """从数据库数据创建ChannelOperator对象"""
        operator = ChannelOperator()
        operator.operators_id = user_data.get('operators_id')
        operator.operators_username = user_data.get('operators_username', '')
        operator.operators_password_hash = user_data.get('operators_password_hash', '')
        operator.operators_real_name = user_data.get('operators_real_name', '')
        operator.channel_users_id = user_data.get('channel_users_id')
        operator.operators_total_credits = user_data.get('operators_total_credits', 0)
        operator.operators_used_credits = user_data.get('operators_used_credits', 0)
        operator.operators_mac_address = user_data.get('operators_mac_address', '')
        operator.operators_status = user_data.get('operators_status', 'active')

        return operator

    def _update_last_login_info(self, operator_id: int, mac_address: str):
        """更新用户最后登录信息"""
        try:
            from database.connection import execute_update

            # 获取客户端IP（简化处理）
            client_ip = "127.0.0.1"  # 在实际环境中可以获取真实IP

            update_query = """
            UPDATE channel_operators 
            SET 
                operators_last_login_time = CURRENT_TIMESTAMP,
                operators_last_login_ip = %s
            WHERE operators_id = %s
            """

            execute_update(update_query, (client_ip, operator_id))

            # 记录登录日志
            from database.connection import execute_update as insert_log
            log_query = """
            INSERT INTO user_login_logs 
            (user_type, user_id, username, login_ip, login_result, login_time)
            VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            """

            try:
                insert_log(log_query, (
                    'channel_operator',
                    operator_id,
                    self.current_user.operators_username if self.current_user else '',
                    client_ip,
                    'success'
                ))
            except Exception as e:
                logger.warning(f"记录登录日志失败: {e}")

        except Exception as e:
            logger.warning(f"更新最后登录信息失败: {e}")

    def _update_user_mac_address(self, operator_id: int, mac_address: str):
        """更新用户MAC地址"""
        try:
            from database.connection import execute_update

            update_query = """
            UPDATE channel_operators 
            SET operators_mac_address = %s
            WHERE operators_id = %s
            """

            execute_update(update_query, (mac_address, operator_id))
            logger.info(f"已为用户ID {operator_id} 绑定MAC地址: {mac_address}")

        except Exception as e:
            logger.error(f"更新用户MAC地址失败: {e}")

    def _verify_password(self, password: str, stored_hash: str) -> bool:
        """验证密码"""
        print(stored_hash)
        print(password)
        try:
            # 如果存储的是明文密码（开发/测试环境）
            if stored_hash == password:
                return True

            # 如果是哈希密码，进行哈希验证
            if stored_hash.startswith('$2b$') or stored_hash.startswith('$2a$'):
                # bcrypt格式
                try:
                    import bcrypt
                    return bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
                except ImportError:
                    logger.warning("bcrypt库未安装，使用简单哈希验证")
                    return False
            else:
                # 简单哈希验证（MD5 + Salt）
                password_with_salt = password + self.password_salt
                hashed = hashlib.md5(password_with_salt.encode('utf-8')).hexdigest()
                return hashed == stored_hash

        except Exception as e:
            logger.error(f"密码验证过程中发生异常: {e}")
            return False

    def _normalize_mac_address(self, mac_address: str) -> str:
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

    def _create_auth_result(self, success: bool, message: str, error_code: str = None, user_data: Dict = None) -> Dict[str, Any]:
        """创建认证结果"""
        result = {
            'success': success,
            'message': message,
            'timestamp': self._get_current_timestamp()
        }

        if error_code:
            result['error_code'] = error_code

        if user_data:
            result['user_data'] = user_data

        return result

    def _get_current_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()

    def logout_current_user(self) -> bool:
        """注销当前用户"""
        try:
            if self.current_user:
                username = self.current_user.operators_username
                log_user_action(username, "注销", success=True)
                logger.info(f"用户 {username} 已注销")
                self.current_user = None
                return True
            return False
        except Exception as e:
            logger.error(f"注销用户失败: {e}")
            return False

    def get_current_user(self) -> Optional[ChannelOperator]:
        """获取当前登录用户"""
        return self.current_user

    def is_user_logged_in(self) -> bool:
        """检查是否有用户登录"""
        return self.current_user is not None

    def validate_mac_address(self, username: str, mac_address: str) -> Dict[str, Any]:
        """独立的MAC地址验证方法"""
        try:
            if self.skip_mac_verification or self.debug_mode:
                return {'valid': True, 'message': 'MAC验证已跳过（开发模式）'}

            # 查询用户的MAC地址
            query = "SELECT operators_mac_address FROM channel_operators WHERE operators_username = %s"
            result = execute_query(query, (username,), fetch_one=True)

            if not result:
                return {'valid': False, 'message': '用户不存在'}

            stored_mac = result[0] if isinstance(result, tuple) else result.get('operators_mac_address')

            if not stored_mac:
                return {'valid': True, 'message': '首次登录，MAC地址将自动绑定'}

            if self._normalize_mac_address(stored_mac) == self._normalize_mac_address(mac_address):
                return {'valid': True, 'message': 'MAC地址验证成功'}
            else:
                return {
                    'valid': False,
                    'message': f'设备未授权\n当前: {mac_address}\n授权: {stored_mac}'
                }

        except Exception as e:
            logger.error(f"MAC地址验证异常: {e}")
            return {'valid': False, 'message': f'验证失败: {str(e)}'}


# 创建全局认证服务实例
auth_service = AuthService()


# 便捷函数
def authenticate_user(username: str, password: str, mac_address: str = None) -> Dict[str, Any]:
    """便捷的用户认证函数"""
    return auth_service.authenticate_user(username, password, mac_address)


def get_current_user() -> Optional[ChannelOperator]:
    """获取当前登录用户"""
    return auth_service.get_current_user()


def logout_current_user() -> bool:
    """注销当前用户"""
    return auth_service.logout_current_user()


def is_user_logged_in() -> bool:
    """检查是否有用户登录"""
    return auth_service.is_user_logged_in()


def validate_mac_address(username: str, mac_address: str = None) -> Dict[str, Any]:
    """验证MAC地址"""
    if not mac_address:
        mac_address = get_mac_address()
    return auth_service.validate_mac_address(username, mac_address)