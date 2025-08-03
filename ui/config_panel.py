"""
参数配置面板模块
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog


class ConfigDialog:
    """配置对话框"""

    def __init__(self, parent, settings):
        self.parent = parent
        self.settings = settings
        self.dialog = None
        self.create_dialog()

    def create_dialog(self):
        """创建对话框"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("选项配置")
        self.dialog.geometry("450x500")
        self.dialog.resizable(False, False)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        # 居中显示
        self.center_window()

        # 创建选项卡
        self.create_tabs()

    def center_window(self):
        """窗口居中"""
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")

    def create_tabs(self):
        """创建选项卡"""
        notebook = ttk.Notebook(self.dialog)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # 基本设置选项卡
        basic_frame = tk.Frame(notebook)
        notebook.add(basic_frame, text='基本设置')
        self.create_basic_settings(basic_frame)

        # 高级设置选项卡
        advanced_frame = tk.Frame(notebook)
        notebook.add(advanced_frame, text='高级设置')
        self.create_advanced_settings(advanced_frame)

        # 监测设置选项卡
        monitor_frame = tk.Frame(notebook)
        notebook.add(monitor_frame, text='监测设置')
        self.create_monitor_settings(monitor_frame)

        # 按钮框架
        self.create_buttons()

    def create_basic_settings(self, parent):
        """创建基本设置"""
        main_frame = tk.Frame(parent, padx=20, pady=20)
        main_frame.pack(fill='both', expand=True)

        # 发送间隔
        self.create_setting_row(main_frame, "发送间隔", "send_interval", 1000, "毫秒", required=True)

        # 卡片更换
        self.create_setting_row(main_frame, "卡片更换", "card_switch", 60, "条/次", required=True)

        # 重试次数
        self.create_setting_row(main_frame, "重试次数", "retry_count", 3, "次")

        # 超时设置
        self.create_setting_row(main_frame, "发送超时", "send_timeout", 10, "秒")

    def create_setting_row(self, parent, label_text, setting_key, default_value, unit_text, required=False):
        """创建设置行"""
        # 标签
        label_color = 'red' if required else 'black'
        prefix = "* " if required else ""
        tk.Label(parent, text=f"{prefix}{label_text}:", fg=label_color).pack(anchor='w', pady=(0, 5))

        # 输入框架
        frame = tk.Frame(parent)
        frame.pack(fill='x', pady=(0, 15))

        # 输入框
        entry = tk.Entry(frame, width=20)
        current_value = self.settings.get(setting_key, default_value)
        entry.insert(0, str(current_value))
        entry.pack(side='left')

        # 单位标签
        tk.Label(frame, text=unit_text).pack(side='left', padx=(5, 0))

        # 保存引用
        setattr(self, f"{setting_key}_entry", entry)

    def create_advanced_settings(self, parent):
        """创建高级设置"""
        main_frame = tk.Frame(parent, padx=20, pady=20)
        main_frame.pack(fill='both', expand=True)

        # 自动重连复选框
        self.auto_reconnect_var = tk.BooleanVar(value=self.settings.get('auto_reconnect', True))
        tk.Checkbutton(main_frame, text="设备断开时自动重连",
                      variable=self.auto_reconnect_var).pack(anchor='w', pady=(0, 10))

        # 自动停止复选框
        self.auto_stop_var = tk.BooleanVar(value=self.settings.get('auto_stop', True))
        tk.Checkbutton(main_frame, text="任务完成后自动停止",
                      variable=self.auto_stop_var).pack(anchor='w', pady=(0, 15))

        # 日志级别
        tk.Label(main_frame, text="日志级别:").pack(anchor='w', pady=(0, 5))
        self.log_level_combo = ttk.Combobox(main_frame,
                                           values=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                                           state='readonly', width=30)
        self.log_level_combo.set(self.settings.get('log_level', 'INFO'))
        self.log_level_combo.pack(anchor='w', pady=(0, 15))

        # 并发端口数
        self.create_number_setting(main_frame, "最大并发端口数", "max_concurrent_ports", 10, "个")

        # 数据保存路径
        self.create_path_setting(main_frame, "数据保存路径", "data_path", "./data")

    def create_number_setting(self, parent, label_text, setting_key, default_value, unit_text):
        """创建数字设置"""
        tk.Label(parent, text=f"{label_text}:").pack(anchor='w', pady=(0, 5))
        frame = tk.Frame(parent)
        frame.pack(fill='x', pady=(0, 15))

        entry = tk.Entry(frame, width=20)
        entry.insert(0, str(self.settings.get(setting_key, default_value)))
        entry.pack(side='left')

        tk.Label(frame, text=unit_text).pack(side='left', padx=(5, 0))

        setattr(self, f"{setting_key}_entry", entry)

    def create_path_setting(self, parent, label_text, setting_key, default_value):
        """创建路径设置"""
        tk.Label(parent, text=f"{label_text}:").pack(anchor='w', pady=(0, 5))
        frame = tk.Frame(parent)
        frame.pack(fill='x', pady=(0, 15))

        entry = tk.Entry(frame)
        entry.insert(0, self.settings.get(setting_key, default_value))
        entry.pack(side='left', fill='x', expand=True)

        tk.Button(frame, text="浏览", command=lambda: self.browse_path(entry),
                  bg='#e0e0e0', padx=10).pack(side='right', padx=(5, 0))

        setattr(self, f"{setting_key}_entry", entry)

    def browse_path(self, entry):
        """浏览路径"""
        directory = filedialog.askdirectory(
            title="选择目录",
            initialdir=entry.get()
        )
        if directory:
            entry.delete(0, tk.END)
            entry.insert(0, directory)

    def create_monitor_settings(self, parent):
        """创建监测设置"""
        main_frame = tk.Frame(parent, padx=20, pady=20)
        main_frame.pack(fill='both', expand=True)

        # 发送成功阈值
        self.create_setting_row(main_frame, "发送成功阈值", "success_threshold", 1000, "条", required=True)

        # 失败率告警阈值
        tk.Label(main_frame, text="失败率告警阈值:").pack(anchor='w', pady=(0, 5))
        frame = tk.Frame(main_frame)
        frame.pack(fill='x', pady=(0, 15))

        self.failure_rate_entry = tk.Entry(frame, width=20)
        self.failure_rate_entry.insert(0, str(self.settings.get('failure_rate_threshold', 0.2)))
        self.failure_rate_entry.pack(side='left')

        tk.Label(frame, text="(0.0-1.0)").pack(side='left', padx=(5, 0))

        # 监测号码
        tk.Label(main_frame, text="监测号码:").pack(anchor='w', pady=(0, 5))
        self.monitor_text = scrolledtext.ScrolledText(main_frame, height=6)
        self.monitor_text.insert('1.0', self.settings.get('monitor_numbers', ''))
        self.monitor_text.pack(fill='x', pady=(0, 15))

        # 启用邮件通知
        self.email_notify_var = tk.BooleanVar(value=self.settings.get('email_notify', False))
        email_check = tk.Checkbutton(main_frame, text="启用邮件告警通知",
                                    variable=self.email_notify_var,
                                    command=self.toggle_email_settings)
        email_check.pack(anchor='w', pady=(0, 10))

        # 邮件设置框架
        self.create_email_settings(main_frame)

    def create_email_settings(self, parent):
        """创建邮件设置"""
        self.email_frame = tk.LabelFrame(parent, text="邮件设置", padx=10, pady=10)
        self.email_frame.pack(fill='x', pady=(0, 15))

        # SMTP服务器
        tk.Label(self.email_frame, text="SMTP服务器:").pack(anchor='w', pady=(0, 2))
        self.smtp_server_entry = tk.Entry(self.email_frame, width=40)
        self.smtp_server_entry.insert(0, self.settings.get('smtp_server', 'smtp.qq.com'))
        self.smtp_server_entry.pack(fill='x', pady=(0, 5))

        # SMTP端口
        port_frame = tk.Frame(self.email_frame)
        port_frame.pack(fill='x', pady=(0, 5))
        tk.Label(port_frame, text="SMTP端口:").pack(side='left')
        self.smtp_port_entry = tk.Entry(port_frame, width=10)
        self.smtp_port_entry.insert(0, str(self.settings.get('smtp_port', 587)))
        self.smtp_port_entry.pack(side='left', padx=(10, 0))

        # 发送邮箱
        tk.Label(self.email_frame, text="发送邮箱:").pack(anchor='w', pady=(5, 2))
        self.sender_email_entry = tk.Entry(self.email_frame, width=40)
        self.sender_email_entry.insert(0, self.settings.get('sender_email', ''))
        self.sender_email_entry.pack(fill='x', pady=(0, 5))

        # 邮箱密码
        tk.Label(self.email_frame, text="邮箱密码:").pack(anchor='w', pady=(5, 2))
        self.email_password_entry = tk.Entry(self.email_frame, width=40, show='*')
        self.email_password_entry.insert(0, self.settings.get('email_password', ''))
        self.email_password_entry.pack(fill='x', pady=(0, 5))

        # 接收邮箱
        tk.Label(self.email_frame, text="接收邮箱:").pack(anchor='w', pady=(5, 2))
        self.receiver_email_entry = tk.Entry(self.email_frame, width=40)
        self.receiver_email_entry.insert(0, self.settings.get('receiver_email', ''))
        self.receiver_email_entry.pack(fill='x', pady=(0, 5))

        # 初始状态
        self.toggle_email_settings()

    def toggle_email_settings(self):
        """切换邮件设置显示状态"""
        if self.email_notify_var.get():
            # 显示邮件设置
            for widget in self.email_frame.winfo_children():
                widget.configure(state='normal')
        else:
            # 隐藏邮件设置（禁用控件）
            for widget in self.email_frame.winfo_children():
                if isinstance(widget, (tk.Entry, tk.Button)):
                    widget.configure(state='disabled')

    def create_buttons(self):
        """创建按钮"""
        btn_frame = tk.Frame(self.dialog)
        btn_frame.pack(fill='x', padx=10, pady=(0, 10))

        tk.Button(btn_frame, text="取消", command=self.dialog.destroy,
                  bg='#e0e0e0', padx=20).pack(side='right', padx=(5, 0))
        tk.Button(btn_frame, text="应用", command=self.apply_settings,
                  bg='#007bff', fg='white', padx=20).pack(side='right', padx=(5, 0))
        tk.Button(btn_frame, text="保存", command=self.save_settings,
                  bg='#ff6b35', fg='white', padx=20).pack(side='right')

    def validate_settings(self):
        """验证设置"""
        try:
            # 验证数字输入
            int(self.send_interval_entry.get())
            int(self.card_switch_entry.get())
            int(self.retry_count_entry.get())
            int(self.send_timeout_entry.get())
            int(self.success_threshold_entry.get())
            int(self.max_concurrent_ports_entry.get())

            float(self.failure_rate_entry.get())

            # 验证邮件设置
            if self.email_notify_var.get():
                int(self.smtp_port_entry.get())

                if not self.sender_email_entry.get().strip():
                    raise ValueError("发送邮箱不能为空")
                if not self.receiver_email_entry.get().strip():
                    raise ValueError("接收邮箱不能为空")

            return True

        except ValueError as e:
            messagebox.showerror("验证错误", f"输入验证失败: {e}")
            return False

    def collect_settings(self):
        """收集设置"""
        return {
            'send_interval': int(self.send_interval_entry.get()),
            'card_switch': int(self.card_switch_entry.get()),
            'retry_count': int(self.retry_count_entry.get()),
            'send_timeout': int(self.send_timeout_entry.get()),
            'auto_reconnect': self.auto_reconnect_var.get(),
            'auto_stop': self.auto_stop_var.get(),
            'log_level': self.log_level_combo.get(),
            'max_concurrent_ports': int(self.max_concurrent_ports_entry.get()),
            'data_path': self.data_path_entry.get().strip(),
            'success_threshold': int(self.success_threshold_entry.get()),
            'failure_rate_threshold': float(self.failure_rate_entry.get()),
            'monitor_numbers': self.monitor_text.get('1.0', tk.END).strip(),
            'email_notify': self.email_notify_var.get(),
            'smtp_server': self.smtp_server_entry.get().strip(),
            'smtp_port': int(self.smtp_port_entry.get()),
            'sender_email': self.sender_email_entry.get().strip(),
            'email_password': self.email_password_entry.get(),
            'receiver_email': self.receiver_email_entry.get().strip()
        }

    def apply_settings(self):
        """应用设置"""
        if not self.validate_settings():
            return

        new_settings = self.collect_settings()
        self.settings.update(new_settings)

        messagebox.showinfo("成功", "设置已应用")

    def save_settings(self):
        """保存设置"""
        if not self.validate_settings():
            return

        new_settings = self.collect_settings()
        self.settings.update(new_settings)

        # 保存到文件
        if self.settings.save_config():
            messagebox.showinfo("成功", "设置已保存")
            self.dialog.destroy()
        else:
            messagebox.showerror("错误", "设置保存失败")


