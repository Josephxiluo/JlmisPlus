"""
登录窗口 - 最小化版本
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Dict, Any

class LoginWindow:
    """登录窗口类"""

    def __init__(self):
        """初始化登录窗口"""
        self.root = None
        self.username_var = None
        self.password_var = None
        self.result = None

    def show(self) -> Optional[Dict[str, Any]]:
        """显示登录窗口"""
        self.root = tk.Tk()
        self.root.title("猫池短信系统 - 用户登录")
        self.root.geometry("400x300")
        self.root.resizable(False, False)

        # 居中显示
        self.center_window()

        # 创建界面
        self.create_widgets()

        # 运行窗口
        self.root.mainloop()

        return self.result

    def center_window(self):
        """窗口居中"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 标题
        title_label = ttk.Label(main_frame, text="猫池短信系统", font=("Microsoft YaHei", 16, "bold"))
        title_label.pack(pady=(0, 20))

        # 用户名
        ttk.Label(main_frame, text="用户名:").pack(anchor=tk.W)
        self.username_var = tk.StringVar(value="test_operator")
        username_entry = ttk.Entry(main_frame, textvariable=self.username_var, width=30)
        username_entry.pack(fill=tk.X, pady=(5, 10))

        # 密码
        ttk.Label(main_frame, text="密码:").pack(anchor=tk.W)
        self.password_var = tk.StringVar(value="123456")
        password_entry = ttk.Entry(main_frame, textvariable=self.password_var, show="*", width=30)
        password_entry.pack(fill=tk.X, pady=(5, 20))

        # 登录按钮
        login_btn = ttk.Button(main_frame, text="登录", command=self.login)
        login_btn.pack(pady=10)

        # 绑定回车键
        self.root.bind('<Return>', lambda e: self.login())

        # 设置焦点
        username_entry.focus()

    def login(self):
        """登录处理"""
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()

        if not username or not password:
            messagebox.showerror("错误", "请输入用户名和密码")
            return

        try:
            # 简单验证
            if username == "test_operator" and password == "123456":
                self.result = {
                    'operators_id': 1,
                    'operators_username': username,
                    'operators_real_name': '测试操作员',
                    'operators_available_credits': 1000,
                    'channel_users_id': 1
                }
                messagebox.showinfo("成功", "登录成功！")
                self.root.quit()
                self.root.destroy()
            else:
                messagebox.showerror("错误", "用户名或密码错误")

        except Exception as e:
            messagebox.showerror("错误", f"登录过程中发生错误: {str(e)}")

    def destroy(self):
        """销毁窗口"""
        if self.root:
            try:
                self.root.destroy()
            except:
                pass
