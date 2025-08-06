"""
优化后的任务列表组件 - 增大字体和改进布局
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
                    'id': 'v342',
                    'title': 'v342',
                    'status': 'stopped',
                    'total': 100,
                    'sent': 0,
                    'success_count': 0,
                    'failed_count': 0,
                    'progress': 0.0
                },
                {
                    'id': 'v365',
                    'title': 'v365',
                    'status': 'stopped',
                    'total': 200,
                    'sent': 0,
                    'success_count': 0,
                    'failed_count': 0,
                    'progress': 0.0
                },
                {
                    'id': 'v378',
                    'title': 'v378',
                    'status': 'stopped',
                    'total': 150,
                    'sent': 0,
                    'success_count': 0,
                    'failed_count': 0,
                    'progress': 0.0
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
    """优化后的任务列表组件 - 增大字体和改进布局"""

    def __init__(self, parent, user_info, on_task_select=None, on_task_update=None):
        self.parent = parent
        self.user_info = user_info
        self.on_task_select = on_task_select
        self.on_task_update = on_task_update
        self.task_service = TaskService()
        self.selected_task = None
        self.tasks = []
        self.task_items = {}  # 存储任务项
        self.create_widgets()
        self.load_tasks()

    def create_widgets(self):
        """创建优化后的任务列表组件"""
        # 创建卡片容器
        self.card_container, self.content_frame = create_card_frame(self.parent, "任务列表")

        # 创建头部控制区域
        self.create_header()

        # 创建列表头部
        self.create_list_header()

        # 创建任务列表区域
        self.create_task_list_area()

    def create_header(self):
        """创建头部控制区域"""
        header_frame = tk.Frame(self.content_frame, bg=get_color('card_bg'))
        header_frame.pack(fill='x', padx=get_spacing('sm'), pady=(get_spacing('sm'), 0))

        # 按钮容器
        button_container = tk.Frame(header_frame, bg=get_color('card_bg'))
        button_container.pack(fill='x')

        # 左侧控制按钮
        left_buttons = tk.Frame(button_container, bg=get_color('card_bg'))
        left_buttons.pack(side='left')

        # 停止发送按钮
        self.stop_button = create_modern_button(
            left_buttons,
            text="⏹ 停止发送",
            style="gray",  # 使用修复后的灰色样式（黑色文字）
            command=self.stop_sending,
            width=10
        )
        self.stop_button.pack(side='left', padx=(0, get_spacing('xs')))

        # 添加任务按钮
        self.add_button = create_modern_button(
            left_buttons,
            text="➕ 添加任务",
            style="primary",
            command=self.add_task,
            width=10
        )
        self.add_button.pack(side='left', padx=(0, get_spacing('xs')))

        # 更多操作按钮
        self.more_button = create_modern_button(
            left_buttons,
            text="▼ 更多",
            style="secondary",
            command=self.show_more_menu,
            width=8
        )
        self.more_button.pack(side='left')

    def create_list_header(self):
        """创建列表头部"""
        header_frame = tk.Frame(self.content_frame, bg=get_color('primary_light'))
        header_frame.pack(fill='x', padx=get_spacing('sm'), pady=(get_spacing('sm'), 0))

        # 表头容器 - 增加高度
        header_container = tk.Frame(header_frame, bg=get_color('primary_light'), height=35)
        header_container.pack(fill='x', padx=get_spacing('sm'), pady=get_spacing('sm'))
        header_container.pack_propagate(False)

        # 列标题定义
        columns = [
            ("任务", 20),      # 任务名称列，占20%宽度
            ("进度", 15),      # 进度列，占15%宽度
            ("成功", 10),      # 成功数列，占10%宽度
            ("失败", 10),      # 失败数列，占10%宽度
            ("状态", 15),      # 状态列，占15%宽度
            ("操作", 30)       # 操作列，占30%宽度
        ]

        # 创建表头
        for col_name, width_percent in columns:
            col_frame = tk.Frame(header_container, bg=get_color('primary_light'))
            col_frame.pack(side='left', fill='both', expand=True if width_percent >= 20 else False)

            if width_percent < 20:
                col_frame.config(width=width_percent * 8)  # 近似宽度控制

            header_label = tk.Label(
                col_frame,
                text=col_name,
                font=get_font('medium'),  # 使用中等字体，更清晰
                fg=get_color('text'),
                bg=get_color('primary_light'),
                anchor='center' if col_name in ['进度', '成功', '失败', '状态'] else 'w'
            )
            header_label.pack(fill='both', expand=True, padx=get_spacing('xs'))

    def create_task_list_area(self):
        """创建任务列表区域"""
        # 列表容器
        list_container = tk.Frame(self.content_frame, bg=get_color('card_bg'))
        list_container.pack(fill='both', expand=True, padx=get_spacing('sm'), pady=get_spacing('sm'))

        # 创建滚动框架
        self.canvas = tk.Canvas(
            list_container,
            bg=get_color('white'),
            highlightthickness=0
        )

        self.scrollbar = ttk.Scrollbar(
            list_container,
            orient="vertical",
            command=self.canvas.yview
        )

        self.scrollable_frame = tk.Frame(self.canvas, bg=get_color('white'))

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
            # 清空现有项目
            for widget in self.scrollable_frame.winfo_children():
                widget.destroy()
            self.task_items.clear()

            # 获取用户任务
            result = self.task_service.get_user_tasks(self.user_info.get('operators_id', 1))
            if result['success']:
                self.tasks = result['tasks']

                # 创建任务列表项
                for i, task in enumerate(self.tasks):
                    self.create_task_item(task, i)

        except Exception as e:
            messagebox.showerror("错误", f"加载任务列表失败：{str(e)}")

    def create_task_item(self, task, index):
        """创建单个任务项 - 增大字体和行高"""
        task_id = task.get('id')

        # 任务行容器 - 增加高度
        row_frame = tk.Frame(
            self.scrollable_frame,
            bg=get_color('white'),
            relief='flat',
            bd=0,
            highlightthickness=1,
            highlightbackground=get_color('border_light'),
            height=45  # 增加行高
        )
        row_frame.pack(fill='x', pady=2, padx=2)
        row_frame.pack_propagate(False)  # 保持固定高度

        # 行内容容器
        content_container = tk.Frame(row_frame, bg=get_color('white'))
        content_container.pack(fill='both', expand=True, padx=get_spacing('sm'), pady=get_spacing('sm'))

        # 任务名称列 (20%)
        name_frame = tk.Frame(content_container, bg=get_color('white'))
        name_frame.pack(side='left', fill='both', expand=True)

        task_name = task.get('title', f"v{task.get('id', '')}")
        name_label = tk.Label(
            name_frame,
            text=task_name,
            font=get_font('medium'),  # 使用中等字体
            fg=get_color('text'),
            bg=get_color('white'),
            anchor='w'
        )
        name_label.pack(fill='both', expand=True, padx=(0, get_spacing('md')))

        # 进度列 (15%) - 增大宽度和字体
        progress_frame = tk.Frame(content_container, bg=get_color('white'), width=140)
        progress_frame.pack(side='left', padx=get_spacing('xs'))
        progress_frame.pack_propagate(False)

        progress = task.get('progress', 0)
        progress_text = f"{progress:.1f}% ({task.get('sent', 0)}/{task.get('total', 1)})"

        progress_label = tk.Label(
            progress_frame,
            text=progress_text,
            font=get_font('medium'),  # 增大字体
            fg=get_color('text'),
            bg=get_color('white'),
            anchor='center'
        )
        progress_label.pack(fill='both', expand=True)

        # 成功列 (10%) - 增大宽度和字体
        success_frame = tk.Frame(content_container, bg=get_color('white'), width=90)
        success_frame.pack(side='left', padx=get_spacing('xs'))
        success_frame.pack_propagate(False)

        success_label = tk.Label(
            success_frame,
            text=str(task.get('success_count', 0)),
            font=get_font('medium'),  # 增大字体
            fg=get_color('success'),
            bg=get_color('white'),
            anchor='center'
        )
        success_label.pack(fill='both', expand=True)

        # 失败列 (10%) - 增大宽度和字体
        failed_frame = tk.Frame(content_container, bg=get_color('white'), width=90)
        failed_frame.pack(side='left', padx=get_spacing('xs'))
        failed_frame.pack_propagate(False)

        failed_label = tk.Label(
            failed_frame,
            text=str(task.get('failed_count', 0)),
            font=get_font('medium'),  # 增大字体
            fg=get_color('danger'),
            bg=get_color('white'),
            anchor='center'
        )
        failed_label.pack(fill='both', expand=True)

        # 状态列 (15%) - 增大宽度和字体
        status_frame = tk.Frame(content_container, bg=get_color('white'), width=110)
        status_frame.pack(side='left', padx=get_spacing('xs'))
        status_frame.pack_propagate(False)

        status = task.get('status', 'stopped')
        status_text, status_style = self.get_status_info(status)

        # 使用橙色操作文字替代徽章
        if status == 'stopped':
            action_text = "操作"
            action_color = get_color('primary')
        else:
            action_text = status_text
            action_color = self.get_status_color(status)

        status_label = tk.Label(
            status_frame,
            text=action_text,
            font=get_font('medium'),  # 增大字体
            fg=action_color,
            bg=get_color('white'),
            anchor='center',
            cursor='hand2'
        )
        status_label.pack(fill='both', expand=True)

        # 绑定状态标签点击事件
        status_label.bind("<Button-1>", lambda e: self.show_task_menu(task, status_label))

        # 操作列 (30%)
        action_frame = tk.Frame(content_container, bg=get_color('white'))
        action_frame.pack(side='right', padx=get_spacing('xs'))

        # 根据状态显示不同的快捷操作按钮
        if status == 'running':
            action_btn = create_modern_button(
                action_frame,
                text="⏸ 暂停",
                style="warning",
                command=lambda: self.pause_task_by_id(task_id),
                width=6
            )
        elif status in ['paused', 'stopped']:
            action_btn = create_modern_button(
                action_frame,
                text="▶ 开始",
                style="success",
                command=lambda: self.start_task_by_id(task_id),
                width=6
            )
        else:
            action_btn = create_modern_button(
                action_frame,
                text="查看",
                style="secondary",
                command=lambda: self.select_task(task),
                width=6
            )

        action_btn.pack(side='left', padx=(0, get_spacing('xs')))

        # 更多操作按钮
        more_btn = create_modern_button(
            action_frame,
            text="⋯",
            style="secondary",
            command=lambda: self.show_task_menu(task, more_btn),
            width=3
        )
        more_btn.pack(side='left')

        # 存储任务项信息
        self.task_items[task_id] = {
            'frame': row_frame,
            'task': task,
            'progress_label': progress_label,
            'success_label': success_label,
            'failed_label': failed_label,
            'status_label': status_label,
            'content_container': content_container
        }

        # 绑定行点击选择事件
        def bind_click_events(widget):
            widget.bind("<Button-1>", lambda e: self.select_task(task))

        # 为行元素绑定点击事件（排除按钮）
        bind_click_events(row_frame)
        bind_click_events(content_container)
        bind_click_events(name_label)
        bind_click_events(progress_label)
        bind_click_events(success_label)
        bind_click_events(failed_label)

        # 绑定右键菜单
        row_frame.bind("<Button-3>", lambda e: self.show_task_menu(task, row_frame))

        # 隔行变色效果
        if index % 2 == 1:
            self.set_row_background(task_id, get_color('gray_light'))

    def set_row_background(self, task_id, bg_color):
        """设置行背景色"""
        if task_id in self.task_items:
            item = self.task_items[task_id]
            widgets = [
                item['frame'],
                item['content_container'],
                item['progress_label'],
                item['success_label'],
                item['failed_label'],
                item['status_label']
            ]

            for widget in widgets:
                try:
                    widget.config(bg=bg_color)
                except:
                    pass

    def get_status_info(self, status):
        """获取状态信息"""
        status_map = {
            'draft': ('草稿', 'gray'),
            'pending': ('待执行', 'info'),
            'running': ('发送中', 'primary'),
            'paused': ('暂停', 'warning'),
            'completed': ('完成', 'success'),
            'cancelled': ('已取消', 'gray'),
            'failed': ('失败', 'danger'),
            'stopped': ('停止', 'gray')
        }
        return status_map.get(status, ('未知', 'gray'))

    def get_status_color(self, status):
        """获取状态颜色"""
        color_map = {
            'running': get_color('primary'),
            'paused': get_color('warning'),
            'completed': get_color('success'),
            'failed': get_color('danger'),
            'stopped': get_color('gray')
        }
        return color_map.get(status, get_color('text'))

    def select_task(self, task):
        """选择任务"""
        # 清除之前的选中状态
        for task_id, item in self.task_items.items():
            item['frame'].config(
                highlightbackground=get_color('border_light'),
                highlightthickness=1
            )
            # 恢复原背景色
            task_index = next((i for i, t in enumerate(self.tasks) if t.get('id') == task_id), 0)
            if task_index % 2 == 1:
                self.set_row_background(task_id, get_color('gray_light'))
            else:
                self.set_row_background(task_id, get_color('white'))

        # 设置当前选中状态
        task_id = task.get('id')
        if task_id in self.task_items:
            self.task_items[task_id]['frame'].config(
                highlightbackground=get_color('primary'),
                highlightthickness=2
            )
            # 设置选中背景色
            self.set_row_background(task_id, get_color('selected'))

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
        if task_id in self.task_items:
            item = self.task_items[task_id]

            # 更新进度文字
            progress = progress_data.get('progress', 0)
            progress_text = f"{progress:.1f}% ({progress_data.get('sent', 0)}/{progress_data.get('total', 0)})"
            item['progress_label'].config(text=progress_text)

            # 更新统计信息
            item['success_label'].config(text=str(progress_data.get('success_count', 0)))
            item['failed_label'].config(text=str(progress_data.get('failed_count', 0)))

            # 更新状态
            status = progress_data.get('status', 'stopped')
            status_text, status_style = self.get_status_info(status)
            item['status_label'].config(
                text=status_text,
                fg=self.get_status_color(status)
            )

    # 保持原有的所有方法逻辑不变，只是界面呈现方式改变
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
    root.title("优化任务列表测试 - 增大字体版本")
    root.geometry("900x600")
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