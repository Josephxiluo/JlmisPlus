"""
通用控件模块
"""
import tkinter as tk
from tkinter import ttk
from datetime import datetime


def init_styles(root):
    style = ttk.Style(root)
    style.theme_use('default')  # 可根据需要换成 'clam', 'alt', 'classic'

    style.configure("Primary.TButton",
                    background="#ff6b35", foreground="white",
                    font=('Arial', 10, 'bold'), padding=6)
    style.map("Primary.TButton",
              background=[("active", "#e65c28")])

    style.configure("Secondary.TButton",
                    background="#e0e0e0", foreground="black",
                    font=('Arial', 10), padding=6)
    style.map("Secondary.TButton",
              background=[("active", "#d0d0d0")])

    style.configure("Danger.TButton",
                    background="#d9534f", foreground="white",
                    font=('Arial', 10, 'bold'), padding=6)
    style.map("Danger.TButton",
              background=[("active", "#c9302c")])

def create_button(parent, text, command, variant="primary"):
    style_map = {
        "primary": "Primary.TButton",
        "secondary": "Secondary.TButton",
        "danger": "Danger.TButton"
    }
    style = style_map.get(variant, "Primary.TButton")
    return ttk.Button(parent, text=text, command=command, style=style)


class StatusBar(tk.Frame):
    """状态栏控件"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg='white', height=30, **kwargs)
        self.pack_propagate(False)

        self.create_widgets()

    def create_widgets(self):
        """创建控件"""
        # 状态标签
        self.status_label = tk.Label(self, text="就绪", bg='white', fg='#666', anchor='w')
        self.status_label.pack(side='left', padx=10, pady=5, fill='x', expand=True)

        # 分隔符
        separator = tk.Label(self, text="|", bg='white', fg='#ccc')
        separator.pack(side='right', padx=5, pady=5)

        # 版本标签
        version_label = tk.Label(self, text="Jinmis Plus - 直发",
                                bg='white', fg='#999', font=('Arial', 8))
        version_label.pack(side='right', padx=10, pady=5)

    def update_status(self, message):
        """更新状态"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.status_label.config(text=f"[{timestamp}] {message}")


