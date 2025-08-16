"""
猫池短信系统短信发送模拟器
SMS sending simulator for SMS Pool System
实现批量发送队列管理和发送结果模拟
"""

import sys
import time
import random
import threading
import queue
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.settings import settings
from config.logging_config import get_logger, log_message_send, log_info, log_error
from core.simulator.port_simulator import port_simulator, SimulatedPort

logger = get_logger('core.simulator.sms')


class SendPriority(Enum):
    """发送优先级"""
    LOW = 1
    NORMAL = 5
    HIGH = 8
    URGENT = 10


@dataclass
class SimulatedMessage:
    """模拟消息类"""

    message_id: int
    task_id: int
    phone: str
    content: str
    port_name: Optional[str] = None
    priority: int = SendPriority.NORMAL.value
    retry_count: int = 0
    max_retries: int = 3
    created_time: datetime = field(default_factory=datetime.now)
    scheduled_time: Optional[datetime] = None

    # 发送结果
    send_time: Optional[datetime] = None
    complete_time: Optional[datetime] = None
    success: Optional[bool] = None
    error_message: Optional[str] = None
    duration: Optional[float] = None

    def __lt__(self, other):
        """比较优先级（用于优先队列）"""
        return self.priority > other.priority

    def can_retry(self) -> bool:
        """是否可以重试"""
        return self.retry_count < self.max_retries and not self.success

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'message_id': self.message_id,
            'task_id': self.task_id,
            'phone': self.phone,
            'content': self.content[:50] + '...' if len(self.content) > 50 else self.content,
            'port_name': self.port_name,
            'priority': self.priority,
            'retry_count': self.retry_count,
            'success': self.success,
            'error_message': self.error_message,
            'duration': self.duration,
            'send_time': self.send_time.isoformat() if self.send_time else None,
            'complete_time': self.complete_time.isoformat() if self.complete_time else None
        }


class MessageQueue:
    """消息队列管理类"""

    def __init__(self, max_size: int = 10000):
        """
        初始化消息队列
        Args:
            max_size: 队列最大容量
        """
        self.queue = queue.PriorityQueue(maxsize=max_size)
        self.processing_messages: Dict[int, SimulatedMessage] = {}
        self.completed_messages: List[SimulatedMessage] = []
        self.failed_messages: List[SimulatedMessage] = []
        self._lock = threading.Lock()

        # 统计信息
        self.total_enqueued = 0
        self.total_processed = 0
        self.total_success = 0
        self.total_failed = 0

    def enqueue(self, message: SimulatedMessage) -> bool:
        """入队消息"""
        try:
            # 使用优先级和时间戳作为排序依据
            priority_key = (-message.priority, time.time())
            self.queue.put((priority_key, message), block=False)

            with self._lock:
                self.total_enqueued += 1

            return True
        except queue.Full:
            log_error(f"消息队列已满，无法添加消息{message.message_id}")
            return False

    def dequeue(self, timeout: float = 1.0) -> Optional[SimulatedMessage]:
        """出队消息"""
        try:
            _, message = self.queue.get(timeout=timeout)

            with self._lock:
                self.processing_messages[message.message_id] = message

            return message
        except queue.Empty:
            return None

    def complete_message(self, message: SimulatedMessage, success: bool, error_message: str = None):
        """完成消息处理"""
        with self._lock:
            # 从处理中移除
            if message.message_id in self.processing_messages:
                del self.processing_messages[message.message_id]

            # 更新统计
            self.total_processed += 1

            if success:
                self.total_success += 1
                self.completed_messages.append(message)
                # 限制历史记录大小
                if len(self.completed_messages) > 1000:
                    self.completed_messages = self.completed_messages[-500:]
            else:
                self.total_failed += 1
                self.failed_messages.append(message)
                # 限制历史记录大小
                if len(self.failed_messages) > 1000:
                    self.failed_messages = self.failed_messages[-500:]

    def get_stats(self) -> Dict[str, Any]:
        """获取队列统计"""
        with self._lock:
            success_rate = 0.0
            if self.total_processed > 0:
                success_rate = (self.total_success / self.total_processed) * 100

            return {
                'queue_size': self.queue.qsize(),
                'processing_count': len(self.processing_messages),
                'total_enqueued': self.total_enqueued,
                'total_processed': self.total_processed,
                'total_success': self.total_success,
                'total_failed': self.total_failed,
                'success_rate': round(success_rate, 2),
                'completed_count': len(self.completed_messages),
                'failed_count': len(self.failed_messages)
            }

    def clear(self):
        """清空队列"""
        with self._lock:
            # 清空队列
            while not self.queue.empty():
                try:
                    self.queue.get_nowait()
                except queue.Empty:
                    break

            # 清空其他数据
            self.processing_messages.clear()
            self.completed_messages.clear()
            self.failed_messages.clear()

            # 重置统计
            self.total_enqueued = 0
            self.total_processed = 0
            self.total_success = 0
            self.total_failed = 0


