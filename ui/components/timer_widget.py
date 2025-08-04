"""
定时器组件 - 五分钟自动更新数据
"""

import tkinter as tk
import threading
import time
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from services.task_service import TaskService
from services.port_service import PortService


class TimerWidget:
    """定时器组件"""

    def __init__(self, task_list_widget=None, port_grid_widget=None, status_bar=None, interval=300):
        """
        初始化定时器组件

        Args:
            task_list_widget: 任务列表组件
            port_grid_widget: 端口网格组件
            status_bar: 状态栏组件
            interval: 更新间隔（秒），默认300秒（5分钟）
        """
        self.task_list_widget = task_list_widget
        self.port_grid_widget = port_grid_widget
        self.status_bar = status_bar
        self.interval = interval
        self.running = False
        self.timer_thread = None
        self.task_service = TaskService()
        self.port_service = PortService()

    def start(self):
        """开始定时器"""
        if not self.running:
            self.running = True
            self.timer_thread = threading.Thread(target=self._timer_loop, daemon=True)
            self.timer_thread.start()
            print(f"定时器已启动，更新间隔：{self.interval}秒")

    def stop(self):
        """停止定时器"""
        self.running = False
        if self.timer_thread and self.timer_thread.is_alive():
            self.timer_thread.join(timeout=1)
        print("定时器已停止")

    def _timer_loop(self):
        """定时器循环"""
        while self.running:
            try:
                # 等待指定间隔
                for _ in range(self.interval):
                    if not self.running:
                        break
                    time.sleep(1)

                if self.running:
                    # 执行更新操作
                    self._update_data()

            except Exception as e:
                print(f"定时器更新数据时发生错误：{str(e)}")

    def _update_data(self):
        """更新数据"""
        print("执行定时更新...")

        # 更新任务列表
        if self.task_list_widget:
            try:
                self._update_task_list()
            except Exception as e:
                print(f"更新任务列表失败：{str(e)}")

        # 更新端口状态
        if self.port_grid_widget:
            try:
                self._update_port_status()
            except Exception as e:
                print(f"更新端口状态失败：{str(e)}")

        # 更新用户余额
        if self.status_bar:
            try:
                self._update_user_balance()
            except Exception as e:
                print(f"更新用户余额失败：{str(e)}")

    def _update_task_list(self):
        """更新任务列表数据"""
        if hasattr(self.task_list_widget, 'user_info'):
            user_id = self.task_list_widget.user_info.get('id')
            if user_id:
                # 获取最新任务数据
                result = self.task_service.get_user_tasks(user_id)
                if result['success']:
                    # 更新任务进度
                    for task in result['tasks']:
                        task_id = task.get('id')
                        progress_data = {
                            'progress': task.get('progress', 0),
                            'sent': task.get('sent', 0),
                            'total': task.get('total', 0),
                            'success_count': task.get('success_count', 0),
                            'failed_count': task.get('failed_count', 0),
                            'status': task.get('status', 'stopped')
                        }

                        # 在主线程中更新UI
                        if hasattr(self.task_list_widget, 'task_tree'):
                            self.task_list_widget.task_tree.after(
                                0,
                                lambda tid=task_id, data=progress_data:
                                self.task_list_widget.update_task_progress(tid, data)
                            )

    def _update_port_status(self):
        """更新端口状态数据"""
        # 获取最新端口数据
        result = self.port_service.get_ports()
        if result['success']:
            ports = result['ports']

            # 更新端口状态
            for port in ports:
                port_id = port.get('id')
                status_data = {
                    'success_count': port.get('success_count', 0),
                    'failed_count': port.get('failed_count', 0),
                    'status': port.get('status', 'idle')
                }

                # 在主线程中更新UI
                if hasattr(self.port_grid_widget, 'port_frames'):
                    self.port_grid_widget.canvas.after(
                        0,
                        lambda pid=port_id, data=status_data:
                        self.port_grid_widget.update_port_status(pid, data)
                    )

    def _update_user_balance(self):
        """更新用户余额"""
        if hasattr(self.status_bar, 'user_info'):
            user_id = self.status_bar.user_info.get('id')
            if user_id:
                try:
                    # 这里应该调用用户服务获取最新余额
                    # result = self.user_service.get_user_balance(user_id)
                    # 暂时模拟余额变化
                    import random
                    current_balance = self.status_bar.user_info.get('balance', 10000)
                    # 模拟余额小幅变化
                    new_balance = max(0, current_balance + random.randint(-100, 50))

                    # 在主线程中更新UI
                    if hasattr(self.status_bar, 'balance_label'):
                        self.status_bar.balance_label.after(
                            0,
                            lambda balance=new_balance: self.status_bar.update_balance(balance)
                        )

                except Exception as e:
                    print(f"更新用户余额失败：{str(e)}")

    def force_update(self):
        """强制立即更新一次"""
        if self.running:
            threading.Thread(target=self._update_data, daemon=True).start()

    def set_interval(self, interval):
        """设置更新间隔"""
        self.interval = max(60, interval)  # 最小间隔1分钟
        print(f"定时器间隔已设置为：{self.interval}秒")

    def is_running(self):
        """检查定时器是否正在运行"""
        return self.running


class TimerManager:
    """定时器管理器"""

    def __init__(self):
        self.timers = {}

    def add_timer(self, name, timer_widget):
        """添加定时器"""
        self.timers[name] = timer_widget

    def start_timer(self, name):
        """启动指定定时器"""
        if name in self.timers:
            self.timers[name].start()

    def stop_timer(self, name):
        """停止指定定时器"""
        if name in self.timers:
            self.timers[name].stop()

    def start_all(self):
        """启动所有定时器"""
        for timer in self.timers.values():
            timer.start()

    def stop_all(self):
        """停止所有定时器"""
        for timer in self.timers.values():
            timer.stop()

    def force_update_all(self):
        """强制更新所有定时器"""
        for timer in self.timers.values():
            timer.force_update()


def main():
    """测试定时器组件"""