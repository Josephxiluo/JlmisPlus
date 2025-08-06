"""
优化后的主窗口 - 添加可调整大小的分割窗口
"""
import tkinter as tk
from tkinter import messagebox
from typing import Dict, Any
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入优化后的UI组件
from ui.styles import get_color, get_font, get_spacing, create_resizable_paned_window
from ui.components.timer_widget import TimerWidget, TimerManager

# 导入对话框
from ui.dialogs.add_task_dialog import AddTaskDialog
from ui.dialogs.task_test_dialog import TaskTestDialog
from ui.dialogs.task_edit_dialog import TaskEditDialog
from ui.dialogs.config_dialog import ConfigDialog
from ui.dialogs.export_dialog import ExportDialog


class MainWindow:
    """优化后的主窗口类 - 支持左右分割窗口调整"""

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
        self.root.title(f"Pulsesports 1.9.0-rc.1-首发 - 测试操作员")
        self.root.geometry("1400x900")
        self.root.configure(bg=get_color('background'))

        # 设置最小窗口大小
        self.root.minsize(1200, 800)

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
        """创建优化后的界面组件"""
        # 1. 创建状态栏（顶部）
        from ui.components.status_bar import StatusBar
        self.status_bar = StatusBar(self.root, self.normalized_user_info)

        # 2. 创建主内容区域容器
        main_container = tk.Frame(self.root, bg=get_color('background'))
        main_container.pack(fill='both', expand=True)

        # 添加内边距容器
        content_frame = tk.Frame(main_container, bg=get_color('background'))
        content_frame.pack(fill='both', expand=True,
                          padx=get_spacing('lg'), pady=get_spacing('md'))

        # 3. 创建可调整大小的分割窗口
        self.paned_window = create_resizable_paned_window(content_frame, orientation='horizontal')
        self.paned_window.pack(fill='both', expand=True)

        # 4. 创建左侧任务管理区域
        left_container = tk.Frame(self.paned_window, bg=get_color('background'))

        from ui.components.task_list_widget import TaskListWidget
        self.task_list_widget = TaskListWidget(
            left_container,
            self.normalized_user_info,
            on_task_select=self.on_task_select,
            on_task_update=self.on_task_update
        )
        self.task_list_widget.get_frame().pack(fill='both', expand=True)

        # 5. 创建右侧端口管理区域
        right_container = tk.Frame(self.paned_window, bg=get_color('background'))

        from ui.components.port_grid_widget import PortGridWidget
        self.port_grid_widget = PortGridWidget(
            right_container,
            self.normalized_user_info,
            on_port_select=self.on_port_select
        )
        self.port_grid_widget.get_frame().pack(fill='both', expand=True)

        # 6. 将左右容器添加到分割窗口
        self.paned_window.add(left_container, minsize=400)  # 左侧最小宽度400px
        self.paned_window.add(right_container, minsize=600)  # 右侧最小宽度600px

        # 7. 设置初始分割比例（左侧40%，右侧60%）
        self.root.after(100, self.set_initial_sash_position)

        # 8. 添加底部状态信息
        self.create_bottom_status()

    def set_initial_sash_position(self):
        """设置初始分割条位置"""
        try:
            # 获取窗口宽度
            total_width = self.paned_window.winfo_width()
            if total_width > 100:  # 确保窗口已经完全加载
                # 设置左侧占40%
                left_width = int(total_width * 0.4)
                self.paned_window.sash_place(0, left_width, 0)
            else:
                # 如果窗口还没完全加载，延迟执行
                self.root.after(100, self.set_initial_sash_position)
        except:
            pass

    def create_bottom_status(self):
        """创建底部状态信息"""
        bottom_frame = tk.Frame(self.root, bg=get_color('gray_light'), height=25)
        bottom_frame.pack(fill='x', side='bottom')
        bottom_frame.pack_propagate(False)

        # 版本信息
        version_label = tk.Label(
            bottom_frame,
            text="Pulsesports v1.9.0-rc.1 | 就绪",
            font=get_font('small'),
            fg=get_color('text_light'),
            bg=get_color('gray_light')
        )
        version_label.pack(side='left', padx=get_spacing('md'), pady=get_spacing('xs'))

        # 分割窗口提示信息
        resize_hint = tk.Label(
            bottom_frame,
            text="💡 可拖拽中间分割线调整左右窗口大小",
            font=get_font('small'),
            fg=get_color('primary'),
            bg=get_color('gray_light')
        )
        resize_hint.pack(side='left', padx=get_spacing('lg'))

        # 连接状态
        self.connection_status = tk.Label(
            bottom_frame,
            text="🟢 已连接",
            font=get_font('small'),
            fg=get_color('success'),
            bg=get_color('gray_light')
        )
        self.connection_status.pack(side='right', padx=get_spacing('md'), pady=get_spacing('xs'))

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
        """显示成功消息"""
        messagebox.showinfo("成功", message)

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
                self.connection_status.config(
                    text="🟢 已连接",
                    fg=get_color('success')
                )
            else:
                self.connection_status.config(
                    text="🔴 连接断开",
                    fg=get_color('danger')
                )

    def on_closing(self):
        """窗口关闭事件"""
        try:
            # 停止所有定时器
            self.timer_manager.stop_all()

            # 确认关闭
            if messagebox.askyesno("确认退出", "确定要退出 Pulsesports 系统吗？"):
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
    """测试优化后的主窗口"""
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