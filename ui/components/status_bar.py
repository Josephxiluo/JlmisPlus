"""
修复后的状态栏组件 - 解决积分显示不见的问题
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
    """修复后的状态栏组件 - 积分显示修复版本"""

    def __init__(self, parent, user_info=None):
        self.parent = parent
        self.user_info = user_info or {}
        self.balance_label = None  # 确保balance_label被正确初始化
        self.time_label = None
        self.create_widgets()
        self.start_time_update()

    def create_widgets(self):
        """创建修复后的状态栏组件"""
        # 状态栏主容器 - 固定高度确保显示
        self.frame = tk.Frame(
            self.parent,
            bg=get_color('primary'),
            height=140  # 增加高度确保内容显示
        )
        self.frame.pack(fill='x', side='top')
        self.frame.pack_propagate(False)  # 重要：禁用自动调整大小

        # 内容容器
        content_frame = tk.Frame(self.frame, bg=get_color('primary'))
        content_frame.pack(fill='both', expand=True, padx=get_spacing('lg'), pady=get_spacing('md'))

        # 左侧：Logo和标题区域
        self.create_left_section(content_frame)

        # 右侧：用户信息和积分区域
        self.create_right_section(content_frame)

    def create_left_section(self, parent):
        """创建左侧Logo和标题区域"""
        left_frame = tk.Frame(parent, bg=get_color('primary'))
        left_frame.pack(side='left', fill='y')

        # Logo容器
        logo_container = tk.Frame(left_frame, bg=get_color('primary'))
        logo_container.pack(side='left', pady=get_spacing('sm'))

        # Logo文字和副标题容器
        text_container = tk.Frame(logo_container, bg=get_color('primary'))
        text_container.pack(side='left', padx=(get_spacing('sm'), 0))

        # Logo主标题
        logo_label = tk.Label(
            text_container,
            text="JlmisPlus 测试系统",
            font=get_font('title'),
            fg='white',
            bg=get_color('primary')
        )
        logo_label.pack(anchor='w')

        # 副标题
        subtitle_label = tk.Label(
            text_container,
            text="本软件仅供技术测试研究，严禁用于违法用途",
            font=get_font('subtitle'),
            fg='white',
            bg=get_color('primary')
        )
        subtitle_label.pack(anchor='w', pady=(2, 0))  # 添加间距

    def create_right_section(self, parent):
        """创建右侧用户信息和积分区域 - 修复积分显示问题"""
        right_frame = tk.Frame(parent, bg=get_color('primary'))
        right_frame.pack(side='right', fill='y', padx=(0, get_spacing('sm')))

        # 信息容器 - 垂直布局，确保所有内容都能显示
        info_container = tk.Frame(right_frame, bg=get_color('primary'))
        info_container.pack(side='right', pady=get_spacing('sm'))

        # 用户信息行
        if self.user_info.get('username'):
            user_frame = tk.Frame(info_container, bg=get_color('primary'))
            user_frame.pack(anchor='e', pady=(get_spacing('xs'), get_spacing('xs')))

            # 在线状态指示器
            status_indicator = tk.Label(
                user_frame,
                text="● ",
                font=get_font('medium'),
                fg='#4CAF50',  # 绿色在线状态
                bg=get_color('primary')
            )
            status_indicator.pack(side='left')

            # 用户信息
            user_text = f"{self.user_info.get('real_name', self.user_info['username'])}   {self.get_current_time()}"
            user_label = tk.Label(
                user_frame,
                text=user_text,
                font=get_font('small'),
                fg='white',
                bg=get_color('primary')
            )
            user_label.pack(side='left')

        # 积分信息行 - 重点修复这里
        balance_frame = tk.Frame(info_container, bg=get_color('primary'))
        balance_frame.pack(anchor='e', pady=get_spacing('xs'))

        # 积分徽章容器 - 增大尺寸，使用更明显的颜色
        badge_container = tk.Frame(
            balance_frame,
            bg='#FFE0B2',  # 使用更明显的浅橙色背景
            relief='solid',
            bd=2,  # 增加边框
            highlightbackground='#FF7043',  # 橙色边框
            highlightthickness=1,
            padx=get_spacing('lg'),
            pady=get_spacing('sm')
        )
        badge_container.pack()

        # 积分图标 - 使用更明显的图标
        balance_icon = tk.Label(
            badge_container,
            text="💎",  # 更醒目的钻石图标
            font=('Microsoft YaHei', 14),  # 增大图标
            fg=get_color('warning'),
            bg='#FFE0B2'
        )
        balance_icon.pack(side='left')

        # 积分文字 - 使用更醒目的样式
        current_balance = self.user_info.get('balance', 10000)
        self.balance_label = tk.Label(
            badge_container,
            text=f"积分: {current_balance:,}",
            font=('Microsoft YaHei', 13, 'bold'),  # 更大更粗的字体
            fg='#D84315',  # 深橙红色，更醒目
            bg='#FFE0B2'
        )
        self.balance_label.pack(side='left', padx=(get_spacing('sm'), 0))

    def get_current_time(self):
        """获取当前时间"""
        return datetime.now().strftime("%H:%M")

    def start_time_update(self):
        """开始时间更新"""
        def update_time():
            if hasattr(self, 'time_label') and self.time_label:
                try:
                    self.time_label.config(text=self.get_current_time())
                except:
                    pass
            # 每秒更新一次
            self.parent.after(1000, update_time)

        update_time()

    def update_balance(self, balance):
        """更新余额显示 - 确保正确更新"""
        if self.balance_label:  # 确保标签存在
            try:
                self.balance_label.config(text=f"积分: {balance:,}")
                print(f"积分已更新为: {balance:,}")  # 调试信息
            except Exception as e:
                print(f"更新积分失败: {e}")
        else:
            print("balance_label 不存在，无法更新积分")

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
    """测试修复后的状态栏组件"""
    root = tk.Tk()
    root.title("修复后状态栏测试")
    root.geometry("1000x120")
    root.configure(bg=get_color('background'))

    # 模拟用户信息
    user_info = {
        'username': 'test_operator',
        'real_name': '测试操作员',
        'balance': 156800  # 大数字测试
    }

    # 创建状态栏
    status_bar = StatusBar(root, user_info)

    # 测试更新余额功能
    def test_balance_update():
        import random
        new_balance = random.randint(50000, 500000)
        status_bar.update_balance(new_balance)
        print(f"测试更新积分为: {new_balance:,}")
        root.after(3000, test_balance_update)

    root.after(2000, test_balance_update)

    root.mainloop()


if __name__ == '__main__':
    main()