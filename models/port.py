"""
猫池短信系统端口模型 - tkinter版
Port models for SMS Pool System - tkinter version
"""

import sys
import re
import time
import threading
from enum import Enum
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from .base import BaseModel, ModelManager
    from .message import MessageCarrier
    from config.settings import settings
    from config.logging_config import get_logger, log_port_action, log_error
except ImportError:
    # 简化处理
    from base import BaseModel, ModelManager

    class MessageCarrier:
        MOBILE = "mobile"
        UNICOM = "unicom"
        TELECOM = "telecom"
        UNKNOWN = "unknown"

    class MockSettings:
        PORT_BAUD_RATE = 115200
        PORT_DATA_BITS = 8
        PORT_STOP_BITS = 1
        PORT_PARITY = 'N'
        DEFAULT_SEND_INTERVAL = 1000
        CARD_SWITCH_INTERVAL = 60

    settings = MockSettings()

    import logging
    def get_logger(name='models.port'):
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

logger = get_logger('models.port')


class PortStatus(Enum):
    """端口状态枚举"""
    AVAILABLE = "available"    # 可用
    BUSY = "busy"             # 忙碌
    ERROR = "error"           # 错误
    OFFLINE = "offline"       # 离线
    DISABLED = "disabled"     # 禁用

    @classmethod
    def get_choices(cls):
        """获取所有选择项"""
        return [status.value for status in cls]

    @classmethod
    def get_display_names(cls):
        """获取显示名称映射"""
        return {
            cls.AVAILABLE.value: "可用",
            cls.BUSY.value: "忙碌",
            cls.ERROR.value: "错误",
            cls.OFFLINE.value: "离线",
            cls.DISABLED.value: "禁用"
        }


class PortCarrier(Enum):
    """端口运营商枚举"""
    MOBILE = "mobile"     # 中国移动
    UNICOM = "unicom"     # 中国联通
    TELECOM = "telecom"   # 中国电信
    UNKNOWN = "unknown"   # 未知

    @classmethod
    def get_choices(cls):
        """获取所有选择项"""
        return [carrier.value for carrier in cls]

    @classmethod
    def get_display_names(cls):
        """获取显示名称映射"""
        return {
            cls.MOBILE.value: "中国移动",
            cls.UNICOM.value: "中国联通",
            cls.TELECOM.value: "中国电信",
            cls.UNKNOWN.value: "未知"
        }