class SMSSimulator:
    """短信发送模拟器"""

    def __init__(self):
        """初始化短信模拟器"""
        self.port_simulator = port_simulator
        self.message_queue = MessageQueue()
        self.worker_threads: List[threading.Thread] = []
        self.is_running = False
        self._lock = threading.Lock()

        # 配置参数
        self.worker_count = 5  # 工作线程数
        self.default_send_interval = getattr(settings, 'DEFAULT_SEND_INTERVAL', 1000)
        self.batch_size = 100  # 批量处理大小
        self.success_rate = 0.7  # 默认成功率

        # 回调函数
        self.send_callbacks: List[Callable] = []

        # 端口分配策略
        self.port_allocation_strategy = 'round_robin'  # round_robin, random, load_balance
        self.current_port_index = 0

        log_info(f"短信模拟器初始化完成，工作线程数: {self.worker_count}")

    def start(self):
        """启动模拟器"""
        if self.is_running:
            log_info("短信模拟器已在运行")
            return

        self.is_running = True

        # 启动工作线程
        for i in range(self.worker_count):
            thread = threading.Thread(
                target=self._worker_loop,
                name=f"SMSWorker-{i}",
                daemon=True
            )
            thread.start()
            self.worker_threads.append(thread)

        log_info(f"短信模拟器启动，{self.worker_count}个工作线程开始工作")

    def stop(self):
        """停止模拟器"""
        if not self.is_running:
            return

        self.is_running = False

        # 等待工作线程结束
        for thread in self.worker_threads:
            thread.join(timeout=5)

        self.worker_threads.clear()
        log_info("短信模拟器已停止")

    def send_message(self, message_id: int, task_id: int, phone: str,
                     content: str, priority: int = SendPriority.NORMAL.value) -> bool:
        """
        发送单条消息
        """
        message = SimulatedMessage(
            message_id=message_id,
            task_id=task_id,
            phone=phone,
            content=content,
            priority=priority
        )

        return self.message_queue.enqueue(message)

    def send_batch(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        批量发送消息
        """
        success_count = 0
        failed_count = 0

        for msg_data in messages:
            message = SimulatedMessage(
                message_id=msg_data.get('message_id', 0),
                task_id=msg_data.get('task_id', 0),
                phone=msg_data.get('phone', ''),
                content=msg_data.get('content', ''),
                priority=msg_data.get('priority', SendPriority.NORMAL.value)
            )

            if self.message_queue.enqueue(message):
                success_count += 1
            else:
                failed_count += 1

        return {
            'success': True,
            'enqueued': success_count,
            'failed': failed_count,
            'queue_size': self.message_queue.queue.qsize()
        }

    def _worker_loop(self):
        """工作线程主循环"""
        thread_name = threading.current_thread().name
        log_info(f"工作线程{thread_name}启动")

        while self.is_running:
            try:
                # 从队列获取消息
                message = self.message_queue.dequeue(timeout=1.0)
                if not message:
                    continue

                # 处理消息
                self._process_message(message)

            except Exception as e:
                log_error(f"工作线程{thread_name}处理异常: {e}")
                time.sleep(0.1)

        log_info(f"工作线程{thread_name}停止")

    def _process_message(self, message: SimulatedMessage):
        """处理单条消息"""
        try:
            # 分配端口
            port = self._allocate_port()
            if not port:
                # 没有可用端口，重新入队
                time.sleep(1)
                message.retry_count += 1
                if message.can_retry():
                    self.message_queue.enqueue(message)
                else:
                    self._handle_send_failure(message, "没有可用端口")
                return

            message.port_name = port.port_name
            message.send_time = datetime.now()

            # 通知开始发送
            self._notify_callback('sending', message)

            # 模拟发送
            success, error_msg, duration = port.send_sms(message.phone, message.content)

            message.complete_time = datetime.now()
            message.duration = duration

            if success:
                self._handle_send_success(message)
            else:
                self._handle_send_failure(message, error_msg)

        except Exception as e:
            log_error(f"处理消息{message.message_id}异常: {e}")
            self._handle_send_failure(message, str(e))

    def _allocate_port(self) -> Optional[SimulatedPort]:
        """分配可用端口"""
        available_ports = []

        # 获取所有已连接的端口
        for port_name, port in self.port_simulator.ports.items():
            if port.is_connected and port.can_send():
                available_ports.append(port)

        if not available_ports:
            return None

        # 根据策略选择端口
        if self.port_allocation_strategy == 'round_robin':
            # 轮询
            self.current_port_index = (self.current_port_index + 1) % len(available_ports)
            return available_ports[self.current_port_index]

        elif self.port_allocation_strategy == 'random':
            # 随机
            return random.choice(available_ports)

        elif self.port_allocation_strategy == 'load_balance':
            # 负载均衡（选择发送量最少的）
            return min(available_ports, key=lambda p: p.send_count)

        return available_ports[0]

    def _handle_send_success(self, message: SimulatedMessage):
        """处理发送成功"""
        message.success = True

        # 更新队列统计
        self.message_queue.complete_message(message, True)

        # 记录日志
        log_message_send(
            message.task_id,
            message.phone,
            message.port_name,
            'success',
            f'耗时: {message.duration:.2f}秒'
        )

        # 通知回调
        self._notify_callback('success', message)

    def _handle_send_failure(self, message: SimulatedMessage, error_msg: str):
        """处理发送失败"""
        message.error_message = error_msg
        message.retry_count += 1

        # 检查是否需要重试
        if message.can_retry():
            # 延迟重试
            message.scheduled_time = datetime.now() + timedelta(seconds=5 * message.retry_count)
            self.message_queue.enqueue(message)

            log_message_send(
                message.task_id,
                message.phone,
                message.port_name or 'N/A',
                'retry',
                f'第{message.retry_count}次重试'
            )
        else:
            # 最终失败
            message.success = False
            self.message_queue.complete_message(message, False, error_msg)

            log_message_send(
                message.task_id,
                message.phone,
                message.port_name or 'N/A',
                'failed',
                error_msg
            )

            # 通知回调
            self._notify_callback('failed', message)

    def _notify_callback(self, event: str, message: SimulatedMessage):
        """通知回调函数"""
        for callback in self.send_callbacks:
            try:
                callback(event, message)
            except Exception as e:
                log_error(f"回调函数执行异常: {e}")

    def add_callback(self, callback: Callable):
        """添加回调函数"""
        if callable(callback):
            self.send_callbacks.append(callback)

    def remove_callback(self, callback: Callable):
        """移除回调函数"""
        if callback in self.send_callbacks:
            self.send_callbacks.remove(callback)

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        queue_stats = self.message_queue.get_stats()
        port_stats = self.port_simulator.get_port_statistics()

        return {
            'simulator_running': self.is_running,
            'worker_count': len([t for t in self.worker_threads if t.is_alive()]),
            'queue': queue_stats,
            'ports': port_stats,
            'allocation_strategy': self.port_allocation_strategy
        }

    def set_success_rate(self, rate: float):
        """设置全局成功率"""
        self.success_rate = max(0.0, min(1.0, rate))
        self.port_simulator.set_global_success_rate(self.success_rate)
        log_info(f"全局成功率设置为{self.success_rate:.2%}")

    def set_allocation_strategy(self, strategy: str):
        """设置端口分配策略"""
        if strategy in ['round_robin', 'random', 'load_balance']:
            self.port_allocation_strategy = strategy
            log_info(f"端口分配策略设置为: {strategy}")

    def clear_queue(self):
        """清空队列"""
        self.message_queue.clear()
        log_info("消息队列已清空")

    def get_queue_messages(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取队列中的消息（不移除）"""
        messages = []
        temp_items = []

        # 临时取出消息查看
        while len(messages) < limit and not self.message_queue.queue.empty():
            try:
                item = self.message_queue.queue.get_nowait()
                temp_items.append(item)
                _, message = item
                messages.append(message.to_dict())
            except queue.Empty:
                break

        # 放回队列
        for item in temp_items:
            try:
                self.message_queue.queue.put_nowait(item)
            except queue.Full:
                break

        return messages


# 全局短信模拟器实例
sms_simulator = SMSSimulator()

if __name__ == "__main__":
    # 测试代码
    print("=" * 50)
    print("短信发送模拟器测试")
    print("=" * 50)

    # 连接一些端口
    print("\n连接虚拟端口...")
    for i in range(1, 6):
        port_name = f"COM{i}"
        if port_simulator.connect_port(port_name):
            print(f"  {port_name} 连接成功")

    # 启动模拟器
    print("\n启动短信模拟器...")
    sms_simulator.start()

    # 发送测试消息
    print("\n添加测试消息到队列...")
    test_messages = [
        {'message_id': i, 'task_id': 1, 'phone': f'1380013800{i}',
         'content': f'测试短信{i}', 'priority': random.choice([1, 5, 10])}
        for i in range(10)
    ]

    result = sms_simulator.send_batch(test_messages)
    print(f"入队结果: {result}")

    # 等待处理
    print("\n等待消息处理...")
    time.sleep(5)

    # 获取统计
    stats = sms_simulator.get_statistics()
    print(f"\n统计信息:")
    print(f"  队列大小: {stats['queue']['queue_size']}")
    print(f"  处理总数: {stats['queue']['total_processed']}")
    print(f"  成功数: {stats['queue']['total_success']}")
    print(f"  失败数: {stats['queue']['total_failed']}")
    print(f"  成功率: {stats['queue']['success_rate']}%")

    # 停止模拟器
    print("\n停止模拟器...")
    sms_simulator.stop()