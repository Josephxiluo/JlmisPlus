"""
猫池短信系统数据模型层 - tkinter版
Data models module for SMS Pool System - tkinter version
"""

from .base import BaseModel, ModelValidationError, ModelNotFoundError
from .user import ChannelOperator, UserAuth
from .task import Task, TaskStatus, TaskMode
from .message import TaskMessage, MessageStatus, MessageCarrier
from .port import Port, PortStatus, PortCarrier

__all__ = [
    # 基础模型
    'BaseModel',
    'ModelValidationError',
    'ModelNotFoundError',

    # 用户模型
    'ChannelOperator',
    'UserAuth',

    # 任务模型
    'Task',
    'TaskStatus',
    'TaskMode',

    # 消息模型
    'TaskMessage',
    'MessageStatus',
    'MessageCarrier',

    # 端口模型
    'Port',
    'PortStatus',
    'PortCarrier'
]

__version__ = '1.0.0'
__author__ = 'SMS Pool System Team'
__description__ = '猫池短信系统数据模型层'