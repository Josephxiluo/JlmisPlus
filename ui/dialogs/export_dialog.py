"""
导出对话框 - 导出任务数据
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sys
import os
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ui.styles import get_color, get_font
from services.export_service import ExportService


class ExportDialog:
    """导出对话框"""

    def __init__(self, parent, task=None, export_type='completed'):
        self.parent = parent
        self.task = task
        self.export_type = export_type  # completed, uncompleted, report
        self.export_service = ExportService()
        self.result = None
        self.create_dialog()

    def create_dialog(self):
        """创建对话框"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title(self.get_dialog_title())
        self.dialog.geometry("450x400")
        self.dialog.resizable(False, False)
        self.dialog.configure(bg=get_color('background'))

        # 设置模态对话框
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        # 居中显示
        self.center_dialog()

        # 创建内容
        self.create_content()

        # 创建按钮
        self.create_buttons()

    def get_dialog_title(self):
        """获取对话框标题"""
        titles = {
            'completed': '导出-已完成',
            'uncompleted': '导出-未完成',
            'report': '导出任务报告'
        }
        return titles.get(self.export_type, '导出数据')

    def center_dialog(self):
        """对话框居中显示"""
        self.dialog.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (450 // 2)
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (400 // 2)
        self.dialog.geometry(f"450x400+{x}+{y}")

    def create_content(self):
        """创建对话框内容"""
        # 主容器
        main_frame = tk.Frame(self.dialog, bg=get_color('background'))
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)

        # 导出信息显示
        self.create_export_info(main_frame)

        # 导出选项
        self.create_export_options(main_frame)

        # 文件设置
        self.create_file_settings(main_frame)

    def create_export_info(self, parent):
        """创建导出信息显示"""
        info_frame = tk.Frame(parent, bg=get_color('primary_light'), relief='solid', bd=1)
        info_frame.pack(fill='x', pady=(0, 20))

        # 导出类型标题
        title_text = self.get_export_title()
        tk.Label(
            info_frame,
            text=title_text,
            font=get_font('title'),
            fg=get_color('text'),
            bg=get_color('primary_light')
        ).pack(anchor='w', padx=15, pady=(10, 5))

        # 任务信息（如果有指定任务）
        if self.task:
            task_name = self.task.get('title', f"v{self.task.get('id', '')}")
            tk.Label(
                info_frame,
                text=f"任务：{task_name}",
                font=get_font('default'),
                fg=get_color('text'),
                bg=get_color('primary_light')
            ).pack(anchor='w', padx=15, pady=(0, 5))

            # 统计信息
            stats_text = self.get_stats_text()
            if stats_text:
                tk.Label(
                    info_frame,
                    text=stats_text,
                    font=get_font('small'),
                    fg=get_color('text'),
                    bg=get_color('primary_light')
                ).pack(anchor='w', padx=15, pady=(0, 10))
        else:
            tk.Label(
                info_frame,
                text="导出所有任务的报告数据",
                font=get_font('default'),
                fg=get_color('text'),
                bg=get_color('primary_light')
            ).pack(anchor='w', padx=15, pady=(0, 10))

    def get_export_title(self):
        """获取导出标题"""
        titles = {
            'completed': '导出已完成记录',
            'uncompleted': '导出未完成记录',
            'report': '导出任务报告'
        }
        return titles.get(self.export_type, '导出数据')

    def get_stats_text(self):
        """获取统计信息文本"""
        if not self.task:
            return ""

        if self.export_type == 'completed':
            count = self.task.get('success_count', 0)
            return f"将导出 {count} 条已完成记录"
        elif self.export_type == 'uncompleted':
            total = self.task.get('total', 0)
            sent = self.task.get('sent', 0)
            unsent = total - sent
            failed = self.task.get('failed_count', 0)
            count = unsent + failed
            return f"将导出 {count} 条未完成记录（未发送：{unsent}，失败：{failed}）"
        else:
            return f"将导出任务的完整报告"

    def create_export_options(self, parent):
        """创建导出选项"""
        options_group = tk.LabelFrame(
            parent,
            text="导出选项",
            font=get_font('button'),
            fg=get_color('primary'),
            bg=get_color('background'),
            padx=15,
            pady=10
        )
        options_group.pack(fill='x', pady=(0, 20))

        # 文件格式
        format_frame = tk.Frame(options_group, bg=get_color('background'))
        format_frame.pack(fill='x', pady=(0, 10))

        tk.Label(
            format_frame,
            text="文件格式:",
            font=get_font('default'),
            fg=get_color('text'),
            bg=get_color('background')
        ).pack(anchor='w', pady=(0, 5))

        self.format_var = tk.StringVar(value="Excel (.xlsx)")
        format_combo = ttk.Combobox(
            format_frame,
            textvariable=self.format_var,
            values=["Excel (.xlsx)", "CSV (.csv)", "文本文件 (.txt)"],
            state='readonly',
            font=get_font('default')
        )
        format_combo.pack(fill='x')

        # 包含字段（根据导出类型显示不同选项）
        fields_frame = tk.Frame(options_group, bg=get_color('background'))
        fields_frame.pack(fill='x')

        tk.Label(
            fields_frame,
            text="包含字段:",
            font=get_font('default'),
            fg=get_color('text'),
            bg=get_color('background')
        ).pack(anchor='w', pady=(0, 5))

        # 创建字段选择
        self.create_field_options(fields_frame)

    def create_field_options(self, parent):
        """创建字段选择选项"""
        fields_container = tk.Frame(parent, bg=get_color('background'))
        fields_container.pack(fill='x')

        # 根据导出类型显示不同字段
        if self.export_type in ['completed', 'uncompleted']:
            fields = [
                ('phone', '接收号码', True),
                ('send_phone', '发送号码', True),
                ('port', '发送串口', True),
                ('carrier', '运营商', False),
                ('status', '发送状态', True),
                ('send_time', '发送时间', True),
                ('receive_time', '接收时间', False),
                ('content', '短信内容', False)
            ]
        else:  # report
            fields = [
                ('task_name', '任务名称', True),
                ('total_count', '总数量', True),
                ('success_count', '成功数量', True),
                ('failed_count', '失败数量', True),
                ('progress', '完成进度', True),
                ('create_time', '创建时间', True),
                ('complete_time', '完成时间', False),
                ('content', '任务内容', False)
            ]

        self.field_vars = {}

        # 创建两列布局
        col1_frame = tk.Frame(fields_container, bg=get_color('background'))
        col1_frame.pack(side='left', fill='both', expand=True)

        col2_frame = tk.Frame(fields_container, bg=get_color('background'))
        col2_frame.pack(side='right', fill='both', expand=True)

        for i, (key, label, default) in enumerate(fields):
            var = tk.BooleanVar(value=default)
            self.field_vars[key] = var

            # 交替放置到两列
            parent_frame = col1_frame if i % 2 == 0 else col2_frame

            check = tk.Checkbutton(
                parent_frame,
                text=label,
                variable=var,
                font=get_font('small'),
                fg=get_color('text'),
                bg=get_color('background'),
                activebackground=get_color('background')
            )
            check.pack(anchor='w', pady=2)

    def create_file_settings(self, parent):
        """创建文件设置"""
        file_group = tk.LabelFrame(
            parent,
            text="文件设置",
            font=get_font('button'),
            fg=get_color('primary'),
            bg=get_color('background'),
            padx=15,
            pady=10
        )
        file_group.pack(fill='x')

        # 保存路径
        path_frame = tk.Frame(file_group, bg=get_color('background'))
        path_frame.pack(fill='x', pady=(0, 10))

        tk.Label(
            path_frame,
            text="保存路径:",
            font=get_font('default'),
            fg=get_color('text'),
            bg=get_color('background')
        ).pack(anchor='w', pady=(0, 5))

        path_input_frame = tk.Frame(path_frame, bg=get_color('background'))
        path_input_frame.pack(fill='x')

        self.path_entry = tk.Entry(
            path_input_frame,
            font=get_font('default'),
            relief='solid',
            bd=1
        )
        self.path_entry.pack(side='left', fill='both', expand=True)

        browse_btn = tk.Button(
            path_input_frame,
            text="浏览",
            font=get_font('button'),
            bg=get_color('primary'),
            fg='white',
            relief='flat',
            cursor='hand2',
            command=self.browse_path,
            width=8
        )
        browse_btn.pack(side='right', padx=(5, 0))

        # 文件名
        name_frame = tk.Frame(file_group, bg=get_color('background'))
        name_frame.pack(fill='x')

        tk.Label(
            name_frame,
            text="文件名:",
            font=get_font('default'),
            fg=get_color('text'),
            bg=get_color('background')
        ).pack(anchor='w', pady=(0, 5))

        self.filename_entry = tk.Entry(
            name_frame,
            font=get_font('default'),
            relief='solid',
            bd=1
        )
        self.filename_entry.pack(fill='x')

        # 设置默认值
        self.set_default_values()

    def set_default_values(self):
        """设置默认值"""
        # 默认保存路径
        default_path = os.path.join(os.path.expanduser("~"), "Desktop")
        self.path_entry.insert(0, default_path)

        # 默认文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if self.task:
            task_name = self.task.get('title', f"v{self.task.get('id', '')}")
            filename = f"{task_name}_{self.export_type}_{timestamp}"
        else:
            filename = f"任务报告_{timestamp}"

        self.filename_entry.insert(0, filename)

    def browse_path(self):
        """浏览保存路径"""
        folder = filedialog.askdirectory(
            title="选择保存路径",
            initialdir=self.path_entry.get()
        )
        if folder:
            self.path_entry.delete(0, 'end')
            self.path_entry.insert(0, folder)

    def create_buttons(self):
        """创建按钮"""
        button_frame = tk.Frame(self.dialog, bg=get_color('background'))
        button_frame.pack(fill='x', padx=20, pady=(0, 20))

        # 取消按钮
        cancel_btn = tk.Button(
            button_frame,
            text="取消",
            font=get_font('button'),
            bg=get_color('gray'),
            fg='white',
            relief='flat',
            cursor='hand2',
            command=self.cancel,
            width=12
        )
        cancel_btn.pack(side='left')

        # 导出按钮
        export_btn = tk.Button(
            button_frame,
            text="开始导出",
            font=get_font('button'),
            bg=get_color('success'),
            fg='white',
            relief='flat',
            cursor='hand2',
            command=self.export,
            width=12
        )
        export_btn.pack(side='right')

    def validate_form(self):
        """验证表单"""
        # 检查保存路径
        save_path = self.path_entry.get().strip()
        if not save_path:
            messagebox.showerror("错误", "请选择保存路径")
            return False

        if not os.path.exists(save_path):
            messagebox.showerror("错误", "保存路径不存在")
            return False

        # 检查文件名
        filename = self.filename_entry.get().strip()
        if not filename:
            messagebox.showerror("错误", "请输入文件名")
            return False

        # 检查是否选择了至少一个字段
        selected_fields = [key for key, var in self.field_vars.items() if var.get()]
        if not selected_fields:
            messagebox.showerror("错误", "请至少选择一个导出字段")
            return False

        return True

    def get_file_extension(self):
        """获取文件扩展名"""
        format_map = {
            "Excel (.xlsx)": ".xlsx",
            "CSV (.csv)": ".csv",
            "文本文件 (.txt)": ".txt"
        }
        return format_map.get(self.format_var.get(), ".xlsx")

    def export(self):
        """开始导出"""
        if not self.validate_form():
            return

        try:
            # 构建导出参数
            save_path = self.path_entry.get().strip()
            filename = self.filename_entry.get().strip()
            extension = self.get_file_extension()

            # 确保文件名有正确的扩展名
            if not filename.lower().endswith(extension.lower()):
                filename += extension

            full_path = os.path.join(save_path, filename)

            # 检查文件是否已存在
            if os.path.exists(full_path):
                if not messagebox.askyesno("文件已存在", f"文件 {filename} 已存在，是否覆盖？"):
                    return

            # 获取选中的字段
            selected_fields = [key for key, var in self.field_vars.items() if var.get()]

            # 构建导出数据
            export_data = {
                'export_type': self.export_type,
                'task': self.task,
                'fields': selected_fields,
                'file_format': self.format_var.get(),
                'file_path': full_path
            }

            # 确认导出
            if messagebox.askyesno("确认导出", f"确定要导出数据到文件 {filename} 吗？"):
                # 禁用导出按钮，显示进度
                export_btn = None
                for widget in self.dialog.winfo_children():
                    if isinstance(widget, tk.Frame):
                        for btn in widget.winfo_children():
                            if isinstance(btn, tk.Button) and btn.cget('text') == '开始导出':
                                export_btn = btn
                                break

                if export_btn:
                    export_btn.config(state='disabled', text='导出中...')

                self.dialog.update()

                # 执行导出
                result = self.export_service.export_data(export_data)

                if result['success']:
                    messagebox.showinfo("导出成功",
                                        f"数据已成功导出到：\n{full_path}\n\n导出记录数：{result.get('count', 0)}")
                    self.result = result
                    self.dialog.destroy()
                else:
                    messagebox.showerror("导出失败", result['message'])
                    if export_btn:
                        export_btn.config(state='normal', text='开始导出')

        except Exception as e:
            messagebox.showerror("错误", f"导出失败：{str(e)}")

    def cancel(self):
        """取消"""
        self.result = None
        self.dialog.destroy()

    def show(self):
        """显示对话框并返回结果"""
        self.dialog.wait_window()
        return self.result


def main():
    """测试导出对话框"""
    root = tk.Tk()
    root.title("导出对话框测试")
    root.geometry("400x300")
    root.configure(bg='#f5f5f5')

    # 模拟任务信息
    task = {
        'id': 'v342',
        'title': '测试任务',
        'total': 100,
        'sent': 80,
        'success_count': 75,
        'failed_count': 5
    }

    def show_completed_dialog():
        dialog = ExportDialog(root, task, 'completed')
        result = dialog.show()
        if result:
            print("导出已完成记录结果:", result)
        else:
            print("导出取消")

    def show_uncompleted_dialog():
        dialog = ExportDialog(root, task, 'uncompleted')
        result = dialog.show()
        if result:
            print("导出未完成记录结果:", result)
        else:
            print("导出取消")

    def show_report_dialog():
        dialog = ExportDialog(root, None, 'report')
        result = dialog.show()
        if result:
            print("导出报告结果:", result)
        else:
            print("导出取消")

    # 测试按钮
    btn_frame = tk.Frame(root, bg='#f5f5f5')
    btn_frame.pack(expand=True)

    btn1 = tk.Button(
        btn_frame,
        text="导出已完成",
        font=('Microsoft YaHei', 10),
        bg='#32CD32',
        fg='white',
        relief='flat',
        cursor='hand2',
        command=show_completed_dialog,
        width=15,
        height=2
    )
    btn1.pack(pady=5)

    btn2 = tk.Button(
        btn_frame,
        text="导出未完成",
        font=('Microsoft YaHei', 10),
        bg='#FF7F50',
        fg='white',
        relief='flat',
        cursor='hand2',
        command=show_uncompleted_dialog,
        width=15,
        height=2
    )
    btn2.pack(pady=5)

    btn3 = tk.Button(
        btn_frame,
        text="导出任务报告",
        font=('Microsoft YaHei', 10),
        bg='#4169E1',
        fg='white',
        relief='flat',
        cursor='hand2',
        command=show_report_dialog,
        width=15,
        height=2
    )
    btn3.pack(pady=5)

    root.mainloop()


if __name__ == '__main__':
    main()