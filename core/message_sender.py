"""
猫池短信系统短信发送器 - tkinter版
Message sender for SMS Pool System - tkinter version
"""

import sys
import time
import threading
import queue
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable, Tuple
from pathlib import Path
from enum import Enum

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from config.settings import settings
    from config.logging_config import get_logger, log_message_send, log_error, log_info
    from .utils import format_duration, clean_phone_number, validate_phone_number
except ImportError:
    # 简化处理
    class MockSettings:
        DEFAULT_SEND_INTERVAL = 1000
        DEFAULT_TIMEOUT = 30
        PORT_BAUD_RATE = 115200


    settings = MockSettings()

    import logging


    def get_logger(name='core.message_sender'):
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger


    def log_message_send(task_id, recipient, port, status, details=None):
        logger = get_logger()
        message = f"[消息发送] 任务ID={task_id} 接收号码={recipient} 端口={port} 状态={status}"
        if details:
            message += f" - {details}"
        if status == 'success':
            logger.info(message)
        elif status in ['failed', 'timeout']:
            logger.warning(message)
        else:
            logger.debug(message)


    def log_error(message, error=None):
        logger = get_logger()
        logger.error(f"{message}: {error}" if error else message)


    def log_info(message):
        logger = get_logger()
        logger.info(message)


    def format_duration(seconds):
        if seconds < 60:
            return f"{seconds:.1f}秒"
        return f"{int(seconds // 60)}分{int(seconds % 60)}秒"


    def clean_phone_number(phone):
        import re
        return re.sub(r'[^\d+]', '', phone) if phone else ""


    def validate_phone_number(phone, international=False):
        import re
        if not phone:
            return False
        if international:
            return bool(re.match(r'^\+\d{8,15}$', phone))
        else:
            return bool(re.match(r'^1[3-9]\d{9}$', phone))

logger = get_logger('core.message_sender')


class SendResult(Enum):
    """发送结果枚举"""
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    ERROR = "error"
    CANCELLED = "cancelled"


class MessageType(Enum):
    """消息类型枚举"""
    SMS = "sms"
    MMS = "mms"


class SendRequest:
    """发送请求类"""

    def __init__(self, message_id: int, phone: str, content: str,
                 message_type: MessageType = MessageType.SMS,
                 priority: int = 5, task_id: int = 0):
        self.message_id = message_id
        self.phone = clean_phone_number(phone)
        self.content = content
        self.message_type = message_type
        self.priority = priority
        self.task_id = task_id
        self.created_time = datetime.now()
        self.attempts = 0
        self.max_attempts = 3
        self.last_error: Optional[str] = None

    def __lt__(self, other):
        """优先级比较（数字越小优先级越高）"""
        return self.priority < other.priority

    def can_retry(self) -> bool:
        """是否可以重试"""
        return self.attempts < self.max_attempts

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'message_id': self.message_id,
            'phone': self.phone,
            'content': self.content[:50] + "..." if len(self.content) > 50 else self.content,
            'message_type': self.message_type.value,
            'priority': self.priority,
            'task_id': self.task_id,
            'attempts': self.attempts,
            'max_attempts': self.max_attempts,
            'last_error': self.last_error
        }


