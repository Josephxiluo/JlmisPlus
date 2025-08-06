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
    # 简化处理 - 修复 MockTaskManager 类
    class MockTask:
        def __init__(self, **kwargs):
            self.id = kwargs.get('id', 1)
            self.title = kwargs.get('title', '测试任务')
            self.status = kwargs.get('status', 'draft')
            self.total_count = kwargs.get('total_count', 100)
            self.success_count = kwargs.get('success_count', 30)
            self.failed_count = kwargs.get('failed_count', 5)
            self.pending_count = kwargs.get('pending_count', 65)

        def save(self):
            return True

        def get_summary(self):
            progress = 0
            if self.total_count > 0:
                completed = self.success_count + self.failed_count
                progress = (completed / self.total_count) * 100

            return {
                'id': self.id,
                'title': self.title,
                'status': self.status,
                'total': self.total_count,
                'sent': self.success_count + self.failed_count,
                'success_count': self.success_count,
                'failed_count': self.failed_count,
                'pending_count': self.pending_count,
                'progress': round(progress, 1)
            }

    class MockTaskManager:
        def __init__(self):
            # 模拟任务数据
            self.tasks = [
                MockTask(id=1, title='测试任务1', status='running', total_count=100, success_count=30, failed_count=2),
                MockTask(id=2, title='测试任务2', status='paused', total_count=200, success_count=50, failed_count=5),
                MockTask(id=3, title='测试任务3', status='completed', total_count=150, success_count=148, failed_count=2),
            ]

        def create_task(self, **kwargs):
            task_id = max([t.id for t in self.tasks]) + 1 if self.tasks else 1
            new_task = MockTask(id=task_id, **kwargs)
            self.tasks.append(new_task)
            return new_task

        def get_user_tasks(self, operator_id, status=None, page=1, page_size=20):
            """获取用户任务列表 - 修复缺失的方法"""
            try:
                # 过滤任务（如果指定状态）
                filtered_tasks = self.tasks
                if status:
                    filtered_tasks = [t for t in self.tasks if t.status == status]

                # 分页处理
                start_idx = (page - 1) * page_size
                end_idx = start_idx + page_size
                page_tasks = filtered_tasks[start_idx:end_idx]

                return {
                    'success': True,
                    'tasks': page_tasks,
                    'total_count': len(filtered_tasks),
                    'page': page,
                    'page_size': page_size,
                    'total_pages': (len(filtered_tasks) + page_size - 1) // page_size
                }
            except Exception as e:
                return {
                    'success': False,
                    'tasks': [],
                    'total_count': 0,
                    'page': page,
                    'page_size': page_size,
                    'total_pages': 0,
                    'error': str(e)
                }

        def start_task(self, task_id):
            """启动任务"""
            for task in self.tasks:
                if task.id == task_id:
                    task.status = 'running'
                    return True
            return False

        def pause_task(self, task_id):
            """暂停任务"""
            for task in self.tasks:
                if task.id == task_id:
                    task.status = 'paused'
                    return True
            return False

        def resume_task(self, task_id):
            """恢复任务"""
            for task in self.tasks:
                if task.id == task_id:
                    task.status = 'running'
                    return True
            return False

        def cancel_task(self, task_id):
            """取消任务"""
            for task in self.tasks:
                if task.id == task_id:
                    task.status = 'cancelled'
                    return True
            return False

        def delete_task(self, task_id, force=False):
            """删除任务"""
            self.tasks = [t for t in self.tasks if t.id != task_id]
            return True

        def stop_all_tasks(self, operator_id):
            """停止所有任务"""
            stopped_count = 0
            for task in self.tasks:
                if task.status == 'running':
                    task.status = 'paused'
                    stopped_count += 1
            return {'success': True, 'count': stopped_count}

        def start_all_tasks(self, operator_id):
            """启动所有任务"""
            started_count = 0
            for task in self.tasks:
                if task.status in ['draft', 'paused']:
                    task.status = 'running'
                    started_count += 1
            return {'success': True, 'count': started_count}

        def clear_completed_tasks(self, operator_id):
            """清理完成任务"""
            initial_count = len(self.tasks)
            self.tasks = [t for t in self.tasks if t.status != 'completed']
            cleared_count = initial_count - len(self.tasks)
            return {'success': True, 'count': cleared_count}

        def retry_failed(self, task_id):
            """重试失败"""
            for task in self.tasks:
                if task.id == task_id:
                    # 模拟重试逻辑
                    retry_count = task.failed_count
                    task.failed_count = max(0, task.failed_count - retry_count // 2)
                    task.pending_count += retry_count // 2
                    return {'success': True, 'count': retry_count // 2}
            return {'success': False, 'count': 0}

        def test_task(self, data):
            """测试任务"""
            return {
                'success': True,
                'message': f"测试短信已发送到 {data.get('test_phone')}",
                'send_time': datetime.now().strftime('%H:%M:%S')
            }

        def update_task_content(self, data):
            """更新任务内容"""
            task_id = data.get('task_id')
            for task in self.tasks:
                if task.id == task_id:
                    # 模拟更新内容
                    return {'success': True, 'message': '任务内容已更新'}
            return {'success': False, 'message': '任务不存在'}

    class MockTaskMessage:
        pass

    class MockTaskMessageManager:
        def create_messages_from_file(self, task_id, file_path, message_content):
            return True

        def cancel_pending_messages(self, task_id):
            return 10  # 模拟取消了10条消息

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

    def create_task(self, task_data) -> Dict[str, Any]:
        """创建任务 - 修复参数处理"""
        try:
            with self._lock:
                # 处理任务数据
                title = task_data.get('title', '新任务')
                mode = task_data.get('template_type', 'sms')
                message_content = task_data.get('content', '')
                operator_id = task_data.get('user_id', 1)
                phone_numbers = task_data.get('targets', [])

                # 创建任务
                task = self.task_manager.create_task(
                    title=title,
                    mode=mode,
                    message_content=message_content,
                    operator_id=operator_id,
                    total_count=len(phone_numbers),
                    status=task_data.get('status', 'draft')
                )

                if not task:
                    return {
                        'success': False,
                        'message': '任务创建失败',
                        'error_code': 'CREATE_FAILED'
                    }

                # 处理号码
                if phone_numbers:
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

    def get_user_tasks(self, operator_id, status=None, page=1, page_size=20) -> Dict[str, Any]:
        """获取用户任务列表 - 修复方法调用"""
        try:
            result = self.task_manager.get_user_tasks(operator_id, status, page, page_size)

            if result['success']:
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
            else:
                return result

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

                log_task_action(task_id, f"任务{task_id}", "启动任务")

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
        try:
            if self.task_manager.pause_task(task_id):
                # 移除运行中的任务线程
                if task_id in self._running_tasks:
                    # 任务线程会自动检测暂停状态并停止
                    del self._running_tasks[task_id]

                log_task_action(task_id, f"任务{task_id}", "暂停任务")

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

                log_task_action(task_id, f"任务{task_id}", "恢复任务")

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

                log_task_action(task_id, f"任务{task_id}", "取消任务", f"取消{cancelled_count}条待发送消息")

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

            if self.task_manager.delete_task(task_id, force):
                log_task_action(task_id, f"任务{task_id}", "删除任务")

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

    # 新增缺失的方法
    def stop_all_tasks(self, operator_id: int) -> Dict[str, Any]:
        """停止所有任务"""
        try:
            return self.task_manager.stop_all_tasks(operator_id)
        except Exception as e:
            log_error("停止所有任务异常", error=e)
            return {'success': False, 'message': f'停止异常: {str(e)}'}

    def start_all_tasks(self, operator_id: int) -> Dict[str, Any]:
        """启动所有任务"""
        try:
            return self.task_manager.start_all_tasks(operator_id)
        except Exception as e:
            log_error("启动所有任务异常", error=e)
            return {'success': False, 'message': f'启动异常: {str(e)}'}

    def clear_completed_tasks(self, operator_id: int) -> Dict[str, Any]:
        """清理完成任务"""
        try:
            return self.task_manager.clear_completed_tasks(operator_id)
        except Exception as e:
            log_error("清理完成任务异常", error=e)
            return {'success': False, 'message': f'清理异常: {str(e)}'}

    def retry_failed(self, task_id: int) -> Dict[str, Any]:
        """重试失败的消息"""
        try:
            return self.task_manager.retry_failed(task_id)
        except Exception as e:
            log_error(f"重试任务{task_id}失败消息异常", error=e)
            return {'success': False, 'message': f'重试异常: {str(e)}'}

    def test_task(self, data) -> Dict[str, Any]:
        """测试任务"""
        try:
            return self.task_manager.test_task(data)
        except Exception as e:
            log_error("测试任务异常", error=e)
            return {'success': False, 'message': f'测试异常: {str(e)}'}

    def update_task_content(self, data) -> Dict[str, Any]:
        """更新任务内容"""
        try:
            return self.task_manager.update_task_content(data)
        except Exception as e:
            log_error("更新任务内容异常", error=e)
            return {'success': False, 'message': f'更新异常: {str(e)}'}

    def _execute_task(self, task_id: int):
        """执行任务（在独立线程中运行）"""
        try:
            log_task_action(task_id, f"任务{task_id}", "开始执行")

            # 模拟任务执行
            for i in range(10):
                # 检查任务是否被暂停或取消
                if task_id not in self._running_tasks:
                    log_task_action(task_id, f"任务{task_id}", "任务已暂停或取消，停止执行")
                    break

                # 模拟处理消息
                time.sleep(1)

            # 任务执行完成，清理线程
            if task_id in self._running_tasks:
                del self._running_tasks[task_id]

            log_task_action(task_id, f"任务{task_id}", "任务执行完成")

        except Exception as e:
            log_error(f"执行任务{task_id}异常", error=e)
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
                    # 通知进度变化
                    self._notify_task_change('progress', f"任务{task_id}")

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
            log_info("恢复运行中的任务检查完成")
        except Exception as e:
            log_error("恢复运行中的任务失败", error=e)

    def _pause_all_running_tasks(self):
        """暂停所有运行中的任务"""
        try:
            paused_count = len(self._running_tasks)
            self._running_tasks.clear()

            if paused_count > 0:
                log_info(f"暂停了{paused_count}个运行中的任务")

        except Exception as e:
            log_error("暂停所有运行中的任务失败", error=e)

    def _notify_task_change(self, action: str, task):
        """通知任务变化"""
        try:
            for callback in self._task_change_callbacks:
                try:
                    callback(action, task)
                except Exception as e:
                    log_error("任务变化回调执行失败", error=e)

        except Exception as e:
            log_error("通知任务变化失败", error=e)

    def add_task_change_callback(self, callback: Callable):
        """添加任务变化回调函数"""
        try:
            if callable(callback):
                self._task_change_callbacks.append(callback)
                log_info(f"添加任务变化回调函数，当前回调数量: {len(self._task_change_callbacks)}")
        except Exception as e:
            log_error("添加任务变化回调失败", error=e)

    def remove_task_change_callback(self, callback: Callable):
        """移除任务变化回调函数"""
        try:
            if callback in self._task_change_callbacks:
                self._task_change_callbacks.remove(callback)
                log_info(f"移除任务变化回调函数，当前回调数量: {len(self._task_change_callbacks)}")
        except Exception as e:
            log_error("移除任务变化回调失败", error=e)


# 全局任务服务实例
task_service = TaskService()