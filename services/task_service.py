"""
猫池短信系统任务管理服务 - tkinter版
Task management service for SMS Pool System - tkinter version
"""

import sys
import threading
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Callable
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from models.task import Task, TaskStatus, TaskMode, task_manager
    from models.message import TaskMessage, MessageStatus, task_message_manager
    from config.settings import settings
    from config.logging_config import get_logger, log_task_action, log_error, log_info, log_timer_action
except ImportError:
    # 简化处理
    class MockTask:
        def __init__(self, **kwargs):
            self.id = 1
            self.title = kwargs.get('title', '')
            self.status = 'draft'

        def save(self):
            return True

    class MockTaskManager:
        def create_task(self, **kwargs):
            return MockTask(**kwargs)

    class MockTaskMessage:
        pass

    class MockTaskMessageManager:
        def create_messages_from_file(self, task_id, file_path, message_content):
            return True

    Task = MockTask
    task_manager = MockTaskManager()
    TaskMessage = MockTaskMessage
    task_message_manager = MockTaskMessageManager()

    class TaskStatus:
        DRAFT = "draft"
        PENDING = "pending"
        RUNNING = "running"
        PAUSED = "paused"
        COMPLETED = "completed"
        CANCELLED = "cancelled"
        FAILED = "failed"

    class TaskMode:
        SMS = "sms"
        MMS = "mms"

    class MessageStatus:
        PENDING = "pending"
        SUCCESS = "success"
        FAILED = "failed"

    class MockSettings:
        TASK_PROGRESS_INTERVAL = 2
        MAX_CONCURRENT_TASKS = 3

    settings = MockSettings()

    import logging
    def get_logger(name='services.task'):
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

    def log_timer_action(timer_name, action, interval=None):
        logger = get_logger()
        message = f"[定时器] {timer_name} {action}"
        if interval:
            message += f" 间隔={interval}秒"
        logger.debug(message)

logger = get_logger('services.task')