class PortConnection:
    """端口连接类"""

    def __init__(self, port_name: str, baud_rate: int = 115200):
        self.port_name = port_name
        self.baud_rate = baud_rate
        self.serial_connection = None
        self.is_connected = False
        self.last_activity = None
        self.total_sent = 0
        self.successful_sent = 0
        self.failed_sent = 0
        self._lock = threading.Lock()

    def connect(self) -> bool:
        """连接端口"""
        try:
            import serial

            with self._lock:
                if self.is_connected:
                    return True

                self.serial_connection = serial.Serial(
                    port=self.port_name,
                    baudrate=self.baud_rate,
                    bytesize=8,
                    stopbits=1,
                    parity='N',
                    timeout=1
                )

                if self.serial_connection.is_open:
                    self.is_connected = True
                    self.last_activity = datetime.now()
                    return True

                return False

        except ImportError:
            log_error("需要安装pyserial库")
            return False
        except Exception as e:
            log_error(f"连接端口{self.port_name}失败: {e}")
            return False

    def disconnect(self):
        """断开端口连接"""
        try:
            with self._lock:
                if self.serial_connection and self.serial_connection.is_open:
                    self.serial_connection.close()

                self.is_connected = False
                self.serial_connection = None

        except Exception as e:
            log_error(f"断开端口{self.port_name}失败: {e}")

    def send_at_command(self, command: str, timeout: int = 5) -> Optional[str]:
        """发送AT命令"""
        try:
            with self._lock:
                if not self.is_connected or not self.serial_connection:
                    return None

                # 发送命令
                cmd = f"{command}\r\n"
                self.serial_connection.write(cmd.encode())

                # 读取响应
                start_time = time.time()
                response = ""

                while time.time() - start_time < timeout:
                    if self.serial_connection.in_waiting > 0:
                        data = self.serial_connection.read(self.serial_connection.in_waiting)
                        response += data.decode('utf-8', errors='ignore')

                        # 检查是否收到完整响应
                        if 'OK' in response or 'ERROR' in response:
                            break

                    time.sleep(0.1)

                self.last_activity = datetime.now()
                return response.strip()

        except Exception as e:
            log_error(f"发送AT命令失败: {command} - {e}")
            return None

    def send_sms(self, phone: str, content: str, timeout: int = 30) -> Tuple[SendResult, str]:
        """发送短信"""
        try:
            with self._lock:
                if not self.is_connected:
                    return SendResult.ERROR, "端口未连接"

                self.total_sent += 1
                start_time = time.time()

                # 设置短信模式
                response = self.send_at_command("AT+CMGF=1", 5)
                if not response or "OK" not in response:
                    self.failed_sent += 1
                    return SendResult.FAILED, "设置短信模式失败"

                # 发送短信命令
                cmd = f'AT+CMGS="{phone}"'
                response = self.send_at_command(cmd, 10)
                if not response or ">" not in response:
                    self.failed_sent += 1
                    return SendResult.FAILED, "短信发送命令失败"

                # 发送消息内容
                msg_cmd = f"{content}\x1A"  # \x1A 是 Ctrl+Z
                self.serial_connection.write(msg_cmd.encode('utf-8', errors='ignore'))

                # 等待发送结果
                response = ""
                while time.time() - start_time < timeout:
                    if self.serial_connection.in_waiting > 0:
                        data = self.serial_connection.read(self.serial_connection.in_waiting)
                        response += data.decode('utf-8', errors='ignore')

                        if '+CMGS:' in response and 'OK' in response:
                            # 发送成功
                            self.successful_sent += 1
                            self.last_activity = datetime.now()
                            return SendResult.SUCCESS, "发送成功"
                        elif 'ERROR' in response:
                            # 发送失败
                            self.failed_sent += 1
                            return SendResult.FAILED, f"发送失败: {response}"

                    time.sleep(0.1)

                # 超时
                self.failed_sent += 1
                return SendResult.TIMEOUT, "发送超时"

        except Exception as e:
            self.failed_sent += 1
            return SendResult.ERROR, f"发送异常: {str(e)}"

    def get_signal_strength(self) -> Optional[int]:
        """获取信号强度"""
        try:
            response = self.send_at_command("AT+CSQ", 5)
            if response and "+CSQ:" in response:
                import re
                match = re.search(r'\+CSQ:\s*(\d+),', response)
                if match:
                    rssi = int(match.group(1))
                    return rssi if rssi != 99 else None
            return None
        except Exception:
            return None

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        success_rate = 0.0
        if self.total_sent > 0:
            success_rate = round(self.successful_sent / self.total_sent * 100, 2)

        return {
            'port_name': self.port_name,
            'is_connected': self.is_connected,
            'total_sent': self.total_sent,
            'successful_sent': self.successful_sent,
            'failed_sent': self.failed_sent,
            'success_rate': success_rate,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'signal_strength': self.get_signal_strength()
        }


