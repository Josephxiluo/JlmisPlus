"""
优化后的端口网格组件 - 现代化卡片设计
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ui.styles import get_color, get_font, get_spacing, create_modern_button, create_card_frame, create_status_badge
from services.port_service import PortService


class PortGridWidget:
    """优化后的端口网格组件"""

    def __init__(self, parent, user_info, on_port_select=None):
        self.parent = parent
        self.user_info = user_info
        self.on_port_select = on_port_select
        self.port_service = PortService()
        self.selected_ports = set()
        self.port_cards = {}
        self.ports_data = []
        self.create_widgets()
        self.load_ports()

    def create_widgets(self):
        """创建优化后的端口网格组件"""
        # 创建卡片容器
        self.card_container, self.content_frame = create_card_frame(self.parent, "串口管理")

        # 创建头部控制区域
        self.create_header()

        # 创建端口网格区域
        self.create_port_grid()

    def create_header(self):
        """创建优化后的头部控制区域"""
        header_frame = tk.Frame(self.content_frame, bg=get_color('card_bg'))
        header_frame.pack(fill='x', padx=get_spacing('sm'), pady=(get_spacing('sm'), 0))

        # 控制按钮容器
        button_container = tk.Frame(header_frame, bg=get_color('card_bg'))
        button_container.pack(fill='x')

        # 第一行按钮
        button_row1 = tk.Frame(button_container, bg=get_color('card_bg'))
        button_row1.pack(fill='x', pady=(0, get_spacing('xs')))

        # 选择控制按钮
        self.select_all_button = create_modern_button(
            button_row1,
            text="☑ 全选",
            style="secondary",
            command=self.select_all,
            width=6
        )
        self.select_all_button.pack(side='left', padx=(0, get_spacing('xs')))

        self.deselect_all_button = create_modern_button(
            button_row1,
            text="☐ 取消全选",
            style="secondary",
            command=self.deselect_all,
            width=8
        )
        self.deselect_all_button.pack(side='left', padx=(0, get_spacing('xs')))

        self.invert_selection_button = create_modern_button(
            button_row1,
            text="↕ 反选",
            style="secondary",
            command=self.invert_selection,
            width=6
        )
        self.invert_selection_button.pack(side='left', padx=(0, get_spacing('xs')))

        self.config_button = create_modern_button(
            button_row1,
            text="⚙ 选项",
            style="secondary",
            command=self.show_config,
            width=6
        )
        self.config_button.pack(side='left')

        # 第二行按钮
        button_row2 = tk.Frame(button_container, bg=get_color('card_bg'))
        button_row2.pack(fill='x')

        self.start_ports_button = create_modern_button(
            button_row2,
            text="▶ 启动端口",
            style="success",
            command=self.start_selected_ports,
            width=8
        )
        self.start_ports_button.pack(side='left', padx=(0, get_spacing('xs')))

        self.stop_ports_button = create_modern_button(
            button_row2,
            text="⏹ 停止端口",
            style="danger",
            command=self.stop_selected_ports,
            width=8
        )
        self.stop_ports_button.pack(side='left', padx=(0, get_spacing('xs')))

        self.clear_all_button = create_modern_button(
            button_row2,
            text="🧹 清除全部记录",
            style="warning",
            command=self.clear_all_records,
            width=12
        )
        self.clear_all_button.pack(side='left', padx=(0, get_spacing('xs')))

        self.clear_current_button = create_modern_button(
            button_row2,
            text="🗑 清除当前记录",
            style="warning",
            command=self.clear_current_records,
            width=12
        )
        self.clear_current_button.pack(side='left')

    def create_port_grid(self):
        """创建优化后的端口网格区域"""
        # 网格容器
        grid_frame = tk.Frame(self.content_frame, bg=get_color('card_bg'))
        grid_frame.pack(fill='both', expand=True, padx=get_spacing('sm'), pady=get_spacing('sm'))

        # 创建滚动框架
        self.canvas = tk.Canvas(
            grid_frame,
            bg=get_color('card_bg'),
            highlightthickness=0
        )

        self.scrollbar = ttk.Scrollbar(
            grid_frame,
            orient="vertical",
            command=self.canvas.yview
        )

        self.scrollable_frame = tk.Frame(self.canvas, bg=get_color('card_bg'))

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # 布局滚动组件
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # 绑定鼠标滚轮事件
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        """处理鼠标滚轮事件"""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

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
        """更新端口网格显示"""
        # 清空现有组件
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.port_cards.clear()

        # 创建端口网格 (2列布局)
        cols = 2
        for i, port in enumerate(self.ports_data):
            row = i // cols
            col = i % cols
            self.create_port_card(port, row, col)

        # 配置列权重
        for col in range(cols):
            self.scrollable_frame.grid_columnconfigure(col, weight=1)

    def create_port_card(self, port, row, col):
        """创建单个端口卡片"""
        port_id = port.get('id')

        # 端口卡片容器
        port_frame = tk.Frame(
            self.scrollable_frame,
            bg=get_color('white'),
            relief='solid',
            bd=1,
            highlightbackground=get_color('border_light'),
            highlightthickness=1
        )
        port_frame.grid(row=row, column=col, padx=get_spacing('xs'), pady=get_spacing('xs'), sticky='ew')

        # 内容容器
        content_container = tk.Frame(port_frame, bg=get_color('white'))
        content_container.pack(fill='both', expand=True, padx=get_spacing('md'), pady=get_spacing('md'))

        # 头部：选择框和端口信息
        header_frame = tk.Frame(content_container, bg=get_color('white'))
        header_frame.pack(fill='x', pady=(0, get_spacing('sm')))

        # 选择区域
        select_frame = tk.Frame(header_frame, bg=get_color('white'))
        select_frame.pack(side='left')

        # 端口选择变量
        port_var = tk.BooleanVar()
        port_var.trace('w', lambda *args, p_id=port_id: self.on_port_selection_change(p_id))

        # 自定义选择框样式
        port_check = tk.Checkbutton(
            select_frame,
            variable=port_var,
            bg=get_color('white'),
            activebackground=get_color('white'),
            font=get_font('default'),
            cursor='hand2'
        )
        port_check.pack(side='left')

        # 端口名称
        port_name = port.get('name', f"COM{port_id}")
        port_label = tk.Label(
            select_frame,
            text=port_name,
            font=get_font('subtitle'),
            fg=get_color('text'),
            bg=get_color('white'),
            cursor='hand2'
        )
        port_label.pack(side='left', padx=(get_spacing('xs'), 0))

        # 运营商信息
        carrier_info = tk.Frame(header_frame, bg=get_color('white'))
        carrier_info.pack(side='right')

        # 运营商图标
        carrier_icon = self.get_carrier_icon(port.get('carrier', '中国联通'))
        carrier_icon_label = tk.Label(
            carrier_info,
            text=carrier_icon,
            font=('Microsoft YaHei', 14),
            fg=self.get_carrier_color(port.get('carrier', '中国联通')),
            bg=get_color('white')
        )
        carrier_icon_label.pack(side='left')

        # 运营商名称
        carrier_label = tk.Label(
            carrier_info,
            text=port.get('carrier', '中国联通'),
            font=get_font('small'),
            fg=get_color('text_light'),
            bg=get_color('white')
        )
        carrier_label.pack(side='left', padx=(get_spacing('xs'), 0))

        # 状态指示器
        status_frame = tk.Frame(content_container, bg=get_color('white'))
        status_frame.pack(fill='x', pady=(0, get_spacing('sm')))

        # 状态点
        status = port.get('status', 'idle')
        status_dot = tk.Label(
            status_frame,
            text="●",
            font=('Microsoft YaHei', 12),
            fg=self.get_status_color(status),
            bg=get_color('white')
        )
        status_dot.pack(side='left')

        # 状态文字
        status_text = self.get_status_text(status)
        status_label = tk.Label(
            status_frame,
            text=status_text,
            font=get_font('small'),
            fg=get_color('text_light'),
            bg=get_color('white')
        )
        status_label.pack(side='left', padx=(get_spacing('xs'), 0))

        # 统计信息区域
        stats_frame = tk.Frame(content_container, bg=get_color('white'))
        stats_frame.pack(fill='x', pady=(0, get_spacing('sm')))

        # 上限信息
        limit_frame = tk.Frame(stats_frame, bg=get_color('white'))
        limit_frame.pack(side='left', fill='x', expand=True)

        limit_label = tk.Label(
            limit_frame,
            text=f"📊 上限：{port.get('limit', 60)}",
            font=get_font('small'),
            fg=get_color('text_light'),
            bg=get_color('white')
        )
        limit_label.pack(anchor='w')

        # 成功数信息
        success_frame = tk.Frame(stats_frame, bg=get_color('white'))
        success_frame.pack(side='right')

        self.success_label = tk.Label(
            success_frame,
            text=f"✓ {port.get('success_count', 0)}",
            font=get_font('button'),
            fg=get_color('success'),
            bg=get_color('white')
        )
        self.success_label.pack()

        # 进度条（如果有使用情况）
        if port.get('success_count', 0) > 0:
            progress_frame = tk.Frame(content_container, bg=get_color('white'))
            progress_frame.pack(fill='x', pady=(0, get_spacing('sm')))

            # 进度条背景
            progress_bg = tk.Frame(
                progress_frame,
                bg=get_color('gray_light'),
                height=4
            )
            progress_bg.pack(fill='x')
            progress_bg.pack_propagate(False)

            # 计算使用率
            usage_rate = min(port.get('success_count', 0) / port.get('limit', 60), 1.0)

            # 进度条填充
            if usage_rate > 0:
                progress_color = self.get_usage_color(usage_rate)
                progress_fill = tk.Frame(
                    progress_bg,
                    bg=progress_color,
                    height=4
                )

                def set_progress():
                    try:
                        total_width = progress_bg.winfo_width()
                        if total_width > 1:
                            fill_width = max(1, int(total_width * usage_rate))
                            progress_fill.place(x=0, y=0, width=fill_width, height=4)
                    except:
                        pass

                progress_bg.after(10, set_progress)

        # 存储端口卡片信息
        self.port_cards[port_id] = {
            'frame': port_frame,
            'var': port_var,
            'port': port,
            'success_label': self.success_label,
            'content_container': content_container
        }

        # 绑定点击事件
        def bind_click_events(widget):
            widget.bind("<Button-1>", lambda e, p_id=port_id: self.toggle_port_selection(p_id))

        # 为所有相关组件绑定点击事件
        bind_click_events(port_frame)
        bind_click_events(content_container)
        bind_click_events(port_label)
        bind_click_events(carrier_label)
        bind_click_events(status_label)
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
            var.set(not var.get())

    def on_port_selection_change(self, port_id):
        """端口选择状态改变事件"""
        if port_id in self.port_cards:
            var = self.port_cards[port_id]['var']
            frame = self.port_cards[port_id]['frame']

            if var.get():
                # 选中状态 - 高亮边框
                self.selected_ports.add(port_id)
                frame.config(
                    highlightbackground=get_color('primary'),
                    highlightthickness=2
                )
                # 更新背景色
                self.update_card_background(port_id, get_color('selected'))
            else:
                # 未选中状态
                self.selected_ports.discard(port_id)
                frame.config(
                    highlightbackground=get_color('border_light'),
                    highlightthickness=1
                )
                # 恢复背景色
                self.update_card_background(port_id, get_color('white'))

        # 调用回调函数
        if self.on_port_select:
            selected_port_data = [
                self.port_cards[pid]['port']
                for pid in self.selected_ports
                if pid in self.port_cards
            ]
            self.on_port_select(selected_port_data)

    def update_card_background(self, port_id, bg_color):
        """更新卡片背景色"""
        if port_id in self.port_cards:
            container = self.port_cards[port_id]['content_container']
            self.update_widget_bg_recursive(container, bg_color)

    def update_widget_bg_recursive(self, widget, bg_color):
        """递归更新组件背景色"""
        try:
            if isinstance(widget, (tk.Frame, tk.Label)):
                widget.config(bg=bg_color)
            elif isinstance(widget, tk.Checkbutton):
                widget.config(bg=bg_color, activebackground=bg_color)

            # 递归更新子组件
            for child in widget.winfo_children():
                self.update_widget_bg_recursive(child, bg_color)
        except:
            pass

    def select_all(self):
        """全选端口"""
        for port_id, port_info in self.port_cards.items():
            port_info['var'].set(True)

    def deselect_all(self):
        """取消全选"""
        for port_id, port_info in self.port_cards.items():
            port_info['var'].set(False)

    def invert_selection(self):
        """反选"""
        for port_id, port_info in self.port_cards.items():
            var = port_info['var']
            var.set(not var.get())

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
            success_label.config(text=f"✓ {success_count}")

    def refresh_ports(self):
        """刷新端口数据"""
        self.load_ports()

    def get_frame(self):
        """获取组件框架"""
        return self.card_container


def main():
    """测试优化后的端口网格组件"""
    root = tk.Tk()
    root.title("优化端口网格测试")
    root.geometry("700x600")
    root.configure(bg=get_color('background'))

    # 模拟用户信息
    user_info = {
        'id': 1,
        'username': 'test_user'
    }

    def on_port_select(ports):
        print(f"选中端口: {[p.get('name') for p in ports]}")

    # 创建端口网格组件
    port_grid = PortGridWidget(root, user_info, on_port_select)
    port_grid.get_frame().pack(fill='both', expand=True, padx=10, pady=10)

    root.mainloop()


if __name__ == '__main__':
    main()