class ProgressDialog:
    """进度对话框"""

    def __init__(self, parent, title="进度", message="处理中..."):
        self.parent = parent
        self.title = title
        self.message = message
        self.cancelled = False

        self.create_dialog()

    def create_dialog(self):
        """创建对话框"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title(self.title)
        self.dialog.geometry("400x150")
        self.dialog.resizable(False, False)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        # 居中显示
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")

        # 主框架
        main_frame = tk.Frame(self.dialog, padx=20, pady=20)
        main_frame.pack(fill='both', expand=True)

        # 消息标签
        self.message_label = tk.Label(main_frame, text=self.message, font=('Arial', 10))
        self.message_label.pack(pady=(0, 15))

        # 进度条
        self.progress_bar = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress_bar.pack(fill='x', pady=(0, 15))
        self.progress_bar.start()

        # 取消按钮
        self.cancel_button = tk.Button(main_frame, text="取消", command=self.cancel,
                                      bg='#e0e0e0', padx=20)
        self.cancel_button.pack()

    def update_message(self, message):
        """更新消息"""
        self.message_label.config(text=message)
        self.dialog.update()

    def update_progress(self, value):
        """更新进度"""
        self.progress_bar.config(mode='determinate')
        self.progress_bar['value'] = value
        self.dialog.update()

    def cancel(self):
        """取消操作"""
        self.cancelled = True
        self.close()

    def close(self):
        """关闭对话框"""
        self.progress_bar.stop()
        self.dialog.destroy()

    def is_cancelled(self):
        """检查是否被取消"""
        return self.cancelled


class MessageBox:
    """自定义消息框"""

    @staticmethod
    def show_info(parent, title, message, details=None):
        """显示信息对话框"""
        return MessageBox._show_dialog(parent, title, message, 'info', details)

    @staticmethod
    def show_warning(parent, title, message, details=None):
        """显示警告对话框"""
        return MessageBox._show_dialog(parent, title, message, 'warning', details)

    @staticmethod
    def show_error(parent, title, message, details=None):
        """显示错误对话框"""
        return MessageBox._show_dialog(parent, title, message, 'error', details)

    @staticmethod
    def show_question(parent, title, message, details=None):
        """显示询问对话框"""
        return MessageBox._show_dialog(parent, title, message, 'question', details)

    @staticmethod
    def _show_dialog(parent, title, message, msg_type, details):
        """显示对话框"""
        dialog = tk.Toplevel(parent)
        dialog.title(title)
        dialog.resizable(False, False)
        dialog.transient(parent)
        dialog.grab_set()

        # 图标和颜色配置
        icons = {
            'info': '🛈',
            'warning': '⚠',
            'error': '❌',
            'question': '❓'
        }

        colors = {
            'info': '#007bff',
            'warning': '#ff9800',
            'error': '#f44336',
            'question': '#4caf50'
        }

        # 主框架
        main_frame = tk.Frame(dialog, padx=20, pady=20)
        main_frame.pack(fill='both', expand=True)

        # 顶部框架（图标和消息）
        top_frame = tk.Frame(main_frame)
        top_frame.pack(fill='x', pady=(0, 15))

        # 图标
        icon_label = tk.Label(top_frame, text=icons.get(msg_type, '🛈'),
                             font=('Arial', 24), fg=colors.get(msg_type, '#007bff'))
        icon_label.pack(side='left', padx=(0, 15))

        # 消息
        message_label = tk.Label(top_frame, text=message, font=('Arial', 10),
                                wraplength=300, justify='left')
        message_label.pack(side='left', fill='both', expand=True)

        # 详细信息（如果有）
        if details:
            details_frame = tk.Frame(main_frame)
            details_frame.pack(fill='both', expand=True, pady=(0, 15))

            tk.Label(details_frame, text="详细信息:", font=('Arial', 9, 'bold')).pack(anchor='w')

            details_text = tk.Text(details_frame, height=6, wrap=tk.WORD, font=('Consolas', 8))
            details_text.pack(fill='both', expand=True)
            details_text.insert('1.0', details)
            details_text.config(state='disabled')

        # 按钮框架
        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(fill='x')

        result = {'value': None}

        def on_yes():
            result['value'] = True
            dialog.destroy()

        def on_no():
            result['value'] = False
            dialog.destroy()

        def on_ok():
            result['value'] = True
            dialog.destroy()

        # 根据对话框类型显示不同的按钮
        if msg_type == 'question':
            tk.Button(btn_frame, text="是", command=on_yes,
                     bg='#4caf50', fg='white', padx=20).pack(side='right', padx=(5, 0))
            tk.Button(btn_frame, text="否", command=on_no,
                     bg='#e0e0e0', padx=20).pack(side='right')
        else:
            tk.Button(btn_frame, text="确定", command=on_ok,
                     bg=colors.get(msg_type, '#007bff'), fg='white', padx=20).pack(side='right')

        # 居中显示
        dialog.update_idletasks()
        width = dialog.winfo_reqwidth()
        height = dialog.winfo_reqheight()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")

        # 等待对话框关闭
        dialog.wait_window()

        return result['value']


class TableWidget(tk.Frame):
    """表格控件"""

    def __init__(self, parent, columns, **kwargs):
        super().__init__(parent, **kwargs)

        self.columns = columns
        self.data = []

        self.create_widgets()

    def create_widgets(self):
        """创建控件"""
        # 创建Treeview
        self.tree = ttk.Treeview(self, columns=self.columns, show='headings')

        # 设置列标题
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor='center')

        # 滚动条
        v_scrollbar = ttk.Scrollbar(self, orient='vertical', command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(self, orient='horizontal', command=self.tree.xview)

        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # 布局
        self.tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')

        # 配置权重
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def add_row(self, values):
        """添加行"""
        item = self.tree.insert('', 'end', values=values)
        self.data.append(values)
        return item

    def clear(self):
        """清空表格"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.data.clear()

    def get_selected_item(self):
        """获取选中的项目"""
        selection = self.tree.selection()
        if selection:
            return self.tree.item(selection[0], 'values')
        return None

    def set_column_width(self, column, width):
        """设置列宽"""
        self.tree.column(column, width=width)

    def bind_double_click(self, callback):
        """绑定双击事件"""
        self.tree.bind('<Double-1>', callback)

    def bind_right_click(self, callback):
        """绑定右键事件"""
        self.tree.bind('<Button-3>', callback)


