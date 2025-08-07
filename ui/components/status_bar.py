"""
现代化状态栏组件 - CustomTkinter版本
"""

import customtkinter as ctk
import sys
import os
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ui.styles import get_color, get_font, get_spacing, create_label


class StatusBar:
    """现代化状态栏组件 - CustomTkinter版本"""

    def __init__(self, parent, user_info=None):
        self.parent = parent
        self.user_info = user_info or {}
        self.balance_label = None
        self.time_label = None
        self.create_widgets()
        self.start_time_update()

    def create_widgets(self):
        """创建现代化状态栏组件"""
        # 状态栏主容器
        self.frame = ctk.CTkFrame(
            self.parent,
            fg_color=get_color('primary'),
            corner_radius=0,
            height=120
        )
        self.frame.pack(fill='x', side='top')
        self.frame.pack_propagate(False)

        # 内容容器
        content_frame = ctk.CTkFrame(
            self.frame,
            fg_color='transparent'
        )
        content_frame.pack(fill='both', expand=True, padx=get_spacing('lg'), pady=get_spacing('md'))

        # 左侧：Logo和标题区域
        self.create_left_section(content_frame)

        # 右侧：用户信息和积分区域
        self.create_right_section(content_frame)

    def create_left_section(self, parent):
        """创建左侧Logo和标题区域"""
        left_frame = ctk.CTkFrame(parent, fg_color='transparent')
        left_frame.pack(side='left', fill='y')

        # Logo容器
        logo_container = ctk.CTkFrame(left_frame, fg_color='transparent')
        logo_container.pack(side='left', pady=get_spacing('sm'))

        # 文字容器
        text_container = ctk.CTkFrame(logo_container, fg_color='transparent')
        text_container.pack(side='left', padx=(get_spacing('sm'), 0))

        # Logo主标题
        logo_label = ctk.CTkLabel(
            text_container,
            text="JlmisPlus 测试系统",
            font=get_font('title'),
            text_color='white'
        )
        logo_label.pack(anchor='w')

        # 副标题
        subtitle_label = ctk.CTkLabel(
            text_container,
            text="本软件仅供技术测试研究，严禁用于违法用途",
            font=get_font('small'),
            text_color='white'
        )
        subtitle_label.pack(anchor='w', pady=(4, 0))

    def create_right_section(self, parent):
        """创建右侧用户信息和积分区域"""
        right_frame = ctk.CTkFrame(parent, fg_color='transparent')
        right_frame.pack(side='right', fill='y', padx=(0, get_spacing('sm')))

        # 信息容器
        info_container = ctk.CTkFrame(right_frame, fg_color='transparent')
        info_container.pack(side='right', pady=get_spacing('sm'))

        # 用户信息行
        if self.user_info.get('username'):
            user_frame = ctk.CTkFrame(info_container, fg_color='transparent')
            user_frame.pack(anchor='e', pady=(get_spacing('xs'), get_spacing('xs')))

            # 在线状态指示器和用户信息
            user_text = f"● {self.user_info.get('real_name', self.user_info['username'])}   {self.get_current_time()}"
            self.user_label = ctk.CTkLabel(
                user_frame,
                text=user_text,
                font=get_font('medium'),
                text_color='white'
            )
            self.user_label.pack(side='left')

        # 积分信息行 - 现代化设计
        balance_frame = ctk.CTkFrame(info_container, fg_color='transparent')
        balance_frame.pack(anchor='e', pady=get_spacing('xs'))

        # 积分徽章容器 - 使用现代化样式
        badge_container = ctk.CTkFrame(
            balance_frame,
            fg_color=('#FFE0B2', '#FF8A50'),  # 渐变效果
            corner_radius=20,
            border_width=2,
            border_color='white',
        )
        badge_container.pack()

        # 积分内容框架
        content_frame = ctk.CTkFrame(badge_container, fg_color='transparent')
        content_frame.pack(padx=get_spacing('md'), pady=get_spacing('xs'))

        # 积分图标和文字
        balance_content_frame = ctk.CTkFrame(content_frame, fg_color='transparent')
        balance_content_frame.pack()

        # 积分图标
        balance_icon = ctk.CTkLabel(
            balance_content_frame,
            text="💎",
            font=('Microsoft YaHei', 16)
        )
        balance_icon.pack(side='left')

        # 积分文字
        current_balance = self.user_info.get('balance', 10000)
        self.balance_label = ctk.CTkLabel(
            balance_content_frame,
            text=f"积分: {current_balance:,}",
            font=('Microsoft YaHei', 14, 'bold'),
            text_color=get_color('primary_dark')
        )
        self.balance_label.pack(side='left', padx=(get_spacing('sm'), 0))

    def get_current_time(self):
        """获取当前时间"""
        return datetime.now().strftime("%H:%M")

    def start_time_update(self):
        """开始时间更新"""
        def update_time():
            if hasattr(self, 'user_label') and self.user_label:
                try:
                    user_text = f"● {self.user_info.get('real_name', self.user_info.get('username', ''))}   {self.get_current_time()}"
                    self.user_label.configure(text=user_text)
                except:
                    pass
            # 每秒更新一次
            self.parent.after(1000, update_time)

        update_time()

    def update_balance(self, balance):
        """更新余额显示"""
        if self.balance_label:
            try:
                self.balance_label.configure(text=f"积分: {balance:,}")
                print(f"积分已更新为: {balance:,}")
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
    """测试现代化状态栏组件"""
    root = ctk.CTk()
    root.title("现代化状态栏测试")
    root.geometry("1000x150")
    root.configure(fg_color=get_color('background'))

    # 模拟用户信息
    user_info = {
        'username': 'test_operator',
        'real_name': '测试操作员',
        'balance': 156800
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