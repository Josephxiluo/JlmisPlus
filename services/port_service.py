"""
猫池短信系统端口管理服务 - tkinter版
Port management service for SMS Pool System - tkinter version
"""

import sys
import threading
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Callable
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from models.port import Port, PortManager, PortStatus, PortCarrier, port_manager
    from config.settings import settings
    from config.logging_config import get_logger, log_port_action, log_error, log_info, log_timer_action
except ImportError:
    # 简化处理 - 修复 Mock 类
    class MockPort:
        def __init__(self, port_name, port_id=None):
            self.port_name = port_name
            self.id = port_id or port_name
            self.name = port_name
            self.status = "available"
            self.is_connected = True
            self.send_count = 0
            self.send_limit = 60
            self.is_selected = False
            self.carrier = ["中国移动", "中国联通", "中国电信"][hash(port_name) % 3]
            self.success_count = hash(port_name) % 50
            self.failed_count = hash(port_name) % 5
            self.limit = self.send_limit

        def connect(self):
            self.status = "available"
            self.is_connected = True
            return True

        def disconnect(self):
            self.status = "offline"
            self.is_connected = False
            return True

        def get_summary(self):
            return {
                'id': self.id,
                'name': self.port_name,
                'port_name': self.port_name,
                'status': self.status,
                'carrier': self.carrier,
                'limit': self.send_limit,
                'success_count': self.success_count,
                'failed_count': self.failed_count,
                'is_connected': self.is_connected,
                'is_selected': self.is_selected
            }

    class MockPortManager:
        def __init__(self):
            # 模拟端口数据
            self.ports = {
                'COM1': MockPort('COM1', 1),
                'COM2': MockPort('COM2', 2),
                'COM3': MockPort('COM3', 3),
                'COM4': MockPort('COM4', 4),
                'COM5': MockPort('COM5', 5),
            }

        def scan_and_update_ports(self):
            return list(self.ports.values())

        def get_all_ports(self):
            return list(self.ports.values())

        def get_available_ports(self):
            return [p for p in self.ports.values() if p.status == "available"]

        def get_selected_ports(self):
            return [p for p in self.ports.values() if p.is_selected]

        def get_port(self, port_name):
            return self.ports.get(port_name)

        def connect_all_ports(self):
            count = 0
            for port in self.ports.values():
                if port.connect():
                    count += 1
            return count

        def disconnect_all_ports(self):
            count = 0
            for port in self.ports.values():
                if port.disconnect():
                    count += 1
            return count

        def select_port(self, port_name, selected=True):
            port = self.ports.get(port_name)
            if port:
                port.is_selected = selected
                return True
            return False

        def select_all_ports(self):
            count = 0
            for port in self.ports.values():
                port.is_selected = True
                count += 1
            return count

        def unselect_all_ports(self):
            count = 0
            for port in self.ports.values():
                port.is_selected = False
                count += 1
            return count

        def invert_selection(self):
            count = 0
            for port in self.ports.values():
                port.is_selected = not port.is_selected
                count += 1
            return count

        def start_selected_ports(self):
            count = 0
            for port in self.ports.values():
                if port.is_selected and port.connect():
                    count += 1
            return count

        def stop_selected_ports(self):
            count = 0
            for port in self.ports.values():
                if port.is_selected and port.disconnect():
                    count += 1
            return count

        def clear_all_statistics(self):
            count = 0
            for port in self.ports.values():
                port.success_count = 0
                port.failed_count = 0
                port.send_count = 0
                count += 1
            return count

        def clear_selected_statistics(self):
            count = 0
            for port in self.ports.values():
                if port.is_selected:
                    port.success_count = 0
                    port.failed_count = 0
                    port.send_count = 0
                    count += 1
            return count

        def reset_all_send_counts(self):
            count = 0
            for port in self.ports.values():
                port.send_count = 0
                count += 1
            return count

        def reset_selected_send_counts(self):
            count = 0
            for port in self.ports.values():
                if port.is_selected:
                    port.send_count = 0
                    count += 1
            return count

        def update_port_config(self, port_name, config):
            port = self.ports.get(port_name)
            if port:
                # 更新配置
                for key, value in config.items():
                    if hasattr(port, key):
                        setattr(port, key, value)
                return True
            return False

        def batch_update_config(self, config, selected_only=True):
            count = 0
            for port in self.ports.values():
                if not selected_only or port.is_selected:
                    for key, value in config.items():
                        if hasattr(port, key):
                            setattr(port, key, value)
                    count += 1
            return count

        def get_next_available_port(self, carrier=None, exclude_ports=None):
            exclude_ports = exclude_ports or []
            for port in self.ports.values():
                if (port.status == "available" and
                    port.port_name not in exclude_ports and
                    (not carrier or port.carrier == carrier)):
                    return port
            return None

    Port = MockPort
    PortManager = MockPortManager
    port_manager = MockPortManager()

    class PortStatus:
        AVAILABLE = "available"
        BUSY = "busy"
        ERROR = "error"
        OFFLINE = "offline"

    class PortCarrier:
        MOBILE = "mobile"
        UNICOM = "unicom"
        TELECOM = "telecom"
        UNKNOWN = "unknown"

    class MockSettings:
        PORT_CHECK_INTERVAL = 10
        AUTO_PORT_SCAN = True
        DEFAULT_SEND_INTERVAL = 1000
        CARD_SWITCH_INTERVAL = 60

    settings = MockSettings()

    import logging
    def get_logger(name='services.port'):
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    def log_port_action(port_name, action, details=None, success=True):
        logger = get_logger()
        status = "成功" if success else "失败"
        message = f"[端口操作] {port_name} {action} {status}"
        if details:
            message += f" - {details}"
        if success:
            logger.info(message)
        else:
            logger.warning(message)

    def log_error(message, error=None):
        logger = get_logger()
        logger.error(f"{message}: {error}" if error else message)

    def log_info(message):
        logger = get_logger()
        logger.info(message)

    def log_timer_action(timer_name, action, interval=None):
        logger = get_logger()
        message = f"[定时器] {timer_name} {action}"
        if interval:
            message += f" 间隔={interval}秒"
        logger.debug(message)