class MessageSender:
    """短信发送器类"""

    def __init__(self):
        """初始化短信发送器"""
        self._send_queue = queue.PriorityQueue()
        self._port_connections: Dict[str, PortConnection] = {}
        self._worker_threads: List[threading.Thread] = []
        self._send_callbacks: List[Callable] = []
        self._is_running = False
        self._lock = threading.Lock()

        # 配置参数
        self.worker_count = 3
        self.default_send_interval = getattr(settings, 'DEFAULT_SEND_INTERVAL', 1000)
        self.default_timeout = getattr(settings, 'DEFAULT_TIMEOUT', 30)
        self.default_baud_rate = getattr(settings, 'PORT_BAUD_RATE', 115200)

        # 统计信息
        self.total_requests = 0
        self.successful_sends = 0
        self.failed_sends = 0
        self.start_time: Optional[datetime] = None

    def initialize(self) -> bool:
        """初始化发送器"""
        try:
            log_info("短信发送器初始化开始")

            # 启动工作线程
            self._start_worker_threads()

            self.start_time = datetime.now()
            log_info(f"短信发送器初始化完成，工作线程数: {self.worker_count}")
            return True

        except Exception as e:
            log_error("短信发送器初始化失败", error=e)
            return False

    def shutdown(self):
        """关闭发送器"""
        try:
            log_info("短信发送器开始关闭")

            # 停止工作线程
            self._is_running = False
            self._stop_worker_threads()

            # 断开所有端口连接
            self._disconnect_all_ports()

            # 清空队列
            while not self._send_queue.empty():
                try:
                    self._send_queue.get_nowait()
                except queue.Empty:
                    break

            # 清除回调
            self._send_callbacks.clear()

            log_info("短信发送器关闭完成")

        except Exception as e:
            log_error("短信发送器关闭失败", error=e)

    def get_status(self) -> Dict[str, Any]:
        """获取发送器状态"""
        success_rate = 0.0
        if self.total_requests > 0:
            success_rate = round(self.successful_sends / self.total_requests * 100, 2)

        return {
            'is_running': self._is_running,
            'worker_count': len([t for t in self._worker_threads if t.is_alive()]),
            'queue_size': self._send_queue.qsize(),
            'connected_ports': len([p for p in self._port_connections.values() if p.is_connected]),
            'total_ports': len(self._port_connections),
            'total_requests': self.total_requests,
            'successful_sends': self.successful_sends,
            'failed_sends': self.failed_sends,
            'success_rate': success_rate,
            'uptime': format_duration((datetime.now() - self.start_time).total_seconds()) if self.start_time else "0秒"
        }

    def add_port(self, port_name: str, baud_rate: int = None) -> bool:
        """添加端口"""
        try:
            if port_name in self._port_connections:
                return True

            if baud_rate is None:
                baud_rate = self.default_baud_rate

            port_conn = PortConnection(port_name, baud_rate)

            if port_conn.connect():
                self._port_connections[port_name] = port_conn
                log_info(f"成功添加端口: {port_name}")
                return True
            else:
                log_error(f"添加端口失败: {port_name}")
                return False

        except Exception as e:
            log_error(f"添加端口{port_name}异常", error=e)
            return False

    def remove_port(self, port_name: str) -> bool:
        """移除端口"""
        try:
            if port_name in self._port_connections:
                port_conn = self._port_connections[port_name]
                port_conn.disconnect()
                del self._port_connections[port_name]
                log_info(f"成功移除端口: {port_name}")
                return True
            return False

        except Exception as e:
            log_error(f"移除端口{port_name}异常", error=e)
            return False

    def send_message(self, message_id: int, phone: str, content: str,
                     message_type: MessageType = MessageType.SMS,
                     priority: int = 5, task_id: int = 0) -> bool:
        """发送消息"""
        try:
            # 验证手机号码
            if not validate_phone_number(phone) and not validate_phone_number(phone, international=True):
                log_error(f"无效的手机号码: {phone}")
                return False

            # 创建发送请求
            request = SendRequest(
                message_id=message_id,
                phone=phone,
                content=content,
                message_type=message_type,
                priority=priority,
                task_id=task_id
            )

            # 添加到队列
            self._send_queue.put((priority, time.time(), request))
            self.total_requests += 1

            log_info(f"消息已加入发送队列: ID={message_id}, 手机号={phone[:3]}****{phone[-4:]}")
            return True

        except Exception as e:
            log_error(f"发送消息异常: {e}")
            return False

    def send_test_message(self, phone: str, content: str, port_name: str = None) -> Dict[str, Any]:
        """发送测试消息"""
        try:
            # 选择端口
            if port_name:
                if port_name not in self._port_connections:
                    return {
                        'success': False,
                        'message': f'端口{port_name}不存在'
                    }
                port_conn = self._port_connections[port_name]
            else:
                # 自动选择可用端口
                port_conn = self._get_available_port()
                if not port_conn:
                    return {
                        'success': False,
                        'message': '没有可用的端口'
                    }

            # 发送测试消息
            result, message = port_conn.send_sms(phone, content, self.default_timeout)

            if result == SendResult.SUCCESS:
                log_message_send(0, phone, port_conn.port_name, 'success', '测试消息')
                return {
                    'success': True,
                    'message': '测试消息发送成功',
                    'port': port_conn.port_name,
                    'phone': phone
                }
            else:
                log_message_send(0, phone, port_conn.port_name, result.value, message)
                return {
                    'success': False,
                    'message': f'测试消息发送失败: {message}',
                    'port': port_conn.port_name,
                    'error': message
                }

        except Exception as e:
            log_error("发送测试消息异常", error=e)
            return {
                'success': False,
                'message': f'发送异常: {str(e)}'
            }

    def get_queue_info(self) -> Dict[str, Any]:
        """获取队列信息"""
        return {
            'queue_size': self._send_queue.qsize(),
            'is_empty': self._send_queue.empty(),
            'estimated_wait_time': self._estimate_wait_time()
        }

    def clear_queue(self) -> int:
        """清空发送队列"""
        try:
            cleared_count = 0
            while not self._send_queue.empty():
                try:
                    self._send_queue.get_nowait()
                    cleared_count += 1
                except queue.Empty:
                    break

            log_info(f"清空发送队列，清除{cleared_count}条消息")
            return cleared_count

        except Exception as e:
            log_error("清空发送队列异常", error=e)
            return 0

    def get_port_statistics(self) -> List[Dict[str, Any]]:
        """获取端口统计"""
        return [port.get_stats() for port in self._port_connections.values()]

    def add_send_callback(self, callback: Callable[[int, str, SendResult, str], None]):
        """添加发送完成回调"""
        if callable(callback):
            self._send_callbacks.append(callback)
            log_info(f"添加发送回调函数，当前回调数量: {len(self._send_callbacks)}")

    def remove_send_callback(self, callback: Callable[[int, str, SendResult, str], None]):
        """移除发送完成回调"""
        if callback in self._send_callbacks:
            self._send_callbacks.remove(callback)
            log_info(f"移除发送回调函数，当前回调数量: {len(self._send_callbacks)}")

    def _start_worker_threads(self):
        """启动工作线程"""
        try:
            self._is_running = True
            self._worker_threads.clear()

            for i in range(self.worker_count):
                worker_thread = threading.Thread(
                    target=self._worker_loop,
                    name=f"MessageSender-Worker-{i}",
                    daemon=True
                )
                worker_thread.start()
                self._worker_threads.append(worker_thread)

            log_info(f"启动{self.worker_count}个发送工作线程")

        except Exception as e:
            log_error("启动工作线程失败", error=e)

    def _stop_worker_threads(self):
        """停止工作线程"""
        try:
            # 等待所有线程结束
            for thread in self._worker_threads:
                if thread.is_alive():
                    thread.join(timeout=5)

            self._worker_threads.clear()
            log_info("所有发送工作线程已停止")

        except Exception as e:
            log_error("停止工作线程失败", error=e)

    def _worker_loop(self):
        """工作线程主循环"""
        thread_name = threading.current_thread().name
        log_info(f"发送工作线程 {thread_name} 启动")

        while self._is_running:
            try:
                # 从队列获取发送请求
                try:
                    priority, timestamp, request = self._send_queue.get(timeout=1)
                except queue.Empty:
                    continue

                # 处理发送请求
                self._process_send_request(request)

                # 标记队列任务完成
                self._send_queue.task_done()

                # 发送间隔控制
                time.sleep(self.default_send_interval / 1000.0)

            except Exception as e:
                log_error(f"工作线程 {thread_name} 处理异常", error=e)
                time.sleep(1)

        log_info(f"发送工作线程 {thread_name} 停止")

    def _process_send_request(self, request: SendRequest):
        """处理发送请求"""
        try:
            request.attempts += 1

            # 选择可用端口
            port_conn = self._get_available_port()
            if not port_conn:
                self._handle_send_result(request, SendResult.ERROR, "没有可用端口")
                return

            # 发送消息
            result, message = port_conn.send_sms(
                request.phone,
                request.content,
                self.default_timeout
            )

            # 处理发送结果
            if result == SendResult.SUCCESS:
                self.successful_sends += 1
                self._handle_send_result(request, result, message)
            else:
                self.failed_sends += 1
                request.last_error = message

                # 检查是否需要重试
                if request.can_retry():
                    log_info(f"消息{request.message_id}发送失败，将重试 ({request.attempts}/{request.max_attempts})")
                    # 重新加入队列
                    self._send_queue.put((request.priority + 1, time.time() + 60, request))  # 1分钟后重试
                else:
                    self._handle_send_result(request, result, message)

        except Exception as e:
            self.failed_sends += 1
            self._handle_send_result(request, SendResult.ERROR, str(e))

    def _handle_send_result(self, request: SendRequest, result: SendResult, message: str):
        """处理发送结果"""
        try:
            # 记录日志
            log_message_send(
                request.task_id,
                request.phone,
                "AUTO",  # 自动选择的端口
                result.value,
                message
            )

            # 通知回调
            self._notify_send_complete(request.message_id, request.phone, result, message)

        except Exception as e:
            log_error("处理发送结果异常", error=e)

    def _notify_send_complete(self, message_id: int, phone: str, result: SendResult, message: str):
        """通知发送完成"""
        try:
            for callback in self._send_callbacks:
                try:
                    callback(message_id, phone, result, message)
                except Exception as e:
                    log_error("发送回调执行失败", error=e)
        except Exception as e:
            log_error("通知发送完成失败", error=e)

    def _get_available_port(self) -> Optional[PortConnection]:
        """获取可用端口"""
        try:
            available_ports = [p for p in self._port_connections.values() if p.is_connected]

            if not available_ports:
                return None

            # 选择发送量最少的端口（负载均衡）
            return min(available_ports, key=lambda p: p.total_sent)

        except Exception as e:
            log_error("获取可用端口异常", error=e)
            return None

    def _disconnect_all_ports(self):
        """断开所有端口连接"""
        try:
            for port_conn in self._port_connections.values():
                port_conn.disconnect()
            log_info("所有端口连接已断开")
        except Exception as e:
            log_error("断开所有端口连接失败", error=e)

    def _estimate_wait_time(self) -> float:
        """估算等待时间（秒）"""
        try:
            queue_size = self._send_queue.qsize()
            if queue_size == 0:
                return 0.0

            # 根据工作线程数和发送间隔估算
            workers = len([t for t in self._worker_threads if t.is_alive()])
            if workers == 0:
                return float('inf')

            avg_send_time = self.default_send_interval / 1000.0 + self.default_timeout
            return (queue_size / workers) * avg_send_time

        except Exception:
            return 0.0

    def reconnect_port(self, port_name: str) -> bool:
        """重连端口"""
        try:
            if port_name not in self._port_connections:
                return False

            port_conn = self._port_connections[port_name]
            port_conn.disconnect()

            if port_conn.connect():
                log_info(f"端口{port_name}重连成功")
                return True
            else:
                log_error(f"端口{port_name}重连失败")
                return False

        except Exception as e:
            log_error(f"重连端口{port_name}异常", error=e)
            return False

    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        try:
            total_time = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0

            avg_throughput = 0.0
            if total_time > 0:
                avg_throughput = round((self.successful_sends + self.failed_sends) / total_time, 2)

            return {
                'uptime_seconds': total_time,
                'uptime_formatted': format_duration(total_time),
                'total_processed': self.successful_sends + self.failed_sends,
                'success_rate': round(self.successful_sends / max(self.total_requests, 1) * 100, 2),
                'avg_throughput_per_second': avg_throughput,
                'current_queue_size': self._send_queue.qsize(),
                'active_workers': len([t for t in self._worker_threads if t.is_alive()]),
                'connected_ports': len([p for p in self._port_connections.values() if p.is_connected])
            }

        except Exception as e:
            log_error("获取性能统计失败", error=e)
            return {}


# 全局短信发送器实例
message_sender = MessageSender()