@dataclass
class Port(BaseModel):
    """端口设备模型"""

    # 表名（这是一个内存模型，不直接对应数据库表）
    _table_name: str = "ports"

    # 验证规则
    _validation_rules: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        'port_name': {
            'required': True,
            'type': str,
            'pattern': r'^COM\d+$',
            'message': '端口名称格式必须是COMx'
        },
        'status': {
            'required': True,
            'type': str,
            'choices': PortStatus.get_choices(),
            'message': '端口状态无效'
        },
        'carrier': {
            'type': str,
            'choices': PortCarrier.get_choices(),
            'message': '运营商类型无效'
        },
        'send_limit': {
            'type': int,
            'min_value': 1,
            'max_value': 10000,
            'message': '发送上限必须在1-10000之间'
        },
        'send_interval': {
            'type': int,
            'min_value': 100,
            'max_value': 10000,
            'message': '发送间隔必须在100-10000毫秒之间'
        },
        'baud_rate': {
            'type': int,
            'choices': [9600, 19200, 38400, 57600, 115200],
            'message': '波特率必须是有效值'
        }
    })

    # 端口基本信息
    port_name: str = ""  # COM1, COM2等
    device_path: Optional[str] = field(default=None)  # 设备路径
    status: str = PortStatus.OFFLINE.value
    carrier: str = PortCarrier.UNKNOWN.value

    # 发送控制
    send_limit: int = 60  # 发送上限
    send_count: int = 0   # 已发送数量
    send_interval: int = 1000  # 发送间隔（毫秒）

    # 串口配置
    baud_rate: int = 115200
    data_bits: int = 8
    stop_bits: int = 1
    parity: str = 'N'

    # 状态信息
    is_connected: bool = False
    is_selected: bool = False  # 是否被选中
    last_activity: Optional[datetime] = field(default=None)
    error_message: Optional[str] = field(default=None)

    # 统计信息
    success_count: int = 0
    failed_count: int = 0
    total_sent: int = 0

    # 运行时信息
    current_task_id: Optional[int] = field(default=None)
    last_send_time: Optional[datetime] = field(default=None)

    # 内部状态（不保存到数据库）
    _serial_connection = field(default=None, init=False, repr=False)
    _lock = field(default_factory=threading.Lock, init=False, repr=False)

    def __post_init__(self):
        """初始化后处理"""
        super().__post_init__()

        # 设置默认发送间隔
        if self.send_interval == 0:
            self.send_interval = getattr(settings, 'DEFAULT_SEND_INTERVAL', 1000)

    def get_status_display(self) -> str:
        """获取状态显示名称"""
        return PortStatus.get_display_names().get(self.status, self.status)

    def get_carrier_display(self) -> str:
        """获取运营商显示名称"""
        return PortCarrier.get_display_names().get(self.carrier, self.carrier)

    def is_available(self) -> bool:
        """是否可用"""
        return (self.status == PortStatus.AVAILABLE.value and
                self.is_connected and
                not self.is_send_limit_reached())

    def is_busy(self) -> bool:
        """是否忙碌"""
        return self.status == PortStatus.BUSY.value

    def is_error(self) -> bool:
        """是否错误状态"""
        return self.status == PortStatus.ERROR.value

    def is_offline(self) -> bool:
        """是否离线"""
        return self.status == PortStatus.OFFLINE.value

    def is_disabled(self) -> bool:
        """是否禁用"""
        return self.status == PortStatus.DISABLED.value

    def is_send_limit_reached(self) -> bool:
        """是否达到发送上限"""
        return self.send_count >= self.send_limit

    def can_send(self) -> bool:
        """是否可以发送"""
        if not self.is_available():
            return False

        # 检查发送间隔
        if self.last_send_time:
            time_since_last = datetime.now() - self.last_send_time
            if time_since_last.total_seconds() * 1000 < self.send_interval:
                return False

        return True

    def update_status(self, new_status: str, error_message: str = None) -> bool:
        """更新端口状态"""
        try:
            with self._lock:
                old_status = self.status
                self.status = new_status
                self.last_activity = datetime.now()

                if new_status == PortStatus.ERROR.value:
                    self.error_message = error_message
                    self.is_connected = False
                elif new_status == PortStatus.OFFLINE.value:
                    self.is_connected = False
                    self.error_message = None
                elif new_status == PortStatus.AVAILABLE.value:
                    self.is_connected = True
                    self.error_message = None

                log_port_action(
                    self.port_name,
                    f"状态变更: {old_status} -> {new_status}",
                    details=error_message
                )

                return True

        except Exception as e:
            log_error("更新端口状态失败", error=e)
            return False

    def mark_as_busy(self, task_id: int = None) -> bool:
        """标记为忙碌状态"""
        self.current_task_id = task_id
        return self.update_status(PortStatus.BUSY.value)

    def mark_as_available(self) -> bool:
        """标记为可用状态"""
        self.current_task_id = None
        return self.update_status(PortStatus.AVAILABLE.value)

    def mark_as_error(self, error_message: str) -> bool:
        """标记为错误状态"""
        return self.update_status(PortStatus.ERROR.value, error_message)

    def mark_as_offline(self) -> bool:
        """标记为离线状态"""
        return self.update_status(PortStatus.OFFLINE.value)

    def connect(self) -> bool:
        """连接端口"""
        try:
            import serial

            with self._lock:
                # 如果已连接，先断开
                if self._serial_connection and self._serial_connection.is_open:
                    self._serial_connection.close()

                # 创建串口连接
                self._serial_connection = serial.Serial(
                    port=self.port_name,
                    baudrate=self.baud_rate,
                    bytesize=self.data_bits,
                    stopbits=self.stop_bits,
                    parity=self.parity,
                    timeout=1
                )

                if self._serial_connection.is_open:
                    self.is_connected = True
                    self.mark_as_available()
                    log_port_action(self.port_name, "连接", success=True)
                    return True

                return False

        except ImportError:
            log_error("需要安装pyserial库")
            return False
        except Exception as e:
            self.mark_as_error(f"连接失败: {str(e)}")
            log_port_action(self.port_name, "连接", details=str(e), success=False)
            return False

    def disconnect(self) -> bool:
        """断开端口连接"""
        try:
            with self._lock:
                if self._serial_connection and self._serial_connection.is_open:
                    self._serial_connection.close()

                self.is_connected = False
                self.mark_as_offline()
                log_port_action(self.port_name, "断开连接", success=True)
                return True

        except Exception as e:
            log_error("断开端口连接失败", error=e)
            return False

    def send_at_command(self, command: str, timeout: int = 5) -> Optional[str]:
        """发送AT命令"""
        try:
            with self._lock:
                if not self.is_connected or not self._serial_connection:
                    return None

                # 发送命令
                cmd = f"{command}\r\n"
                self._serial_connection.write(cmd.encode())

                # 读取响应
                start_time = time.time()
                response = ""

                while time.time() - start_time < timeout:
                    if self._serial_connection.in_waiting > 0:
                        data = self._serial_connection.read(self._serial_connection.in_waiting)
                        response += data.decode('utf-8', errors='ignore')

                        # 检查是否收到完整响应
                        if 'OK' in response or 'ERROR' in response:
                            break

                    time.sleep(0.1)

                return response.strip()

        except Exception as e:
            log_error(f"发送AT命令失败: {command}", error=e)
            return None

    def send_sms(self, phone: str, message: str) -> bool:
        """发送短信"""
        try:
            if not self.can_send():
                return False

            with self._lock:
                # 标记为忙碌
                self.mark_as_busy()

                # 设置短信模式
                response = self.send_at_command("AT+CMGF=1")
                if not response or "OK" not in response:
                    self.mark_as_error("设置短信模式失败")
                    return False

                # 发送短信
                cmd = f'AT+CMGS="{phone}"'
                response = self.send_at_command(cmd)
                if not response or ">" not in response:
                    self.mark_as_error("发送短信命令失败")
                    return False

                # 发送消息内容
                msg_cmd = f"{message}\x1A"  # \x1A 是 Ctrl+Z
                self._serial_connection.write(msg_cmd.encode())

                # 等待发送结果
                start_time = time.time()
                response = ""

                while time.time() - start_time < 30:  # 30秒超时
                    if self._serial_connection.in_waiting > 0:
                        data = self._serial_connection.read(self._serial_connection.in_waiting)
                        response += data.decode('utf-8', errors='ignore')

                        if '+CMGS:' in response and 'OK' in response:
                            # 发送成功
                            self.record_send_result(True)
                            self.mark_as_available()
                            return True
                        elif 'ERROR' in response:
                            # 发送失败
                            self.record_send_result(False)
                            self.mark_as_error("短信发送失败")
                            return False

                    time.sleep(0.1)

                # 超时
                self.record_send_result(False)
                self.mark_as_error("短信发送超时")
                return False

        except Exception as e:
            self.record_send_result(False)
            self.mark_as_error(f"发送短信异常: {str(e)}")
            log_error("发送短信失败", error=e)
            return False

    def record_send_result(self, success: bool):
        """记录发送结果"""
        self.send_count += 1
        self.total_sent += 1
        self.last_send_time = datetime.now()

        if success:
            self.success_count += 1
        else:
            self.failed_count += 1

    def reset_send_count(self):
        """重置发送计数"""
        self.send_count = 0
        log_port_action(self.port_name, "重置发送计数")

    def clear_statistics(self):
        """清除统计信息"""
        self.success_count = 0
        self.failed_count = 0
        self.total_sent = 0
        self.send_count = 0
        log_port_action(self.port_name, "清除统计信息")

    def get_signal_strength(self) -> Optional[int]:
        """获取信号强度"""
        try:
            response = self.send_at_command("AT+CSQ")
            if response and "+CSQ:" in response:
                # 解析信号强度
                match = re.search(r'\+CSQ:\s*(\d+),', response)
                if match:
                    rssi = int(match.group(1))
                    if rssi == 99:
                        return None  # 未知或不可检测
                    return rssi
            return None

        except Exception as e:
            log_error("获取信号强度失败", error=e)
            return None

    def get_network_info(self) -> Dict[str, Any]:
        """获取网络信息"""
        try:
            info = {
                'signal_strength': self.get_signal_strength(),
                'network_registration': None,
                'operator': None
            }

            # 网络注册状态
            response = self.send_at_command("AT+CREG?")
            if response and "+CREG:" in response:
                match = re.search(r'\+CREG:\s*\d+,(\d+)', response)
                if match:
                    status = int(match.group(1))
                    status_map = {
                        0: "未注册",
                        1: "已注册（本地网络）",
                        2: "未注册（正在搜索）",
                        3: "注册被拒绝",
                        5: "已注册（漫游）"
                    }
                    info['network_registration'] = status_map.get(status, f"未知({status})")

            # 运营商信息
            response = self.send_at_command("AT+COPS?")
            if response and "+COPS:" in response:
                match = re.search(r'\+COPS:\s*\d+,\d+,"([^"]+)"', response)
                if match:
                    info['operator'] = match.group(1)

            return info

        except Exception as e:
            log_error("获取网络信息失败", error=e)
            return {}

    def detect_carrier(self) -> str:
        """检测运营商"""
        try:
            network_info = self.get_network_info()
            operator = network_info.get('operator', '').lower()

            if 'mobile' in operator or '移动' in operator:
                return PortCarrier.MOBILE.value
            elif 'unicom' in operator or '联通' in operator:
                return PortCarrier.UNICOM.value
            elif 'telecom' in operator or '电信' in operator:
                return PortCarrier.TELECOM.value
            else:
                return PortCarrier.UNKNOWN.value

        except Exception as e:
            log_error("检测运营商失败", error=e)
            return PortCarrier.UNKNOWN.value

    def get_summary(self) -> Dict[str, Any]:
        """获取端口摘要"""
        return {
            'port_name': self.port_name,
            'status': self.status,
            'status_display': self.get_status_display(),
            'carrier': self.carrier,
            'carrier_display': self.get_carrier_display(),
            'is_connected': self.is_connected,
            'is_selected': self.is_selected,
            'send_progress': {
                'current': self.send_count,
                'limit': self.send_limit,
                'percentage': round(self.send_count / self.send_limit * 100, 2) if self.send_limit > 0 else 0
            },
            'statistics': {
                'success': self.success_count,
                'failed': self.failed_count,
                'total': self.total_sent,
                'success_rate': round(self.success_count / self.total_sent * 100, 2) if self.total_sent > 0 else 0
            },
            'config': {
                'send_interval': self.send_interval,
                'baud_rate': self.baud_rate
            },
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'error_message': self.error_message
        }

    @classmethod
    def scan_ports(cls) -> List[str]:
        """扫描可用的COM端口"""
        try:
            import serial.tools.list_ports

            ports = []
            for port_info in serial.tools.list_ports.comports():
                ports.append(port_info.device)

            return sorted(ports)

        except ImportError:
            log_error("需要安装pyserial库")
            return []
        except Exception as e:
            log_error("扫描端口失败", error=e)
            return []

    def save(self) -> bool:
        """保存端口信息（内存模型，不保存到数据库）"""
        # 端口信息通常不保存到数据库，而是保存到配置文件或内存中
        return True

    def delete(self) -> bool:
        """删除端口（内存模型）"""
        self.disconnect()
        return True


