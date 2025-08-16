"""
任务编辑对话框 - 修改任务内容
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

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
        def update_task_content(self, data):
            print("模拟更新任务:", data)
            return {'success': True, 'message': '任务更新成功'}

    def execute_query(query, params=None, fetch_one=False, dict_cursor=False):
        # 模拟查询消息模板
        if 'message_templates' in query:
            return [
                {'templates_id': 1, 'templates_name': '通知模板', 'templates_description': '这是一条通知消息'},
                {'templates_id': 2, 'templates_name': '营销模板', 'templates_description': '这是一条营销消息'},
                {'templates_id': 3, 'templates_name': '验证码模板', 'templates_description': '您的验证码是：{code}'}
            ]
        # 模拟查询任务详情
        elif 'tasks' in query:
            return {
                'tasks_id': 1,
                'tasks_title': '测试任务',
                'tasks_mode': 'sms',
                'tasks_subject_name': '测试主题',
                'tasks_message_content': '这是一条测试短信内容',
                'templates_id': 1,
                'tasks_number_mode': 'domestic'
            }
        return []


class TaskEditDialog:
    """任务编辑对话框 - 仅修改5个字段（任务名称、主题、发送模板、号码模式、短信内容）"""

    def __init__(self, parent, task):
        self.parent = parent
        self.task = task
        self.task_service = TaskService()
        self.result = None
        self.message_templates = []
        self.original_data = {}  # 保存原始数据用于比较
        self.create_dialog()
        self.load_task_data()

    def create_dialog(self):
        """创建对话框"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("修改任务")
        self.dialog.geometry("600x600")
        self.dialog.resizable(False, False)
        self.dialog.configure(bg=get_color('background'))

        # 设置模态对话框
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        # 居中显示
        self.center_dialog()

        # 创建内容
        self.create_content()

    def center_dialog(self):
        """对话框居中显示"""
        self.dialog.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (600 // 2)
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (600 // 2)
        self.dialog.geometry(f"600x700+{x}+{y}")

    def create_content(self):
        """创建对话框内容"""
        # 主框架
        main_frame = tk.Frame(self.dialog, bg=get_color('background'))
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)

        # 任务信息显示（只读）
        self.create_task_info(main_frame)

        # 创建表单内容
        self.create_form_content(main_frame)

        # 创建按钮
        self.create_buttons(main_frame)

    def create_task_info(self, parent):
        """创建任务信息显示（只读信息）"""
        info_frame = tk.Frame(parent, bg=get_color('primary_light'), relief='solid', bd=1)
        info_frame.pack(fill='x', pady=(0, 20))

        # 任务ID和状态
        header_frame = tk.Frame(info_frame, bg=get_color('primary_light'))
        header_frame.pack(fill='x', padx=15, pady=(10, 5))

        tk.Label(
            header_frame,
            text=f"任务ID：{self.task.get('id', 'Unknown')}",
            font=get_font('default'),
            fg=get_color('text'),
            bg=get_color('primary_light')
        ).pack(side='left', padx=(0, 30))

        # 任务状态
        status_map = {
            'draft': '草稿',
            'pending': '待执行',
            'running': '执行中',
            'paused': '已暂停',
            'completed': '已完成',
            'cancelled': '已取消',
            'failed': '失败',
            'stopped': '已停止'
        }
        status = self.task.get('status', 'unknown')
        status_text = status_map.get(status, status)

        tk.Label(
            header_frame,
            text=f"状态：{status_text}",
            font=get_font('default'),
            fg=get_color('text'),
            bg=get_color('primary_light')
        ).pack(side='left')

        # 任务统计信息
        stats_frame = tk.Frame(info_frame, bg=get_color('primary_light'))
        stats_frame.pack(fill='x', padx=15, pady=(0, 10))

        stats_info = [
            ('总数', self.task.get('total', 0), get_color('text')),
            ('已发送', self.task.get('sent', 0), get_color('text')),
            ('成功', self.task.get('success_count', 0), get_color('success')),
            ('失败', self.task.get('failed_count', 0), get_color('danger'))
        ]

        for label, value, color in stats_info:
            tk.Label(
                stats_frame,
                text=f"{label}：{value}",
                font=get_font('small'),
                fg=color,
                bg=get_color('primary_light')
            ).pack(side='left', padx=(0, 1))

    def create_form_content(self, parent):
        """创建可编辑的表单内容"""
        # 表单容器
        form_frame = tk.Frame(parent, bg=get_color('background'))
        form_frame.pack(fill='both', expand=True)

        # 1. 任务名称
        self.create_field(form_frame, "任务名称:", required=True)
        self.task_name_entry = tk.Entry(
            form_frame,
            font=get_font('default'),
            relief='solid',
            bd=1
        )
        self.task_name_entry.pack(fill='x', pady=(0, 1))
        self.task_name_entry.bind('<KeyRelease>', self.limit_task_name)

        # 2. 主题（彩信专用）- 创建占位框架
        self.subject_placeholder = tk.Frame(form_frame, bg=get_color('background'))
        self.subject_placeholder.pack(fill='x', pady=0)  # 先占位，但高度为0

        # 创建主题容器（作为占位框架的子元素）
        self.subject_container = tk.Frame(self.subject_placeholder, bg=get_color('background'))

        self.create_field(self.subject_container, "主题:", required=True)
        self.subject_entry = tk.Entry(
            self.subject_container,
            font=get_font('default'),
            relief='solid',
            bd=1
        )
        self.subject_entry.pack(fill='x')

        # 3. 发送模板和号码模式（一行显示）
        template_row = tk.Frame(form_frame, bg=get_color('background'))
        template_row.pack(fill='x', pady=(0, 1))

        # 左侧：发送模板
        template_left = tk.Frame(template_row, bg=get_color('background'))
        template_left.pack(side='left', fill='both', expand=True, padx=(0, 1))

        self.create_field(template_left, "发送模板:", required=True)
        template_combo_frame = tk.Frame(template_left, bg=get_color('background'))
        template_combo_frame.pack(fill='x')

        self.template_var = tk.StringVar()
        self.template_combo = ttk.Combobox(
            template_combo_frame,
            textvariable=self.template_var,
            values=[],
            state='readonly',
            font=get_font('default')
        )
        self.template_combo.pack(side='left', fill='x', expand=True)
        self.template_combo.bind('<<ComboboxSelected>>', self.on_template_select)

        # 模板说明按钮
        template_help_btn = tk.Button(
            template_combo_frame,
            text="?",
            font=get_font('small'),
            bg='#E0E0E0',
            fg='#666666',
            relief='flat',
            cursor='hand2',
            command=self.show_template_help,
            width=2,
            height=1
        )
        template_help_btn.pack(side='left', padx=(5, 0))

        # 右侧：号码模式
        mode_right = tk.Frame(template_row, bg=get_color('background'))
        mode_right.pack(side='right', fill='both', expand=True, padx=(10, 0))

        self.create_field(mode_right, "号码模式:", required=True)
        self.number_mode_var = tk.StringVar()
        self.mode_combo = ttk.Combobox(
            mode_right,
            textvariable=self.number_mode_var,
            values=["国内号码", "国际号码"],
            state='readonly',
            font=get_font('default')
        )
        self.mode_combo.pack(fill='x')

        # 4. 短信内容
        self.create_field(form_frame, "短信内容:", required=True)

        content_container = tk.Frame(form_frame, bg=get_color('background'))
        content_container.pack(fill='x', expand=False, pady=(0, 10))

        self.content_text = tk.Text(
            content_container,
            font=get_font('default'),
            relief='solid',
            bd=1,
            height=4,
            wrap='word'
        )
        self.content_text.pack(side='left', fill='both', expand=True)

        content_scroll = ttk.Scrollbar(content_container, orient='vertical', command=self.content_text.yview)
        self.content_text.configure(yscrollcommand=content_scroll.set)
        content_scroll.pack(side='right', fill='y')

        # 字符计数
        self.char_count_label = tk.Label(
            form_frame,
            text="字符数：0",
            font=get_font('small'),
            fg=get_color('text_light'),
            bg=get_color('background')
        )
        self.char_count_label.pack(anchor='w', pady=(0, 15))

        # 绑定内容变化事件
        self.content_text.bind('<KeyRelease>', self.on_content_change)

        # 编辑提示
        tip_frame = tk.Frame(form_frame, bg=get_color('white'), relief='solid', bd=1)
        tip_frame.pack(fill='x')

        tip_text = """⚠ 注意事项：
        • 可修改任务名称、发送模板、号码模式、主题（彩信）和短信内容
        • 修改内容后，未发送的消息将使用新内容
        • 已经发送成功的消息不会受影响
        • 建议在任务开始前完成内容编辑"""

        tk.Label(
            tip_frame,
            text=tip_text,
            font=get_font('small'),
            fg=get_color('text'),
            bg=get_color('white'),
            justify='left'
        ).pack(anchor='w', padx=10, pady=10)

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

    def on_template_select(self, event=None):
        """模板选择改变事件"""
        try:
            selected_index = self.template_combo.current()
            if selected_index >= 0 and selected_index < len(self.message_templates):
                selected_template = self.message_templates[selected_index]
                print(f"选中模板: ID={selected_template['templates_id']}, 名称={selected_template['templates_name']}")
        except Exception as e:
            print(f"模板选择处理失败: {e}")

    def show_template_help(self):
        """显示模板帮助信息"""
        selected_index = self.template_combo.current()
        if selected_index >= 0 and selected_index < len(self.message_templates):
            template = self.message_templates[selected_index]
            desc = template.get('templates_description', '无描述')
            messagebox.showinfo(
                f"模板说明 - {template['templates_name']}",
                f"{desc}\n\n模板ID: {template['templates_id']}"
            )
        else:
            messagebox.showinfo("模板说明", "请先选择一个发送模板")

    def on_content_change(self, event=None):
        """内容变化事件"""
        self.update_char_count()

    def update_char_count(self):
        """更新字符计数"""
        content = self.content_text.get('1.0', 'end-1c')
        char_count = len(content)
        self.char_count_label.config(text=f"字符数：{char_count}")

        # 根据字符数设置颜色提示
        if char_count > 500:
            color = get_color('danger')
        elif char_count > 300:
            color = get_color('warning')
        else:
            color = get_color('text_light')

        self.char_count_label.config(fg=color)

    def load_task_data(self):
        """加载任务数据"""
        try:
            # 先尝试从数据库加载完整的任务信息
            task_id = self.task.get('id')
            if task_id:
                query = """
                SELECT tasks_id, tasks_title, tasks_mode, tasks_subject_name, 
                       tasks_message_content, templates_id, tasks_number_mode
                FROM tasks
                WHERE tasks_id = %s
                """
                result = execute_query(query, (task_id,), fetch_one=True, dict_cursor=True)
                if result:
                    # 保存原始数据
                    self.original_data = {
                        'title': result.get('tasks_title', ''),
                        'mode': result.get('tasks_mode', 'sms'),
                        'subject': result.get('tasks_subject_name', ''),
                        'template_id': result.get('templates_id'),
                        'number_mode': result.get('tasks_number_mode', 'domestic'),
                        'content': result.get('tasks_message_content', '')
                    }

                    # 填充任务名称
                    self.task_name_entry.insert(0, self.original_data['title'])

                    # 根据任务模式显示/隐藏主题字段
                    if self.original_data['mode'] == 'mms':
                        self.show_subject_field()
                        self.subject_entry.insert(0, self.original_data['subject'])
                    else:
                        self.hide_subject_field()

                    # 填充号码模式
                    mode_text = "国际号码" if self.original_data['number_mode'] == 'international' else "国内号码"
                    self.number_mode_var.set(mode_text)

                    # 填充内容
                    self.content_text.insert('1.0', self.original_data['content'])

                    # 加载模板列表
                    self.load_message_templates(self.original_data['mode'], self.original_data['template_id'])
            else:
                # 如果没有任务ID，使用传入的task字典数据
                self.original_data = {
                    'title': self.task.get('title', ''),
                    'mode': self.task.get('mode', 'sms'),
                    'subject': self.task.get('subject', ''),
                    'template_id': self.task.get('template_id'),
                    'number_mode': self.task.get('number_mode', 'domestic'),
                    'content': self.task.get('content', '')
                }

                # 填充表单
                self.task_name_entry.insert(0, self.original_data['title'])

                # 根据任务模式显示/隐藏主题字段
                if self.original_data['mode'] == 'mms':
                    self.show_subject_field()
                    self.subject_entry.insert(0, self.original_data['subject'])
                else:
                    self.hide_subject_field()

                # 填充号码模式
                mode_text = "国际号码" if self.original_data['number_mode'] == 'international' else "国内号码"
                self.number_mode_var.set(mode_text)
                self.content_text.insert('1.0', self.original_data['content'])

                # 加载模板
                self.load_message_templates(self.original_data['mode'], self.original_data['template_id'])

            # 更新字符计数
            self.update_char_count()

        except Exception as e:
            print(f"加载任务数据失败: {e}")
            # 使用默认值
            self.task_name_entry.insert(0, self.task.get('title', ''))
            self.content_text.insert('1.0', self.task.get('content', ''))
            self.number_mode_var.set("国内号码")
            self.hide_subject_field()
            self.load_message_templates('sms')

    def show_subject_field(self):
        """显示主题字段（彩信模式）"""
        self.subject_container.pack(fill='x', pady=(0, 5))
        self.subject_placeholder.pack_configure(pady=(0, 5))

    def hide_subject_field(self):
        """隐藏主题字段（短信模式）"""
        self.subject_container.pack_forget()
        self.subject_placeholder.pack_configure(pady=0)
        self.subject_entry.delete(0, 'end')

    def load_message_templates(self, template_type='sms', selected_template_id=None):
        """加载消息模板"""
        try:
            # 根据任务类型加载对应的模板
            query = """
            SELECT templates_id, templates_name, templates_description
            FROM message_templates 
            WHERE templates_type = %s 
            AND (templates_status = 'active' OR templates_status IS NULL)
            ORDER BY templates_name
            """
            templates = execute_query(query, (template_type,), dict_cursor=True)

            if templates:
                self.message_templates = templates
                template_values = [t['templates_name'] for t in templates]
                self.template_combo['values'] = template_values

                # 设置当前选中的模板
                if selected_template_id:
                    for i, t in enumerate(templates):
                        if t['templates_id'] == selected_template_id:
                            self.template_combo.set(template_values[i])
                            break
                else:
                    # 如果没有选中的模板，选择第一个
                    if template_values:
                        self.template_combo.set(template_values[0])
            else:
                self.message_templates = []
                self.template_combo['values'] = ['暂无可用模板']
                self.template_combo.set('暂无可用模板')

        except Exception as e:
            print(f"加载消息模板失败: {e}")
            self.message_templates = []
            self.template_combo['values'] = ['加载失败']
            self.template_combo.set('加载失败')

    def get_selected_template_id(self):
        """获取选中的模板ID"""
        try:
            selected_index = self.template_combo.current()
            if selected_index >= 0 and selected_index < len(self.message_templates):
                return self.message_templates[selected_index]['templates_id']
        except:
            pass
        return None

    def create_buttons(self, parent):
        """创建按钮"""
        button_frame = tk.Frame(parent, bg=get_color('background'))
        button_frame.pack(side='bottom', fill='x', pady=(1, 0))

        # 取消按钮
        cancel_btn = tk.Button(
            button_frame,
            text="取消",
            font=get_font('button'),
            bg=get_color('gray'),
            fg='#333333',
            relief='flat',
            cursor='hand2',
            command=self.cancel,
            width=12,
            height=2
        )
        cancel_btn.pack(side='left')

        # 保存按钮
        save_btn = tk.Button(
            button_frame,
            text="保存修改",
            font=get_font('button'),
            bg=get_color('primary'),
            fg='#000000',
            relief='flat',
            cursor='hand2',
            command=self.save,
            width=12,
            height=2
        )
        save_btn.pack(side='right')

    def validate_form(self):
        """验证表单"""
        # 验证任务名称
        if not self.task_name_entry.get().strip():
            messagebox.showerror("错误", "请输入任务名称")
            self.task_name_entry.focus()
            return False

        # 验证模板
        if not self.get_selected_template_id():
            messagebox.showerror("错误", "请选择发送模板")
            self.template_combo.focus()
            return False

        # 验证内容
        content = self.content_text.get('1.0', 'end-1c').strip()
        if not content:
            messagebox.showerror("错误", "请输入短信内容")
            self.content_text.focus()
            return False

        # 彩信模式下验证主题
        if hasattr(self, 'original_data') and self.original_data.get('mode') == 'mms':
            subject = self.subject_entry.get().strip()
            if not subject:
                messagebox.showerror("错误", "彩信模式下请输入主题")
                self.subject_entry.focus()
                return False

        return True

    def get_form_data(self):
        """获取表单数据"""
        data = {
            'task_id': self.task.get('id'),
            'title': self.task_name_entry.get().strip(),
            'template_id': self.get_selected_template_id(),
            'number_mode': 'international' if self.number_mode_var.get() == "国际号码" else 'domestic',
            'content': self.content_text.get('1.0', 'end-1c').strip()
        }

        # 如果是彩信模式，添加主题
        if hasattr(self, 'original_data') and self.original_data.get('mode') == 'mms':
            data['subject'] = self.subject_entry.get().strip()

        return data

    def check_changes(self):
        """检查是否有修改"""
        current_data = self.get_form_data()

        # 比较各字段是否有变化
        has_changes = (
            current_data['title'] != self.original_data.get('title', '') or
            current_data['template_id'] != self.original_data.get('template_id') or
            current_data['number_mode'] != self.original_data.get('number_mode', 'domestic') or
            current_data['content'] != self.original_data.get('content', '')
        )

        # 如果是彩信模式，还要比较主题
        if hasattr(self, 'original_data') and self.original_data.get('mode') == 'mms':
            has_changes = has_changes or (
                current_data.get('subject', '') != self.original_data.get('subject', '')
            )

        return has_changes

    def save_to_database(self, task_data):
        """保存修改到数据库"""
        conn = None
        cursor = None

        try:
            from database.connection import get_db_connection
            from datetime import datetime

            # 获取数据库连接
            conn = get_db_connection()

            # 检查连接对象是否有效
            if not hasattr(conn, 'cursor'):
                from database.connection import get_connection
                conn = get_connection()

            cursor = conn.cursor()

            # 构建更新SQL - 包含 tasks_number_mode 字段
            if 'subject' in task_data:
                # 彩信模式，包含主题
                update_query = """
                UPDATE tasks 
                SET tasks_title = %s,
                    templates_id = %s,
                    tasks_number_mode = %s,
                    tasks_subject_name = %s,
                    tasks_message_content = %s,
                    updated_time = %s
                WHERE tasks_id = %s
                """
                params = (
                    task_data['title'],
                    task_data['template_id'],
                    task_data['number_mode'],
                    task_data['subject'],
                    task_data['content'],
                    datetime.now(),
                    task_data['task_id']
                )
            else:
                # 短信模式，不包含主题
                update_query = """
                UPDATE tasks 
                SET tasks_title = %s,
                    templates_id = %s,
                    tasks_number_mode = %s,
                    tasks_message_content = %s,
                    updated_time = %s
                WHERE tasks_id = %s
                """
                params = (
                    task_data['title'],
                    task_data['template_id'],
                    task_data['number_mode'],
                    task_data['content'],
                    datetime.now(),
                    task_data['task_id']
                )

            cursor.execute(update_query, params)

            # 更新未发送的消息详情（如果内容有变化）
            if task_data['content'] != self.original_data.get('content', ''):
                # 检查 task_message_details 表是否存在 message_content 字段
                # 如果不存在，可以跳过这步
                try:
                    update_messages_query = """
                    UPDATE task_message_details
                    SET details_status = 'pending'
                    WHERE tasks_id = %s 
                    AND details_status = 'pending'
                    """
                    cursor.execute(update_messages_query, (task_data['task_id'],))

                    affected_rows = cursor.rowcount
                    print(f"[DEBUG] 标记了 {affected_rows} 条待发送消息需要使用新内容")
                except Exception as e:
                    print(f"[WARNING] 更新消息详情时出现问题（可忽略）: {e}")

            # 提交事务
            conn.commit()
            return {'success': True, 'message': '任务修改成功'}

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
        """保存修改"""
        if not self.validate_form():
            return

        # 检查是否有修改
        if not self.check_changes():
            messagebox.showinfo("提示", "没有修改内容")
            return

        # 获取表单数据
        form_data = self.get_form_data()

        # 确认修改
        if messagebox.askyesno("确认修改", "确定要保存对任务的修改吗？\n修改后将影响未发送的消息。"):
            try:
                # 保存到数据库
                result = self.save_to_database(form_data)

                if result['success']:
                    messagebox.showinfo("成功", result['message'])
                    self.result = result
                    self.dialog.destroy()
                else:
                    messagebox.showerror("失败", result['message'])

            except Exception as e:
                messagebox.showerror("错误", f"保存修改失败：{str(e)}")

    def cancel(self):
        """取消修改"""
        # 检查是否有未保存的修改
        if self.check_changes():
            if messagebox.askyesno("确认取消", "有未保存的修改，确定要取消吗？"):
                self.result = None
                self.dialog.destroy()
        else:
            self.result = None
            self.dialog.destroy()

    def show(self):
        """显示对话框并返回结果"""
        self.dialog.wait_window()
        return self.result


def main():
    """测试任务编辑对话框"""
    root = tk.Tk()
    root.title("任务编辑对话框测试")
    root.geometry("400x300")
    root.configure(bg='#f5f5f5')

    # 模拟任务信息
    task = {
        'id': 'v342',
        'title': '测试任务',
        'content': '这是一条测试短信内容，可以进行修改。',
        'subject': '测试主题',
        'mode': 'mms',  # 或 'sms'
        'template_id': 1,
        'number_mode': 'domestic',
        'total': 100,
        'sent': 25,
        'success_count': 20,
        'failed_count': 5,
        'status': 'running'
    }

    def show_dialog():
        dialog = TaskEditDialog(root, task)
        result = dialog.show()
        if result:
            print("编辑结果:", result)
        else:
            print("编辑取消")

    # 测试按钮
    test_btn = tk.Button(
        root,
        text="打开任务编辑对话框",
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