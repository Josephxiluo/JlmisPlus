"""
猫池短信系统任务模型 - tkinter版
Task models for SMS Pool System - tkinter version
"""

import sys
import json
from enum import Enum
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Union
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from .base import BaseModel, ModelManager
    from config.settings import settings
    from config.logging_config import get_logger, log_task_action, log_error
except ImportError:
    # 简化处理
    from base import BaseModel, ModelManager

    import logging


    def get_logger(name='models.task'):
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

logger = get_logger('models.task')


class TaskStatus(Enum):
    """任务状态枚举"""
    DRAFT = "draft"  # 草稿
    PENDING = "pending"  # 待执行
    RUNNING = "running"  # 执行中
    PAUSED = "paused"  # 已暂停
    COMPLETED = "completed"  # 已完成
    CANCELLED = "cancelled"  # 已取消
    FAILED = "failed"  # 失败

    @classmethod
    def get_choices(cls):
        """获取所有选择项"""
        return [status.value for status in cls]

    @classmethod
    def get_display_names(cls):
        """获取显示名称映射"""
        return {
            cls.DRAFT.value: "草稿",
            cls.PENDING.value: "待执行",
            cls.RUNNING.value: "执行中",
            cls.PAUSED.value: "已暂停",
            cls.COMPLETED.value: "已完成",
            cls.CANCELLED.value: "已取消",
            cls.FAILED.value: "失败"
        }


class TaskMode(Enum):
    """任务模式枚举"""
    SMS = "sms"  # 短信
    MMS = "mms"  # 彩信

    @classmethod
    def get_choices(cls):
        """获取所有选择项"""
        return [mode.value for mode in cls]

    @classmethod
    def get_display_names(cls):
        """获取显示名称映射"""
        return {
            cls.SMS.value: "短信",
            cls.MMS.value: "彩信"
        }


