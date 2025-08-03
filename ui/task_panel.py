"""
任务管理面板模块
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from datetime import datetime
from core.utils import parse_phone_numbers
from ui.widgets import create_button

class TaskPanel(tk.LabelFrame):
    """任务管理面板"""

    def __init__(self, parent, task_manager, port_manager, message_sender, status_callback):
        super().__init__(parent, text="任务列表", font=('Arial', 12, 'bold'),
                         bg='white', padx=10, pady=10)

        self.task_manager = task_manager
        self.port_manager = port_manager
        self.message_sender = message_sender
        self.status_callback = status_callback

        self.create_widgets()
        self.create_context_menu()

    def create_widgets(self):
        """创建控件"""
        # 任务控制按钮
        btn_frame = tk.Frame(self, bg='white')
        btn_frame.pack(fill='x', pady=(0, 10))

        (create_button(btn_frame, "停止发送", self.stop_all_tasks, variant="secondary")
         .pack(side='left', padx=(0, 5)))
        (create_button(btn_frame, "添加任务", self.show_add_task_dialog, variant="primary")
         .pack(side='left',padx=(0, 5)))
        (create_button(btn_frame, "更多", self.show_more_menu, variant="primary")
         .pack(side='left'))

        # tk.Button(btn_frame, text="停止发送", command=self.stop_all_tasks,
        #           bg='#e0e0e0', padx=10).pack(side='left', padx=(0, 5))
        # tk.Button(btn_frame, text="添加任务", command=self.show_add_task_dialog,
        #           bg='#ff6b35', fg='white', padx=10).pack(side='left', padx=(0, 5))
        # tk.Button(btn_frame, text="更多", command=self.show_more_menu,
        #           bg='#ff6b35', fg='white', padx=10).pack(side='left')

        # 任务列表
        columns = ('任务', '进度', '成功', '失败', '状态')
        self.task_tree = ttk.Treeview(self, columns=columns, show='headings', height=15)

        for col in columns:
            self.task_tree.heading(col, text=col)
            self.task_tree.column(col, width=100)

        # 滚动条
        scrollbar = ttk.Scrollbar(self, orient='vertical', command=self.task_tree.yview)
        self.task_tree.configure(yscrollcommand=scrollbar.set)

        self.task_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # 绑定事件
        self.task_tree.bind("<Button-3>", self.show_context_menu)
        self.task_tree.bind("<Double-1>", self.on_double_click)

    def create_context_menu(self):
        """创建右键菜单"""
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="开始任务", command=self.start_selected_task)
        self.context_menu.add_command(label="停止任务", command=self.stop_selected_task)
        self.context_menu.add_command(label="测试任务", command=self.test_selected_task)
        self.context_menu.add_command(label="修改内容", command=self.edit_selected_task)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="导出完成", command=self.export_completed_task)
        self.context_menu.add_command(label="导出未完成", command=self.export_incomplete_task)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="删除任务", command=self.delete_selected_task)

    def show_context_menu(self, event):
        """显示右键菜单"""
        try:
            # 选择点击的项目
            item = self.task_tree.identify_row(event.y)
            if item:
                self.task_tree.selection_set(item)
                self.context_menu.post(event.x_root, event.y_root)
        except:
            pass

    def on_double_click(self, event):
        """双击事件"""
        self.edit_selected_task()

    def show_more_menu(self):
        """显示更多菜单"""
        more_menu = tk.Menu(self, tearoff=0)
        more_menu.add_command(label="批量导入", command=self.batch_import_tasks)
        more_menu.add_command(label="批量导出", command=self.batch_export_tasks)
        more_menu.add_command(label="清空完成任务", command=self.clear_completed_tasks)
        more_menu.add_command(label="任务统计", command=self.show_task_statistics)

        # 显示菜单
        try:
            more_menu.post(self.winfo_rootx() + 200, self.winfo_rooty() + 50)
        except:
            pass

    def show_add_task_dialog(self):
        """显示添加任务对话框"""
        dialog = AddTaskDialog(self, self.task_manager)
        self.wait_window(dialog.dialog)
        self.update_display()

    def get_selected_task_id(self):
        """获取选中的任务ID"""
        selection = self.task_tree.selection()
        if not selection:
            return None

        item = selection[0]
        tags = self.task_tree.item(item, 'tags')
        return tags[0] if tags else None

    def start_selected_task(self):
        """启动选中的任务"""
        task_id = self.get_selected_task_id()
        if not task_id:
            messagebox.showwarning("警告", "请选择一个任务")
            return

        # 检查是否有活动端口
        if not self.port_manager.get_running_ports():
            messagebox.showwarning("警告", "没有活动的端口，请先启动端口")
            return

        if self.task_manager.start_task(task_id):
            task = self.task_manager.get_task(task_id)
            self.status_callback(f"任务 '{task['name']}' 已启动")
            self.update_display()

    def stop_selected_task(self):
        """停止选中的任务"""
        task_id = self.get_selected_task_id()
        if not task_id:
            messagebox.showwarning("警告", "请选择一个任务")
            return

        if self.task_manager.stop_task(task_id):
            task = self.task_manager.get_task(task_id)
            self.status_callback(f"任务 '{task['name']}' 已停止")
            self.update_display()

    def test_selected_task(self):
        """测试选中的任务"""
        task_id = self.get_selected_task_id()
        if not task_id:
            messagebox.showwarning("警告", "请选择一个任务")
            return

        task = self.task_manager.get_task(task_id)
        dialog = TestTaskDialog(self, task, self.port_manager, self.message_sender)
        self.wait_window(dialog.dialog)

    def edit_selected_task(self):
        """编辑选中的任务"""
        task_id = self.get_selected_task_id()
        if not task_id:
            messagebox.showwarning("警告", "请选择一个任务")
            return

        task = self.task_manager.get_task(task_id)
        dialog = EditTaskDialog(self, task_id, task, self.task_manager)
        self.wait_window(dialog.dialog)
        self.update_display()

    def delete_selected_task(self):
        """删除选中的任务"""
        task_id = self.get_selected_task_id()
        if not task_id:
            messagebox.showwarning("警告", "请选择一个任务")
            return

        task = self.task_manager.get_task(task_id)
        if messagebox.askyesno("确认", f"确定要删除任务 '{task['name']}' 吗？"):
            if self.task_manager.delete_task(task_id):
                self.status_callback(f"任务 '{task['name']}' 已删除")
                self.update_display()

    def stop_all_tasks(self):
        """停止所有任务"""
        self.task_manager.stop_all_tasks()
        self.status_callback("所有任务已停止")
        self.update_display()

    def export_completed_task(self):
        """导出已完成的号码"""
        task_id = self.get_selected_task_id()
        if not task_id:
            messagebox.showwarning("警告", "请选择一个任务")
            return

        task = self.task_manager.get_task(task_id)
        completed_count = task['success'] + task['failed']
        completed_numbers = task['numbers'][:completed_count]

        self._export_numbers(completed_numbers, f"{task['name']}_已完成.txt")

    def export_incomplete_task(self):
        """导出未完成的号码"""
        task_id = self.get_selected_task_id()
        if not task_id:
            messagebox.showwarning("警告", "请选择一个任务")
            return

        task = self.task_manager.get_task(task_id)
        completed_count = task['success'] + task['failed']
        incomplete_numbers = task['numbers'][completed_count:]

        self._export_numbers(incomplete_numbers, f"{task['name']}_未完成.txt")

    def _export_numbers(self, numbers, default_filename):
        """导出号码列表"""
        from tkinter import filedialog

        filename = filedialog.asksaveasfilename(
            title="保存号码文件",
            defaultextension=".txt",
            initialvalue=default_filename,
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )

        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    for number in numbers:
                        f.write(number + '\n')
                messagebox.showinfo("成功", f"已导出 {len(numbers)} 个号码")
            except Exception as e:
                messagebox.showerror("错误", f"导出失败: {e}")

    def batch_import_tasks(self):
        """批量导入任务"""
        from tkinter import filedialog

        filename = filedialog.askopenfilename(
            title="选择任务文件",
            filetypes=[("JSON文件", "*.json"), ("CSV文件", "*.csv"), ("所有文件", "*.*")]
        )

        if filename:
            try:
                # 这里可以实现具体的导入逻辑
                messagebox.showinfo("提示", "批量导入功能开发中...")
            except Exception as e:
                messagebox.showerror("错误", f"导入失败: {e}")

    def batch_export_tasks(self):
        """批量导出任务"""
        from tkinter import filedialog

        filename = filedialog.asksaveasfilename(
            title="保存任务文件",
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("CSV文件", "*.csv")]
        )

        if filename:
            try:
                # 这里可以实现具体的导出逻辑
                messagebox.showinfo("提示", "批量导出功能开发中...")
            except Exception as e:
                messagebox.showerror("错误", f"导出失败: {e}")

    def clear_completed_tasks(self):
        """清空已完成的任务"""
        if messagebox.askyesno("确认", "确定要清空所有已完成的任务吗？"):
            completed_tasks = [
                task_id for task_id, task in self.task_manager.tasks.items()
                if task['success'] + task['failed'] >= task['total']
            ]

            for task_id in completed_tasks:
                self.task_manager.delete_task(task_id)

            self.status_callback(f"已清空 {len(completed_tasks)} 个完成的任务")
            self.update_display()

    def show_task_statistics(self):
        """显示任务统计"""
        stats = self._calculate_task_statistics()

        stats_window = tk.Toplevel(self)
        stats_window.title("任务统计")
        stats_window.geometry("400x300")
        stats_window.resizable(False, False)

        # 居中显示
        stats_window.transient(self)
        stats_window.grab_set()

        main_frame = tk.Frame(stats_window, padx=20, pady=20)
        main_frame.pack(fill='both', expand=True)

        # 统计信息
        stats_text = f"""
