"""
优化后的任务列表组件 - 卡片式设计
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ui.styles import get_color, get_font, get_spacing, create_modern_button, create_card_frame, create_status_badge

# 导入服务时处理异常
try:
    from services.task_service import TaskService
except ImportError:
    # 创建一个模拟的TaskService类
    class TaskService:
        def get_user_tasks(self, user_id, status=None, page=1, page_size=20):
            """模拟获取用户任务"""
            mock_tasks = [
                {
                    'id': 1,
                    'title': '测试任务1',
                    'status': 'running',
                    'total': 100,
                    'sent': 35,
                    'success_count': 30,
                    'failed_count': 5,
                    'progress': 35.0
                },
                {
                    'id': 2,
                    'title': '测试任务2',
                    'status': 'paused',
                    'total': 200,
                    'sent': 55,
                    'success_count': 50,
                    'failed_count': 5,
                    'progress': 27.5
                },
                {
                    'id': 3,
                    'title': '测试任务3',
                    'status': 'completed',
                    'total': 150,
                    'sent': 150,
                    'success_count': 148,
                    'failed_count': 2,
                    'progress': 100.0
                }
            ]
            return {
                'success': True,
                'tasks': mock_tasks,
                'total_count': len(mock_tasks),
                'page': page,
                'page_size': page_size,
                'total_pages': 1
            }

        def start_task(self, task_id):
            return {'success': True}

        def pause_task(self, task_id):
            return {'success': True}

        def stop_all_tasks(self, user_id):
            return {'success': True, 'count': 2}

        def start_all_tasks(self, user_id):
            return {'success': True, 'count': 1}

        def clear_completed_tasks(self, user_id):
            return {'success': True, 'count': 1}

        def retry_failed(self, task_id):
            return {'success': True, 'count': 3}

        def delete_task(self, task_id):
            return {'success': True}


class TaskListWidget:
    """优化后的任务列表组件"""

    def __init__(self, parent, user_info, on_task_select=None, on_task_update=None):
        self.parent = parent
        self.user_info = user_info
        self.on_task_select = on_task_select
        self.on_task_update = on_task_update
        self.task_service = TaskService()
        self.selected_task = None
        self.tasks = []
        self.task_cards = {}  # 存储任务卡片
        self.create_widgets()
        self.load_tasks()

    def create_widgets(self):
        """创建优化后的任务列表组件"""
        # 创建卡片容器
        self.card_container, self.content_frame = create_card_frame(self.parent, "任务列表")

        # 创建头部控制区域
        self.create_header()

        # 创建任务卡片区域
        self.create_task_cards_area()

    def create_header(self):
        """创建优化后的头部控制区域"""
        header_frame = tk.Frame(self.content_frame, bg=get_color('card_bg'))
        header_frame.pack(fill='x', padx=get_spacing('sm'), pady=(get_spacing('sm'), 0))

        # 按钮容器 - 两行布局
        button_container = tk.Frame(header_frame, bg=get_color('card_bg'))
        button_container.pack(fill='x')

        # 第一行按钮
        button_row1 = tk.Frame(button_container, bg=get_color('card_bg'))
        button_row1.pack(fill='x', pady=(0, get_spacing('xs')))

        # 停止发送按钮
        self.stop_button = create_modern_button(
            button_row1,
            text="⏹ 停止发送",
            style="gray",
            command=self.stop_sending,
            width=10
        )
        self.stop_button.pack(side='left', padx=(0, get_spacing('xs')))

        # 添加任务按钮
        self.add_button = create_modern_button(
            button_row1,
            text="➕ 添加任务",
            style="primary",
            command=self.add_task,
            width=10
        )
        self.add_button.pack(side='left', padx=(0, get_spacing('xs')))

        # 更多操作按钮
        self.more_button = create_modern_button(
            button_row1,
            text="⚙ 更多",
            style="secondary",
            command=self.show_more_menu,
            width=8
        )
        self.more_button.pack(side='left')

    def create_task_cards_area(self):
        """创建任务卡片区域"""
        # 滚动区域容器
        scroll_container = tk.Frame(self.content_frame, bg=get_color('card_bg'))
        scroll_container.pack(fill='both', expand=True, padx=get_spacing('sm'), pady=get_spacing('sm'))

        # 创建滚动框架
        self.canvas = tk.Canvas(
            scroll_container,
            bg=get_color('card_bg'),
            highlightthickness=0
        )

        self.scrollbar = ttk.Scrollbar(
            scroll_container,
            orient="vertical",
            command=self.canvas.yview
        )

        self.scrollable_frame = tk.Frame(self.canvas, bg=get_color('card_bg'))

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # 布局滚动组件
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # 绑定鼠标滚轮事件
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        """处理鼠标滚轮事件"""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def load_tasks(self):
        """加载任务列表"""
        try:
            # 清空现有卡片
            for widget in self.scrollable_frame.winfo_children():
                widget.destroy()
            self.task_cards.clear()

            # 获取用户任务
            result = self.task_service.get_user_tasks(self.user_info.get('operators_id', 1))
            if result['success']:
                self.tasks = result['tasks']

                # 创建任务卡片
                for i, task in enumerate(self.tasks):
                    self.create_task_card(task, i)

        except Exception as e:
            messagebox.showerror("错误", f"加载任务列表失败：{str(e)}")

    def create_task_card(self, task, index):
        """创建单个任务卡片"""
        task_id = task.get('id')

        # 任务卡片容器
        card_frame = tk.Frame(
            self.scrollable_frame,
            bg=get_color('white'),
            relief='solid',
            bd=1,
            highlightbackground=get_color('border_light'),
            highlightthickness=1
        )
        card_frame.pack(fill='x', pady=get_spacing('xs'), padx=get_spacing('xs'))

        # 内容容器
        content_container = tk.Frame(card_frame, bg=get_color('white'))
        content_container.pack(fill='both', expand=True, padx=get_spacing('md'), pady=get_spacing('md'))

        # 头部：任务名称和状态
        header_frame = tk.Frame(content_container, bg=get_color('white'))
        header_frame.pack(fill='x', pady=(0, get_spacing('sm')))

        # 任务名称
        task_name = task.get('title', f"v{task.get('id', '')}")
        name_label = tk.Label(
            header_frame,
            text=task_name,
            font=get_font('subtitle'),
            fg=get_color('text'),
            bg=get_color('white')
        )
        name_label.pack(side='left')

        # 状态徽章
        status = task.get('status', 'stopped')
        status_text, status_style = self.get_status_info(status)
        status_badge = create_status_badge(header_frame, status_text, status_style)
        status_badge.pack(side='right')

        # 进度区域
        progress_frame = tk.Frame(content_container, bg=get_color('white'))
        progress_frame.pack(fill='x', pady=(0, get_spacing('sm')))

        # 进度条背景
        progress_bg = tk.Frame(
            progress_frame,
            bg=get_color('gray_light'),
            height=8
        )
        progress_bg.pack(fill='x')
        progress_bg.pack_propagate(False)

        # 进度条
        progress = task.get('progress', 0)
        if progress > 0:
            progress_fill = tk.Frame(
                progress_bg,
                bg=self.get_progress_color(status),
                height=8
            )
            # 使用after方法延迟设置进度条宽度
            def set_progress():
                try:
                    total_width = progress_bg.winfo_width()
                    if total_width > 1:
                        progress_width = max(1, int(total_width * progress / 100))
                        progress_fill.place(x=0, y=0, width=progress_width, height=8)
                except:
                    pass

            progress_bg.after(10, set_progress)

        # 进度文字
        progress_text = f"{progress:.1f}% ({task.get('sent', 0)}/{task.get('total', 0)})"
        progress_label = tk.Label(
            progress_frame,
            text=progress_text,
            font=get_font('small'),
            fg=get_color('text_light'),
            bg=get_color('white')
        )
        progress_label.pack(pady=(get_spacing('xs'), 0))

        # 统计信息区域
        stats_frame = tk.Frame(content_container, bg=get_color('white'))
        stats_frame.pack(fill='x', pady=(0, get_spacing('sm')))

        # 成功数量
        success_label = tk.Label(
            stats_frame,
            text=f"✓ 成功: {task.get('success_count', 0)}",
            font=get_font('small'),
            fg=get_color('success'),
            bg=get_color('white')
        )
        success_label.pack(side='left', padx=(0, get_spacing('md')))

        # 失败数量
        failed_label = tk.Label(
            stats_frame,
            text=f"✗ 失败: {task.get('failed_count', 0)}",
            font=get_font('small'),
            fg=get_color('danger'),
            bg=get_color('white')
        )
        failed_label.pack(side='left')

        # 操作按钮区域（悬停时显示）
        action_frame = tk.Frame(content_container, bg=get_color('white'))
        action_frame.pack(fill='x')

        # 快捷操作按钮
        if status == 'running':
            action_btn = create_modern_button(
                action_frame,
                text="⏸ 暂停",
                style="warning",
                command=lambda: self.pause_task_by_id(task_id),
                width=8
            )
        elif status in ['paused', 'stopped']:
            action_btn = create_modern_button(
                action_frame,
                text="▶ 开始",
                style="success",
                command=lambda: self.start_task_by_id(task_id),
                width=8
            )
        else:
            action_btn = create_modern_button(
                action_frame,
                text="📊 查看",
                style="info",
                command=lambda: self.select_task(task),
                width=8
            )

        action_btn.pack(side='left')

        # 更多操作按钮
        more_btn = create_modern_button(
            action_frame,
            text="⋯",
            style="secondary",
            command=lambda: self.show_task_menu(task, card_frame),
            width=4
        )
        more_btn.pack(side='right')

        # 存储卡片信息
        self.task_cards[task_id] = {
            'frame': card_frame,
            'task': task,
            'progress_bg': progress_bg,
            'progress_label': progress_label,
            'success_label': success_label,
            'failed_label': failed_label
        }

        # 绑定点击选择事件
        card_frame.bind("<Button-1>", lambda e: self.select_task(task))
        content_container.bind("<Button-1>", lambda e: self.select_task(task))
        name_label.bind("<Button-1>", lambda e: self.select_task(task))

        # 绑定右键菜单
        card_frame.bind("<Button-3>", lambda e: self.show_task_menu(task, card_frame))

    def get_status_info(self, status):
        """获取状态信息"""
        status_map = {
            'draft': ('草稿', 'gray'),
            'pending': ('待执行', 'info'),
            'running': ('发送中', 'primary'),
            'paused': ('暂停', 'warning'),
            'completed': ('完成', 'success'),
            'cancelled': ('已取消', 'gray'),
            'failed': ('失败', 'danger')
        }
        return status_map.get(status, ('未知', 'gray'))

    def get_progress_color(self, status):
        """获取进度条颜色"""
        color_map = {
            'running': get_color('primary'),
            'paused': get_color('warning'),
            'completed': get_color('success'),
            'failed': get_color('danger')
        }
        return color_map.get(status, get_color('info'))

    def select_task(self, task):
        """选择任务"""
        # 清除之前的选中状态
        for card_info in self.task_cards.values():
            card_info['frame'].config(
                highlightbackground=get_color('border_light'),
                highlightthickness=1
            )

        # 设置当前选中状态
        task_id = task.get('id')
        if task_id in self.task_cards:
            self.task_cards[task_id]['frame'].config(
                highlightbackground=get_color('primary'),
                highlightthickness=2
            )

        self.selected_task = task

        # 调用回调函数
        if self.on_task_select:
            self.on_task_select(task)

    def start_task_by_id(self, task_id):
        """通过ID开始任务"""
        try:
            result = self.task_service.start_task(task_id)
            if result['success']:
                messagebox.showinfo("成功", "任务已开始")
                self.refresh_tasks()
            else:
                messagebox.showerror("失败", result['message'])
        except Exception as e:
            messagebox.showerror("错误", f"开始任务失败：{str(e)}")

    def pause_task_by_id(self, task_id):
        """通过ID暂停任务"""
        try:
            result = self.task_service.pause_task(task_id)
            if result['success']:
                messagebox.showinfo("成功", "任务已暂停")
                self.refresh_tasks()
            else:
                messagebox.showerror("失败", result['message'])
        except Exception as e:
            messagebox.showerror("错误", f"暂停任务失败：{str(e)}")

    def show_task_menu(self, task, widget):
        """显示任务菜单"""
        self.selected_task = task

        # 创建弹出菜单
        menu = tk.Menu(self.parent, tearoff=0, bg=get_color('white'))

        # 根据任务状态显示不同选项
        status = task.get('status', 'stopped')

        if status in ['paused', 'stopped']:
            menu.add_command(label="▶ 开始任务", command=self.start_task)
        elif status == 'running':
            menu.add_command(label="⏸ 暂停任务", command=self.pause_task)

        menu.add_separator()
        menu.add_command(label="🧪 测试任务", command=self.test_task)
        menu.add_command(label="✏ 修改内容", command=self.edit_task)

        menu.add_separator()
        menu.add_command(label="🔄 重试失败", command=self.retry_failed)

        menu.add_separator()
        menu.add_command(label="📤 导出-已完成", command=self.export_completed)
        menu.add_command(label="📤 导出-未完成", command=self.export_uncompleted)

        menu.add_separator()
        menu.add_command(
            label="🗑 删除该任务",
            command=self.delete_task,
            foreground=get_color('danger')
        )

        # 显示菜单
        try:
            x = widget.winfo_rootx()
            y = widget.winfo_rooty() + widget.winfo_height()
            menu.post(x, y)
        except:
            pass

    def show_more_menu(self):
        """显示更多操作菜单"""
        more_menu = tk.Menu(self.parent, tearoff=0, bg=get_color('white'))
        more_menu.add_command(label="🔄 刷新列表", command=self.refresh_tasks)
        more_menu.add_command(label="▶ 全部开始", command=self.start_all_tasks)
        more_menu.add_command(label="⏹ 全部停止", command=self.stop_all_tasks)
        more_menu.add_separator()
        more_menu.add_command(label="🧹 清理完成任务", command=self.clear_completed)
        more_menu.add_command(label="📊 导出任务报告", command=self.export_report)

        # 在按钮下方显示菜单
        try:
            x = self.more_button.winfo_rootx()
            y = self.more_button.winfo_rooty() + self.more_button.winfo_height()
            more_menu.post(x, y)
        except:
            pass

    def update_task_progress(self, task_id, progress_data):
        """更新任务进度显示"""
        if task_id in self.task_cards:
            card_info = self.task_cards[task_id]

            # 更新进度条
            progress = progress_data.get('progress', 0)
            def update_progress():
                try:
                    total_width = card_info['progress_bg'].winfo_width()
                    if total_width > 1:
                        progress_width = max(1, int(total_width * progress / 100))
                        # 这里需要重新创建进度条填充
                        for child in card_info['progress_bg'].winfo_children():
                            child.destroy()
                        if progress > 0:
                            progress_fill = tk.Frame(
                                card_info['progress_bg'],
                                bg=self.get_progress_color(progress_data.get('status', 'stopped')),
                                height=8
                            )
                            progress_fill.place(x=0, y=0, width=progress_width, height=8)
                except:
                    pass

            card_info['progress_bg'].after(10, update_progress)

            # 更新进度文字
            progress_text = f"{progress:.1f}% ({progress_data.get('sent', 0)}/{progress_data.get('total', 0)})"
            card_info['progress_label'].config(text=progress_text)

            # 更新统计信息
            card_info['success_label'].config(text=f"✓ 成功: {progress_data.get('success_count', 0)}")
            card_info['failed_label'].config(text=f"✗ 失败: {progress_data.get('failed_count', 0)}")

    # 保持原有的所有方法逻辑不变，只是调用方式
    def stop_sending(self):
        """停止发送"""
        if messagebox.askyesno("确认", "确定要停止所有正在发送的任务吗？"):
            try:
                result = self.task_service.stop_all_tasks(self.user_info.get('operators_id'))
                if result['success']:
                    messagebox.showinfo("成功", "已停止所有发送任务")
                    self.refresh_tasks()
                else:
                    messagebox.showerror("失败", result['message'])
            except Exception as e:
                messagebox.showerror("错误", f"停止发送失败：{str(e)}")

    def add_task(self):
        """添加任务"""
        if self.on_task_update:
            self.on_task_update('add', None)

    def start_task(self):
        """开始任务"""
        if not self.selected_task:
            messagebox.showwarning("警告", "请先选择一个任务")
            return
        self.start_task_by_id(self.selected_task['id'])

    def pause_task(self):
        """暂停任务"""
        if not self.selected_task:
            messagebox.showwarning("警告", "请先选择一个任务")
            return
        self.pause_task_by_id(self.selected_task['id'])

    def retry_failed(self):
        """重试失败"""
        if not self.selected_task:
            messagebox.showwarning("警告", "请先选择一个任务")
            return

        if messagebox.askyesno("确认", f"确定要重试任务 '{self.selected_task.get('title')}' 的失败项目吗？"):
            try:
                result = self.task_service.retry_failed(self.selected_task['id'])
                if result['success']:
                    messagebox.showinfo("成功", f"已重试 {result['count']} 个失败项目")
                    self.refresh_tasks()
                else:
                    messagebox.showerror("失败", result['message'])
            except Exception as e:
                messagebox.showerror("错误", f"重试失败：{str(e)}")

    def test_task(self):
        """测试任务"""
        if not self.selected_task:
            messagebox.showwarning("警告", "请先选择一个任务")
            return
        if self.on_task_update:
            self.on_task_update('test', self.selected_task)

    def edit_task(self):
        """修改任务内容"""
        if not self.selected_task:
            messagebox.showwarning("警告", "请先选择一个任务")
            return
        if self.on_task_update:
            self.on_task_update('edit', self.selected_task)

    def delete_task(self):
        """删除任务"""
        if not self.selected_task:
            messagebox.showwarning("警告", "请先选择一个任务")
            return

        if messagebox.askyesno("确认删除", f"确定要删除任务 '{self.selected_task.get('title')}' 吗？\n此操作不可恢复！"):
            try:
                result = self.task_service.delete_task(self.selected_task['id'])
                if result['success']:
                    messagebox.showinfo("成功", "任务已删除")
                    self.refresh_tasks()
                else:
                    messagebox.showerror("失败", result['message'])
            except Exception as e:
                messagebox.showerror("错误", f"删除任务失败：{str(e)}")

    def export_completed(self):
        """导出已完成"""
        if not self.selected_task:
            messagebox.showwarning("警告", "请先选择一个任务")
            return
        if self.on_task_update:
            self.on_task_update('export_completed', self.selected_task)

    def export_uncompleted(self):
        """导出未完成"""
        if not self.selected_task:
            messagebox.showwarning("警告", "请先选择一个任务")
            return
        if self.on_task_update:
            self.on_task_update('export_uncompleted', self.selected_task)

    def refresh_tasks(self):
        """刷新任务列表"""
        self.load_tasks()

    def start_all_tasks(self):
        """开始所有任务"""
        if messagebox.askyesno("确认", "确定要开始所有停止的任务吗？"):
            try:
                result = self.task_service.start_all_tasks(self.user_info.get('operators_id'))
                if result['success']:
                    messagebox.showinfo("成功", f"已开始 {result['count']} 个任务")
                    self.refresh_tasks()
                else:
                    messagebox.showerror("失败", result['message'])
            except Exception as e:
                messagebox.showerror("错误", f"开始所有任务失败：{str(e)}")

    def stop_all_tasks(self):
        """停止所有任务"""
        if messagebox.askyesno("确认", "确定要停止所有正在运行的任务吗？"):
            try:
                result = self.task_service.stop_all_tasks(self.user_info.get('operators_id'))
                if result['success']:
                    messagebox.showinfo("成功", f"已停止 {result['count']} 个任务")
                    self.refresh_tasks()
                else:
                    messagebox.showerror("失败", result['message'])
            except Exception as e:
                messagebox.showerror("错误", f"停止所有任务失败：{str(e)}")

    def clear_completed(self):
        """清理完成任务"""
        if messagebox.askyesno("确认", "确定要清理所有已完成的任务吗？\n此操作不可恢复！"):
            try:
                result = self.task_service.clear_completed_tasks(self.user_info.get('operators_id'))
                if result['success']:
                    messagebox.showinfo("成功", f"已清理 {result['count']} 个完成任务")
                    self.refresh_tasks()
                else:
                    messagebox.showerror("失败", result['message'])
            except Exception as e:
                messagebox.showerror("错误", f"清理完成任务失败：{str(e)}")

    def export_report(self):
        """导出任务报告"""
        if self.on_task_update:
            self.on_task_update('export_report', None)

    def get_frame(self):
        """获取组件框架"""
        return self.card_container


def main():
    """测试优化后的任务列表组件"""
    root = tk.Tk()
    root.title("优化任务列表测试")
    root.geometry("500x700")
    root.configure(bg=get_color('background'))

    # 模拟用户信息
    user_info = {
        'operators_id': 1,
        'operators_username': 'test_user',
        'operators_available_credits': 10000
    }

    def on_task_select(task):
        print(f"选中任务: {task}")

    def on_task_update(action, task):
        print(f"任务操作: {action}, 任务: {task}")

    # 创建任务列表组件
    task_list = TaskListWidget(root, user_info, on_task_select, on_task_update)
    task_list.get_frame().pack(fill='both', expand=True, padx=10, pady=10)

    root.mainloop()


if __name__ == '__main__':
    main()