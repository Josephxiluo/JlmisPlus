"""
优化后的状态栏组件 - 现代化设计
"""

import tkinter as tk
from tkinter import ttk
import sys
import os
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ui.styles import get_color, get_font, get_spacing, create_status_badge


class StatusBar:
    """优化后的状态栏组件"""

    def __init__(self, parent, user_info=None):
        self.parent = parent
        self.user_info = user_info or {}
        self.create_widgets()
        self.start_time_update()

    def create_widgets(self):
        """创建优化后的状态栏组件"""
        # 状态栏主容器 - 渐变效果背景
        self.frame = tk.Frame(
            self.parent,
            bg=get_color('primary'),
            height=60  # 增加高度
        )
        self.frame.pack(fill='x', side='top')
        self.frame.pack_propagate(False)

        # 内容容器
        content_frame = tk.Frame(self.frame, bg=get_color('primary'))
        content_frame.pack(fill='both', expand=True, padx=get_spacing('lg'), pady=get_spacing('sm'))

        # 左侧：Logo和标题区域
        self.create_left_section(content_frame)

        # 中间：用户信息区域
        self.create_center_section(content_frame)

        # 右侧：余额和时间区域
        self.create_right_section(content_frame)

    def create_left_section(self, parent):
        """创建左侧Logo和标题区域"""
        left_frame = tk.Frame(parent, bg=get_color('primary'))
        left_frame.pack(side='left', fill='y')

        # Logo容器
        logo_container = tk.Frame(left_frame, bg=get_color('primary'))
        logo_container.pack(side='left', pady=get_spacing('sm'))

        # Logo图标（使用文字代替）
        logo_icon = tk.Label(
            logo_container,
            text="📱",
            font=('Microsoft YaHei', 20),
            fg='white',
            bg=get_color('primary')
        )
        logo_icon.pack(side='left')

        # Logo文字和副标题容器
        text_container = tk.Frame(logo_container, bg=get_color('primary'))
        text_container.pack(side='left', padx=(get_spacing('sm'), 0))

        # Logo主标题
        logo_label = tk.Label(
            text_container,
            text="Pulse",
            font=('Microsoft YaHei', 16, 'bold'),
            fg='white',
            bg=get_color('primary')
        )
        logo_label.pack(anchor='w')

        # 副标题
        subtitle_label = tk.Label(
            text_container,
            text="仅供测试研究，严禁用于违法用途",
            font=get_font('small'),
            fg='white',
            bg=get_color('primary')
        )
        subtitle_label.pack(anchor='w')

    def create_center_section(self, parent):
        """创建中间用户信息区域"""
        center_frame = tk.Frame(parent, bg=get_color('primary'))
        center_frame.pack(side='left', expand=True, fill='both', padx=get_spacing('xl'))

        if self.user_info.get('username'):
            # 用户信息容器
            user_container = tk.Frame(center_frame, bg=get_color('primary'))
            user_container.pack(expand=True)

            # 用户头像占位符
            avatar_frame = tk.Frame(
                user_container,
                bg='white',
                width=36,
                height=36,
                relief='solid',
                bd=1
            )
            avatar_frame.pack(side='left', pady=get_spacing('xs'))
            avatar_frame.pack_propagate(False)

            # 头像图标
            avatar_icon = tk.Label(
                avatar_frame,
                text="👤",
                font=('Microsoft YaHei', 16),
                fg=get_color('primary'),
                bg='white'
            )
            avatar_icon.pack(expand=True)

            # 用户信息文字
            user_info_frame = tk.Frame(user_container, bg=get_color('primary'))
            user_info_frame.pack(side='left', padx=(get_spacing('sm'), 0), fill='y')

            # 用户名
            user_label = tk.Label(
                user_info_frame,
                text=f"欢迎，{self.user_info.get('real_name', self.user_info['username'])}",
                font=get_font('button'),
                fg='white',
                bg=get_color('primary')
            )
            user_label.pack(anchor='w')

            # 在线状态
            status_label = tk.Label(
                user_info_frame,
                text="● 在线",
                font=get_font('small'),
                fg='#4CAF50',
                bg=get_color('primary')
            )
            status_label.pack(anchor='w')

    def create_right_section(self, parent):
        """创建右侧余额和时间区域"""
        right_frame = tk.Frame(parent, bg=get_color('primary'))
        right_frame.pack(side='right', fill='y')

        # 信息容器
        info_container = tk.Frame(right_frame, bg=get_color('primary'))
        info_container.pack(side='right', pady=get_spacing('sm'))

        # 时间显示
        time_frame = tk.Frame(info_container, bg=get_color('primary'))
        time_frame.pack(anchor='e', pady=(0, get_spacing('xs')))

        self.time_label = tk.Label(
            time_frame,
            text=self.get_current_time(),
            font=get_font('small'),
            fg='white',
            bg=get_color('primary')
        )
        self.time_label.pack(side='right')

        # 余额显示 - 徽章样式
        balance_frame = tk.Frame(info_container, bg=get_color('primary'))
        balance_frame.pack(anchor='e')

        # 余额徽章容器
        badge_container = tk.Frame(
            balance_frame,
            bg='white',
            relief='flat',
            bd=0,
            padx=get_spacing('md'),
            pady=get_spacing('xs')
        )
        badge_container.pack()

        # 余额图标
        balance_icon = tk.Label(
            badge_container,
            text="💰",
            font=('Microsoft YaHei', 12),
            fg=get_color('warning'),
            bg='white'
        )
        balance_icon.pack(side='left')

        # 余额文字
        self.balance_label = tk.Label(
            badge_container,
            text=f"积分 {self.user_info.get('balance', 10000):,}",
            font=get_font('button'),
            fg=get_color('text'),
            bg='white'
        )
        self.balance_label.pack(side='left', padx=(get_spacing('xs'), 0))

    def get_current_time(self):
        """获取当前时间"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def start_time_update(self):
        """开始时间更新"""
        def update_time():
            if hasattr(self, 'time_label'):
                try:
                    self.time_label.config(text=self.get_current_time())
                except:
                    pass
            # 每秒更新一次
            self.parent.after(1000, update_time)

        update_time()

    def update_balance(self, balance):
        """更新余额显示"""
        self.balance_label.config(text=f"积分 {balance:,}")

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
    """测试优化后的状态栏组件"""
    root = tk.Tk()
    root.title("优化状态栏测试")
    root.geometry("1000x120")
    root.configure(bg=get_color('background'))

    # 模拟用户信息
    user_info = {
        'username': 'test_operator',
        'real_name': '测试操作员',
        'balance': 15680
    }

    # 创建状态栏
    status_bar = StatusBar(root, user_info)

    # 测试更新余额
    def update_balance():
        import random
        new_balance = random.randint(5000, 50000)
        status_bar.update_balance(new_balance)
        root.after(3000, update_balance)

    root.after(3000, update_balance)

    root.mainloop()


if __name__ == '__main__':
    main()