@dataclass
class Task(BaseModel):
    """任务模型"""

    # 表名
    _table_name: str = "tasks"

    # 字段映射（模型字段名 -> 数据库字段名）
    _field_mappings: Dict[str, str] = field(default_factory=lambda: {
        'id': 'tasks_id',
        'title': 'tasks_title',
        'mode': 'tasks_mode',
        'subject': 'tasks_subject',
        'message_content': 'tasks_message_content',
        'template_id': 'tasks_template_id',
        'number_mode': 'tasks_number_mode',
        'total_count': 'tasks_total_count',
        'success_count': 'tasks_success_count',
        'failed_count': 'tasks_failed_count',
        'pending_count': 'tasks_pending_count',
        'status': 'tasks_status',
        'operators_id': 'operators_id',
        'priority': 'tasks_priority',
        'scheduled_time': 'tasks_scheduled_time',
        'started_time': 'tasks_started_time',
        'completed_time': 'tasks_completed_time',
        'send_config': 'tasks_send_config',
        'statistics': 'tasks_statistics',
        'error_info': 'tasks_error_info',
        'remark': 'tasks_remark',
        'created_at': 'tasks_created_at',
        'updated_at': 'tasks_updated_at'
    })

    # 验证规则
    _validation_rules: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        'title': {
            'required': True,
            'type': str,
            'min_length': 1,
            'max_length': 200,
            'message': '任务标题必须在1-200个字符之间'
        },
        'mode': {
            'required': True,
            'type': str,
            'choices': TaskMode.get_choices(),
            'message': '任务模式必须是sms或mms'
        },
        'message_content': {
            'required': True,
            'type': str,
            'min_length': 1,
            'max_length': 1000,
            'message': '消息内容必须在1-1000个字符之间'
        },
        'status': {
            'required': True,
            'type': str,
            'choices': TaskStatus.get_choices(),
            'message': '任务状态无效'
        },
        'operators_id': {
            'required': True,
            'type': int,
            'min_value': 1,
            'message': '操作用户ID必须是正整数'
        },
        'total_count': {
            'type': int,
            'min_value': 0,
            'message': '总数量不能为负数'
        },
        'success_count': {
            'type': int,
            'min_value': 0,
            'message': '成功数量不能为负数'
        },
        'failed_count': {
            'type': int,
            'min_value': 0,
            'message': '失败数量不能为负数'
        },
        'pending_count': {
            'type': int,
            'min_value': 0,
            'message': '待发送数量不能为负数'
        },
        'priority': {
            'type': int,
            'min_value': 1,
            'max_value': 10,
            'message': '优先级必须在1-10之间'
        }
    })

    # 任务基本信息
    title: str = ""
    mode: str = TaskMode.SMS.value
    subject: Optional[str] = field(default=None)  # 彩信主题
    message_content: str = ""
    template_id: Optional[int] = field(default=None)
    number_mode: str = "domestic"  # domestic/international

    # 统计信息
    total_count: int = 0
    success_count: int = 0
    failed_count: int = 0
    pending_count: int = 0

    # 任务状态
    status: str = TaskStatus.DRAFT.value

    # 关联信息
    operators_id: int = 0

    # 执行控制
    priority: int = 5
    scheduled_time: Optional[datetime] = field(default=None)
    started_time: Optional[datetime] = field(default=None)
    completed_time: Optional[datetime] = field(default=None)

    # 配置信息
    send_config: Optional[str] = field(default=None)  # JSON字符串
    statistics: Optional[str] = field(default=None)  # JSON字符串
    error_info: Optional[str] = field(default=None)  # JSON字符串

    # 备注
    remark: Optional[str] = field(default=None)

    def __post_init__(self):
        """初始化后处理"""
        super().__post_init__()

        # 初始化待发送数量
        if self.pending_count == 0 and self.total_count > 0:
            self.pending_count = self.total_count - self.success_count - self.failed_count

    def get_status_display(self) -> str:
        """获取状态显示名称"""
        return TaskStatus.get_display_names().get(self.status, self.status)

    def get_mode_display(self) -> str:
        """获取模式显示名称"""
        return TaskMode.get_display_names().get(self.mode, self.mode)

    def is_draft(self) -> bool:
        """是否为草稿状态"""
        return self.status == TaskStatus.DRAFT.value

    def is_pending(self) -> bool:
        """是否为待执行状态"""
        return self.status == TaskStatus.PENDING.value

    def is_running(self) -> bool:
        """是否为执行中状态"""
        return self.status == TaskStatus.RUNNING.value

    def is_paused(self) -> bool:
        """是否为暂停状态"""
        return self.status == TaskStatus.PAUSED.value

    def is_completed(self) -> bool:
        """是否为已完成状态"""
        return self.status == TaskStatus.COMPLETED.value

    def is_cancelled(self) -> bool:
        """是否为已取消状态"""
        return self.status == TaskStatus.CANCELLED.value

    def is_failed(self) -> bool:
        """是否为失败状态"""
        return self.status == TaskStatus.FAILED.value

    def can_start(self) -> bool:
        """是否可以开始执行"""
        return self.status in [TaskStatus.DRAFT.value, TaskStatus.PENDING.value]

    def can_pause(self) -> bool:
        """是否可以暂停"""
        return self.status == TaskStatus.RUNNING.value

    def can_resume(self) -> bool:
        """是否可以恢复"""
        return self.status == TaskStatus.PAUSED.value

    def can_cancel(self) -> bool:
        """是否可以取消"""
        return self.status in [
            TaskStatus.DRAFT.value,
            TaskStatus.PENDING.value,
            TaskStatus.RUNNING.value,
            TaskStatus.PAUSED.value
        ]

    def can_delete(self) -> bool:
        """是否可以删除"""
        return self.status in [
            TaskStatus.DRAFT.value,
            TaskStatus.COMPLETED.value,
            TaskStatus.CANCELLED.value,
            TaskStatus.FAILED.value
        ]

    def can_edit(self) -> bool:
        """是否可以编辑"""
        return self.status in [TaskStatus.DRAFT.value, TaskStatus.PENDING.value]

    def get_progress_percentage(self) -> float:
        """获取进度百分比"""
        if self.total_count == 0:
            return 0.0

        completed = self.success_count + self.failed_count
        return round(completed / self.total_count * 100, 2)

    def get_success_rate(self) -> float:
        """获取成功率"""
        completed = self.success_count + self.failed_count
        if completed == 0:
            return 0.0

        return round(self.success_count / completed * 100, 2)

    def update_status(self, new_status: str, auto_save: bool = True) -> bool:
        """更新任务状态"""
        try:
            old_status = self.status
            self.status = new_status

            # 设置时间戳
            current_time = datetime.now()

            if new_status == TaskStatus.RUNNING.value and not self.started_time:
                self.started_time = current_time
            elif new_status in [TaskStatus.COMPLETED.value, TaskStatus.CANCELLED.value, TaskStatus.FAILED.value]:
                if not self.completed_time:
                    self.completed_time = current_time

            # 自动保存
            if auto_save and self.save():
                log_task_action(self.id, self.title, f"状态变更: {old_status} -> {new_status}")
                return True

            return not auto_save  # 如果不自动保存，返回True

        except Exception as e:
            log_error("更新任务状态失败", error=e)
            return False

    def update_progress(self, success_delta: int = 0, failed_delta: int = 0, auto_save: bool = True) -> bool:
        """更新任务进度"""
        try:
            # 更新计数
            self.success_count += success_delta
            self.failed_count += failed_delta
            self.pending_count = max(0, self.total_count - self.success_count - self.failed_count)

            # 检查是否完成
            if self.pending_count == 0 and self.is_running():
                if self.failed_count == 0:
                    self.update_status(TaskStatus.COMPLETED.value, False)
                elif self.success_count == 0:
                    self.update_status(TaskStatus.FAILED.value, False)
                else:
                    self.update_status(TaskStatus.COMPLETED.value, False)

            # 自动保存
            if auto_save and self.save():
                log_task_action(
                    self.id, self.title,
                    f"进度更新: 成功+{success_delta}, 失败+{failed_delta}"
                )
                return True

            return not auto_save

        except Exception as e:
            log_error("更新任务进度失败", error=e)
            return False

    def get_send_config(self) -> Dict[str, Any]:
        """获取发送配置"""
        if not self.send_config:
            return {}

        try:
            return json.loads(self.send_config)
        except (json.JSONDecodeError, TypeError):
            return {}

    def set_send_config(self, config: Dict[str, Any]):
        """设置发送配置"""
        try:
            self.send_config = json.dumps(config, ensure_ascii=False)
        except (TypeError, ValueError) as e:
            log_error("设置发送配置失败", error=e)

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        if not self.statistics:
            return {}

        try:
            return json.loads(self.statistics)
        except (json.JSONDecodeError, TypeError):
            return {}

    def set_statistics(self, stats: Dict[str, Any]):
        """设置统计信息"""
        try:
            self.statistics = json.dumps(stats, ensure_ascii=False)
        except (TypeError, ValueError) as e:
            log_error("设置统计信息失败", error=e)

    def get_error_info(self) -> Dict[str, Any]:
        """获取错误信息"""
        if not self.error_info:
            return {}

        try:
            return json.loads(self.error_info)
        except (json.JSONDecodeError, TypeError):
            return {}

    def set_error_info(self, error: Dict[str, Any]):
        """设置错误信息"""
        try:
            self.error_info = json.dumps(error, ensure_ascii=False)
        except (TypeError, ValueError) as e:
            log_error("设置错误信息失败", error=e)

    def add_error(self, error_type: str, error_message: str, context: Dict[str, Any] = None):
        """添加错误信息"""
        current_errors = self.get_error_info()

        if 'errors' not in current_errors:
            current_errors['errors'] = []

        error_entry = {
            'type': error_type,
            'message': error_message,
            'timestamp': datetime.now().isoformat(),
            'context': context or {}
        }

        current_errors['errors'].append(error_entry)
        self.set_error_info(current_errors)

    def get_duration(self) -> Optional[float]:
        """获取任务执行时长（秒）"""
        if not self.started_time:
            return None

        end_time = self.completed_time or datetime.now()
        duration = end_time - self.started_time
        return duration.total_seconds()

    def get_estimated_completion_time(self) -> Optional[datetime]:
        """获取预计完成时间"""
        if not self.is_running() or self.success_count + self.failed_count == 0:
            return None

        duration = self.get_duration()
        if not duration or duration <= 0:
            return None

        completed = self.success_count + self.failed_count
        rate = completed / duration  # 条/秒

        if rate <= 0:
            return None

        remaining_time = self.pending_count / rate
        return datetime.now() + timedelta(seconds=remaining_time)

    def calculate_cost(self) -> float:
        """计算任务成本"""
        sms_rate = getattr(settings, 'SMS_RATE', 1.0) if hasattr(settings, 'SMS_RATE') else 1.0
        mms_rate = getattr(settings, 'MMS_RATE', 3.0) if hasattr(settings, 'MMS_RATE') else 3.0

        rate = mms_rate if self.mode == TaskMode.MMS.value else sms_rate
        return self.success_count * rate

    def get_summary(self) -> Dict[str, Any]:
        """获取任务摘要"""
        return {
            'id': self.id,
            'title': self.title,
            'mode': self.mode,
            'mode_display': self.get_mode_display(),
            'status': self.status,
            'status_display': self.get_status_display(),
            'progress': {
                'total': self.total_count,
                'success': self.success_count,
                'failed': self.failed_count,
                'pending': self.pending_count,
                'percentage': self.get_progress_percentage(),
                'success_rate': self.get_success_rate()
            },
            'timing': {
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'started_time': self.started_time.isoformat() if self.started_time else None,
                'completed_time': self.completed_time.isoformat() if self.completed_time else None,
                'duration': self.get_duration(),
                'estimated_completion': self.get_estimated_completion_time().isoformat() if self.get_estimated_completion_time() else None
            },
            'cost': self.calculate_cost(),
            'operators_id': self.operators_id
        }

    @classmethod
    def find_by_operator(cls, operator_id: int, status: str = None) -> List['Task']:
        """根据操作用户查找任务"""
        where = "operators_id = %s"
        params = [operator_id]

        if status:
            where += " AND tasks_status = %s"
            params.append(status)

        return cls.find_all(where, tuple(params), order_by="tasks_created_at DESC")

    @classmethod
    def find_running_tasks(cls, operator_id: int = None) -> List['Task']:
        """查找正在运行的任务"""
        where = "tasks_status = %s"
        params = [TaskStatus.RUNNING.value]

        if operator_id:
            where += " AND operators_id = %s"
            params.append(operator_id)

        return cls.find_all(where, tuple(params))

    @classmethod
    def find_pending_tasks(cls, operator_id: int = None) -> List['Task']:
        """查找待执行的任务"""
        where = "tasks_status IN %s"
        params = [(TaskStatus.PENDING.value, TaskStatus.PAUSED.value)]

        if operator_id:
            where += " AND operators_id = %s"
            params.append(operator_id)

        return cls.find_all(where, tuple(params), order_by="tasks_priority DESC, tasks_created_at ASC")

    @classmethod
    def get_task_statistics(cls, operator_id: int = None, start_date: datetime = None, end_date: datetime = None) -> \
    Dict[str, Any]:
        """获取任务统计信息"""
        try:
            from database.connection import get_db_connection
            db = get_db_connection()

            # 构建查询条件
            where_parts = []
            params = []

            if operator_id:
                where_parts.append("operators_id = %s")
                params.append(operator_id)

            if start_date:
                where_parts.append("tasks_created_at >= %s")
                params.append(start_date)

            if end_date:
                where_parts.append("tasks_created_at <= %s")
                params.append(end_date)

            where_clause = " AND ".join(where_parts) if where_parts else "1=1"

            # 统计查询
            query = f"""
                SELECT 
                    tasks_status,
                    COUNT(*) as task_count,
                    SUM(tasks_total_count) as total_messages,
                    SUM(tasks_success_count) as success_messages,
                    SUM(tasks_failed_count) as failed_messages
                FROM {cls.get_table_name()}
                WHERE {where_clause}
                GROUP BY tasks_status
            """

            results = db.execute_query(query, tuple(params), dict_cursor=True)

            # 处理结果
            stats = {
                'total_tasks': 0,
                'total_messages': 0,
                'success_messages': 0,
                'failed_messages': 0,
                'by_status': {}
            }

            for row in results:
                status = row['tasks_status']
                task_count = row['task_count'] or 0
                total_messages = row['total_messages'] or 0
                success_messages = row['success_messages'] or 0
                failed_messages = row['failed_messages'] or 0

                stats['total_tasks'] += task_count
                stats['total_messages'] += total_messages
                stats['success_messages'] += success_messages
                stats['failed_messages'] += failed_messages

                stats['by_status'][status] = {
                    'task_count': task_count,
                    'total_messages': total_messages,
                    'success_messages': success_messages,
                    'failed_messages': failed_messages
                }

            # 计算成功率
            if stats['total_messages'] > 0:
                stats['success_rate'] = round(stats['success_messages'] / stats['total_messages'] * 100, 2)
            else:
                stats['success_rate'] = 0.0

            return stats

        except Exception as e:
            log_error("获取任务统计信息失败", error=e)
            return {}


