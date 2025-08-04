"""
猫池短信系统工具函数 - tkinter版
Utility functions for SMS Pool System - tkinter version
"""

import os
import re
import sys
import json
import uuid
import hashlib
import platform
import socket
import psutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Tuple

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 时间工具函数
def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """格式化日期时间"""
    if dt is None:
        return ""
    return dt.strftime(format_str)

def format_duration(seconds: float) -> str:
    """格式化时长"""
    if seconds < 0:
        return "0秒"

    if seconds < 60:
        return f"{seconds:.1f}秒"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}分{secs}秒"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}小时{minutes}分钟"

def get_current_timestamp() -> str:
    """获取当前时间戳字符串"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def parse_datetime(date_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> Optional[datetime]:
    """解析日期时间字符串"""
    try:
        return datetime.strptime(date_str, format_str)
    except (ValueError, TypeError):
        return None

# 字符串工具函数
def mask_phone_number(phone: str, mask_char: str = "*") -> str:
    """手机号码脱敏显示"""
    if not phone or len(phone) < 4:
        return phone

    if len(phone) == 11 and phone.startswith('1'):
        # 国内手机号：138****1234
        return f"{phone[:3]}{mask_char * 4}{phone[-4:]}"
    elif phone.startswith('+'):
        # 国际号码：+86138****1234
        if len(phone) > 8:
            return f"{phone[:5]}{mask_char * 4}{phone[-4:]}"

    # 其他格式，中间部分脱敏
    if len(phone) > 6:
        start_len = len(phone) // 3
        end_len = len(phone) // 3
        mask_len = len(phone) - start_len - end_len
        return f"{phone[:start_len]}{mask_char * mask_len}{phone[-end_len:]}"

    return phone

def validate_phone_number(phone: str, international: bool = False) -> bool:
    """验证手机号码格式"""
    if not phone:
        return False

    # 清理号码
    clean_phone = re.sub(r'[^\d+]', '', phone)

    if international:
        # 国际号码：+国家代码+号码，总长度8-15位
        pattern = r'^\+\d{8,15}$'
        return bool(re.match(pattern, clean_phone))
    else:
        # 国内手机号：1开头，11位数字
        pattern = r'^1[3-9]\d{9}$'
        return bool(re.match(pattern, clean_phone))

def clean_phone_number(phone: str) -> str:
    """清理手机号码，移除非数字字符（保留+号）"""
    if not phone:
        return ""

    # 保留数字和+号
    cleaned = re.sub(r'[^\d+]', '', phone)

    # 如果是国内号码且前面有+86，去掉+86
    if cleaned.startswith('+86') and len(cleaned) == 14:
        cleaned = cleaned[3:]

    return cleaned

def extract_numbers_from_text(text: str) -> List[str]:
    """从文本中提取手机号码"""
    if not text:
        return []

    # 匹配模式
    patterns = [
        r'\+\d{8,15}',  # 国际号码
        r'1[3-9]\d{9}',  # 国内手机号
        r'\d{3}[-\s]?\d{4}[-\s]?\d{4}'  # 带分隔符的号码
    ]

    numbers = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        numbers.extend(matches)

    # 清理和去重
    cleaned_numbers = []
    seen = set()

    for number in numbers:
        clean_num = clean_phone_number(number)
        if clean_num and clean_num not in seen:
            if validate_phone_number(clean_num) or validate_phone_number(clean_num, international=True):
                cleaned_numbers.append(clean_num)
                seen.add(clean_num)

    return cleaned_numbers

# 文件工具函数
def ensure_directory(path: Union[str, Path]) -> Path:
    """确保目录存在"""
    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj

def get_file_size(file_path: Union[str, Path]) -> int:
    """获取文件大小（字节）"""
    try:
        return Path(file_path).stat().st_size
    except (OSError, FileNotFoundError):
        return 0

def get_file_extension(file_path: Union[str, Path]) -> str:
    """获取文件扩展名"""
    return Path(file_path).suffix.lower()

def is_file_exists(file_path: Union[str, Path]) -> bool:
    """检查文件是否存在"""
    return Path(file_path).is_file()

def get_safe_filename(filename: str) -> str:
    """获取安全的文件名"""
    # 移除或替换不安全字符
    safe_chars = re.sub(r'[<>:"/\\|?*]', '_', filename)

    # 限制长度
    if len(safe_chars) > 200:
        name, ext = os.path.splitext(safe_chars)
        safe_chars = name[:200-len(ext)] + ext

    return safe_chars

def copy_file_safe(src: Union[str, Path], dst: Union[str, Path]) -> bool:
    """安全复制文件"""
    try:
        import shutil

        src_path = Path(src)
        dst_path = Path(dst)

        if not src_path.exists():
            return False

        # 确保目标目录存在
        ensure_directory(dst_path.parent)

        shutil.copy2(src_path, dst_path)
        return True
    except Exception:
        return False

# 数据工具函数
def calculate_percentage(current: Union[int, float], total: Union[int, float], decimal_places: int = 2) -> float:
    """计算百分比"""
    if total == 0:
        return 0.0
    return round(current / total * 100, decimal_places)

def format_file_size(size_bytes: int) -> str:
    """格式化文件大小"""
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)

    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1

    return f"{size:.1f} {size_names[i]}"

def generate_unique_id() -> str:
    """生成唯一ID"""
    return str(uuid.uuid4())

def generate_short_id(length: int = 8) -> str:
    """生成短ID"""
    return str(uuid.uuid4()).replace('-', '')[:length]

def clamp(value: Union[int, float], min_val: Union[int, float], max_val: Union[int, float]) -> Union[int, float]:
    """限制数值范围"""
    return max(min_val, min(value, max_val))

def safe_divide(numerator: Union[int, float], denominator: Union[int, float], default: Union[int, float] = 0) -> Union[int, float]:
    """安全除法"""
    if denominator == 0:
        return default
    return numerator / denominator

# 验证工具函数
def is_valid_port_name(port_name: str) -> bool:
    """验证端口名称"""
    if not port_name:
        return False

    # COM端口格式：COM1, COM2, etc.
    pattern = r'^COM\d+$'
    return bool(re.match(pattern, port_name.upper()))

def is_valid_baud_rate(baud_rate: int) -> bool:
    """验证波特率"""
    valid_rates = [9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600]
    return baud_rate in valid_rates

def is_valid_ip_address(ip: str) -> bool:
    """验证IP地址"""
    try:
        socket.inet_aton(ip)
        return True
    except socket.error:
        return False

def is_valid_email(email: str) -> bool:
    """验证邮箱地址"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