class TaskService:
    """任务管理服务类"""

    def __init__(self):
        """初始化任务服务"""
        self.task_manager = task_manager
        self.message_manager = task_message_manager
        self._lock = threading.Lock()
        self._progress_timer: Optional[threading.Timer] = None
        self._task_change_callbacks: list = []
        self._running_tasks: Dict[int, threading.Thread] = {}
        self.is_initialized = False

        # 配置参数
        self.progress_interval = getattr(settings, 'TASK_PROGRESS_INTERVAL', 2)  # 进度更新间隔
        self.max_concurrent_tasks = getattr(settings, 'MAX_CONCURRENT_TASKS', 3)  # 最大并发任务数

    def initialize(self) -> bool:
        """初始化服务"""
        try:
            log_info("任务管理服务初始化开始")

            # 启动进度监控
            self._start_progress_monitoring()

            # 恢复运行中的任务
            self._recover_running_tasks()

            self.is_initialized = True
            log_info(f"任务管理服务初始化完成，最大并发: {self.max_concurrent_tasks}")
            return True

        except Exception as e:
            log_error("任务管理服务初始化失败", error=e)
            return False

    def shutdown(self):
        """关闭服务"""
        try:
            log_info("任务管理服务开始关闭")

            # 停止进度监控
            self._stop_progress_monitoring()

            # 暂停所有运行中的任务
            self._pause_all_running_tasks()

            # 清除回调
            self._task_change_callbacks.clear()

            self.is_initialized = False
            log_info("任务管理服务关闭完成")

        except Exception as e:
            log_error("任务管理服务关闭失败", error=e)

    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        return {
            'running': self.is_initialized,
            'progress_interval': self.progress_interval,
            'max_concurrent_tasks': self.max_concurrent_tasks,
            'running_tasks_count': len(self._running_tasks),
            'running_task_ids': list(self._running_tasks.keys()),
            'monitoring_active': self._progress_timer is not None,
            'message': '任务管理服务正常运行' if self.is_initialized else '任务管理服务未初始化'
        }

    def create_task(self, title: str, mode: str, message_content: str,
                   operator_id: int, phone_numbers: List[str] = None,
                   phone_file: str = None, **kwargs) -> Dict[str, Any]:
        """创建任务"""
        try:
            with self._lock:
                # 创建任务
                task = self.task_manager.create_task(
                    title=title,
                    mode=mode,
                    message_content=message_content,
                    operator_id=operator_id,
                    **kwargs
                )

                if not task:
                    return {
                        'success': False,
                        'message': '任务创建失败',
                        'error_code': 'CREATE_FAILED'
                    }

                # 处理号码
                if phone_file:
                    # 从文件导入号码
                    if not self.message_manager.create_messages_from_file(
                        task_id=task.id,
                        file_path=phone_file,
                        message_content=message_content
                    ):
                        return {
                            'success': False,
                            'message': '从文件导入号码失败',
                            'error_code': 'IMPORT_FAILED'
                        }
                elif phone_numbers:
                    # 批量创建消息
                    if not TaskMessage.bulk_create_from_phones(
                        task_id=task.id,
                        phone_numbers=phone_numbers,
                        message_content=message_content
                    ):
                        return {
                            'success': False,
                            'message': '批量创建消息失败',
                            'error_code': 'CREATE_MESSAGES_FAILED'
                        }

                # 更新任务统计
                task.total_count = len(phone_numbers) if phone_numbers else 0
                task.pending_count = task.total_count
                task.save()

                # 通知任务变化
                self._notify_task_change('create', task)

                log_task_action(task.id, task.title, "创建任务", f"总数: {task.total_count}")

                return {
                    'success': True,
                    'message': '任务创建成功',
                    'task_id': task.id,
                    'task_info': task.get_summary()
                }

        except Exception as e:
            log_error("创建任务异常", error=e)
            return {
                'success': False,
                'message': f'创建异常: {str(e)}',
                'error_code': 'SYSTEM_ERROR'
            }

    def start_task(self, task_id: int) -> Dict[str, Any]:
        """启动任务"""
        try:
            # 检查并发限制
            if len(self._running_tasks) >= self.max_concurrent_tasks:
                return {
                    'success': False,
                    'message': f'已达到最大并发任务数限制({self.max_concurrent_tasks})',
                    'error_code': 'MAX_CONCURRENT_REACHED'
                }

            # 检查任务是否已在运行
            if task_id in self._running_tasks:
                return {
                    'success': False,
                    'message': '任务已在运行中',
                    'error_code': 'ALREADY_RUNNING'
                }

            # 启动任务
            if self.task_manager.start_task(task_id):
                # 创建任务执行线程
                task_thread = threading.Thread(
                    target=self._execute_task,
                    args=(task_id,),
                    daemon=True
                )
                task_thread.start()

                self._running_tasks[task_id] = task_thread

                # 获取任务信息
                task = Task.find_by_id(task_id)
                if task:
                    self._notify_task_change('start', task)
                    log_task_action(task_id, task.title, "启动任务")

                return {
                    'success': True,
                    'message': '任务启动成功',
                    'task_id': task_id
                }
            else:
                return {
                    'success': False,
                    'message': '任务启动失败',
                    'error_code': 'START_FAILED'
                }

        except Exception as e:
            log_error(f"启动任务{task_id}异常", error=e)
            return {
                'success': False,
                'message': f'启动异常: {str(e)}',
                'error_code': 'SYSTEM_ERROR'
            }

    def pause_task(self, task_id: int) -> Dict[str, Any]:
        """暂停任务"""
    def pause_task(self, task_id: int) -> Dict[str, Any]:
        """暂停任务"""
        try:
            if self.task_manager.pause_task(task_id):
                # 移除运行中的任务线程
                if task_id in self._running_tasks:
                    # 任务线程会自动检测暂停状态并停止
                    del self._running_tasks[task_id]

                # 获取任务信息
                task = Task.find_by_id(task_id)
                if task:
                    self._notify_task_change('pause', task)
                    log_task_action(task_id, task.title, "暂停任务")

                return {
                    'success': True,
                    'message': '任务暂停成功',
                    'task_id': task_id
                }
            else:
                return {
                    'success': False,
                    'message': '任务暂停失败',
                    'error_code': 'PAUSE_FAILED'
                }

        except Exception as e:
            log_error(f"暂停任务{task_id}异常", error=e)
            return {
                'success': False,
                'message': f'暂停异常: {str(e)}',
                'error_code': 'SYSTEM_ERROR'
            }

    def resume_task(self, task_id: int) -> Dict[str, Any]:
        """恢复任务"""
        try:
            # 检查并发限制
            if len(self._running_tasks) >= self.max_concurrent_tasks:
                return {
                    'success': False,
                    'message': f'已达到最大并发任务数限制({self.max_concurrent_tasks})',
                    'error_code': 'MAX_CONCURRENT_REACHED'
                }

            if self.task_manager.resume_task(task_id):
                # 创建任务执行线程
                task_thread = threading.Thread(
                    target=self._execute_task,
                    args=(task_id,),
                    daemon=True
                )
                task_thread.start()

                self._running_tasks[task_id] = task_thread

                # 获取任务信息
                task = Task.find_by_id(task_id)
                if task:
                    self._notify_task_change('resume', task)
                    log_task_action(task_id, task.title, "恢复任务")

                return {
                    'success': True,
                    'message': '任务恢复成功',
                    'task_id': task_id
                }
            else:
                return {
                    'success': False,
                    'message': '任务恢复失败',
                    'error_code': 'RESUME_FAILED'
                }

        except Exception as e:
            log_error(f"恢复任务{task_id}异常", error=e)
            return {
                'success': False,
                'message': f'恢复异常: {str(e)}',
                'error_code': 'SYSTEM_ERROR'
            }

    def cancel_task(self, task_id: int) -> Dict[str, Any]:
        """取消任务"""
        try:
            if self.task_manager.cancel_task(task_id):
                # 移除运行中的任务线程
                if task_id in self._running_tasks:
                    del self._running_tasks[task_id]

                # 取消待发送的消息
                cancelled_count = self.message_manager.cancel_pending_messages(task_id)

                # 获取任务信息
                task = Task.find_by_id(task_id)
                if task:
                    self._notify_task_change('cancel', task)
                    log_task_action(task_id, task.title, "取消任务", f"取消{cancelled_count}条待发送消息")

                return {
                    'success': True,
                    'message': f'任务取消成功，取消了{cancelled_count}条待发送消息',
                    'task_id': task_id,
                    'cancelled_messages': cancelled_count
                }
            else:
                return {
                    'success': False,
                    'message': '任务取消失败',
                    'error_code': 'CANCEL_FAILED'
                }

        except Exception as e:
            log_error(f"取消任务{task_id}异常", error=e)
            return {
                'success': False,
                'message': f'取消异常: {str(e)}',
                'error_code': 'SYSTEM_ERROR'
            }

    def delete_task(self, task_id: int, force: bool = False) -> Dict[str, Any]:
        """删除任务"""
        try:
            # 如果任务正在运行，先取消
            if task_id in self._running_tasks:
                self.cancel_task(task_id)

            # 获取任务信息（删除前）
            task = Task.find_by_id(task_id)
            task_title = task.title if task else f"任务{task_id}"

            if self.task_manager.delete_task(task_id, force):
                if task:
                    self._notify_task_change('delete', task)
                    log_task_action(task_id, task_title, "删除任务")

                return {
                    'success': True,
                    'message': '任务删除成功',
                    'task_id': task_id
                }
            else:
                return {
                    'success': False,
                    'message': '任务删除失败',
                    'error_code': 'DELETE_FAILED'
                }

        except Exception as e:
            log_error(f"删除任务{task_id}异常", error=e)
            return {
                'success': False,
                'message': f'删除异常: {str(e)}',
                'error_code': 'SYSTEM_ERROR'
            }

    def retry_failed_messages(self, task_id: int) -> Dict[str, Any]:
        """重试失败的消息"""
        try:
            retry_count = self.message_manager.retry_failed_messages(task_id)

            # 获取任务信息
            task = Task.find_by_id(task_id)
            if task:
                log_task_action(task_id, task.title, "重试失败消息", f"重试{retry_count}条消息")

            return {
                'success': True,
                'message': f'成功重试{retry_count}条失败消息',
                'task_id': task_id,
                'retry_count': retry_count
            }

        except Exception as e:
            log_error(f"重试任务{task_id}失败消息异常", error=e)
            return {
                'success': False,
                'message': f'重试异常: {str(e)}',
                'error_code': 'SYSTEM_ERROR'
            }

    def get_task_info(self, task_id: int) -> Optional[Dict[str, Any]]:
        """获取任务信息"""
        try:
            task = Task.find_by_id(task_id)
            if task:
                return task.get_summary()
            return None
        except Exception as e:
            log_error(f"获取任务{task_id}信息异常", error=e)
            return None

    def get_user_tasks(self, operator_id: int, status: str = None,
                      page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """获取用户任务列表"""
        try:
            result = self.task_manager.get_user_tasks(operator_id, status, page, page_size)

            # 转换为摘要格式
            tasks_summary = []
            for task in result['tasks']:
                summary = task.get_summary()
                # 添加运行状态
                summary['is_running'] = task.id in self._running_tasks
                tasks_summary.append(summary)

            return {
                'success': True,
                'tasks': tasks_summary,
                'total_count': result['total_count'],
                'page': result['page'],
                'page_size': result['page_size'],
                'total_pages': result['total_pages']
            }

        except Exception as e:
            log_error(f"获取用户{operator_id}任务列表异常", error=e)
            return {
                'success': False,
                'tasks': [],
                'total_count': 0,
                'page': page,
                'page_size': page_size,
                'total_pages': 0,
                'error': str(e)
            }

    def get_task_messages(self, task_id: int, status: str = None,
                         page: int = 1, page_size: int = 50) -> Dict[str, Any]:
        """获取任务消息列表"""
        try:
            result = self.message_manager.get_task_messages(task_id, status, page, page_size)

            # 转换为摘要格式
            messages_summary = []
            for message in result['messages']:
                messages_summary.append(message.get_summary())

            return {
                'success': True,
                'messages': messages_summary,
                'total_count': result['total_count'],
                'page': result['page'],
                'page_size': result['page_size'],
                'total_pages': result['total_pages']
            }

        except Exception as e:
            log_error(f"获取任务{task_id}消息列表异常", error=e)
            return {
                'success': False,
                'messages': [],
                'total_count': 0,
                'page': page,
                'page_size': page_size,
                'total_pages': 0,
                'error': str(e)
            }

    def export_task_messages(self, task_id: int, status: str = None,
                           file_format: str = 'xlsx') -> Dict[str, Any]:
        """导出任务消息"""
        try:
            file_path = self.message_manager.export_messages(task_id, status, file_format)

            if file_path:
                # 获取任务信息
                task = Task.find_by_id(task_id)
                task_title = task.title if task else f"任务{task_id}"

                log_task_action(task_id, task_title, "导出消息", f"格式: {file_format}")

                return {
                    'success': True,
                    'message': '消息导出成功',
                    'file_path': file_path,
                    'task_id': task_id,
                    'format': file_format
                }
            else:
                return {
                    'success': False,
                    'message': '没有可导出的消息或导出失败',
                    'error_code': 'EXPORT_FAILED'
                }

        except Exception as e:
            log_error(f"导出任务{task_id}消息异常", error=e)
            return {
                'success': False,
                'message': f'导出异常: {str(e)}',
                'error_code': 'SYSTEM_ERROR'
            }

    def get_task_statistics(self, operator_id: int = None, start_date: datetime = None,
                           end_date: datetime = None) -> Dict[str, Any]:
        """获取任务统计"""
        try:
            return Task.get_task_statistics(operator_id, start_date, end_date)
        except Exception as e:
            log_error("获取任务统计异常", error=e)
            return {}

    def test_task(self, task_id: int, test_phone: str, test_port: str = None) -> Dict[str, Any]:
        """测试任务"""
        try:
            task = Task.find_by_id(task_id)
            if not task:
                return {
                    'success': False,
                    'message': '任务不存在',
                    'error_code': 'TASK_NOT_FOUND'
                }

            # 这里需要调用消息发送服务进行测试
            # 暂时返回模拟结果
            log_task_action(task_id, task.title, "测试任务", f"测试号码: {test_phone}")

            return {
                'success': True,
                'message': f'向{test_phone}发送测试消息成功',
                'test_phone': test_phone,
                'test_port': test_port,
                'task_id': task_id
            }

        except Exception as e:
            log_error(f"测试任务{task_id}异常", error=e)
            return {
                'success': False,
                'message': f'测试异常: {str(e)}',
                'error_code': 'SYSTEM_ERROR'
            }

    def add_task_change_callback(self, callback: Callable[[str, Task], None]):
        """添加任务变化回调函数"""
        try:
            if callable(callback):
                self._task_change_callbacks.append(callback)
                log_info(f"添加任务变化回调函数，当前回调数量: {len(self._task_change_callbacks)}")
        except Exception as e:
            log_error("添加任务变化回调失败", error=e)

    def remove_task_change_callback(self, callback: Callable[[str, Task], None]):
        """移除任务变化回调函数"""
        try:
            if callback in self._task_change_callbacks:
                self._task_change_callbacks.remove(callback)
                log_info(f"移除任务变化回调函数，当前回调数量: {len(self._task_change_callbacks)}")
        except Exception as e:
            log_error("移除任务变化回调失败", error=e)

    def set_progress_interval(self, interval_seconds: int):
        """设置进度更新间隔"""
        try:
            if interval_seconds < 1:  # 最小1秒
                interval_seconds = 1
            elif interval_seconds > 60:  # 最大1分钟
                interval_seconds = 60

            old_interval = self.progress_interval
            self.progress_interval = interval_seconds

            # 重启监控
            if self.is_initialized:
                self._stop_progress_monitoring()
                self._start_progress_monitoring()

            log_info(f"任务进度更新间隔已更新: {old_interval}秒 -> {interval_seconds}秒")

        except Exception as e:
            log_error("设置进度更新间隔失败", error=e)

    def _execute_task(self, task_id: int):
        """执行任务（在独立线程中运行）"""
        try:
            task = Task.find_by_id(task_id)
            if not task:
                log_error(f"任务{task_id}不存在，无法执行")
                return

            log_task_action(task_id, task.title, "开始执行")

            # 获取待发送的消息
            pending_messages = TaskMessage.find_pending_messages(task_id)

            for message in pending_messages:
                # 检查任务是否被暂停或取消
                current_task = Task.find_by_id(task_id)
                if not current_task or not current_task.is_running():
                    log_task_action(task_id, task.title, "任务已暂停或取消，停止执行")
                    break

                # 这里需要调用消息发送服务发送消息
                # 暂时模拟发送过程
                time.sleep(0.1)  # 模拟发送延迟

                # 模拟发送结果
                import random
                if random.random() > 0.1:  # 90%成功率
                    message.mark_as_success()
                    task.update_progress(success_delta=1)
                else:
                    message.mark_as_failed("模拟发送失败")
                    task.update_progress(failed_delta=1)

            # 任务执行完成，清理线程
            if task_id in self._running_tasks:
                del self._running_tasks[task_id]

            # 检查任务是否完成
            final_task = Task.find_by_id(task_id)
            if final_task and final_task.pending_count == 0:
                if final_task.failed_count == 0:
                    final_task.update_status(TaskStatus.COMPLETED.value)
                    log_task_action(task_id, final_task.title, "任务完成", "全部成功")
                else:
                    final_task.update_status(TaskStatus.COMPLETED.value)
                    log_task_action(task_id, final_task.title, "任务完成", f"成功{final_task.success_count}，失败{final_task.failed_count}")

                self._notify_task_change('complete', final_task)

        except Exception as e:
            log_error(f"执行任务{task_id}异常", error=e)
            # 标记任务为失败状态
            task = Task.find_by_id(task_id)
            if task:
                task.update_status(TaskStatus.FAILED.value)
                task.add_error('execution_error', str(e))
                task.save()

            # 清理线程
            if task_id in self._running_tasks:
                del self._running_tasks[task_id]

    def _start_progress_monitoring(self):
        """启动进度监控"""
        try:
            if self._progress_timer:
                self._progress_timer.cancel()

            self._progress_timer = threading.Timer(self.progress_interval, self._progress_check_callback)
            self._progress_timer.daemon = True
            self._progress_timer.start()

            log_timer_action("任务进度监控", "启动", self.progress_interval)

        except Exception as e:
            log_error("启动进度监控失败", error=e)

    def _stop_progress_monitoring(self):
        """停止进度监控"""
        try:
            if self._progress_timer:
                self._progress_timer.cancel()
                self._progress_timer = None
                log_timer_action("任务进度监控", "停止")

        except Exception as e:
            log_error("停止进度监控失败", error=e)

    def _progress_check_callback(self):
        """进度检查回调"""
        try:
            if self.is_initialized:
                # 检查运行中的任务
                for task_id in list(self._running_tasks.keys()):
                    task = Task.find_by_id(task_id)
                    if task:
                        # 通知进度变化
                        self._notify_task_change('progress', task)
                    else:
                        # 任务不存在，清理线程
                        if task_id in self._running_tasks:
                            del self._running_tasks[task_id]

            # 重新启动定时器
            if self.is_initialized:
                self._start_progress_monitoring()

        except Exception as e:
            log_error("进度检查回调异常", error=e)
            # 即使出错也要重新启动定时器
            if self.is_initialized:
                self._start_progress_monitoring()

    def _recover_running_tasks(self):
        """恢复运行中的任务"""
        try:
            # 查找运行状态的任务
            running_tasks = Task.find_all("tasks_status = %s", (TaskStatus.RUNNING.value,))

            for task in running_tasks:
                # 重新启动任务
                log_task_action(task.id, task.title, "恢复运行中的任务")

                task_thread = threading.Thread(
                    target=self._execute_task,
                    args=(task.id,),
                    daemon=True
                )
                task_thread.start()

                self._running_tasks[task.id] = task_thread

            if running_tasks:
                log_info(f"恢复了{len(running_tasks)}个运行中的任务")

        except Exception as e:
            log_error("恢复运行中的任务失败", error=e)

    def _pause_all_running_tasks(self):
        """暂停所有运行中的任务"""
        try:
            paused_count = 0
            for task_id in list(self._running_tasks.keys()):
                if self.task_manager.pause_task(task_id):
                    paused_count += 1

            self._running_tasks.clear()

            if paused_count > 0:
                log_info(f"暂停了{paused_count}个运行中的任务")

        except Exception as e:
            log_error("暂停所有运行中的任务失败", error=e)

    def _notify_task_change(self, action: str, task: Task):
        """通知任务变化"""
        try:
            for callback in self._task_change_callbacks:
                try:
                    callback(action, task)
                except Exception as e:
                    log_error("任务变化回调执行失败", error=e)

        except Exception as e:
            log_error("通知任务变化失败", error=e)

    def cleanup_old_tasks(self, days: int = 30) -> Dict[str, Any]:
        """清理旧任务"""
        try:
            deleted_count = self.task_manager.cleanup_old_tasks(days)

            return {
                'success': True,
                'message': f'成功清理{deleted_count}个{days}天前的旧任务',
                'deleted_count': deleted_count,
                'days': days
            }

        except Exception as e:
            log_error("清理旧任务异常", error=e)
            return {
                'success': False,
                'message': f'清理异常: {str(e)}',
                'error_code': 'SYSTEM_ERROR'
            }


# 全局任务服务实例
task_service = TaskService()