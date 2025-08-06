"""
完整主窗口 - 集成所有UI组件
"""
import tkinter as tk
from tkinter import messagebox
from typing import Dict, Any
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入UI组件
from ui.components.status_bar import StatusBar
from ui.components.task_list_widget import TaskListWidget
from ui.components.port_grid_widget import PortGridWidget
from ui.components.timer_widget import TimerWidget, TimerManager

# 导入对话框
from ui.dialogs.add_task_dialog import AddTaskDialog
from ui.dialogs.task_test_dialog import TaskTestDialog
from ui.dialogs.task_edit_dialog import TaskEditDialog
from ui.dialogs.config_dialog import ConfigDialog
from ui.dialogs.export_dialog import ExportDialog

# 导入样式
from ui.styles import get_color, get_font


class MainWindow:
    """完整主窗口类"""

    def __init__(self, user_info: Dict[str, Any]):
        """初始化主窗口"""
        self.user_info = user_info
        self.root = None
        self.status_bar = None
        self.task_list_widget = None
        self.port_grid_widget = None
        self.timer_manager = TimerManager()

        # 重新映射用户信息字段
        self.normalized_user_info = self.normalize_user_info(user_info)

    def normalize_user_info(self, user_info: Dict[str, Any]) -> Dict[str, Any]:
        """标准化用户信息字段名"""
        return {
            'id': user_info.get('operators_id', user_info.get('id', 1)),
            'username': user_info.get('operators_username', user_info.get('username', 'Unknown')),
            'real_name': user_info.get('operators_real_name', user_info.get('real_name', '用户')),
            'balance': user_info.get('operators_available_credits', user_info.get('balance', 10000)),
            'channel_id': user_info.get('channel_users_id', user_info.get('channel_id', 1))
        }

    def show(self):
        """显示主窗口"""
        self.root = tk.Tk()
        self.root.title(f"Pulsesports 1.9.0-rc.1-首发 - {self.normalized_user_info.get('real_name', '用户')}")
        self.root.geometry("1200x800")
        self.root.configure(bg=get_color('background'))

        # 设置窗口图标（如果有的话）
        try:
            # self.root.iconbitmap('static/icons/logo.ico')  # 如果有图标文件
            pass
        except:
            pass

        # 居中显示
        self.center_window()

        # 创建界面
        self.create_widgets()

        # 启动定时器
        self.start_timers()

        # 绑定关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # 运行窗口
        self.root.mainloop()

    def center_window(self):
        """窗口居中"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def create_widgets(self):
        """创建界面组件"""
        # 1. 创建状态栏（顶部）
        self.status_bar = StatusBar(self.root, self.normalized_user_info)

        # 2. 创建主内容区域
        main_frame = tk.Frame(self.root, bg=get_color('background'))
        main_frame.pack(fill='both', expand=True)

        # 3. 创建左侧任务管理区域
        left_frame = tk.Frame(main_frame, bg=get_color('background'))
        left_frame.pack(side='left', fill='both', expand=True, padx=(10, 5), pady=10)

        self.task_list_widget = TaskListWidget(
            left_frame,
            self.normalized_user_info,
            on_task_select=self.on_task_select,
            on_task_update=self.on_task_update
        )
        self.task_list_widget.get_frame().pack(fill='both', expand=True)

        # 4. 创建右侧端口管理区域
        right_frame = tk.Frame(main_frame, bg=get_color('background'))
        right_frame.pack(side='right', fill='both', expand=True, padx=(5, 10), pady=10)

        self.port_grid_widget = PortGridWidget(
            right_frame,
            self.normalized_user_info,
            on_port_select=self.on_port_select
        )
        self.port_grid_widget.get_frame().pack(fill='both', expand=True)

    def on_task_select(self, task):
        """任务选择回调"""
        print(f"选中任务: {task.get('title', task.get('id', 'Unknown'))}")

    def on_task_update(self, action, task):
        """任务更新回调"""
        try:
            if action == 'add':
                self.show_add_task_dialog()
            elif action == 'test':
                self.show_task_test_dialog(task)
            elif action == 'edit':
                self.show_task_edit_dialog(task)
            elif action == 'export_completed':
                self.show_export_dialog(task, 'completed')
            elif action == 'export_uncompleted':
                self.show_export_dialog(task, 'uncompleted')
            elif action == 'export_report':
                self.show_export_dialog(None, 'report')
        except Exception as e:
            messagebox.showerror("错误", f"操作失败：{str(e)}")

    def on_port_select(self, ports):
        """端口选择回调"""
        port_names = [p.get('name', f"COM{p.get('id', '')}") for p in ports]
        print(f"选中端口: {port_names}")

    def show_add_task_dialog(self):
        """显示添加任务对话框"""
        try:
            dialog = AddTaskDialog(self.root, self.normalized_user_info)
            result = dialog.show()
            if result:
                messagebox.showinfo("成功", "任务创建成功！")
                # 刷新任务列表
                if self.task_list_widget:
                    self.task_list_widget.refresh_tasks()
                # 更新余额
                self.refresh_balance()
        except Exception as e:
            messagebox.showerror("错误", f"打开添加任务对话框失败：{str(e)}")

    def show_task_test_dialog(self, task):
        """显示任务测试对话框"""
        try:
            dialog = TaskTestDialog(self.root, task)
            result = dialog.show()
            if result:
                messagebox.showinfo("测试完成", "任务测试完成！")
        except Exception as e:
            messagebox.showerror("错误", f"打开任务测试对话框失败：{str(e)}")

    def show_task_edit_dialog(self, task):
        """显示任务编辑对话框"""
        try:
            dialog = TaskEditDialog(self.root, task)
            result = dialog.show()
            if result:
                messagebox.showinfo("成功", "任务内容已更新！")
                # 刷新任务列表
                if self.task_list_widget:
                    self.task_list_widget.refresh_tasks()
        except Exception as e:
            messagebox.showerror("错误", f"打开任务编辑对话框失败：{str(e)}")

    def show_config_dialog(self):
        """显示配置对话框"""
        try:
            dialog = ConfigDialog(self.root)
            result = dialog.show()
            if result:
                messagebox.showinfo("成功", "配置已保存！")
        except Exception as e:
            messagebox.showerror("错误", f"打开配置对话框失败：{str(e)}")

    def show_export_dialog(self, task, export_type):
        """显示导出对话框"""
        try:
            dialog = ExportDialog(self.root, task, export_type)
            result = dialog.show()
            if result:
                messagebox.showinfo("成功", "数据导出完成！")
        except Exception as e:
            messagebox.showerror("错误", f"打开导出对话框失败：{str(e)}")

    def start_timers(self):
        """启动定时器"""
        try:
            # 创建主定时器
            main_timer = TimerWidget(
                task_list_widget=self.task_list_widget,
                port_grid_widget=self.port_grid_widget,
                status_bar=self.status_bar,
                interval=300  # 5分钟更新一次
            )

            # 添加到定时器管理器
            self.timer_manager.add_timer('main', main_timer)

            # 启动定时器
            self.timer_manager.start_timer('main')

            print("定时器已启动")
        except Exception as e:
            print(f"启动定时器失败：{str(e)}")

    def refresh_balance(self):
        """刷新用户余额"""
        try:
            # 这里应该调用用户服务获取最新余额
            # 暂时保持现有余额
            if self.status_bar:
                current_balance = self.normalized_user_info.get('balance', 10000)
                self.status_bar.update_balance(current_balance)
        except Exception as e:
            print(f"刷新余额失败：{str(e)}")

    def on_closing(self):
        """窗口关闭事件"""
        try:
            # 停止所有定时器
            self.timer_manager.stop_all()

            # 确认关闭
            if messagebox.askyesno("确认退出", "确定要退出系统吗？"):
                self.destroy()
        except Exception as e:
            print(f"关闭窗口时发生错误：{str(e)}")
            self.destroy()

    def destroy(self):
        """销毁窗口"""
        if self.root:
            try:
                self.root.quit()
                self.root.destroy()
            except:
                pass


def main():
    """测试完整主窗口"""
    # 模拟用户信息
    user_info = {
        'operators_id': 1,
        'operators_username': 'test_operator',
        'operators_real_name': '测试操作员',
        'operators_available_credits': 10000,
        'channel_users_id': 1
    }

    # 创建并显示主窗口
    main_window = MainWindow(user_info)
    main_window.show()


if __name__ == '__main__':
    main()