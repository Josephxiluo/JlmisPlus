"""
状态栏组件 - 显示用户信息和余额
"""

import tkinter as tk
from tkinter import ttk
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ui.styles import get_color, get_font


class StatusBar:
    """状态栏组件"""

    def __init__(self, parent, user_info=None):
        self.parent = parent
        self.user_info = user_info or {}
        self.create_widgets()

    def create_widgets(self):
        """创建状态栏组件"""
        # 状态栏主容器
        self.frame = tk.Frame(
            self.parent,
            bg=get_color('primary'),
            height=50
        )
        self.frame.pack(fill='x', side='top')
        self.frame.pack_propagate(False)  # 固定高度

        # 左侧：Logo和标题
        left_frame = tk.Frame(self.frame, bg=get_color('primary'))
        left_frame.pack(side='left', fill='y', padx=20, pady=10)

        # Logo文字
        logo_label = tk.Label(
            left_frame,
            text="Pulse",
            font=('Microsoft YaHei', 14, 'bold'),
            fg='white',
            bg=get_color('primary')
        )
        logo_label.pack(side='left')

        # 副标题
        subtitle_label = tk.Label(
            left_frame,
            text="仅供测试研究，严禁用于违法用途",
            font=get_font('small'),
            fg='white',
            bg=get_color('primary')
        )
        subtitle_label.pack(side='left', padx=(10, 0))

        # 右侧：用户信息和余额
        right_frame = tk.Frame(self.frame, bg=get_color('primary'))
        right_frame.pack(side='right', fill='y', padx=20, pady=10)

        # 余额显示
        self.balance_label = tk.Label(
            right_frame,
            text=f"余额：积分{self.user_info.get('balance', 10000)}",
            font=get_font('button'),
            fg='white',
            bg=get_color('primary_dark'),
            padx=15,
            pady=5,
            relief='solid',
            bd=1
        )
        self.balance_label.pack(side='right')

        # 用户名显示（如果有用户信息）
        if self.user_info.get('username'):
            user_label = tk.Label(
                right_frame,
                text=f"用户：{self.user_info['username']}",
                font=get_font('default'),
                fg='white',
                bg=get_color('primary')
            )
            user_label.pack(side='right', padx=(0, 15))

    def update_balance(self, balance):
        """更新余额显示"""
        self.balance_label.config(text=f"余额：积分{balance}")

    def update_user_info(self, user_info):
        """更新用户信息"""
        self.user_info = user_info
        # 重新创建组件以更新显示
        for widget in self.frame.winfo_children():
            widget.destroy()
        self.create_widgets()

    def get_frame(self):
        """获取状态栏框架"""
        return self.frame


def main():
    """测试状态栏组件"""
    root = tk.Tk()
    root.title("状态栏测试")
    root.geometry("800x100")

    # 模拟用户信息
    user_info = {
        'username': 'test_user',
        'balance': 10000
    }

    # 创建状态栏
    status_bar = StatusBar(root, user_info)

    # 测试更新余额
    def update_balance():
        import random
        new_balance = random.randint(1000, 50000)
        status_bar.update_balance(new_balance)
        root.after(2000, update_balance)  # 2秒后再次更新

    root.after(2000, update_balance)

    root.mainloop()


if __name__ == '__main__':
    main()