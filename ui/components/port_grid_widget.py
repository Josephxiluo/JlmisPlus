"""
现代化端口网格组件 - CustomTkinter版本
"""

import customtkinter as ctk
from tkinter import messagebox
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ui.styles import get_color, get_font, get_spacing, create_modern_button, create_card_frame, create_scrollable_frame, create_label, create_checkbox

try:
    from services.port_service import PortService
except ImportError:
    # 模拟端口服务
    class PortService:
        def get_ports(self):
            mock_ports = [
                {
                    'id': 101,
                    'name': 'COM101',
                    'carrier': '中国联通',
                    'status': 'idle',
                    'limit': 60,
                    'success_count': 45,
                    'failed_count': 3
                },
                {
                    'id': 102,
                    'name': 'COM102',
                    'carrier': '中国电信',
                    'status': 'working',
                    'limit': 60,
                    'success_count': 38,
                    'failed_count': 2
                },
                {
                    'id': 103,
                    'name': 'COM103',
                    'carrier': '中国移动',
                    'status': 'busy',
                    'limit': 60,
                    'success_count': 55,
                    'failed_count': 1
                },
                {
                    'id': 104,
                    'name': 'COM104',
                    'carrier': '中国联通',
                    'status': 'error',
                    'limit': 60,
                    'success_count': 12,
                    'failed_count': 8
                },
                {
                    'id': 105,
                    'name': 'COM105',
                    'carrier': '中国电信',
                    'status': 'offline',
                    'limit': 60,
                    'success_count': 0,
                    'failed_count': 0
                },
                {
                    'id': 106,
                    'name': 'COM106',
                    'carrier': '中国移动',
                    'status': 'idle',
                    'limit': 60,
                    'success_count': 28,
                    'failed_count': 2
                }
            ]
            return {'success': True, 'ports': mock_ports}

        def start_ports(self, port_ids):
            return {'success': True, 'count': len(port_ids)}

        def stop_ports(self, port_ids):
            return {'success': True, 'count': len(port_ids)}

        def clear_all_records(self):
            return {'success': True}

        def clear_ports_records(self, port_ids):
            return {'success': True, 'count': len(port_ids)}