class SearchWidget(tk.Frame):
    """搜索控件"""

    def __init__(self, parent, placeholder="搜索...", callback=None, **kwargs):
        super().__init__(parent, **kwargs)

        self.placeholder = placeholder
        self.callback = callback
        self.is_placeholder = True

        self.create_widgets()

    def create_widgets(self):
        """创建控件"""
        # 搜索图标
        self.search_icon = tk.Label(self, text="🔍", font=('Arial', 12))
        self.search_icon.pack(side='left', padx=(5, 0))

        # 搜索框
        self.search_entry = tk.Entry(self, font=('Arial', 10), relief='flat', bd=5)
        self.search_entry.pack(side='left', fill='x', expand=True, padx=5)

        # 清除按钮
        self.clear_button = tk.Button(self, text="×", font=('Arial', 12),
                                     command=self.clear_search, relief='flat', bd=0)
        self.clear_button.pack(side='right', padx=(0, 5))

        # 设置占位符
        self.set_placeholder()

        # 绑定事件
        self.search_entry.bind('<FocusIn>', self.on_focus_in)
        self.search_entry.bind('<FocusOut>', self.on_focus_out)
        self.search_entry.bind('<KeyRelease>', self.on_key_release)

    def set_placeholder(self):
        """设置占位符"""
        self.search_entry.delete(0, tk.END)
        self.search_entry.insert(0, self.placeholder)
        self.search_entry.config(fg='#999')
        self.is_placeholder = True

    def clear_placeholder(self):
        """清除占位符"""
        if self.is_placeholder:
            self.search_entry.delete(0, tk.END)
            self.search_entry.config(fg='black')
            self.is_placeholder = False

    def on_focus_in(self, event):
        """获得焦点事件"""
        self.clear_placeholder()

    def on_focus_out(self, event):
        """失去焦点事件"""
        if not self.search_entry.get():
            self.set_placeholder()

    def on_key_release(self, event):
        """按键释放事件"""
        if not self.is_placeholder and self.callback:
            self.callback(self.search_entry.get())

    def clear_search(self):
        """清除搜索"""
        self.search_entry.delete(0, tk.END)
        if self.callback:
            self.callback("")

    def get_text(self):
        """获取搜索文本"""
        if self.is_placeholder:
            return ""
        return self.search_entry.get()


class NotificationWidget(tk.Toplevel):
    """通知控件"""

    def __init__(self, parent, message, msg_type='info', duration=3000):
        super().__init__(parent)

        self.message = message
        self.msg_type = msg_type
        self.duration = duration

        self.create_widget()
        self.show_notification()

    def create_widget(self):
        """创建控件"""
        # 窗口设置
        self.overrideredirect(True)  # 去除标题栏
        self.attributes('-topmost', True)  # 置顶

        # 颜色配置
        colors = {
            'info': {'bg': '#d1ecf1', 'fg': '#0c5460', 'border': '#bee5eb'},
            'success': {'bg': '#d4edda', 'fg': '#155724', 'border': '#c3e6cb'},
            'warning': {'bg': '#fff3cd', 'fg': '#856404', 'border': '#ffeaa7'},
            'error': {'bg': '#f8d7da', 'fg': '#721c24', 'border': '#f5c6cb'}
        }

        color_config = colors.get(self.msg_type, colors['info'])

        # 主框架
        main_frame = tk.Frame(self, bg=color_config['border'], padx=1, pady=1)
        main_frame.pack(fill='both', expand=True)

        content_frame = tk.Frame(main_frame, bg=color_config['bg'], padx=15, pady=10)
        content_frame.pack(fill='both', expand=True)

        # 图标
        icons = {
            'info': 'ℹ',
            'success': '✓',
            'warning': '⚠',
            'error': '✗'
        }

        icon_label = tk.Label(content_frame, text=icons.get(self.msg_type, 'ℹ'),
                             font=('Arial', 14), bg=color_config['bg'], fg=color_config['fg'])
        icon_label.pack(side='left', padx=(0, 10))

        # 消息文本
        message_label = tk.Label(content_frame, text=self.message, font=('Arial', 10),
                               bg=color_config['bg'], fg=color_config['fg'],
                               wraplength=300)
        message_label.pack(side='left', fill='both', expand=True)

        # 关闭按钮
        close_button = tk.Button(content_frame, text='×', font=('Arial', 12),
                               command=self.close_notification, relief='flat', bd=0,
                               bg=color_config['bg'], fg=color_config['fg'])
        close_button.pack(side='right')

    def show_notification(self):
        """显示通知"""
        # 获取屏幕尺寸
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        # 更新窗口以获取实际尺寸
        self.update_idletasks()
        width = self.winfo_reqwidth()
        height = self.winfo_reqheight()

        # 计算位置（右上角）
        x = screen_width - width - 20
        y = 20

        self.geometry(f"{width}x{height}+{x}+{y}")

        # 淡入效果
        self.attributes('-alpha', 0.0)
        self.fade_in()

        # 自动关闭
        if self.duration > 0:
            self.after(self.duration, self.fade_out)

    def fade_in(self, alpha=0.0):
        """淡入效果"""
        alpha += 0.1
        if alpha <= 1.0:
            self.attributes('-alpha', alpha)
            self.after(50, lambda: self.fade_in(alpha))
        else:
            self.attributes('-alpha', 1.0)

    def fade_out(self, alpha=1.0):
        """淡出效果"""
        alpha -= 0.1
        if alpha >= 0.0:
            self.attributes('-alpha', alpha)
            self.after(50, lambda: self.fade_out(alpha))
        else:
            self.destroy()

    def close_notification(self):
        """关闭通知"""
        self.fade_out()