任务统计信息

总任务数: {stats['total_tasks']}
运行中任务: {stats['running_tasks']}
已完成任务: {stats['completed_tasks']}
待处理任务: {stats['pending_tasks']}

发送统计:
总发送数: {stats['total_sent']}
成功发送: {stats['total_success']}
发送失败: {stats['total_failed']}
成功率: {stats['success_rate']:.2%}
        """

        text_widget = tk.Text(main_frame, wrap=tk.WORD, width=40, height=15)
        text_widget.pack(fill='both', expand=True)
        text_widget.insert('1.0', stats_text.strip())
        text_widget.config(state='disabled')

        # 关闭按钮
        tk.Button(main_frame, text="关闭", command=stats_window.destroy,
                  bg='#e0e0e0', padx=20, pady=5).pack(pady=(10, 0))

    def _calculate_task_statistics(self):
        """计算任务统计信息"""
        tasks = self.task_manager.get_all_tasks()

        total_tasks = len(tasks)
        running_tasks = len(self.task_manager.running_tasks)
        completed_tasks = len([t for t in tasks.values()
                               if t['success'] + t['failed'] >= t['total']])
        pending_tasks = total_tasks - completed_tasks - running_tasks

        total_sent = sum(t['success'] + t['failed'] for t in tasks.values())
        total_success = sum(t['success'] for t in tasks.values())
        total_failed = sum(t['failed'] for t in tasks.values())
        success_rate = total_success / max(1, total_sent)

        return {
            'total_tasks': total_tasks,
            'running_tasks': running_tasks,
            'completed_tasks': completed_tasks,
            'pending_tasks': pending_tasks,
            'total_sent': total_sent,
            'total_success': total_success,
            'total_failed': total_failed,
            'success_rate': success_rate
        }

    def update_display(self):
        """更新任务显示"""
        # 清空现有项目
        for item in self.task_tree.get_children():
            self.task_tree.delete(item)

        # 添加任务
        for task_id, task_info in self.task_manager.get_all_tasks().items():
            status_text = '运行中' if task_info['status'] == 'running' else '停止'
            self.task_tree.insert('', 'end', values=(
                task_info['name'],
                task_info['progress'],
                task_info['success'],
                task_info['failed'],
                status_text
            ), tags=(task_id,))


class AddTaskDialog:
    """添加任务对话框"""

    def __init__(self, parent, task_manager):
        self.parent = parent
        self.task_manager = task_manager
        self.create_dialog()

    def create_dialog(self):
        """创建对话框"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("添加任务")
        self.dialog.geometry("500x600")
        self.dialog.resizable(False, False)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        # 居中显示
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")

        # 创建表单
        main_frame = tk.Frame(self.dialog, padx=20, pady=20)
        main_frame.pack(fill='both', expand=True)

        # 任务名称
        tk.Label(main_frame, text="* 任务名称:", fg='red').pack(anchor='w', pady=(0, 5))
        self.name_entry = tk.Entry(main_frame, width=50)
        self.name_entry.pack(fill='x', pady=(0, 10))

        # 目标号码
        tk.Label(main_frame, text="* 目标号码:", fg='red').pack(anchor='w', pady=(0, 5))
        self.numbers_text = scrolledtext.ScrolledText(main_frame, height=6, width=50)
        self.numbers_text.pack(fill='x', pady=(0, 10))
        self.numbers_text.insert('1.0', "请输入手机号，每行一个")

        # 模板选择
        tk.Label(main_frame, text="模板:", fg='black').pack(anchor='w', pady=(0, 5))
        self.template_combo = ttk.Combobox(main_frame, values=['默认模板', '验证码模板', '通知模板'],
                                           state='readonly')
        self.template_combo.set('默认模板')
        self.template_combo.pack(fill='x', pady=(0, 10))

        # 号码格式
        tk.Label(main_frame, text="号码格式:", fg='black').pack(anchor='w', pady=(0, 5))
        self.format_combo = ttk.Combobox(main_frame, values=['国内号码', '国际号码'],
                                         state='readonly')
        self.format_combo.set('国内号码')
        self.format_combo.pack(fill='x', pady=(0, 10))

        # 主题
        tk.Label(main_frame, text="主题:", fg='black').pack(anchor='w', pady=(0, 5))
        self.subject_entry = tk.Entry(main_frame, width=50)
        self.subject_entry.pack(fill='x', pady=(0, 10))

        # 上传文件按钮
        file_frame = tk.Frame(main_frame)
        file_frame.pack(fill='x', pady=(0, 10))
        tk.Button(file_frame, text="上传文件", command=self.upload_file,
                  bg='#e0e0e0', padx=10).pack(side='left')
        tk.Label(file_frame, text="支持txt、csv格式的号码文件").pack(side='left', padx=(10, 0))

        # 内容
        tk.Label(main_frame, text="* 内容:", fg='red').pack(anchor='w', pady=(0, 5))
        self.content_text = scrolledtext.ScrolledText(main_frame, height=6, width=50)
        self.content_text.pack(fill='x', pady=(0, 20))

        # 按钮
        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(fill='x')

        tk.Button(btn_frame, text="取消", command=self.dialog.destroy,
                  bg='#e0e0e0', padx=20).pack(side='right', padx=(5, 0))
        tk.Button(btn_frame, text="提交", command=self.submit_task,
                  bg='#ff6b35', fg='white', padx=20).pack(side='right', padx=(5, 0))
        tk.Button(btn_frame, text="保存", command=self.save_task,
                  bg='#ff6b35', fg='white', padx=20).pack(side='right')

    def upload_file(self):
        """上传号码文件"""
        from tkinter import filedialog

        filename = filedialog.askopenfilename(
            title="选择号码文件",
            filetypes=[("文本文件", "*.txt"), ("CSV文件", "*.csv"), ("所有文件", "*.*")]
        )

        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 清空并插入新内容
                self.numbers_text.delete('1.0', tk.END)
                self.numbers_text.insert('1.0', content)

                messagebox.showinfo("成功", "文件上传成功")
            except Exception as e:
                messagebox.showerror("错误", f"文件上传失败: {e}")

    def validate_input(self):
        """验证输入"""
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showerror("错误", "请输入任务名称")
            return False

        numbers_text = self.numbers_text.get('1.0', tk.END).strip()
        if not numbers_text or numbers_text == "请输入手机号，每行一个":
            messagebox.showerror("错误", "请输入目标号码")
            return False

        content = self.content_text.get('1.0', tk.END).strip()
        if not content:
            messagebox.showerror("错误", "请输入短信内容")
            return False

        return True

    def submit_task(self):
        """提交任务"""
        if not self.validate_input():
            return

        self._create_task()
        self.dialog.destroy()

    def save_task(self):
        """保存任务"""
        if not self.validate_input():
            return

        self._create_task()

        # 清空表单准备下一个任务
        self.name_entry.delete(0, tk.END)
        self.numbers_text.delete('1.0', tk.END)
        self.numbers_text.insert('1.0', "请输入手机号，每行一个")
        self.subject_entry.delete(0, tk.END)
        self.content_text.delete('1.0', tk.END)

        messagebox.showinfo("成功", "任务保存成功，可以继续添加下一个任务")

    def _create_task(self):
        """创建任务"""
        name = self.name_entry.get().strip()
        numbers_text = self.numbers_text.get('1.0', tk.END).strip()
        subject = self.subject_entry.get().strip()
        content = self.content_text.get('1.0', tk.END).strip()

        # 解析手机号
        phone_list = parse_phone_numbers(numbers_text)

        if not phone_list:
            messagebox.showerror("错误", "没有找到有效的手机号码")
            return

        # 创建任务
        task_id = self.task_manager.create_task(
            name=name,
            numbers=phone_list,
            subject=subject,
            content=content,
            template=self.template_combo.get(),
            options={'format': self.format_combo.get()}
        )

        messagebox.showinfo("成功", f"任务 '{name}' 创建成功，共 {len(phone_list)} 个号码")


