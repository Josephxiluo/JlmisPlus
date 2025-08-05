"""
认证服务 - 最小化版本
"""
from typing import Optional, Dict, Any

class AuthService:
    """认证服务"""

    def __init__(self):
        """初始化认证服务"""
        self.initialized = True

    def authenticate_user(self, username: str, password: str, mac_address: str = None) -> Optional[Dict[str, Any]]:
        """用户认证"""
        # 简单的测试认证
        if username == "test_operator" and password == "123456":
            return {
                'operators_id': 1,
                'operators_username': username,
                'operators_real_name': '测试操作员',
                'operators_available_credits': 1000,
                'channel_users_id': 1
            }
        return None

    def validate_mac_address(self, username: str, mac_address: str) -> bool:
        """MAC地址验证"""
        # 开发模式下直接返回True
        return True

# 创建全局实例
auth_service = AuthService()
