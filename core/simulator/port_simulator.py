"""
猫池短信系统端口模拟器
Port simulator for SMS Pool System
模拟20个虚拟COM端口，用于开发和测试
"""

import sys
import random
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.settings import settings
from config.logging_config import get_logger, log_port_action, log_info, log_error
from models.port import PortStatus, PortCarrier

logger = get_logger('core.simulator.port')


class SimulatedPortStatus(Enum):
    """模拟端口状态"""
    IDLE = "idle"
    SENDING = "sending"
    READY = "ready"
    ERROR = "error"
    BUSY = "busy"


@dataclass
class SimulatedPort:
    """模拟端口类"""

    port_name: str
    port_index: int
    carrier: str = PortCarrier.UNKNOWN.value
    status: str = SimulatedPortStatus.IDLE.value
    is_connected: bool = False
    is_selected: bool = False

    # 发送统计
    send_count: int = 0
    send_limit: int = 60
    success_count: int = 0
    failed_count: int = 0
    total_sent: int = 0

    # 配置参数
    send_interval: int = 1000  # 毫秒
    success_rate: float = 0.7  # 70%成功率
    response_time_range: Tuple[float, float] = (0.5, 3.0)  # 响应时间范围（秒）

    # 状态信息
    last_send_time: Optional[datetime] = field(default=None)
    last_activity: Optional[datetime] = field(default=None)
    signal_strength: int = field(default=31)  # 0-31, 99=未知
    error_message: Optional[str] = field(default=None)

    # 内部状态
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)
    _is_sending: bool = field(default=False, init=False)

    def __post_init__(self):
        """初始化后处理"""
        # 根据端口索引分配运营商
        carriers = [PortCarrier.MOBILE.value, PortCarrier.UNICOM.value, PortCarrier.TELECOM.value]
        self.carrier = carriers[self.port_index % 3]

        # 设置初始信号强度（模拟不同的信号质量）
        self.signal_strength = random.randint(15, 31)  # 中等到优秀信号

        # 根据端口索引设置不同的成功率（模拟端口质量差异）
        base_rate = 0.7
        variation = (self.port_index % 5) * 0.05  # ±0.25的变化
        self.success_rate = min(0.95, max(0.45, base_rate + variation - 0.1))

        log_info(f"初始化模拟端口 {self.port_name}, 运营商: {self.carrier}, 成功率: {self.success_rate:.2%}")

    def connect(self) -> bool:
        """连接端口"""
        with self._lock:
            if self.is_connected:
                return True

            # 模拟连接过程
            time.sleep(random.uniform(0.1, 0.3))

            # 随机连接失败（5%概率）
            if random.random() < 0.05:
                self.error_message = "连接失败：端口无响应"
                self.status = SimulatedPortStatus.ERROR.value
                log_port_action(self.port_name, "连接", details=self.error_message, success=False)
                return False

            self.is_connected = True
            self.status = SimulatedPortStatus.READY.value
            self.last_activity = datetime.now()
            self.error_message = None

            log_port_action(self.port_name, "连接", success=True)
            return True

    def disconnect(self) -> bool:
        """断开端口"""
        with self._lock:
            self.is_connected = False
            self.status = SimulatedPortStatus.IDLE.value
            self._is_sending = False
            self.last_activity = datetime.now()

            log_port_action(self.port_name, "断开", success=True)
            return True

    def send_sms(self, phone: str, content: str) -> Tuple[bool, str, float]:
        """
        模拟发送短信
        返回: (成功标志, 消息, 耗时)
        """
        with self._lock:
            if not self.is_connected:
                return False, "端口未连接", 0.0

            if self._is_sending:
                return False, "端口正忙", 0.0

            if self.send_count >= self.send_limit:
                return False, "已达到发送上限", 0.0

            # 检查发送间隔
            if self.last_send_time:
                elapsed = (datetime.now() - self.last_send_time).total_seconds() * 1000
                if elapsed < self.send_interval:
                    return False, f"发送间隔未到（需等待{self.send_interval - elapsed:.0f}ms）", 0.0

            self._is_sending = True
            self.status = SimulatedPortStatus.SENDING.value

        try:
            # 模拟发送延迟
            send_time = random.uniform(*self.response_time_range)
            time.sleep(send_time)

            # 根据成功率决定结果
            success = random.random() < self.success_rate

            # 模拟各种失败原因
            if not success:
                failure_reasons = [
                    "发送超时",
                    "号码无效",
                    "余额不足",
                    "网络错误",
                    "短信内容违规",
                    "接收方已满",
                    "运营商拒绝",
                    "信号太弱"
                ]
                # 根据信号强度调整失败原因权重
                if self.signal_strength < 10:
                    failure_reason = "信号太弱"
                else:
                    failure_reason = random.choice(failure_reasons)
            else:
                failure_reason = None

            # 更新统计
            with self._lock:
                self.send_count += 1
                self.total_sent += 1
                self.last_send_time = datetime.now()
                self.last_activity = datetime.now()

                if success:
                    self.success_count += 1
                    message = f"发送成功 (耗时: {send_time:.2f}秒)"
                else:
                    self.failed_count += 1
                    message = f"发送失败: {failure_reason}"

                # 模拟信号波动
                self._update_signal_strength()

                self._is_sending = False
                self.status = SimulatedPortStatus.READY.value

            return success, message, send_time

        except Exception as e:
            with self._lock:
                self._is_sending = False
                self.status = SimulatedPortStatus.ERROR.value
                self.error_message = str(e)

            log_error(f"模拟发送短信异常: {e}")
            return False, f"发送异常: {str(e)}", 0.0

    def _update_signal_strength(self):
        """模拟信号强度波动"""
        # 小幅度随机波动
        change = random.randint(-2, 2)
        self.signal_strength = max(0, min(31, self.signal_strength + change))

        # 极小概率出现信号大幅下降
        if random.random() < 0.01:
            self.signal_strength = random.randint(0, 10)

        # 恢复信号
        if self.signal_strength < 10 and random.random() < 0.3:
            self.signal_strength = random.randint(15, 25)

    def reset_send_count(self):
        """重置发送计数"""
        with self._lock:
            self.send_count = 0
            log_port_action(self.port_name, "重置发送计数")

    def clear_statistics(self):
        """清除统计信息"""
        with self._lock:
            self.send_count = 0
            self.success_count = 0
            self.failed_count = 0
            self.total_sent = 0
            log_port_action(self.port_name, "清除统计")

    def get_status_info(self) -> Dict[str, Any]:
        """获取状态信息"""
        with self._lock:
            success_rate = 0.0
            if self.total_sent > 0:
                success_rate = (self.success_count / self.total_sent) * 100

            return {
                'port_name': self.port_name,
                'carrier': self.carrier,
                'status': self.status,
                'is_connected': self.is_connected,
                'is_selected': self.is_selected,
                'send_count': self.send_count,
                'send_limit': self.send_limit,
                'success_count': self.success_count,
                'failed_count': self.failed_count,
                'total_sent': self.total_sent,
                'success_rate': round(success_rate, 2),
                'signal_strength': self.signal_strength,
                'last_activity': self.last_activity.isoformat() if self.last_activity else None,
                'error_message': self.error_message
            }

    def can_send(self) -> bool:
        """检查是否可以发送"""
        if not self.is_connected:
            return False

        if self._is_sending:
            return False

        if self.send_count >= self.send_limit:
            return False

        if self.status == SimulatedPortStatus.ERROR.value:
            return False

        # 检查发送间隔
        if self.last_send_time:
            elapsed = (datetime.now() - self.last_send_time).total_seconds() * 1000
            if elapsed < self.send_interval:
                return False

        return True