class QuickSettingsPanel(tk.Frame):
    """快速设置面板"""

    def __init__(self, parent, settings, **kwargs):
        super().__init__(parent, **kwargs)
        self.settings = settings

        self.create_widgets()

    def create_widgets(self):
        """创建控件"""
        # 标题
        title_label = tk.Label(self, text="快速设置", font=('Arial', 12, 'bold'))
        title_label.pack(anchor='w', pady=(0, 10))

        # 发送间隔
        interval_frame = tk.Frame(self)
        interval_frame.pack(fill='x', pady=5)

        tk.Label(interval_frame, text="发送间隔:", width=10, anchor='w').pack(side='left')
        self.interval_var = tk.StringVar(value=str(self.settings.get('send_interval', 1000)))
        interval_spinbox = tk.Spinbox(interval_frame, from_=100, to=10000, increment=100,
                                     textvariable=self.interval_var, width=10)
        interval_spinbox.pack(side='left', padx=(5, 0))
        tk.Label(interval_frame, text="毫秒").pack(side='left', padx=(5, 0))

        # 卡片更换
        card_frame = tk.Frame(self)
        card_frame.pack(fill='x', pady=5)

        tk.Label(card_frame, text="卡片更换:", width=10, anchor='w').pack(side='left')
        self.card_var = tk.StringVar(value=str(self.settings.get('card_switch', 60)))
        card_spinbox = tk.Spinbox(card_frame, from_=1, to=1000, increment=10,
                                 textvariable=self.card_var, width=10)
        card_spinbox.pack(side='left', padx=(5, 0))
        tk.Label(card_frame, text="条/次").pack(side='left', padx=(5, 0))

        # 应用按钮
        tk.Button(self, text="应用设置", command=self.apply_quick_settings,
                  bg='#ff6b35', fg='white', padx=15, pady=5).pack(pady=(10, 0))

    def apply_quick_settings(self):
        """应用快速设置"""
        try:
            self.settings.set('send_interval', int(self.interval_var.get()))
            self.settings.set('card_switch', int(self.card_var.get()))
            messagebox.showinfo("成功", "快速设置已应用")
        except ValueError:
            messagebox.showerror("错误", "设置值必须是数字")
        except Exception as e:
            messagebox.showerror("错误", f"应用设置失败: {e}")