# 转换工具函数
def bytes_to_str(data: bytes, encoding: str = 'utf-8', errors: str = 'ignore') -> str:
    """字节转字符串"""
    try:
        return data.decode(encoding, errors)
    except (UnicodeDecodeError, AttributeError):
        return str(data)

def str_to_bytes(text: str, encoding: str = 'utf-8') -> bytes:
    """字符串转字节"""
    try:
        return text.encode(encoding)
    except (UnicodeEncodeError, AttributeError):
        return bytes(text, encoding, errors='ignore')

def dict_to_query_string(params: Dict[str, Any]) -> str:
    """字典转查询字符串"""
    try:
        from urllib.parse import urlencode
        return urlencode(params)
    except ImportError:
        # Python 2 fallback
        items = []
        for key, value in params.items():
            items.append(f"{key}={value}")
        return "&".join(items)

def parse_query_string(query_string: str) -> Dict[str, str]:
    """解析查询字符串"""
    try:
        from urllib.parse import parse_qs
        parsed = parse_qs(query_string)
        # 提取单个值
        return {k: v[0] if v else '' for k, v in parsed.items()}
    except ImportError:
        # 简单解析
        result = {}
        if query_string:
            pairs = query_string.split('&')
            for pair in pairs:
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    result[key] = value
        return result

