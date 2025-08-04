"""
猫池短信系统任务执行器 - tkinter版
Task executor for SMS Pool System - tkinter version
"""

import sys
import time
import threading
import queue
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable, Tuple
from enum import Enum
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from config.settings import settings
    from config.logging_config import get_logger, log_task_action, log_error, log_info
    from .utils import format_duration, generate_unique_id
except ImportError:
    # 简化处理
    class MockSettings:
        MAX_CONCURRENT_TASKS = 3
        TASK_PROGRESS_INTERVAL = 2
        DEFAULT_RETRY_COUNT = 3
        DEFAULT_TIMEOUT = 30

    settings = MockSettings()

    import logging
    def get_logger(name='core.task_executor'):
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    def log_task_action(task_id, task_name, action, details=None):
        logger = get_logger()
        message = f"[任务操作] ID={task_id} 名称={task_name} 操作={action}"
        if details:
            message += f" - {details}"
        logger.info(message)

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

    def generate_unique_id():
        import uuid
        return str(uuid.uuid4())

logger = get_logger('core.task_executor')


class TaskStatus(Enum):
    """任务状态枚举"""
    DRAFT = "draft"
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class TaskPriority(Enum):
    """任务优先级枚举"""
    LOW = 1
    NORMAL = 5
    HIGH = 8
    URGENT = 10


class TaskExecutionResult:
    """任务执行结果类"""

    def __init__(self, task_id: int, success: bool = False,
                 message: str = "", details: Dict[str, Any] = None):
        self.task_id = task_id
        self.success = success
        self.message = message
        self.details = details or {}
        self.execution_time = datetime.now()
        self.duration: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'task_id': self.task_id,
            'success': self.success,
            'message': self.message,
            'details': self.details,
            'execution_time': self.execution_time.isoformat(),
            'duration': self.duration
        }


class TaskRequest:
    """任务请求类"""

    def __init__(self, task_id: int, task_name: str, priority: int = TaskPriority.NORMAL.value,
                 retry_count: int = 0, max_retries: int = 3):
        self.task_id = task_id
        self.task_name = task_name
        self.priority = priority
        self.retry_count = retry_count
        self.max_retries = max_retries
        self.created_time = datetime.now()
        self.started_time: Optional[datetime] = None
        self.completed_time: Optional[datetime] = None
        self.execution_id = generate_unique_id()
        self.status = TaskStatus.PENDING
        self.error_message: Optional[str] = None

    def __lt__(self, other):
        """优先级比较（数字越大优先级越高）"""
        if self.priority != other.priority:
            return self.priority > other.priority
        # 相同优先级按创建时间排序
        return self.created_time < other.created_time

    def can_retry(self) -> bool:
        """是否可以重试"""
        return self.retry_count < self.max_retries

    def increment_retry(self):
        """增加重试次数"""
        self.retry_count += 1

    def get_wait_time(self) -> float:
        """获取等待时间（秒）"""
        if self.started_time:
            return 0.0
        return (datetime.now() - self.created_time).total_seconds()

    def get_execution_time(self) -> Optional[float]:
        """获取执行时间（秒）"""
        if not self.started_time:
            return None
        end_time = self.completed_time or datetime.now()
        return (end_time - self.started_time).total_seconds()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'task_id': self.task_id,
            'task_name': self.task_name,
            'priority': self.priority,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'execution_id': self.execution_id,
            'status': self.status.value,
            'created_time': self.created_time.isoformat(),
            'started_time': self.started_time.isoformat() if self.started_time else None,
            'completed_time': self.completed_time.isoformat() if self.completed_time else None,
            'wait_time': self.get_wait_time(),
            'execution_time': self.get_execution_time(),
            'error_message': self.error_message
        }


