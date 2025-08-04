"""
猫池短信系统业务逻辑层 - tkinter版
Services module for SMS Pool System - tkinter version
"""

from .auth_service import AuthService, auth_service
from .task_service import TaskService, task_service
from .port_service import PortService, port_service
from .message_service import MessageService, message_service
from .credit_service import CreditService, credit_service

__all__ = [
    # 认证服务
    'AuthService',
    'auth_service',

    # 任务管理服务
    'TaskService',
    'task_service',

    # 端口管理服务
    'PortService',
    'port_service',

    # 消息处理服务
    'MessageService',
    'message_service',

    # 积分管理服务
    'CreditService',
    'credit_service'
]

__version__ = '1.0.0'
__author__ = 'SMS Pool System Team'
__description__ = '猫池短信系统业务逻辑服务层'

# 服务启动顺序
SERVICE_STARTUP_ORDER = [
    'auth_service',
    'credit_service',
    'port_service',
    'message_service',
    'task_service'
]


def initialize_all_services():
    """初始化所有服务"""
    services = {
        'auth_service': auth_service,
        'credit_service': credit_service,
        'port_service': port_service,
        'message_service': message_service,
        'task_service': task_service
    }

    results = {}

    for service_name in SERVICE_STARTUP_ORDER:
        try:
            service = services[service_name]
            if hasattr(service, 'initialize') and callable(service.initialize):
                results[service_name] = service.initialize()
            else:
                results[service_name] = True
        except Exception as e:
            print(f"初始化服务 {service_name} 失败: {e}")
            results[service_name] = False

    return results


def shutdown_all_services():
    """关闭所有服务"""
    services = {
        'auth_service': auth_service,
        'credit_service': credit_service,
        'port_service': port_service,
        'message_service': message_service,
        'task_service': task_service
    }

    # 按相反顺序关闭
    for service_name in reversed(SERVICE_STARTUP_ORDER):
        try:
            service = services[service_name]
            if hasattr(service, 'shutdown') and callable(service.shutdown):
                service.shutdown()
        except Exception as e:
            print(f"关闭服务 {service_name} 失败: {e}")


def get_services_status():
    """获取所有服务状态"""
    services = {
        'auth_service': auth_service,
        'credit_service': credit_service,
        'port_service': port_service,
        'message_service': message_service,
        'task_service': task_service
    }

    status = {}

    for service_name, service in services.items():
        try:
            if hasattr(service, 'get_status') and callable(service.get_status):
                status[service_name] = service.get_status()
            else:
                status[service_name] = {'running': True, 'message': '服务正常'}
        except Exception as e:
            status[service_name] = {'running': False, 'message': f'状态获取失败: {e}'}

    return status