class TooltipWidget:
    """工具提示控件"""

    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None

        # 绑定事件
        self.widget.bind('<Enter>', self.show_tooltip)
        self.widget.bind('<Leave>', self.hide_tooltip)
        self.widget.bind('<Motion>', self.update_position)

    def show_tooltip(self, event=None):
        """显示工具提示"""
        if self.tooltip_window or not self.text:
            return

        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + 20

        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")

        label = tk.Label(self.tooltip_window, text=self.text,
                        justify='left', background='#ffffe0', relief='solid',
                        borderwidth=1, font=('Arial', 9))
        label.pack()

    def hide_tooltip(self, event=None):
        """隐藏工具提示"""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

    def update_position(self, event=None):
        """更新位置"""
        if self.tooltip_window:
            x = self.widget.winfo_rootx() + event.x + 20
            y = self.widget.winfo_rooty() + event.y + 20
            self.tooltip_window.wm_geometry(f"+{x}+{y}")


class LoadingWidget(tk.Frame):
    """加载控件"""

    def __init__(self, parent, message="加载中...", **kwargs):
        super().__init__(parent, **kwargs)

        self.message = message
        self.is_loading = False

        self.create_widgets()

    def create_widgets(self):
        """创建控件"""
        # 加载动画
        self.loading_label = tk.Label(self, text="●", font=('Arial', 20), fg='#ff6b35')
        self.loading_label.pack(pady=(20, 10))

        # 消息标签
        self.message_label = tk.Label(self, text=self.message, font=('Arial', 10))
        self.message_label.pack(pady=(0, 20))

    def start_loading(self, message=None):
        """开始加载"""
        if message:
            self.message_label.config(text=message)

        self.is_loading = True
        self.animate()

    def stop_loading(self):
        """停止加载"""
        self.is_loading = False

    def animate(self):
        """动画效果"""
        if not self.is_loading:
            return

        current_text = self.loading_label.cget('text')

        if current_text == '●':
            self.loading_label.config(text='●●')
        elif current_text == '●●':
            self.loading_label.config(text='●●●')
        else:
            self.loading_label.config(text='●')

        self.after(500, self.animate)


class CollapsibleFrame(tk.Frame):
    """可折叠框架"""

    def __init__(self, parent, title="", **kwargs):
        super().__init__(parent, **kwargs)

        self.title = title
        self.is_expanded = True

        self.create_widgets()

    def create_widgets(self):
        """创建控件"""
        # 标题框架
        self.title_frame = tk.Frame(self, bg='#f0f0f0', relief='raised', bd=1)
        self.title_frame.pack(fill='x')

        # 展开/折叠按钮
        self.toggle_button = tk.Button(self.title_frame, text='▼', font=('Arial', 8),
                                      command=self.toggle_frame, relief='flat', bd=0,
                                      bg='#f0f0f0', width=3)
        self.toggle_button.pack(side='left', padx=5)

        # 标题标签
        title_label = tk.Label(self.title_frame, text=self.title, font=('Arial', 10, 'bold'),
                              bg='#f0f0f0')
        title_label.pack(side='left', padx=5, pady=5)

        # 内容框架
        self.content_frame = tk.Frame(self)
        self.content_frame.pack(fill='both', expand=True, padx=5, pady=5)

    def toggle_frame(self):
        """切换展开/折叠状态"""
        if self.is_expanded:
            self.content_frame.pack_forget()
            self.toggle_button.config(text='▶')
            self.is_expanded = False
        else:
            self.content_frame.pack(fill='both', expand=True, padx=5, pady=5)
            self.toggle_button.config(text='▼')
            self.is_expanded = True

    def get_content_frame(self):
        """获取内容框架"""
        return self.content_frame


def create_tooltip(widget, text):
    """创建工具提示的便捷函数"""
    return TooltipWidget(widget, text)


def show_notification(parent, message, msg_type='info', duration=3000):
    """显示通知的便捷函数"""
    return NotificationWidget(parent, message, msg_type, duration)


def show_progress_dialog(parent, title="进度", message="处理中..."):
    """显示进度对话框的便捷函数"""
    return ProgressDialog(parent, title, message)