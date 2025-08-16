"""
猫池短信系统端口管理服务 - 增强版
支持模拟模式和真实模式自动切换
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

# 尝试导入真实模块，如果失败则使用模拟模式
try:
    from config.settings import settings
    from config.logging_config import get_logger, log_port_action, log_error, log_info
    REAL_MODE_AVAILABLE = True
except ImportError:
    REAL_MODE_AVAILABLE = False
    # 创建简单的日志函数
    import logging

    class MockSettings:
        SIMULATION_MODE = True
        AUTO_PORT_SCAN = True
        PORT_CHECK_INTERVAL = 10
        DEFAULT_SEND_INTERVAL = 1000
        CARD_SWITCH_INTERVAL = 60
        MAX_CONCURRENT_TASKS = 3
        SMS_RATE = 1.0
        MMS_RATE = 3.0

    settings = MockSettings()

    def get_logger(name):
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    def log_info(msg):
        logger = get_logger('port_service')
        logger.info(msg)

    def log_error(msg):
        logger = get_logger('port_service')
        logger.error(msg)

    def log_port_action(port_name, action, success=True, details=None):
        status = "成功" if success else "失败"
        msg = f"[端口] {port_name} {action} {status}"
        if details:
            msg += f" - {details}"
        if success:
            log_info(msg)
        else:
            log_error(msg)

logger = get_logger('services.port')

# 尝试导入真实端口管理器
REAL_PORT_MANAGER = None
try:
    # 首先确认 models 包存在
    import models
    # 尝试从 models 包导入 port 模块
    try:
        from models import port
        if hasattr(port, 'port_manager'):
            REAL_PORT_MANAGER = port.port_manager
            log_info("成功加载真实端口管理模块")
    except (ImportError, AttributeError) as e:
        log_info(f"无法加载 models.port: {e}")
except ImportError as e:
    log_info(f"无法加载 models 包: {e}")


class EnhancedPortService:
    """增强版端口管理服务 - 支持模拟和真实模式"""

    def __init__(self):
        """初始化端口服务"""
        self._lock = threading.Lock()
        self._port_change_callbacks: List[Callable] = []
        self._last_scan_time: Optional[datetime] = None
        self._status_check_timer: Optional[threading.Timer] = None
        self.is_initialized = False

        # 检查是否为模拟模式
        self.simulation_mode = getattr(settings, 'SIMULATION_MODE', True)

        # 根据模式选择端口管理器
        if self.simulation_mode or not REAL_MODE_AVAILABLE or REAL_PORT_MANAGER is None:
            # 使用模拟器
            try:
                from core.simulator.port_simulator import port_simulator
                self.port_manager = port_simulator
                self.simulation_mode = True
                log_info("端口服务运行在【模拟模式】")
            except ImportError as e:
                log_error(f"无法加载端口模拟器: {e}")
                raise
        else:
            # 使用真实端口管理器
            self.port_manager = REAL_PORT_MANAGER
            log_info("端口服务运行在【真实模式】")

        # 配置参数
        self.auto_scan = getattr(settings, 'AUTO_PORT_SCAN', True)
        self.check_interval = getattr(settings, 'PORT_CHECK_INTERVAL', 10)
        self.default_send_interval = getattr(settings, 'DEFAULT_SEND_INTERVAL', 1000)
        self.card_switch_limit = getattr(settings, 'CARD_SWITCH_INTERVAL', 60)

        # 端口配置存储
        self.port_configs = {}

    def initialize(self) -> bool:
        """初始化服务"""
        try:
            log_info(f"端口管理服务初始化开始 (模式: {'模拟' if self.simulation_mode else '真实'})")

            # 初始扫描
            if self.auto_scan:
                self.scan_ports()

            # 启动状态监控
            self._start_status_monitoring()

            self.is_initialized = True
            log_info("端口管理服务初始化完成")
            return True

        except Exception as e:
            log_error(f"端口管理服务初始化失败: {e}")
            return False

    def shutdown(self):
        """关闭服务"""
        try:
            log_info("端口管理服务开始关闭")

            # 停止监控
            self._stop_status_monitoring()

            # 断开所有端口
            self.disconnect_all_ports()

            # 清除回调
            self._port_change_callbacks.clear()

            self.is_initialized = False
            log_info("端口管理服务关闭完成")

        except Exception as e:
            log_error(f"端口管理服务关闭失败: {e}")

    def scan_ports(self) -> Dict[str, Any]:
        """扫描端口（支持虚拟和真实）"""
        try:
            log_info("开始扫描端口...")

            with self._lock:
                if self.simulation_mode:
                    # 模拟模式：扫描虚拟端口
                    available_ports = self.port_manager.scan_ports()
                    ports = []

                    for port_name in available_ports:
                        port = self.port_manager.get_port(port_name)
                        if port:
                            ports.append(port)
                else:
                    # 真实模式：扫描真实COM端口
                    ports = self.port_manager.scan_and_update_ports()

                self._last_scan_time = datetime.now()

                # 统计信息
                total_count = len(ports)
                connected_count = len([p for p in ports if getattr(p, 'is_connected', False)])

                # 通知端口变化
                self._notify_port_change('scan', ports)

                log_info(f"端口扫描完成: 发现{total_count}个端口, 已连接{connected_count}个")

                return {
                    'success': True,
                    'total_count': total_count,
                    'connected_count': connected_count,
                    'ports': [self._format_port_info(p) for p in ports],
                    'scan_time': self._last_scan_time.isoformat(),
                    'mode': 'simulation' if self.simulation_mode else 'real'
                }

        except Exception as e:
            log_error(f"扫描端口失败: {e}")
            return {
                'success': False,
                'message': f'扫描失败: {str(e)}'
            }

    def get_ports(self) -> Dict[str, Any]:
        """获取所有端口信息"""
        try:
            if self.simulation_mode:
                ports = []
                for name in self.port_manager.get_all_ports():
                    port = self.port_manager.get_port(name)
                    if port:
                        ports.append(port)
            else:
                ports = self.port_manager.get_all_ports() if hasattr(self.port_manager, 'get_all_ports') else []

            ports_data = [self._format_port_info(p) for p in ports if p]

            return {
                'success': True,
                'ports': ports_data,
                'total_count': len(ports_data),
                'available_count': len([p for p in ports_data if p.get('status') in ['available', 'ready', 'idle']]),
                'mode': 'simulation' if self.simulation_mode else 'real'
            }

        except Exception as e:
            log_error(f"获取端口列表失败: {e}")
            return {
                'success': False,
                'ports': [],
                'message': str(e)
            }

    def connect_port(self, port_name: str) -> Dict[str, Any]:
        """连接端口"""
        try:
            port = self.port_manager.get_port(port_name) if hasattr(self.port_manager, 'get_port') else None
            if not port:
                return {
                    'success': False,
                    'message': f'端口{port_name}不存在'
                }

            # 连接端口
            if hasattr(port, 'connect'):
                success = port.connect()
            elif hasattr(self.port_manager, 'connect_port'):
                success = self.port_manager.connect_port(port_name)
            else:
                success = False

            if success:
                log_port_action(port_name, "连接", success=True)
                self._notify_port_change('connect', [port])

                return {
                    'success': True,
                    'message': f'端口{port_name}连接成功',
                    'port_info': self._format_port_info(port)
                }
            else:
                return {
                    'success': False,
                    'message': f'端口{port_name}连接失败'
                }

        except Exception as e:
            log_error(f"连接端口{port_name}异常: {e}")
            return {
                'success': False,
                'message': str(e)
            }

    def disconnect_port(self, port_name: str) -> Dict[str, Any]:
        """断开端口"""
        try:
            port = self.port_manager.get_port(port_name) if hasattr(self.port_manager, 'get_port') else None
            if not port:
                return {
                    'success': False,
                    'message': f'端口{port_name}不存在'
                }

            # 断开端口
            if hasattr(port, 'disconnect'):
                success = port.disconnect()
            elif hasattr(self.port_manager, 'disconnect_port'):
                success = self.port_manager.disconnect_port(port_name)
            else:
                success = False

            if success:
                log_port_action(port_name, "断开", success=True)
                self._notify_port_change('disconnect', [port])

                return {
                    'success': True,
                    'message': f'端口{port_name}断开成功'
                }
            else:
                return {
                    'success': False,
                    'message': f'端口{port_name}断开失败'
                }

        except Exception as e:
            log_error(f"断开端口{port_name}异常: {e}")
            return {
                'success': False,
                'message': str(e)
            }

    def start_ports(self, port_ids: List[int]) -> Dict[str, Any]:
        """启动指定端口"""
        try:
            started_count = 0

            for port_id in port_ids:
                # 通过ID查找端口
                port_name = f"COM{port_id}"
                result = self.connect_port(port_name)
                if result['success']:
                    started_count += 1

            return {
                'success': True,
                'count': started_count,
                'message': f'成功启动{started_count}个端口'
            }

        except Exception as e:
            log_error(f"启动端口失败: {e}")
            return {
                'success': False,
                'message': str(e)
            }

    def stop_ports(self, port_ids: List[int]) -> Dict[str, Any]:
        """停止指定端口"""
        try:
            stopped_count = 0

            for port_id in port_ids:
                # 通过ID查找端口
                port_name = f"COM{port_id}"
                result = self.disconnect_port(port_name)
                if result['success']:
                    stopped_count += 1

            return {
                'success': True,
                'count': stopped_count,
                'message': f'成功停止{stopped_count}个端口'
            }

        except Exception as e:
            log_error(f"停止端口失败: {e}")
            return {
                'success': False,
                'message': str(e)
            }

    def clear_all_records(self) -> Dict[str, Any]:
        """清除所有端口记录"""
        try:
            if self.simulation_mode:
                if hasattr(self.port_manager, 'reset_all_statistics'):
                    self.port_manager.reset_all_statistics()
            else:
                # 真实模式清除
                if hasattr(self.port_manager, 'get_all_ports'):
                    for port in self.port_manager.get_all_ports():
                        if hasattr(port, 'reset_send_count'):
                            port.reset_send_count()

            log_info("已清除所有端口记录")
            return {'success': True}

        except Exception as e:
            log_error(f"清除所有记录失败: {e}")
            return {
                'success': False,
                'message': str(e)
            }

    def clear_ports_records(self, port_ids: List[int]) -> Dict[str, Any]:
        """清除指定端口记录"""
        try:
            cleared_count = 0

            for port_id in port_ids:
                port_name = f"COM{port_id}"
                if hasattr(self.port_manager, 'get_port'):
                    port = self.port_manager.get_port(port_name)
                    if port:
                        if hasattr(port, 'clear_statistics'):
                            port.clear_statistics()
                        elif hasattr(port, 'reset_send_count'):
                            port.reset_send_count()
                        cleared_count += 1

            return {
                'success': True,
                'count': cleared_count,
                'message': f'成功清除{cleared_count}个端口记录'
            }

        except Exception as e:
            log_error(f"清除端口记录失败: {e}")
            return {
                'success': False,
                'message': str(e)
            }

    def connect_all_ports(self) -> Dict[str, Any]:
        """连接所有端口"""
        try:
            connected_count = 0

            if self.simulation_mode:
                for port_name in self.port_manager.get_all_ports():
                    if self.port_manager.connect_port(port_name):
                        connected_count += 1
            else:
                if hasattr(self.port_manager, 'connect_all_ports'):
                    connected_count = self.port_manager.connect_all_ports()

            return {
                'success': True,
                'connected_count': connected_count,
                'message': f'成功连接{connected_count}个端口'
            }

        except Exception as e:
            log_error(f"连接所有端口失败: {e}")
            return {
                'success': False,
                'message': str(e)
            }

    def disconnect_all_ports(self) -> Dict[str, Any]:
        """断开所有端口"""
        try:
            disconnected_count = 0

            if self.simulation_mode:
                for port_name in self.port_manager.get_all_ports():
                    if hasattr(self.port_manager, 'disconnect_port'):
                        if self.port_manager.disconnect_port(port_name):
                            disconnected_count += 1
            else:
                if hasattr(self.port_manager, 'disconnect_all_ports'):
                    disconnected_count = self.port_manager.disconnect_all_ports()

            return {
                'success': True,
                'disconnected_count': disconnected_count,
                'message': f'成功断开{disconnected_count}个端口'
            }

        except Exception as e:
            log_error(f"断开所有端口失败: {e}")
            return {
                'success': False,
                'message': str(e)
            }

    def _format_port_info(self, port) -> Dict[str, Any]:
        """格式化端口信息（统一接口）"""
        try:
            # 对于模拟端口，直接从端口对象获取最新数据
            if hasattr(port, 'send_count'):
                send_count = port.send_count  # 直接获取当前值
            else:
                send_count = 0

            # 尝试不同的方法获取端口信息
            if hasattr(port, 'get_status_info'):
                # 模拟端口
                info = port.get_status_info()
                port_name = getattr(port, 'port_name', 'Unknown')
                return {
                    'id': int(port_name.replace('COM', '')) if 'COM' in port_name else 0,
                    'name': port_name,
                    'port_name': port_name,
                    'carrier': info.get('carrier', '未知'),
                    'status': info.get('status', 'offline'),
                    'limit': info.get('send_limit', 60),
                    'send_count': info.get('send_count', 0),
                    'success_count': info.get('success_count', 0),
                    'failed_count': info.get('failed_count', 0),
                    'is_connected': info.get('is_connected', False),
                    'is_selected': info.get('is_selected', False)
                }
            elif hasattr(port, 'get_summary'):
                # 真实端口
                info = port.get_summary()
                port_name = getattr(port, 'port_name', 'Unknown')
                return {
                    'id': int(port_name.replace('COM', '')) if 'COM' in port_name else 0,
                    'name': port_name,
                    'port_name': port_name,
                    'carrier': info.get('carrier_display', '未知'),
                    'status': info.get('status', 'offline'),
                    'limit': info.get('send_progress', {}).get('limit', 60),
                    'send_count': info.get('send_progress', {}).get('current', 0),
                    'success_count': info.get('statistics', {}).get('success', 0),
                    'failed_count': info.get('statistics', {}).get('failed', 0),
                    'is_connected': getattr(port, 'is_connected', False),
                    'is_selected': getattr(port, 'is_selected', False)
                }
            else:
                # 基本格式
                port_name = getattr(port, 'port_name', 'Unknown')
                return {
                    'id': int(port_name.replace('COM', '')) if 'COM' in port_name else 0,
                    'name': port_name,
                    'port_name': port_name,
                    'carrier': getattr(port, 'carrier', '未知'),
                    'status': getattr(port, 'status', 'offline'),
                    'limit': getattr(port, 'send_limit', 60),
                    'send_count': getattr(port, 'send_count', 0),
                    'success_count': getattr(port, 'success_count', 0),
                    'failed_count': getattr(port, 'failed_count', 0),
                    'is_connected': getattr(port, 'is_connected', False),
                    'is_selected': getattr(port, 'is_selected', False)
                }
        except Exception as e:
            log_error(f"格式化端口信息失败: {e}")
            return {
                'id': 0,
                'name': 'Unknown',
                'port_name': 'Unknown',
                'carrier': '未知',
                'status': 'error',
                'limit': 60,
                'send_count': 0,
                'success_count': 0,
                'failed_count': 0,
                'is_connected': False,
                'is_selected': False
            }

    def _start_status_monitoring(self):
        """启动状态监控"""
        try:
            if self._status_check_timer:
                self._status_check_timer.cancel()

            self._status_check_timer = threading.Timer(
                self.check_interval,
                self._status_check_callback
            )
            self._status_check_timer.daemon = True
            self._status_check_timer.start()

        except Exception as e:
            log_error(f"启动状态监控失败: {e}")

    def _stop_status_monitoring(self):
        """停止状态监控"""
        try:
            if self._status_check_timer:
                self._status_check_timer.cancel()
                self._status_check_timer = None

        except Exception as e:
            log_error(f"停止状态监控失败: {e}")

    def _status_check_callback(self):
        """状态检查回调"""
        try:
            if self.is_initialized:
                # 自动扫描
                if self.auto_scan:
                    if (self._last_scan_time is None or
                        datetime.now() - self._last_scan_time > timedelta(minutes=1)):
                        self.scan_ports()

            # 重新启动定时器
            if self.is_initialized:
                self._start_status_monitoring()

        except Exception as e:
            log_error(f"状态检查异常: {e}")
            if self.is_initialized:
                self._start_status_monitoring()

    def _notify_port_change(self, action: str, ports: List):
        """通知端口变化"""
        try:
            for callback in self._port_change_callbacks:
                try:
                    callback(action, ports)
                except Exception as e:
                    log_error(f"端口变化回调执行失败: {e}")

        except Exception as e:
            log_error(f"通知端口变化失败: {e}")

    def add_port_change_callback(self, callback: Callable):
        """添加端口变化回调"""
        if callable(callback):
            self._port_change_callbacks.append(callback)

    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        return {
            'running': self.is_initialized,
            'mode': 'simulation' if self.simulation_mode else 'real',
            'auto_scan': self.auto_scan,
            'check_interval': self.check_interval,
            'last_scan': self._last_scan_time.isoformat() if self._last_scan_time else None
        }


# 全局端口服务实例（替换原有的）
port_service = EnhancedPortService()

# 为了兼容性，创建类别名
PortService = EnhancedPortService


# 测试代码
if __name__ == "__main__":
    print("=" * 50)
    print("增强版端口服务测试")
    print("=" * 50)

    # 初始化服务
    print("\n初始化端口服务...")
    if port_service.initialize():
        print("✅ 初始化成功")

        # 获取服务状态
        status = port_service.get_status()
        print(f"\n服务状态:")
        print(f"  运行模式: {status['mode']}")
        print(f"  自动扫描: {status['auto_scan']}")

        # 扫描端口
        print("\n扫描端口...")
        scan_result = port_service.scan_ports()
        if scan_result['success']:
            print(f"✅ 发现 {scan_result['total_count']} 个端口")

            # 显示端口信息
            for port in scan_result['ports'][:5]:  # 只显示前5个
                print(f"  - {port['name']}: {port['carrier']} ({port['status']})")

        # 连接端口测试
        print("\n连接端口COM1...")
        connect_result = port_service.connect_port("COM1")
        if connect_result['success']:
            print("✅ 连接成功")

        # 关闭服务
        print("\n关闭服务...")
        port_service.shutdown()
        print("✅ 服务已关闭")