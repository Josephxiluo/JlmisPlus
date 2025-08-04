"""
猫池短信系统消息处理服务 - tkinter版
Message processing service for SMS Pool System - tkinter version
"""

import sys
import threading
import time
import queue
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Callable
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from models.message import TaskMessage, MessageStatus, MessageCarrier, task_message_manager
    from models.port import Port, port_manager
    from models.task import Task
    from config.settings import settings
    from config.logging_config import get_logger, log_message_send, log_error, log_info, log_timer_action
except ImportError:
    # 简化处理
    class MockTaskMessage:
        def __init__(self, **kwargs):
            self.id = 1
            self.recipient_number = kwargs.get('recipient_number', '')
            self.status = 'pending'

        def mark_as_sending(self, port):
            return True

        def mark_as_success(self):
            return True

        def mark_as_failed(self, error_msg):
            return True


    class MockPort:
        def __init__(self, name):
            self.port_name = name
            self.is_available = lambda: True
            self.can_send = lambda: True
            self.send_sms = lambda phone, msg: True


    class MockPortManager:
        def get_next_available_port(self, carrier=None, exclude=None):
            return MockPort("COM1")


    class MockTaskMessageManager:
        pass


    TaskMessage = MockTaskMessage
    port_manager = MockPortManager()
    task_message_manager = MockTaskMessageManager()


    class MessageStatus:
        PENDING = "pending"
        SENDING = "sending"
        SUCCESS = "success"
        FAILED = "failed"
        TIMEOUT = "timeout"


    class MessageCarrier:
        MOBILE = "mobile"
        UNICOM = "unicom"
        TELECOM = "telecom"
        UNKNOWN = "unknown"


    class MockTask:
        @classmethod
        def find_by_id(cls, task_id):
            return cls()

        def update_progress(self, **kwargs):
            return True


    Task = MockTask


    class MockSettings:
        DEFAULT_SEND_INTERVAL = 1000
        MONITOR_ALERT_INTERVAL = 1000
        DEFAULT_MONITOR_PHONE = ""
        SMS_RATE = 1.0
        MMS_RATE = 3.0


    settings = MockSettings()

    import logging


    def get_logger(name='services.message'):
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


    def log_timer_action(timer_name, action, interval=None):
        logger = get_logger()
        message = f"[定时器] {timer_name} {action}"
        if interval:
            message += f" 间隔={interval}秒"
        logger.debug(message)

logger = get_logger('services.message')


