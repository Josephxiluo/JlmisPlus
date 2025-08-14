"""
添加任务对话框 - 简化布局版
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sys
import os
import pandas as pd
import csv

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ui.styles import get_color, get_font

# 导入服务时处理异常
try:
    from services.task_service import TaskService
    from database.connection import execute_query
except ImportError:
    # 创建模拟服务类
    class TaskService:
        def create_task(self, task_data):
            print("模拟创建任务:", task_data)
            return {'success': True, 'message': '任务创建成功', 'task_id': 1}

    def execute_query(query, params=None, fetch_one=False, dict_cursor=False):
        # 模拟查询消息模板
        if 'message_templates' in query:
            return [
                (1, '通知模板', '这是一条通知消息'),
                (2, '营销模板', '这是一条营销消息'),
                (3, '验证码模板', '您的验证码是：{code}')
            ]
        return []


class AddTaskDialog:
    """添加任务对话框 - 简化布局版"""

    def __init__(self, parent, user_info):
        self.parent = parent
        self.user_info = user_info
        self.task_service = TaskService()
        self.result = None
        self.target_file_path = None
        self.message_templates = []
        self.create_dialog()
        self.load_message_templates()

    def create_dialog(self):
        """创建对话框"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("添加任务")
        self.dialog.geometry("600x700")
        self.dialog.resizable(True, True)
        self.dialog.minsize(600, 650)
        self.dialog.configure(bg=get_color('background'))

        # 设置模态对话框
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        # 居中显示
        self.center_dialog()

        # 直接创建表单和按钮，不使用复杂的滚动容器
        self.create_main_content()

    def center_dialog(self):
        """对话框居中显示"""
        self.dialog.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (600 // 2)
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (700 // 2)
        self.dialog.geometry(f"600x700+{x}+{y}")

    def create_main_content(self):
        """创建主要内容"""
        # 创建主框架
        main_frame = tk.Frame(self.dialog, bg=get_color('background'))
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)

        # 创建内容滚动区域
        self.create_scroll_content(main_frame)

        # 创建固定按钮区域
        self.create_fixed_buttons(main_frame)

    def create_scroll_content(self, parent):
        """创建滚动内容区域"""
        # 内容框架（留出底部按钮空间）
        content_frame = tk.Frame(parent, bg=get_color('background'))
        content_frame.pack(fill='both', expand=True, pady=(0, 70))  # 底部留出70px给按钮

        # 创建Canvas和滚动条
        canvas = tk.Canvas(content_frame, bg=get_color('background'), highlightthickness=0)
        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)

        # 滚动内容框架
        scroll_frame = tk.Frame(canvas, bg=get_color('background'))

        # 配置滚动
        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        scroll_frame.bind("<Configure>", on_frame_configure)

        # 配置Canvas窗口
        canvas_frame = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")

        def on_canvas_configure(event):
            canvas.itemconfig(canvas_frame, width=event.width)

        canvas.bind('<Configure>', on_canvas_configure)
        canvas.configure(yscrollcommand=scrollbar.set)

        # 布局Canvas和滚动条
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 鼠标滚轮支持
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        canvas.bind("<MouseWheel>", _on_mousewheel)
        canvas.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

        # 创建表单内容
        self.create_form_content(scroll_frame)

    def create_form_content(self, parent):
        """创建表单内容"""
        # 表单容器
        form_frame = tk.Frame(parent, bg=get_color('background'))
        form_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # 1. 短信模式选择
        self.create_field(form_frame, "短信模式:", required=True)
        mode_frame = tk.Frame(form_frame, bg=get_color('background'))
        mode_frame.pack(fill='x', pady=(0, 15))

        self.sms_mode_var = tk.StringVar(value="sms")

        sms_radio = tk.Radiobutton(
            mode_frame,
            text="短信模式",
            variable=self.sms_mode_var,
            value="sms",
            font=get_font('default'),
            bg=get_color('background'),
            command=self.on_mode_change
        )
        sms_radio.pack(side='left')

        mms_radio = tk.Radiobutton(
            mode_frame,
            text="彩信模式",
            variable=self.sms_mode_var,
            value="mms",
            font=get_font('default'),
            bg=get_color('background'),
            command=self.on_mode_change
        )
        mms_radio.pack(side='left', padx=(20, 0))

        # 2. 任务名称 - 左右布局
        task_name_row = tk.Frame(form_frame, bg=get_color('background'))
        task_name_row.pack(fill='x', pady=(0, 15))

        # 左侧标签
        task_name_label_frame = tk.Frame(task_name_row, bg=get_color('background'), width=100)
        task_name_label_frame.pack(side='left', fill='y')
        task_name_label_frame.pack_propagate(False)

        self.create_field(task_name_label_frame, "任务名称:", required=True)

        # 右侧输入框
        self.task_name_entry = tk.Entry(
            task_name_row,
            font=get_font('default'),
            relief='solid',
            bd=1
        )
        self.task_name_entry.pack(side='right', fill='x', expand=True, padx=(10, 0))
        self.task_name_entry.bind('<KeyRelease>', self.limit_task_name)

        # 3. 目标号码 - 标题和提示放在一行
        target_header_row = tk.Frame(form_frame, bg=get_color('background'))
        target_header_row.pack(fill='x', pady=(0, 5))

        self.create_field(target_header_row, "目标号码:", required=True)

        tip_label = tk.Label(
            target_header_row,
            text="提示：多个号码请换行输入，每行一个号码",
            font=('Microsoft YaHei', 8),
            fg=get_color('text_light'),
            bg=get_color('background')
        )
        tip_label.pack(side='right')

        # 目标号码输入区域 - 增加高度
        target_container = tk.Frame(form_frame, bg=get_color('background'))
        target_container.pack(fill='x', pady=(0, 15))

        self.target_text = tk.Text(
            target_container,
            font=get_font('default'),
            relief='solid',
            bd=1,
            height=6,
            wrap='word'
        )
        self.target_text.pack(side='left', fill='both', expand=True)

        target_scroll = ttk.Scrollbar(target_container, orient='vertical', command=self.target_text.yview)
        self.target_text.configure(yscrollcommand=target_scroll.set)
        target_scroll.pack(side='right', fill='y')

        # 4. 文件操作按钮区域
        file_button_frame = tk.Frame(form_frame, bg=get_color('background'))
        file_button_frame.pack(fill='x', pady=(0, 15))

        # 上传文件按钮
        upload_btn = tk.Button(
            file_button_frame,
            text="📁 导入号码文件",
            font=get_font('button'),
            bg=get_color('primary'),
            fg='#5D4037',
            relief='flat',
            cursor='hand2',
            command=self.upload_file,
            width=15,
            height=1
        )
        upload_btn.pack(side='left', padx=(0, 10))

        # 清空号码按钮
        clear_btn = tk.Button(
            file_button_frame,
            text="🗑 清空号码",
            font=get_font('button'),
            bg='#F5F5F5',
            fg='#333333',
            relief='solid',
            bd=1,
            cursor='hand2',
            command=self.clear_phone_numbers,
            width=12,
            height=1
        )
        clear_btn.pack(side='left')

        # 号码计数标签
        self.phone_count_label = tk.Label(
            file_button_frame,
            text="共 0 个号码",
            font=get_font('small'),
            fg=get_color('text_light'),
            bg=get_color('background')
        )
        self.phone_count_label.pack(side='right', padx=(20, 0))

        # 5. 模板和号码模式一行显示
        template_row = tk.Frame(form_frame, bg=get_color('background'))
        template_row.pack(fill='x', pady=(0, 15))

        # 左侧：短信模板
        template_left = tk.Frame(template_row, bg=get_color('background'))
        template_left.pack(side='left', fill='both', expand=True, padx=(0, 10))

        self.create_field(template_left, "短信模板:", required=True)
        self.template_var = tk.StringVar()
        self.template_combo = ttk.Combobox(
            template_left,
            textvariable=self.template_var,
            values=[],
            state='readonly',
            font=get_font('default')
        )
        self.template_combo.pack(fill='x')
        self.template_combo.bind('<<ComboboxSelected>>', self.on_template_select)

        # 右侧：号码模式
        mode_right = tk.Frame(template_row, bg=get_color('background'))
        mode_right.pack(side='right', fill='both', expand=True, padx=(10, 0))

        self.create_field(mode_right, "号码模式:", required=True)
        self.number_mode_var = tk.StringVar()
        mode_combo = ttk.Combobox(
            mode_right,
            textvariable=self.number_mode_var,
            values=["国内号码", "国际号码"],
            state='readonly',
            font=get_font('default')
        )
        mode_combo.pack(fill='x')
        mode_combo.set("国内号码")

        # 6. 主题（彩信专用，初始隐藏）- 左右布局
        self.subject_container = tk.Frame(form_frame, bg=get_color('background'))

        # 左侧标签
        subject_label_frame = tk.Frame(self.subject_container, bg=get_color('background'), width=100)
        subject_label_frame.pack(side='left', fill='y')
        subject_label_frame.pack_propagate(False)

        self.subject_label = tk.Label(
            subject_label_frame,
            text="* 主题:",
            font=get_font('default'),
            fg=get_color('danger'),
            bg=get_color('background')
        )
        self.subject_label.pack(anchor='w')

        # 右侧输入框
        self.subject_entry = tk.Entry(
            self.subject_container,
            font=get_font('default'),
            relief='solid',
            bd=1
        )
        self.subject_entry.pack(side='right', fill='x', expand=True, padx=(10, 0))

        # 7. 短信内容
        self.create_field(form_frame, "短信内容:", required=True)

        content_container = tk.Frame(form_frame, bg=get_color('background'))
        content_container.pack(fill='both', expand=True, pady=(0, 20))

        self.content_text = tk.Text(
            content_container,
            font=get_font('default'),
            relief='solid',
            bd=1,
            height=5,
            wrap='word'
        )
        self.content_text.pack(side='left', fill='both', expand=True)

        content_scroll = ttk.Scrollbar(content_container, orient='vertical', command=self.content_text.yview)
        self.content_text.configure(yscrollcommand=content_scroll.set)
        content_scroll.pack(side='right', fill='y')

        # 初始状态
        self.update_mode_fields()

        # 绑定文本变化事件以更新计数
        self.target_text.bind('<KeyRelease>', self.on_target_text_change)

    def create_fixed_buttons(self, parent):
        """创建固定按钮区域"""
        # 按钮容器 - 固定在底部
        button_container = tk.Frame(parent, bg=get_color('background'))
        button_container.pack(side='bottom', fill='x', pady=(10, 0))

        # 分隔线
        separator = tk.Frame(button_container, height=1, bg='#DDDDDD')
        separator.pack(fill='x', pady=(0, 15))

        # 按钮框架
        button_frame = tk.Frame(button_container, bg=get_color('background'))
        button_frame.pack(fill='x')

        # 取消按钮
        cancel_btn = tk.Button(
            button_frame,
            text="取消",
            font=get_font('button'),
            bg='#F5F5F5',
            fg='#333333',
            relief='solid',
            bd=1,
            cursor='hand2',
            command=self.cancel,
            width=12,
            height=2
        )
        cancel_btn.pack(side='left', padx=(0, 10))

        # 保存按钮
        save_btn = tk.Button(
            button_frame,
            text="保存",
            font=get_font('button'),
            bg=get_color('primary'),
            fg='#000000',
            relief='flat',
            cursor='hand2',
            command=self.save,
            width=12,
            height=2
        )
        save_btn.pack(side='left', padx=(0, 10))

        # 提交按钮
        submit_btn = tk.Button(
            button_frame,
            text="提交",
            font=get_font('button'),
            bg=get_color('success'),
            fg='#000000',
            relief='flat',
            cursor='hand2',
            command=self.submit,
            width=12,
            height=2
        )
        submit_btn.pack(side='right')

    def load_message_templates(self):
        """加载消息模板"""
        try:
            query = """
            SELECT templates_id, templates_name, templates_content 
            FROM message_templates 
            ORDER BY templates_name
            """
            templates = execute_query(query, dict_cursor=True)

            if templates:
                self.message_templates = templates
                template_values = [f"{t['templates_name']}" for t in templates]
                self.template_combo['values'] = template_values
                if template_values:
                    self.template_combo.set(template_values[0])
                    self.on_template_select()

        except Exception as e:
            print(f"加载消息模板失败: {e}")
            self.message_templates = [
                {'templates_id': 1, 'templates_name': '默认模板', 'templates_content': '请输入短信内容'}
            ]

    def create_field(self, parent, text, required=False):
        """创建字段标签"""
        color = get_color('danger') if required else get_color('text')
        marker = "* " if required else ""

        label = tk.Label(
            parent,
            text=f"{marker}{text}",
            font=get_font('default'),
            fg=color,
            bg=get_color('background')
        )
        label.pack(anchor='w', pady=(0, 5))
        return label

    def limit_task_name(self, event=None):
        """限制任务名称长度"""
        content = self.task_name_entry.get()
        if len(content) > 20:
            self.task_name_entry.delete(20, 'end')

    def on_mode_change(self):
        """短信模式改变事件"""
        self.update_mode_fields()

    def update_mode_fields(self):
        """更新模式相关字段状态"""
        is_mms = self.sms_mode_var.get() == "mms"

        if is_mms:
            self.subject_container.pack(fill='x', pady=(0, 15))
        else:
            self.subject_container.pack_forget()
            self.subject_entry.delete(0, 'end')

    def on_template_select(self, event=None):
        """模板选择改变事件"""
        try:
            selected_template = self.template_var.get()
            if selected_template and self.message_templates:
                for template in self.message_templates:
                    if template['templates_name'] == selected_template:
                        self.content_text.delete('1.0', 'end')
                        self.content_text.insert('1.0', template['templates_content'])
                        break
        except Exception as e:
            print(f"模板选择处理失败: {e}")

    def on_target_text_change(self, event=None):
        """目标文本框内容变化时更新计数"""
        content = self.target_text.get('1.0', 'end').strip()
        if content:
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            valid_count = sum(1 for line in lines if self.is_phone_number(line))
            self.update_phone_count_display(valid_count)
        else:
            self.update_phone_count_display(0)

    def get_selected_template_id(self):
        """获取选中的模板ID"""
        selected_template = self.template_var.get()
        if selected_template and self.message_templates:
            for template in self.message_templates:
                if template['templates_name'] == selected_template:
                    return template['templates_id']
        return None

    def validate_form(self):
        """验证表单"""
        if not self.task_name_entry.get().strip():
            messagebox.showerror("错误", "请输入任务名称")
            self.task_name_entry.focus()
            return False

        if not self.target_text.get('1.0', 'end').strip():
            messagebox.showerror("错误", "请输入目标号码")
            self.target_text.focus()
            return False

        if not self.template_var.get():
            messagebox.showerror("错误", "请选择短信模板")
            self.template_combo.focus()
            return False

        if not self.content_text.get('1.0', 'end').strip():
            messagebox.showerror("错误", "请输入短信内容")
            self.content_text.focus()
            return False

        if self.sms_mode_var.get() == "mms":
            if not self.subject_entry.get().strip():
                messagebox.showerror("错误", "彩信模式下请输入主题")
                self.subject_entry.focus()
                return False

        return True

    def get_form_data(self):
        """获取表单数据"""
        targets = []
        target_content = self.target_text.get('1.0', 'end').strip()
        if target_content:
            lines = target_content.split('\n')
            for line in lines:
                line = line.strip()
                if line:
                    if line.isdigit() or (line.startswith('+') and line[1:].isdigit()):
                        targets.append(line)

        # 获取渠道用户ID
        channel_users_id = self.user_info.get('channel_users_id')
        if not channel_users_id:
            try:
                operators_id = self.user_info.get('operators_id') or self.user_info.get('id', 1)
                query = "SELECT channel_users_id FROM channel_operators WHERE operators_id = %s"
                result = execute_query(query, (operators_id,), fetch_one=True)
                if result:
                    channel_users_id = result[0]
                else:
                    channel_users_id = 1
            except Exception as e:
                print(f"获取渠道用户ID失败: {e}")
                channel_users_id = 1

        return {
            'title': self.task_name_entry.get().strip(),
            'mode': self.sms_mode_var.get(),
            'subject': self.subject_entry.get().strip() if self.sms_mode_var.get() == "mms" else '',
            'message_content': self.content_text.get('1.0', 'end').strip(),
            'templates_id': self.get_selected_template_id(),
            'number_mode': 'international' if self.number_mode_var.get() == "国际号码" else 'domestic',
            'targets': targets,
            'operators_id': self.user_info.get('operators_id') or self.user_info.get('id', 1),
            'channel_users_id': channel_users_id
        }

    def save_task_to_database(self, task_data, status='draft'):
        """保存任务到数据库 - 改进版本"""
        conn = None
        cursor = None

        try:
            from database.connection import get_db_connection
            from datetime import datetime

            # 获取数据库连接
            conn = get_db_connection()

            # 检查连接对象是否有效
            if not hasattr(conn, 'cursor'):
                # 如果是包装器对象但没有cursor方法，尝试直接获取连接
                from database.connection import get_connection
                conn = get_connection()

            cursor = conn.cursor()

            # 插入任务并获取ID
            insert_query = """
            INSERT INTO tasks (
                tasks_title, tasks_mode, tasks_subject_name, tasks_message_content,
                templates_id, tasks_total_count, tasks_status, 
                operators_id, channel_users_id, created_time
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING tasks_id
            """

            params = (
                task_data['title'],
                task_data['mode'],
                task_data.get('subject', ''),
                task_data['message_content'],
                task_data.get('templates_id'),
                len(task_data['targets']),
                status,
                task_data['operators_id'],
                task_data['channel_users_id'],
                datetime.now()
            )

            cursor.execute(insert_query, params)
            result = cursor.fetchone()

            if result:
                task_id = result[0]
                print(f"[DEBUG] 任务创建成功，ID: {task_id}")

                # 批量插入消息详情
                if task_data['targets']:
                    message_query = """
                    INSERT INTO task_message_details (
                        tasks_id, recipient_number, details_status, created_time
                    ) VALUES (%s, %s, %s, %s)
                    """

                    for phone in task_data['targets']:
                        cursor.execute(message_query, (task_id, phone, 'pending', datetime.now()))

                    print(f"[DEBUG] 插入了 {len(task_data['targets'])} 条消息详情")

                # 提交事务
                conn.commit()
                return {'success': True, 'task_id': task_id, 'message': '任务保存成功'}
            else:
                conn.rollback()
                return {'success': False, 'message': '任务保存失败'}

        except Exception as e:
            if conn:
                conn.rollback()
            print(f"[ERROR] 数据库操作失败: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'message': f'数据库保存失败: {str(e)}'}
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def save(self):
        """保存任务"""
        if not self.validate_form():
            return

        try:
            task_data = self.get_form_data()

            if not task_data['targets']:
                messagebox.showerror("错误", "没有有效的目标号码")
                return

            result = self.save_task_to_database(task_data, 'draft')
            if result['success']:
                messagebox.showinfo("成功", "任务已保存为草稿")
                self.result = result
                self.dialog.destroy()
            else:
                messagebox.showerror("失败", result['message'])

        except Exception as e:
            messagebox.showerror("错误", f"保存任务失败：{str(e)}")

    def submit(self):
        """提交任务"""
        if not self.validate_form():
            return

        try:
            task_data = self.get_form_data()

            if not task_data['targets']:
                messagebox.showerror("错误", "没有有效的目标号码")
                return

            target_count = len(task_data['targets'])

            # 获取当前用户积分余额
            current_balance = self.user_info.get('operators_available_credits', 0)

            # 如果获取不到积分信息，尝试从数据库刷新
            if current_balance == 0:
                try:
                    operators_id = self.user_info.get('operators_id') or self.user_info.get('id', 1)
                    query = "SELECT operators_available_credits FROM channel_operators WHERE operators_id = %s"
                    result = execute_query(query, (operators_id,), fetch_one=True)
                    if result:
                        current_balance = result[0]
                        # 更新用户信息
                        self.user_info['operators_available_credits'] = current_balance
                except Exception as e:
                    print(f"获取用户积分失败: {e}")
                    current_balance = 0

            # 提交任务不消耗积分，只是检查余额是否足够
            if current_balance < target_count:
                messagebox.showerror("余额不足", f"发送 {target_count} 条短信需要 {target_count} 积分，当前余额：{current_balance} 积分")
                return

            # 确认提交（不消耗积分，只是创建任务）
            if messagebox.askyesno("确认提交", f"将创建任务准备发送 {target_count} 条短信，预计消耗 {target_count} 积分，确定提交吗？"):
                result = self.save_task_to_database(task_data, 'pending')
                if result['success']:
                    messagebox.showinfo("成功", "任务已提交到待发送队列，开始发送时才会消耗积分")
                    self.result = result
                    self.dialog.destroy()
                else:
                    messagebox.showerror("失败", result['message'])

        except Exception as e:
            messagebox.showerror("错误", f"提交任务失败：{str(e)}")

    def cancel(self):
        """取消"""
        self.result = None
        self.dialog.destroy()

    def show(self):
        """显示对话框并返回结果"""
        self.dialog.wait_window()
        return self.result

    def upload_file(self):
        """上传文件并导入号码 - 修复 macOS 兼容性问题"""
        try:
            import platform

            # 检测操作系统
            is_macos = platform.system() == 'Darwin'

            if is_macos:
                # macOS 版本 - 每个扩展名单独列出
                file_path = filedialog.askopenfilename(
                    title="选择号码文件",
                    filetypes=[
                        ("Excel文件", "*.xlsx"),
                        ("Excel文件", "*.xls"),
                        ("CSV文件", "*.csv"),
                        ("文本文件", "*.txt"),
                        ("所有文件", "*.*")
                    ]
                )
            else:
                # Windows/Linux 版本 - 可以使用分号分隔
                file_path = filedialog.askopenfilename(
                    title="选择号码文件",
                    filetypes=[
                        ("Excel文件", "*.xlsx;*.xls"),
                        ("CSV文件", "*.csv"),
                        ("文本文件", "*.txt"),
                        ("所有文件", "*.*")
                    ]
                )

            if not file_path:
                return

            # 根据文件类型读取号码
            file_ext = os.path.splitext(file_path)[1].lower()
            phone_numbers = []

            if file_ext in ['.xlsx', '.xls']:
                phone_numbers = self.read_excel_file(file_path)
            elif file_ext == '.csv':
                phone_numbers = self.read_csv_file(file_path)
            elif file_ext == '.txt':
                phone_numbers = self.read_txt_file(file_path)
            else:
                messagebox.showerror("错误", "不支持的文件格式")
                return

            if phone_numbers:
                # 将号码添加到文本框
                self.append_phone_numbers(phone_numbers)
                messagebox.showinfo("成功", f"成功导入 {len(phone_numbers)} 个号码")
            else:
                messagebox.showwarning("警告", "文件中没有找到有效的号码")

        except Exception as e:
            messagebox.showerror("错误", f"读取文件失败：{str(e)}")

    # 备选方案：更简洁的跨平台版本
    def upload_file_v2(self):
        """上传文件并导入号码 - 跨平台简化版"""
        try:
            # 使用更通用的文件类型定义
            file_path = filedialog.askopenfilename(
                title="选择号码文件",
                filetypes=[
                    ("支持的文件", "*.xlsx *.xls *.csv *.txt"),  # 使用空格分隔
                    ("Excel文件", "*.xlsx"),
                    ("Excel 97-2003", "*.xls"),
                    ("CSV文件", "*.csv"),
                    ("文本文件", "*.txt"),
                    ("所有文件", "*.*")
                ]
            )

            if not file_path:
                return

            # 根据文件类型读取号码
            file_ext = os.path.splitext(file_path)[1].lower()
            phone_numbers = []

            if file_ext in ['.xlsx', '.xls']:
                phone_numbers = self.read_excel_file(file_path)
            elif file_ext == '.csv':
                phone_numbers = self.read_csv_file(file_path)
            elif file_ext == '.txt':
                phone_numbers = self.read_txt_file(file_path)
            else:
                messagebox.showerror("错误", "不支持的文件格式")
                return

            if phone_numbers:
                # 将号码添加到文本框
                self.append_phone_numbers(phone_numbers)
                messagebox.showinfo("成功", f"成功导入 {len(phone_numbers)} 个号码")
            else:
                messagebox.showwarning("警告", "文件中没有找到有效的号码")

        except Exception as e:
            messagebox.showerror("错误", f"读取文件失败：{str(e)}")
            import traceback
            traceback.print_exc()

    # 方案3：最简单的版本（推荐）
    def upload_file_simple(self):
        """上传文件并导入号码 - 最简化版本"""
        try:
            # 不使用复杂的文件类型过滤
            file_path = filedialog.askopenfilename(
                title="选择号码文件（支持 Excel、CSV、文本文件）"
            )

            if not file_path:
                return

            # 检查文件扩展名
            file_ext = os.path.splitext(file_path)[1].lower()

            # 支持的文件格式
            supported_formats = {
                '.xlsx': self.read_excel_file,
                '.xls': self.read_excel_file,
                '.csv': self.read_csv_file,
                '.txt': self.read_txt_file
            }

            if file_ext not in supported_formats:
                messagebox.showerror(
                    "不支持的文件格式",
                    f"请选择以下格式的文件：\n• Excel (.xlsx, .xls)\n• CSV (.csv)\n• 文本文件 (.txt)"
                )
                return

            # 读取文件
            read_function = supported_formats[file_ext]
            phone_numbers = read_function(file_path)

            if phone_numbers:
                # 将号码添加到文本框
                self.append_phone_numbers(phone_numbers)
                messagebox.showinfo("成功", f"成功导入 {len(phone_numbers)} 个号码")
            else:
                messagebox.showwarning("警告", "文件中没有找到有效的号码")

        except Exception as e:
            messagebox.showerror("错误", f"读取文件失败：{str(e)}")
            import traceback
            traceback.print_exc()

    def read_excel_file(self, file_path):
        """读取Excel文件中的号码"""
        phone_numbers = []
        try:
            # 读取Excel文件
            df = pd.read_excel(file_path, dtype=str)

            # 查找包含电话号码的列
            phone_columns = []
            for col in df.columns:
                col_lower = str(col).lower()
                if any(keyword in col_lower for keyword in ['phone', '电话', '号码', '手机', 'mobile', 'tel']):
                    phone_columns.append(col)

            # 如果没有找到明确的电话列，使用第一列
            if not phone_columns and len(df.columns) > 0:
                phone_columns = [df.columns[0]]

            # 提取号码
            for col in phone_columns:
                for value in df[col].dropna():
                    phone = self.clean_phone_number(str(value))
                    if phone:
                        phone_numbers.append(phone)

            # 去重
            phone_numbers = list(dict.fromkeys(phone_numbers))

        except Exception as e:
            print(f"读取Excel文件失败: {e}")
            raise

        return phone_numbers

    def read_csv_file(self, file_path):
        """读取CSV文件中的号码"""
        phone_numbers = []
        try:
            # 尝试不同的编码
            encodings = ['utf-8', 'gbk', 'gb2312', 'utf-8-sig']

            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        csv_reader = csv.reader(file)

                        # 读取所有行
                        rows = list(csv_reader)
                        if not rows:
                            continue

                        # 查找电话号码列
                        header = rows[0] if rows else []
                        phone_col_index = -1

                        # 查找包含电话关键词的列
                        for i, col in enumerate(header):
                            col_lower = str(col).lower()
                            if any(keyword in col_lower for keyword in
                                   ['phone', '电话', '号码', '手机', 'mobile', 'tel']):
                                phone_col_index = i
                                break

                        # 如果没有找到，假设第一列是电话号码
                        if phone_col_index == -1:
                            phone_col_index = 0

                        # 提取号码（跳过标题行）
                        start_row = 1 if len(header) > 0 and not self.is_phone_number(header[phone_col_index]) else 0

                        for row in rows[start_row:]:
                            if phone_col_index < len(row):
                                phone = self.clean_phone_number(row[phone_col_index])
                                if phone:
                                    phone_numbers.append(phone)

                        # 如果成功读取，跳出编码循环
                        if phone_numbers:
                            break

                except UnicodeDecodeError:
                    continue

            # 去重
            phone_numbers = list(dict.fromkeys(phone_numbers))

        except Exception as e:
            print(f"读取CSV文件失败: {e}")
            raise

        return phone_numbers

    def read_txt_file(self, file_path):
        """读取文本文件中的号码"""
        phone_numbers = []
        try:
            # 尝试不同的编码
            encodings = ['utf-8', 'gbk', 'gb2312', 'utf-8-sig']

            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        for line in file:
                            # 支持多种分隔符
                            separators = [',', ';', '\t', '|', ' ']

                            # 尝试分割行
                            parts = [line.strip()]
                            for sep in separators:
                                if sep in line:
                                    parts = line.split(sep)
                                    break

                            # 提取每个部分的号码
                            for part in parts:
                                phone = self.clean_phone_number(part)
                                if phone:
                                    phone_numbers.append(phone)

                        # 如果成功读取，跳出编码循环
                        if phone_numbers:
                            break

                except UnicodeDecodeError:
                    continue

            # 去重
            phone_numbers = list(dict.fromkeys(phone_numbers))

        except Exception as e:
            print(f"读取文本文件失败: {e}")
            raise

        return phone_numbers

    def clean_phone_number(self, phone_str):
        """清理和验证电话号码"""
        if not phone_str:
            return None

        # 转换为字符串并去除空白
        phone = str(phone_str).strip()

        # 移除常见的非数字字符（保留+号用于国际号码）
        phone = phone.replace('-', '').replace(' ', '').replace('(', '').replace(')', '')
        phone = phone.replace('.', '').replace('/', '').replace('\\', '')

        # 如果是浮点数格式（Excel可能会这样），转换为整数字符串
        if '.' in phone and phone.replace('.', '').replace('+', '').isdigit():
            phone = phone.split('.')[0]

        # 验证号码格式
        if self.is_phone_number(phone):
            return phone

        return None

    def is_phone_number(self, phone):
        """验证是否为有效的电话号码"""
        if not phone:
            return False

        # 去除+号后应该都是数字
        phone_digits = phone.replace('+', '')
        if not phone_digits.isdigit():
            return False

        # 国内手机号：11位数字
        if len(phone_digits) == 11 and phone_digits[0] == '1':
            return True

        # 国际号码：以+开头，总长度8-15位
        if phone.startswith('+') and 8 <= len(phone_digits) <= 15:
            return True

        # 其他10-15位的号码也接受
        if 10 <= len(phone_digits) <= 15:
            return True

        return False

    def append_phone_numbers(self, phone_numbers):
        """将号码添加到文本框"""
        # 获取现有内容
        current_content = self.target_text.get('1.0', 'end').strip()

        # 解析现有号码
        existing_numbers = set()
        if current_content:
            for line in current_content.split('\n'):
                line = line.strip()
                if line:
                    existing_numbers.add(line)

        # 添加新号码（去重）
        new_numbers = []
        for phone in phone_numbers:
            if phone not in existing_numbers:
                new_numbers.append(phone)
                existing_numbers.add(phone)

        if new_numbers:
            # 如果文本框有内容，先添加换行
            if current_content:
                self.target_text.insert('end', '\n')

            # 添加新号码
            self.target_text.insert('end', '\n'.join(new_numbers))

        # 更新统计信息（可选）
        total_count = len(existing_numbers)
        self.update_phone_count_display(total_count)

    def update_phone_count_display(self, count):
        """更新号码数量显示（可选功能）"""
        # 如果有号码计数标签，更新它
        if hasattr(self, 'phone_count_label'):
            self.phone_count_label.config(text=f"共 {count} 个号码")

    def clear_phone_numbers(self):
        """清空号码列表"""
        if messagebox.askyesno("确认", "确定要清空所有号码吗？"):
            self.target_text.delete('1.0', 'end')
            if hasattr(self, 'phone_count_label'):
                self.phone_count_label.config(text="共 0 个号码")

def main():
    """测试添加任务对话框"""
    root = tk.Tk()
    root.title("添加任务对话框测试")
    root.geometry("400x300")
    root.configure(bg='#f5f5f5')

    user_info = {
        'operators_id': 1,
        'operators_username': 'test_user',
        'operators_available_credits': 10000
    }

    def show_dialog():
        dialog = AddTaskDialog(root, user_info)
        result = dialog.show()
        if result:
            print("任务创建结果:", result)
        else:
            print("任务创建取消")

    test_btn = tk.Button(
        root,
        text="打开添加任务对话框",
        font=('Microsoft YaHei', 12),
        bg='#FF7F50',
        fg='white',
        relief='flat',
        cursor='hand2',
        command=show_dialog,
        width=20,
        height=2
    )
    test_btn.pack(expand=True)

    root.mainloop()


if __name__ == '__main__':
    main()