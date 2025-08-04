"""
添加任务对话框
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ui.styles import get_color, get_font
from services.task_service import TaskService


class AddTaskDialog:
    """添加任务对话框"""

    def __init__(self, parent, user_info):
        self.parent = parent
        self.user_info = user_info
        self.task_service = TaskService()
        self.result = None
        self.target_file_path = None
        self.image_file_path = None
        self.create_dialog()

    def create_dialog(self):
        """创建对话框"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("添加任务")
        self.dialog.geometry("500x650")
        self.dialog.resizable(False, False)
        self.dialog.configure(bg=get_color('background'))

        # 设置模态对话框
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        # 居中显示
        self.center_dialog()

        # 创建表单内容
        self.create_form()

        # 创建按钮
        self.create_buttons()

    def center_dialog(self):
        """对话框居中显示"""
        self.dialog.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (500 // 2)
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (650 // 2)
        self.dialog.geometry(f"500x650+{x}+{y}")

    def create_form(self):
        """创建表单"""
        # 主容器
        main_frame = tk.Frame(self.dialog, bg=get_color('background'))
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)

        # 任务名称
        self.create_field(main_frame, "任务名称:", required=True)
        self.task_name_entry = tk.Entry(
            main_frame,
            font=get_font('default'),
            relief='solid',
            bd=1
        )
        self.task_name_entry.pack(fill='x', pady=(0, 15))

        # 目标号码
        self.create_field(main_frame, "目标号码:", required=True)

        # 目标号码输入区域
        target_frame = tk.Frame(main_frame, bg=get_color('background'))
        target_frame.pack(fill='x', pady=(0, 15))

        # 文本输入框
        self.target_text = tk.Text(
            target_frame,
            font=get_font('default'),
            relief='solid',
            bd=1,
            height=4,
            wrap='word'
        )
        self.target_text.pack(side='left', fill='both', expand=True)

        # 滚动条
        target_scroll = ttk.Scrollbar(target_frame, orient='vertical', command=self.target_text.yview)
        self.target_text.configure(yscrollcommand=target_scroll.set)
        target_scroll.pack(side='right', fill='y')

        # 上传文件按钮
        upload_btn = tk.Button(
            main_frame,
            text="上传文件",
            font=get_font('button'),
            bg=get_color('primary'),
            fg='white',
            relief='flat',
            cursor='hand2',
            command=self.upload_target_file,
            width=10
        )
        upload_btn.pack(anchor='w', pady=(0, 15))

        # 模板选择
        self.create_field(main_frame, "模板:", required=True)
        self.template_var = tk.StringVar()
        template_combo = ttk.Combobox(
            main_frame,
            textvariable=self.template_var,
            values=["短信模板", "彩信模板"],
            state='readonly',
            font=get_font('default')
        )
        template_combo.pack(fill='x', pady=(0, 15))
        template_combo.set("短信模板")
        template_combo.bind('<<ComboboxSelected>>', self.on_template_change)

        # 选项
        self.create_field(main_frame, "选项:")
        self.option_var = tk.StringVar()
        option_combo = ttk.Combobox(
            main_frame,
            textvariable=self.option_var,
            values=["选项1", "选项2", "选项3"],
            state='readonly',
            font=get_font('default')
        )
        option_combo.pack(fill='x', pady=(0, 15))
        option_combo.set("选项1")

        # 号码模式
        self.create_field(main_frame, "号码模式:", required=True)
        self.number_mode_var = tk.StringVar()
        mode_combo = ttk.Combobox(
            main_frame,
            textvariable=self.number_mode_var,
            values=["国内号码", "国际号码"],
            state='readonly',
            font=get_font('default')
        )
        mode_combo.pack(fill='x', pady=(0, 15))
        mode_combo.set("国内号码")

        # 主题（彩信专用）
        self.subject_label = self.create_field(main_frame, "主题:")
        self.subject_entry = tk.Entry(
            main_frame,
            font=get_font('default'),
            relief='solid',
            bd=1,
            state='disabled'
        )
        self.subject_entry.pack(fill='x', pady=(0, 15))

        # 图片上传（彩信专用）
        self.image_label = tk.Label(
            main_frame,
            text="图片:",
            font=get_font('default'),
            fg=get_color('text_light'),
            bg=get_color('background')
        )
        self.image_label.pack(anchor='w', pady=(0, 5))

        # 图片上传区域
        self.image_frame = tk.Frame(
            main_frame,
            bg=get_color('white'),
            relief='solid',
            bd=1,
            height=120
        )
        self.image_frame.pack(fill='x', pady=(0, 15))
        self.image_frame.pack_propagate(False)

        # 上传图片按钮
        self.upload_image_btn = tk.Button(
            self.image_frame,
            text="+\n上传图片",
            font=get_font('default'),
            bg=get_color('background'),
            fg=get_color('text_light'),
            relief='flat',
            cursor='hand2',
            command=self.upload_image_file,
            state='disabled'
        )
        self.upload_image_btn.pack(expand=True)

        # 内容
        self.create_field(main_frame, "内容:", required=True)

        # 内容输入区域
        content_frame = tk.Frame(main_frame, bg=get_color('background'))
        content_frame.pack(fill='both', expand=True, pady=(0, 20))

        # 内容文本框
        self.content_text = tk.Text(
            content_frame,
            font=get_font('default'),
            relief='solid',
            bd=1,
            height=6,
            wrap='word'
        )
        self.content_text.pack(side='left', fill='both', expand=True)

        # 滚动条
        content_scroll = ttk.Scrollbar(content_frame, orient='vertical', command=self.content_text.yview)
        self.content_text.configure(yscrollcommand=content_scroll.set)
        content_scroll.pack(side='right', fill='y')

        # 初始状态设置
        self.update_template_fields()

    def create_field(self, parent, text, required=False):
        """创建字段标签"""
        color = get_color('danger') if required else get_color('text')
        marker = "*" if required else ""

        label = tk.Label(
            parent,
            text=f"{marker} {text}",
            font=get_font('default'),
            fg=color,
            bg=get_color('background')
        )
        label.pack(anchor='w', pady=(0, 5))
        return label

    def on_template_change(self, event):
        """模板类型改变事件"""
        self.update_template_fields()

    def update_template_fields(self):
        """更新模板相关字段状态"""
        is_mms = self.template_var.get() == "彩信模板"

        # 主题字段
        state = 'normal' if is_mms else 'disabled'
        self.subject_entry.config(state=state)
        color = get_color('text') if is_mms else get_color('text_light')
        self.subject_label.config(fg=color)

        # 图片字段
        color = get_color('text') if is_mms else get_color('text_light')
        self.image_label.config(fg=color)

        btn_state = 'normal' if is_mms else 'disabled'
        self.upload_image_btn.config(state=btn_state)

        if not is_mms:
            # 清空彩信相关内容
            self.subject_entry.delete(0, 'end')
            self.image_file_path = None
            self.upload_image_btn.config(text="+\n上传图片")

    def upload_target_file(self):
        """上传目标号码文件"""
        file_path = filedialog.askopenfilename(
            title="选择号码文件",
            filetypes=[
                ("文本文件", "*.txt"),
                ("CSV文件", "*.csv"),
                ("Excel文件", "*.xlsx *.xls"),
                ("所有文件", "*.*")
            ]
        )

        if file_path:
            try:
                # 读取文件内容
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 清空并填入内容
                self.target_text.delete('1.0', 'end')
                self.target_text.insert('1.0', content)

                self.target_file_path = file_path
                messagebox.showinfo("成功", f"已加载文件：{os.path.basename(file_path)}")

            except Exception as e:
                messagebox.showerror("错误", f"读取文件失败：{str(e)}")

    def upload_image_file(self):
        """上传图片文件"""
        file_path = filedialog.askopenfilename(
            title="选择图片文件",
            filetypes=[
                ("图片文件", "*.jpg *.jpeg *.png *.gif *.bmp"),
                ("JPEG文件", "*.jpg *.jpeg"),
                ("PNG文件", "*.png"),
                ("所有文件", "*.*")
            ]
        )

        if file_path:
            self.image_file_path = file_path
            filename = os.path.basename(file_path)
            self.upload_image_btn.config(text=f"已选择:\n{filename}")

    def create_buttons(self):
        """创建按钮"""
        button_frame = tk.Frame(self.dialog, bg=get_color('background'))
        button_frame.pack(fill='x', padx=20, pady=(0, 20))

        # 取消按钮
        cancel_btn = tk.Button(
            button_frame,
            text="取消",
            font=get_font('button'),
            bg=get_color('gray'),
            fg='white',
            relief='flat',
            cursor='hand2',
            command=self.cancel,
            width=10
        )
        cancel_btn.pack(side='left')

        # 保存按钮
        save_btn = tk.Button(
            button_frame,
            text="保存",
            font=get_font('button'),
            bg=get_color('primary'),
            fg='white',
            relief='flat',
            cursor='hand2',
            command=self.save,
            width=10
        )
        save_btn.pack(side='left', padx=(10, 0))

        # 提交按钮
        submit_btn = tk.Button(
            button_frame,
            text="提交",
            font=get_font('button'),
            bg=get_color('success'),
            fg='white',
            relief='flat',
            cursor='hand2',
            command=self.submit,
            width=10
        )
        submit_btn.pack(side='right')

    def validate_form(self):
        """验证表单"""
        # 检查必填字段
        if not self.task_name_entry.get().strip():
            messagebox.showerror("错误", "请输入任务名称")
            self.task_name_entry.focus()
            return False

        if not self.target_text.get('1.0', 'end').strip():
            messagebox.showerror("错误", "请输入目标号码")
            self.target_text.focus()
            return False

        if not self.content_text.get('1.0', 'end').strip():
            messagebox.showerror("错误", "请输入短信内容")
            self.content_text.focus()
            return False

        # 彩信特殊验证
        if self.template_var.get() == "彩信模板":
            if not self.subject_entry.get().strip():
                messagebox.showerror("错误", "彩信模式下请输入主题")
                self.subject_entry.focus()
                return False

        return True

    def get_form_data(self):
        """获取表单数据"""
        # 处理目标号码
        targets = []
        target_content = self.target_text.get('1.0', 'end').strip()
        if target_content:
            # 按行分割号码
            lines = target_content.split('\n')
            for line in lines:
                line = line.strip()
                if line:
                    # 可以支持多种格式：纯号码、逗号分隔等
                    if ',' in line:
                        targets.extend([num.strip() for num in line.split(',') if num.strip()])
                    else:
                        targets.append(line)

        return {
            'title': self.task_name_entry.get().strip(),
            'template_type': 'mms' if self.template_var.get() == "彩信模板" else 'sms',
            'subject': self.subject_entry.get().strip() if self.template_var.get() == "彩信模板" else '',
            'content': self.content_text.get('1.0', 'end').strip(),
            'targets': targets,
            'number_mode': self.number_mode_var.get(),
            'option': self.option_var.get(),
            'image_path': self.image_file_path,
            'user_id': self.user_info.get('id')
        }

    def save(self):
        """保存任务"""
        if not self.validate_form():
            return

        try:
            task_data = self.get_form_data()
            task_data['status'] = 'draft'  # 保存为草稿

            result = self.task_service.create_task(task_data)
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

            # 检查余额是否足够
            target_count = len(task_data['targets'])
            if target_count == 0:
                messagebox.showerror("错误", "没有有效的目标号码")
                return

            current_balance = self.user_info.get('balance', 0)
            if current_balance < target_count:
                messagebox.showerror("余额不足", f"发送 {target_count} 条短信需要 {target_count} 积分，当前余额：{current_balance} 积分")
                return

            # 确认提交
            if messagebox.askyesno("确认提交", f"将创建任务发送 {target_count} 条短信，消耗 {target_count} 积分，确定提交吗？"):
                task_data['status'] = 'pending'  # 提交状态

                result = self.task_service.create_task(task_data)
                if result['success']:
                    messagebox.showinfo("成功", "任务已提交，开始执行")
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


def main():
    """测试添加任务对话框"""
    root = tk.Tk()
    root.title("添加任务对话框测试")
    root.geometry("400x300")
    root.configure(bg='#f5f5f5')

    # 模拟用户信息
    user_info = {
        'id': 1,
        'username': 'test_user',
        'balance': 10000
    }

    def show_dialog():
        dialog = AddTaskDialog(root, user_info)
        result = dialog.show()
        if result:
            print("任务创建结果:", result)
        else:
            print("任务创建取消")

    # 测试按钮
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