class MessageService:
    """消息处理服务类"""

    def __init__(self):
        """初始化消息服务"""
        self.message_manager = task_message_manager
        self.port_manager = port_manager
        self._lock = threading.Lock()
        self._send_queue = queue.PriorityQueue()
        self._worker_threads: List[threading.Thread] = []
        self._message_callbacks: list = []
        self._monitor_counters: Dict[int, int] = {}  # 任务ID -> 发送计数
        self.is_initialized = False
        self.is_running = False

        # 配置参数
        self.worker_count = 3  # 工作线程数量
        self.default_send_interval = getattr(settings, 'DEFAULT_SEND_INTERVAL', 1000)
        self.monitor_alert_interval = getattr(settings, 'MONITOR_ALERT_INTERVAL', 1000)
        self.default_monitor_phone = getattr(settings, 'DEFAULT_MONITOR_PHONE', '')
        self.max_retry_count = 3
        self.send_timeout = 30  # 发送超时时间（秒）

    def initialize(self) -> bool:
        """初始化服务"""
        try:
            log_info("消息处理服务初始化开始")

            # 启动工作线程
            self._start_worker_threads()

            self.is_initialized = True
            self.is_running = True
            log_info(f"消息处理服务初始化完成，工作线程数: {self.worker_count}")
            return True

        except Exception as e:
            log_error("消息处理服务初始化失败", error=e)
            return False

    def shutdown(self):
        """关闭服务"""
        try:
            log_info("消息处理服务开始关闭")

            # 停止工作线程
            self.is_running = False
            self._stop_worker_threads()

            # 清空队列
            while not self._send_queue.empty():
                try:
                    self._send_queue.get_nowait()
                except queue.Empty:
                    break

            # 清除回调
            self._message_callbacks.clear()
            self._monitor_counters.clear()

            self.is_initialized = False
            log_info("消息处理服务关闭完成")

        except Exception as e:
            log_error("消息处理服务关闭失败", error=e)

    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        return {
            'running': self.is_initialized and self.is_running,
            'worker_count': self.worker_count,
            'active_workers': len([t for t in self._worker_threads if t.is_alive()]),
            'queue_size': self._send_queue.qsize(),
            'default_send_interval': self.default_send_interval,
            'monitor_alert_interval': self.monitor_alert_interval,
            'max_retry_count': self.max_retry_count,
            'send_timeout': self.send_timeout,
            'message': '消息处理服务正常运行' if (self.is_initialized and self.is_running) else '消息处理服务未运行'
        }

    def send_message(self, message_id: int, priority: int = 5) -> Dict[str, Any]:
        """发送单条消息"""
        try:
            message = TaskMessage.find_by_id(message_id)
            if not message:
                return {
                    'success': False,
                    'message': '消息不存在',
                    'error_code': 'MESSAGE_NOT_FOUND'
                }

            # 添加到发送队列
            self._send_queue.put((priority, time.time(), message_id))

            return {
                'success': True,
                'message': '消息已加入发送队列',
                'message_id': message_id,
                'queue_size': self._send_queue.qsize()
            }

        except Exception as e:
            log_error(f"发送消息{message_id}异常", error=e)
            return {
                'success': False,
                'message': f'发送异常: {str(e)}',
                'error_code': 'SYSTEM_ERROR'
            }

    def send_task_messages(self, task_id: int) -> Dict[str, Any]:
        """发送任务的所有待发送消息"""
        try:
            # 获取待发送消息
            pending_messages = TaskMessage.find_pending_messages(task_id)

            if not pending_messages:
                return {
                    'success': False,
                    'message': '没有待发送的消息',
                    'error_code': 'NO_PENDING_MESSAGES'
                }

            # 批量添加到发送队列
            added_count = 0
            for message in pending_messages:
                priority = message.priority if hasattr(message, 'priority') else 5
                self._send_queue.put((priority, time.time(), message.id))
                added_count += 1

            log_info(f"任务{task_id}的{added_count}条消息已加入发送队列")

            return {
                'success': True,
                'message': f'{added_count}条消息已加入发送队列',
                'task_id': task_id,
                'added_count': added_count,
                'queue_size': self._send_queue.qsize()
            }

        except Exception as e:
            log_error(f"发送任务{task_id}消息异常", error=e)
            return {
                'success': False,
                'message': f'发送异常: {str(e)}',
                'error_code': 'SYSTEM_ERROR'
            }

    def send_test_message(self, phone: str, content: str, port_name: str = None) -> Dict[str, Any]:
        """发送测试消息"""
        try:
            # 获取指定端口或自动选择
            if port_name:
                port = self.port_manager.get_port(port_name)
                if not port or not port.is_available():
                    return {
                        'success': False,
                        'message': f'端口{port_name}不可用',
                        'error_code': 'PORT_UNAVAILABLE'
                    }
            else:
                port = self.port_manager.get_next_available_port()
                if not port:
                    return {
                        'success': False,
                        'message': '没有可用的端口',
                        'error_code': 'NO_AVAILABLE_PORT'
                    }

            # 发送测试消息
            if port.send_sms(phone, content):
                log_message_send(0, phone, port.port_name, 'success', '测试消息')
                return {
                    'success': True,
                    'message': f'测试消息发送成功',
                    'phone': phone,
                    'port': port.port_name
                }
            else:
                log_message_send(0, phone, port.port_name, 'failed', '测试消息发送失败')
                return {
                    'success': False,
                    'message': '测试消息发送失败',
                    'error_code': 'SEND_FAILED'
                }

        except Exception as e:
            log_error("发送测试消息异常", error=e)
            return {
                'success': False,
                'message': f'发送异常: {str(e)}',
                'error_code': 'SYSTEM_ERROR'
            }

    def get_queue_status(self) -> Dict[str, Any]:
        """获取队列状态"""
        try:
            return {
                'queue_size': self._send_queue.qsize(),
                'is_empty': self._send_queue.empty(),
                'worker_status': [
                    {
                        'thread_id': i,
                        'is_alive': thread.is_alive(),
                        'name': thread.name
                    }
                    for i, thread in enumerate(self._worker_threads)
                ]
            }
        except Exception as e:
            log_error("获取队列状态异常", error=e)
            return {}

    def clear_queue(self) -> Dict[str, Any]:
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

            return {
                'success': True,
                'message': f'成功清除{cleared_count}条待发送消息',
                'cleared_count': cleared_count
            }

        except Exception as e:
            log_error("清空发送队列异常", error=e)
            return {
                'success': False,
                'message': f'清空异常: {str(e)}',
                'error_code': 'SYSTEM_ERROR'
            }

    def pause_sending(self) -> Dict[str, Any]:
        """暂停发送"""
        try:
            self.is_running = False
            log_info("消息发送已暂停")

            return {
                'success': True,
                'message': '消息发送已暂停',
                'queue_size': self._send_queue.qsize()
            }

        except Exception as e:
            log_error("暂停发送异常", error=e)
            return {
                'success': False,
                'message': f'暂停异常: {str(e)}',
                'error_code': 'SYSTEM_ERROR'
            }

    def resume_sending(self) -> Dict[str, Any]:
        """恢复发送"""
        try:
            self.is_running = True
            log_info("消息发送已恢复")

            return {
                'success': True,
                'message': '消息发送已恢复',
                'queue_size': self._send_queue.qsize()
            }

        except Exception as e:
            log_error("恢复发送异常", error=e)
            return {
                'success': False,
                'message': f'恢复异常: {str(e)}',
                'error_code': 'SYSTEM_ERROR'
            }

    def add_message_callback(self, callback: Callable[[str, TaskMessage], None]):
        """添加消息状态变化回调函数"""
        try:
            if callable(callback):
                self._message_callbacks.append(callback)
                log_info(f"添加消息回调函数，当前回调数量: {len(self._message_callbacks)}")
        except Exception as e:
            log_error("添加消息回调失败", error=e)

    def remove_message_callback(self, callback: Callable[[str, TaskMessage], None]):
        """移除消息状态变化回调函数"""
        try:
            if callback in self._message_callbacks:
                self._message_callbacks.remove(callback)
                log_info(f"移除消息回调函数，当前回调数量: {len(self._message_callbacks)}")
        except Exception as e:
            log_error("移除消息回调失败", error=e)

    def get_sending_statistics(self) -> Dict[str, Any]:
        """获取发送统计"""
        try:
            # 这里可以从数据库获取更详细的统计信息
            return {
                'queue_size': self._send_queue.qsize(),
                'is_running': self.is_running,
                'worker_count': len([t for t in self._worker_threads if t.is_alive()]),
                'monitor_counters': self._monitor_counters.copy()
            }
        except Exception as e:
            log_error("获取发送统计异常", error=e)
            return {}

    def _start_worker_threads(self):
        """启动工作线程"""
        try:
            self._worker_threads.clear()

            for i in range(self.worker_count):
                worker_thread = threading.Thread(
                    target=self._worker_loop,
                    name=f"MessageWorker-{i}",
                    daemon=True
                )
                worker_thread.start()
                self._worker_threads.append(worker_thread)

            log_info(f"启动{self.worker_count}个消息发送工作线程")

        except Exception as e:
            log_error("启动工作线程失败", error=e)

    def _stop_worker_threads(self):
        """停止工作线程"""
        try:
            # 等待所有线程结束
            for thread in self._worker_threads:
                if thread.is_alive():
                    thread.join(timeout=5)  # 最多等待5秒

            self._worker_threads.clear()
            log_info("所有消息发送工作线程已停止")

        except Exception as e:
            log_error("停止工作线程失败", error=e)

    def _worker_loop(self):
        """工作线程主循环"""
        thread_name = threading.current_thread().name
        log_info(f"消息发送工作线程 {thread_name} 启动")

        while self.is_running:
            try:
                # 从队列获取消息
                try:
                    priority, timestamp, message_id = self._send_queue.get(timeout=1)
                except queue.Empty:
                    continue

                # 处理消息
                self._process_message(message_id)

                # 标记队列任务完成
                self._send_queue.task_done()

            except Exception as e:
                log_error(f"工作线程 {thread_name} 处理异常", error=e)
                time.sleep(1)  # 避免异常循环

        log_info(f"消息发送工作线程 {thread_name} 停止")

    def _process_message(self, message_id: int):
        """处理单条消息"""
        try:
            # 获取消息
            message = TaskMessage.find_by_id(message_id)
            if not message:
                log_error(f"消息{message_id}不存在")
                return

            # 检查消息状态
            if message.status != MessageStatus.PENDING.value:
                log_error(f"消息{message_id}状态不是待发送: {message.status}")
                return

            # 获取可用端口
            port = self.port_manager.get_next_available_port(
                carrier=message.carrier,
                exclude_ports=[]
            )

            if not port:
                log_error(f"没有可用端口发送消息{message_id}")
                message.mark_as_failed('没有可用端口')
                self._notify_message_change('failed', message)
                return

            # 检查端口发送能力
            if not port.can_send():
                log_error(f"端口{port.port_name}暂时不能发送")
                # 重新放回队列，稍后重试
                self._send_queue.put((5, time.time() + 60, message_id))  # 1分钟后重试
                return

            # 标记消息为发送中
            message.mark_as_sending(port.port_name)
            self._notify_message_change('sending', message)

            # 发送消息
            success = self._send_message_via_port(message, port)

            if success:
                # 发送成功
                message.mark_as_success()
                self._notify_message_change('success', message)

                # 更新任务进度
                task = Task.find_by_id(message.task_id)
                if task:
                    task.update_progress(success_delta=1)

                # 检查监测提醒
                self._check_monitor_alert(message.task_id)

                log_message_send(
                    message.task_id,
                    message.recipient_number,
                    port.port_name,
                    'success'
                )

            else:
                # 发送失败
                error_msg = port.error_message or '发送失败'
                message.mark_as_failed(error_msg)
                self._notify_message_change('failed', message)

                # 更新任务进度
                task = Task.find_by_id(message.task_id)
                if task:
                    task.update_progress(failed_delta=1)

                log_message_send(
                    message.task_id,
                    message.recipient_number,
                    port.port_name,
                    'failed',
                    error_msg
                )

        except Exception as e:
            log_error(f"处理消息{message_id}异常", error=e)
            # 标记消息失败
            try:
                message = TaskMessage.find_by_id(message_id)
                if message:
                    message.mark_as_failed(f'处理异常: {str(e)}')
                    self._notify_message_change('failed', message)
            except:
                pass

    def _send_message_via_port(self, message: TaskMessage, port: Port) -> bool:
        """通过指定端口发送消息"""
        try:
            # 检查发送间隔
            if port.last_send_time:
                time_since_last = datetime.now() - port.last_send_time
                interval_ms = time_since_last.total_seconds() * 1000

                if interval_ms < port.send_interval:
                    # 等待到发送间隔
                    wait_time = (port.send_interval - interval_ms) / 1000
                    time.sleep(wait_time)

            # 发送短信
            start_time = time.time()
            success = port.send_sms(message.recipient_number, message.message_content)
            send_duration = time.time() - start_time

            # 检查超时
            if send_duration > self.send_timeout:
                log_error(f"消息发送超时: {send_duration:.2f}秒")
                message.mark_as_timeout()
                return False

            return success

        except Exception as e:
            log_error("通过端口发送消息异常", error=e)
            return False

    def _check_monitor_alert(self, task_id: int):
        """检查监测提醒"""
        try:
            if not self.default_monitor_phone:
                return

            # 更新发送计数
            self._monitor_counters[task_id] = self._monitor_counters.get(task_id, 0) + 1

            # 检查是否需要发送监测消息
            if self._monitor_counters[task_id] % self.monitor_alert_interval == 0:
                self._send_monitor_message(task_id)

        except Exception as e:
            log_error(f"检查监测提醒异常", error=e)

    def _send_monitor_message(self, task_id: int):
        """发送监测消息"""
        try:
            if not self.default_monitor_phone:
                return

            # 获取任务信息
            task = Task.find_by_id(task_id)
            if not task:
                return

            # 构建监测消息内容
            monitor_content = f"监测提醒: 任务【{task.title}】已发送{self._monitor_counters[task_id]}条消息"

            # 发送监测消息
            result = self.send_test_message(self.default_monitor_phone, monitor_content)

            if result['success']:
                log_info(f"任务{task_id}监测消息发送成功")
            else:
                log_error(f"任务{task_id}监测消息发送失败: {result['message']}")

        except Exception as e:
            log_error(f"发送监测消息异常", error=e)

    def _notify_message_change(self, action: str, message: TaskMessage):
        """通知消息状态变化"""
        try:
            for callback in self._message_callbacks:
                try:
                    callback(action, message)
                except Exception as e:
                    log_error("消息变化回调执行失败", error=e)

        except Exception as e:
            log_error("通知消息变化失败", error=e)

    def set_worker_count(self, count: int):
        """设置工作线程数量"""
        try:
            if count < 1:
                count = 1
            elif count > 10:
                count = 10

            old_count = self.worker_count
            self.worker_count = count

            # 重启工作线程
            if self.is_initialized:
                self.is_running = False
                self._stop_worker_threads()
                self.is_running = True
                self._start_worker_threads()

            log_info(f"消息发送工作线程数量已更新: {old_count} -> {count}")

        except Exception as e:
            log_error("设置工作线程数量失败", error=e)

    def set_send_timeout(self, timeout_seconds: int):
        """设置发送超时时间"""
        try:
            if timeout_seconds < 5:
                timeout_seconds = 5
            elif timeout_seconds > 300:
                timeout_seconds = 300

            old_timeout = self.send_timeout
            self.send_timeout = timeout_seconds

            log_info(f"消息发送超时时间已更新: {old_timeout}秒 -> {timeout_seconds}秒")

        except Exception as e:
            log_error("设置发送超时时间失败", error=e)

    def set_monitor_phone(self, phone: str):
        """设置监测号码"""
        try:
            old_phone = self.default_monitor_phone
            self.default_monitor_phone = phone

            log_info(f"监测号码已更新: {old_phone} -> {phone}")

        except Exception as e:
            log_error("设置监测号码失败", error=e)

    def reset_monitor_counter(self, task_id: int = None):
        """重置监测计数器"""
        try:
            if task_id:
                self._monitor_counters[task_id] = 0
                log_info(f"任务{task_id}监测计数器已重置")
            else:
                self._monitor_counters.clear()
                log_info("所有监测计数器已重置")

        except Exception as e:
            log_error("重置监测计数器失败", error=e)

    def get_message_queue_info(self) -> List[Dict[str, Any]]:
        """获取消息队列信息"""
        try:
            queue_info = []
            temp_items = []

            # 临时取出所有项目查看
            while not self._send_queue.empty():
                try:
                    item = self._send_queue.get_nowait()
                    temp_items.append(item)

                    priority, timestamp, message_id = item
                    message = TaskMessage.find_by_id(message_id)

                    queue_info.append({
                        'message_id': message_id,
                        'priority': priority,
                        'timestamp': timestamp,
                        'recipient': message.recipient_number if message else 'Unknown',
                        'task_id': message.task_id if message else 0,
                        'wait_time': time.time() - timestamp
                    })
                except queue.Empty:
                    break

            # 将项目放回队列
            for item in temp_items:
                self._send_queue.put(item)

            return sorted(queue_info, key=lambda x: x['priority'])

        except Exception as e:
            log_error("获取消息队列信息异常", error=e)
            return []


# 全局消息服务实例
message_service = MessageService()