# 网络工具函数
def get_local_ip() -> str:
    """获取本地IP地址"""
    try:
        # 连接到外部地址来获取本地IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"

def get_mac_address() -> str:
    """获取MAC地址"""
    try:
        mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
        return ":".join([mac[e:e+2] for e in range(0, 11, 2)]).upper()
    except Exception:
        return "00:00:00:00:00:00"

def ping_host(host: str, timeout: int = 5) -> bool:
    """Ping主机"""
    try:
        import subprocess

        if platform.system().lower() == "windows":
            cmd = ["ping", "-n", "1", "-w", str(timeout * 1000), host]
        else:
            cmd = ["ping", "-c", "1", "-W", str(timeout), host]

        result = subprocess.run(cmd, capture_output=True, timeout=timeout + 2)
        return result.returncode == 0
    except Exception:
        return False

def get_network_interfaces() -> List[Dict[str, str]]:
    """获取网络接口信息"""
    try:
        interfaces = []
        addrs = psutil.net_if_addrs()

        for interface_name, interface_addresses in addrs.items():
            for address in interface_addresses:
                if address.family == socket.AF_INET:  # IPv4
                    interfaces.append({
                        'name': interface_name,
                        'ip': address.address,
                        'netmask': address.netmask,
                        'broadcast': address.broadcast or ''
                    })

        return interfaces
    except Exception:
        return []

# 系统工具函数
def get_system_info() -> Dict[str, Any]:
    """获取系统信息"""
    try:
        return {
            'platform': platform.system(),
            'platform_version': platform.version(),
            'architecture': platform.architecture()[0],
            'processor': platform.processor(),
            'python_version': platform.python_version(),
            'hostname': socket.gethostname(),
            'username': os.getenv('USERNAME') or os.getenv('USER') or 'unknown'
        }
    except Exception:
        return {}

def get_memory_usage() -> Dict[str, Union[int, float]]:
    """获取内存使用情况"""
    try:
        memory = psutil.virtual_memory()
        return {
            'total': memory.total,
            'available': memory.available,
            'used': memory.used,
            'percentage': memory.percent,
            'total_mb': round(memory.total / 1024 / 1024, 2),
            'available_mb': round(memory.available / 1024 / 1024, 2),
            'used_mb': round(memory.used / 1024 / 1024, 2)
        }
    except Exception:
        return {}

def get_disk_usage(path: str = '/') -> Dict[str, Union[int, float]]:
    """获取磁盘使用情况"""
    try:
        if platform.system().lower() == 'windows':
            path = 'C:\\'

        disk = psutil.disk_usage(path)
        return {
            'total': disk.total,
            'used': disk.used,
            'free': disk.free,
            'percentage': round(disk.used / disk.total * 100, 2),
            'total_gb': round(disk.total / 1024 / 1024 / 1024, 2),
            'used_gb': round(disk.used / 1024 / 1024 / 1024, 2),
            'free_gb': round(disk.free / 1024 / 1024 / 1024, 2)
        }
    except Exception:
        return {}

def get_cpu_usage() -> float:
    """获取CPU使用率"""
    try:
        return psutil.cpu_percent(interval=1)
    except Exception:
        return 0.0

def is_process_running(process_name: str) -> bool:
    """检查进程是否运行"""
    try:
        for process in psutil.process_iter(['name']):
            if process.info['name'] and process_name.lower() in process.info['name'].lower():
                return True
        return False
    except Exception:
        return False

