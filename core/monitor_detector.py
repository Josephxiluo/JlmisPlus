"""
猫池短信系统监测检测器 - tkinter版
Monitor detector for SMS Pool System - tkinter version
"""

import sys
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from config.settings import settings
    from config.logging_config import get_logger, log_info, log_error, log_timer_action
    from .utils import format_duration, validate_phone_number
except ImportError:
    # 简化处理
    class MockSettings:
        MONITOR_ALERT_INTERVAL = 1000
        DEFAULT_MONITOR_PHONE = ""
        DEFAULT_SEND_INTERVAL = 1000

    settings = MockSettings()

    import logging
    def get_logger(name='core.monitor_detector'):
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    def log_info(message):
        logger = get_logger()
        logger.info(message)

    def log_error(message, error=None):
        logger = get_logger()
        logger.error(f"{message}: {error}" if error else message)

    def log_timer_action(timer_name, action, interval=None):
        logger = get_logger()
        message = f"[定时器] {timer_name} {action}"
        if interval:
            message += f" 间隔={interval}秒"
        logger.debug(message)

    def format_duration(seconds):
        if seconds < 60:
            return f"{seconds:.1f}秒"
        return f"{int(seconds // 60)}分{int(seconds % 60)}秒"

    def validate_phone_number(phone, international=False):
        import re
        if international:
            return bool(re.match(r'^\+\d{8,15}$', phone))
        else:
            return bool(re.match(r'^1[3-9]\d{9}$', phone))

logger = get_logger('core.monitor_detector')


class MonitorEvent:
    """监测事件类"""

    def __init__(self, event_type: str, task_id: int, task_name: str,
                 message_count: int, details: Dict[str, Any] = None):
        self.event_type = event_type
        self.task_id = task_id
        self.task_name = task_name
        self.message_count = message_count
        self.details = details or {}
        self.timestamp = datetime.now()
        self.processed = False
        self.notification_sent = False

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'event_type': self.event_type,
            'task_id': self.task_id,
            'task_name': self.task_name,
            'message_count': self.message_count,
            'details': self.details,
            'timestamp': self.timestamp.isoformat(),
            'processed': self.processed,
            'notification_sent': self.notification_sent
        }


class TaskMonitor:
    """任务监控器类"""

    def __init__(self, task_id: int, task_name: str, alert_interval: int = 1000):
        self.task_id = task_id
        self.task_name = task_name
        self.alert_interval = alert_interval
        self.sent_count = 0
        self.success_count = 0
        self.failed_count = 0
        self.last_alert_count = 0
        self.created_time = datetime.now()
        self.last_activity_time = datetime.now()
        self.is_active = True

    def increment_sent(self):
        """增加发送计数"""
        self.sent_count += 1
        self.last_activity_time = datetime.now()

    def increment_success(self):
        """增加成功计数"""
        self.success_count += 1
        self.last_activity_time = datetime.now()

    def increment_failed(self):
        """增加失败计数"""
        self.failed_count += 1
        self.last_activity_time = datetime.now()

    def should_alert(self) -> bool:
        """是否应该发送监测提醒"""
        if not self.is_active:
            return False

        # 检查是否达到提醒间隔
        messages_since_alert = self.sent_count - self.last_alert_count
        return messages_since_alert >= self.alert_interval

    def mark_alerted(self):
        """标记已发送提醒"""
        self.last_alert_count = self.sent_count

    def get_success_rate(self) -> float:
        """获取成功率"""
        if self.sent_count == 0:
            return 0.0
        return round(self.success_count / self.sent_count * 100, 2)

    def get_duration(self) -> float:
        """获取监控时长（秒）"""
        return (datetime.now() - self.created_time).total_seconds()

    def is_idle(self, idle_threshold: int = 300) -> bool:
        """是否空闲（超过指定时间无活动）"""
        idle_time = (datetime.now() - self.last_activity_time).total_seconds()
        return idle_time > idle_threshold

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'task_id': self.task_id,
            'task_name': self.task_name,
            'alert_interval': self.alert_interval,
            'sent_count': self.sent_count,
            'success_count': self.success_count,
            'failed_count': self.failed_count,
            'success_rate': self.get_success_rate(),
            'last_alert_count': self.last_alert_count,
            'messages_since_alert': self.sent_count - self.last_alert_count,
            'created_time': self.created_time.isoformat(),
            'last_activity_time': self.last_activity_time.isoformat(),
            'duration': self.get_duration(),
            'is_active': self.is_active,
            'is_idle': self.is_idle()
        }


