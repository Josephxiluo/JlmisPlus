"""
猫池短信系统业务逻辑层 - tkinter版
Services module for SMS Pool System - tkinter version
"""

import sys
import time
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 延迟导入服务，避免循环导入
_services = {}
_service_instances = {}
_initialized = False

# 服务启动顺序
SERVICE_STARTUP_ORDER = [
    'auth_service',
    'credit_service',
    'port_service',
    'message_service',
    'task_service'
]

# 服务模块映射
SERVICE_MODULES = {
    'auth_service': 'services.auth_service',
    'credit_service': 'services.credit_service',
    'port_service': 'services.port_service',
    'message_service': 'services.message_service',
    'task_service': 'services.task_service'
}


def _import_service(service_name: str):
    """安全导入服务"""
    try:
        if service_name not in _services:
            module_path = SERVICE_MODULES[service_name]
            module = __import__(module_path, fromlist=[service_name])
            _services[service_name] = getattr(module, service_name)
        return _services[service_name]
    except ImportError as e:
        print(f"导入服务 {service_name} 失败: {e}")
        return None
    except AttributeError as e:
        print(f"服务 {service_name} 不存在于模块中: {e}")
        return None


def get_service(service_name: str):
    """获取服务实例"""
    if service_name not in _service_instances:
        service_class = _import_service(service_name)
        if service_class:
            _service_instances[service_name] = service_class
    return _service_instances.get(service_name)


def initialize_all_services() -> Dict[str, bool]:
    """初始化所有服务"""
    global _initialized

    if _initialized:
        return {name: True for name in SERVICE_STARTUP_ORDER}

    results = {}

    # 按顺序初始化服务
    for service_name in SERVICE_STARTUP_ORDER:
        try:
            print(f"正在初始化服务: {service_name}")

            service = get_service(service_name)
            if service is None:
                results[service_name] = False
                print(f"服务 {service_name} 导入失败")
                continue

            # 检查是否有初始化方法
            if hasattr(service, 'initialize') and callable(service.initialize):
                result = service.initialize()
                results[service_name] = result
                if result:
                    print(f"服务 {service_name} 初始化成功")
                else:
                    print(f"服务 {service_name} 初始化失败")
            else:
                results[service_name] = True
                print(f"服务 {service_name} 无需初始化")

            # 给每个服务一点启动时间
            time.sleep(0.1)

        except Exception as e:
            print(f"初始化服务 {service_name} 时出现异常: {e}")
            results[service_name] = False

    # 检查依赖关系
    _check_service_dependencies(results)

    _initialized = True
    return results


def _check_service_dependencies(results: Dict[str, bool]):
    """检查服务依赖关系"""
    # 认证服务是基础，其他服务依赖它
    if not results.get('auth_service', False):
        print("警告: 认证服务初始化失败，其他服务可能无法正常工作")

    # 端口服务和消息服务相互依赖
    if not results.get('port_service', False):
        print("警告: 端口服务初始化失败，消息发送功能将不可用")

    # 任务服务依赖消息服务
    if not results.get('message_service', False) and results.get('task_service', False):
        print("警告: 消息服务初始化失败，任务服务功能将受限")


def shutdown_all_services():
    """关闭所有服务"""
    global _initialized

    if not _initialized:
        return

    # 按相反顺序关闭服务
    for service_name in reversed(SERVICE_STARTUP_ORDER):
        try:
            print(f"正在关闭服务: {service_name}")

            service = _service_instances.get(service_name)
            if service and hasattr(service, 'shutdown') and callable(service.shutdown):
                service.shutdown()
                print(f"服务 {service_name} 关闭成功")

            # 给每个服务一点时间完成关闭
            time.sleep(0.1)

        except Exception as e:
            print(f"关闭服务 {service_name} 时出现异常: {e}")

    # 清理缓存
    _services.clear()
    _service_instances.clear()
    _initialized = False
    print("所有服务已关闭")


