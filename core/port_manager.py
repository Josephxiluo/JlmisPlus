"""
猫池端口扫描、识别、控制模块
"""
import serial
import serial.tools.list_ports
from core.utils import SmsDevice


class PortManager:
    """端口管理器"""

    def __init__(self):
        self.ports = {}  # 串口信息
        self.running_ports = set()  # 正在运行的端口
        self.devices = {}  # 设备连接池

    def scan_ports(self):
        """扫描可用串口"""
        ports_list = serial.tools.list_ports.comports()
        carriers = ['中国联通', '中国电信', '中国移动']

        for i, port in enumerate(ports_list):
            port_name = port.device
            if port_name not in self.ports:
                self.ports[port_name] = {
                    'name': port_name,
                    'carrier': carriers[i % len(carriers)],
                    'limit': 60,
                    'success': 0,
                    'status': 'stopped',
                    'selected': False,
                    'description': port.description
                }

        # 如果没有找到串口，添加一些示例串口
        if not self.ports:
            for i in range(1, 17):
                port_name = f"COM{100 + i}"
                self.ports[port_name] = {
                    'name': port_name,
                    'carrier': carriers[i % len(carriers)],
                    'limit': 60,
                    'success': i % 4,
                    'status': 'stopped',
                    'selected': False,
                    'description': 'Mock Port'
                }

        return self.ports

    def get_port_info(self, port_name):
        """获取端口信息"""
        return self.ports.get(port_name)

    def update_port_status(self, port_name, status):
        """更新端口状态"""
        if port_name in self.ports:
            self.ports[port_name]['status'] = status

            if status == 'running':
                self.running_ports.add(port_name)
            else:
                self.running_ports.discard(port_name)

    def toggle_port_status(self, port_name):
        """切换端口运行状态"""
        if port_name in self.ports:
            current_status = self.ports[port_name]['status']
            new_status = 'stopped' if current_status == 'running' else 'running'
            self.update_port_status(port_name, new_status)
            return new_status
        return None

    def set_port_selection(self, port_name, selected):
        """设置端口选择状态"""
        if port_name in self.ports:
            self.ports[port_name]['selected'] = selected

    def select_all_ports(self):
        """全选端口"""
        for port_name in self.ports:
            self.ports[port_name]['selected'] = True

    def deselect_all_ports(self):
        """取消全选端口"""
        for port_name in self.ports:
            self.ports[port_name]['selected'] = False

    def reverse_select_ports(self):
        """反选端口"""
        for port_name in self.ports:
            self.ports[port_name]['selected'] = not self.ports[port_name]['selected']

    def get_selected_ports(self):
        """获取已选择的端口"""
        return [name for name, info in self.ports.items() if info['selected']]

    def get_running_ports(self):
        """获取正在运行的端口"""
        return list(self.running_ports)

    def start_selected_ports(self):
        """启动选中的端口"""
        selected_ports = self.get_selected_ports()
        for port_name in selected_ports:
            self.update_port_status(port_name, 'running')
        return len(selected_ports)

    def stop_selected_ports(self):
        """停止选中的端口"""
        selected_ports = self.get_selected_ports()
        for port_name in selected_ports:
            self.update_port_status(port_name, 'stopped')
        return len(selected_ports)

    def clear_all_records(self):
        """清除所有记录"""
        for port_name in self.ports:
            self.ports[port_name]['success'] = 0

    def clear_current_records(self):
        """清除当前记录"""
        for port_name in self.ports:
            self.ports[port_name]['success'] = max(0, self.ports[port_name]['success'] - 1)

    def add_device(self, port_name):
        """添加设备连接"""
        if port_name not in self.devices:
            device = SmsDevice(port_name)
            if device.connect():
                self.devices[port_name] = device
                return True
        return False

    def remove_device(self, port_name):
        """移除设备连接"""
        if port_name in self.devices:
            self.devices[port_name].disconnect()
            del self.devices[port_name]

    def get_available_devices(self, port_names=None):
        """获取可用的设备"""
        if port_names is None:
            port_names = self.get_running_ports()

        return [self.devices[port] for port in port_names if port in self.devices]

    def update_port_success(self, port_name, increment=1):
        """更新端口成功计数"""
        if port_name in self.ports:
            self.ports[port_name]['success'] += increment