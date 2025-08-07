"""
简化版现代化登录窗口 - CustomTkinter版本
"""
import customtkinter as ctk
from tkinter import messagebox
from typing import Optional, Dict, Any
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from ui.styles import get_color, get_font, get_spacing, create_modern_button, create_entry, create_label
except ImportError:
    # 如果导入失败，使用基础配置
    def get_color(name):
        colors = {'primary': '#FF7043', 'background': '#FAFAFA', 'card_bg': '#FFFFFF', 'text': '#212121'}
        return colors.get(name, '#000000')

    def get_font(name):
        fonts = {'title': ('Microsoft YaHei', 18, 'bold'), 'default': ('Microsoft YaHei', 12), 'small': ('Microsoft YaHei', 10)}
        return fonts.get(name, ('Microsoft YaHei', 12))

    def get_spacing(name):
        return {'sm': 8, 'md': 16, 'lg': 24}.get(name, 8)


class LoginWindow:
    """简化版现代化登录窗口类"""

    def __init__(self):
        """初始化登录窗口"""
        self.root = None
        self.username_var = None
        self.password_var = None
        self.result = None

    def show(self) -> Optional[Dict[str, Any]]:
        """显示现代化登录窗口"""
        self.root = ctk.CTk()
        self.root.title("用户登录 - JlmisPlus")
        self.root.geometry("400x500")
        self.root.resizable(False, False)

        try:
            self.root.configure(fg_color=get_color('background'))
        except:
            self.root.configure(fg_color='#FAFAFA')

        # 居中显示
        self.center_window()

        # 创建现代化界面
        self.create_widgets()

        # 绑定回车键
        self.root.bind('<Return>', lambda e: self.login())

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
        """创建现代化界面组件"""
        # 主容器
        main_container = ctk.CTkFrame(self.root, fg_color='transparent')
        main_container.pack(fill='both', expand=True, padx=30, pady=30)

        # 登录卡片
        try:
            login_card = ctk.CTkFrame(
                main_container,
                fg_color=get_color('card_bg'),
                corner_radius=15,
                border_width=1,
                border_color='#E0E0E0'
            )
        except:
            login_card = ctk.CTkFrame(
                main_container,
                fg_color='white',
                corner_radius=15
            )

        login_card.pack(fill='both', expand=True)

        # 卡片内容
        self.create_card_content(login_card)

    def create_card_content(self, parent):
        """创建卡片内容"""
        content_frame = ctk.CTkFrame(parent, fg_color='transparent')
        content_frame.pack(fill='both', expand=True, padx=25, pady=25)

        # Logo和标题
        self.create_header(content_frame)

        # 表单
        self.create_form(content_frame)

        # 按钮
        self.create_buttons(content_frame)

        # 底部信息
        self.create_footer(content_frame)

    def create_header(self, parent):
        """创建头部Logo和标题"""
        header_frame = ctk.CTkFrame(parent, fg_color='transparent')
        header_frame.pack(fill='x', pady=(0, 25))

        # Logo图标
        try:
            logo_label = ctk.CTkLabel(
                header_frame,
                text="🚀",
                font=get_font('title'),
                text_color=get_color('primary')
            )
        except:
            logo_label = ctk.CTkLabel(
                header_frame,
                text="🚀",
                font=('Microsoft YaHei', 18, 'bold'),
                text_color='#FF7043'
            )
        logo_label.pack()

        # 主标题
        try:
            title_label = ctk.CTkLabel(
                header_frame,
                text="JlmisPlus 测试系统",
                font=get_font('title'),
                text_color=get_color('text')
            )
        except:
            title_label = ctk.CTkLabel(
                header_frame,
                text="JlmisPlus 测试系统",
                font=('Microsoft YaHei', 18, 'bold'),
                text_color='#212121'
            )
        title_label.pack(pady=(10, 5))

        # 副标题
        try:
            subtitle_label = ctk.CTkLabel(
                header_frame,
                text="现代化猫池控制平台",
                font=get_font('small'),
                text_color='#757575'
            )
        except:
            subtitle_label = ctk.CTkLabel(
                header_frame,
                text="现代化猫池控制平台",
                font=('Microsoft YaHei', 10),
                text_color='#757575'
            )
        subtitle_label.pack()

    def create_form(self, parent):
        """创建表单"""
        form_frame = ctk.CTkFrame(parent, fg_color='transparent')
        form_frame.pack(fill='x', pady=(0, 20))

        # 用户名
        username_label = ctk.CTkLabel(
            form_frame,
            text="用户名",
            font=('Microsoft YaHei', 12),
            text_color='#212121'
        )
        username_label.pack(anchor='w', pady=(0, 5))

        self.username_var = ctk.StringVar(value="test_operator")
        self.username_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text="请输入用户名",
            textvariable=self.username_var,
            height=35,
            corner_radius=8,
            border_width=2,
            border_color='#E0E0E0',
            font=('Microsoft YaHei', 12)
        )
        self.username_entry.pack(fill='x', pady=(0, 15))

        # 密码
        password_label = ctk.CTkLabel(
            form_frame,
            text="密码",
            font=('Microsoft YaHei', 12),
            text_color='#212121'
        )
        password_label.pack(anchor='w', pady=(0, 5))

        self.password_var = ctk.StringVar(value="123456")
        self.password_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text="请输入密码",
            textvariable=self.password_var,
            show="*",
            height=35,
            corner_radius=8,
            border_width=2,
            border_color='#E0E0E0',
            font=('Microsoft YaHei', 12)
        )
        self.password_entry.pack(fill='x')

    def create_buttons(self, parent):
        """创建按钮"""
        button_frame = ctk.CTkFrame(parent, fg_color='transparent')
        button_frame.pack(fill='x', pady=(25, 0))

        # 登录按钮
        try:
            login_button = ctk.CTkButton(
                button_frame,
                text="登录",
                command=self.login,
                height=40,
                corner_radius=10,
                fg_color=get_color('primary'),
                hover_color='#FF5722',
                font=('Microsoft YaHei', 12, 'bold')
            )
        except:
            login_button = ctk.CTkButton(
                button_frame,
                text="登录",
                command=self.login,
                height=40,
                corner_radius=10,
                fg_color='#FF7043',
                hover_color='#FF5722',
                font=('Microsoft YaHei', 12, 'bold')
            )
        login_button.pack(fill='x')

        # 记住密码选项
        options_frame = ctk.CTkFrame(button_frame, fg_color='transparent')
        options_frame.pack(fill='x', pady=(15, 0))

        self.remember_var = ctk.BooleanVar(value=True)
        remember_check = ctk.CTkCheckBox(
            options_frame,
            text="记住密码",
            variable=self.remember_var,
            font=('Microsoft YaHei', 10),
            text_color='#757575'
        )
        remember_check.pack(side='left')

    def create_footer(self, parent):
        """创建底部信息"""
        footer_frame = ctk.CTkFrame(parent, fg_color='transparent')
        footer_frame.pack(side='bottom', fill='x', pady=(15, 0))

        # 版本信息
        version_label = ctk.CTkLabel(
            footer_frame,
            text="版本 1.015 - CustomTkinter现代化版",
            font=('Microsoft YaHei', 9),
            text_color='#9E9E9E'
        )
        version_label.pack()

        # 使用提示
        tip_label = ctk.CTkLabel(
            footer_frame,
            text="仅供技术研究使用，严禁用于违法用途",
            font=('Microsoft YaHei', 9),
            text_color='#9E9E9E'
        )
        tip_label.pack(pady=(3, 0))

    def login(self):
        """登录处理"""
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()

        if not username or not password:
            messagebox.showerror("错误", "请输入用户名和密码")
            return

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

    def destroy(self):
        """销毁窗口"""
        if self.root:
            try:
                self.root.destroy()
            except:
                pass


def main():
    """测试现代化登录窗口"""
    login_window = LoginWindow()
    result = login_window.show()

    if result:
        print("登录成功！用户信息：", result)
    else:
        print("登录取消或失败")


if __name__ == '__main__':
    main()