logger = get_logger('services.port')


class PortService:
    """端口管理服务类"""

    def __init__(self):
        """初始化端口服务"""
        self.port_manager = port_manager
        self._lock = threading.Lock()
        self._status_check_timer: Optional[threading.Timer] = None
        self._port_change_callbacks: list = []
        self._last_scan_time: Optional[datetime] = None
        self.is_initialized = False

        # 配置参数
        self.auto_scan = getattr(settings, 'AUTO_PORT_SCAN', True)
        self.check_interval = getattr(settings, 'PORT_CHECK_INTERVAL', 10)  # 状态检查间隔
        self.default_send_interval = getattr(settings, 'DEFAULT_SEND_INTERVAL', 1000)
        self.card_switch_interval = getattr(settings, 'CARD_SWITCH_INTERVAL', 60)

    def initialize(self) -> bool:
        """初始化服务"""
        try:
            log_info("端口管理服务初始化开始")

            # 初始端口扫描
            if self.auto_scan:
                self.scan_ports()

            # 启动状态监控
            self._start_status_monitoring()

            self.is_initialized = True
            log_info(f"端口管理服务初始化完成，自动扫描: {self.auto_scan}")
            return True

        except Exception as e:
            log_error("端口管理服务初始化失败", error=e)
            return False

    def shutdown(self):
        """关闭服务"""
        try:
            log_info("端口管理服务开始关闭")

            # 停止状态监控
            self._stop_status_monitoring()

            # 断开所有端口
            self.disconnect_all_ports()

            # 清除回调
            self._port_change_callbacks.clear()

            self.is_initialized = False
            log_info("端口管理服务关闭完成")

        except Exception as e:
            log_error("端口管理服务关闭失败", error=e)

    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        return {
            'running': self.is_initialized,
            'auto_scan': self.auto_scan,
            'check_interval': self.check_interval,
            'last_scan': self._last_scan_time.isoformat() if self._last_scan_time else None,
            'port_count': len(self.port_manager.get_all_ports()),
            'available_count': len(self.port_manager.get_available_ports()),
            'connected_count': len([p for p in self.port_manager.get_all_ports() if p.is_connected]),
            'monitoring_active': self._status_check_timer is not None,
            'message': '端口管理服务正常运行' if self.is_initialized else '端口管理服务未初始化'
        }

    def get_ports(self) -> Dict[str, Any]:
        """获取所有端口 - 添加缺失的方法"""
        try:
            ports = self.port_manager.get_all_ports()
            ports_data = [port.get_summary() for port in ports]

            return {
                'success': True,
                'ports': ports_data,
                'total_count': len(ports_data),
                'available_count': len([p for p in ports_data if p['status'] == 'available']),
                'message': f'成功获取{len(ports_data)}个端口信息'
            }

        except Exception as e:
            log_error("获取端口列表失败", error=e)
            return {
                'success': False,
                'ports': [],
                'total_count': 0,
                'available_count': 0,
                'message': f'获取端口失败: {str(e)}',
                'error': str(e)
            }

    def scan_ports(self) -> Dict[str, Any]:
        """扫描端口"""
        try:
            log_info("开始扫描端口")

            with self._lock:
                ports = self.port_manager.scan_and_update_ports()
                self._last_scan_time = datetime.now()

                # 统计端口信息
                total_count = len(ports)
                online_count = len([p for p in ports if p.status != "offline"])

                # 通知端口变化
                self._notify_port_change('scan', ports)

                log_info(f"端口扫描完成，发现{total_count}个端口，在线{online_count}个")

                return {
                    'success': True,
                    'total_count': total_count,
                    'online_count': online_count,
                    'ports': [port.get_summary() for port in ports],
                    'scan_time': self._last_scan_time.isoformat()
                }

        except Exception as e:
            log_error("扫描端口失败", error=e)
            return {
                'success': False,
                'message': f'扫描失败: {str(e)}',
                'error_code': 'SCAN_FAILED'
            }

    def get_all_ports(self) -> List[Dict[str, Any]]:
        """获取所有端口信息"""
        try:
            ports = self.port_manager.get_all_ports()
            return [port.get_summary() for port in ports]
        except Exception as e:
            log_error("获取端口列表失败", error=e)
            return []

    def get_available_ports(self) -> List[Dict[str, Any]]:
        """获取可用端口"""
        try:
            ports = self.port_manager.get_available_ports()
            return [port.get_summary() for port in ports]
        except Exception as e:
            log_error("获取可用端口失败", error=e)
            return []

    def get_port_info(self, port_name: str) -> Optional[Dict[str, Any]]:
        """获取指定端口信息"""
        try:
            port = self.port_manager.get_port(port_name)
            if port:
                return port.get_summary()
            return None
        except Exception as e:
            log_error(f"获取端口{port_name}信息失败", error=e)
            return None

    def connect_port(self, port_name: str) -> Dict[str, Any]:
        """连接端口"""
        try:
            with self._lock:
                port = self.port_manager.get_port(port_name)
                if not port:
                    return {
                        'success': False,
                        'message': f'端口{port_name}不存在',
                        'error_code': 'PORT_NOT_FOUND'
                    }

                if port.connect():
                    self._notify_port_change('connect', [port])
                    log_port_action(port_name, "连接", success=True)

                    return {
                        'success': True,
                        'message': f'端口{port_name}连接成功',
                        'port_info': port.get_summary()
                    }
                else:
                    return {
                        'success': False,
                        'message': f'端口{port_name}连接失败',
                        'error_code': 'CONNECT_FAILED'
                    }

        except Exception as e:
            log_error(f"连接端口{port_name}异常", error=e)
            return {
                'success': False,
                'message': f'连接异常: {str(e)}',
                'error_code': 'SYSTEM_ERROR'
            }

    def disconnect_port(self, port_name: str) -> Dict[str, Any]:
        """断开端口"""
        try:
            with self._lock:
                port = self.port_manager.get_port(port_name)
                if not port:
                    return {
                        'success': False,
                        'message': f'端口{port_name}不存在',
                        'error_code': 'PORT_NOT_FOUND'
                    }

                if port.disconnect():
                    self._notify_port_change('disconnect', [port])
                    log_port_action(port_name, "断开", success=True)

                    return {
                        'success': True,
                        'message': f'端口{port_name}断开成功',
                        'port_info': port.get_summary()
                    }
                else:
                    return {
                        'success': False,
                        'message': f'端口{port_name}断开失败',
                        'error_code': 'DISCONNECT_FAILED'
                    }

        except Exception as e:
            log_error(f"断开端口{port_name}异常", error=e)
            return {
                'success': False,
                'message': f'断开异常: {str(e)}',
                'error_code': 'SYSTEM_ERROR'
            }

    def connect_all_ports(self) -> Dict[str, Any]:
        """连接所有端口"""
        try:
            log_info("开始连接所有端口")
            connected_count = self.port_manager.connect_all_ports()

            return {
                'success': True,
                'message': f'成功连接{connected_count}个端口',
                'connected_count': connected_count,
                'total_count': len(self.port_manager.get_all_ports())
            }

        except Exception as e:
            log_error("连接所有端口异常", error=e)
            return {
                'success': False,
                'message': f'连接异常: {str(e)}',
                'error_code': 'SYSTEM_ERROR'
            }

    def disconnect_all_ports(self) -> Dict[str, Any]:
        """断开所有端口"""
        try:
            log_info("开始断开所有端口")
            disconnected_count = self.port_manager.disconnect_all_ports()

            return {
                'success': True,
                'message': f'成功断开{disconnected_count}个端口',
                'disconnected_count': disconnected_count,
                'total_count': len(self.port_manager.get_all_ports())
            }

        except Exception as e:
            log_error("断开所有端口异常", error=e)
            return {
                'success': False,
                'message': f'断开异常: {str(e)}',
                'error_code': 'SYSTEM_ERROR'
            }

    def select_port(self, port_name: str, selected: bool = True) -> Dict[str, Any]:
        """选择/取消选择端口"""
        try:
            if self.port_manager.select_port(port_name, selected):
                action = "选择" if selected else "取消选择"
                return {
                    'success': True,
                    'message': f'端口{port_name}{action}成功'
                }
            else:
                return {
                    'success': False,
                    'message': f'端口{port_name}不存在',
                    'error_code': 'PORT_NOT_FOUND'
                }

        except Exception as e:
            log_error(f"选择端口{port_name}异常", error=e)
            return {
                'success': False,
                'message': f'选择异常: {str(e)}',
                'error_code': 'SYSTEM_ERROR'
            }

    def select_all_ports(self) -> Dict[str, Any]:
        """选择所有端口"""
        try:
            selected_count = self.port_manager.select_all_ports()
            return {
                'success': True,
                'message': f'已选择{selected_count}个端口',
                'selected_count': selected_count
            }
        except Exception as e:
            log_error("选择所有端口异常", error=e)
            return {
                'success': False,
                'message': f'选择异常: {str(e)}',
                'error_code': 'SYSTEM_ERROR'
            }

    def unselect_all_ports(self) -> Dict[str, Any]:
        """取消选择所有端口"""
        try:
            unselected_count = self.port_manager.unselect_all_ports()
            return {
                'success': True,
                'message': f'已取消选择{unselected_count}个端口',
                'unselected_count': unselected_count
            }
        except Exception as e:
            log_error("取消选择所有端口异常", error=e)
            return {
                'success': False,
                'message': f'取消选择异常: {str(e)}',
                'error_code': 'SYSTEM_ERROR'
            }

    def invert_selection(self) -> Dict[str, Any]:
        """反选端口"""
        try:
            inverted_count = self.port_manager.invert_selection()
            return {
                'success': True,
                'message': f'已反选{inverted_count}个端口',
                'inverted_count': inverted_count
            }
        except Exception as e:
            log_error("反选端口异常", error=e)
            return {
                'success': False,
                'message': f'反选异常: {str(e)}',
                'error_code': 'SYSTEM_ERROR'
            }

    def start_selected_ports(self) -> Dict[str, Any]:
        """启动选中的端口"""
        try:
            started_count = self.port_manager.start_selected_ports()
            selected_ports = self.port_manager.get_selected_ports()

            self._notify_port_change('start_selected', selected_ports)

            return {
                'success': True,
                'message': f'成功启动{started_count}个端口',
                'started_count': started_count,
                'selected_count': len(selected_ports)
            }
        except Exception as e:
            log_error("启动选中端口异常", error=e)
            return {
                'success': False,
                'message': f'启动异常: {str(e)}',
                'error_code': 'SYSTEM_ERROR'
            }

    def stop_selected_ports(self) -> Dict[str, Any]:
        """停止选中的端口"""
        try:
            stopped_count = self.port_manager.stop_selected_ports()
            selected_ports = self.port_manager.get_selected_ports()

            self._notify_port_change('stop_selected', selected_ports)

            return {
                'success': True,
                'message': f'成功停止{stopped_count}个端口',
                'stopped_count': stopped_count,
                'selected_count': len(selected_ports)
            }
        except Exception as e:
            log_error("停止选中端口异常", error=e)
            return {
                'success': False,
                'message': f'停止异常: {str(e)}',
                'error_code': 'SYSTEM_ERROR'
            }

    def clear_all_statistics(self) -> Dict[str, Any]:
        """清除所有端口统计"""
        try:
            cleared_count = self.port_manager.clear_all_statistics()
            return {
                'success': True,
                'message': f'已清除{cleared_count}个端口的统计信息',
                'cleared_count': cleared_count
            }
        except Exception as e:
            log_error("清除所有统计异常", error=e)
            return {
                'success': False,
                'message': f'清除异常: {str(e)}',
                'error_code': 'SYSTEM_ERROR'
            }

    def clear_selected_statistics(self) -> Dict[str, Any]:
        """清除选中端口统计"""
        try:
            cleared_count = self.port_manager.clear_selected_statistics()
            return {
                'success': True,
                'message': f'已清除{cleared_count}个选中端口的统计信息',
                'cleared_count': cleared_count
            }
        except Exception as e:
            log_error("清除选中统计异常", error=e)
            return {
                'success': False,
                'message': f'清除异常: {str(e)}',
                'error_code': 'SYSTEM_ERROR'
            }

    def reset_all_send_counts(self) -> Dict[str, Any]:
        """重置所有端口发送计数"""
        try:
            reset_count = self.port_manager.reset_all_send_counts()
            return {
                'success': True,
                'message': f'已重置{reset_count}个端口的发送计数',
                'reset_count': reset_count
            }
        except Exception as e:
            log_error("重置所有发送计数异常", error=e)
            return {
                'success': False,
                'message': f'重置异常: {str(e)}',
                'error_code': 'SYSTEM_ERROR'
            }

    def reset_selected_send_counts(self) -> Dict[str, Any]:
        """重置选中端口发送计数"""
        try:
            reset_count = self.port_manager.reset_selected_send_counts()
            return {
                'success': True,
                'message': f'已重置{reset_count}个选中端口的发送计数',
                'reset_count': reset_count
            }
        except Exception as e:
            log_error("重置选中发送计数异常", error=e)
            return {
                'success': False,
                'message': f'重置异常: {str(e)}',
                'error_code': 'SYSTEM_ERROR'
            }

    def _start_status_monitoring(self):
        """启动状态监控"""
        try:
            if self._status_check_timer:
                self._status_check_timer.cancel()

            self._status_check_timer = threading.Timer(self.check_interval, self._status_check_callback)
            self._status_check_timer.daemon = True
            self._status_check_timer.start()

            log_timer_action("端口状态检查", "启动", self.check_interval)

        except Exception as e:
            log_error("启动状态监控失败", error=e)

    def _stop_status_monitoring(self):
        """停止状态监控"""
        try:
            if self._status_check_timer:
                self._status_check_timer.cancel()
                self._status_check_timer = None
                log_timer_action("端口状态检查", "停止")

        except Exception as e:
            log_error("停止状态监控失败", error=e)

    def _status_check_callback(self):
        """状态检查回调"""
        try:
            if self.is_initialized:
                # 检查端口状态
                ports = self.port_manager.get_all_ports()

                # 自动重新扫描（如果启用）
                if self.auto_scan:
                    # 每分钟检查一次新端口
                    if (self._last_scan_time is None or
                        datetime.now() - self._last_scan_time > timedelta(minutes=1)):
                        self.scan_ports()

            # 重新启动定时器
            if self.is_initialized:
                self._start_status_monitoring()

        except Exception as e:
            log_error("状态检查回调异常", error=e)
            # 即使出错也要重新启动定时器
            if self.is_initialized:
                self._start_status_monitoring()

    def _notify_port_change(self, action: str, ports: List):
        """通知端口变化"""
        try:
            for callback in self._port_change_callbacks:
                try:
                    callback(action, ports)
                except Exception as e:
                    log_error("端口变化回调执行失败", error=e)

        except Exception as e:
            log_error("通知端口变化失败", error=e)

    def add_port_change_callback(self, callback: Callable):
        """添加端口变化回调函数"""
        try:
            if callable(callback):
                self._port_change_callbacks.append(callback)
                log_info(f"添加端口变化回调函数，当前回调数量: {len(self._port_change_callbacks)}")
        except Exception as e:
            log_error("添加端口变化回调失败", error=e)

    def remove_port_change_callback(self, callback: Callable):
        """移除端口变化回调函数"""
        try:
            if callback in self._port_change_callbacks:
                self._port_change_callbacks.remove(callback)
                log_info(f"移除端口变化回调函数，当前回调数量: {len(self._port_change_callbacks)}")
        except Exception as e:
            log_error("移除端口变化回调失败", error=e)


# 全局端口服务实例
port_service = PortService()