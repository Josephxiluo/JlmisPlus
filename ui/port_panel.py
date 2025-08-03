"""
端口管理面板模块
"""
import tkinter as tk
from tkinter import ttk, messagebox
from ui.config_panel import ConfigDialog
from ui.widgets import create_button



class PortPanel(tk.LabelFrame):
    """端口管理面板"""

    def __init__(self, parent, port_manager, status_callback):
        super().__init__(parent, text="串口管理", font=('Arial', 12, 'bold'),
                         bg='white', padx=10, pady=10)

        self.port_manager = port_manager
        self.status_callback = status_callback

        self.create_widgets()

    def create_widgets(self):
        """创建控件"""
        # 串口控制按钮组1
        btn_frame1 = tk.Frame(self, bg='white')
        btn_frame1.pack(fill='x', pady=(0, 5))

        (create_button(btn_frame1, "全选", self.select_all_ports, variant="primary")
         .pack(side='left', padx=(0, 5)))
        (create_button(btn_frame1, "取消全选", self.deselect_all_ports, variant="secondary")
         .pack(side='left', padx=(0, 5)))
        (create_button(btn_frame1, "反选", self.reverse_select_ports, variant="secondary")
         .pack(side='left', padx=(0, 5)))
        (create_button(btn_frame1, "选项", self.show_settings_dialog, variant="secondary")
         .pack(side='left'))

        # tk.Button(btn_frame1, text="全选", command=self.select_all_ports,
        #           bg='#ff6b35', fg='white', padx=10).pack(side='left', padx=(0, 5))
        # tk.Button(btn_frame1, text="取消全选", command=self.deselect_all_ports,
        #           bg='#e0e0e0', padx=10).pack(side='left', padx=(0, 5))
        # tk.Button(btn_frame1, text="反选", command=self.reverse_select_ports,
        #           bg='#e0e0e0', padx=10).pack(side='left', padx=(0, 5))
        # tk.Button(btn_frame1, text="选项", command=self.show_settings_dialog,
        #           bg='#e0e0e0', padx=10).pack(side='left')

        # 串口控制按钮组2
        btn_frame2 = tk.Frame(self, bg='white')
        btn_frame2.pack(fill='x', pady=(0, 10))

        (create_button(btn_frame2, "启动端口", self.start_selected_ports, variant="secondary")
         .pack(side='left', padx=(0, 5)))
        (create_button(btn_frame2, "停止端口", self.stop_selected_ports, variant="secondary")
         .pack(side='left', padx=(0, 5)))
        (create_button(btn_frame2, "清除全部记数", self.clear_all_records, variant="secondary")
         .pack(side='left', padx=(0, 5)))
        (create_button(btn_frame2, "清除当前记数", self.clear_current_records, variant="primary")
         .pack(side='left'))

        # tk.Button(btn_frame2, text="启动端口", command=self.start_selected_ports,
        #           bg='#28a745', fg='white', padx=10).pack(side='left', padx=(0, 5))
        # tk.Button(btn_frame2, text="停止端口", command=self.stop_selected_ports,
        #           bg='#dc3545', fg='white', padx=10).pack(side='left', padx=(0, 5))
        # tk.Button(btn_frame2, text="清除全部记数", command=self.clear_all_records,
        #           bg='#ff6b35', fg='white', padx=10).pack(side='left', padx=(0, 5))
        # tk.Button(btn_frame2, text="清除当前记数", command=self.clear_current_records,
        #           bg='#e0e0e0', padx=10).pack(side='left')

        # 串口列表框架
        port_list_frame = tk.Frame(self, bg='white')
        port_list_frame.pack(fill='both', expand=True)

        # 创建滚动区域
        self.canvas = tk.Canvas(port_list_frame, bg='white')
        scrollbar = ttk.Scrollbar(port_list_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg='white')

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 绑定鼠标滚轮事件
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        """鼠标滚轮事件"""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def create_port_widget(self, parent, port_name, port_info):
        """创建单个串口控件"""
        frame = tk.Frame(parent, relief='raised', bd=1, bg='#f8f8f8', padx=8, pady=8)

        # 顶部：复选框和端口名
        top_frame = tk.Frame(frame, bg='#f8f8f8')
        top_frame.pack(fill='x', pady=(0, 5))

        var = tk.BooleanVar(value=port_info['selected'])
        checkbox = tk.Checkbutton(top_frame, variable=var, bg='#f8f8f8',
                                  command=lambda: self.toggle_port_selection(port_name, var.get()))
        checkbox.pack(side='left')

        name_label = tk.Label(top_frame, text=port_name, font=('Arial', 10, 'bold'),
                              bg='#f8f8f8')
        name_label.pack(side='left', padx=(5, 0))

        # 状态按钮
        status_color = '#28a745' if port_info['status'] == 'running' else '#dc3545'
        status_text = '■' if port_info['status'] == 'running' else '▶'
        status_btn = tk.Button(top_frame, text=status_text, fg=status_color, bg='#f8f8f8',
                               bd=0, font=('Arial', 12),
                               command=lambda: self.toggle_port_status(port_name))
        status_btn.pack(side='right')

        # 信息显示
        info_frame = tk.Frame(frame, bg='#f8f8f8')
        info_frame.pack(fill='both', expand=True)

        # 运营商信息
        carrier_label = tk.Label(info_frame, text=port_info['carrier'],
                                 font=('Arial', 9, 'bold'), bg='#f8f8f8',
                                 fg='#ff6b35', anchor='w')
        carrier_label.pack(fill='x', pady=1)

        # 详细信息
        info_texts = [
            f"上限: {port_info['limit']}",
            f"成功: {port_info['success']}"
        ]

        for text in info_texts:
            label = tk.Label(info_frame, text=text, font=('Arial', 9),
                             bg='#f8f8f8', anchor='w')
            label.pack(fill='x', pady=1)

        # 状态信息
        status_text = '运行中' if port_info['status'] == 'running' else '已停止'
        status_color = '#28a745' if port_info['status'] == 'running' else '#666'
        status_label = tk.Label(info_frame, text=f"状态: {status_text}",
                                font=('Arial', 9), bg='#f8f8f8',
                                fg=status_color, anchor='w')
        status_label.pack(fill='x', pady=1)

        return frame

    def update_display(self):
        """更新端口显示"""
        # 清除现有的端口显示
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        # 重新创建端口显示
        ports = self.port_manager.ports
        if not ports:
            # 显示无端口提示
            no_port_label = tk.Label(self.scrollable_frame,
                                     text="未检测到可用端口\n请检查设备连接",
                                     font=('Arial', 12), fg='#666', bg='white')
            no_port_label.pack(expand=True, fill='both')
            return

        row = 0
        col = 0
        for port_name, port_info in ports.items():
            port_widget = self.create_port_widget(self.scrollable_frame, port_name, port_info)
            port_widget.grid(row=row, column=col, padx=5, pady=5, sticky='ew')

            col += 1
            if col >= 2:  # 每行显示2个端口
                col = 0
                row += 1

        # 配置列权重
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        self.scrollable_frame.grid_columnconfigure(1, weight=1)

    def toggle_port_selection(self, port_name, selected):
        """切换端口选择状态"""
        self.port_manager.set_port_selection(port_name, selected)

    def select_all_ports(self):
        """全选端口"""
        self.port_manager.select_all_ports()
        self.update_display()
        self.status_callback("已全选所有端口")

    def deselect_all_ports(self):
        """取消全选端口"""
        self.port_manager.deselect_all_ports()
        self.update_display()
        self.status_callback("已取消全选端口")

    def reverse_select_ports(self):
        """反选端口"""
        self.port_manager.reverse_select_ports()
        self.update_display()
        self.status_callback("已反选端口")

    def toggle_port_status(self, port_name):
        """切换端口运行状态"""
        new_status = self.port_manager.toggle_port_status(port_name)
        if new_status:
            self.update_display()
            status_text = "启动" if new_status == 'running' else "停止"
            self.status_callback(f"端口 {port_name} 已{status_text}")

    def start_selected_ports(self):
        """启动选中的端口"""
        selected_ports = self.port_manager.get_selected_ports()
        if not selected_ports:
            messagebox.showwarning("警告", "请先选择要启动的端口")
            return

        # 尝试连接设备
        connected_count = 0
        for port_name in selected_ports:
            if self.port_manager.add_device(port_name):
                connected_count += 1

        # 启动端口
        started_count = self.port_manager.start_selected_ports()

        self.update_display()
        self.status_callback(f"已启动 {started_count} 个端口，成功连接 {connected_count} 个设备")

    def stop_selected_ports(self):
        """停止选中的端口"""
        selected_ports = self.port_manager.get_selected_ports()
        if not selected_ports:
            messagebox.showwarning("警告", "请先选择要停止的端口")
            return

        # 断开设备连接
        for port_name in selected_ports:
            self.port_manager.remove_device(port_name)

        # 停止端口
        stopped_count = self.port_manager.stop_selected_ports()

        self.update_display()
        self.status_callback(f"已停止 {stopped_count} 个端口")

    def clear_all_records(self):
        """清除所有记录"""
        if messagebox.askyesno("确认", "确定要清除所有发送记录吗？"):
            self.port_manager.clear_all_records()
            self.update_display()
            self.status_callback("所有发送记录已清除")

    def clear_current_records(self):
        """清除当前记录"""
        if messagebox.askyesno("确认", "确定要清除当前发送记录吗？"):
            self.port_manager.clear_current_records()
            self.update_display()
            self.status_callback("当前发送记录已清除")

    def show_settings_dialog(self):
        """显示设置对话框"""
        from config.settings import settings
        dialog = ConfigDialog(self, settings)
        self.wait_window(dialog.dialog)

    def refresh_ports(self):
        """刷新端口列表"""
        try:
            # 重新扫描端口
            self.port_manager.scan_ports()
            self.update_display()
            port_count = len(self.port_manager.ports)
            self.status_callback(f"端口刷新完成，发现 {port_count} 个端口")
        except Exception as e:
            messagebox.showerror("错误", f"刷新端口失败: {e}")

    def show_port_details(self, port_name):
        """显示端口详细信息"""
        port_info = self.port_manager.get_port_info(port_name)
        if not port_info:
            return

        # 创建详情窗口
        details_window = tk.Toplevel(self)
        details_window.title(f"端口详情 - {port_name}")
        details_window.geometry("400x300")
        details_window.resizable(False, False)
        details_window.transient(self)
        details_window.grab_set()

        # 居中显示
        details_window.update_idletasks()
        x = (details_window.winfo_screenwidth() // 2) - (details_window.winfo_width() // 2)
        y = (details_window.winfo_screenheight() // 2) - (details_window.winfo_height() // 2)
        details_window.geometry(f"+{x}+{y}")

        main_frame = tk.Frame(details_window, padx=20, pady=20)
        main_frame.pack(fill='both', expand=True)

        # 端口信息
        info_text = f"""
端口名称: {port_info['name']}
运营商: {port_info['carrier']}
发送上限: {port_info['limit']}
成功发送: {port_info['success']}
当前状态: {'运行中' if port_info['status'] == 'running' else '已停止'}
描述: {port_info.get('description', '无')}
        """

        text_widget = tk.Text(main_frame, wrap=tk.WORD, width=40, height=12)
        text_widget.pack(fill='both', expand=True)
        text_widget.insert('1.0', info_text.strip())
        text_widget.config(state='disabled')

        # 按钮框架
        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(fill='x', pady=(10, 0))

        # 测试连接按钮
        tk.Button(btn_frame, text="测试连接",
                  command=lambda: self.test_port_connection(port_name),
                  bg='#007bff', fg='white', padx=10).pack(side='left', padx=(0, 5))

        # 关闭按钮
        tk.Button(btn_frame, text="关闭", command=details_window.destroy,
                  bg='#e0e0e0', padx=20).pack(side='right')

    def test_port_connection(self, port_name):
        """测试端口连接"""
        try:
            # 这里可以实现实际的端口连接测试
            from core.utils import check_port_availability

            if check_port_availability(port_name):
                messagebox.showinfo("测试结果", f"端口 {port_name} 连接正常")
            else:
                messagebox.showwarning("测试结果", f"端口 {port_name} 连接失败")

        except Exception as e:
            messagebox.showerror("测试错误", f"测试端口连接时出错: {e}")

    def export_port_info(self):
        """导出端口信息"""
        from tkinter import filedialog
        from core.utils import export_data_to_csv

        filename = filedialog.asksaveasfilename(
            title="保存端口信息",
            defaultextension=".csv",
            filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")]
        )

        if filename:
            try:
                port_data = []
                for port_name, port_info in self.port_manager.ports.items():
                    port_data.append({
                        'port_name': port_name,
                        'carrier': port_info['carrier'],
                        'limit': port_info['limit'],
                        'success': port_info['success'],
                        'status': port_info['status'],
                        'description': port_info.get('description', '')
                    })

                headers = ['port_name', 'carrier', 'limit', 'success', 'status', 'description']
                if export_data_to_csv(port_data, filename, headers):
                    messagebox.showinfo("成功", f"端口信息已导出到 {filename}")
                else:
                    messagebox.showerror("错误", "导出端口信息失败")

            except Exception as e:
                messagebox.showerror("错误", f"导出端口信息时出错: {e}")

    def create_context_menu(self):
        """创建右键菜单"""
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="启动端口", command=self.start_context_port)
        self.context_menu.add_command(label="停止端口", command=self.stop_context_port)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="端口详情", command=self.show_context_port_details)
        self.context_menu.add_command(label="测试连接", command=self.test_context_port)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="清除记录", command=self.clear_context_port_record)

    def show_context_menu(self, event, port_name):
        """显示右键菜单"""
        self.context_port_name = port_name
        try:
            self.context_menu.post(event.x_root, event.y_root)
        except:
            pass

    def start_context_port(self):
        """启动右键选中的端口"""
        if hasattr(self, 'context_port_name'):
            self.port_manager.update_port_status(self.context_port_name, 'running')
            self.port_manager.add_device(self.context_port_name)
            self.update_display()
            self.status_callback(f"端口 {self.context_port_name} 已启动")

    def stop_context_port(self):
        """停止右键选中的端口"""
        if hasattr(self, 'context_port_name'):
            self.port_manager.update_port_status(self.context_port_name, 'stopped')
            self.port_manager.remove_device(self.context_port_name)
            self.update_display()
            self.status_callback(f"端口 {self.context_port_name} 已停止")

    def show_context_port_details(self):
        """显示右键选中端口的详情"""
        if hasattr(self, 'context_port_name'):
            self.show_port_details(self.context_port_name)

    def test_context_port(self):
        """测试右键选中的端口"""
        if hasattr(self, 'context_port_name'):
            self.test_port_connection(self.context_port_name)

    def clear_context_port_record(self):
        """清除右键选中端口的记录"""
        if hasattr(self, 'context_port_name'):
            port_name = self.context_port_name
            if messagebox.askyesno("确认", f"确定要清除端口 {port_name} 的发送记录吗？"):
                if port_name in self.port_manager.ports:
                    self.port_manager.ports[port_name]['success'] = 0
                    self.update_display()
                    self.status_callback(f"端口 {port_name} 的发送记录已清除")


