"""
常用工具函数模块
"""
import serial
import time
import re
import json
import os
from datetime import datetime


class SmsDevice:
    """短信设备类 - 用于实际的硬件通信"""

    def __init__(self, port_name):
        self.port_name = port_name
        self.serial_connection = None
        self.is_connected = False
        self.device_info = {}

    def connect(self):
        """连接设备"""
        try:
            self.serial_connection = serial.Serial(
                port=self.port_name,
                baudrate=115200,
                timeout=1
            )
            self.is_connected = True

            # 获取设备信息
            self._initialize_device()
            return True
        except Exception as e:
            print(f"连接端口 {self.port_name} 失败: {e}")
            return False

    def disconnect(self):
        """断开连接"""
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
        self.is_connected = False

    def _initialize_device(self):
        """初始化设备"""
        if not self.is_connected:
            return

        # 基本AT命令测试
        response = self.send_at_command("AT")
        if response and "OK" in response:
            self.device_info['status'] = 'ready'
        else:
            self.device_info['status'] = 'error'

        # 获取设备型号
        model_response = self.send_at_command("ATI")
        if model_response:
            self.device_info['model'] = model_response.replace('OK', '').strip()

        # 设置文本模式
        self.send_at_command("AT+CMGF=1")

    def send_at_command(self, command, timeout=1):
        """发送AT命令"""
        if not self.is_connected or not self.serial_connection:
            return None

        try:
            # 清空输入缓冲区
            self.serial_connection.reset_input_buffer()

            # 发送命令
            self.serial_connection.write((command + '\r\n').encode())
            time.sleep(0.1)

            # 读取响应
            response = ""
            start_time = time.time()
            while time.time() - start_time < timeout:
                if self.serial_connection.in_waiting > 0:
                    data = self.serial_connection.read(self.serial_connection.in_waiting)
                    response += data.decode('utf-8', errors='ignore')
                    if 'OK' in response or 'ERROR' in response:
                        break
                time.sleep(0.01)

            return response.strip()
        except Exception as e:
            print(f"发送AT命令失败: {e}")
            return None

    def send_sms(self, phone_number, message):
        """发送短信"""
        if not self.is_connected:
            return False

        try:
            # 设置短信模式为文本模式
            response = self.send_at_command("AT+CMGF=1")
            if not response or "OK" not in response:
                return False

            # 设置接收方号码
            cmd = f'AT+CMGS="{phone_number}"'
            response = self.send_at_command(cmd, timeout=2)

            if not response or ">" not in response:
                return False

            # 发送短信内容
            message_cmd = message + chr(26)  # Ctrl+Z
            response = self.send_at_command(message_cmd, timeout=10)

            return response and ("OK" in response or "+CMGS:" in response)
        except Exception as e:
            print(f"发送短信失败: {e}")
            return False

    def get_signal_strength(self):
        """获取信号强度"""
        response = self.send_at_command("AT+CSQ")
        if response and "+CSQ:" in response:
            try:
                # 解析信号强度
                csq_line = [line for line in response.split('\n') if '+CSQ:' in line][0]
                values = csq_line.split(':')[1].strip().split(',')
                rssi = int(values[0])
                return rssi
            except:
                pass
        return -1

    def get_operator_info(self):
        """获取运营商信息"""
        response = self.send_at_command("AT+COPS?")
        if response and "+COPS:" in response:
            try:
                # 解析运营商信息
                cops_line = [line for line in response.split('\n') if '+COPS:' in line][0]
                # 提取运营商名称
                match = re.search(r'"([^"]+)"', cops_line)
                if match:
                    return match.group(1)
            except:
                pass
        return "未知运营商"

    def get_sim_status(self):
        """获取SIM卡状态"""
        response = self.send_at_command("AT+CPIN?")
        if response and "+CPIN:" in response:
            if "READY" in response:
                return "ready"
            elif "SIM PIN" in response:
                return "pin_required"
            elif "SIM PUK" in response:
                return "puk_required"
        return "unknown"


def validate_phone_number(phone_number, format_type='domestic'):
    """验证手机号格式"""
    # 移除空格和特殊字符
    phone_number = phone_number.strip().replace(' ', '').replace('-', '').replace('(', '').replace(')', '')

    if format_type == 'domestic':
        # 中国大陆手机号验证
        pattern = r'^1[3-9]\d{9}$'
        return bool(re.match(pattern, phone_number))
    elif format_type == 'international':
        # 国际号码格式验证
        pattern = r'^\+\d{10,15}$'
        return bool(re.match(pattern, phone_number))

    return False


