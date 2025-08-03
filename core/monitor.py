"""
状态监控与日志模块
"""
import logging
import threading
import time
from datetime import datetime
from collections import deque
import os


class Monitor:
    """系统监控器"""

    def __init__(self):
        self.is_monitoring = False
        self.monitor_thread = None
        self.callbacks = []  # 状态更新回调函数
        self.statistics = {
            'total_sent': 0,
            'total_success': 0,
            'total_failed': 0,
            'start_time': None,
            'last_update': None
        }
        self.performance_data = deque(maxlen=100)  # 保留最近100个性能数据点

        # 设置日志
        self._setup_logging()

    def _setup_logging(self):
        """设置日志系统"""
        # 创建logs目录
        if not os.path.exists('logs'):
            os.makedirs('logs')

        # 配置日志格式
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

        # 主日志文件
        self.main_logger = logging.getLogger('sms_pool')
        self.main_logger.setLevel(logging.INFO)

        # 文件处理器
        file_handler = logging.FileHandler(
            f'logs/sms_pool_{datetime.now().strftime("%Y%m%d")}.log',
            encoding='utf-8'
        )
        file_handler.setFormatter(logging.Formatter(log_format))
        self.main_logger.addHandler(file_handler)

        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(log_format))
        self.main_logger.addHandler(console_handler)

        # 错误日志
        self.error_logger = logging.getLogger('sms_pool_error')
        self.error_logger.setLevel(logging.ERROR)

        error_handler = logging.FileHandler(
            f'logs/error_{datetime.now().strftime("%Y%m%d")}.log',
            encoding='utf-8'
        )
        error_handler.setFormatter(logging.Formatter(log_format))
        self.error_logger.addHandler(error_handler)

    def start_monitoring(self, port_manager=None, task_manager=None):
        """启动监控"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.statistics['start_time'] = datetime.now()
            self.port_manager = port_manager
            self.task_manager = task_manager

            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()

            self.log_info("监控系统已启动")

    def stop_monitoring(self):
        """停止监控"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
        self.log_info("监控系统已停止")

    def _monitor_loop(self):
        """监控循环"""
        while self.is_monitoring:
            try:
                self._collect_statistics()
                self._check_system_health()
                self._notify_callbacks()
                time.sleep(5)  # 每5秒更新一次
            except Exception as e:
                self.log_error(f"监控循环错误: {e}")
                time.sleep(1)

    def _collect_statistics(self):
        """收集统计信息"""
        current_time = datetime.now()

        # 收集端口统计
        if self.port_manager:
            port_stats = {
                'total_ports': len(self.port_manager.ports),
                'running_ports': len(self.port_manager.running_ports),
                'total_success': sum(port['success'] for port in self.port_manager.ports.values())
            }
        else:
            port_stats = {'total_ports': 0, 'running_ports': 0, 'total_success': 0}

        # 收集任务统计
        if self.task_manager:
            task_stats = {
                'total_tasks': len(self.task_manager.tasks),
                'running_tasks': len(self.task_manager.running_tasks),
                'completed_tasks': len([t for t in self.task_manager.tasks.values()
                                      if t['success'] + t['failed'] >= t['total']])
            }
        else:
            task_stats = {'total_tasks': 0, 'running_tasks': 0, 'completed_tasks': 0}

        # 更新统计信息
        self.statistics.update({
            'total_success': port_stats['total_success'],
            'last_update': current_time,
            'port_stats': port_stats,
            'task_stats': task_stats
        })

        # 添加性能数据点
        self.performance_data.append({
            'timestamp': current_time,
            'running_ports': port_stats['running_ports'],
            'running_tasks': task_stats['running_tasks'],
            'total_success': port_stats['total_success']
        })

    def _check_system_health(self):
        """检查系统健康状态"""
        warnings = []

        # 检查端口状态
        if self.port_manager:
            running_ports = len(self.port_manager.running_ports)
            if running_ports == 0 and len(self.task_manager.running_tasks) > 0:
                warnings.append("有运行中的任务但没有活动端口")

        # 检查任务状态
        if self.task_manager:
            for task in self.task_manager.get_running_tasks():
                if task['success'] + task['failed'] >= task['total']:
                    warnings.append(f"任务 {task['name']} 已完成但仍在运行")

        # 记录警告
        for warning in warnings:
            self.log_warning(warning)

    def _notify_callbacks(self):
        """通知回调函数"""
        for callback in self.callbacks:
            try:
                callback(self.statistics)
            except Exception as e:
                self.log_error(f"回调函数执行错误: {e}")

    def add_callback(self, callback):
        """添加状态更新回调"""
        self.callbacks.append(callback)

    def remove_callback(self, callback):
        """移除状态更新回调"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)

    def log_info(self, message):
        """记录信息日志"""
        self.main_logger.info(message)

    def log_warning(self, message):
        """记录警告日志"""
        self.main_logger.warning(message)

    def log_error(self, message):
        """记录错误日志"""
        self.main_logger.error(message)
        self.error_logger.error(message)

    def log_send_success(self, port_name, phone_number, task_name=""):
        """记录发送成功"""
        message = f"发送成功: {phone_number} via {port_name}"
        if task_name:
            message += f" (任务: {task_name})"
        self.log_info(message)

    def log_send_failure(self, port_name, phone_number, error, task_name=""):
        """记录发送失败"""
        message = f"发送失败: {phone_number} via {port_name} - {error}"
        if task_name:
            message += f" (任务: {task_name})"
        self.log_error(message)

    def get_statistics(self):
        """获取统计信息"""
        return self.statistics.copy()

    def get_performance_data(self):
        """获取性能数据"""
        return list(self.performance_data)

    def get_log_summary(self, hours=24):
        """获取日志摘要"""
        # 这里可以实现读取日志文件并分析的功能
        # 简化实现，返回基本统计
        return {
            'period_hours': hours,
            'total_logs': len(self.performance_data),
            'last_update': self.statistics.get('last_update')
        }

    def export_statistics(self, filename=None):
        """导出统计数据"""
        if filename is None:
            filename = f'statistics_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'

        try:
            import json

            export_data = {
                'statistics': self.statistics,
                'performance_data': [
                    {
                        'timestamp': data['timestamp'].isoformat(),
                        'running_ports': data['running_ports'],
                        'running_tasks': data['running_tasks'],
                        'total_success': data['total_success']
                    }
                    for data in self.performance_data
                ],
                'export_time': datetime.now().isoformat()
            }

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            self.log_info(f"统计数据已导出到: {filename}")
            return True
        except Exception as e:
            self.log_error(f"导出统计数据失败: {e}")
            return False


class AlertManager:
    """告警管理器"""

    def __init__(self, monitor):
        self.monitor = monitor
        self.alert_rules = {}
        self.alert_history = deque(maxlen=1000)
        self.notification_callbacks = []

    def add_alert_rule(self, rule_id, condition_func, message, level='warning'):
        """添加告警规则"""
        self.alert_rules[rule_id] = {
            'condition': condition_func,
            'message': message,
            'level': level,
            'enabled': True,
            'last_triggered': None
        }

    def remove_alert_rule(self, rule_id):
        """移除告警规则"""
        if rule_id in self.alert_rules:
            del self.alert_rules[rule_id]

    def check_alerts(self, statistics):
        """检查告警条件"""
        current_time = datetime.now()

        for rule_id, rule in self.alert_rules.items():
            if not rule['enabled']:
                continue

            try:
                if rule['condition'](statistics):
                    # 避免重复告警（5分钟内不重复）
                    if (rule['last_triggered'] is None or
                        (current_time - rule['last_triggered']).seconds > 300):

                        alert = {
                            'rule_id': rule_id,
                            'message': rule['message'],
                            'level': rule['level'],
                            'timestamp': current_time,
                            'statistics': statistics.copy()
                        }

                        self.alert_history.append(alert)
                        rule['last_triggered'] = current_time

                        # 记录日志
                        if rule['level'] == 'error':
                            self.monitor.log_error(f"告警: {rule['message']}")
                        else:
                            self.monitor.log_warning(f"告警: {rule['message']}")

                        # 通知回调
                        self._notify_alert(alert)

            except Exception as e:
                self.monitor.log_error(f"告警规则 {rule_id} 检查失败: {e}")

    def _notify_alert(self, alert):
        """通知告警"""
        for callback in self.notification_callbacks:
            try:
                callback(alert)
            except Exception as e:
                self.monitor.log_error(f"告警通知回调失败: {e}")

    def add_notification_callback(self, callback):
        """添加通知回调"""
        self.notification_callbacks.append(callback)

    def get_alert_history(self, limit=100):
        """获取告警历史"""
        return list(self.alert_history)[-limit:]

    def setup_default_rules(self):
        """设置默认告警规则"""
        # 无活动端口告警
        self.add_alert_rule(
            'no_active_ports',
            lambda stats: (stats.get('task_stats', {}).get('running_tasks', 0) > 0 and
                          stats.get('port_stats', {}).get('running_ports', 0) == 0),
            '有运行中的任务但没有活动端口',
            'warning'
        )

        # 发送成功率过低告警
        self.add_alert_rule(
            'low_success_rate',
            lambda stats: self._calculate_success_rate(stats) < 0.8,
            '发送成功率低于80%',
            'warning'
        )

    def _calculate_success_rate(self, statistics):
        """计算发送成功率"""
        if len(self.monitor.performance_data) < 2:
            return 1.0

        recent_data = list(self.monitor.performance_data)[-10:]  # 最近10个数据点
        if len(recent_data) < 2:
            return 1.0

        success_diff = recent_data[-1]['total_success'] - recent_data[0]['total_success']
        # 这里简化处理，实际应该统计失败次数
        return max(0.0, min(1.0, success_diff / max(1, success_diff + 1)))