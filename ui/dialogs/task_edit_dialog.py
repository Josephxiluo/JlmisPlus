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
from services.task_service import TaskService


class TaskEditDialog:
    """任务编辑对话框"""

    def __init__(self, parent, task):
        self.parent = parent
        self.task = task
        self.task_service = TaskService()
        self.result = None
        self.create_dialog()

    def create_dialog(self):
        """创建对话框"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("修改内容")
        self.dialog.geometry("500x500")
        self.dialog.resizable(False, False)
        self.dialog.configure(bg=get_color('background'))

        # 设置模态对话框
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        # 居中显示
        self.center_dialog()

        # 创建内容
        self.create_content()

        # 创建按钮
        self.create_buttons()

        # 加载任务数据
        self.load_task_data()

    def center_dialog(self):
        """对话框居中显示"""
        self.dialog.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (500 // 2)
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (500 // 2)
        self.dialog.geometry(f"500x500+{x}+{y}")

    def create_content(self):
        """创建对话框内容"""
        # 主容器
        main_frame = tk.Frame(self.dialog, bg=get_color('background'))
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)

        # 任务信息显示
        self.create_task_info(main_frame)

        # 内容编辑区域
        self.create_content_editor(main_frame)

    def create_task_info(self, parent):
        """创建任务信息显示"""
        info_frame = tk.Frame(parent, bg=get_color('primary_light'), relief='solid', bd=1)
        info_frame.pack(fill='x', pady=(0, 20))

        # 任务标题
        task_name = self.task.get('title', f"v{self.task.get('id', '')}")
        tk.Label(
            info_frame,
            text=f"任务：{task_name}",
            font=get_font('title'),
            fg=get_color('text'),
            bg=get_color('primary_light')
        ).pack(anchor='w', padx=15, pady=(10, 5))

        # 任务统计信息
        stats_frame = tk.Frame(info_frame, bg=get_color('primary_light'))
        stats_frame.pack(fill='x', padx=15, pady=(0, 10))

        total = self.task.get('total', 0)
        sent = self.task.get('sent', 0)
        success = self.task.get('success_count', 0)
        failed = self.task.get('failed_count', 0)

        tk.Label(
            stats_frame,
            text=f"总数：{total}",
            font=get_font('small'),
            fg=get_color('text'),
            bg=get_color('primary_light')
        ).pack(side='left', padx=(0, 20))

        tk.Label(
            stats_frame,
            text=f"已发送：{sent}",
            font=get_font('small'),
            fg=get_color('text'),
            bg=get_color('primary_light')
        ).pack(side='left', padx=(0, 20))

        tk.Label(
            stats_frame,
            text=f"成功：{success}",
            font=get_font('small'),
            fg=get_color('success'),
            bg=get_color('primary_light')
        ).pack(side='left', padx=(0, 20))

        tk.Label(
            stats_frame,
            text=f"失败：{failed}",
            font=get_font('small'),
            fg=get_color('danger'),
            bg=get_color('primary_light')
        ).pack(side='left')

    def create_content_editor(self, parent):
        """创建内容编辑器"""
        # 任务类型显示
        task_type = "彩信" if self.task.get('type') == 'mms' else "短信"
        tk.Label(
            parent,
            text=f"任务类型：{task_type}",
            font=get_font('default'),
            fg=get_color('text'),
            bg=get_color('background')
        ).pack(anchor='w', pady=(0, 10))

        # 主题编辑（彩信专用）
        if self.task.get('type') == 'mms':
            tk.Label(
                parent,
                text="主题:",
                font=get_font('default'),
                fg=get_color('text'),
                bg=get_color('background')
            ).pack(anchor='w', pady=(0, 5))

            self.subject_entry = tk.Entry(
                parent,
                font=get_font('default'),
                relief='solid',
                bd=1
            )
            self.subject_entry.pack(fill='x', pady=(0, 15))
        else:
            self.subject_entry = None

        # 内容编辑
        tk.Label(
            parent,
            text="* 短信内容:",
            font=get_font('default'),
            fg=get_color('danger'),
            bg=get_color('background')
        ).pack(anchor='w', pady=(0, 5))

        # 内容输入区域
        content_frame = tk.Frame(parent, bg=get_color('background'))
        content_frame.pack(fill='both', expand=True, pady=(0, 15))

        # 内容文本框
        self.content_text = tk.Text(
            content_frame,
            font=get_font('default'),
            relief='solid',
            bd=1,
            wrap='word'
        )
        self.content_text.pack(side='left', fill='both', expand=True)

        # 滚动条
        content_scroll = ttk.Scrollbar(content_frame, orient='vertical', command=self.content_text.yview)
        self.content_text.configure(yscrollcommand=content_scroll.set)
        content_scroll.pack(side='right', fill='y')

        # 字符计数
        self.char_count_label = tk.Label(
            parent,
            text="字符数：0",
            font=get_font('small'),
            fg=get_color('text_light'),
            bg=get_color('background')
        )
        self.char_count_label.pack(anchor='w', pady=(0, 10))

        # 绑定内容变化事件
        self.content_text.bind('<KeyRelease>', self.on_content_change)
        self.content_text.bind('<Button-1>', self.on_content_change)

        # 编辑提示
        tip_frame = tk.Frame(parent, bg=get_color('primary_light'), relief='solid', bd=1)
        tip_frame.pack(fill='x')

        tip_text = """注意事项：
• 修改内容后，未发送的消息将使用新内容
• 已经发送成功的消息不会受影响
• 建议在任务开始前完成内容编辑"""

        tk.Label(
            tip_frame,
            text=tip_text,
            font=get_font('small'),
            fg=get_color('text'),
            bg=get_color('primary_light'),
            justify='left'
        ).pack(anchor='w', padx=10, pady=10)

    def load_task_data(self):
        """加载任务数据"""
        # 加载主题（如果是彩信）
        if self.subject_entry and self.task.get('subject'):
            self.subject_entry.insert(0, self.task.get('subject', ''))

        # 加载内容
        content = self.task.get('content', '')
        if content:
            self.content_text.insert('1.0', content)

        # 更新字符计数
        self.update_char_count()

    def on_content_change(self, event=None):
        """内容变化事件"""
        self.update_char_count()

    def update_char_count(self):
        """更新字符计数"""
        content = self.content_text.get('1.0', 'end-1c')
        char_count = len(content)
        self.char_count_label.config(text=f"字符数：{char_count}")

        # 根据字符数设置颜色提示
        if char_count > 70:
            color = get_color('danger')
        elif char_count > 50:
            color = get_color('warning')
        else:
            color = get_color('text_light')

        self.char_count_label.config(fg=color)

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
            width=12
        )
        cancel_btn.pack(side='left')

        # 保存按钮
        save_btn = tk.Button(
            button_frame,
            text="保存修改",
            font=get_font('button'),
            bg=get_color('primary'),
            fg='white',
            relief='flat',
            cursor='hand2',
            command=self.save,
            width=12
        )
        save_btn.pack(side='right')

    def validate_form(self):
        """验证表单"""
        content = self.content_text.get('1.0', 'end-1c').strip()
        if not content:
            messagebox.showerror("错误", "请输入短信内容")
            self.content_text.focus()
            return False

        # 彩信主题验证
        if self.subject_entry:
            subject = self.subject_entry.get().strip()
            if not subject:
                messagebox.showerror("错误", "彩信模式下请输入主题")
                self.subject_entry.focus()
                return False

        return True

    def save(self):
        """保存修改"""
        if not self.validate_form():
            return

        content = self.content_text.get('1.0', 'end-1c').strip()
        subject = self.subject_entry.get().strip() if self.subject_entry else ''

        # 确认修改
        if messagebox.askyesno("确认修改", "确定要保存对任务内容的修改吗？\n修改后将影响未发送的消息。"):
            try:
                # 构建更新数据
                update_data = {
                    'task_id': self.task.get('id'),
                    'content': content
                }

                if subject:
                    update_data['subject'] = subject

                # 调用服务更新任务
                result = self.task_service.update_task_content(update_data)
                if result['success']:
                    messagebox.showinfo("成功", "任务内容已更新")
                    self.result = result
                    self.dialog.destroy()
                else:
                    messagebox.showerror("失败", result['message'])

            except Exception as e:
                messagebox.showerror("错误", f"保存修改失败：{str(e)}")

    def cancel(self):
        """取消修改"""
        # 检查是否有未保存的修改
        current_content = self.content_text.get('1.0', 'end-1c').strip()
        original_content = self.task.get('content', '').strip()

        if current_content != original_content:
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
        'type': 'sms',  # 或 'mms'
        'total': 100,
        'sent': 25,
        'success_count': 20,
        'failed_count': 5
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