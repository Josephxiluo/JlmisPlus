"""
现代化任务列表组件 - CustomTkinter版本
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ui.styles import get_color, get_font, get_spacing, create_modern_button, create_card_frame, create_scrollable_frame, create_label, create_status_badge

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
                    'total': 150,
                    'sent': 45,
                    'success_count': 38,
                    'failed_count': 7,
                    'progress': 30.0
                },
                {
                    'id': 'v365',
                    'title': 'v365',
                    'status': 'running',
                    'total': 200,
                    'sent': 120,
                    'success_count': 108,
                    'failed_count': 12,
                    'progress': 60.0
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
    """现代化任务列表组件 - CustomTkinter版本"""

    def __init__(self, parent, user_info, on_task_select=None, on_task_update=None):
        self.parent = parent
        self.user_info = user_info
        self.on_task_select = on_task_select
        self.on_task_update = on_task_update
        self.task_service = TaskService()
        self.selected_task = None
        self.tasks = []
        self.task_items = {}
        self.context_menu = None
        self.create_widgets()
        self.create_context_menu()
        self.load_tasks()

    def create_widgets(self):
        """创建现代化任务列表组件"""
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
        header_frame = ctk.CTkFrame(self.content_frame, fg_color='transparent')
        header_frame.pack(fill='x', padx=get_spacing('sm'), pady=(get_spacing('sm'), 0))

        # 按钮容器
        button_container = ctk.CTkFrame(header_frame, fg_color='transparent')
        button_container.pack(fill='x')

        # 左侧控制按钮
        left_buttons = ctk.CTkFrame(button_container, fg_color='transparent')
        left_buttons.pack(side='left')

        # 停止发送按钮
        self.stop_button = create_modern_button(
            left_buttons,
            text="⏹ 停止发送",
            style="gray",
            command=self.stop_sending,
            width=100
        )
        self.stop_button.pack(side='left', padx=(0, get_spacing('xs')))

        # 添加任务按钮
        self.add_button = create_modern_button(
            left_buttons,
            text="➕ 添加任务",
            style="primary",
            command=self.add_task,
            width=100
        )
        self.add_button.pack(side='left', padx=(0, get_spacing('xs')))

        # 更多操作按钮
        self.more_button = create_modern_button(
            left_buttons,
            text="▼ 更多",
            style="secondary",
            command=self.show_more_menu,
            width=80
        )
        self.more_button.pack(side='left', padx=(0, get_spacing('xs')))

    def create_list_header(self):
        """创建列表头部 - 修复版（固定宽度对齐）"""
        header_frame = ctk.CTkFrame(
            self.content_frame,
            fg_color=get_color('primary_light'),
            corner_radius=8,
            height=40
        )
        header_frame.pack(fill='x', padx=get_spacing('sm'), pady=(get_spacing('sm'), 0))
        header_frame.pack_propagate(False)

        # 列标题容器
        header_container = ctk.CTkFrame(header_frame, fg_color='transparent')
        header_container.pack(fill='both', expand=True, padx=get_spacing('sm'), pady=get_spacing('xs'))

        # 列标题定义 - 使用固定像素宽度确保对齐
        columns = [
            ("任务", 160),  # 固定150px
            ("进度", 80),  # 固定100px
            ("成功", 60),  # 固定50px
            ("失败", 60),  # 固定50px
            ("状态", 60),  # 固定60px
            ("操作", None)  # 占用剩余空间
        ]

        # 创建表头标签
        for col_name, width in columns:
            if width is not None:
                # 固定宽度的列
                col_frame = ctk.CTkFrame(header_container, fg_color='transparent', width=width)
                col_frame.pack(side='left', fill='y', padx=1)
                col_frame.pack_propagate(False)

                header_label = create_label(
                    col_frame,
                    text=col_name,
                    style="default"
                )
                header_label.pack(expand=True, fill='both')
            else:
                # 操作列占用剩余空间
                header_label = create_label(
                    header_container,
                    text=col_name,
                    style="default"
                )
                header_label.pack(side='left', fill='both', expand=True, padx=(get_spacing('xs'), 0))

    def create_task_list_area(self):
        """创建任务列表区域"""
        # 创建可滚动框架
        self.scrollable_frame = create_scrollable_frame(
            self.content_frame,
            height=400
        )
        self.scrollable_frame.pack(fill='both', expand=True, padx=get_spacing('sm'), pady=get_spacing('sm'))

    def load_tasks(self):
        """加载任务列表"""
        try:
            # 清空现有项目
            for widget in self.scrollable_frame.winfo_children():
                widget.destroy()
            self.task_items.clear()

            # 获取用户任务
            user_id = self.user_info.get('id') or self.user_info.get('operators_id', 1)
            result = self.task_service.get_user_tasks(user_id)
            if result['success']:
                self.tasks = result['tasks']

                # 创建任务列表项
                for i, task in enumerate(self.tasks):
                    self.create_task_item(task, i)

        except Exception as e:
            messagebox.showerror("错误", f"加载任务列表失败：{str(e)}")

    def create_task_item(self, task, index):
        """创建单个任务项 - 修复版（与表头完美对齐）"""
        task_id = task.get('id')

        # 任务行容器 - 与您当前的设置保持一致
        row_frame = ctk.CTkFrame(
            self.scrollable_frame,
            fg_color=get_color('white'),
            corner_radius=2,
            border_width=1,
            border_color=get_color('border_light'),
            height=70
        )
        row_frame.pack(fill='x', pady=4, padx=2)
        row_frame.pack_propagate(False)

        # 行内容容器
        content_container = ctk.CTkFrame(row_frame, fg_color='transparent')
        content_container.pack(fill='both', expand=True, padx=get_spacing('md'), pady=get_spacing('sm'))

        # 任务名称列 - 与表头对齐：150px
        name_frame = ctk.CTkFrame(content_container, fg_color='transparent', width=140)
        name_frame.pack(side='left', fill='y', padx=1)
        name_frame.pack_propagate(False)

        task_name = task.get('title', f"v{task.get('id', '')}")
        name_label = create_label(
            name_frame,
            text=task_name,
            style="medium"
        )
        name_label.pack(fill='both', expand=True, padx=(0, get_spacing('sm')))

        # 进度列 - 与表头对齐：100px
        progress_frame = ctk.CTkFrame(content_container, fg_color='transparent', width=80)
        progress_frame.pack(side='left', fill='y', padx=1)
        progress_frame.pack_propagate(False)

        progress = task.get('progress', 0)
        progress_text = f"{progress:.1f}%"
        detail_text = f"({task.get('sent', 0)}/{task.get('total', 1)})"

        # 进度百分比
        self.progress_label = create_label(
            progress_frame,
            text=progress_text,
            style="default"
        )
        self.progress_label.pack(anchor='center')

        # 详细进度
        detail_label = create_label(
            progress_frame,
            text=detail_text,
            style="small"
        )
        detail_label.configure(text_color=get_color('text_light'))
        detail_label.pack(anchor='center')

        # 进度条
        progress_bar = ctk.CTkProgressBar(
            progress_frame,
            height=4,
            corner_radius=2,
            progress_color=get_color('primary'),
            fg_color=get_color('gray_light')
        )
        progress_bar.pack(fill='x', pady=(1, 0), padx=2)
        progress_bar.set(progress / 100.0)

        # 成功列 - 与表头对齐：50px
        success_frame = ctk.CTkFrame(content_container, fg_color='transparent', width=60)
        success_frame.pack(side='left', fill='y', padx=1)
        success_frame.pack_propagate(False)

        self.success_label = create_label(
            success_frame,
            text=str(task.get('success_count', 0)),
            style="default"
        )
        self.success_label.configure(text_color=get_color('success'))
        self.success_label.pack(anchor='center', expand=True)

        # 失败列 - 与表头对齐：50px
        failed_frame = ctk.CTkFrame(content_container, fg_color='transparent', width=60)
        failed_frame.pack(side='left', fill='y', padx=1)
        failed_frame.pack_propagate(False)

        self.failed_label = create_label(
            failed_frame,
            text=str(task.get('failed_count', 0)),
            style="default"
        )
        self.failed_label.configure(text_color=get_color('danger'))
        self.failed_label.pack(anchor='center', expand=True)

        # 状态列 - 与表头对齐：60px
        status_frame = ctk.CTkFrame(content_container, fg_color='transparent', width=60)
        status_frame.pack(side='left', fill='y', padx=1)
        status_frame.pack_propagate(False)

        status = task.get('status', 'stopped')
        status_text, status_style = self.get_status_info(status)

        # 使用状态徽章
        self.status_badge = create_status_badge(
            status_frame,
            text=status_text,
            status_type=status_style
        )
        self.status_badge.pack(anchor='center', expand=True)

        # 操作列 - 占用剩余空间（与表头一致）
        action_frame = ctk.CTkFrame(content_container, fg_color='transparent')
        action_frame.pack(side='right', fill='both', expand=True, padx=(get_spacing('xs'), 0))

        # 操作按钮容器
        button_container = ctk.CTkFrame(action_frame, fg_color='transparent')
        button_container.pack(expand=True, fill='both')

        # 根据状态显示不同的快捷操作按钮
        if status == 'running':
            action_btn = ctk.CTkButton(
                button_container,
                text="⏸ 暂停",
                command=lambda: self.pause_task_by_id(task_id),
                font=get_font('small'),
                width=65,
                height=26,
                fg_color=get_color('warning'),
                hover_color='#FB8C00'
            )
        elif status in ['paused', 'stopped']:
            action_btn = ctk.CTkButton(
                button_container,
                text="▶ 开始",
                command=lambda: self.start_task_by_id(task_id),
                font=get_font('small'),
                width=65,
                height=26,
                fg_color=get_color('success'),
                hover_color='#45A049'
            )
        else:
            action_btn = ctk.CTkButton(
                button_container,
                text="查看",
                command=lambda: self.select_task(task),
                font=get_font('small'),
                width=65,
                height=26,
                fg_color=get_color('gray'),
                hover_color='#E0E0E0'
            )

        action_btn.pack(side='left', padx=(10, 5), pady=5)

        # 更多操作按钮
        more_btn = ctk.CTkButton(
            button_container,
            text="操作",
            command=lambda: self.show_task_menu(task, more_btn),
            font=get_font('default'),
            width=50,
            height=28,
            fg_color=get_color('gray_light'),
            hover_color=get_color('hover_bg'),
            text_color=get_color('text')
        )
        more_btn.pack(side='left', padx=(0, 10), pady=5)

        # 存储任务项信息
        self.task_items[task_id] = {
            'frame': row_frame,
            'task': task,
            'progress_label': self.progress_label,
            'success_label': self.success_label,
            'failed_label': self.failed_label,
            'status_badge': self.status_badge,
            'content_container': content_container
        }

        # 绑定点击选择事件
        def bind_click_events(widget):
            widget.bind("<Button-1>", lambda e: self.select_task(task))

        # 绑定右键菜单事件
        def bind_context_menu(widget):
            widget.bind("<Button-3>", lambda e: self.show_context_menu(e, task))

        # 为行元素绑定点击事件（排除按钮）
        bind_click_events(row_frame)
        bind_click_events(content_container)
        bind_click_events(name_label)
        bind_click_events(self.progress_label)
        bind_click_events(self.success_label)
        bind_click_events(self.failed_label)

        # 绑定右键菜单
        bind_context_menu(row_frame)
        bind_context_menu(content_container)
        bind_context_menu(name_label)
        bind_context_menu(self.progress_label)
        bind_context_menu(self.success_label)
        bind_context_menu(self.failed_label)

        # 隔行变色效果
        if index % 2 == 1:
            row_frame.configure(fg_color=get_color('gray_light'))
            content_container.configure(fg_color=get_color('gray_light'))

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

    def select_task(self, task):
        """选择任务"""
        # 清除之前的选中状态
        for task_id, item in self.task_items.items():
            item['frame'].configure(border_color=get_color('border_light'))

        # 设置当前选中状态
        task_id = task.get('id')
        if task_id in self.task_items:
            self.task_items[task_id]['frame'].configure(border_color=get_color('primary'), border_width=2)

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
        """显示任务菜单 - 兼容旧版本的按钮菜单"""
        self.selected_task = task
        self.show_context_menu_at_widget(widget, task)

    def show_more_menu(self):
        """显示更多操作菜单"""
        # 导入tkinter的Menu
        import tkinter as tk

        more_menu = tk.Menu(self.parent, tearoff=0,
                           bg=get_color('white'),
                           fg=get_color('text'),
                           activebackground=get_color('primary'),
                           activeforeground='white',
                           font=get_font('default'))

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
        except Exception as e:
            print(f"显示更多菜单时发生错误: {e}")
            # 备用方案：在鼠标位置显示
            try:
                import tkinter as tk
                root = self.more_button.winfo_toplevel()
                x = root.winfo_pointerx()
                y = root.winfo_pointery()
                more_menu.post(x, y)
            except:
                pass

    def create_context_menu(self):
        """创建右键菜单"""
        # 导入tkinter的Menu，因为CustomTkinter没有Menu组件
        import tkinter as tk

        self.context_menu = tk.Menu(self.parent, tearoff=0,
                                   bg=get_color('white'),
                                   fg=get_color('text'),
                                   activebackground=get_color('primary'),
                                   activeforeground='white',
                                   font=get_font('default'))

        self.context_menu.add_command(label="▶ 开始任务", command=self.start_task)
        self.context_menu.add_command(label="⏸ 暂停任务", command=self.pause_task)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="🔄 重试失败", command=self.retry_failed)
        self.context_menu.add_command(label="🧪 测试任务", command=self.test_task)
        self.context_menu.add_command(label="✏ 修改内容", command=self.edit_task)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="📤 导出-已完成", command=self.export_completed)
        self.context_menu.add_command(label="📤 导出-未完成", command=self.export_uncompleted)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="🗑 删除该任务", command=self.delete_task,
                                     foreground=get_color('danger'))

    def show_context_menu(self, event, task):
        """显示右键菜单"""
        self.selected_task = task

        # 根据任务状态动态更新菜单项
        self.update_context_menu_state(task)

        try:
            self.context_menu.post(event.x_root, event.y_root)
        except Exception as e:
            print(f"显示右键菜单时发生错误: {e}")

    def show_context_menu_at_widget(self, widget, task):
        """在指定控件位置显示右键菜单"""
        self.selected_task = task

        # 根据任务状态动态更新菜单项
        self.update_context_menu_state(task)

        try:
            x = widget.winfo_rootx()
            y = widget.winfo_rooty() + widget.winfo_height()
            self.context_menu.post(x, y)
        except Exception as e:
            print(f"显示菜单时发生错误: {e}")

    def update_context_menu_state(self, task):
        """根据任务状态更新右键菜单项"""
        if not self.context_menu:
            return

        status = task.get('status', 'stopped')

        try:
            # 清除现有菜单项
            self.context_menu.delete(0, 'end')

            # 根据状态添加相应菜单项
            if status in ['paused', 'stopped']:
                self.context_menu.add_command(label="▶ 开始任务", command=self.start_task)
            elif status == 'running':
                self.context_menu.add_command(label="⏸ 暂停任务", command=self.pause_task)
            else:
                self.context_menu.add_command(label="▶ 开始任务", command=self.start_task)
                self.context_menu.add_command(label="⏸ 暂停任务", command=self.pause_task)

            self.context_menu.add_separator()
            self.context_menu.add_command(label="🔄 重试失败", command=self.retry_failed)
            self.context_menu.add_command(label="🧪 测试任务", command=self.test_task)
            self.context_menu.add_command(label="✏ 修改内容", command=self.edit_task)
            self.context_menu.add_separator()
            self.context_menu.add_command(label="📤 导出-已完成", command=self.export_completed)
            self.context_menu.add_command(label="📤 导出-未完成", command=self.export_uncompleted)
            self.context_menu.add_separator()
            self.context_menu.add_command(label="🗑 删除该任务", command=self.delete_task,
                                         foreground=get_color('danger'))

        except Exception as e:
            print(f"更新右键菜单状态时发生错误: {e}")

    def update_task_progress(self, task_id, progress_data):
        """更新任务进度显示"""
        if task_id in self.task_items:
            item = self.task_items[task_id]

            # 更新进度文字
            progress = progress_data.get('progress', 0)
            progress_text = f"{progress:.1f}% ({progress_data.get('sent', 0)}/{progress_data.get('total', 0)})"
            item['progress_label'].configure(text=progress_text)

            # 更新统计信息
            item['success_label'].configure(text=str(progress_data.get('success_count', 0)))
            item['failed_label'].configure(text=str(progress_data.get('failed_count', 0)))

            # 更新状态徽章
            status = progress_data.get('status', 'stopped')
            status_text, status_style = self.get_status_info(status)
            item['status_badge'].configure(text=status_text)

    # 保持原有的所有方法逻辑不变，添加右键菜单功能
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
                    messagebox.showinfo("成功", f"已重试 {result.get('count', 0)} 个失败项目")
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

    """
    将以下方法添加到您的TaskListWidget类中，放在 refresh_tasks() 方法之前
    """

    def start_all_tasks(self):
        """开始所有任务"""
        if messagebox.askyesno("确认", "确定要开始所有停止的任务吗？"):
            try:
                result = self.task_service.start_all_tasks(self.user_info.get('operators_id'))
                if result['success']:
                    messagebox.showinfo("成功", f"已开始 {result.get('count', 0)} 个任务")
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
                    messagebox.showinfo("成功", f"已停止 {result.get('count', 0)} 个任务")
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
                    messagebox.showinfo("成功", f"已清理 {result.get('count', 0)} 个完成任务")
                    self.refresh_tasks()
                else:
                    messagebox.showerror("失败", result['message'])
            except Exception as e:
                messagebox.showerror("错误", f"清理完成任务失败：{str(e)}")

    def export_report(self):
        """导出任务报告"""
        if self.on_task_update:
            self.on_task_update('export_report', None)

    def refresh_tasks(self):
        """刷新任务列表"""
        self.load_tasks()

    def get_frame(self):
        """获取组件框架"""
        return self.card_container


def main():
    """测试现代化任务列表组件"""
    root = ctk.CTk()
    root.title("现代化任务列表测试")
    root.geometry("900x700")
    root.configure(fg_color=get_color('background'))

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
    task_list.get_frame().pack(fill='both', expand=True, padx=20, pady=20)

    root.mainloop()


if __name__ == '__main__':
    main()