class TaskExecutor:
    """任务执行器类"""

    def __init__(self):
        """初始化任务执行器"""
        self._task_queue = queue.PriorityQueue()
        self._worker_threads: List[threading.Thread] = []
        self._running_tasks: Dict[int, TaskRequest] = {}
        self._completed_tasks: List[TaskExecutionResult] = []
        self._task_callbacks: List[Callable] = []
        self._lock = threading.Lock()
        self._is_running = False
        self._shutdown_event = threading.Event()

        # 配置参数
        self.max_concurrent_tasks = getattr(settings, 'MAX_CONCURRENT_TASKS', 3)
        self.worker_count = self.max_concurrent_tasks
        self.default_retry_count = getattr(settings, 'DEFAULT_RETRY_COUNT', 3)
        self.default_timeout = getattr(settings, 'DEFAULT_TIMEOUT', 30)
        self.progress_interval = getattr(settings, 'TASK_PROGRESS_INTERVAL', 2)

        # 统计信息
        self.total_executed = 0
        self.successful_executions = 0
        self.failed_executions = 0
        self.start_time: Optional[datetime] = None

    def initialize(self) -> bool:
        """初始化执行器"""
        try:
            log_info("任务执行器初始化开始")

            # 启动工作线程
            self._start_worker_threads()

            self.start_time = datetime.now()
            self._is_running = True

            log_info(f"任务执行器初始化完成，工作线程数: {self.worker_count}")
            return True

        except Exception as e:
            log_error("任务执行器初始化失败", error=e)
            return False

    def shutdown(self):
        """关闭执行器"""
        try:
            log_info("任务执行器开始关闭")

            # 设置关闭标志
            self._is_running = False
            self._shutdown_event.set()

            # 停止工作线程
            self._stop_worker_threads()

            # 清空队列
            while not self._task_queue.empty():
                try:
                    self._task_queue.get_nowait()
                except queue.Empty:
                    break

            # 清除回调
            self._task_callbacks.clear()

            # 清理数据
            self._running_tasks.clear()

            log_info("任务执行器关闭完成")

        except Exception as e:
            log_error("任务执行器关闭失败", error=e)

    def get_status(self) -> Dict[str, Any]:
        """获取执行器状态"""
        success_rate = 0.0
        if self.total_executed > 0:
            success_rate = round(self.successful_executions / self.total_executed * 100, 2)

        uptime = 0.0
        if self.start_time:
            uptime = (datetime.now() - self.start_time).total_seconds()

        return {
            'is_running': self._is_running,
            'worker_count': len([t for t in self._worker_threads if t.is_alive()]),
            'max_concurrent': self.max_concurrent_tasks,
            'queue_size': self._task_queue.qsize(),
            'running_tasks': len(self._running_tasks),
            'total_executed': self.total_executed,
            'successful_executions': self.successful_executions,
            'failed_executions': self.failed_executions,
            'success_rate': success_rate,
            'uptime': format_duration(uptime),
            'message': '任务执行器正常运行' if self._is_running else '任务执行器未运行'
        }

    def submit_task(self, task_id: int, task_name: str, priority: int = TaskPriority.NORMAL.value,
                   max_retries: int = None) -> Dict[str, Any]:
        """提交任务"""
        try:
            if not self._is_running:
                return {
                    'success': False,
                    'message': '任务执行器未运行',
                    'error_code': 'EXECUTOR_NOT_RUNNING'
                }

            # 检查任务是否已存在
            if task_id in self._running_tasks:
                return {
                    'success': False,
                    'message': f'任务{task_id}已在执行中',
                    'error_code': 'TASK_ALREADY_RUNNING'
                }

            # 创建任务请求
            if max_retries is None:
                max_retries = self.default_retry_count

            task_request = TaskRequest(
                task_id=task_id,
                task_name=task_name,
                priority=priority,
                max_retries=max_retries
            )

            # 添加到队列
            self._task_queue.put((task_request.priority, time.time(), task_request))

            log_task_action(task_id, task_name, "提交任务", f"优先级={priority}")

            return {
                'success': True,
                'message': '任务提交成功',
                'task_id': task_id,
                'execution_id': task_request.execution_id,
                'queue_position': self._task_queue.qsize()
            }

        except Exception as e:
            log_error(f"提交任务{task_id}异常", error=e)
            return {
                'success': False,
                'message': f'提交异常: {str(e)}',
                'error_code': 'SUBMIT_ERROR'
            }

    def cancel_task(self, task_id: int) -> Dict[str, Any]:
        """取消任务"""
        try:
            with self._lock:
                # 检查是否在运行中
                if task_id in self._running_tasks:
                    task_request = self._running_tasks[task_id]
                    task_request.status = TaskStatus.CANCELLED

                    log_task_action(task_id, task_request.task_name, "取消任务")

                    return {
                        'success': True,
                        'message': f'任务{task_id}已标记为取消',
                        'task_id': task_id
                    }

                # 尝试从队列中移除（注意：这里无法直接从PriorityQueue中移除特定项）
                return {
                    'success': False,
                    'message': f'任务{task_id}不在运行队列中',
                    'error_code': 'TASK_NOT_FOUND'
                }

        except Exception as e:
            log_error(f"取消任务{task_id}异常", error=e)
            return {
                'success': False,
                'message': f'取消异常: {str(e)}',
                'error_code': 'CANCEL_ERROR'
            }

    def pause_all_tasks(self) -> Dict[str, Any]:
        """暂停所有任务"""
        try:
            paused_count = 0
            with self._lock:
                for task_request in self._running_tasks.values():
                    if task_request.status == TaskStatus.RUNNING:
                        task_request.status = TaskStatus.PAUSED
                        paused_count += 1

            log_info(f"暂停了{paused_count}个正在运行的任务")

            return {
                'success': True,
                'message': f'暂停了{paused_count}个任务',
                'paused_count': paused_count
            }

        except Exception as e:
            log_error("暂停所有任务异常", error=e)
            return {
                'success': False,
                'message': f'暂停异常: {str(e)}',
                'error_code': 'PAUSE_ERROR'
            }

    def resume_all_tasks(self) -> Dict[str, Any]:
        """恢复所有任务"""
        try:
            resumed_count = 0
            with self._lock:
                for task_request in self._running_tasks.values():
                    if task_request.status == TaskStatus.PAUSED:
                        task_request.status = TaskStatus.RUNNING
                        resumed_count += 1

            log_info(f"恢复了{resumed_count}个暂停的任务")

            return {
                'success': True,
                'message': f'恢复了{resumed_count}个任务',
                'resumed_count': resumed_count
            }

        except Exception as e:
            log_error("恢复所有任务异常", error=e)
            return {
                'success': False,
                'message': f'恢复异常: {str(e)}',
                'error_code': 'RESUME_ERROR'
            }

    def get_running_tasks(self) -> List[Dict[str, Any]]:
        """获取正在运行的任务"""
        try:
            with self._lock:
                return [task.to_dict() for task in self._running_tasks.values()]
        except Exception as e:
            log_error("获取运行任务列表异常", error=e)
            return []

    def get_queue_info(self) -> Dict[str, Any]:
        """获取队列信息"""
        return {
            'queue_size': self._task_queue.qsize(),
            'is_empty': self._task_queue.empty(),
            'running_tasks': len(self._running_tasks),
            'max_concurrent': self.max_concurrent_tasks,
            'available_slots': max(0, self.max_concurrent_tasks - len(self._running_tasks))
        }

    def get_task_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取任务历史"""
        try:
            # 返回最近的任务执行结果
            recent_tasks = self._completed_tasks[-limit:] if limit > 0 else self._completed_tasks
            return [task.to_dict() for task in recent_tasks]
        except Exception as e:
            log_error("获取任务历史异常", error=e)
            return []

    def clear_completed_tasks(self) -> Dict[str, Any]:
        """清除已完成的任务历史"""
        try:
            cleared_count = len(self._completed_tasks)
            self._completed_tasks.clear()

            log_info(f"清除了{cleared_count}条任务历史记录")

            return {
                'success': True,
                'message': f'清除了{cleared_count}条历史记录',
                'cleared_count': cleared_count
            }

        except Exception as e:
            log_error("清除任务历史异常", error=e)
            return {
                'success': False,
                'message': f'清除异常: {str(e)}',
                'error_code': 'CLEAR_ERROR'
            }

    def add_task_callback(self, callback: Callable[[str, TaskRequest, TaskExecutionResult], None]):
        """添加任务状态变化回调"""
        if callable(callback):
            self._task_callbacks.append(callback)
            log_info(f"添加任务回调函数，当前回调数量: {len(self._task_callbacks)}")

    def remove_task_callback(self, callback: Callable[[str, TaskRequest, TaskExecutionResult], None]):
        """移除任务状态变化回调"""
        if callback in self._task_callbacks:
            self._task_callbacks.remove(callback)
            log_info(f"移除任务回调函数，当前回调数量: {len(self._task_callbacks)}")

    def get_statistics(self) -> Dict[str, Any]:
        """获取执行统计"""
        try:
            uptime = 0.0
            throughput = 0.0

            if self.start_time:
                uptime = (datetime.now() - self.start_time).total_seconds()
                if uptime > 0:
                    throughput = self.total_executed / uptime

            success_rate = 0.0
            if self.total_executed > 0:
                success_rate = round(self.successful_executions / self.total_executed * 100, 2)

            return {
                'uptime_seconds': uptime,
                'uptime_formatted': format_duration(uptime),
                'total_executed': self.total_executed,
                'successful_executions': self.successful_executions,
                'failed_executions': self.failed_executions,
                'success_rate': success_rate,
                'throughput_per_second': round(throughput, 3),
                'current_queue_size': self._task_queue.qsize(),
                'current_running': len(self._running_tasks),
                'max_concurrent': self.max_concurrent_tasks
            }

        except Exception as e:
            log_error("获取执行统计异常", error=e)
            return {}

    def _start_worker_threads(self):
        """启动工作线程"""
        try:
            self._worker_threads.clear()

            for i in range(self.worker_count):
                worker_thread = threading.Thread(
                    target=self._worker_loop,
                    name=f"TaskExecutor-Worker-{i}",
                    daemon=True
                )
                worker_thread.start()
                self._worker_threads.append(worker_thread)

            log_info(f"启动{self.worker_count}个任务执行工作线程")

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
            log_info("所有任务执行工作线程已停止")

        except Exception as e:
            log_error("停止工作线程失败", error=e)

    def _worker_loop(self):
        """工作线程主循环"""
        thread_name = threading.current_thread().name
        log_info(f"任务执行工作线程 {thread_name} 启动")

        while self._is_running and not self._shutdown_event.is_set():
            try:
                # 从队列获取任务
                try:
                    priority, timestamp, task_request = self._task_queue.get(timeout=1)
                except queue.Empty:
                    continue

                # 检查并发限制
                if len(self._running_tasks) >= self.max_concurrent_tasks:
                    # 重新放回队列
                    self._task_queue.put((priority, timestamp, task_request))
                    time.sleep(0.1)
                    continue

                # 执行任务
                self._execute_task(task_request)

                # 标记队列任务完成
                self._task_queue.task_done()

            except Exception as e:
                log_error(f"工作线程 {thread_name} 处理异常", error=e)
                time.sleep(1)

        log_info(f"任务执行工作线程 {thread_name} 停止")

    def _execute_task(self, task_request: TaskRequest):
        """执行单个任务"""
        execution_result = None

        try:
            # 标记任务开始
            task_request.status = TaskStatus.RUNNING
            task_request.started_time = datetime.now()

            with self._lock:
                self._running_tasks[task_request.task_id] = task_request

            # 通知任务开始
            self._notify_task_change('start', task_request)

            log_task_action(
                task_request.task_id,
                task_request.task_name,
                "开始执行",
                f"执行ID={task_request.execution_id}"
            )

            # 实际的任务执行逻辑
            execution_result = self._perform_task_execution(task_request)

            # 更新统计
            self.total_executed += 1
            if execution_result.success:
                self.successful_executions += 1
                task_request.status = TaskStatus.COMPLETED
            else:
                self.failed_executions += 1
                task_request.status = TaskStatus.FAILED
                task_request.error_message = execution_result.message

        except Exception as e:
            # 处理执行异常
            self.total_executed += 1
            self.failed_executions += 1
            task_request.status = TaskStatus.FAILED
            task_request.error_message = str(e)

            execution_result = TaskExecutionResult(
                task_id=task_request.task_id,
                success=False,
                message=f'执行异常: {str(e)}',
                details={'exception': str(e)}
            )

            log_error(f"执行任务{task_request.task_id}异常", error=e)

        finally:
            # 任务完成处理
            task_request.completed_time = datetime.now()

            if execution_result:
                execution_result.duration = task_request.get_execution_time()

            # 从运行列表中移除
            with self._lock:
                self._running_tasks.pop(task_request.task_id, None)

            # 保存到历史记录
            if execution_result:
                self._completed_tasks.append(execution_result)

                # 限制历史记录数量
                if len(self._completed_tasks) > 1000:
                    self._completed_tasks = self._completed_tasks[-500:]

            # 检查是否需要重试
            if (not execution_result.success and
                task_request.can_retry() and
                task_request.status != TaskStatus.CANCELLED):

                self._handle_task_retry(task_request)
            else:
                # 通知任务完成
                self._notify_task_change('complete', task_request, execution_result)

                log_task_action(
                    task_request.task_id,
                    task_request.task_name,
                    "执行完成",
                    f"结果={'成功' if execution_result.success else '失败'}, 耗时={format_duration(execution_result.duration or 0)}"
                )

    def _perform_task_execution(self, task_request: TaskRequest) -> TaskExecutionResult:
        """执行具体的任务逻辑"""
        try:
            # 检查任务是否被取消或暂停
            if task_request.status in [TaskStatus.CANCELLED, TaskStatus.PAUSED]:
                return TaskExecutionResult(
                    task_id=task_request.task_id,
                    success=False,
                    message=f'任务被{task_request.status.value}'
                )

            # 这里是实际的任务执行逻辑
            # 在实际应用中，这里会调用具体的任务处理函数
            # 例如：发送短信、处理文件等

            # 模拟任务执行时间
            time.sleep(0.1)

            # 模拟任务执行结果
            # 在实际应用中，这里应该调用相应的服务来执行任务
            import random
            success = random.random() > 0.1  # 90%成功率

            if success:
                return TaskExecutionResult(
                    task_id=task_request.task_id,
                    success=True,
                    message='任务执行成功',
                    details={
                        'execution_id': task_request.execution_id,
                        'retry_count': task_request.retry_count
                    }
                )
            else:
                return TaskExecutionResult(
                    task_id=task_request.task_id,
                    success=False,
                    message='任务执行失败',
                    details={
                        'execution_id': task_request.execution_id,
                        'retry_count': task_request.retry_count,
                        'error_type': 'simulation_failure'
                    }
                )

        except Exception as e:
            return TaskExecutionResult(
                task_id=task_request.task_id,
                success=False,
                message=f'任务执行异常: {str(e)}',
                details={'exception': str(e)}
            )

    def _handle_task_retry(self, task_request: TaskRequest):
        """处理任务重试"""
        try:
            task_request.increment_retry()
            task_request.status = TaskStatus.PENDING

            # 计算重试延迟（指数退避）
            retry_delay = min(60, 2 ** task_request.retry_count)

            # 重新提交到队列（延迟执行）
            def delayed_resubmit():
                time.sleep(retry_delay)
                if self._is_running:
                    self._task_queue.put((
                        task_request.priority - 1,  # 降低优先级
                        time.time(),
                        task_request
                    ))

            retry_thread = threading.Thread(target=delayed_resubmit, daemon=True)
            retry_thread.start()

            log_task_action(
                task_request.task_id,
                task_request.task_name,
                "安排重试",
                f"第{task_request.retry_count}次重试，延迟{retry_delay}秒"
            )

        except Exception as e:
            log_error(f"处理任务{task_request.task_id}重试异常", error=e)

    def _notify_task_change(self, event: str, task_request: TaskRequest,
                           execution_result: TaskExecutionResult = None):
        """通知任务状态变化"""
        try:
            for callback in self._task_callbacks:
                try:
                    callback(event, task_request, execution_result)
                except Exception as e:
                    log_error("任务状态变化回调执行失败", error=e)
        except Exception as e:
            log_error("通知任务状态变化失败", error=e)

    def set_max_concurrent(self, max_concurrent: int):
        """设置最大并发数"""
        try:
            if max_concurrent < 1:
                max_concurrent = 1
            elif max_concurrent > 20:
                max_concurrent = 20

            old_max = self.max_concurrent_tasks
            self.max_concurrent_tasks = max_concurrent

            # 如果需要调整工作线程数
            if max_concurrent != self.worker_count:
                log_info(f"最大并发数已更新: {old_max} -> {max_concurrent}")
                # 注意：这里不重启线程，只是调整并发限制

        except Exception as e:
            log_error("设置最大并发数失败", error=e)

    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        try:
            current_time = datetime.now()

            # 计算平均等待时间
            total_wait_time = 0.0
            wait_count = 0

            with self._lock:
                for task in self._running_tasks.values():
                    if task.started_time:
                        wait_time = (task.started_time - task.created_time).total_seconds()
                        total_wait_time += wait_time
                        wait_count += 1

            avg_wait_time = total_wait_time / max(wait_count, 1)

            # 计算平均执行时间
            recent_completed = self._completed_tasks[-100:] if len(self._completed_tasks) > 100 else self._completed_tasks
            total_execution_time = sum(task.duration or 0 for task in recent_completed)
            avg_execution_time = total_execution_time / max(len(recent_completed), 1)

            return {
                'avg_wait_time': round(avg_wait_time, 3),
                'avg_execution_time': round(avg_execution_time, 3),
                'queue_efficiency': round((1 - avg_wait_time / max(avg_execution_time, 1)) * 100, 2),
                'worker_utilization': round(len(self._running_tasks) / self.max_concurrent_tasks * 100, 2),
                'recent_success_rate': self._calculate_recent_success_rate(),
                'tasks_per_minute': self._calculate_throughput_per_minute()
            }

        except Exception as e:
            log_error("获取性能指标失败", error=e)
            return {}

    def _calculate_recent_success_rate(self) -> float:
        """计算最近的成功率"""
        try:
            recent_tasks = self._completed_tasks[-50:] if len(self._completed_tasks) > 50 else self._completed_tasks
            if not recent_tasks:
                return 0.0

            successful = sum(1 for task in recent_tasks if task.success)
            return round(successful / len(recent_tasks) * 100, 2)

        except Exception:
            return 0.0

    def _calculate_throughput_per_minute(self) -> float:
        """计算每分钟处理量"""
        try:
            if not self.start_time:
                return 0.0

            uptime_minutes = (datetime.now() - self.start_time).total_seconds() / 60
            if uptime_minutes == 0:
                return 0.0

            return round(self.total_executed / uptime_minutes, 2)

        except Exception:
            return 0.0


# 全局任务执行器实例
task_executor = TaskExecutor()