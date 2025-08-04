"""
猫池短信系统核心功能模块 - tkinter版
Core functionality module for SMS Pool System - tkinter version
"""

from .port_scanner import PortScanner, port_scanner
from .task_executor import TaskExecutor, task_executor
from .message_sender import MessageSender, message_sender
from .monitor_detector import MonitorDetector, monitor_detector
from .file_handler import FileHandler, file_handler
from .utils import (
    # 时间工具
    format_datetime,
    format_duration,
    get_current_timestamp,

    # 字符串工具
    mask_phone_number,
    validate_phone_number,
    clean_phone_number,

    # 文件工具
    ensure_directory,
    get_file_size,
    get_file_extension,

    # 数据工具
    calculate_percentage,
    format_file_size,
    generate_unique_id,

    # 验证工具
    is_valid_port_name,
    is_valid_baud_rate,

    # 转换工具
    bytes_to_str,
    str_to_bytes,

    # 网络工具
    get_local_ip,
    get_mac_address,

    # 系统工具
    get_system_info,
    get_memory_usage,

    # 配置工具
    load_json_config,
    save_json_config,

    # 安全工具
    generate_hash,
    verify_hash
)

__all__ = [
    # 核心组件
    'PortScanner',
    'port_scanner',
    'TaskExecutor',
    'task_executor',
    'MessageSender',
    'message_sender',
    'MonitorDetector',
    'monitor_detector',
    'FileHandler',
    'file_handler',

    # 工具函数
    'format_datetime',
    'format_duration',
    'get_current_timestamp',
    'mask_phone_number',
    'validate_phone_number',
    'clean_phone_number',
    'ensure_directory',
    'get_file_size',
    'get_file_extension',
    'calculate_percentage',
    'format_file_size',
    'generate_unique_id',
    'is_valid_port_name',
    'is_valid_baud_rate',
    'bytes_to_str',
    'str_to_bytes',
    'get_local_ip',
    'get_mac_address',
    'get_system_info',
    'get_memory_usage',
    'load_json_config',
    'save_json_config',
    'generate_hash',
    'verify_hash'
]

__version__ = '1.0.0'
__author__ = 'SMS Pool System Team'
__description__ = '猫池短信系统核心功能模块'

# 核心组件启动顺序
CORE_STARTUP_ORDER = [
    'port_scanner',
    'message_sender',
    'monitor_detector',
    'file_handler',
    'task_executor'
]

def initialize_core_components():
    """初始化所有核心组件"""
    components = {
        'port_scanner': port_scanner,
        'message_sender': message_sender,
        'monitor_detector': monitor_detector,
        'file_handler': file_handler,
        'task_executor': task_executor
    }

    results = {}

    for component_name in CORE_STARTUP_ORDER:
        try:
            component = components[component_name]
            if hasattr(component, 'initialize') and callable(component.initialize):
                results[component_name] = component.initialize()
            else:
                results[component_name] = True
        except Exception as e:
            print(f"初始化核心组件 {component_name} 失败: {e}")
            results[component_name] = False

    return results

def shutdown_core_components():
    """关闭所有核心组件"""
    components = {
        'port_scanner': port_scanner,
        'message_sender': message_sender,
        'monitor_detector': monitor_detector,
        'file_handler': file_handler,
        'task_executor': task_executor
    }

    # 按相反顺序关闭
    for component_name in reversed(CORE_STARTUP_ORDER):
        try:
            component = components[component_name]
            if hasattr(component, 'shutdown') and callable(component.shutdown):
                component.shutdown()
        except Exception as e:
            print(f"关闭核心组件 {component_name} 失败: {e}")

def get_core_components_status():
    """获取所有核心组件状态"""
    components = {
        'port_scanner': port_scanner,
        'message_sender': message_sender,
        'monitor_detector': monitor_detector,
        'file_handler': file_handler,
        'task_executor': task_executor
    }

    status = {}

    for component_name, component in components.items():
        try:
            if hasattr(component, 'get_status') and callable(component.get_status):
                status[component_name] = component.get_status()
            else:
                status[component_name] = {'running': True, 'message': '组件正常'}
        except Exception as e:
            status[component_name] = {'running': False, 'message': f'状态获取失败: {e}'}

    return status