# 端口管理器
class PortManager:
    """端口管理器"""

    def __init__(self):
        self.ports: Dict[str, Port] = {}
        self._lock = threading.Lock()

    def scan_and_update_ports(self) -> List[Port]:
        """扫描并更新端口列表"""
        try:
            available_ports = Port.scan_ports()

            with self._lock:
                # 标记不存在的端口为离线
                for port_name in list(self.ports.keys()):
                    if port_name not in available_ports:
                        self.ports[port_name].mark_as_offline()

                # 添加新发现的端口
                for port_name in available_ports:
                    if port_name not in self.ports:
                        port = Port(
                            port_name=port_name,
                            status=PortStatus.OFFLINE.value,
                            send_limit=60,
                            send_interval=getattr(settings, 'DEFAULT_SEND_INTERVAL', 1000)
                        )
                        self.ports[port_name] = port

                return list(self.ports.values())

        except Exception as e:
            log_error("扫描和更新端口失败", error=e)
            return []

    def get_port(self, port_name: str) -> Optional[Port]:
        """获取指定端口"""
        return self.ports.get(port_name)

    def get_all_ports(self) -> List[Port]:
        """获取所有端口"""
        return list(self.ports.values())

    def get_available_ports(self) -> List[Port]:
        """获取可用端口"""
        return [port for port in self.ports.values() if port.is_available()]

    def get_selected_ports(self) -> List[Port]:
        """获取选中的端口"""
        return [port for port in self.ports.values() if port.is_selected]

    def get_ports_by_carrier(self, carrier: str) -> List[Port]:
        """根据运营商获取端口"""
        return [port for port in self.ports.values() if port.carrier == carrier]

    def connect_port(self, port_name: str) -> bool:
        """连接端口"""
        port = self.get_port(port_name)
        if port:
            return port.connect()
        return False

    def disconnect_port(self, port_name: str) -> bool:
        """断开端口"""
        port = self.get_port(port_name)
        if port:
            return port.disconnect()
        return False

    def connect_all_ports(self) -> int:
        """连接所有端口"""
        connected_count = 0
        for port in self.ports.values():
            if port.connect():
                connected_count += 1
        return connected_count

    def disconnect_all_ports(self) -> int:
        """断开所有端口"""
        disconnected_count = 0
        for port in self.ports.values():
            if port.disconnect():
                disconnected_count += 1
        return disconnected_count

    def select_port(self, port_name: str, selected: bool = True) -> bool:
        """选择/取消选择端口"""
        port = self.get_port(port_name)
        if port:
            port.is_selected = selected
            log_port_action(port_name, "选择" if selected else "取消选择")
            return True
        return False

    def select_all_ports(self) -> int:
        """选择所有端口"""
        selected_count = 0
        for port in self.ports.values():
            port.is_selected = True
            selected_count += 1
        log_port_action("所有端口", f"全选({selected_count}个)")
        return selected_count

    def unselect_all_ports(self) -> int:
        """取消选择所有端口"""
        unselected_count = 0
        for port in self.ports.values():
            port.is_selected = False
            unselected_count += 1
        log_port_action("所有端口", f"取消全选({unselected_count}个)")
        return unselected_count

    def invert_selection(self) -> int:
        """反选端口"""
        inverted_count = 0
        for port in self.ports.values():
            port.is_selected = not port.is_selected
            inverted_count += 1
        log_port_action("所有端口", f"反选({inverted_count}个)")
        return inverted_count

    def start_selected_ports(self) -> int:
        """启动选中的端口"""
        started_count = 0
        for port in self.get_selected_ports():
            if port.connect():
                started_count += 1
        log_port_action("选中端口", f"启动({started_count}个)")
        return started_count

    def stop_selected_ports(self) -> int:
        """停止选中的端口"""
        stopped_count = 0
        for port in self.get_selected_ports():
            if port.disconnect():
                stopped_count += 1
        log_port_action("选中端口", f"停止({stopped_count}个)")
        return stopped_count

    def clear_all_statistics(self) -> int:
        """清除所有端口统计"""
        cleared_count = 0
        for port in self.ports.values():
            port.clear_statistics()
            cleared_count += 1
        log_port_action("所有端口", f"清除统计({cleared_count}个)")
        return cleared_count

    def clear_selected_statistics(self) -> int:
        """清除选中端口统计"""
        cleared_count = 0
        for port in self.get_selected_ports():
            port.clear_statistics()
            cleared_count += 1
        log_port_action("选中端口", f"清除统计({cleared_count}个)")
        return cleared_count

    def reset_all_send_counts(self) -> int:
        """重置所有端口发送计数"""
        reset_count = 0
        for port in self.ports.values():
            port.reset_send_count()
            reset_count += 1
        log_port_action("所有端口", f"重置计数({reset_count}个)")
        return reset_count

    def reset_selected_send_counts(self) -> int:
        """重置选中端口发送计数"""
        reset_count = 0
        for port in self.get_selected_ports():
            port.reset_send_count()
            reset_count += 1
        log_port_action("选中端口", f"重置计数({reset_count}个)")
        return reset_count


# 全局端口管理器实例
port_manager = PortManager()