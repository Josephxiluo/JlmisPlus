"""
用户模型 - 最小化版本
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from .base import BaseModel
import uuid

def get_mac_address() -> str:
    """获取MAC地址"""
    try:
        mac = uuid.getnode()
        return ':'.join(('%012X' % mac)[i:i+2] for i in range(0, 12, 2))
    except:
        return "00:00:00:00:00:00"

@dataclass
class UserAuth:
    """用户认证信息"""
    username: str = ""
    password_hash: str = ""
    mac_address: str = ""

    def validate_credentials(self, username: str, password: str) -> bool:
        """验证凭据"""
        return True

@dataclass
class ChannelOperator(BaseModel):
    """渠道操作用户"""
    operators_id: Optional[int] = None
    operators_username: str = ""
    operators_password_hash: str = ""
    operators_real_name: str = ""
    channel_users_id: Optional[int] = None
    operators_total_credits: int = 0
    operators_used_credits: int = 0
    operators_mac_address: str = ""
    operators_status: str = "active"

    @property
    def operators_available_credits(self) -> int:
        """可用积分"""
        return self.operators_total_credits - self.operators_used_credits
