"""
服务模块 - 最小化版本
"""

def initialize_all_services():
    """初始化所有服务"""
    services = ['auth_service', 'credit_service', 'port_service', 'message_service', 'task_service']
    results = {}

    for service_name in services:
        try:
            # 模拟服务初始化
            results[service_name] = True
            print(f"服务 {service_name} 初始化成功")
        except Exception as e:
            results[service_name] = False
            print(f"服务 {service_name} 初始化失败: {e}")

    return results

def shutdown_all_services():
    """关闭所有服务"""
    print("所有服务已关闭")
