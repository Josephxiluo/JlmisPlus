"""
猫池短信系统端口扫描器 - tkinter版
Port scanner for SMS Pool System - tkinter version
"""

import sys
import time
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Callable
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from config.settings import settings
    from config.logging_config import get_logger, log_port_action, log_error, log_info
    from .utils import is_valid_port_name, format_duration
except ImportError:
    """
    猫池短信系统端口扫描器 - tkinter版
    Port scanner for SMS Pool System - tkinter version
    """

import sys
import time
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Callable
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from config.settings import settings
    from config.logging_config import get_logger, log_port_action, log_error, log_info
    from .utils import is_valid_port_name, format_duration
except ImportError:
    # 简化处理
    class MockSettings:
        PORT_SCAN_TIMEOUT = 5
        AUTO_PORT_SCAN = True
        PORT_BAUD_RATE = 115200

    settings = MockSettings()

    import logging
    def get_logger(name='core.port_scanner'):
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

    def is_valid_port_name(port_name):
        import re
        return bool(re.match(r'^COM\d+', port_name.upper())) if port_name else False

    def format_duration(seconds):
        if seconds < 60:
            return f"{seconds:.1f}秒"
        return f"{int(seconds // 60)}分{int(seconds % 60)}秒"

logger = get_logger('core.port_scanner')


class PortInfo:
    """端口信息类"""

    def __init__(self, port_name: str, description: str = "", manufacturer: str = ""):
        self.port_name = port_name
        self.description = description
        self.manufacturer = manufacturer
        self.is_available = False
        self.is_modem = False
        self.last_scan_time: Optional[datetime] = None
        self.response_time: Optional[float] = None
        self.error_message: Optional[str] = None
        self.device_info: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'port_name': self.port_name,
            'description': self.description,
            'manufacturer': self.manufacturer,
            'is_available': self.is_available,
            'is_modem': self.is_modem,
            'last_scan_time': self.last_scan_time.isoformat() if self.last_scan_time else None,
            'response_time': self.response_time,
            'error_message': self.error_message,
            'device_info': self.device_info
        }


