"""
端口网格组件 - 右侧串口管理区域（完整版）
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ui.styles import get_color, get_font
from services.port_service import PortService


class PortGridWidget:
    """端口网格组件"""

    def __init__(self, parent, user_info, on_port_select=None):
        self.parent = parent
        self.user_info = user_info
        self.on_port_select = on_port_select  # 端口选择回调
        self.port_service = PortService()
        self.selected_ports = set()  # 选中的端口集合
        self.port_frames = {}  # 端口框架字典
        self.ports_data = []
        self.create_widgets()
        self.load_ports()

    def create_widgets(self):
        """创建端口网格组件"""
        # 主容器
        self.frame = tk.Frame(self.parent, bg=get_color('background'))

        # 标题和控制按钮
        self.create_header()

        # 端口网格区域
        self.create_port_grid()

    def create_header(self):
        """创建头部控制区域"""
        header_frame = tk.Frame(self.frame, bg=get_color('background'))
        header_frame.pack(fill='x', padx=10, pady=(10, 5))

        # 标题
        title_label = tk.Label(
            header_frame,
            text="串口管理",
            font=get_font('title'),
            fg=get_color('text'),
            bg=get_color('background')
        )
        title_label.pack(side='left')

        # 控制按钮容器
        button_frame = tk.Frame(header_frame, bg=get_color('background'))
        button_frame.pack(side='right')

        # 第一行按钮
        button_row1 = tk.Frame(button_frame, bg=get_color('background'))
        button_row1.pack(fill='x', pady=(0, 2))

        # 全选按钮
        self.select_all_button = tk.Button(
            button_row1,
            text="全选",
            font=get_font('button'),
            bg=get_color('primary'),
            fg='white',
            relief='flat',
            cursor='hand2',
            command=self.select_all,
            width=6
        )
        self.select_all_button.pack(side='left', padx=(0, 2))

        # 取消全选按钮
        self.deselect_all_button = tk.Button(
            button_row1,
            text="取消全选",
            font=get_font('button'),
            bg=get_color('gray'),
            fg='white',
            relief='flat',
            cursor='hand2',
            command=self.deselect_all,
            width=8
        )
        self.deselect_all_button.pack(side='left', padx=(0, 2))

        # 反选按钮
        self.invert_selection_button = tk.Button(
            button_row1,
            text="反选",
            font=get_font('button'),
            bg=get_color('primary'),
            fg='white',
            relief='flat',
            cursor='hand2',
            command=self.invert_selection,
            width=6
        )
        self.invert_selection_button.pack(side='left', padx=(0, 2))

        # 选项按钮
        self.config_button = tk.Button(
            button_row1,
            text="选项",
            font=get_font('button'),
            bg=get_color('primary'),
            fg='white',
            relief='flat',
            cursor='hand2',
            command=self.show_config,
            width=6
        )
        self.config_button.pack(side='left')

        # 第二行按钮
        button_row2 = tk.Frame(button_frame, bg=get_color('background'))
        button_row2.pack(fill='x')

        # 启动端口按钮
        self.start_ports_button = tk.Button(
            button_row2,
            text="启动端口",
            font=get_font('button'),
            bg=get_color('success'),
            fg='white',
            relief='flat',
            cursor='hand2',
            command=self.start_selected_ports,
            width=8
        )
        self.start_ports_button.pack(side='left', padx=(0, 2))

        # 停止端口按钮
        self.stop_ports_button = tk.Button(
            button_row2,
            text="停止端口",
            font=get_font('button'),
            bg=get_color('danger'),
            fg='white',
            relief='flat',
            cursor='hand2',
            command=self.stop_selected_ports,
            width=8
        )
        self.stop_ports_button.pack(side='left', padx=(0, 2))

        # 清除全部记录按钮
        self.clear_all_button = tk.Button(
            button_row2,
            text="清除全部记录",
            font=get_font('button'),
            bg=get_color('warning'),
            fg='white',
            relief='flat',
            cursor='hand2',
            command=self.clear_all_records,
            width=12
        )
        self.clear_all_button.pack(side='left', padx=(0, 2))

        # 清除当前记录按钮
        self.clear_current_button = tk.Button(
            button_row2,
            text="清除当前记录",
            font=get_font('button'),
            bg=get_color('warning'),
            fg='white',
            relief='flat',
            cursor='hand2',
            command=self.clear_current_records,
            width=12
        )
        self.clear_current_button.pack(side='left')

    def create_port_grid(self):
        """创建端口网格区域"""
        # 网格容器
        grid_frame = tk.Frame(self.frame, bg=get_color('background'))
        grid_frame.pack(fill='both', expand=True, padx=10, pady=5)

        # 创建滚动框架
        self.canvas = tk.Canvas(grid_frame, bg=get_color('background'), highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(grid_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=get_color('background'))

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
            # 获取端口列表
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
        self.port_frames.clear()

        # 创建端口网格 (2列布局)
        cols = 2
        for i, port in enumerate(self.ports_data):
            row = i // cols
            col = i % cols
            self.create_port_frame(port, row, col)

    def create_port_frame(self, port, row, col):
        """创建单个端口框架"""
        port_id = port.get('id')

        # 端口框架
        port_frame = tk.Frame(
            self.scrollable_frame,
            bg=get_color('white'),
            relief='solid',
            bd=1,
            padx=10,
            pady=8
        )
        port_frame.grid(row=row, column=col, padx=5, pady=5, sticky='ew')

        # 配置列权重
        self.scrollable_frame.grid_columnconfigure(col, weight=1)

        # 端口选择变量
        port_var = tk.BooleanVar()
        port_var.trace('w', lambda *args, p_id=port_id: self.on_port_selection_change(p_id))

        # 端口信息行1：端口号和运营商
        info_frame1 = tk.Frame(port_frame, bg=get_color('white'))
        info_frame1.pack(fill='x')

        # 选择复选框和端口号
        check_frame = tk.Frame(info_frame1, bg=get_color('white'))
        check_frame.pack(side='left')

        port_check = tk.Checkbutton(
            check_frame,
            variable=port_var,
            bg=get_color('white'),
            activebackground=get_color('white')
        )
        port_check.pack(side='left')

        port_label = tk.Label(
            check_frame,
            text=port.get('name', f"COM{port_id}"),
            font=get_font('button'),
            fg=get_color('text'),
            bg=get_color('white')
        )
        port_label.pack(side='left', padx=(5, 0))

        # 运营商
        carrier_label = tk.Label(
            info_frame1,
            text=port.get('carrier', '中国联通'),
            font=get_font('default'),
            fg=get_color('text'),
            bg=get_color('white')
        )
        carrier_label.pack(side='right')

        # 端口信息行2：上限和成功数
        info_frame2 = tk.Frame(port_frame, bg=get_color('white'))
        info_frame2.pack(fill='x', pady=(5, 0))

        # 上限
        limit_label = tk.Label(
            info_frame2,
            text=f"上限：{port.get('limit', 60)}",
            font=get_font('small'),
            fg=get_color('text_light'),
            bg=get_color('white')
        )
        limit_label.pack(side='left')

        # 成功数
        success_label = tk.Label(
            info_frame2,
            text=f"成功：{port.get('success_count', 0)}",
            font=get_font('small'),
            fg=get_color('success'),
            bg=get_color('white')
        )
        success_label.pack(side='right')

        # 存储端口框架信息
        self.port_frames[port_id] = {
            'frame': port_frame,
            'var': port_var,
            'port': port,
            'success_label': success_label
        }

        # 绑定点击事件
        port_frame.bind("<Button-1>", lambda e, p_id=port_id: self.toggle_port_selection(p_id))
        port_label.bind("<Button-1>", lambda e, p_id=port_id: self.toggle_port_selection(p_id))

    def toggle_port_selection(self, port_id):
        """切换端口选择状态"""
        if port_id in self.port_frames:
            var = self.port_frames[port_id]['var']
            var.set(not var.get())

    def on_port_selection_change(self, port_id):
        """端口选择状态改变事件"""
        if port_id in self.port_frames:
            var = self.port_frames[port_id]['var']
            frame = self.port_frames[port_id]['frame']

            if var.get():
                # 选中状态
                self.selected_ports.add(port_id)
                frame.configure(bg=get_color('primary_light'), bd=2)
                # 更新子组件背景色
                self.update_frame_bg(frame, get_color('primary_light'))
            else:
                # 未选中状态
                self.selected_ports.discard(port_id)
                frame.configure(bg=get_color('white'), bd=1)
                # 更新子组件背景色
                self.update_frame_bg(frame, get_color('white'))

        # 调用回调函数
        if self.on_port_select:
            selected_port_data = [
                self.port_frames[pid]['port']
                for pid in self.selected_ports
                if pid in self.port_frames
            ]
            self.on_port_select(selected_port_data)

    def update_frame_bg(self, frame, bg_color):
        """递归更新框架及其子组件的背景色"""
        for child in frame.winfo_children():
            if isinstance(child, (tk.Frame, tk.Label)):
                child.configure(bg=bg_color)
                if isinstance(child, tk.Frame):
                    self.update_frame_bg(child, bg_color)
            elif isinstance(child, tk.Checkbutton):
                child.configure(bg=bg_color, activebackground=bg_color)

    def select_all(self):
        """全选端口"""
        for port_id, port_info in self.port_frames.items():
            port_info['var'].set(True)

    def deselect_all(self):
        """取消全选"""
        for port_id, port_info in self.port_frames.items():
            port_info['var'].set(False)

    def invert_selection(self):
        """反选"""
        for port_id, port_info in self.port_frames.items():
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
                # 这里应该调用端口服务启动端口
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
                # 这里应该调用端口服务停止端口
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
                # 这里应该调用端口服务清除所有记录
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
                # 这里应该调用端口服务清除选中端口的记录
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
            self.port_frames[pid]['port']
            for pid in self.selected_ports
            if pid in self.port_frames
        ]

    def update_port_status(self, port_id, status_data):
        """更新端口状态显示"""
        if port_id in self.port_frames:
            success_label = self.port_frames[port_id]['success_label']
            success_count = status_data.get('success_count', 0)
            success_label.config(text=f"成功：{success_count}")

    def refresh_ports(self):
        """刷新端口数据"""
        self.load_ports()

    def get_frame(self):
        """获取组件框架"""
        return self.frame


def main():
    """测试端口网格组件"""
    root = tk.Tk()
    root.title("端口网格测试")
    root.geometry("600x500")
    root.configure(bg='#f5f5f5')

    # 模拟用户信息
    user_info = {
        'id': 1,
        'username': 'test_user'
    }

    def on_port_select(ports):
        print(f"选中端口: {[p.get('name') for p in ports]}")

    # 创建端口网格组件
    port_grid = PortGridWidget(root, user_info, on_port_select)
    port_grid.get_frame().pack(fill='both', expand=True)

    root.mainloop()


if __name__ == '__main__':
    main()