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
    # 简化处理
    class MockPort:
        def __init__(self, port_name):
            self.port_name = port_name
            self.status = "offline"
            self.is_connected = False
            self.send_count = 0
            self.send_limit = 60
            self.is_selected = False

        def connect(self):
            return True

        def disconnect(self):
            return True

        def get_summary(self):
            return {'port_name': self.port_name}

    class MockPortManager:
        def __init__(self):
            self.ports = {}

        def scan_and_update_ports(self):
            return []

        def get_all_ports(self):
            return []

        def get_available_ports(self):
            return []

        def get_selected_ports(self):
            return []

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

    def scan_ports(self) -> Dict[str, Any]:
        """扫描端口"""
        try:
            log_info("开始扫描端口")

            with self._lock:
                ports = self.port_manager.scan_and_update_ports()
                self._last_scan_time = datetime.now()

                # 统计端口信息
                total_count = len(ports)
                online_count = len([p for p in ports if not p.is_offline()])

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

    def update_port_config(self, port_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """更新端口配置"""
        try:
            if self.port_manager.update_port_config(port_name, config):
                return {
                    'success': True,
                    'message': f'端口{port_name}配置更新成功',
                    'config': config
                }
            else:
                return {
                    'success': False,
                    'message': f'端口{port_name}不存在或配置更新失败',
                    'error_code': 'UPDATE_FAILED'
                }
        except Exception as e:
            log_error(f"更新端口{port_name}配置异常", error=e)
            return {
                'success': False,
                'message': f'配置更新异常: {str(e)}',
                'error_code': 'SYSTEM_ERROR'
            }

    def batch_update_config(self, config: Dict[str, Any], selected_only: bool = True) -> Dict[str, Any]:
        """批量更新端口配置"""
        try:
            updated_count = self.port_manager.batch_update_config(config, selected_only)
            target = "选中端口" if selected_only else "所有端口"

            return {
                'success': True,
                'message': f'成功更新{updated_count}个{target}的配置',
                'updated_count': updated_count,
                'config': config
            }
        except Exception as e:
            log_error("批量更新端口配置异常", error=e)
            return {
                'success': False,
                'message': f'批量更新异常: {str(e)}',
                'error_code': 'SYSTEM_ERROR'
            }

    def get_ports_summary(self) -> Dict[str, Any]:
        """获取端口概览"""
        try:
            return self.port_manager.get_ports_summary()
        except Exception as e:
            log_error("获取端口概览异常", error=e)
            return {}

    def auto_detect_carriers(self) -> Dict[str, Any]:
        """自动检测运营商"""
        try:
            detected_count = self.port_manager.auto_detect_carriers()
            return {
                'success': True,
                'message': f'自动检测完成，{detected_count}个端口运营商信息有变更',
                'detected_count': detected_count
            }
        except Exception as e:
            log_error("自动检测运营商异常", error=e)
            return {
                'success': False,
                'message': f'检测异常: {str(e)}',
                'error_code': 'SYSTEM_ERROR'
            }

    def check_send_limits(self) -> Dict[str, Any]:
        """检查发送上限"""
        try:
            limit_reached_ports = self.port_manager.check_send_limits()
            return {
                'limit_reached_ports': limit_reached_ports,
                'count': len(limit_reached_ports),
                'need_reset': len(limit_reached_ports) > 0,
                'message': f'有{len(limit_reached_ports)}个端口达到发送上限' if limit_reached_ports else '所有端口发送正常'
            }
        except Exception as e:
            log_error("检查发送上限异常", error=e)
            return {
                'limit_reached_ports': [],
                'count': 0,
                'need_reset': False,
                'error': str(e)
            }

    def get_port_health_status(self) -> Dict[str, Any]:
        """获取端口健康状态"""
        try:
            return self.port_manager.get_port_health_status()
        except Exception as e:
            log_error("获取端口健康状态异常", error=e)
            return {
                'healthy_ports': [],
                'warning_ports': [],
                'error_ports': [],
                'offline_ports': [],
                'error': str(e)
            }

    def get_next_available_port(self, carrier: str = None, exclude_ports: List[str] = None) -> Optional[Dict[str, Any]]:
        """获取下一个可用端口"""
        try:
            port = self.port_manager.get_next_available_port(carrier, exclude_ports)
            if port:
                return port.get_summary()
            return None
        except Exception as e:
            log_error("获取下一个可用端口异常", error=e)
            return None

    def distribute_messages_to_ports(self, message_count: int, carrier: str = None) -> Dict[str, Any]:
        """将消息分配到端口"""
        try:
            distribution = self.port_manager.distribute_messages_to_ports(message_count, carrier)

            if not distribution:
                return {
                    'success': False,
                    'message': '没有可用的端口进行消息分配',
                    'distribution': {}
                }

            return {
                'success': True,
                'message': f'成功将{message_count}条消息分配到{len(distribution)}个端口',
                'distribution': distribution,
                'total_allocated': sum(distribution.values())
            }
        except Exception as e:
            log_error("分配消息到端口异常", error=e)
            return {
                'success': False,
                'message': f'分配异常: {str(e)}',
                'distribution': {},
                'error_code': 'SYSTEM_ERROR'
            }

    def add_port_change_callback(self, callback: Callable[[str, List], None]):
        """添加端口变化回调函数"""
        try:
            if callable(callback):
                self._port_change_callbacks.append(callback)
                log_info(f"添加端口变化回调函数，当前回调数量: {len(self._port_change_callbacks)}")
        except Exception as e:
            log_error("添加端口变化回调失败", error=e)

    def remove_port_change_callback(self, callback: Callable[[str, List], None]):
        """移除端口变化回调函数"""
        try:
            if callback in self._port_change_callbacks:
                self._port_change_callbacks.remove(callback)
                log_info(f"移除端口变化回调函数，当前回调数量: {len(self._port_change_callbacks)}")
        except Exception as e:
            log_error("移除端口变化回调失败", error=e)

    def set_check_interval(self, interval_seconds: int):
        """设置状态检查间隔"""
        try:
            if interval_seconds < 5:  # 最小5秒
                interval_seconds = 5
            elif interval_seconds > 300:  # 最大5分钟
                interval_seconds = 300

            old_interval = self.check_interval
            self.check_interval = interval_seconds

            # 重启监控
            if self.is_initialized:
                self._stop_status_monitoring()
                self._start_status_monitoring()

            log_info(f"端口状态检查间隔已更新: {old_interval}秒 -> {interval_seconds}秒")

        except Exception as e:
            log_error("设置检查间隔失败", error=e)

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

                # 检查发送上限
                limit_reached = self.check_send_limits()
                if limit_reached['need_reset']:
                    log_info(f"检测到{limit_reached['count']}个端口达到发送上限")

                # 检查端口健康状态
                health_status = self.get_port_health_status()
                error_ports = health_status.get('error_ports', [])
                if error_ports:
                    log_info(f"检测到{len(error_ports)}个端口处于错误状态")

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

    def get_default_config(self) -> Dict[str, Any]:
        """获取默认端口配置"""
        return {
            'send_limit': self.card_switch_interval,
            'send_interval': self.default_send_interval,
            'baud_rate': 115200,
            'data_bits': 8,
            'stop_bits': 1,
            'parity': 'N'
        }

    def export_port_config(self) -> Dict[str, Any]:
        """导出端口配置"""
        try:
            ports = self.port_manager.get_all_ports()
            config_data = []

            for port in ports:
                config_data.append({
                    'port_name': port.port_name,
                    'carrier': port.carrier,
                    'send_limit': port.send_limit,
                    'send_interval': port.send_interval,
                    'baud_rate': port.baud_rate,
                    'data_bits': port.data_bits,
                    'stop_bits': port.stop_bits,
                    'parity': port.parity
                })

            return {
                'success': True,
                'config_data': config_data,
                'export_time': datetime.now().isoformat(),
                'total_ports': len(config_data)
            }

        except Exception as e:
            log_error("导出端口配置异常", error=e)
            return {
                'success': False,
                'message': f'导出异常: {str(e)}',
                'error_code': 'EXPORT_FAILED'
            }

    def import_port_config(self, config_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """导入端口配置"""
        try:
            imported_count = 0
            failed_count = 0

            for port_config in config_data:
                port_name = port_config.get('port_name')
                if not port_name:
                    failed_count += 1
                    continue

                # 移除端口名称，剩下的作为配置
                config = {k: v for k, v in port_config.items() if k != 'port_name'}

                if self.port_manager.update_port_config(port_name, config):
                    imported_count += 1
                else:
                    failed_count += 1

            return {
                'success': True,
                'message': f'成功导入{imported_count}个端口配置，失败{failed_count}个',
                'imported_count': imported_count,
                'failed_count': failed_count,
                'total_count': len(config_data)
            }

        except Exception as e:
            log_error("导入端口配置异常", error=e)
            return {
                'success': False,
                'message': f'导入异常: {str(e)}',
                'error_code': 'IMPORT_FAILED'
            }

    def get_port_statistics(self) -> Dict[str, Any]:
        """获取端口统计信息"""
        try:
            all_ports = self.port_manager.get_all_ports()

            if not all_ports:
                return {
                    'total_ports': 0,
                    'statistics': {}
                }

            stats = {
                'total_ports': len(all_ports),
                'connected_ports': len([p for p in all_ports if p.is_connected]),
                'available_ports': len(self.port_manager.get_available_ports()),
                'selected_ports': len(self.port_manager.get_selected_ports()),
                'total_sent': sum(p.total_sent for p in all_ports),
                'total_success': sum(p.success_count for p in all_ports),
                'total_failed': sum(p.failed_count for p in all_ports),
                'by_carrier': {},
                'by_status': {},
                'send_progress': []
            }

            # 按运营商统计
            for carrier in ['mobile', 'unicom', 'telecom', 'unknown']:
                carrier_ports = [p for p in all_ports if p.carrier == carrier]
                if carrier_ports:
                    stats['by_carrier'][carrier] = {
                        'count': len(carrier_ports),
                        'connected': len([p for p in carrier_ports if p.is_connected]),
                        'total_sent': sum(p.total_sent for p in carrier_ports),
                        'success_rate': round(
                            sum(p.success_count for p in carrier_ports) /
                            max(sum(p.total_sent for p in carrier_ports), 1) * 100, 2
                        )
                    }

            # 按状态统计
            for status in ['available', 'busy', 'error', 'offline']:
                status_ports = [p for p in all_ports if p.status == status]
                stats['by_status'][status] = len(status_ports)

            # 发送进度统计
            for port in all_ports:
                if port.send_limit > 0:
                    progress = round(port.send_count / port.send_limit * 100, 2)
                    stats['send_progress'].append({
                        'port_name': port.port_name,
                        'progress': progress,
                        'current': port.send_count,
                        'limit': port.send_limit
                    })

            return stats

        except Exception as e:
            log_error("获取端口统计信息异常", error=e)
            return {'total_ports': 0, 'error': str(e)}

    def optimize_port_distribution(self) -> Dict[str, Any]:
        """优化端口分配"""
        try:
            ports = self.port_manager.get_all_ports()
            if not ports:
                return {
                    'success': False,
                    'message': '没有可用端口进行优化',
                    'optimizations': []
                }

            optimizations = []

            # 检查负载均衡
            connected_ports = [p for p in ports if p.is_connected]
            if connected_ports:
                avg_sent = sum(p.send_count for p in connected_ports) / len(connected_ports)

                for port in connected_ports:
                    if port.send_count > avg_sent * 1.5:  # 超过平均值50%
                        optimizations.append({
                            'type': 'high_load',
                            'port': port.port_name,
                            'current_load': port.send_count,
                            'average_load': round(avg_sent, 2),
                            'suggestion': '考虑暂停此端口或重置发送计数'
                        })
                    elif port.send_count < avg_sent * 0.5:  # 低于平均值50%
                        optimizations.append({
                            'type': 'low_utilization',
                            'port': port.port_name,
                            'current_load': port.send_count,
                            'average_load': round(avg_sent, 2),
                            'suggestion': '此端口利用率较低，可优先分配任务'
                        })

            # 检查端口配置
            for port in ports:
                if port.send_interval < 500:
                    optimizations.append({
                        'type': 'fast_interval',
                        'port': port.port_name,
                        'current_interval': port.send_interval,
                        'suggestion': '发送间隔过短，可能导致发送过快被限制'
                    })

                if port.send_limit > 100:
                    optimizations.append({
                        'type': 'high_limit',
                        'port': port.port_name,
                        'current_limit': port.send_limit,
                        'suggestion': '发送上限较高，建议降低以避免运营商限制'
                    })

            return {
                'success': True,
                'message': f'端口优化分析完成，发现{len(optimizations)}项建议',
                'optimizations': optimizations,
                'total_ports': len(ports),
                'analyzed_time': datetime.now().isoformat()
            }

        except Exception as e:
            log_error("优化端口分配异常", error=e)
            return {
                'success': False,
                'message': f'优化异常: {str(e)}',
                'error_code': 'OPTIMIZATION_FAILED'
            }

    def backup_port_settings(self) -> Dict[str, Any]:
        """备份端口设置"""
        try:
            backup_data = {
                'backup_time': datetime.now().isoformat(),
                'service_config': {
                    'auto_scan': self.auto_scan,
                    'check_interval': self.check_interval,
                    'default_send_interval': self.default_send_interval,
                    'card_switch_interval': self.card_switch_interval
                },
                'ports': []
            }

            # 备份所有端口配置
            for port in self.port_manager.get_all_ports():
                port_data = {
                    'port_name': port.port_name,
                    'carrier': port.carrier,
                    'send_limit': port.send_limit,
                    'send_interval': port.send_interval,
                    'baud_rate': port.baud_rate,
                    'data_bits': port.data_bits,
                    'stop_bits': port.stop_bits,
                    'parity': port.parity,
                    'is_selected': port.is_selected
                }
                backup_data['ports'].append(port_data)

            return {
                'success': True,
                'message': f'成功备份{len(backup_data["ports"])}个端口的设置',
                'backup_data': backup_data,
                'backup_size': len(str(backup_data))
            }

        except Exception as e:
            log_error("备份端口设置异常", error=e)
            return {
                'success': False,
                'message': f'备份异常: {str(e)}',
                'error_code': 'BACKUP_FAILED'
            }

    def restore_port_settings(self, backup_data: Dict[str, Any]) -> Dict[str, Any]:
        """恢复端口设置"""
        try:
            if 'ports' not in backup_data:
                return {
                    'success': False,
                    'message': '备份数据格式错误',
                    'error_code': 'INVALID_BACKUP_DATA'
                }

            restored_count = 0
            failed_count = 0

            # 恢复服务配置
            if 'service_config' in backup_data:
                service_config = backup_data['service_config']
                self.auto_scan = service_config.get('auto_scan', self.auto_scan)
                self.default_send_interval = service_config.get('default_send_interval', self.default_send_interval)
                self.card_switch_interval = service_config.get('card_switch_interval', self.card_switch_interval)

                # 更新检查间隔
                new_interval = service_config.get('check_interval', self.check_interval)
                if new_interval != self.check_interval:
                    self.set_check_interval(new_interval)

            # 恢复端口配置
            for port_data in backup_data['ports']:
                port_name = port_data.get('port_name')
                if not port_name:
                    failed_count += 1
                    continue

                # 移除端口名称，剩下的作为配置
                config = {k: v for k, v in port_data.items() if k != 'port_name'}

                if self.port_manager.update_port_config(port_name, config):
                    # 恢复选择状态
                    if 'is_selected' in port_data:
                        self.port_manager.select_port(port_name, port_data['is_selected'])
                    restored_count += 1
                else:
                    failed_count += 1

            backup_time = backup_data.get('backup_time', '未知时间')

            return {
                'success': True,
                'message': f'从{backup_time}的备份中恢复了{restored_count}个端口设置，失败{failed_count}个',
                'restored_count': restored_count,
                'failed_count': failed_count,
                'backup_time': backup_time
            }

        except Exception as e:
            log_error("恢复端口设置异常", error=e)
            return {
                'success': False,
                'message': f'恢复异常: {str(e)}',
                'error_code': 'RESTORE_FAILED'
            }


# 全局端口服务实例
port_service = PortService()