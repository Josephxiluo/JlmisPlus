# 创建文件：core/platform_adapter.py
import platform
from abc import ABC, abstractmethod
from typing import List, Dict


class PlatformAdapter(ABC):
    """平台适配器基类"""

    @abstractmethod
    def get_available_ports(self) -> List[Dict]:
        pass

    @abstractmethod
    def create_serial_connection(self, port: str, baudrate: int):
        pass

    @abstractmethod
    def get_system_info(self) -> Dict:
        pass


class MacAdapter(PlatformAdapter):
    """Mac平台适配器"""

    def get_available_ports(self) -> List[Dict]:
        from core.mac_port_scanner import MacPortScanner
        scanner = MacPortScanner()
        return scanner.scan_available_ports()

    def create_serial_connection(self, port: str, baudrate: int):
        import serial
        return serial.Serial(port, baudrate, timeout=1)

    def get_system_info(self) -> Dict:
        return {
            'platform': 'macOS',
            'version': platform.mac_ver()[0],
            'architecture': platform.machine(),
            'python_version': platform.python_version()
        }


class WindowsAdapter(PlatformAdapter):
    """Windows平台适配器"""

    def get_available_ports(self) -> List[Dict]:
        import serial.tools.list_ports
        ports = []
        for port in serial.tools.list_ports.comports():
            ports.append({
                'port': port.device,
                'description': port.description,
                'manufacturer': getattr(port, 'manufacturer', 'Unknown'),
                'product': getattr(port, 'product', 'Unknown'),
                'hwid': port.hwid,
                'status': 'available'
            })
        return ports

    def create_serial_connection(self, port: str, baudrate: int):
        import serial
        return serial.Serial(port, baudrate, timeout=1)

    def get_system_info(self) -> Dict:
        return {
            'platform': 'Windows',
            'version': platform.version(),
            'architecture': platform.machine(),
            'python_version': platform.python_version()
        }


# 平台适配器工厂
def get_platform_adapter() -> PlatformAdapter:
    system = platform.system()
    if system == 'Darwin':
        return MacAdapter()
    elif system == 'Windows':
        return WindowsAdapter()
    else:
        raise NotImplementedError(f"Unsupported platform: {system}")