# 创建文件：core/mac_port_scanner.py
import glob
import serial
from typing import List, Dict
import platform
import subprocess


class MacPortScanner:
    """Mac平台端口扫描器"""

    def __init__(self):
        self.system = platform.system()

    def scan_available_ports(self) -> List[Dict[str, str]]:
        """扫描可用串口"""
        ports = []

        if self.system == 'Darwin':  # macOS
            # Mac串口通常在 /dev/tty.* 或 /dev/cu.*
            tty_ports = glob.glob('/dev/tty.*')
            cu_ports = glob.glob('/dev/cu.*')

            # 合并并过滤
            all_ports = tty_ports + cu_ports

            # 过滤出USB设备和蓝牙设备
            usb_ports = [p for p in all_ports if 'usb' in p.lower() or 'serial' in p.lower()]
            bluetooth_ports = [p for p in all_ports if 'bluetooth' in p.lower()]

            # 模拟设备端口（开发阶段）
            mock_ports = [f'/dev/ttys{i:03d}' for i in range(1, 9)]

            for port_path in usb_ports + bluetooth_ports + mock_ports:
                port_info = self._get_port_info(port_path)
                if port_info:
                    ports.append(port_info)

        return ports

    def _get_port_info(self, port_path: str) -> Dict[str, str]:
        """获取端口详细信息"""
        try:
            # 尝试打开端口获取信息
            with serial.Serial(port_path, 9600, timeout=1) as ser:
                port_info = {
                    'port': port_path,
                    'description': self._get_port_description(port_path),
                    'manufacturer': 'Unknown',
                    'product': 'Unknown',
                    'hwid': port_path,
                    'status': 'available'
                }

                # 如果是模拟端口，添加模拟信息
                if 'ttys' in port_path:
                    port_info.update({
                        'description': f'Mock Modem Port {port_path.split("/")[-1]}',
                        'manufacturer': 'Mock Devices Inc.',
                        'product': 'Virtual SMS Modem',
                        'status': 'mock'
                    })

                return port_info

        except (serial.SerialException, PermissionError):
            # 端口被占用或无权限
            return {
                'port': port_path,
                'description': 'Port busy or no permission',
                'status': 'unavailable'
            }

    def _get_port_description(self, port_path: str) -> str:
        """获取端口描述"""
        try:
            # 使用系统命令获取设备信息
            result = subprocess.run([
                'system_profiler', 'SPUSBDataType', '-xml'
            ], capture_output=True, text=True)

            # 简化处理，实际可以解析XML获取详细信息
            if 'usb' in port_path.lower():
                return 'USB Serial Device'
            elif 'bluetooth' in port_path.lower():
                return 'Bluetooth Serial Device'
            else:
                return 'Serial Device'

        except:
            return 'Unknown Serial Device'

    def test_port_communication(self, port_path: str) -> Dict[str, any]:
        """测试端口通信"""
        try:
            with serial.Serial(port_path, 9600, timeout=2) as ser:
                # 发送AT指令测试
                ser.write(b'AT\r\n')
                response = ser.readline().decode('utf-8', errors='ignore').strip()

                if 'OK' in response:
                    return {
                        'success': True,
                        'response': response,
                        'type': 'modem'
                    }
                else:
                    return {
                        'success': False,
                        'error': 'No AT response',
                        'response': response
                    }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }