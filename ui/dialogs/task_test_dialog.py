"""
任务测试对话框
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ui.styles import get_color, get_font
from services.task_service import TaskService


class TaskTestDialog:
    """任务测试对话框"""

    def __init__(self, parent, task):
        self.parent = parent
        self.task = task
        self.task_service = TaskService()
        self.result = None
        self.create_dialog()

    def create_dialog(self):
        """创建对话框"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("任务测试")
        self.dialog.geometry("400x300")
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

    def center_dialog(self):
        """对话框居中显示"""
        self.dialog.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (400 // 2)
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (400 // 2)
        self.dialog.geometry(f"400x500+{x}+{y}")

    def create_content(self):
        """创建对话框内容"""
        # 主容器
        main_frame = tk.Frame(self.dialog, bg=get_color('background'))
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)

        # 任务名称显示
        task_name = self.task.get('title', f"v{self.task.get('id', '')}")
        tk.Label(
            main_frame,
            text=f"任务名称：{task_name}",
            font=get_font('title'),
            fg=get_color('text'),
            bg=get_color('background')
        ).pack(anchor='w', pady=(0, 15))

        # 测试手机号
        tk.Label(
            main_frame,
            text="* 测试手机号:",
            font=get_font('default'),
            fg=get_color('danger'),
            bg=get_color('background')
        ).pack(anchor='w', pady=(0, 5))

        self.phone_entry = tk.Entry(
            main_frame,
            font=get_font('default'),
            relief='solid',
            bd=1
        )
        self.phone_entry.pack(fill='x', pady=(0, 15))
        self.phone_entry.insert(0, "请输入手机号")
        self.phone_entry.bind('<FocusIn>', self.on_phone_focus_in)
        self.phone_entry.bind('<FocusOut>', self.on_phone_focus_out)

        # 测试端口
        tk.Label(
            main_frame,
            text="* 测试端口:",
            font=get_font('default'),
            fg=get_color('danger'),
            bg=get_color('background')
        ).pack(anchor='w', pady=(0, 5))

        self.port_var = tk.StringVar()
        port_combo = ttk.Combobox(
            main_frame,
            textvariable=self.port_var,
            values=["请选择测试端口"],
            state='readonly',
            font=get_font('default')
        )
        port_combo.pack(fill='x', pady=(0, 15))
        port_combo.set("请选择测试端口")

        # 加载可用端口
        self.load_available_ports(port_combo)

        # 测试说明
        info_frame = tk.Frame(main_frame, bg=get_color('primary_light'), relief='solid', bd=1)
        info_frame.pack(fill='x', pady=(15, 0))

        tk.Label(
            info_frame,
            text="测试说明：",
            font=get_font('button'),
            fg=get_color('text'),
            bg=get_color('primary_light')
        ).pack(anchor='w', padx=10, pady=(10, 5))

        info_text = """• 测试将向指定手机号发送一条测试短信
• 测试不会消耗您的短信积分
• 请确保手机号码格式正确
• 测试结果将显示发送状态"""

        tk.Label(
            info_frame,
            text=info_text,
            font=get_font('small'),
            fg=get_color('text'),
            bg=get_color('primary_light'),
            justify='left'
        ).pack(anchor='w', padx=10, pady=(0, 10))

    def load_available_ports(self, combo):
        """加载可用端口"""
        try:
            # 这里应该调用服务获取可用端口
            # 暂时使用模拟数据
            ports = [
                "COM101 - 中国联通",
                "COM102 - 中国联通",
                "COM103 - 中国电信",
                "COM104 - 中国电信",
                "COM105 - 中国电信"
            ]
            combo['values'] = ports
            if ports:
                combo.set(ports[0])
        except Exception as e:
            print(f"加载端口失败：{str(e)}")

    def on_phone_focus_in(self, event):
        """手机号输入框获得焦点"""
        if self.phone_entry.get() == "请输入手机号":
            self.phone_entry.delete(0, 'end')
            self.phone_entry.config(fg=get_color('text'))

    def on_phone_focus_out(self, event):
        """手机号输入框失去焦点"""
        if not self.phone_entry.get().strip():
            self.phone_entry.insert(0, "请输入手机号")
            self.phone_entry.config(fg=get_color('text_light'))

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
            fg='#000000',
            relief='flat',
            cursor='hand2',
            command=self.cancel,
            width=12
        )
        cancel_btn.pack(side='left')

        # 确定按钮
        confirm_btn = tk.Button(
            button_frame,
            text="确定",
            font=get_font('button'),
            bg=get_color('primary'),
            fg='#000000',
            relief='flat',
            cursor='hand2',
            command=self.confirm,
            width=12
        )
        confirm_btn.pack(side='right')

    def validate_form(self):
        """验证表单"""
        phone = self.phone_entry.get().strip()
        if not phone or phone == "请输入手机号":
            messagebox.showerror("错误", "请输入测试手机号")
            self.phone_entry.focus()
            return False

        # 简单的手机号格式验证
        if not phone.isdigit() or len(phone) != 11:
            messagebox.showerror("错误", "请输入正确的11位手机号")
            self.phone_entry.focus()
            return False

        if self.port_var.get() == "请选择测试端口":
            messagebox.showerror("错误", "请选择测试端口")
            return False

        return True

    def confirm(self):
        """确认测试"""
        if not self.validate_form():
            return

        phone = self.phone_entry.get().strip()
        port = self.port_var.get()

        # 确认测试
        if messagebox.askyesno("确认测试", f"确定要向 {phone} 发送测试短信吗？\n使用端口：{port}"):
            try:
                # 执行测试
                test_data = {
                    'task_id': self.task.get('id'),
                    'test_phone': phone,
                    'test_port': port.split(' ')[0]  # 提取端口号
                }

                result = self.task_service.test_task(test_data)
                if result['success']:
                    messagebox.showinfo("测试成功", f"测试短信已发送到 {phone}\n发送时间：{result.get('send_time', '刚刚')}")
                    self.result = result
                    self.dialog.destroy()
                else:
                    messagebox.showerror("测试失败", result['message'])

            except Exception as e:
                messagebox.showerror("错误", f"测试失败：{str(e)}")

    def cancel(self):
        """取消测试"""
        self.result = None
        self.dialog.destroy()

    def show(self):
        """显示对话框并返回结果"""
        self.dialog.wait_window()
        return self.result


def main():
    """测试任务测试对话框"""
    root = tk.Tk()
    root.title("任务测试对话框测试")
    root.geometry("400x300")
    root.configure(bg='#f5f5f5')

    # 模拟任务信息
    task = {
        'id': 'v342',
        'title': '测试任务',
        'content': '这是一条测试短信',
        'type': 'sms'
    }

    def show_dialog():
        dialog = TaskTestDialog(root, task)
        result = dialog.show()
        if result:
            print("测试结果:", result)
        else:
            print("测试取消")

    # 测试按钮
    test_btn = tk.Button(
        root,
        text="打开任务测试对话框",
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