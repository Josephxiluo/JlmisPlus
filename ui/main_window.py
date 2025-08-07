"""
修复版现代化主窗口 - 可调整的分割窗口
"""
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from typing import Dict, Any
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入现代化UI组件
from ui.styles import get_color, get_font, get_spacing, create_label
from ui.components.timer_widget import TimerWidget, TimerManager

# 导入对话框
from ui.dialogs.add_task_dialog import AddTaskDialog
from ui.dialogs.task_test_dialog import TaskTestDialog
from ui.dialogs.task_edit_dialog import TaskEditDialog
from ui.dialogs.config_dialog import ConfigDialog
from ui.dialogs.export_dialog import ExportDialog


class MainWindow:
    """修复版现代化主窗口类 - 可调整分割窗口"""

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
        self.root = ctk.CTk()
        self.root.title(f"JlmisPlus 1.015 - 测试学习系统")
        self.root.geometry("1400x900")
        self.root.configure(fg_color=get_color('background'))

        # 设置最小窗口大小
        self.root.minsize(1200, 800)

        # 居中显示
        self.center_window()

        # 创建现代化界面
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
        """创建现代化界面组件"""
        # 1. 创建状态栏（顶部）
        from ui.components.status_bar import StatusBar
        self.status_bar = StatusBar(self.root, self.normalized_user_info)

        # 2. 创建主内容区域容器
        main_container = ctk.CTkFrame(self.root, fg_color='transparent')
        main_container.pack(fill='both', expand=True)

        # 添加内边距容器
        content_frame = ctk.CTkFrame(main_container, fg_color='transparent')
        content_frame.pack(fill='both', expand=True,
                          padx=get_spacing('lg'), pady=get_spacing('md'))

        # 3. 创建可调整的分割窗口布局（使用原生tkinter的PanedWindow）
        self.create_resizable_paned_layout(content_frame)

        # 4. 添加底部状态信息
        self.create_bottom_status()

    def create_resizable_paned_layout(self, parent):
        """创建可调整大小的分割窗口布局"""
        # 使用tkinter的PanedWindow来实现可拖拽调整
        self.paned_window = tk.PanedWindow(
            parent,
            orient=tk.HORIZONTAL,
            sashwidth=8,
            sashrelief='flat',
            sashpad=2,
            bg=get_color('background'),
            bd=0,
            relief='flat'
        )
        self.paned_window.pack(fill='both', expand=True)

        # 左侧面板容器（任务管理）
        left_container = ctk.CTkFrame(
            self.paned_window,
            fg_color='transparent'
        )

        # 右侧面板容器（端口管理）
        right_container = ctk.CTkFrame(
            self.paned_window,
            fg_color='transparent'
        )

        # 创建任务列表组件
        from ui.components.task_list_widget import TaskListWidget
        self.task_list_widget = TaskListWidget(
            left_container,
            self.normalized_user_info,
            on_task_select=self.on_task_select,
            on_task_update=self.on_task_update
        )
        self.task_list_widget.get_frame().pack(fill='both', expand=True)

        # 创建端口网格组件
        from ui.components.port_grid_widget import PortGridWidget
        self.port_grid_widget = PortGridWidget(
            right_container,
            self.normalized_user_info,
            on_port_select=self.on_port_select
        )
        self.port_grid_widget.get_frame().pack(fill='both', expand=True)

        # 添加到分割窗口
        self.paned_window.add(left_container, minsize=500)  # 左侧最小400px
        self.paned_window.add(right_container, minsize=500)  # 右侧最小600px

        # 设置初始分割位置（左侧50%，右侧50%）
        self.root.after(100, self.set_initial_paned_position)

    def set_initial_paned_position(self):
        """设置初始分割位置"""
        try:
            # 获取窗口宽度
            total_width = self.paned_window.winfo_width()
            if total_width > 100:  # 确保窗口已经完全加载
                # 设置左侧占50%
                left_width = int(total_width * 0.5)
                self.paned_window.sash_place(0, left_width, 0)
            else:
                # 如果窗口还没完全加载，延迟执行
                self.root.after(100, self.set_initial_paned_position)
        except Exception as e:
            print(f"设置分割位置时发生错误: {e}")

    def create_bottom_status(self):
        """创建现代化底部状态栏"""
        bottom_frame = ctk.CTkFrame(
            self.root,
            fg_color=get_color('gray_light'),
            corner_radius=0,
            height=30
        )
        bottom_frame.pack(fill='x', side='bottom')
        bottom_frame.pack_propagate(False)

        # 底部状态容器
        status_container = ctk.CTkFrame(bottom_frame, fg_color='transparent')
        status_container.pack(fill='both', expand=True, padx=get_spacing('md'), pady=get_spacing('xs'))

        # 版本信息（左侧）
        version_label = create_label(
            status_container,
            text="JlmisPlus 1.015 - CustomTkinter现代化版本",
            style="small"
        )
        version_label.configure(text_color=get_color('text_light'))
        version_label.pack(side='left')

        # 拖拽提示（中间）
        hint_label = create_label(
            status_container,
            text="💡 拖拽中间分割线可调整左右面板大小",
            style="small"
        )
        hint_label.configure(text_color=get_color('primary'))
        hint_label.pack(side='left', padx=get_spacing('xl'))

        # 连接状态（右侧）
        self.connection_status = create_label(
            status_container,
            text="🟢 已连接",
            style="small"
        )
        self.connection_status.configure(text_color=get_color('success'))
        self.connection_status.pack(side='right')

    def on_task_select(self, task):
        """任务选择回调"""
        print(f"选中任务: {task.get('title', task.get('id', 'Unknown'))}")

    def on_task_update(self, action, task):
        """任务更新回调 - 处理各种任务操作"""
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
                self.show_success_message("任务创建成功！")
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
                self.show_success_message("任务测试完成！")
        except Exception as e:
            messagebox.showerror("错误", f"打开任务测试对话框失败：{str(e)}")

    def show_task_edit_dialog(self, task):
        """显示任务编辑对话框"""
        try:
            dialog = TaskEditDialog(self.root, task)
            result = dialog.show()
            if result:
                self.show_success_message("任务内容已更新！")
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
                self.show_success_message("配置已保存！")
        except Exception as e:
            messagebox.showerror("错误", f"打开配置对话框失败：{str(e)}")

    def show_export_dialog(self, task, export_type):
        """显示导出对话框"""
        try:
            dialog = ExportDialog(self.root, task, export_type)
            result = dialog.show()
            if result:
                self.show_success_message("数据导出完成！")
        except Exception as e:
            messagebox.showerror("错误", f"打开导出对话框失败：{str(e)}")

    def show_success_message(self, message):
        """显示成功消息 - 使用现代化消息框"""
        # 创建现代化成功提示窗口
        success_window = ctk.CTkToplevel(self.root)
        success_window.title("操作成功")
        success_window.geometry("350x150")
        success_window.configure(fg_color=get_color('background'))
        success_window.transient(self.root)
        success_window.grab_set()

        # 居中显示
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 175
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 75
        success_window.geometry(f"350x150+{x}+{y}")

        # 成功图标和消息
        content_frame = ctk.CTkFrame(success_window, fg_color='transparent')
        content_frame.pack(fill='both', expand=True, padx=20, pady=20)

        # 成功图标
        icon_label = create_label(
            content_frame,
            text="✅",
            style="large"
        )
        icon_label.pack(pady=(0, 10))

        # 成功消息
        message_label = create_label(
            content_frame,
            text=message,
            style="default"
        )
        message_label.pack(pady=(0, 15))

        # 确定按钮
        ok_button = ctk.CTkButton(
            content_frame,
            text="确定",
            command=success_window.destroy,
            font=get_font('button'),
            fg_color=get_color('success'),
            hover_color='#45A049',
            width=100,
            height=32
        )
        ok_button.pack()

        # 3秒后自动关闭
        success_window.after(3000, success_window.destroy)

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
            if self.status_bar:
                current_balance = self.normalized_user_info.get('balance', 10000)
                self.status_bar.update_balance(current_balance)
        except Exception as e:
            print(f"刷新余额失败：{str(e)}")

    def update_connection_status(self, connected=True):
        """更新连接状态"""
        if hasattr(self, 'connection_status'):
            if connected:
                self.connection_status.configure(
                    text="🟢 已连接",
                    text_color=get_color('success')
                )
            else:
                self.connection_status.configure(
                    text="🔴 连接断开",
                    text_color=get_color('danger')
                )

    def on_closing(self):
        """窗口关闭事件"""
        try:
            # 停止所有定时器
            self.timer_manager.stop_all()

            # 确认关闭
            if messagebox.askyesno("确认退出", "确定要退出 JlmisPlus 系统吗？"):
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
    """测试现代化主窗口"""
    # 模拟用户信息
    user_info = {
        'operators_id': 1,
        'operators_username': 'test_operator',
        'operators_real_name': '测试操作员',
        'operators_available_credits': 156800,
        'channel_users_id': 1
    }

    # 创建并显示主窗口
    main_window = MainWindow(user_info)
    main_window.show()


if __name__ == '__main__':
    main()