class MonitorDetector:
    """监测检测器类"""

    def __init__(self):
        """初始化监测检测器"""
        self._lock = threading.Lock()
        self._task_monitors: Dict[int, TaskMonitor] = {}
        self._monitor_events: List[MonitorEvent] = []
        self._alert_callbacks: List[Callable] = []
        self._cleanup_timer: Optional[threading.Timer] = None
        self.is_initialized = False

        # 配置参数
        self.default_alert_interval = getattr(settings, 'MONITOR_ALERT_INTERVAL', 1000)
        self.default_monitor_phone = getattr(settings, 'DEFAULT_MONITOR_PHONE', '')
        self.cleanup_interval = 300  # 5分钟清理一次
        self.idle_threshold = 600    # 10分钟无活动视为空闲
        self.max_events_history = 1000  # 最大事件历史数量

        # 统计信息
        self.total_alerts_sent = 0
        self.total_events_processed = 0
        self.start_time: Optional[datetime] = None

    def initialize(self) -> bool:
        """初始化检测器"""
        try:
            log_info("监测检测器初始化开始")

            # 启动清理定时器
            self._start_cleanup_timer()

            self.start_time = datetime.now()
            self.is_initialized = True

            log_info(f"监测检测器初始化完成，默认提醒间隔: {self.default_alert_interval}")
            return True

        except Exception as e:
            log_error("监测检测器初始化失败", error=e)
            return False

    def shutdown(self):
        """关闭检测器"""
        try:
            log_info("监测检测器开始关闭")

            # 停止清理定时器
            self._stop_cleanup_timer()

            # 清理数据
            with self._lock:
                self._task_monitors.clear()
                self._monitor_events.clear()
                self._alert_callbacks.clear()

            self.is_initialized = False
            log_info("监测检测器关闭完成")

        except Exception as e:
            log_error("监测检测器关闭失败", error=e)

    def get_status(self) -> Dict[str, Any]:
        """获取检测器状态"""
        uptime = 0.0
        if self.start_time:
            uptime = (datetime.now() - self.start_time).total_seconds()

        return {
            'running': self.is_initialized,
            'monitored_tasks': len(self._task_monitors),
            'active_monitors': len([m for m in self._task_monitors.values() if m.is_active]),
            'total_events': len(self._monitor_events),
            'total_alerts_sent': self.total_alerts_sent,
            'total_events_processed': self.total_events_processed,
            'default_alert_interval': self.default_alert_interval,
            'default_monitor_phone': self.default_monitor_phone,
            'uptime': format_duration(uptime),
            'message': '监测检测器正常运行' if self.is_initialized else '监测检测器未初始化'
        }

    def start_monitoring_task(self, task_id: int, task_name: str,
                             alert_interval: int = None) -> Dict[str, Any]:
        """开始监控任务"""
        try:
            if alert_interval is None:
                alert_interval = self.default_alert_interval

            with self._lock:
                # 检查是否已在监控
                if task_id in self._task_monitors:
                    existing_monitor = self._task_monitors[task_id]
                    return {
                        'success': False,
                        'message': f'任务{task_id}已在监控中',
                        'monitor_info': existing_monitor.to_dict()
                    }

                # 创建新的监控器
                monitor = TaskMonitor(task_id, task_name, alert_interval)
                self._task_monitors[task_id] = monitor

                log_info(f"开始监控任务: ID={task_id}, 名称={task_name}, 提醒间隔={alert_interval}")

                return {
                    'success': True,
                    'message': f'开始监控任务{task_id}',
                    'task_id': task_id,
                    'monitor_info': monitor.to_dict()
                }

        except Exception as e:
            log_error(f"开始监控任务{task_id}异常", error=e)
            return {
                'success': False,
                'message': f'监控启动异常: {str(e)}',
                'error_code': 'MONITOR_START_ERROR'
            }

    def stop_monitoring_task(self, task_id: int) -> Dict[str, Any]:
        """停止监控任务"""
        try:
            with self._lock:
                if task_id not in self._task_monitors:
                    return {
                        'success': False,
                        'message': f'任务{task_id}未在监控中',
                        'error_code': 'TASK_NOT_MONITORED'
                    }

                monitor = self._task_monitors[task_id]
                monitor.is_active = False

                # 创建停止监控事件
                event = MonitorEvent(
                    event_type='monitor_stopped',
                    task_id=task_id,
                    task_name=monitor.task_name,
                    message_count=monitor.sent_count,
                    details={
                        'final_success_rate': monitor.get_success_rate(),
                        'total_duration': monitor.get_duration()
                    }
                )
                self._monitor_events.append(event)

                log_info(f"停止监控任务: ID={task_id}, 名称={monitor.task_name}")

                return {
                    'success': True,
                    'message': f'停止监控任务{task_id}',
                    'task_id': task_id,
                    'final_stats': monitor.to_dict()
                }

        except Exception as e:
            log_error(f"停止监控任务{task_id}异常", error=e)
            return {
                'success': False,
                'message': f'停止监控异常: {str(e)}',
                'error_code': 'MONITOR_STOP_ERROR'
            }

    def record_message_sent(self, task_id: int, success: bool = True) -> bool:
        """记录消息发送"""
        try:
            with self._lock:
                if task_id not in self._task_monitors:
                    return False

                monitor = self._task_monitors[task_id]
                if not monitor.is_active:
                    return False

                # 更新计数
                monitor.increment_sent()
                if success:
                    monitor.increment_success()
                else:
                    monitor.increment_failed()

                # 检查是否需要发送监测提醒
                if monitor.should_alert():
                    self._handle_monitor_alert(monitor)

                return True

        except Exception as e:
            log_error(f"记录任务{task_id}消息发送异常", error=e)
            return False

    def set_alert_interval(self, task_id: int, new_interval: int) -> Dict[str, Any]:
        """设置任务的提醒间隔"""
        try:
            with self._lock:
                if task_id not in self._task_monitors:
                    return {
                        'success': False,
                        'message': f'任务{task_id}未在监控中',
                        'error_code': 'TASK_NOT_MONITORED'
                    }

                monitor = self._task_monitors[task_id]
                old_interval = monitor.alert_interval
                monitor.alert_interval = new_interval

                log_info(f"任务{task_id}提醒间隔已更新: {old_interval} -> {new_interval}")

                return {
                    'success': True,
                    'message': f'任务{task_id}提醒间隔已更新',
                    'old_interval': old_interval,
                    'new_interval': new_interval
                }

        except Exception as e:
            log_error(f"设置任务{task_id}提醒间隔异常", error=e)
            return {
                'success': False,
                'message': f'设置异常: {str(e)}',
                'error_code': 'SET_INTERVAL_ERROR'
            }

    def get_task_monitor_info(self, task_id: int) -> Optional[Dict[str, Any]]:
        """获取任务监控信息"""
        try:
            with self._lock:
                monitor = self._task_monitors.get(task_id)
                return monitor.to_dict() if monitor else None
        except Exception as e:
            log_error(f"获取任务{task_id}监控信息异常", error=e)
            return None

    def get_all_monitors(self) -> List[Dict[str, Any]]:
        """获取所有监控器信息"""
        try:
            with self._lock:
                return [monitor.to_dict() for monitor in self._task_monitors.values()]
        except Exception as e:
            log_error("获取所有监控器信息异常", error=e)
            return []

    def get_active_monitors(self) -> List[Dict[str, Any]]:
        """获取活跃的监控器"""
        try:
            with self._lock:
                return [monitor.to_dict() for monitor in self._task_monitors.values()
                       if monitor.is_active]
        except Exception as e:
            log_error("获取活跃监控器异常", error=e)
            return []

    def get_monitor_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取监测事件"""
        try:
            recent_events = self._monitor_events[-limit:] if limit > 0 else self._monitor_events
            return [event.to_dict() for event in recent_events]
        except Exception as e:
            log_error("获取监测事件异常", error=e)
            return []

    def clear_monitor_events(self) -> Dict[str, Any]:
        """清除监测事件历史"""
        try:
            with self._lock:
                cleared_count = len(self._monitor_events)
                self._monitor_events.clear()

                log_info(f"清除了{cleared_count}条监测事件记录")

                return {
                    'success': True,
                    'message': f'清除了{cleared_count}条事件记录',
                    'cleared_count': cleared_count
                }

        except Exception as e:
            log_error("清除监测事件异常", error=e)
            return {
                'success': False,
                'message': f'清除异常: {str(e)}',
                'error_code': 'CLEAR_EVENTS_ERROR'
            }

    def add_alert_callback(self, callback: Callable[[MonitorEvent], None]):
        """添加监测提醒回调函数"""
        try:
            if callable(callback):
                self._alert_callbacks.append(callback)
                log_info(f"添加监测提醒回调函数，当前回调数量: {len(self._alert_callbacks)}")
        except Exception as e:
            log_error("添加监测提醒回调失败", error=e)

    def remove_alert_callback(self, callback: Callable[[MonitorEvent], None]):
        """移除监测提醒回调函数"""
        try:
            if callback in self._alert_callbacks:
                self._alert_callbacks.remove(callback)
                log_info(f"移除监测提醒回调函数，当前回调数量: {len(self._alert_callbacks)}")
        except Exception as e:
            log_error("移除监测提醒回调失败", error=e)

    def set_default_monitor_phone(self, phone: str) -> Dict[str, Any]:
        """设置默认监测号码"""
        try:
            # 验证手机号码格式
            if phone and not validate_phone_number(phone) and not validate_phone_number(phone, international=True):
                return {
                    'success': False,
                    'message': '手机号码格式不正确',
                    'error_code': 'INVALID_PHONE_FORMAT'
                }

            old_phone = self.default_monitor_phone
            self.default_monitor_phone = phone

            log_info(f"默认监测号码已更新: {old_phone} -> {phone}")

            return {
                'success': True,
                'message': '默认监测号码已更新',
                'old_phone': old_phone,
                'new_phone': phone
            }

        except Exception as e:
            log_error("设置默认监测号码异常", error=e)
            return {
                'success': False,
                'message': f'设置异常: {str(e)}',
                'error_code': 'SET_PHONE_ERROR'
            }

    def get_monitoring_statistics(self) -> Dict[str, Any]:
        """获取监控统计信息"""
        try:
            with self._lock:
                active_count = len([m for m in self._task_monitors.values() if m.is_active])
                idle_count = len([m for m in self._task_monitors.values() if m.is_idle()])

                total_sent = sum(m.sent_count for m in self._task_monitors.values())
                total_success = sum(m.success_count for m in self._task_monitors.values())

                avg_success_rate = 0.0
                if total_sent > 0:
                    avg_success_rate = round(total_success / total_sent * 100, 2)

                uptime = 0.0
                if self.start_time:
                    uptime = (datetime.now() - self.start_time).total_seconds()

                return {
                    'total_monitors': len(self._task_monitors),
                    'active_monitors': active_count,
                    'idle_monitors': idle_count,
                    'total_sent_messages': total_sent,
                    'total_success_messages': total_success,
                    'overall_success_rate': avg_success_rate,
                    'total_alerts_sent': self.total_alerts_sent,
                    'total_events_processed': self.total_events_processed,
                    'events_in_history': len(self._monitor_events),
                    'uptime_seconds': uptime,
                    'uptime_formatted': format_duration(uptime)
                }

        except Exception as e:
            log_error("获取监控统计信息异常", error=e)
            return {}

    def _handle_monitor_alert(self, monitor: TaskMonitor):
        """处理监测提醒"""
        try:
            # 创建监测事件
            event = MonitorEvent(
                event_type='alert_triggered',
                task_id=monitor.task_id,
                task_name=monitor.task_name,
                message_count=monitor.sent_count,
                details={
                    'success_rate': monitor.get_success_rate(),
                    'alert_interval': monitor.alert_interval,
                    'messages_since_last_alert': monitor.sent_count - monitor.last_alert_count,
                    'monitor_phone': self.default_monitor_phone
                }
            )

            # 添加到事件列表
            self._monitor_events.append(event)
            self.total_events_processed += 1

            # 标记监控器已发送提醒
            monitor.mark_alerted()

            # 触发回调
            self._notify_alert_callbacks(event)

            # 发送监测短信（如果有监测号码）
            if self.default_monitor_phone:
                self._send_monitor_message(event)

            log_info(f"触发监测提醒: 任务{monitor.task_id}, 已发送{monitor.sent_count}条消息")

        except Exception as e:
            log_error(f"处理监测提醒异常", error=e)

    def _send_monitor_message(self, event: MonitorEvent):
        """发送监测短信"""
        try:
            if not self.default_monitor_phone:
                return

            # 构建监测消息内容
            message_content = self._build_monitor_message_content(event)

            # 这里应该调用消息发送服务发送监测短信
            # 暂时记录日志
            log_info(f"发送监测短信到 {self.default_monitor_phone}: {message_content}")

            # 标记事件已发送通知
            event.notification_sent = True
            self.total_alerts_sent += 1

        except Exception as e:
            log_error("发送监测短信异常", error=e)

    def _build_monitor_message_content(self, event: MonitorEvent) -> str:
        """构建监测消息内容"""
        try:
            success_rate = event.details.get('success_rate', 0)

            content = f"监测提醒\n"
            content += f"任务: {event.task_name}\n"
            content += f"已发送: {event.message_count}条\n"
            content += f"成功率: {success_rate}%\n"
            content += f"时间: {event.timestamp.strftime('%H:%M:%S')}"

            return content

        except Exception as e:
            log_error("构建监测消息内容异常", error=e)
            return f"监测提醒: 任务{event.task_name}已发送{event.message_count}条消息"

    def _notify_alert_callbacks(self, event: MonitorEvent):
        """通知监测提醒回调"""
        try:
            for callback in self._alert_callbacks:
                try:
                    callback(event)
                except Exception as e:
                    log_error("监测提醒回调执行失败", error=e)
        except Exception as e:
            log_error("通知监测提醒回调失败", error=e)

    def _start_cleanup_timer(self):
        """启动清理定时器"""
        try:
            if self._cleanup_timer:
                self._cleanup_timer.cancel()

            self._cleanup_timer = threading.Timer(self.cleanup_interval, self._cleanup_callback)
            self._cleanup_timer.daemon = True
            self._cleanup_timer.start()

            log_timer_action("监测器清理", "启动", self.cleanup_interval)

        except Exception as e:
            log_error("启动清理定时器失败", error=e)

    def _stop_cleanup_timer(self):
        """停止清理定时器"""
        try:
            if self._cleanup_timer:
                self._cleanup_timer.cancel()
                self._cleanup_timer = None
                log_timer_action("监测器清理", "停止")

        except Exception as e:
            log_error("停止清理定时器失败", error=e)

    def _cleanup_callback(self):
        """清理回调"""
        try:
            if self.is_initialized:
                self._cleanup_idle_monitors()
                self._cleanup_old_events()

            # 重新启动定时器
            if self.is_initialized:
                self._start_cleanup_timer()

        except Exception as e:
            log_error("清理回调异常", error=e)
            # 即使出错也要重新启动定时器
            if self.is_initialized:
                self._start_cleanup_timer()

    def _cleanup_idle_monitors(self):
        """清理空闲的监控器"""
        try:
            with self._lock:
                idle_monitors = []

                for task_id, monitor in self._task_monitors.items():
                    if monitor.is_idle(self.idle_threshold) and not monitor.is_active:
                        idle_monitors.append(task_id)

                # 移除空闲监控器
                for task_id in idle_monitors:
                    del self._task_monitors[task_id]

                if idle_monitors:
                    log_info(f"清理了{len(idle_monitors)}个空闲监控器")

        except Exception as e:
            log_error("清理空闲监控器异常", error=e)

    def _cleanup_old_events(self):
        """清理旧的事件记录"""
        try:
            if len(self._monitor_events) > self.max_events_history:
                with self._lock:
                    # 保留最近的事件
                    keep_count = self.max_events_history // 2
                    removed_count = len(self._monitor_events) - keep_count
                    self._monitor_events = self._monitor_events[-keep_count:]

                    log_info(f"清理了{removed_count}条旧的事件记录")

        except Exception as e:
            log_error("清理旧事件记录异常", error=e)

    def reset_task_monitor(self, task_id: int) -> Dict[str, Any]:
        """重置任务监控器"""
        try:
            with self._lock:
                if task_id not in self._task_monitors:
                    return {
                        'success': False,
                        'message': f'任务{task_id}未在监控中',
                        'error_code': 'TASK_NOT_MONITORED'
                    }

                monitor = self._task_monitors[task_id]
                old_stats = monitor.to_dict()

                # 重置计数器
                monitor.sent_count = 0
                monitor.success_count = 0
                monitor.failed_count = 0
                monitor.last_alert_count = 0
                monitor.created_time = datetime.now()
                monitor.last_activity_time = datetime.now()

                log_info(f"重置任务{task_id}监控器")

                return {
                    'success': True,
                    'message': f'任务{task_id}监控器已重置',
                    'old_stats': old_stats,
                    'new_stats': monitor.to_dict()
                }

        except Exception as e:
            log_error(f"重置任务{task_id}监控器异常", error=e)
            return {
                'success': False,
                'message': f'重置异常: {str(e)}',
                'error_code': 'RESET_MONITOR_ERROR'
            }

    def batch_reset_monitors(self, task_ids: List[int] = None) -> Dict[str, Any]:
        """批量重置监控器"""
        try:
            with self._lock:
                target_ids = task_ids if task_ids else list(self._task_monitors.keys())
                reset_count = 0

                for task_id in target_ids:
                    if task_id in self._task_monitors:
                        monitor = self._task_monitors[task_id]
                        monitor.sent_count = 0
                        monitor.success_count = 0
                        monitor.failed_count = 0
                        monitor.last_alert_count = 0
                        monitor.created_time = datetime.now()
                        monitor.last_activity_time = datetime.now()
                        reset_count += 1

                log_info(f"批量重置了{reset_count}个监控器")

                return {
                    'success': True,
                    'message': f'批量重置了{reset_count}个监控器',
                    'reset_count': reset_count,
                    'target_count': len(target_ids)
                }

        except Exception as e:
            log_error("批量重置监控器异常", error=e)
            return {
                'success': False,
                'message': f'批量重置异常: {str(e)}',
                'error_code': 'BATCH_RESET_ERROR'
            }

    def export_monitor_data(self) -> Dict[str, Any]:
        """导出监控数据"""
        try:
            export_data = {
                'export_time': datetime.now().isoformat(),
                'statistics': self.get_monitoring_statistics(),
                'monitors': self.get_all_monitors(),
                'recent_events': self.get_monitor_events(100),
                'configuration': {
                    'default_alert_interval': self.default_alert_interval,
                    'default_monitor_phone': self.default_monitor_phone,
                    'cleanup_interval': self.cleanup_interval,
                    'idle_threshold': self.idle_threshold
                }
            }

            return {
                'success': True,
                'message': f'成功导出{len(self._task_monitors)}个监控器数据',
                'data': export_data,
                'data_size': len(str(export_data))
            }

        except Exception as e:
            log_error("导出监控数据异常", error=e)
            return {
                'success': False,
                'message': f'导出异常: {str(e)}',
                'error_code': 'EXPORT_DATA_ERROR'
            }

    def set_cleanup_interval(self, interval_seconds: int):
        """设置清理间隔"""
        try:
            if interval_seconds < 60:  # 最小1分钟
                interval_seconds = 60
            elif interval_seconds > 3600:  # 最大1小时
                interval_seconds = 3600

            old_interval = self.cleanup_interval
            self.cleanup_interval = interval_seconds

            # 重启清理定时器
            if self.is_initialized:
                self._stop_cleanup_timer()
                self._start_cleanup_timer()

            log_info(f"监测器清理间隔已更新: {old_interval}秒 -> {interval_seconds}秒")

        except Exception as e:
            log_error("设置清理间隔失败", error=e)

    def set_idle_threshold(self, threshold_seconds: int):
        """设置空闲阈值"""
        try:
            if threshold_seconds < 60:  # 最小1分钟
                threshold_seconds = 60
            elif threshold_seconds > 7200:  # 最大2小时
                threshold_seconds = 7200

            old_threshold = self.idle_threshold
            self.idle_threshold = threshold_seconds

            log_info(f"监测器空闲阈值已更新: {old_threshold}秒 -> {threshold_seconds}秒")

        except Exception as e:
            log_error("设置空闲阈值失败", error=e)

    def force_trigger_alert(self, task_id: int) -> Dict[str, Any]:
        """强制触发监测提醒"""
        try:
            with self._lock:
                if task_id not in self._task_monitors:
                    return {
                        'success': False,
                        'message': f'任务{task_id}未在监控中',
                        'error_code': 'TASK_NOT_MONITORED'
                    }

                monitor = self._task_monitors[task_id]

                # 强制触发提醒
                self._handle_monitor_alert(monitor)

                return {
                    'success': True,
                    'message': f'强制触发任务{task_id}监测提醒',
                    'task_id': task_id,
                    'monitor_info': monitor.to_dict()
                }

        except Exception as e:
            log_error(f"强制触发任务{task_id}提醒异常", error=e)
            return {
                'success': False,
                'message': f'强制触发异常: {str(e)}',
                'error_code': 'FORCE_ALERT_ERROR'
            }

    def get_task_progress_summary(self, task_id: int) -> Optional[Dict[str, Any]]:
        """获取任务进度摘要"""
        try:
            with self._lock:
                monitor = self._task_monitors.get(task_id)
                if not monitor:
                    return None

                # 计算进度信息
                messages_to_next_alert = monitor.alert_interval - (monitor.sent_count - monitor.last_alert_count)
                progress_percent = ((monitor.sent_count - monitor.last_alert_count) / monitor.alert_interval * 100) if monitor.alert_interval > 0 else 0

                return {
                    'task_id': task_id,
                    'task_name': monitor.task_name,
                    'current_count': monitor.sent_count,
                    'success_count': monitor.success_count,
                    'failed_count': monitor.failed_count,
                    'success_rate': monitor.get_success_rate(),
                    'last_alert_count': monitor.last_alert_count,
                    'messages_since_alert': monitor.sent_count - monitor.last_alert_count,
                    'messages_to_next_alert': max(0, messages_to_next_alert),
                    'progress_to_alert_percent': min(100, round(progress_percent, 2)),
                    'alert_interval': monitor.alert_interval,
                    'duration': monitor.get_duration(),
                    'is_active': monitor.is_active,
                    'last_activity': monitor.last_activity_time.isoformat()
                }

        except Exception as e:
            log_error(f"获取任务{task_id}进度摘要异常", error=e)
            return None

    def get_system_health_check(self) -> Dict[str, Any]:
        """获取系统健康检查"""
        try:
            with self._lock:
                health_info = {
                    'status': 'healthy',
                    'issues': [],
                    'warnings': [],
                    'recommendations': []
                }

                # 检查监控器数量
                if len(self._task_monitors) == 0:
                    health_info['warnings'].append('当前没有任何任务在监控中')

                # 检查空闲监控器
                idle_monitors = [m for m in self._task_monitors.values() if m.is_idle()]
                if idle_monitors:
                    health_info['warnings'].append(f'有{len(idle_monitors)}个监控器处于空闲状态')

                # 检查事件历史数量
                if len(self._monitor_events) > self.max_events_history * 0.8:
                    health_info['warnings'].append('事件历史记录接近上限，建议清理')

                # 检查监测号码
                if not self.default_monitor_phone:
                    health_info['warnings'].append('未设置默认监测号码')

                # 检查成功率
                stats = self.get_monitoring_statistics()
                if stats.get('overall_success_rate', 100) < 80:
                    health_info['issues'].append(f'整体成功率偏低: {stats.get("overall_success_rate", 0)}%')

                # 生成建议
                if health_info['warnings']:
                    health_info['recommendations'].append('定期清理空闲监控器和旧事件记录')

                if not self.default_monitor_phone:
                    health_info['recommendations'].append('设置默认监测号码以接收提醒')

                # 确定整体状态
                if health_info['issues']:
                    health_info['status'] = 'unhealthy'
                elif health_info['warnings']:
                    health_info['status'] = 'warning'

                return health_info

        except Exception as e:
            log_error("系统健康检查异常", error=e)
            return {
                'status': 'error',
                'issues': [f'健康检查异常: {str(e)}'],
                'warnings': [],
                'recommendations': []
            }


# 全局监测检测器实例
monitor_detector = MonitorDetector()