# 任务管理器
class TaskManager(ModelManager):
    """任务管理器"""

    def __init__(self):
        super().__init__(Task)

    def create_task(self, title: str, mode: str, message_content: str,
                    operator_id: int, **kwargs) -> Optional[Task]:
        """创建新任务"""
        try:
            task = self.create(
                title=title,
                mode=mode,
                message_content=message_content,
                operators_id=operator_id,
                status=TaskStatus.DRAFT.value,
                **kwargs
            )

            if task.save():
                log_task_action(task.id, task.title, "创建任务")
                return task

            return None

        except Exception as e:
            log_error("创建任务失败", error=e)
            return None

    def start_task(self, task_id: int) -> bool:
        """启动任务"""
        try:
            task = self.model_class.find_by_id(task_id)
            if not task:
                return False

            if not task.can_start():
                log_error(f"任务{task_id}当前状态不允许启动")
                return False

            return task.update_status(TaskStatus.RUNNING.value)

        except Exception as e:
            log_error("启动任务失败", error=e)
            return False

    def pause_task(self, task_id: int) -> bool:
        """暂停任务"""
        try:
            task = self.model_class.find_by_id(task_id)
            if not task:
                return False

            if not task.can_pause():
                log_error(f"任务{task_id}当前状态不允许暂停")
                return False

            return task.update_status(TaskStatus.PAUSED.value)

        except Exception as e:
            log_error("暂停任务失败", error=e)
            return False

    def resume_task(self, task_id: int) -> bool:
        """恢复任务"""
        try:
            task = self.model_class.find_by_id(task_id)
            if not task:
                return False

            if not task.can_resume():
                log_error(f"任务{task_id}当前状态不允许恢复")
                return False

            return task.update_status(TaskStatus.RUNNING.value)

        except Exception as e:
            log_error("恢复任务失败", error=e)
            return False

    def cancel_task(self, task_id: int) -> bool:
        """取消任务"""
        try:
            task = self.model_class.find_by_id(task_id)
            if not task:
                return False

            if not task.can_cancel():
                log_error(f"任务{task_id}当前状态不允许取消")
                return False

            return task.update_status(TaskStatus.CANCELLED.value)

        except Exception as e:
            log_error("取消任务失败", error=e)
            return False

    def delete_task(self, task_id: int, force: bool = False) -> bool:
        """删除任务"""
        try:
            task = self.model_class.find_by_id(task_id)
            if not task:
                return False

            if not force and not task.can_delete():
                log_error(f"任务{task_id}当前状态不允许删除")
                return False

            # 删除相关的消息明细（如果需要）
            # 这里可以添加级联删除逻辑

            if task.delete():
                log_task_action(task_id, task.title, "删除任务")
                return True

            return False

        except Exception as e:
            log_error("删除任务失败", error=e)
            return False

    def get_user_tasks(self, operator_id: int, status: str = None,
                       page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """分页获取用户任务"""
        try:
            # 构建查询条件
            where = "operators_id = %s"
            params = [operator_id]

            if status:
                where += " AND tasks_status = %s"
                params.append(status)

            # 计算偏移量
            offset = (page - 1) * page_size

            # 查询任务
            tasks = self.model_class.find_all(
                where=where,
                params=tuple(params),
                order_by="tasks_created_at DESC",
                limit=page_size,
                offset=offset
            )

            # 统计总数
            total_count = self.model_class.count(where, tuple(params))

            return {
                'tasks': tasks,
                'total_count': total_count,
                'page': page,
                'page_size': page_size,
                'total_pages': (total_count + page_size - 1) // page_size
            }

        except Exception as e:
            log_error("获取用户任务失败", error=e)
            return {'tasks': [], 'total_count': 0, 'page': page, 'page_size': page_size, 'total_pages': 0}

    def cleanup_old_tasks(self, days: int = 30) -> int:
        """清理旧任务"""
        try:
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=days)

            # 只清理已完成、已取消或失败的任务
            where = """
                tasks_status IN %s 
                AND tasks_completed_time < %s
            """
            params = (
                (TaskStatus.COMPLETED.value, TaskStatus.CANCELLED.value, TaskStatus.FAILED.value),
                cutoff_date
            )

            # 获取要删除的任务
            old_tasks = self.model_class.find_all(where, params)

            deleted_count = 0
            for task in old_tasks:
                if task.delete():
                    deleted_count += 1

            log_task_action(0, "系统清理", f"清理{deleted_count}个旧任务")
            return deleted_count

        except Exception as e:
            log_error("清理旧任务失败", error=e)
            return 0


# 全局任务管理器实例
task_manager = TaskManager()