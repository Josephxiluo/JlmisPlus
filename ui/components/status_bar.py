"""
优化后的状态栏组件 - 去除头像，右对齐用户信息和积分
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

        # 右侧：用户信息和积分区域（合并到一起）
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

    def create_right_section(self, parent):
        """创建右侧用户信息和积分区域 - 去除头像，右对齐"""
        right_frame = tk.Frame(parent, bg=get_color('primary'))
        right_frame.pack(side='right', fill='y')

        # 信息容器 - 垂直布局
        info_container = tk.Frame(right_frame, bg=get_color('primary'))
        info_container.pack(side='right', pady=get_spacing('sm'))

        # 用户信息行
        if self.user_info.get('username'):
            user_frame = tk.Frame(info_container, bg=get_color('primary'))
            user_frame.pack(anchor='e', pady=(0, get_spacing('xs')))

            # 在线状态指示器
            status_indicator = tk.Label(
                user_frame,
                text="● ",
                font=('Microsoft YaHei', 10),
                fg='#4CAF50',  # 绿色在线状态
                bg=get_color('primary')
            )
            status_indicator.pack(side='left')

            # 用户信息
            user_text = f"欢迎，{self.user_info.get('real_name', self.user_info['username'])}"
            user_label = tk.Label(
                user_frame,
                text=user_text,
                font=get_font('medium'),  # 使用中等字体，更清晰
                fg='white',
                bg=get_color('primary')
            )
            user_label.pack(side='left')

        # 积分信息行 - 使用更大更清晰的样式
        balance_frame = tk.Frame(info_container, bg=get_color('primary'))
        balance_frame.pack(anchor='e')

        # 积分徽章容器 - 增大尺寸，提高可读性
        badge_container = tk.Frame(
            balance_frame,
            bg='white',
            relief='flat',
            bd=0,
            padx=get_spacing('lg'),  # 增大内边距
            pady=get_spacing('sm')
        )
        badge_container.pack()

        # 积分图标
        balance_icon = tk.Label(
            badge_container,
            text="💰",
            font=('Microsoft YaHei', 14),  # 增大图标
            fg=get_color('warning'),
            bg='white'
        )
        balance_icon.pack(side='left')

        # 积分文字 - 使用更大更醒目的字体
        current_balance = self.user_info.get('balance', 10000)
        self.balance_label = tk.Label(
            badge_container,
            text=f"积分: {current_balance:,}",  # 格式化数字，添加千位分隔符
            font=('Microsoft YaHei', 12, 'bold'),  # 使用更大的粗体字体
            fg=get_color('text'),
            bg='white'
        )
        self.balance_label.pack(side='left', padx=(get_spacing('sm'), 0))

        # 时间信息行 - 小字显示在最下方
        time_frame = tk.Frame(info_container, bg=get_color('primary'))
        time_frame.pack(anchor='e', pady=(get_spacing('xs'), 0))

        self.time_label = tk.Label(
            time_frame,
            text=self.get_current_time(),
            font=get_font('small'),
            fg='white',
            bg=get_color('primary')
        )
        self.time_label.pack(side='right')

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
        """更新余额显示 - 确保格式化显示"""
        if hasattr(self, 'balance_label'):
            self.balance_label.config(text=f"积分: {balance:,}")

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
        'balance': 156800  # 使用更大的数字测试格式化效果
    }

    # 创建状态栏
    status_bar = StatusBar(root, user_info)

    # 测试更新余额
    def update_balance():
        import random
        new_balance = random.randint(50000, 500000)
        status_bar.update_balance(new_balance)
        print(f"更新积分为: {new_balance:,}")
        root.after(3000, update_balance)

    root.after(3000, update_balance)

    # 显示说明
    info_label = tk.Label(
        root,
        text="✅ 优化项目:\n• 去除了头像\n• 用户信息和积分右对齐\n• 积分数字更大更清晰\n• 添加千位分隔符\n• 在线状态指示器",
        font=get_font('default'),
        fg=get_color('text'),
        bg=get_color('background'),
        justify='left'
    )
    info_label.pack(pady=20)

    root.mainloop()


if __name__ == '__main__':
    main()