class PortSimulator:
    """端口模拟器管理类"""

    def __init__(self, port_count: int = 20):
        """
        初始化端口模拟器
        Args:
            port_count: 模拟端口数量，默认20个
        """
        self.port_count = port_count
        self.ports: Dict[str, SimulatedPort] = {}
        self._lock = threading.Lock()

        # 配置参数
        self.default_send_interval = getattr(settings, 'DEFAULT_SEND_INTERVAL', 1000)
        self.default_success_rate = 0.7  # 默认70%成功率

        # 初始化端口
        self._initialize_ports()

        log_info(f"端口模拟器初始化完成，创建了{self.port_count}个虚拟端口")

    def _initialize_ports(self):
        """初始化虚拟端口"""
        for i in range(1, self.port_count + 1):
            port_name = f"COM{i}"
            port = SimulatedPort(
                port_name=port_name,
                port_index=i,
                send_interval=self.default_send_interval,
                success_rate=self.default_success_rate
            )
            self.ports[port_name] = port

    def get_all_ports(self) -> List[str]:
        """获取所有端口名称"""
        return list(self.ports.keys())

    def get_port(self, port_name: str) -> Optional[SimulatedPort]:
        """获取指定端口"""
        return self.ports.get(port_name)

    def scan_ports(self) -> List[str]:
        """扫描可用端口（模拟）"""
        # 模拟端口扫描过程
        time.sleep(random.uniform(0.5, 1.0))

        # 随机让一些端口"不可用"（模拟真实环境）
        available_ports = []
        for port_name, port in self.ports.items():
            # 90%的概率端口可用
            if random.random() < 0.9:
                available_ports.append(port_name)

        log_info(f"模拟端口扫描完成，发现{len(available_ports)}个可用端口")
        return available_ports

    def connect_port(self, port_name: str) -> bool:
        """连接指定端口"""
        port = self.get_port(port_name)
        if port:
            return port.connect()
        return False

    def disconnect_port(self, port_name: str) -> bool:
        """断开指定端口"""
        port = self.get_port(port_name)
        if port:
            return port.disconnect()
        return False

    def send_sms(self, port_name: str, phone: str, content: str) -> Tuple[bool, str, float]:
        """通过指定端口发送短信"""
        port = self.get_port(port_name)
        if port:
            return port.send_sms(phone, content)
        return False, "端口不存在", 0.0

    def get_port_statistics(self) -> Dict[str, Any]:
        """获取所有端口统计信息"""
        stats = {
            'total_ports': len(self.ports),
            'connected_ports': 0,
            'total_sent': 0,
            'total_success': 0,
            'total_failed': 0,
            'ports': []
        }

        for port in self.ports.values():
            if port.is_connected:
                stats['connected_ports'] += 1

            stats['total_sent'] += port.total_sent
            stats['total_success'] += port.success_count
            stats['total_failed'] += port.failed_count

            stats['ports'].append(port.get_status_info())

        # 计算总体成功率
        if stats['total_sent'] > 0:
            stats['overall_success_rate'] = round(
                (stats['total_success'] / stats['total_sent']) * 100, 2
            )
        else:
            stats['overall_success_rate'] = 0.0

        return stats

    def reset_all_statistics(self):
        """重置所有端口统计"""
        for port in self.ports.values():
            port.clear_statistics()
        log_info("已重置所有模拟端口统计信息")

    def set_success_rate(self, port_name: str, success_rate: float):
        """设置指定端口的成功率"""
        port = self.get_port(port_name)
        if port:
            port.success_rate = max(0.0, min(1.0, success_rate))
            log_info(f"端口{port_name}成功率设置为{port.success_rate:.2%}")

    def set_global_success_rate(self, success_rate: float):
        """设置全局成功率"""
        success_rate = max(0.0, min(1.0, success_rate))
        for port in self.ports.values():
            port.success_rate = success_rate
        log_info(f"全局成功率设置为{success_rate:.2%}")

    def simulate_port_failure(self, port_name: str, error_message: str = "模拟故障"):
        """模拟端口故障"""
        port = self.get_port(port_name)
        if port:
            with port._lock:
                port.status = SimulatedPortStatus.ERROR.value
                port.error_message = error_message
                port.is_connected = False
            log_port_action(port_name, "模拟故障", details=error_message)

    def recover_port(self, port_name: str):
        """恢复端口"""
        port = self.get_port(port_name)
        if port:
            with port._lock:
                port.status = SimulatedPortStatus.IDLE.value
                port.error_message = None
            log_port_action(port_name, "故障恢复")


# 全局端口模拟器实例
port_simulator = PortSimulator(port_count=20)

if __name__ == "__main__":
    # 测试代码
    print("=" * 50)
    print("端口模拟器测试")
    print("=" * 50)

    # 扫描端口
    available_ports = port_simulator.scan_ports()
    print(f"发现端口: {available_ports}")

    # 连接第一个端口
    if available_ports:
        test_port = available_ports[0]
        print(f"\n连接端口: {test_port}")
        if port_simulator.connect_port(test_port):
            print("连接成功")

            # 发送测试短信
            print("\n发送测试短信...")
            success, message, duration = port_simulator.send_sms(
                test_port,
                "13800138000",
                "这是一条测试短信"
            )
            print(f"结果: {message}")

            # 获取统计信息
            print("\n端口统计信息:")
            stats = port_simulator.get_port_statistics()
            print(f"总发送: {stats['total_sent']}")
            print(f"成功: {stats['total_success']}")
            print(f"失败: {stats['total_failed']}")
            print(f"成功率: {stats['overall_success_rate']}%")