def format_phone_number(phone_number, format_type='domestic'):
    """格式化手机号"""
    phone_number = phone_number.strip().replace(' ', '').replace('-', '')

    if format_type == 'domestic':
        # 国内格式
        if phone_number.startswith('+86'):
            phone_number = phone_number[3:]
        elif phone_number.startswith('86') and len(phone_number) == 13:
            phone_number = phone_number[2:]
    elif format_type == 'international':
        # 国际格式
        if not phone_number.startswith('+'):
            if phone_number.startswith('86'):
                phone_number = '+' + phone_number
            elif phone_number.startswith('1') and len(phone_number) == 11:
                phone_number = '+86' + phone_number

    return phone_number


def parse_phone_numbers(text):
    """解析手机号列表"""
    if not text:
        return []

    # 按行分割
    lines = text.strip().split('\n')
    phone_numbers = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 检查是否包含多个号码（逗号或分号分隔）
        if ',' in line or ';' in line:
            numbers = re.split(r'[,;]', line)
            for num in numbers:
                num = num.strip()
                if num and validate_phone_number(num):
                    phone_numbers.append(num)
        else:
            if validate_phone_number(line):
                phone_numbers.append(line)

    return phone_numbers


def format_time_duration(seconds):
    """格式化时间长度"""
    if seconds < 60:
        return f"{int(seconds)}秒"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes}分钟"
    else:
        hours = int(seconds / 3600)
        minutes = int((seconds % 3600) / 60)
        return f"{hours}小时{minutes}分钟"


def calculate_send_time(total_numbers, send_interval, active_ports=1):
    """计算预估发送时间"""
    if active_ports == 0:
        return float('inf')

    # 每个端口平均发送的数量
    numbers_per_port = total_numbers / active_ports

    # 总时间（秒）
    total_seconds = numbers_per_port * (send_interval / 1000.0)

    return total_seconds


def export_data_to_csv(data, filename, headers=None):
    """导出数据到CSV文件"""
    try:
        import csv

        with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
            if not data:
                return False

            if headers is None:
                headers = data[0].keys() if isinstance(data[0], dict) else range(len(data[0]))

            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()

            for row in data:
                if isinstance(row, dict):
                    writer.writerow(row)
                else:
                    writer.writerow(dict(zip(headers, row)))

        return True
    except Exception as e:
        print(f"导出CSV失败: {e}")
        return False


def import_data_from_csv(filename):
    """从CSV文件导入数据"""
    try:
        import csv

        data = []
        with open(filename, 'r', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                data.append(dict(row))

        return data
    except Exception as e:
        print(f"导入CSV失败: {e}")
        return []


def create_backup(data, backup_dir='backups'):
    """创建数据备份"""
    try:
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f'backup_{timestamp}.json')

        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

        return backup_file
    except Exception as e:
        print(f"创建备份失败: {e}")
        return None


def restore_from_backup(backup_file):
    """从备份恢复数据"""
    try:
        with open(backup_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"恢复备份失败: {e}")
        return None


def get_system_info():
    """获取系统信息"""
    import platform
    import psutil

    try:
        info = {
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'cpu_count': psutil.cpu_count(),
            'memory_total': psutil.virtual_memory().total,
            'memory_available': psutil.virtual_memory().available,
            'disk_usage': psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:\\').percent
        }
        return info
    except Exception as e:
        print(f"获取系统信息失败: {e}")
        return {}


def check_port_availability(port_name):
    """检查端口是否可用"""
    try:
        with serial.Serial(port_name, baudrate=115200, timeout=0.1) as ser:
            return True
    except:
        return False


def get_available_ports():
    """获取可用串口列表"""
    try:
        ports = serial.tools.list_ports.comports()
        available_ports = []

        for port in ports:
            port_info = {
                'device': port.device,
                'description': port.description,
                'hwid': port.hwid,
                'available': check_port_availability(port.device)
            }
            available_ports.append(port_info)

        return available_ports
    except Exception as e:
        print(f"获取端口列表失败: {e}")
        return []


class ConfigManager:
    """配置文件管理器"""

    def __init__(self, config_file='config.json'):
        self.config_file = config_file
        self.config = {}

    def load(self):
        """加载配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            return True
        except Exception as e:
            print(f"加载配置失败: {e}")
            return False

    def save(self):
        """保存配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2, default=str)
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False

    def get(self, key, default=None):
        """获取配置项"""
        return self.config.get(key, default)

    def set(self, key, value):
        """设置配置项"""
        self.config[key] = value

    def update(self, data):
        """批量更新配置"""
        self.config.update(data)


def retry(max_attempts=3, delay=1, exceptions=(Exception,)):
    """重试装饰器"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        time.sleep(delay)
                    continue

            raise last_exception

        return wrapper

    return decorator


def sanitize_filename(filename):
    """清理文件名，移除非法字符"""
    # 移除或替换非法字符
    illegal_chars = '<>:"/\\|?*'
    for char in illegal_chars:
        filename = filename.replace(char, '_')

    # 限制长度
    if len(filename) > 200:
        filename = filename[:200]

    return filename


def ensure_directory(directory):
    """确保目录存在"""
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
        return True
    except Exception as e:
        print(f"创建目录失败: {e}")
        return False