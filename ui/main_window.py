"""
主窗口 - 三区域布局（状态栏、任务列表、端口网格）
"""

import tkinter as tk
from tkinter import messagebox
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.styles import get_color, get_font
from ui.components import StatusBar, TaskListWidget, PortGridWidget, TimerWidget
from ui.dialogs import (AddTaskDialog, TaskTestDialog, TaskEditDialog,
                       ConfigDialog, ExportDialog)


class MainWindow:
    """主窗口类"""

    def __init__(self, user_info):
        self.user_info = user_info
        self.root = tk.Tk()
        self.setup_window()
        self.create_widgets()
        self.setup_timer()

    def setup_window(self):
        """设置窗口属性"""
        self.root.title("Pulsesports 1.9.0-rc.1-直发")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 600)

        # 设置窗口居中
        self.center_window()

        # 设置背景色
        self.root.configure(bg=get_color('background'))

        # 设置窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def center_window(self):
        """窗口居中显示"""
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (1200 // 2)
        y = (self.root.winfo_screenheight() // 2) - (800 // 2)
        self.root.geometry(f"1200x800+{x}+{y}")

    def create_widgets(self):
        """创建界面组件"""
        # 创建状态栏（顶部）
        self.status_bar = StatusBar(self.root, self.user_info)

        # 创建主内容区域
        self.create_main_content()

    def create_main_content(self):
        """创建主内容区域"""
        # 主内容容器
        main_frame = tk.Frame(self.root, bg=get_color('background'))
        main_frame.pack(fill='both', expand=True)

        # 创建左右分割的面板
        # 左侧：任务列表（占40%宽度）
        left_frame = tk.Frame(main_frame, bg=get_color('background'), width=480)
        left_frame.pack(side='left', fill='both', expand=False)
        left_frame.pack_propagate(False)  # 固定宽度

        # 右侧：端口网格（占60%宽度）
        right_frame = tk.Frame(main_frame, bg=get_color('background'))
        right_frame.pack(side='right', fill='both', expand=True)

        # 创建任务列表组件
        self.task_list = TaskListWidget(
            left_frame,
            self.user_info,
            on_task_select=self.on_task_select,
            on_task_update=self.on_task_update
        )
        self.task_list.get_frame().pack(fill='both', expand=True)

        # 创建端口网格组件
        self.port_grid = PortGridWidget(
            right_frame,
            self.user_info,
            on_port_select=self.on_port_select
        )
        self.port_grid.get_frame().pack(fill='both', expand=True)

    def setup_timer(self):
        """设置定时器"""
        self.timer = TimerWidget(
            task_list_widget=self.task_list,
            port_grid_widget=self.port_grid,
            status_bar=self.status_bar,
            interval=300  # 5分钟更新间隔
        )
        self.timer.start()

    def on_task_select(self, task):
        """任务选择回调"""
        print(f"选中任务: {task.get('title', task.get('id'))}")

    def on_task_update(self, action, task):
        """任务更新回调"""
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

    def on_port_select(self, ports):
        """端口选择回调"""
        port_names = [p.get('name', f"COM{p.get('id')}") for p in ports]
        print(f"选中端口: {port_names}")

    def show_add_task_dialog(self):
        """显示添加任务对话框"""
        try:
            dialog = AddTaskDialog(self.root, self.user_info)
            result = dialog.show()
            if result:
                messagebox.showinfo("成功", "任务创建成功！")
                self.task_list.refresh_tasks()
                self.status_bar.update_balance(result.get('new_balance', self.user_info.get('balance')))
        except Exception as e:
            messagebox.showerror("错误", f"创建任务失败：{str(e)}")

    def show_task_test_dialog(self, task):
        """显示任务测试对话框"""
        try:
            dialog = TaskTestDialog(self.root, task)
            result = dialog.show()
            if result:
                messagebox.showinfo("测试完成", f"测试结果：{result.get('message', '测试成功')}")
        except Exception as e:
            messagebox.showerror("错误", f"任务测试失败：{str(e)}")

    def show_task_edit_dialog(self, task):
        """显示任务编辑对话框"""
        try:
            dialog = TaskEditDialog(self.root, task)
            result = dialog.show()
            if result:
                messagebox.showinfo("成功", "任务内容已更新！")
                self.task_list.refresh_tasks()
        except Exception as e:
            messagebox.showerror("错误", f"修改任务失败：{str(e)}")

    def show_export_dialog(self, task, export_type):
        """显示导出对话框"""
        try:
            dialog = ExportDialog(self.root, task, export_type)
            result = dialog.show()
            if result:
                messagebox.showinfo("成功", f"导出完成：{result.get('file_path', '')}")
        except Exception as e:
            messagebox.showerror("错误", f"导出失败：{str(e)}")

    def show_config_dialog(self):
        """显示配置对话框"""
        try:
            dialog = ConfigDialog(self.root)
            result = dialog.show()
            if result:
                messagebox.showinfo("成功", "配置已保存！")
        except Exception as e:
            messagebox.showerror("错误", f"配置失败：{str(e)}")

    def on_closing(self):
        """窗口关闭事件"""
        if messagebox.askyesno("确认退出", "确定要退出程序吗？"):
            # 停止定时器
            if hasattr(self, 'timer'):
                self.timer.stop()
            self.root.quit()

    def show(self):
        """显示主窗口"""
        self.root.mainloop()

    def destroy(self):
        """销毁窗口"""
        if hasattr(self, 'timer'):
            self.timer.stop()
        self.root.destroy()


def main():
    """测试主窗口"""
    # 模拟用户信息
    user_info = {
        'id': 1,
        'username': 'test_user',
        'balance': 10000,
        'role': 'channel_user'
    }

    # 创建并显示主窗口
    main_window = MainWindow(user_info)
    main_window.show()
    main_window.destroy()


if __name__ == '__main__':
    main()