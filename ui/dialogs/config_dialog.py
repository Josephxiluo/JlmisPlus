"""
选项配置对话框
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ui.styles import get_color, get_font
from config.settings import Settings


class ConfigDialog:
    """选项配置对话框"""

    def __init__(self, parent):
        self.parent = parent
        self.settings = Settings()
        self.result = None
        self.create_dialog()

    def create_dialog(self):
        """创建对话框"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("选项配置")
        self.dialog.geometry("450x400")
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

        # 加载当前配置
        self.load_current_config()

    def center_dialog(self):
        """对话框居中显示"""
        self.dialog.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (450 // 2)
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (400 // 2)
        self.dialog.geometry(f"450x400+{x}+{y}")

    def create_content(self):
        """创建对话框内容"""
        # 主容器
        main_frame = tk.Frame(self.dialog, bg=get_color('background'))
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)

        # 发送设置组
        self.create_send_settings(main_frame)

        # 监测设置组
        self.create_monitor_settings(main_frame)

    def create_send_settings(self, parent):
        """创建发送设置"""
        # 发送设置分组
        send_group = tk.LabelFrame(
            parent,
            text="发送设置",
            font=get_font('button'),
            fg=get_color('primary'),
            bg=get_color('background'),
            padx=15,
            pady=10
        )
        send_group.pack(fill='x', pady=(0, 20))

        # 发送间隔
        interval_frame = tk.Frame(send_group, bg=get_color('background'))
        interval_frame.pack(fill='x', pady=(0, 10))

        tk.Label(
            interval_frame,
            text="* 发送间隔:",
            font=get_font('default'),
            fg=get_color('danger'),
            bg=get_color('background')
        ).pack(side='left')

        self.send_interval_var = tk.StringVar(value="1000")
        interval_entry = tk.Entry(
            interval_frame,
            textvariable=self.send_interval_var,
            font=get_font('default'),
            relief='solid',
            bd=1,
            width=10
        )
        interval_entry.pack(side='left', padx=(10, 5))

        tk.Label(
            interval_frame,
            text="毫秒",
            font=get_font('default'),
            fg=get_color('text'),
            bg=get_color('background')
        ).pack(side='left')

        # 卡片更换
        card_frame = tk.Frame(send_group, bg=get_color('background'))
        card_frame.pack(fill='x')

        tk.Label(
            card_frame,
            text="* 卡片更换:",
            font=get_font('default'),
            fg=get_color('danger'),
            bg=get_color('background')
        ).pack(side='left')

        self.card_change_var = tk.StringVar(value="60")
        card_entry = tk.Entry(
            card_frame,
            textvariable=self.card_change_var,
            font=get_font('default'),
            relief='solid',
            bd=1,
            width=10
        )
        card_entry.pack(side='left', padx=(10, 5))

        tk.Label(
            card_frame,
            text="条/次",
            font=get_font('default'),
            fg=get_color('text'),
            bg=get_color('background')
        ).pack(side='left')

    def create_monitor_settings(self, parent):
        """创建监测设置"""
        # 监测设置分组
        monitor_group = tk.LabelFrame(
            parent,
            text="监测设置",
            font=get_font('button'),
            fg=get_color('primary'),
            bg=get_color('background'),
            padx=15,
            pady=10
        )
        monitor_group.pack(fill='x', pady=(0, 20))

        # 发送成功
        success_frame = tk.Frame(monitor_group, bg=get_color('background'))
        success_frame.pack(fill='x', pady=(0, 10))

        tk.Label(
            success_frame,
            text="* 发送成功:",
            font=get_font('default'),
            fg=get_color('danger'),
            bg=get_color('background')
        ).pack(side='left')

        self.success_count_var = tk.StringVar(value="1000")
        success_entry = tk.Entry(
            success_frame,
            textvariable=self.success_count_var,
            font=get_font('default'),
            relief='solid',
            bd=1,
            width=10
        )
        success_entry.pack(side='left', padx=(10, 5))

        tk.Label(
            success_frame,
            text="条",
            font=get_font('default'),
            fg=get_color('text'),
            bg=get_color('background')
        ).pack(side='left')

        # 监测号码
        phone_frame = tk.Frame(monitor_group, bg=get_color('background'))
        phone_frame.pack(fill='x')

        tk.Label(
            phone_frame,
            text="监测号码:",
            font=get_font('default'),
            fg=get_color('text'),
            bg=get_color('background')
        ).pack(anchor='w', pady=(0, 5))

        self.monitor_phone_entry = tk.Entry(
            phone_frame,
            font=get_font('default'),
            relief='solid',
            bd=1
        )
        self.monitor_phone_entry.pack(fill='x')

        # 提示信息
        tip_frame = tk.Frame(parent, bg=get_color('primary_light'), relief='solid', bd=1)
        tip_frame.pack(fill='x')

        tk.Label(
            tip_frame,
            text="配置说明：",
            font=get_font('button'),
            fg=get_color('text'),
            bg=get_color('primary_light')
        ).pack(anchor='w', padx=10, pady=(10, 5))

        tip_text = """• 发送间隔：每条短信发送之间的时间间隔（毫秒）
• 卡片更换：发送指定条数后自动更换SIM卡
• 发送成功：达到此数量时触发监测机制
• 监测号码：用于接收监测短信的手机号码"""

        tk.Label(
            tip_frame,
            text=tip_text,
            font=get_font('small'),
            fg=get_color('text'),
            bg=get_color('primary_light'),
            justify='left'
        ).pack(anchor='w', padx=10, pady=(0, 10))

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
            text="保存",
            font=get_font('button'),
            bg=get_color('primary'),
            fg='white',
            relief='flat',
            cursor='hand2',
            command=self.save,
            width=12
        )
        save_btn.pack(side='right')

    def load_current_config(self):
        """加载当前配置"""
        try:
            config = self.settings.get_all()

            # 发送设置
            send_config = config.get('send', {})
            self.send_interval_var.set(str(send_config.get('interval', 1000)))
            self.card_change_var.set(str(send_config.get('card_change_count', 60)))

            # 监测设置
            monitor_config = config.get('monitor', {})
            self.success_count_var.set(str(monitor_config.get('success_threshold', 1000)))
            self.monitor_phone_entry.insert(0, monitor_config.get('monitor_phone', ''))

        except Exception as e:
            print(f"加载配置失败：{str(e)}")

    def validate_form(self):
        """验证表单"""
        try:
            # 验证发送间隔
            interval = int(self.send_interval_var.get())
            if interval < 100:
                messagebox.showerror("错误", "发送间隔不能小于100毫秒")
                return False

            # 验证卡片更换
            card_change = int(self.card_change_var.get())
            if card_change < 1:
                messagebox.showerror("错误", "卡片更换数量不能小于1")
                return False

            # 验证成功数量
            success_count = int(self.success_count_var.get())
            if success_count < 1:
                messagebox.showerror("错误", "监测成功数量不能小于1")
                return False

            # 验证监测号码（如果填写了）
            monitor_phone = self.monitor_phone_entry.get().strip()
            if monitor_phone:
                if not monitor_phone.isdigit() or len(monitor_phone) != 11:
                    messagebox.showerror("错误", "监测号码格式不正确")
                    return False

            return True

        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字")
            return False

    def save(self):
        """保存配置"""
        if not self.validate_form():
            return

        try:
            # 构建配置数据
            config_data = {
                'send': {
                    'interval': int(self.send_interval_var.get()),
                    'card_change_count': int(self.card_change_var.get())
                },
                'monitor': {
                    'success_threshold': int(self.success_count_var.get()),
                    'monitor_phone': self.monitor_phone_entry.get().strip()
                }
            }

            # 保存配置
            self.settings.update_config(config_data)

            messagebox.showinfo("成功", "配置已保存")
            self.result = config_data
            self.dialog.destroy()

        except Exception as e:
            messagebox.showerror("错误", f"保存配置失败：{str(e)}")

    def cancel(self):
        """取消"""
        self.result = None
        self.dialog.destroy()

    def show(self):
        """显示对话框并返回结果"""
        self.dialog.wait_window()
        return self.result


def main():
    """测试配置对话框"""
    root = tk.Tk()
    root.title("配置对话框测试")
    root.geometry("400x300")
    root.configure(bg='#f5f5f5')

    def show_dialog():
        dialog = ConfigDialog(root)
        result = dialog.show()
        if result:
            print("配置结果:", result)
        else:
            print("配置取消")

    # 测试按钮
    test_btn = tk.Button(
        root,
        text="打开配置对话框",
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