# 配置工具函数
def load_json_config(file_path: Union[str, Path], default: Any = None) -> Any:
    """加载JSON配置文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, Exception):
        return default or {}

def save_json_config(data: Any, file_path: Union[str, Path]) -> bool:
    """保存JSON配置文件"""
    try:
        # 确保目录存在
        ensure_directory(Path(file_path).parent)

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False

def merge_configs(base_config: Dict, user_config: Dict) -> Dict:
    """合并配置"""
    result = base_config.copy()

    for key, value in user_config.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_configs(result[key], value)
        else:
            result[key] = value

    return result

def load_ini_config(file_path: Union[str, Path]) -> Dict[str, Dict[str, str]]:
    """加载INI配置文件"""
    try:
        import configparser

        config = configparser.ConfigParser()
        config.read(file_path, encoding='utf-8')

        result = {}
        for section_name in config.sections():
            result[section_name] = dict(config[section_name])

        return result
    except Exception:
        return {}

# 安全工具函数
def generate_hash(text: str, algorithm: str = 'sha256') -> str:
    """生成哈希值"""
    try:
        hash_obj = hashlib.new(algorithm)
        hash_obj.update(text.encode('utf-8'))
        return hash_obj.hexdigest()
    except Exception:
        return ""

def verify_hash(text: str, hash_value: str, algorithm: str = 'sha256') -> bool:
    """验证哈希值"""
    try:
        return generate_hash(text, algorithm) == hash_value
    except Exception:
        return False

def generate_random_string(length: int = 16, charset: str = None) -> str:
    """生成随机字符串"""
    import random
    import string

    if charset is None:
        charset = string.ascii_letters + string.digits

    return ''.join(random.choice(charset) for _ in range(length))

def encode_base64(data: Union[str, bytes]) -> str:
    """Base64编码"""
    try:
        import base64

        if isinstance(data, str):
            data = data.encode('utf-8')

        return base64.b64encode(data).decode('utf-8')
    except Exception:
        return ""

def decode_base64(encoded_data: str) -> bytes:
    """Base64解码"""
    try:
        import base64
        return base64.b64decode(encoded_data)
    except Exception:
        return b""

# 调试工具函数
def print_debug(message: str, *args, **kwargs):
    """调试输出"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[DEBUG {timestamp}] {message}", *args, **kwargs)

def log_function_call(func_name: str, args: tuple = (), kwargs: dict = None):
    """记录函数调用"""
    kwargs = kwargs or {}
    args_str = ", ".join([str(arg) for arg in args])
    if kwargs:
        kwargs_str = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
        if args_str:
            args_str += f", {kwargs_str}"
        else:
            args_str = kwargs_str

    print_debug(f"调用函数: {func_name}({args_str})")

def measure_execution_time(func):
    """测量函数执行时间的装饰器"""
    import functools
    import time

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        print_debug(f"函数 {func.__name__} 执行时间: {execution_time:.4f}秒")
        return result

    return wrapper

# 缓存工具函数
def simple_cache(maxsize: int = 128):
    """简单缓存装饰器"""
    import functools

    def decorator(func):
        cache = {}
        cache_order = []

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 创建缓存键
            key = str(args) + str(sorted(kwargs.items()))

            if key in cache:
                return cache[key]

            # 计算结果
            result = func(*args, **kwargs)

            # 添加到缓存
            if len(cache) >= maxsize:
                # 移除最旧的项
                oldest_key = cache_order.pop(0)
                del cache[oldest_key]

            cache[key] = result
            cache_order.append(key)

            return result

        wrapper.cache_clear = lambda: (cache.clear(), cache_order.clear())
        wrapper.cache_info = lambda: {'hits': len(cache), 'maxsize': maxsize}

        return wrapper

    return decorator

# 重试工具函数
def retry_on_exception(max_retries: int = 3, delay: float = 1.0, exceptions: Tuple = (Exception,)):
    """重试装饰器"""
    import functools
    import time

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        print_debug(f"函数 {func.__name__} 第{attempt + 1}次重试，错误: {e}")
                        time.sleep(delay * (attempt + 1))
                    else:
                        print_debug(f"函数 {func.__name__} 重试{max_retries}次后仍然失败")
                        raise last_exception

            raise last_exception

        return wrapper

    return decorator