class PortScanner:
    """端口扫描器类"""

    def __init__(self):
        """初始化端口扫描器"""
        self._lock = threading.Lock()
        self._scan_callbacks: List[Callable] = []
        self._discovered_ports: Dict[str, PortInfo] = {}
        self._scan_history: List[Dict[str, Any]] = []
        self._is_scanning = False
        self._scan_thread: Optional[threading.Thread] = None

        # 配置参数
        self.scan_timeout = getattr(settings, 'PORT_SCAN_TIMEOUT', 5)
        self.auto_scan = getattr(settings, 'AUTO_PORT_SCAN', True)
        self.default_baud_rate = getattr(settings, 'PORT_BAUD_RATE', 115200)

        # 扫描统计
        self.total_scans = 0
        self.successful_scans = 0
        self.last_scan_time: Optional[datetime] = None
        self.last_scan_duration: Optional[float] = None

    def initialize(self) -> bool:
        """初始化扫描器"""
        try:
            log_info("端口扫描器初始化开始")

            # 执行初始扫描
            if self.auto_scan:
                self.scan_ports()

            log_info("端口扫描器初始化完成")
            return True

        except Exception as e:
            log_error("端口扫描器初始化失败", error=e)
            return False

    def shutdown(self):
        """关闭扫描器"""
        try:
            log_info("端口扫描器开始关闭")

            # 停止正在进行的扫描
            self.stop_scan()

            # 清理数据
            self._discovered_ports.clear()
            self._scan_callbacks.clear()

            log_info("端口扫描器关闭完成")

        except Exception as e:
            log_error("端口扫描器关闭失败", error=e)

    def get_status(self) -> Dict[str, Any]:
        """获取扫描器状态"""
        return {
            'is_scanning': self._is_scanning,
            'discovered_ports_count': len(self._discovered_ports),
            'total_scans': self.total_scans,
            'successful_scans': self.successful_scans,
            'last_scan_time': self.last_scan_time.isoformat() if self.last_scan_time else None,
            'last_scan_duration': self.last_scan_duration,
            'scan_timeout': self.scan_timeout,
            'auto_scan': self.auto_scan
        }

    def scan_ports(self, force_rescan: bool = False) -> Dict[str, Any]:
        """扫描COM端口"""
        try:
            with self._lock:
                if self._is_scanning and not force_rescan:
                    return {
                        'success': False,
                        'message': '端口扫描正在进行中',
                        'ports': []
                    }

                self._is_scanning = True
                scan_start_time = time.time()

                log_info("开始扫描COM端口")

                # 扫描系统端口
                system_ports = self._scan_system_ports()

                # 检测端口可用性
                available_ports = []
                for port_info in system_ports:
                    if self._test_port_availability(port_info):
                        available_ports.append(port_info)
                        self._discovered_ports[port_info.port_name] = port_info

                # 记录扫描结果
                scan_duration = time.time() - scan_start_time
                self.last_scan_time = datetime.now()
                self.last_scan_duration = scan_duration
                self.total_scans += 1

                if available_ports:
                    self.successful_scans += 1

                # 记录扫描历史
                scan_record = {
                    'scan_time': self.last_scan_time.isoformat(),
                    'duration': scan_duration,
                    'ports_found': len(available_ports),
                    'ports': [port.to_dict() for port in available_ports]
                }
                self._scan_history.append(scan_record)

                # 保持历史记录数量限制
                if len(self._scan_history) > 10:
                    self._scan_history.pop(0)

                # 通知回调
                self._notify_scan_complete(available_ports)

                log_info(f"端口扫描完成，发现{len(available_ports)}个可用端口，耗时{format_duration(scan_duration)}")

                return {
                    'success': True,
                    'message': f'扫描完成，发现{len(available_ports)}个可用端口',
                    'ports': [port.to_dict() for port in available_ports],
                    'scan_duration': scan_duration,
                    'total_ports': len(system_ports)
                }

        except Exception as e:
            log_error("端口扫描异常", error=e)
            return {
                'success': False,
                'message': f'扫描异常: {str(e)}',
                'ports': []
            }
        finally:
            self._is_scanning = False

    def scan_ports_async(self, callback: Optional[Callable] = None) -> bool:
        """异步扫描端口"""
        try:
            if self._is_scanning:
                return False

            def scan_worker():
                result = self.scan_ports()
                if callback:
                    callback(result)

            self._scan_thread = threading.Thread(target=scan_worker, daemon=True)
            self._scan_thread.start()

            return True

        except Exception as e:
            log_error("异步端口扫描启动失败", error=e)
            return False

    def stop_scan(self):
        """停止扫描"""
        try:
            if self._scan_thread and self._scan_thread.is_alive():
                # 设置停止标志
                self._is_scanning = False

                # 等待线程结束
                self._scan_thread.join(timeout=5)

                log_info("端口扫描已停止")

        except Exception as e:
            log_error("停止端口扫描失败", error=e)

    def get_discovered_ports(self) -> List[Dict[str, Any]]:
        """获取已发现的端口"""
        return [port.to_dict() for port in self._discovered_ports.values()]

    def get_port_info(self, port_name: str) -> Optional[Dict[str, Any]]:
        """获取指定端口信息"""
        port_info = self._discovered_ports.get(port_name)
        return port_info.to_dict() if port_info else None

    def test_port(self, port_name: str) -> Dict[str, Any]:
        """测试单个端口"""
        try:
            if not is_valid_port_name(port_name):
                return {
                    'success': False,
                    'message': '无效的端口名称',
                    'port_name': port_name
                }

            log_info(f"测试端口: {port_name}")

            # 创建端口信息对象
            port_info = PortInfo(port_name, f"测试端口 {port_name}")

            # 测试端口可用性
            if self._test_port_availability(port_info):
                # 更新已发现端口列表
                self._discovered_ports[port_name] = port_info

                return {
                    'success': True,
                    'message': f'端口{port_name}测试成功',
                    'port_info': port_info.to_dict()
                }
            else:
                return {
                    'success': False,
                    'message': f'端口{port_name}不可用',
                    'port_name': port_name,
                    'error': port_info.error_message
                }

        except Exception as e:
            log_error(f"测试端口{port_name}异常", error=e)
            return {
                'success': False,
                'message': f'测试异常: {str(e)}',
                'port_name': port_name
            }

    def _scan_system_ports(self) -> List[PortInfo]:
        """扫描系统端口"""
        ports = []

        try:
            import serial.tools.list_ports

            # 获取系统端口列表
            system_ports = serial.tools.list_ports.comports()

            for port in system_ports:
                port_info = PortInfo(
                    port_name=port.device,
                    description=port.description or "",
                    manufacturer=getattr(port, 'manufacturer', '') or ""
                )

                # 添加设备信息
                port_info.device_info = {
                    'vid': getattr(port, 'vid', None),
                    'pid': getattr(port, 'pid', None),
                    'serial_number': getattr(port, 'serial_number', None),
                    'hwid': getattr(port, 'hwid', '')
                }

                ports.append(port_info)

        except ImportError:
            log_error("需要安装pyserial库")
            # 手动扫描COM端口（Windows）
            ports = self._manual_scan_com_ports()

        except Exception as e:
            log_error("扫描系统端口失败", error=e)

        return ports

    def _manual_scan_com_ports(self) -> List[PortInfo]:
        """手动扫描COM端口（Windows）"""
        ports = []

        try:
            # 尝试COM1到COM20
            for i in range(1, 21):
                port_name = f"COM{i}"
                port_info = PortInfo(port_name, f"COM端口 {i}")
                ports.append(port_info)

        except Exception as e:
            log_error("手动扫描COM端口失败", error=e)

        return ports

    def _test_port_availability(self, port_info: PortInfo) -> bool:
        """测试端口可用性"""
        try:
            import serial

            start_time = time.time()

            # 尝试打开端口
            with serial.Serial(
                port=port_info.port_name,
                baudrate=self.default_baud_rate,
                timeout=self.scan_timeout
            ) as ser:
                # 记录响应时间
                port_info.response_time = time.time() - start_time
                port_info.last_scan_time = datetime.now()
                port_info.is_available = True

                # 测试是否为调制解调器
                port_info.is_modem = self._test_modem_capability(ser)

                log_port_action(
                    port_info.port_name,
                    "可用性测试",
                    f"响应时间: {port_info.response_time:.3f}秒",
                    success=True
                )

                return True

        except ImportError:
            log_error("需要安装pyserial库")
            port_info.error_message = "缺少pyserial库"
            return False

        except Exception as e:
            port_info.error_message = str(e)
            port_info.last_scan_time = datetime.now()
            port_info.is_available = False

            log_port_action(
                port_info.port_name,
                "可用性测试",
                str(e),
                success=False
            )

            return False

    def _test_modem_capability(self, serial_port) -> bool:
        """测试调制解调器能力"""
        try:
            # 发送AT命令测试
            serial_port.write(b'AT\r\n')
            serial_port.flush()

            # 等待响应
            time.sleep(0.5)

            if serial_port.in_waiting > 0:
                response = serial_port.read(serial_port.in_waiting).decode('utf-8', errors='ignore')
                return 'OK' in response.upper()

            return False

        except Exception:
            return False

    def add_scan_callback(self, callback: Callable[[List[PortInfo]], None]):
        """添加扫描完成回调"""
        if callable(callback):
            self._scan_callbacks.append(callback)
            log_info(f"添加端口扫描回调函数，当前回调数量: {len(self._scan_callbacks)}")

    def remove_scan_callback(self, callback: Callable[[List[PortInfo]], None]):
        """移除扫描完成回调"""
        if callback in self._scan_callbacks:
            self._scan_callbacks.remove(callback)
            log_info(f"移除端口扫描回调函数，当前回调数量: {len(self._scan_callbacks)}")

    def _notify_scan_complete(self, ports: List[PortInfo]):
        """通知扫描完成"""
        try:
            for callback in self._scan_callbacks:
                try:
                    callback(ports)
                except Exception as e:
                    log_error("端口扫描回调执行失败", error=e)
        except Exception as e:
            log_error("通知端口扫描完成失败", error=e)

    def get_scan_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取扫描历史"""
        return self._scan_history[-limit:] if limit > 0 else self._scan_history

    def get_scan_statistics(self) -> Dict[str, Any]:
        """获取扫描统计"""
        success_rate = 0.0
        if self.total_scans > 0:
            success_rate = round(self.successful_scans / self.total_scans * 100, 2)

        avg_ports_found = 0.0
        if self._scan_history:
            total_ports = sum(record['ports_found'] for record in self._scan_history)
            avg_ports_found = round(total_ports / len(self._scan_history), 2)

        avg_scan_time = 0.0
        if self._scan_history:
            total_time = sum(record['duration'] for record in self._scan_history)
            avg_scan_time = round(total_time / len(self._scan_history), 3)

        return {
            'total_scans': self.total_scans,
            'successful_scans': self.successful_scans,
            'success_rate': success_rate,
            'discovered_ports_count': len(self._discovered_ports),
            'avg_ports_found': avg_ports_found,
            'avg_scan_time': avg_scan_time,
            'last_scan_time': self.last_scan_time.isoformat() if self.last_scan_time else None,
            'last_scan_duration': self.last_scan_duration
        }

    def clear_discovered_ports(self):
        """清除已发现的端口"""
        try:
            cleared_count = len(self._discovered_ports)
            self._discovered_ports.clear()
            log_info(f"清除了{cleared_count}个已发现的端口")
        except Exception as e:
            log_error("清除已发现端口失败", error=e)

    def export_port_list(self) -> Dict[str, Any]:
        """导出端口列表"""
        try:
            export_data = {
                'export_time': datetime.now().isoformat(),
                'scan_statistics': self.get_scan_statistics(),
                'ports': self.get_discovered_ports(),
                'scan_history': self.get_scan_history()
            }

            return {
                'success': True,
                'message': f'成功导出{len(self._discovered_ports)}个端口信息',
                'data': export_data
            }

        except Exception as e:
            log_error("导出端口列表失败", error=e)
            return {
                'success': False,
                'message': f'导出失败: {str(e)}'
            }

    def set_scan_timeout(self, timeout_seconds: int):
        """设置扫描超时时间"""
        try:
            if timeout_seconds < 1:
                timeout_seconds = 1
            elif timeout_seconds > 30:
                timeout_seconds = 30

            old_timeout = self.scan_timeout
            self.scan_timeout = timeout_seconds

            log_info(f"端口扫描超时时间已更新: {old_timeout}秒 -> {timeout_seconds}秒")

        except Exception as e:
            log_error("设置扫描超时时间失败", error=e)

    def set_default_baud_rate(self, baud_rate: int):
        """设置默认波特率"""
        try:
            valid_rates = [9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600]

            if baud_rate not in valid_rates:
                log_error(f"无效的波特率: {baud_rate}，有效值: {valid_rates}")
                return

            old_rate = self.default_baud_rate
            self.default_baud_rate = baud_rate

            log_info(f"默认波特率已更新: {old_rate} -> {baud_rate}")

        except Exception as e:
            log_error("设置默认波特率失败", error=e)

    def refresh_port_info(self, port_name: str) -> Dict[str, Any]:
        """刷新指定端口信息"""
        try:
            if port_name not in self._discovered_ports:
                return {
                    'success': False,
                    'message': f'端口{port_name}未在已发现列表中'
                }

            port_info = self._discovered_ports[port_name]

            # 重新测试端口
            if self._test_port_availability(port_info):
                return {
                    'success': True,
                    'message': f'端口{port_name}信息刷新成功',
                    'port_info': port_info.to_dict()
                }
            else:
                return {
                    'success': False,
                    'message': f'端口{port_name}当前不可用',
                    'port_info': port_info.to_dict()
                }

        except Exception as e:
            log_error(f"刷新端口{port_name}信息失败", error=e)
            return {
                'success': False,
                'message': f'刷新失败: {str(e)}'
            }

    def get_modem_ports(self) -> List[Dict[str, Any]]:
        """获取调制解调器端口"""
        modem_ports = []

        for port_info in self._discovered_ports.values():
            if port_info.is_modem:
                modem_ports.append(port_info.to_dict())

        return modem_ports

    def diagnose_port_issues(self) -> Dict[str, Any]:
        """诊断端口问题"""
        try:
            issues = []
            recommendations = []

            # 检查是否有可用端口
            if not self._discovered_ports:
                issues.append("未发现任何可用的COM端口")
                recommendations.append("请检查设备连接和驱动程序安装")

            # 检查调制解调器端口
            modem_count = len(self.get_modem_ports())
            if modem_count == 0:
                issues.append("未发现调制解调器端口")
                recommendations.append("请确认设备支持AT命令")

            # 检查端口响应时间
            slow_ports = []
            for port_info in self._discovered_ports.values():
                if port_info.response_time and port_info.response_time > 2.0:
                    slow_ports.append(port_info.port_name)

            if slow_ports:
                issues.append(f"端口响应较慢: {', '.join(slow_ports)}")
                recommendations.append("考虑检查端口配置或更换设备")

            # 检查扫描成功率
            stats = self.get_scan_statistics()
            if stats['success_rate'] < 80:
                issues.append(f"扫描成功率较低: {stats['success_rate']}%")
                recommendations.append("建议检查系统环境和设备状态")

            return {
                'issues_found': len(issues),
                'issues': issues,
                'recommendations': recommendations,
                'scan_statistics': stats,
                'diagnosis_time': datetime.now().isoformat()
            }

        except Exception as e:
            log_error("诊断端口问题失败", error=e)
            return {
                'issues_found': 0,
                'issues': [f"诊断异常: {str(e)}"],
                'recommendations': []
            }


# 全局端口扫描器实例
port_scanner = PortScanner()