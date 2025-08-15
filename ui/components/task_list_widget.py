"""
现代化任务列表组件 - CustomTkinter版本（修复版）
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import sys
import os
from typing import Dict, Any, List, Optional, Callable

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ui.styles import get_color, get_font, get_spacing, create_modern_button, create_card_frame, create_scrollable_frame, create_label, create_status_badge

# 尝试导入真实的TaskService
try:
    from services.task_service import task_service  # 使用全局实例
    USE_MOCK_SERVICE = False
except ImportError:
    USE_MOCK_SERVICE = True
    print("警告: 无法导入task_service，使用模拟服务")

    # 模拟的TaskService类
    class MockTaskService:
        def __init__(self):
            self.mock_tasks = []
            self.next_id = 1

        def get_user_tasks(self, user_id, status=None, page=1, page_size=20):
            """模拟获取用户任务"""
            # 如果没有任务，创建一些示例任务
            if not self.mock_tasks:
                self.mock_tasks = [
                    {
                        'id': 'v342',
                        'title': 'v342',
                        'status': 'stopped',
                        'total': 150,
                        'sent': 45,
                        'success_count': 38,
                        'failed_count': 7,
                        'pending_count': 105,
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
                        'pending_count': 80,
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
                        'pending_count': 150,
                        'progress': 0.0
                    }
                ]

            # 根据状态过滤
            filtered_tasks = self.mock_tasks
            if status:
                filtered_tasks = [t for t in self.mock_tasks if t.get('status') == status]

            # 分页
            start = (page - 1) * page_size
            end = start + page_size
            page_tasks = filtered_tasks[start:end]

            return {
                'success': True,
                'tasks': page_tasks,
                'total_count': len(filtered_tasks),
                'page': page,
                'page_size': page_size,
                'total_pages': (len(filtered_tasks) + page_size - 1) // page_size
            }

        def create_task(self, task_data):
            """模拟创建任务"""
            new_task = {
                'id': f'v{self.next_id:03d}',
                'title': task_data.get('title', f'新任务{self.next_id}'),
                'status': 'stopped',
                'total': len(task_data.get('targets', [])) or 100,
                'sent': 0,
                'success_count': 0,
                'failed_count': 0,
                'pending_count': len(task_data.get('targets', [])) or 100,
                'progress': 0.0
            }
            self.mock_tasks.insert(0, new_task)  # 添加到列表开头
            self.next_id += 1
            return {'success': True, 'task_id': new_task['id'], 'task_info': new_task}

        def start_task(self, task_id):
            for task in self.mock_tasks:
                if task['id'] == task_id:
                    task['status'] = 'running'
                    return {'success': True}
            return {'success': False, 'message': '任务不存在'}

        def pause_task(self, task_id):
            for task in self.mock_tasks:
                if task['id'] == task_id:
                    task['status'] = 'paused'
                    return {'success': True}
            return {'success': False, 'message': '任务不存在'}

        def stop_all_tasks(self, user_id):
            count = 0
            for task in self.mock_tasks:
                if task['status'] == 'running':
                    task['status'] = 'stopped'
                    count += 1
            return {'success': True, 'count': count}

        def start_all_tasks(self, user_id):
            count = 0
            for task in self.mock_tasks:
                if task['status'] in ['stopped', 'paused']:
                    task['status'] = 'running'
                    count += 1
            return {'success': True, 'count': count}

        def clear_completed_tasks(self, user_id):
            initial_count = len(self.mock_tasks)
            self.mock_tasks = [t for t in self.mock_tasks if t['status'] != 'completed']
            return {'success': True, 'count': initial_count - len(self.mock_tasks)}

        def retry_failed(self, task_id):
            for task in self.mock_tasks:
                if task['id'] == task_id:
                    retry_count = task.get('failed_count', 0)
                    task['failed_count'] = 0
                    task['pending_count'] += retry_count
                    return {'success': True, 'count': retry_count}
            return {'success': False, 'count': 0}

        def delete_task(self, task_id):
            self.mock_tasks = [t for t in self.mock_tasks if t['id'] != task_id]
            return {'success': True}

    # 如果需要使用模拟服务
    if USE_MOCK_SERVICE:
        task_service = MockTaskService()


class TaskListWidget:
    """现代化任务列表组件 - CustomTkinter版本"""

    def __init__(self, parent, user_info, on_task_select=None, on_task_update=None):
        self.parent = parent
        self.user_info = user_info
        self.on_task_select = on_task_select
        self.on_task_update = on_task_update
        self.task_service = task_service  # 使用全局服务实例
        self.selected_task = None
        self.tasks = []
        self.task_items = {}
        self.context_menu = None

        # 分页相关
        self.current_page = 1
        self.page_size = 20
        self.total_pages = 1

        # 创建UI
        self.create_widgets()
        self.create_context_menu()

        # 初始加载任务
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

        # 创建分页控制
        self.create_pagination()

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

        # 刷新按钮
        self.refresh_button = create_modern_button(
            left_buttons,
            text="🔄 刷新",
            style="secondary",
            command=self.refresh_tasks,
            width=80
        )
        self.refresh_button.pack(side='left', padx=(0, get_spacing('xs')))

        # 更多操作按钮
        self.more_button = create_modern_button(
            left_buttons,
            text="▼ 更多",
            style="secondary",
            command=self.show_more_menu,
            width=80
        )
        self.more_button.pack(side='left', padx=(0, get_spacing('xs')))

        # 右侧状态信息
        right_info = ctk.CTkFrame(button_container, fg_color='transparent')
        right_info.pack(side='right')

        self.task_count_label = create_label(
            right_info,
            text="共 0 个任务",
            style="default"
        )
        self.task_count_label.pack(side='right', padx=get_spacing('sm'))

    def create_list_header(self):
        """创建列表头部"""
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

        # 列标题定义
        columns = [
            ("任务", 160),
            ("进度", 80),
            ("成功", 60),
            ("失败", 60),
            ("状态", 60),
            ("操作", None)
        ]

        # 创建表头标签
        for col_name, width in columns:
            if width is not None:
                col_frame = ctk.CTkFrame(header_container, fg_color='transparent', width=width)
                col_frame.pack(side='left', fill='y', padx=1)
                col_frame.pack_propagate(False)

                header_label = create_label(col_frame, text=col_name, style="default")
                header_label.pack(expand=True, fill='both')
            else:
                header_label = create_label(header_container, text=col_name, style="default")
                header_label.pack(side='left', fill='both', expand=True, padx=(get_spacing('xs'), 0))

    def create_task_list_area(self):
        """创建任务列表区域"""
        # 创建可滚动框架
        self.scrollable_frame = create_scrollable_frame(
            self.content_frame,
            height=400
        )
        self.scrollable_frame.pack(fill='both', expand=True, padx=get_spacing('sm'), pady=get_spacing('sm'))

        # 创建空状态提示（初始隐藏）
        self.empty_label = create_label(
            self.scrollable_frame,
            text="暂无任务，点击‘添加任务’创建新任务",
            style="default"
        )
        self.empty_label.configure(text_color=get_color('text_light'))

    def create_pagination(self):
        """创建分页控制"""
        pagination_frame = ctk.CTkFrame(self.content_frame, fg_color='transparent')
        pagination_frame.pack(fill='x', padx=get_spacing('sm'), pady=get_spacing('sm'))

        # 上一页按钮
        self.prev_button = ctk.CTkButton(
            pagination_frame,
            text="上一页",
            command=self.prev_page,
            font=get_font('small'),
            width=80,
            height=28,
            fg_color=get_color('gray'),
            hover_color=get_color('hover_bg')
        )
        self.prev_button.pack(side='left', padx=(0, get_spacing('xs')))

        # 页码信息
        self.page_label = create_label(
            pagination_frame,
            text="第 1 / 1 页",
            style="default"
        )
        self.page_label.pack(side='left', padx=get_spacing('md'))

        # 下一页按钮
        self.next_button = ctk.CTkButton(
            pagination_frame,
            text="下一页",
            command=self.next_page,
            font=get_font('small'),
            width=80,
            height=28,
            fg_color=get_color('gray'),
            hover_color=get_color('hover_bg')
        )
        self.next_button.pack(side='left', padx=(get_spacing('xs'), 0))

    def load_tasks(self, keep_selection=False):
        """加载任务列表 - 支持从数据库加载"""
        try:
            print(f"[DEBUG] 开始加载任务列表 - 页码: {self.current_page}")

            # 保存当前选中的任务ID
            selected_task_id = None
            if keep_selection and self.selected_task:
                selected_task_id = self.selected_task.get('id')

            # 清空现有项目
            for widget in self.scrollable_frame.winfo_children():
                if widget != self.empty_label:
                    widget.destroy()
            self.task_items.clear()

            # 获取用户ID
            user_id = self.user_info.get('id') or self.user_info.get('operators_id', 1)

            # 如果没有真实的task_service，尝试直接从数据库加载
            if USE_MOCK_SERVICE:
                print("[DEBUG] 使用模拟服务，尝试从数据库加载...")
                result = self.load_tasks_from_database(user_id)
            else:
                result = self.task_service.get_user_tasks(
                    user_id,
                    status=None,
                    page=self.current_page,
                    page_size=self.page_size
                )

            if result.get('success'):
                self.tasks = result.get('tasks', [])
                total_count = result.get('total_count', 0)
                self.total_pages = result.get('total_pages', 1)

                # 更新任务计数
                self.task_count_label.configure(text=f"共 {total_count} 个任务")

                # 更新分页信息
                self.page_label.configure(text=f"第 {self.current_page} / {self.total_pages} 页")
                self.update_pagination_buttons()

                if self.tasks:
                    # 隐藏空状态提示
                    self.empty_label.pack_forget()

                    # 创建任务列表项
                    for i, task in enumerate(self.tasks):
                        self.create_task_item(task, i)

                        # 恢复选中状态
                        if keep_selection and task.get('id') == selected_task_id:
                            self.select_task(task)

                    print(f"成功加载 {len(self.tasks)} 个任务")
                else:
                    # 显示空状态提示
                    self.empty_label.pack(expand=True, pady=50)
                    print("任务列表为空")
            else:
                print(f"加载任务失败: {result.get('message', '未知错误')}")
                self.empty_label.configure(text="加载任务失败，请重试")
                self.empty_label.pack(expand=True, pady=50)

        except Exception as e:
            print(f"加载任务列表异常: {str(e)}")
            import traceback
            traceback.print_exc()

            self.empty_label.configure(text=f"加载失败: {str(e)}")
            self.empty_label.pack(expand=True, pady=50)

    def load_tasks_from_database(self, user_id):
        """直接从数据库加载任务"""
        try:
            from database.connection import execute_query

            # 计算分页
            offset = (self.current_page - 1) * self.page_size

            # 查询任务总数
            count_query = """
                SELECT COUNT(*) 
                FROM tasks 
                WHERE operators_id = %s
            """
            count_result = execute_query(count_query, (user_id,), fetch_one=True)
            total_count = count_result[0] if count_result else 0

            # 查询任务列表
            tasks_query = """
                SELECT 
                    tasks_id as id,
                    tasks_title as title,
                    tasks_mode as mode,
                    tasks_status as status,
                    tasks_total_count as total,
                    tasks_success_count as success_count,
                    tasks_failed_count as failed_count,
                    tasks_pending_count as pending_count,
                    CASE 
                        WHEN tasks_total_count > 0 
                        THEN ROUND((tasks_success_count + tasks_failed_count) * 100.0 / tasks_total_count, 1)
                        ELSE 0 
                    END as progress
                FROM tasks 
                WHERE operators_id = %s
                ORDER BY created_time DESC
                LIMIT %s OFFSET %s
            """

            tasks = execute_query(
                tasks_query,
                (user_id, self.page_size, offset),
                dict_cursor=True
            )

            if not tasks:
                tasks = []

            # 计算 sent 字段（兼容旧代码）
            for task in tasks:
                task['sent'] = task.get('success_count', 0) + task.get('failed_count', 0)
                # 确保 pending_count 正确
                if task.get('pending_count') is None:
                    task['pending_count'] = task.get('total', 0) - task['sent']

            print(f"[DEBUG] 从数据库加载了 {len(tasks)} 个任务")

            return {
                'success': True,
                'tasks': tasks,
                'total_count': total_count,
                'page': self.current_page,
                'page_size': self.page_size,
                'total_pages': (total_count + self.page_size - 1) // self.page_size if total_count > 0 else 1
            }

        except Exception as e:
            print(f"[ERROR] 从数据库加载任务失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'tasks': [],
                'total_count': 0,
                'page': self.current_page,
                'page_size': self.page_size,
                'total_pages': 1
            }

    def create_task_item(self, task, index):
        """创建单个任务项"""
        task_id = task.get('id')

        # 任务行容器
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

        # 任务名称列
        name_frame = ctk.CTkFrame(content_container, fg_color='transparent', width=140)
        name_frame.pack(side='left', fill='y', padx=1)
        name_frame.pack_propagate(False)

        task_name = task.get('title', f"任务{task.get('id', '')}")
        name_label = create_label(name_frame, text=task_name, style="medium")
        name_label.pack(fill='both', expand=True, padx=(0, get_spacing('sm')))

        # 进度列
        progress_frame = ctk.CTkFrame(content_container, fg_color='transparent', width=80)
        progress_frame.pack(side='left', fill='y', padx=1)
        progress_frame.pack_propagate(False)

        progress = task.get('progress', 0)
        sent = task.get('sent', task.get('success_count', 0) + task.get('failed_count', 0))
        total = task.get('total', 1)

        progress_text = f"{progress:.1f}%"
        detail_text = f"({sent}/{total})"

        progress_label = create_label(progress_frame, text=progress_text, style="default")
        progress_label.pack(anchor='center')

        detail_label = create_label(progress_frame, text=detail_text, style="small")
        detail_label.configure(text_color=get_color('text_light'))
        detail_label.pack(anchor='center')

        progress_bar = ctk.CTkProgressBar(
            progress_frame,
            height=4,
            corner_radius=2,
            progress_color=get_color('primary'),
            fg_color=get_color('gray_light')
        )
        progress_bar.pack(fill='x', pady=(1, 0), padx=2)
        progress_bar.set(progress / 100.0 if progress <= 100 else 1.0)

        # 成功列
        success_frame = ctk.CTkFrame(content_container, fg_color='transparent', width=60)
        success_frame.pack(side='left', fill='y', padx=1)
        success_frame.pack_propagate(False)

        success_label = create_label(
            success_frame,
            text=str(task.get('success_count', 0)),
            style="default"
        )
        success_label.configure(text_color=get_color('success'))
        success_label.pack(anchor='center', expand=True)

        # 失败列
        failed_frame = ctk.CTkFrame(content_container, fg_color='transparent', width=60)
        failed_frame.pack(side='left', fill='y', padx=1)
        failed_frame.pack_propagate(False)

        failed_label = create_label(
            failed_frame,
            text=str(task.get('failed_count', 0)),
            style="default"
        )
        failed_label.configure(text_color=get_color('danger'))
        failed_label.pack(anchor='center', expand=True)

        # 状态列
        status_frame = ctk.CTkFrame(content_container, fg_color='transparent', width=60)
        status_frame.pack(side='left', fill='y', padx=1)
        status_frame.pack_propagate(False)

        status = task.get('status', 'stopped')
        status_text, status_style = self.get_status_info(status)

        status_badge = create_status_badge(
            status_frame,
            text=status_text,
            status_type=status_style
        )
        status_badge.pack(anchor='center', expand=True)

        # 操作列
        action_frame = ctk.CTkFrame(content_container, fg_color='transparent')
        action_frame.pack(side='right', fill='both', expand=True, padx=(get_spacing('xs'), 0))

        button_container = ctk.CTkFrame(action_frame, fg_color='transparent')
        button_container.pack(expand=True, fill='both')

        # 根据状态显示不同的快捷操作按钮
        if status == 'running':
            action_btn = ctk.CTkButton(
                button_container,
                text="⏸ 暂停",
                command=lambda t_id=task_id: self.pause_task_by_id(t_id),
                font=get_font('small'),
                width=65,
                height=26,
                fg_color=get_color('warning'),
                hover_color='#FB8C00'
            )
        elif status in ['paused', 'stopped', 'draft']:
            action_btn = ctk.CTkButton(
                button_container,
                text="▶ 开始",
                command=lambda t_id=task_id: self.start_task_by_id(t_id),
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
                command=lambda t=task: self.select_task(t),
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
            command=lambda t=task, w=button_container: self.show_task_menu(t, w),
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
            'progress_label': progress_label,
            'success_label': success_label,
            'failed_label': failed_label,
            'status_badge': status_badge,
            'content_container': content_container
        }

        # 绑定点击选择事件
        def bind_click_events(widget):
            widget.bind("<Button-1>", lambda e, t=task: self.select_task(t))

        # 绑定右键菜单事件
        def bind_context_menu(widget):
            widget.bind("<Button-3>", lambda e, t=task: self.show_context_menu(e, t))

        # 为行元素绑定事件
        bind_click_events(row_frame)
        bind_click_events(content_container)
        bind_click_events(name_label)
        bind_context_menu(row_frame)
        bind_context_menu(content_container)

        # 隔行变色
        if index % 2 == 1:
            row_frame.configure(fg_color=get_color('gray_light'))

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
            item['frame'].configure(border_color=get_color('border_light'), border_width=1)

        # 设置当前选中状态
        task_id = task.get('id')
        if task_id in self.task_items:
            self.task_items[task_id]['frame'].configure(border_color=get_color('primary'), border_width=2)

        self.selected_task = task

        # 调用回调函数
        if self.on_task_select:
            self.on_task_select(task)

    def refresh_tasks(self):
        """刷新任务列表（保持当前页）"""
        print("刷新任务列表...")
        self.load_tasks(keep_selection=True)

    def load_tasks_from_database(self, user_id):
        """直接从数据库加载任务"""
        try:
            from database.connection import execute_query

            # 计算分页
            offset = (self.current_page - 1) * self.page_size

            # 查询任务总数
            count_query = """
                SELECT COUNT(*) 
                FROM tasks 
                WHERE operators_id = %s
            """
            count_result = execute_query(count_query, (user_id,), fetch_one=True)
            total_count = count_result[0] if count_result else 0

            # 查询任务列表
            tasks_query = """
                SELECT 
                    tasks_id as id,
                    tasks_title as title,
                    tasks_mode as mode,
                    tasks_status as status,
                    tasks_total_count as total,
                    tasks_success_count as success_count,
                    tasks_failed_count as failed_count,
                    tasks_pending_count as pending_count,
                    CASE 
                        WHEN tasks_total_count > 0 
                        THEN ROUND((tasks_success_count + tasks_failed_count) * 100.0 / tasks_total_count, 1)
                        ELSE 0 
                    END as progress
                FROM tasks 
                WHERE operators_id = %s
                ORDER BY created_time DESC
                LIMIT %s OFFSET %s
            """

            tasks = execute_query(
                tasks_query,
                (user_id, self.page_size, offset),
                dict_cursor=True
            )

            if not tasks:
                tasks = []

            # 计算 sent 字段（兼容旧代码）
            for task in tasks:
                task['sent'] = task.get('success_count', 0) + task.get('failed_count', 0)
                # 确保 pending_count 正确
                if task.get('pending_count') is None:
                    task['pending_count'] = task.get('total', 0) - task['sent']

            print(f"[DEBUG] 从数据库加载了 {len(tasks)} 个任务")

            return {
                'success': True,
                'tasks': tasks,
                'total_count': total_count,
                'page': self.current_page,
                'page_size': self.page_size,
                'total_pages': (total_count + self.page_size - 1) // self.page_size if total_count > 0 else 1
            }

        except Exception as e:
            print(f"[ERROR] 从数据库加载任务失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'tasks': [],
                'total_count': 0,
                'page': self.current_page,
                'page_size': self.page_size,
                'total_pages': 1
            }

    def reload_tasks(self):
        """重新加载任务列表（返回第一页）"""
        print("[DEBUG] 重新加载任务列表...")
        self.current_page = 1
        self.load_tasks(keep_selection=False)

    def add_task(self):
        """添加任务 - 触发添加任务对话框"""
        try:
            # 如果有外部回调，使用回调
            if self.on_task_update:
                self.on_task_update('add', None)
            else:
                # 否则直接在这里处理
                print("[DEBUG] 直接处理添加任务...")
                from ui.dialogs.add_task_dialog import AddTaskDialog
                dialog = AddTaskDialog(self.parent, self.user_info)
                result = dialog.show()

                if result and result.get('success'):
                    print(f"[DEBUG] 任务创建成功: {result}")
                    # 刷新任务列表
                    self.reload_tasks()

        except Exception as e:
            print(f"[ERROR] 添加任务失败: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("错误", f"添加任务失败：{str(e)}")

    def prev_page(self):
        """上一页"""
        if self.current_page > 1:
            self.current_page -= 1
            self.load_tasks()

    def next_page(self):
        """下一页"""
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.load_tasks()

    def update_pagination_buttons(self):
        """更新分页按钮状态"""
        self.prev_button.configure(state='normal' if self.current_page > 1 else 'disabled')
        self.next_button.configure(state='normal' if self.current_page < self.total_pages else 'disabled')

    def on_task_update(self, action, task):
        """任务更新回调 - 处理各种任务操作"""
        try:
            print(f"[DEBUG] on_task_update: action={action}, task={task}")

            if action == 'add':
                # 显示添加任务对话框
                from ui.dialogs.add_task_dialog import AddTaskDialog
                dialog = AddTaskDialog(self.parent, self.user_info)
                result = dialog.show()

                if result and result.get('success'):
                    print(f"[DEBUG] 任务添加成功: {result}")
                    # 直接调用 reload_tasks 刷新列表
                    self.reload_tasks()

            elif action == 'test':
                if self.on_task_update:
                    self.on_task_update('test', task)
            elif action == 'edit':
                if self.on_task_update:
                    self.on_task_update('edit', task)
            elif action == 'export_completed':
                if self.on_task_update:
                    self.on_task_update('export_completed', task)
            elif action == 'export_uncompleted':
                if self.on_task_update:
                    self.on_task_update('export_uncompleted', task)
            elif action == 'export_report':
                if self.on_task_update:
                    self.on_task_update('export_report', None)

        except Exception as e:
            print(f"[ERROR] 任务操作失败: {e}")
            import traceback
            traceback.print_exc()

    def add_task_to_list(self, new_task):
        """添加新任务到列表（由外部调用）"""
        print(f"添加新任务到列表: {new_task}")
        # 重新加载列表以显示新任务
        self.reload_tasks()

    # ... 其他方法保持不变 ...

    def start_task_by_id(self, task_id):
        """通过ID开始任务"""
        try:
            result = self.task_service.start_task(task_id)
            if result.get('success'):
                messagebox.showinfo("成功", "任务已开始")
                self.refresh_tasks()
            else:
                messagebox.showerror("失败", result.get('message', '启动失败'))
        except Exception as e:
            messagebox.showerror("错误", f"开始任务失败：{str(e)}")

    def pause_task_by_id(self, task_id):
        """通过ID暂停任务"""
        try:
            result = self.task_service.pause_task(task_id)
            if result.get('success'):
                messagebox.showinfo("成功", "任务已暂停")
                self.refresh_tasks()
            else:
                messagebox.showerror("失败", result.get('message', '暂停失败'))
        except Exception as e:
            messagebox.showerror("错误", f"暂停任务失败：{str(e)}")

    def stop_sending(self):
        """停止发送"""
        if messagebox.askyesno("确认", "确定要停止所有正在发送的任务吗？"):
            try:
                user_id = self.user_info.get('id') or self.user_info.get('operators_id', 1)
                result = self.task_service.stop_all_tasks(user_id)
                if result.get('success'):
                    messagebox.showinfo("成功", f"已停止 {result.get('count', 0)} 个任务")
                    self.refresh_tasks()
                else:
                    messagebox.showerror("失败", result.get('message', '停止失败'))
            except Exception as e:
                messagebox.showerror("错误", f"停止发送失败：{str(e)}")

    def add_task(self):
        """添加任务 - 触发添加任务对话框"""
        try:
            # 如果有外部回调，使用回调
            if self.on_task_update:
                self.on_task_update('add', None)
            else:
                # 否则直接在这里处理
                print("[DEBUG] 直接处理添加任务...")
                from ui.dialogs.add_task_dialog import AddTaskDialog
                dialog = AddTaskDialog(self.parent, self.user_info)
                result = dialog.show()

                if result and result.get('success'):
                    print(f"[DEBUG] 任务创建成功: {result}")
                    # 刷新任务列表
                    self.reload_tasks()

        except Exception as e:
            print(f"[ERROR] 添加任务失败: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("错误", f"添加任务失败：{str(e)}")

    def show_more_menu(self):
        """显示更多操作菜单"""
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

        try:
            x = self.more_button.winfo_rootx()
            y = self.more_button.winfo_rooty() + self.more_button.winfo_height()
            more_menu.post(x, y)
        except Exception:
            pass

    def show_task_menu(self, task, widget):
        """显示任务菜单"""
        self.selected_task = task
        self.show_context_menu_at_widget(widget, task)

    def create_context_menu(self):
        """创建右键菜单"""
        self.context_menu = tk.Menu(self.parent, tearoff=0,
                                   bg=get_color('white'),
                                   fg=get_color('text'),
                                   activebackground=get_color('primary'),
                                   activeforeground='white',
                                   font=get_font('default'))

    def show_context_menu(self, event, task):
        """显示右键菜单"""
        self.selected_task = task
        self.update_context_menu_state(task)
        try:
            self.context_menu.post(event.x_root, event.y_root)
        except Exception:
            pass

    def show_context_menu_at_widget(self, widget, task):
        """在指定控件位置显示右键菜单"""
        self.selected_task = task
        self.update_context_menu_state(task)
        try:
            x = widget.winfo_rootx()
            y = widget.winfo_rooty() + widget.winfo_height()
            self.context_menu.post(x, y)
        except Exception:
            pass

    def update_context_menu_state(self, task):
        """根据任务状态更新右键菜单项"""
        if not self.context_menu:
            return

        status = task.get('status', 'stopped')

        try:
            self.context_menu.delete(0, 'end')

            if status in ['paused', 'stopped', 'draft']:
                self.context_menu.add_command(label="▶ 开始任务", command=self.start_task)
            elif status == 'running':
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
        except Exception:
            pass

    # 任务操作方法
    def start_task(self):
        if self.selected_task:
            self.start_task_by_id(self.selected_task['id'])

    def pause_task(self):
        if self.selected_task:
            self.pause_task_by_id(self.selected_task['id'])

    def retry_failed(self):
        if not self.selected_task:
            return
        if messagebox.askyesno("确认", f"确定要重试任务的失败项目吗？"):
            try:
                result = self.task_service.retry_failed(self.selected_task['id'])
                if result.get('success'):
                    messagebox.showinfo("成功", f"已重试 {result.get('count', 0)} 个失败项目")
                    self.refresh_tasks()
            except Exception as e:
                messagebox.showerror("错误", f"重试失败：{str(e)}")

    def test_task(self):
        if self.selected_task and self.on_task_update:
            self.on_task_update('test', self.selected_task)

    def edit_task(self):
        if self.selected_task and self.on_task_update:
            self.on_task_update('edit', self.selected_task)

    def delete_task(self):
        if not self.selected_task:
            return
        if messagebox.askyesno("确认删除", "确定要删除该任务吗？\n此操作不可恢复！"):
            try:
                result = self.task_service.delete_task(self.selected_task['id'])
                if result.get('success'):
                    messagebox.showinfo("成功", "任务已删除")
                    self.selected_task = None
                    self.refresh_tasks()
            except Exception as e:
                messagebox.showerror("错误", f"删除任务失败：{str(e)}")

    def export_completed(self):
        if self.selected_task and self.on_task_update:
            self.on_task_update('export_completed', self.selected_task)

    def export_uncompleted(self):
        if self.selected_task and self.on_task_update:
            self.on_task_update('export_uncompleted', self.selected_task)

    def start_all_tasks(self):
        if messagebox.askyesno("确认", "确定要开始所有停止的任务吗？"):
            try:
                user_id = self.user_info.get('id') or self.user_info.get('operators_id', 1)
                result = self.task_service.start_all_tasks(user_id)
                if result.get('success'):
                    messagebox.showinfo("成功", f"已开始 {result.get('count', 0)} 个任务")
                    self.refresh_tasks()
            except Exception as e:
                messagebox.showerror("错误", f"开始所有任务失败：{str(e)}")

    def stop_all_tasks(self):
        if messagebox.askyesno("确认", "确定要停止所有正在运行的任务吗？"):
            try:
                user_id = self.user_info.get('id') or self.user_info.get('operators_id', 1)
                result = self.task_service.stop_all_tasks(user_id)
                if result.get('success'):
                    messagebox.showinfo("成功", f"已停止 {result.get('count', 0)} 个任务")
                    self.refresh_tasks()
            except Exception as e:
                messagebox.showerror("错误", f"停止所有任务失败：{str(e)}")

    def clear_completed(self):
        if messagebox.askyesno("确认", "确定要清理所有已完成的任务吗？\n此操作不可恢复！"):
            try:
                user_id = self.user_info.get('id') or self.user_info.get('operators_id', 1)
                result = self.task_service.clear_completed_tasks(user_id)
                if result.get('success'):
                    messagebox.showinfo("成功", f"已清理 {result.get('count', 0)} 个完成任务")
                    self.refresh_tasks()
            except Exception as e:
                messagebox.showerror("错误", f"清理完成任务失败：{str(e)}")

    def export_report(self):
        if self.on_task_update:
            self.on_task_update('export_report', None)

    def get_frame(self):
        """获取组件框架"""
        return self.card_container


def main():
    """测试任务列表组件"""
    root = ctk.CTk()
    root.title("任务列表测试")
    root.geometry("900x700")
    root.configure(fg_color=get_color('background'))

    user_info = {
        'operators_id': 1,
        'operators_username': 'test_user',
        'operators_available_credits': 10000
    }

    def on_task_select(task):
        print(f"选中任务: {task}")

    def on_task_update(action, task):
        print(f"任务操作: {action}, 任务: {task}")
        if action == 'add':
            # 模拟添加任务后刷新
            task_list.reload_tasks()

    task_list = TaskListWidget(root, user_info, on_task_select, on_task_update)
    task_list.get_frame().pack(fill='both', expand=True, padx=20, pady=20)

    root.mainloop()


if __name__ == '__main__':
    main()