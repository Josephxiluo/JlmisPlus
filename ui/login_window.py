"""
登录窗口 - Tkinter版本
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.auth_service import AuthService
from .styles import get_color, get_font


class LoginWindow:
    """登录窗口类"""

    def __init__(self):
        self.root = tk.Tk()
        self.auth_service = AuthService()
        self.user_info = None
        self.setup_window()
        self.create_widgets()

    def setup_window(self):
        """设置窗口属性"""
        self.root.title("Pulsesports - 用户登录")
        self.root.geometry("400x300")
        self.root.resizable(False, False)

        # 设置窗口居中
        self.center_window()

        # 设置窗口图标和背景色
        self.root.configure(bg=get_color('background'))

        # 设置窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def center_window(self):
        """窗口居中显示"""
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.root.winfo_screenheight() // 2) - (300 // 2)
        self.root.geometry(f"400x300+{x}+{y}")

    def create_widgets(self):
        """创建界面组件"""
        # 主容器
        main_frame = tk.Frame(self.root, bg=get_color('background'))
        main_frame.pack(fill='both', expand=True, padx=40, pady=30)

        # 标题
        title_label = tk.Label(
            main_frame,
            text="Pulse",
            font=('Microsoft YaHei', 18, 'bold'),
            fg=get_color('primary'),
            bg=get_color('background')
        )
        title_label.pack(pady=(0, 10))

        subtitle_label = tk.Label(
            main_frame,
            text="仅供测试研究，严禁用于违法用途",
            font=get_font('small'),
            fg=get_color('text_light'),
            bg=get_color('background')
        )
        subtitle_label.pack(pady=(0, 30))

        # 登录表单容器
        form_frame = tk.Frame(main_frame, bg=get_color('background'))
        form_frame.pack(fill='x', pady=20)

        # 用户名输入
        tk.Label(
            form_frame,
            text="用户名:",
            font=get_font('default'),
            fg=get_color('text'),
            bg=get_color('background')
        ).pack(anchor='w', pady=(0, 5))

        self.username_entry = tk.Entry(
            form_frame,
            font=get_font('default'),
            relief='solid',
            bd=1,
            highlightthickness=1,
            highlightcolor=get_color('primary')
        )
        self.username_entry.pack(fill='x', pady=(0, 15), ipady=5)

        # 密码输入
        tk.Label(
            form_frame,
            text="密码:",
            font=get_font('default'),
            fg=get_color('text'),
            bg=get_color('background')
        ).pack(anchor='w', pady=(0, 5))

        self.password_entry = tk.Entry(
            form_frame,
            font=get_font('default'),
            show="*",
            relief='solid',
            bd=1,
            highlightthickness=1,
            highlightcolor=get_color('primary')
        )
        self.password_entry.pack(fill='x', pady=(0, 25), ipady=5)

        # 按钮容器
        button_frame = tk.Frame(main_frame, bg=get_color('background'))
        button_frame.pack(fill='x')

        # 登录按钮
        self.login_button = tk.Button(
            button_frame,
            text="登录",
            font=get_font('button'),
            bg=get_color('primary'),
            fg='white',
            relief='flat',
            cursor='hand2',
            command=self.login,
            height=2
        )
        self.login_button.pack(fill='x', pady=(0, 10))

        # 取消按钮
        self.cancel_button = tk.Button(
            button_frame,
            text="取消",
            font=get_font('button'),
            bg=get_color('gray'),
            fg='white',
            relief='flat',
            cursor='hand2',
            command=self.on_closing,
            height=2
        )
        self.cancel_button.pack(fill='x')

        # 绑定回车键登录
        self.root.bind('<Return>', lambda e: self.login())

        # 设置焦点到用户名输入框
        self.username_entry.focus()

    def login(self):
        """执行登录"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username:
            messagebox.showerror("错误", "请输入用户名")
            self.username_entry.focus()
            return

        if not password:
            messagebox.showerror("错误", "请输入密码")
            self.password_entry.focus()
            return

        try:
            # 禁用登录按钮防止重复点击
            self.login_button.config(state='disabled', text='登录中...')
            self.root.update()

            # 调用认证服务
            result = self.auth_service.login(username, password)

            if result['success']:
                self.user_info = result['user']
                messagebox.showinfo("成功", "登录成功！")
                self.root.quit()  # 退出主循环，但不销毁窗口
            else:
                messagebox.showerror("登录失败", result['message'])
                self.password_entry.delete(0, 'end')
                self.password_entry.focus()

        except Exception as e:
            messagebox.showerror("错误", f"登录时发生错误：{str(e)}")

        finally:
            # 重新启用登录按钮
            self.login_button.config(state='normal', text='登录')

    def on_closing(self):
        """窗口关闭事件"""
        self.user_info = None
        self.root.quit()

    def show(self):
        """显示登录窗口并返回用户信息"""
        self.root.mainloop()
        return self.user_info

    def destroy(self):
        """销毁窗口"""
        self.root.destroy()


def main():
    """测试登录窗口"""
    login = LoginWindow()
    user_info = login.show()
    login.destroy()

    if user_info:
        print(f"登录成功: {user_info}")
    else:
        print("登录取消")


if __name__ == '__main__':
    main()