"""
猫池短信系统数据模型模块 - tkinter版 (修复版)
Data models module for SMS Pool System - tkinter version (Fixed)
"""

from .base import (
    BaseModel,
    BaseEntity,
    TimestampMixin,
    ModelValidationError,
    ModelNotFoundError,
    DatabaseError,
    validate_required_fields,
    validate_field_length,
    validate_field_type,
    validate_field_range,
    safe_convert_type,
    apply_common_validation,
    COMMON_VALIDATIONS
)

# 延迟导入其他模型，避免循环导入
def get_user_models():
    """获取用户相关模型"""
    try:
        from .user import ChannelOperator, UserAuth, get_mac_address
        return ChannelOperator, UserAuth, get_mac_address
    except ImportError as e:
        print(f"警告: 无法导入用户模型: {e}")
        return None, None, None

def get_task_models():
    """获取任务相关模型"""
    try:
        from .task import Task, TaskStatus, TaskMode
        return Task, TaskStatus, TaskMode
    except ImportError as e:
        print(f"警告: 无法导入任务模型: {e}")
        return None, None, None

def get_message_models():
    """获取消息相关模型"""
    try:
        from .message import MessageDetail, MessageStatus, MessageType
        return MessageDetail, MessageStatus, MessageType
    except ImportError as e:
        print(f"警告: 无法导入消息模型: {e}")
        return None, None, None

def get_port_models():
    """获取端口相关模型"""
    try:
        from .port import PortDevice, PortStatus, OperatorType
        return PortDevice, PortStatus, OperatorType
    except ImportError as e:
        print(f"警告: 无法导入端口模型: {e}")
        return None, None, None

__all__ = [
    # 基础模型和异常
    'BaseModel',
    'BaseEntity',
    'TimestampMixin',
    'ModelValidationError',
    'ModelNotFoundError',
    'DatabaseError',

    # 验证函数
    'validate_required_fields',
    'validate_field_length',
    'validate_field_type',
    'validate_field_range',
    'safe_convert_type',
    'apply_common_validation',
    'COMMON_VALIDATIONS',

    # 模型获取函数
    'get_user_models',
    'get_task_models',
    'get_message_models',
    'get_port_models'
]

__version__ = '1.0.0'
__author__ = 'SMS Pool System Team'
__description__ = '猫池短信系统数据模型模块'