class PortGridWidget:
    """现代化端口网格组件 - CustomTkinter版本"""

    def __init__(self, parent, user_info, on_port_select=None):
        self.parent = parent
        self.user_info = user_info
        self.on_port_select = on_port_select
        self.port_service = PortService()
        self.selected_ports = set()
        self.port_cards = {}
        self.ports_data = []
        self.card_width = 280
        self.card_height = 180
        self.create_widgets()
        self.load_ports()

    def create_widgets(self):
        """创建现代化端口网格组件"""
        # 创建卡片容器
        self.card_container, self.content_frame = create_card_frame(self.parent, "串口管理")

        # 创建头部控制区域
        self.create_header()

        # 创建端口网格区域
        self.create_port_grid()

    def create_header(self):
        """创建现代化头部控制区域"""
        header_frame = ctk.CTkFrame(self.content_frame, fg_color='transparent')
        header_frame.pack(fill='x', padx=get_spacing('sm'), pady=(get_spacing('sm'), 0))

        # 控制按钮容器
        button_container = ctk.CTkFrame(header_frame, fg_color='transparent')
        button_container.pack(fill='x')

        # 第一行按钮
        button_row1 = ctk.CTkFrame(button_container, fg_color='transparent')
        button_row1.pack(fill='x', pady=(0, get_spacing('xs')))

        # 选择控制按钮
        self.select_all_button = create_modern_button(
            button_row1,
            text="☑ 全选",
            style="secondary",
            command=self.select_all,
            width=80
        )
        self.select_all_button.pack(side='left', padx=(0, get_spacing('xs')))

        self.deselect_all_button = create_modern_button(
            button_row1,
            text="☐ 取消全选",
            style="secondary",
            command=self.deselect_all,
            width=100
        )
        self.deselect_all_button.pack(side='left', padx=(0, get_spacing('xs')))

        self.invert_selection_button = create_modern_button(
            button_row1,
            text="↕ 反选",
            style="secondary",
            command=self.invert_selection,
            width=80
        )
        self.invert_selection_button.pack(side='left', padx=(0, get_spacing('xs')))

        self.config_button = create_modern_button(
            button_row1,
            text="⚙ 选项",
            style="secondary",
            command=self.show_config,
            width=80
        )
        self.config_button.pack(side='left')

        # 第二行按钮
        button_row2 = ctk.CTkFrame(button_container, fg_color='transparent')
        button_row2.pack(fill='x')

        self.start_ports_button = create_modern_button(
            button_row2,
            text="▶ 启动端口",
            style="success",
            command=self.start_selected_ports,
            width=90
        )
        self.start_ports_button.pack(side='left', padx=(0, get_spacing('xs')))

        self.stop_ports_button = create_modern_button(
            button_row2,
            text="⏹ 停止端口",
            style="gray",
            command=self.stop_selected_ports,
            width=90
        )
        self.stop_ports_button.pack(side='left', padx=(0, get_spacing('xs')))

        self.clear_all_button = create_modern_button(
            button_row2,
            text="🧹 清除全部记录",
            style="gray",
            command=self.clear_all_records,
            width=120
        )
        self.clear_all_button.pack(side='left', padx=(0, get_spacing('xs')))

        self.clear_current_button = create_modern_button(
            button_row2,
            text="🗑 清除当前记录",
            style="gray",
            command=self.clear_current_records,
            width=120
        )
        self.clear_current_button.pack(side='left')

    def create_port_grid(self):
        """创建现代化端口网格区域"""
        # 创建可滚动框架
        self.scrollable_frame = create_scrollable_frame(
            self.content_frame,
            height=500
        )
        self.scrollable_frame.pack(fill='both', expand=True, padx=get_spacing('sm'), pady=get_spacing('sm'))

        # 创建网格容器
        self.grid_container = ctk.CTkFrame(self.scrollable_frame, fg_color='transparent')
        self.grid_container.pack(fill='both', expand=True)

    def load_ports(self):
        """加载端口数据"""
        try:
            result = self.port_service.get_ports()
            if result['success']:
                self.ports_data = result['ports']
                self.update_port_grid()
            else:
                messagebox.showerror("错误", f"加载端口数据失败：{result['message']}")
        except Exception as e:
            messagebox.showerror("错误", f"加载端口数据失败：{str(e)}")

    def update_port_grid(self):
        """更新端口网格显示 - 自适应网格布局"""
        # 清空现有组件
        for widget in self.grid_container.winfo_children():
            widget.destroy()
        self.port_cards.clear()

        if not self.ports_data:
            return

        # 计算列数（根据容器宽度自动调整）
        cols = 2  # 默认3列，可以根据实际情况调整

        # 创建端口网格
        for i, port in enumerate(self.ports_data):
            row = i // cols
            col = i % cols
            self.create_port_card(port, row, col)

    def create_port_card(self, port, row, col):
        """创建单个端口卡片 - 现代化设计"""
        port_id = port.get('id')

        # 端口卡片容器 - 现代化样式
        port_frame = ctk.CTkFrame(
            self.grid_container,
            fg_color=get_color('white'),
            corner_radius=8,
            border_width=2,
            border_color=get_color('border_light'),
            width=self.card_width,
            height=self.card_height
        )
        port_frame.grid(
            row=row,
            column=col,
            padx=get_spacing('sm'),
            pady=get_spacing('sm'),
            sticky='nsew'
        )

        # 配置网格权重
        self.grid_container.grid_columnconfigure(col, weight=1)
        self.grid_container.grid_rowconfigure(row, weight=0)

        # 内容容器
        content_container = ctk.CTkFrame(port_frame, fg_color='transparent')
        content_container.pack(fill='both', expand=True, padx=get_spacing('md'), pady=get_spacing('md'))

        # 头部：选择框和端口信息
        header_frame = ctk.CTkFrame(content_container, fg_color='transparent')
        header_frame.pack(fill='x', pady=(0, get_spacing('sm')))

        # 端口选择变量和复选框 - 小尺寸版本
        port_var = ctk.BooleanVar()
        port_check = ctk.CTkCheckBox(
            header_frame,
            text="",
            variable=port_var,
            command=lambda: self.on_port_selection_change(port_id, port_var.get()),
            width=18,  # 整体宽度16px（比默认小）
            height=18,  # 整体高度16px（比默认小）
            checkbox_width=16,  # 复选框本体12px
            checkbox_height=16,  # 复选框本体12px
            corner_radius=2,  # 小圆角
            border_width=1,  # 细边框
            fg_color=get_color('primary'),
            hover_color=get_color('primary_hover'),
            checkmark_color='white',
            text_color=get_color('text')
        )
        port_check.pack(side='left', padx=(0, 6))  # 右侧留6px间距

        # 端口名称
        port_name = port.get('name', f"COM{port_id}")
        port_label = create_label(
            header_frame,
            text=port_name,
            style="title"
        )
        port_label.pack(side='left', padx=(get_spacing('xs'), 0))

        # 运营商信息（右侧）
        carrier_info = ctk.CTkFrame(header_frame, fg_color='transparent')
        carrier_info.pack(side='right')

        # 运营商图标和名称
        carrier_icon = self.get_carrier_icon(port.get('carrier', '中国联通'))
        carrier_color = self.get_carrier_color(port.get('carrier', '中国联通'))

        carrier_frame = ctk.CTkFrame(carrier_info, fg_color='transparent')
        carrier_frame.pack()

        carrier_icon_label = create_label(
            carrier_frame,
            text=carrier_icon,
            style="default",
            height=get_spacing('sm')
        )
        carrier_icon_label.configure(text_color=carrier_color)
        carrier_icon_label.pack(side='left')

        carrier_label = create_label(
            carrier_frame,
            text=port.get('carrier', '中国联通'),
            style="medium"
        )
        carrier_label.pack(side='left', padx=(get_spacing('xs'), 0))

        # 状态指示器
        status_frame = ctk.CTkFrame(content_container, fg_color='transparent')
        status_frame.pack(fill='x', pady=(0, get_spacing('sm')))

        status = port.get('status', 'idle')
        status_color = self.get_status_color(status)
        status_text = self.get_status_text(status)

        # 状态点和文字
        status_indicator = create_label(
            status_frame,
            text=f"● {status_text}",
            style="medium"
        )
        status_indicator.configure(text_color=status_color)
        status_indicator.pack(side='left')

        # 统计信息区域
        stats_frame = ctk.CTkFrame(content_container, fg_color='transparent')
        stats_frame.pack(fill='x', pady=(0, get_spacing('sm')))

        # 上限信息（左侧）
        limit_info = ctk.CTkFrame(stats_frame, fg_color='transparent')
        limit_info.pack(side='left', fill='x', expand=True)

        limit_label = create_label(
            limit_info,
            text=f"📊 上限：{port.get('limit', 60)}",
            style="medium"
        )
        limit_label.pack(anchor='w')

        # 成功数信息（右侧）
        success_info = ctk.CTkFrame(stats_frame, fg_color='transparent')
        success_info.pack(side='right')

        self.success_label = create_label(
            success_info,
            text=f"✓ {port.get('success_count', 0)}",
            style="medium"
        )
        self.success_label.configure(text_color=get_color('success'))
        self.success_label.pack()

        # 进度条区域（如果有使用情况）
        if port.get('success_count', 0) > 0:
            progress_frame = ctk.CTkFrame(content_container, fg_color='transparent')
            progress_frame.pack(fill='x', pady=(0, get_spacing('sm')))

            # 计算使用率
            usage_rate = min(port.get('success_count', 0) / port.get('limit', 60), 1.0)
            progress_color = self.get_usage_color(usage_rate)

            # 现代化进度条
            progress_bar = ctk.CTkProgressBar(
                progress_frame,
                height=6,
                corner_radius=3,
                progress_color=progress_color,
                fg_color=get_color('gray_light')
            )
            progress_bar.pack(fill='x')
            progress_bar.set(usage_rate)

        # 存储端口卡片信息
        self.port_cards[port_id] = {
            'frame': port_frame,
            'var': port_var,
            'port': port,
            'success_label': self.success_label,
            'content_container': content_container,
            'checkbox': port_check
        }

        # 绑定点击事件
        def bind_click_events(widget):
            widget.bind("<Button-1>", lambda e: self.toggle_port_selection(port_id))

        # 为相关组件绑定点击事件
        bind_click_events(port_frame)
        bind_click_events(content_container)
        bind_click_events(port_label)
        bind_click_events(carrier_label)
        bind_click_events(status_indicator)
        bind_click_events(limit_label)

    def get_carrier_icon(self, carrier):
        """获取运营商图标"""
        icons = {
            '中国联通': '🔵',
            '中国电信': '🔴',
            '中国移动': '🟢',
            '中国广电': '🟡'
        }
        return icons.get(carrier, '📱')

    def get_carrier_color(self, carrier):
        """获取运营商颜色"""
        colors = {
            '中国联通': '#1E88E5',
            '中国电信': '#E53935',
            '中国移动': '#43A047',
            '中国广电': '#FB8C00'
        }
        return colors.get(carrier, get_color('primary'))

    def get_status_color(self, status):
        """获取状态颜色"""
        colors = {
            'idle': get_color('gray'),
            'working': get_color('primary'),
            'busy': get_color('warning'),
            'error': get_color('danger'),
            'offline': get_color('text_hint')
        }
        return colors.get(status, get_color('gray'))

    def get_status_text(self, status):
        """获取状态文字"""
        texts = {
            'idle': '空闲',
            'working': '工作中',
            'busy': '繁忙',
            'error': '错误',
            'offline': '离线'
        }
        return texts.get(status, '未知')

    def get_usage_color(self, usage_rate):
        """根据使用率获取颜色"""
        if usage_rate >= 0.9:
            return get_color('danger')
        elif usage_rate >= 0.7:
            return get_color('warning')
        elif usage_rate >= 0.3:
            return get_color('primary')
        else:
            return get_color('success')

    def toggle_port_selection(self, port_id):
        """切换端口选择状态"""
        if port_id in self.port_cards:
            var = self.port_cards[port_id]['var']
            current_state = var.get()
            var.set(not current_state)
            self.on_port_selection_change(port_id, not current_state)

    def on_port_selection_change(self, port_id, selected):
        """端口选择状态改变事件"""
        if port_id in self.port_cards:
            frame = self.port_cards[port_id]['frame']

            if selected:
                # 选中状态 - 高亮边框
                self.selected_ports.add(port_id)
                frame.configure(
                    border_color=get_color('primary'),
                    border_width=3
                )
            else:
                # 未选中状态
                self.selected_ports.discard(port_id)
                frame.configure(
                    border_color=get_color('border_light'),
                    border_width=2
                )

        # 调用回调函数
        if self.on_port_select:
            selected_port_data = [
                self.port_cards[pid]['port']
                for pid in self.selected_ports
                if pid in self.port_cards
            ]
            self.on_port_select(selected_port_data)

    def select_all(self):
        """全选端口"""
        for port_id, port_info in self.port_cards.items():
            port_info['var'].set(True)
            self.on_port_selection_change(port_id, True)

    def deselect_all(self):
        """取消全选"""
        for port_id, port_info in self.port_cards.items():
            port_info['var'].set(False)
            self.on_port_selection_change(port_id, False)

    def invert_selection(self):
        """反选"""
        for port_id, port_info in self.port_cards.items():
            var = port_info['var']
            current_state = var.get()
            var.set(not current_state)
            self.on_port_selection_change(port_id, not current_state)

    def show_config(self):
        """显示配置对话框"""
        try:
            from ui.dialogs.config_dialog import ConfigDialog
            dialog = ConfigDialog(self.parent)
            result = dialog.show()
            if result:
                messagebox.showinfo("成功", "配置已保存")
        except Exception as e:
            messagebox.showerror("错误", f"打开配置对话框失败：{str(e)}")

    def start_selected_ports(self):
        """启动选中的端口"""
        if not self.selected_ports:
            messagebox.showwarning("警告", "请先选择要启动的端口")
            return

        if messagebox.askyesno("确认启动", f"确定要启动选中的 {len(self.selected_ports)} 个端口吗？"):
            try:
                result = self.port_service.start_ports(list(self.selected_ports))
                if result['success']:
                    messagebox.showinfo("成功", f"已启动 {result.get('count', 0)} 个端口")
                    self.refresh_ports()
                else:
                    messagebox.showerror("失败", result['message'])
            except Exception as e:
                messagebox.showerror("错误", f"启动端口失败：{str(e)}")

    def stop_selected_ports(self):
        """停止选中的端口"""
        if not self.selected_ports:
            messagebox.showwarning("警告", "请先选择要停止的端口")
            return

        if messagebox.askyesno("确认停止", f"确定要停止选中的 {len(self.selected_ports)} 个端口吗？"):
            try:
                result = self.port_service.stop_ports(list(self.selected_ports))
                if result['success']:
                    messagebox.showinfo("成功", f"已停止 {result.get('count', 0)} 个端口")
                    self.refresh_ports()
                else:
                    messagebox.showerror("失败", result['message'])
            except Exception as e:
                messagebox.showerror("错误", f"停止端口失败：{str(e)}")

    def clear_all_records(self):
        """清除全部端口记录"""
        if messagebox.askyesno("确认清除", "确定要清除所有端口的发送记录吗？\n此操作不可恢复！"):
            try:
                result = self.port_service.clear_all_records()
                if result['success']:
                    messagebox.showinfo("成功", "已清除所有端口记录")
                    self.refresh_ports()
                else:
                    messagebox.showerror("失败", result['message'])
            except Exception as e:
                messagebox.showerror("错误", f"清除记录失败：{str(e)}")

    def clear_current_records(self):
        """清除当前选中端口的记录"""
        if not self.selected_ports:
            messagebox.showwarning("警告", "请先选择要清除记录的端口")
            return

        if messagebox.askyesno("确认清除", f"确定要清除选中的 {len(self.selected_ports)} 个端口的发送记录吗？\n此操作不可恢复！"):
            try:
                result = self.port_service.clear_ports_records(list(self.selected_ports))
                if result['success']:
                    messagebox.showinfo("成功", f"已清除 {result.get('count', 0)} 个端口的记录")
                    self.refresh_ports()
                else:
                    messagebox.showerror("失败", result['message'])
            except Exception as e:
                messagebox.showerror("错误", f"清除记录失败：{str(e)}")

    def get_selected_ports(self):
        """获取选中的端口列表"""
        return [
            self.port_cards[pid]['port']
            for pid in self.selected_ports
            if pid in self.port_cards
        ]

    def update_port_status(self, port_id, status_data):
        """更新端口状态显示"""
        if port_id in self.port_cards:
            success_label = self.port_cards[port_id]['success_label']
            success_count = status_data.get('success_count', 0)
            success_label.configure(text=f"✓ {success_count}")

    def refresh_ports(self):
        """刷新端口数据"""
        self.load_ports()

    def get_frame(self):
        """获取组件框架"""
        return self.card_container


def main():
    """测试现代化端口网格组件"""
    root = ctk.CTk()
    root.title("现代化端口网格测试")
    root.geometry("1000x800")
    root.configure(fg_color=get_color('background'))

    # 模拟用户信息
    user_info = {
        'id': 1,
        'username': 'test_user'
    }

    def on_port_select(ports):
        print(f"选中端口: {[p.get('name') for p in ports]}")

    # 创建端口网格组件
    port_grid = PortGridWidget(root, user_info, on_port_select)
    port_grid.get_frame().pack(fill='both', expand=True, padx=20, pady=20)

    root.mainloop()


if __name__ == '__main__':
    main()