class PortStatusWidget(tk.Frame):
    """端口状态控件"""

    def __init__(self, parent, port_name, port_info, callback):
        super().__init__(parent, relief='raised', bd=1, bg='#f8f8f8', padx=8, pady=8)

        self.port_name = port_name
        self.port_info = port_info
        self.callback = callback

        self.create_widgets()

        # 绑定右键菜单
        self.bind("<Button-3>", self.show_context_menu)
        for widget in self.winfo_children():
            widget.bind("<Button-3>", self.show_context_menu)

    def create_widgets(self):
        """创建控件"""
        # 顶部：复选框和端口名
        top_frame = tk.Frame(self, bg='#f8f8f8')
        top_frame.pack(fill='x', pady=(0, 5))

        self.var = tk.BooleanVar(value=self.port_info['selected'])
        checkbox = tk.Checkbutton(top_frame, variable=self.var, bg='#f8f8f8',
                                  command=self.on_selection_change)
        checkbox.pack(side='left')

        name_label = tk.Label(top_frame, text=self.port_name,
                              font=('Arial', 10, 'bold'), bg='#f8f8f8')
        name_label.pack(side='left', padx=(5, 0))

        # 状态按钮
        status_color = '#28a745' if self.port_info['status'] == 'running' else '#dc3545'
        status_text = '■' if self.port_info['status'] == 'running' else '▶'
        self.status_btn = tk.Button(top_frame, text=status_text, fg=status_color,
                                    bg='#f8f8f8', bd=0, font=('Arial', 12),
                                    command=self.toggle_status)
        self.status_btn.pack(side='right')

        # 信息显示
        info_frame = tk.Frame(self, bg='#f8f8f8')
        info_frame.pack(fill='both', expand=True)

        # 运营商
        carrier_label = tk.Label(info_frame, text=self.port_info['carrier'],
                                 font=('Arial', 9, 'bold'), bg='#f8f8f8',
                                 fg='#ff6b35', anchor='w')
        carrier_label.pack(fill='x', pady=1)

        # 上限和成功数
        limit_label = tk.Label(info_frame, text=f"上限: {self.port_info['limit']}",
                               font=('Arial', 9), bg='#f8f8f8', anchor='w')
        limit_label.pack(fill='x', pady=1)

        success_label = tk.Label(info_frame, text=f"成功: {self.port_info['success']}",
                                 font=('Arial', 9), bg='#f8f8f8', anchor='w')
        success_label.pack(fill='x', pady=1)

        # 状态
        status_text = '运行中' if self.port_info['status'] == 'running' else '已停止'
        status_color = '#28a745' if self.port_info['status'] == 'running' else '#666'
        self.status_label = tk.Label(info_frame, text=f"状态: {status_text}",
                                     font=('Arial', 9), bg='#f8f8f8',
                                     fg=status_color, anchor='w')
        self.status_label.pack(fill='x', pady=1)

    def on_selection_change(self):
        """选择状态改变"""
        if self.callback:
            self.callback('selection_change', self.port_name, self.var.get())

    def toggle_status(self):
        """切换状态"""
        if self.callback:
            self.callback('toggle_status', self.port_name, None)

    def show_context_menu(self, event):
        """显示右键菜单"""
        if self.callback:
            self.callback('context_menu', self.port_name, event)

    def update_info(self, port_info):
        """更新端口信息"""
        self.port_info = port_info
        # 重新创建控件
        for widget in self.winfo_children():
            widget.destroy()
        self.create_widgets()