def get_services_status() -> Dict[str, Any]:
    """获取所有服务状态"""
    status = {}

    for service_name in SERVICE_STARTUP_ORDER:
        try:
            service = _service_instances.get(service_name)
            if service and hasattr(service, 'get_status') and callable(service.get_status):
                status[service_name] = service.get_status()
            else:
                status[service_name] = {
                    'running': service is not None,
                    'message': '服务已加载' if service else '服务未加载',
                    'initialized': _initialized
                }
        except Exception as e:
            status[service_name] = {
                'running': False,
                'message': f'状态获取失败: {e}',
                'error': True
            }

    return status


def restart_service(service_name: str) -> bool:
    """重启指定服务"""
    try:
        if service_name not in SERVICE_STARTUP_ORDER:
            print(f"未知的服务名称: {service_name}")
            return False

        print(f"正在重启服务: {service_name}")

        # 关闭服务
        service = _service_instances.get(service_name)
        if service and hasattr(service, 'shutdown'):
            service.shutdown()

        # 清理缓存
        _services.pop(service_name, None)
        _service_instances.pop(service_name, None)

        # 重新初始化
        service = get_service(service_name)
        if service and hasattr(service, 'initialize'):
            result = service.initialize()
            print(f"服务 {service_name} 重启{'成功' if result else '失败'}")
            return result

        return True

    except Exception as e:
        print(f"重启服务 {service_name} 失败: {e}")
        return False


def is_service_available(service_name: str) -> bool:
    """检查服务是否可用"""
    service = _service_instances.get(service_name)
    if not service:
        return False

    if hasattr(service, 'is_initialized'):
        return service.is_initialized

    return True


def get_service_health() -> Dict[str, Any]:
    """获取服务健康状态"""
    health = {
        'overall_status': 'healthy',
        'initialized': _initialized,
        'services': {},
        'issues': []
    }

    healthy_count = 0
    total_count = len(SERVICE_STARTUP_ORDER)

    for service_name in SERVICE_STARTUP_ORDER:
        try:
            service = _service_instances.get(service_name)
            if service:
                if hasattr(service, 'get_status'):
                    service_status = service.get_status()
                    is_healthy = service_status.get('running', False)
                else:
                    is_healthy = True
                    service_status = {'running': True, 'message': '服务正常'}

                health['services'][service_name] = service_status

                if is_healthy:
                    healthy_count += 1
                else:
                    health['issues'].append(f"服务 {service_name} 运行异常")
            else:
                health['services'][service_name] = {
                    'running': False,
                    'message': '服务未初始化'
                }
                health['issues'].append(f"服务 {service_name} 未初始化")

        except Exception as e:
            health['services'][service_name] = {
                'running': False,
                'message': f'检查异常: {e}',
                'error': True
            }
            health['issues'].append(f"服务 {service_name} 检查异常: {e}")

    # 计算整体健康状态
    if healthy_count == total_count:
        health['overall_status'] = 'healthy'
    elif healthy_count >= total_count * 0.8:
        health['overall_status'] = 'degraded'
    else:
        health['overall_status'] = 'unhealthy'

    health['healthy_services'] = healthy_count
    health['total_services'] = total_count
    health['health_percentage'] = round(healthy_count / total_count * 100, 2)

    return health


# 便捷访问函数
def get_auth_service():
    """获取认证服务"""
    return get_service('auth_service')


def get_credit_service():
    """获取积分服务"""
    return get_service('credit_service')


def get_port_service():
    """获取端口服务"""
    return get_service('port_service')


def get_message_service():
    """获取消息服务"""
    return get_service('message_service')


def get_task_service():
    """获取任务服务"""
    return get_service('task_service')


# 兼容性导出
__all__ = [
    # 服务管理
    'initialize_all_services',
    'shutdown_all_services',
    'get_services_status',
    'restart_service',
    'is_service_available',
    'get_service_health',

    # 服务访问
    'get_service',
    'get_auth_service',
    'get_credit_service',
    'get_port_service',
    'get_message_service',
    'get_task_service'
]

__version__ = '1.0.0'
__author__ = 'SMS Pool System Team'
__description__ = '猫池短信系统业务逻辑服务层'