class EditTaskDialog:
    """编辑任务对话框"""

    def __init__(self, parent, task_id, task, task_manager):
        self.parent = parent
        self.task_id = task_id
        self.task = task
        self.task_manager = task_manager
        self.create_dialog()

    def create_dialog(self):
        """创建对话框"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("编辑任务")
        self.dialog.geometry("500x600")
        self.dialog.resizable(False, False)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        # 居中显示
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")

        main_frame = tk.Frame(self.dialog, padx=20, pady=20)
        main_frame.pack(fill='both', expand=True)

        # 任务名称
        tk.Label(main_frame, text="* 任务名称:", fg='red').pack(anchor='w', pady=(0, 5))
        self.name_entry = tk.Entry(main_frame, width=50)
        self.name_entry.insert(0, self.task['name'])
        self.name_entry.pack(fill='x', pady=(0, 10))

        # 目标号码
        tk.Label(main_frame, text="* 目标号码:", fg='red').pack(anchor='w', pady=(0, 5))
        self.numbers_text = scrolledtext.ScrolledText(main_frame, height=6, width=50)
        self.numbers_text.insert('1.0', '\n'.join(self.task['numbers']))
        self.numbers_text.pack(fill='x', pady=(0, 10))

        # 主题
        tk.Label(main_frame, text="主题:", fg='black').pack(anchor='w', pady=(0, 5))
        self.subject_entry = tk.Entry(main_frame, width=50)
        self.subject_entry.insert(0, self.task.get('subject', ''))
        self.subject_entry.pack(fill='x', pady=(0, 10))

        # 内容
        tk.Label(main_frame, text="* 内容:", fg='red').pack(anchor='w', pady=(0, 5))
        self.content_text = scrolledtext.ScrolledText(main_frame, height=8, width=50)
        self.content_text.insert('1.0', self.task['content'])
        self.content_text.pack(fill='x', pady=(0, 20))

        # 按钮
        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(fill='x')

        tk.Button(btn_frame, text="取消", command=self.dialog.destroy,
                  bg='#e0e0e0', padx=20).pack(side='right', padx=(5, 0))
        tk.Button(btn_frame, text="保存", command=self.save_changes,
                  bg='#ff6b35', fg='white', padx=20).pack(side='right')

    def save_changes(self):
        """保存更改"""
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showerror("错误", "请输入任务名称")
            return

        numbers_text = self.numbers_text.get('1.0', tk.END).strip()
        if not numbers_text:
            messagebox.showerror("错误", "请输入目标号码")
            return

        content = self.content_text.get('1.0', tk.END).strip()
        if not content:
            messagebox.showerror("错误", "请输入短信内容")
            return

        # 解析手机号
        phone_list = parse_phone_numbers(numbers_text)
        if not phone_list:
            messagebox.showerror("错误", "没有找到有效的手机号码")
            return

        # 更新任务
        subject = self.subject_entry.get().strip()

        success = self.task_manager.update_task_info(
            self.task_id,
            name=name,
            numbers=phone_list,
            subject=subject,
            content=content
        )

        if success:
            messagebox.showinfo("成功", "任务更新成功")
            self.dialog.destroy()
        else:
            messagebox.showerror("错误", "任务更新失败")


class TestTaskDialog:
    """测试任务对话框"""

    def __init__(self, parent, task, port_manager, message_sender):
        self.parent = parent
        self.task = task
        self.port_manager = port_manager
        self.message_sender = message_sender
        self.create_dialog()

    def create_dialog(self):
        """创建对话框"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("任务测试")
        self.dialog.geometry("400x250")
        self.dialog.resizable(False, False)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        # 居中显示
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")

        main_frame = tk.Frame(self.dialog, padx=20, pady=20)
        main_frame.pack(fill='both', expand=True)

        # 任务名称
        tk.Label(main_frame, text="* 任务名称:", fg='red').pack(anchor='w', pady=(0, 5))
        name_entry = tk.Entry(main_frame, width=40)
        name_entry.insert(0, self.task['name'])
        name_entry.configure(state='readonly')
        name_entry.pack(fill='x', pady=(0, 10))

        # 测试手机号
        tk.Label(main_frame, text="* 测试手机号:", fg='red').pack(anchor='w', pady=(0, 5))
        self.phone_entry = tk.Entry(main_frame, width=40)
        self.phone_entry.pack(fill='x', pady=(0, 10))

        # 测试端口
        tk.Label(main_frame, text="* 测试端口:", fg='red').pack(anchor='w', pady=(0, 5))
        running_ports = self.port_manager.get_running_ports()
        self.port_combo = ttk.Combobox(main_frame, values=running_ports, state='readonly')
        if running_ports:
            self.port_combo.set(running_ports[0])
        self.port_combo.pack(fill='x', pady=(0, 20))

        # 按钮
        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(fill='x')

        tk.Button(btn_frame, text="取消", command=self.dialog.destroy,
                  bg='#e0e0e0', padx=20).pack(side='right', padx=(5, 0))
        tk.Button(btn_frame, text="确定", command=self.execute_test,
                  bg='#ff6b35', fg='white', padx=20).pack(side='right')

    def execute_test(self):
        """执行测试"""
        phone_number = self.phone_entry.get().strip()
        if not phone_number:
            messagebox.showerror("错误", "请输入测试手机号")
            return

        port_name = self.port_combo.get()
        if not port_name:
            messagebox.showerror("错误", "请选择测试端口")
            return

        self.dialog.destroy()

        # 发送测试短信
        success = self.message_sender.send_test_message(
            port_name, phone_number, self.task['content']
        )

        if success:
            messagebox.showinfo("测试结果", f"测试短信已发送到 {phone_number}\n使用端口: {port_name}")
        else:
            messagebox.showerror("测试结果", f"测试短信发送失败\n号码: {phone_number}\n端口: {port_name}")