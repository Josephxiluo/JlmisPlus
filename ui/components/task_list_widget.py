"""
任务列表组件 - 左侧任务管理区域
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ui.styles import get_color, get_font
from services.task_service import TaskService


class TaskListWidget:
    """任务列表组件"""

    def __init__(self, parent, user_info, on_task_select=None, on_task_update=None):
        self.parent = parent
        self.user_info = user_info
        self.on_task_select = on_task_select  # 任务选择回调
        self.on_task_update = on_task_update  # 任务更新回调
        self.task_service = TaskService()
        self.selected_task = None
        self.tasks = []
        self.create_widgets()
        self.load_tasks()

    def create_widgets(self):
        """创建任务列表组件"""
        # 主容器
        self.frame = tk.Frame(self.parent, bg=get_color('background'))

        # 标题和控制按钮
        self.create_header()

        # 任务列表
        self.create_task_list()

    def create_header(self):
        """创建头部控制区域"""
        header_frame = tk.Frame(self.frame, bg=get_color('background'))
        header_frame.pack(fill='x', padx=10, pady=(10, 5))

        # 标题
        title_label = tk.Label(
            header_frame,
            text="任务列表",
            font=get_font('title'),
            fg=get_color('text'),
            bg=get_color('background')
        )
        title_label.pack(side='left')

        # 控制按钮容器
        button_frame = tk.Frame(header_frame, bg=get_color('background'))
        button_frame.pack(side='right')

        # 停止发送按钮
        self.stop_button = tk.Button(
            button_frame,
            text="停止发送",
            font=get_font('button'),
            bg=get_color('gray'),
            fg='white',
            relief='flat',
            cursor='hand2',
            command=self.stop_sending,
            width=8
        )
        self.stop_button.pack(side='left', padx=(0, 5))

        # 添加任务按钮
        self.add_button = tk.Button(
            button_frame,
            text="添加任务",
            font=get_font('button'),
            bg=get_color('primary'),
            fg='white',
            relief='flat',
            cursor='hand2',
            command=self.add_task,
            width=8
        )
        self.add_button.pack(side='left', padx=(0, 5))

        # 更多操作按钮
        self.more_button = tk.Button(
            button_frame,
            text="更多",
            font=get_font('button'),
            bg=get_color('primary'),
            fg='white',
            relief='flat',
            cursor='hand2',
            command=self.show_more_menu,
            width=6
        )
        self.more_button.pack(side='left')

    def create_task_list(self):
        """创建任务列表"""
        # 列表容器
        list_frame = tk.Frame(self.frame, bg=get_color('background'))
        list_frame.pack(fill='both', expand=True, padx=10, pady=5)

        # 创建Treeview用于显示任务列表
        columns = ('task', 'progress', 'success', 'failed', 'status')
        self.task_tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show='headings',
            height=10
        )

        # 设置列标题和宽度
        self.task_tree.heading('task', text='任务')
        self.task_tree.heading('progress', text='进度')
        self.task_tree.heading('success', text='成功')
        self.task_tree.heading('failed', text='失败')
        self.task_tree.heading('status', text='状态')

        self.task_tree.column('task', width=100)
        self.task_tree.column('progress', width=120)
        self.task_tree.column('success', width=60)
        self.task_tree.column('failed', width=60)
        self.task_tree.column('status', width=80)

        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.task_tree.yview)
        self.task_tree.configure(yscrollcommand=scrollbar.set)

        # 布局
        self.task_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # 绑定选择事件
        self.task_tree.bind('<<TreeviewSelect>>', self.on_task_select_event)
        self.task_tree.bind('<Button-3>', self.show_context_menu)  # 右键菜单

        # 创建右键菜单
        self.create_context_menu()

    def create_context_menu(self):
        """创建右键菜单"""
        self.context_menu = tk.Menu(self.frame, tearoff=0)
        self.context_menu.add_command(label="开始任务", command=self.start_task)
        self.context_menu.add_command(label="暂停任务", command=self.pause_task)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="重试失败", command=self.retry_failed)
        self.context_menu.add_command(label="测试任务", command=self.test_task)
        self.context_menu.add_command(label="修改内容", command=self.edit_task)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="导出-已完成", command=self.export_completed)
        self.context_menu.add_command(label="导出-未完成", command=self.export_uncompleted)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="删除该任务", command=self.delete_task, foreground='red')

    def load_tasks(self):
        """加载任务列表"""
        try:
            # 清空现有列表
            for item in self.task_tree.get_children():
                self.task_tree.delete(item)

            # 获取用户任务
            result = self.task_service.get_user_tasks(self.user_info.get('id'))
            if result['success']:
                self.tasks = result['tasks']

                # 填充任务列表
                for task in self.tasks:
                    progress = f"{task.get('progress', 0):.1f}% ({task.get('sent', 0)}/{task.get('total', 0)})"
                    status_text = self.get_status_text(task.get('status', 'stopped'))

                    self.task_tree.insert('', 'end', values=(
                        task.get('title', f"v{task.get('id', '')}"),
                        progress,
                        task.get('success_count', 0),
                        task.get('failed_count', 0),
                        status_text
                    ), tags=(str(task.get('id')),))

        except Exception as e:
            messagebox.showerror("错误", f"加载任务列表失败：{str(e)}")

    def get_status_text(self, status):
        """获取状态显示文本"""
        status_map = {
            'stopped': '停止',
            'running': '发送中',
            'paused': '暂停',
            'completed': '完成',
            'failed': '失败'
        }
        return status_map.get(status, '未知')

    def on_task_select_event(self, event):
        """任务选择事件"""
        selection = self.task_tree.selection()
        if selection:
            item = self.task_tree.item(selection[0])
            task_id = item['tags'][0] if item['tags'] else None

            # 查找对应的任务对象
            self.selected_task = None
            for task in self.tasks:
                if str(task.get('id')) == task_id:
                    self.selected_task = task
                    break

            # 调用回调函数
            if self.on_task_select and self.selected_task:
                self.on_task_select(self.selected_task)

    def show_context_menu(self, event):
        """显示右键菜单"""
        # 选中右键点击的项目
        item = self.task_tree.identify_row(event.y)
        if item:
            self.task_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def show_more_menu(self):
        """显示更多操作菜单"""
        # 创建弹出菜单
        more_menu = tk.Menu(self.frame, tearoff=0)
        more_menu.add_command(label="刷新列表", command=self.refresh_tasks)
        more_menu.add_command(label="全部开始", command=self.start_all_tasks)
        more_menu.add_command(label="全部停止", command=self.stop_all_tasks)
        more_menu.add_separator()
        more_menu.add_command(label="清理完成任务", command=self.clear_completed)
        more_menu.add_command(label="导出任务报告", command=self.export_report)

        # 在按钮下方显示菜单
        x = self.more_button.winfo_rootx()
        y = self.more_button.winfo_rooty() + self.more_button.winfo_height()
        more_menu.post(x, y)

    def stop_sending(self):
        """停止发送"""
        if messagebox.askyesno("确认", "确定要停止所有正在发送的任务吗？"):
            try:
                result = self.task_service.stop_all_tasks(self.user_info.get('id'))
                if result['success']:
                    messagebox.showinfo("成功", "已停止所有发送任务")
                    self.refresh_tasks()
                else:
                    messagebox.showerror("失败", result['message'])
            except Exception as e:
                messagebox.showerror("错误", f"停止发送失败：{str(e)}")

    def add_task(self):
        """添加任务"""
        # 这里应该调用添加任务对话框
        if self.on_task_update:
            self.on_task_update('add', None)

    def start_task(self):
        """开始任务"""
        if not self.selected_task:
            messagebox.showwarning("警告", "请先选择一个任务")
            return

        try:
            result = self.task_service.start_task(self.selected_task['id'])
            if result['success']:
                messagebox.showinfo("成功", "任务已开始")
                self.refresh_tasks()
            else:
                messagebox.showerror("失败", result['message'])
        except Exception as e:
            messagebox.showerror("错误", f"开始任务失败：{str(e)}")

    def pause_task(self):
        """暂停任务"""
        if not self.selected_task:
            messagebox.showwarning("警告", "请先选择一个任务")
            return

        try:
            result = self.task_service.pause_task(self.selected_task['id'])
            if result['success']:
                messagebox.showinfo("成功", "任务已暂停")
                self.refresh_tasks()
            else:
                messagebox.showerror("失败", result['message'])
        except Exception as e:
            messagebox.showerror("错误", f"暂停任务失败：{str(e)}")

    def retry_failed(self):
        """重试失败"""
        if not self.selected_task:
            messagebox.showwarning("警告", "请先选择一个任务")
            return

        if messagebox.askyesno("确认", f"确定要重试任务 '{self.selected_task.get('title')}' 的失败项目吗？"):
            try:
                result = self.task_service.retry_failed(self.selected_task['id'])
                if result['success']:
                    messagebox.showinfo("成功", f"已重试 {result['count']} 个失败项目")
                    self.refresh_tasks()
                else:
                    messagebox.showerror("失败", result['message'])
            except Exception as e:
                messagebox.showerror("错误", f"重试失败：{str(e)}")

    def test_task(self):
        """测试任务"""
        if not self.selected_task:
            messagebox.showwarning("警告", "请先选择一个任务")
            return

        if self.on_task_update:
            self.on_task_update('test', self.selected_task)

    def edit_task(self):
        """修改任务内容"""
        if not self.selected_task:
            messagebox.showwarning("警告", "请先选择一个任务")
            return

        if self.on_task_update:
            self.on_task_update('edit', self.selected_task)

    def delete_task(self):
        """删除任务"""
        if not self.selected_task:
            messagebox.showwarning("警告", "请先选择一个任务")
            return

        if messagebox.askyesno("确认删除", f"确定要删除任务 '{self.selected_task.get('title')}' 吗？\n此操作不可恢复！"):
            try:
                result = self.task_service.delete_task(self.selected_task['id'])
                if result['success']:
                    messagebox.showinfo("成功", "任务已删除")
                    self.refresh_tasks()
                else:
                    messagebox.showerror("失败", result['message'])
            except Exception as e:
                messagebox.showerror("错误", f"删除任务失败：{str(e)}")

    def export_completed(self):
        """导出已完成"""
        if not self.selected_task:
            messagebox.showwarning("警告", "请先选择一个任务")
            return

        if self.on_task_update:
            self.on_task_update('export_completed', self.selected_task)

    def export_uncompleted(self):
        """导出未完成"""
        if not self.selected_task:
            messagebox.showwarning("警告", "请先选择一个任务")
            return

        if self.on_task_update:
            self.on_task_update('export_uncompleted', self.selected_task)

    def refresh_tasks(self):
        """刷新任务列表"""
        self.load_tasks()

    def start_all_tasks(self):
        """开始所有任务"""
        if messagebox.askyesno("确认", "确定要开始所有停止的任务吗？"):
            try:
                result = self.task_service.start_all_tasks(self.user_info.get('id'))
                if result['success']:
                    messagebox.showinfo("成功", f"已开始 {result['count']} 个任务")
                    self.refresh_tasks()
                else:
                    messagebox.showerror("失败", result['message'])
            except Exception as e:
                messagebox.showerror("错误", f"开始所有任务失败：{str(e)}")

    def stop_all_tasks(self):
        """停止所有任务"""
        if messagebox.askyesno("确认", "确定要停止所有正在运行的任务吗？"):
            try:
                result = self.task_service.stop_all_tasks(self.user_info.get('id'))
                if result['success']:
                    messagebox.showinfo("成功", f"已停止 {result['count']} 个任务")
                    self.refresh_tasks()
                else:
                    messagebox.showerror("失败", result['message'])
            except Exception as e:
                messagebox.showerror("错误", f"停止所有任务失败：{str(e)}")

    def clear_completed(self):
        """清理完成任务"""
        if messagebox.askyesno("确认", "确定要清理所有已完成的任务吗？\n此操作不可恢复！"):
            try:
                result = self.task_service.clear_completed_tasks(self.user_info.get('id'))
                if result['success']:
                    messagebox.showinfo("成功", f"已清理 {result['count']} 个完成任务")
                    self.refresh_tasks()
                else:
                    messagebox.showerror("失败", result['message'])
            except Exception as e:
                messagebox.showerror("错误", f"清理完成任务失败：{str(e)}")

    def export_report(self):
        """导出任务报告"""
        if self.on_task_update:
            self.on_task_update('export_report', None)

    def get_frame(self):
        """获取组件框架"""
        return self.frame

    def update_task_progress(self, task_id, progress_data):
        """更新任务进度显示"""
        # 查找对应的树节点并更新
        for item in self.task_tree.get_children():
            item_data = self.task_tree.item(item)
            if item_data['tags'] and item_data['tags'][0] == str(task_id):
                # 更新进度显示
                progress = f"{progress_data.get('progress', 0):.1f}% ({progress_data.get('sent', 0)}/{progress_data.get('total', 0)})"
                status_text = self.get_status_text(progress_data.get('status', 'stopped'))

                self.task_tree.item(item, values=(
                    item_data['values'][0],  # 保持任务名不变
                    progress,
                    progress_data.get('success_count', 0),
                    progress_data.get('failed_count', 0),
                    status_text
                ))
                break


def main():
    """测试任务列表组件"""
    root = tk.Tk()
    root.title("任务列表测试")
    root.geometry("600x400")
    root.configure(bg='#f5f5f5')

    # 模拟用户信息
    user_info = {
        'id': 1,
        'username': 'test_user',
        'balance': 10000
    }

    def on_task_select(task):
        print(f"选中任务: {task}")

    def on_task_update(action, task):
        print(f"任务操作: {action}, 任务: {task}")

    # 创建任务列表组件
    task_list = TaskListWidget(root, user_info, on_task_select, on_task_update)
    task_list.get_frame().pack(fill='both', expand=True)

    root.mainloop()


if __name__ == '__main__':
    main()