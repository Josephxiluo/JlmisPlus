"""
主界面模块
"""
import tkinter as tk
from tkinter import messagebox
import threading
import time
from datetime import timezone

from config.settings import settings
from core.port_manager import PortManager
from core.task_manager import TaskManager, TaskWorker
from core.message_sender import MessageSender
from core.monitor import Monitor, AlertManager
from ui.port_panel import PortPanel
from ui.task_panel import TaskPanel
from ui.config_panel import ConfigDialog
from ui.widgets import StatusBar
from ui.widgets import init_styles


class SmsPoolManager:
    """短信池管理主界面"""

    def __init__(self, root):
        self.root = root
        self.root.title("JinmisPlus-直发")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')

        init_styles(self.root)  # 初始化统一样式

        # 初始化数据库
        from core.database import get_db_manager
        try:
            self.db_manager = get_db_manager()
        except Exception as e:
            print(f"数据库连接失败: {e}")
            self.db_manager = None

        # 初始化核心组件
        self.port_manager = PortManager()
        self.task_manager = TaskManager(self.db_manager)  # 传入数据库管理器
        self.message_sender = MessageSender(self.port_manager, self.db_manager)
        self.monitor = Monitor()
        self.alert_manager = AlertManager(self.monitor)
        self.task_worker = TaskWorker(self.task_manager, self.port_manager, self.message_sender)

        # UI组件
        self.port_panel = None
        self.task_panel = None
        self.status_bar = None

        # 创建界面
        self.create_header()
        self.create_main_content()
        self.create_status_bar()

        # 初始化系统
        self.initialize_system()

    def create_header(self):
        """创建头部"""
        header_frame = tk.Frame(self.root, bg='white', height=60)
        header_frame.pack(fill='x', padx=10, pady=5)
        header_frame.pack_propagate(False)

        # 左侧标题
        title_frame = tk.Frame(header_frame, bg='white')
        title_frame.pack(side='left', pady=15)

        title_label = tk.Label(title_frame, text="Jinmis Plus", font=('Arial', 16, 'bold'),
                               fg='#ff6b35', bg='white')
        title_label.pack(side='left')

        subtitle_label = tk.Label(title_frame, text="本软件仅供学习测试研究，严禁用于违法用途",
                                  font=('Arial', 10), fg='#666', bg='white')
        subtitle_label.pack(side='left', padx=(10, 0))

        # 右侧余额
        balance_label = tk.Label(header_frame, text="测试积分：10000",
                                 font=('Arial', 10), fg='white', bg='#ff6b35',
                                 padx=15, pady=5)
        balance_label.pack(side='right', pady=15)

    def create_main_content(self):
        """创建主要内容区域"""
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill='both', expand=True, padx=10, pady=5)

        # 创建任务面板
        self.task_panel = TaskPanel(main_frame, self.task_manager, self.port_manager,
                                    self.message_sender, self.update_status)
        self.task_panel.pack(side='left', fill='both', expand=True, padx=(0, 5))

        # 创建端口面板
        self.port_panel = PortPanel(main_frame, self.port_manager, self.update_status)
        self.port_panel.pack(side='right', fill='both', expand=True, padx=(5, 0))

    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = StatusBar(self.root)
        self.status_bar.pack(fill='x', side='bottom')

    def initialize_system(self):
        """初始化系统"""
        # 扫描端口
        self.port_manager.scan_ports()
        self.port_panel.update_display()

        # 设置默认告警规则
        self.alert_manager.setup_default_rules()

        # 启动监控
        self.monitor.start_monitoring(self.port_manager, self.task_manager)

        # 启动任务工作器
        self.task_worker.start()

        # 设置状态更新回调
        self.monitor.add_callback(self.on_statistics_update)

        self.update_status("系统初始化完成")

    def on_statistics_update(self, statistics):
        """统计信息更新回调"""
        # 更新状态栏
        running_tasks = statistics.get('task_stats', {}).get('running_tasks', 0)
        running_ports = statistics.get('port_stats', {}).get('running_ports', 0)
        total_success = statistics.get('total_success', 0)

        status_text = f"运行任务: {running_tasks} | 活动端口: {running_ports} | 发送成功: {total_success}"
        self.status_bar.update_status(status_text)

        # 检查告警
        self.alert_manager.check_alerts(statistics)

    def update_status(self, message):
        """更新状态"""
        if self.status_bar:
            self.status_bar.update_status(message)

    def show_config_dialog(self):
        """显示配置对话框"""
        dialog = ConfigDialog(self.root, settings)
        self.root.wait_window(dialog.dialog)

    def start_background_tasks(self):
        """启动后台任务处理"""

        def background_worker():
            while True:
                try:
                    # 处理正在运行的任务
                    running_tasks = self.task_manager.get_running_tasks()

                    for task in running_tasks:
                        if not hasattr(self, '_stop_background'):
                            task_id = task['id']

                            # 检查任务是否需要处理
                            completed = task['success'] + task['failed']
                            if completed < task['total']:
                                # 获取下一个要发送的号码
                                phone_number = task['numbers'][completed]

                                # 获取可用端口
                                available_ports = self.port_manager.get_running_ports()
                                if available_ports:
                                    port_name = available_ports[completed % len(available_ports)]

                                    # 发送短信
                                    success = self.message_sender.send_message(
                                        port_name=port_name,
                                        phone_number=phone_number,
                                        message=task['content'],
                                        subject=task.get('subject', '')
                                    )

                                    # 更新任务进度
                                    if success:
                                        self.task_manager.update_task_progress(
                                            task_id, task['success'] + 1, task['failed']
                                        )
                                        self.port_manager.update_port_success(port_name)
                                        self.monitor.log_send_success(port_name, phone_number, task['name'])
                                    else:
                                        self.task_manager.update_task_progress(
                                            task_id, task['success'], task['failed'] + 1
                                        )
                                        self.monitor.log_send_failure(port_name, phone_number,
                                                                      "发送失败", task['name'])

                                    # 更新显示
                                    self.root.after(0, self.task_panel.update_display)
                                    self.root.after(0, self.port_panel.update_display)

                    # 发送间隔
                    time.sleep(settings.get('send_interval', 1000) / 1000.0)

                except Exception as e:
                    self.monitor.log_error(f"后台任务错误: {e}")
                    time.sleep(1)

        # 启动后台线程
        self.background_thread = threading.Thread(target=background_worker, daemon=True)
        self.background_thread.start()

    def load_config(self):
        """加载配置"""
        config = settings.load_config()

        # 加载任务信息
        saved_tasks = config.get('tasks', {})
        if saved_tasks:
            self.task_manager.tasks.update(saved_tasks)
            # 重置运行状态
            for task_id in self.task_manager.tasks:
                self.task_manager.tasks[task_id]['status'] = 'stopped'
            self.task_manager.running_tasks.clear()

        # 更新显示
        if self.task_panel:
            self.task_panel.update_display()

        self.update_status("配置加载完成")

    def save_config(self):
        """保存配置"""
        try:
            # 准备任务数据（移除不需要序列化的数据）
            tasks_to_save = {}
            for task_id, task in self.task_manager.tasks.items():
                task_copy = task.copy()
                # 重置运行状态
                task_copy['status'] = 'stopped'
                tasks_to_save[task_id] = task_copy

            # 保存配置
            success = settings.save_config(
                ports=None,  # 端口信息不保存，每次重新扫描
                tasks=tasks_to_save
            )

            if success:
                self.update_status("配置保存成功")
            else:
                self.update_status("配置保存失败")

        except Exception as e:
            self.monitor.log_error(f"保存配置失败: {e}")
            self.update_status("配置保存失败")

    def export_logs(self):
        """导出日志"""
        try:
            success = self.monitor.export_statistics()
            if success:
                messagebox.showinfo("成功", "日志导出成功")
            else:
                messagebox.showerror("错误", "日志导出失败")
        except Exception as e:
            messagebox.showerror("错误", f"导出日志时出错: {e}")

    def show_about_dialog(self):
        """显示关于对话框"""
        about_text = """
                JinmisPlus-直发
                
                猫池短信管理系统
                
                仅供测试研究，严禁用于违法用途
                
                © 2025 All Rights Reserved
        """
        messagebox.showinfo("关于", about_text.strip())

    def on_closing(self):
        """程序关闭时的处理"""
        try:
            # 停止所有任务
            self.task_manager.stop_all_tasks()

            # 停止后台工作器
            self._stop_background = True
            if hasattr(self, 'task_worker'):
                self.task_worker.stop()

            # 停止监控
            if hasattr(self, 'monitor'):
                self.monitor.stop_monitoring()

            # 断开所有设备连接
            for device in self.port_manager.devices.values():
                device.disconnect()

            # 关闭数据库连接
            if hasattr(self, 'db_manager'):
                self.db_manager.close()

            # 保存配置
            self.save_config()

            # 关闭窗口
            self.root.destroy()

        except Exception as e:
            print(f"关闭程序时出错: {e}")
            self.root.destroy()

    def create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="导入任务", command=self.import_tasks)
        file_menu.add_command(label="导出任务", command=self.export_tasks)
        file_menu.add_separator()
        file_menu.add_command(label="导出日志", command=self.export_logs)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.on_closing)

        # 工具菜单
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="工具", menu=tools_menu)
        tools_menu.add_command(label="系统配置", command=self.show_config_dialog)
        tools_menu.add_command(label="端口检测", command=self.scan_ports)
        tools_menu.add_command(label="清理日志", command=self.clean_logs)

        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="使用说明", command=self.show_help)
        help_menu.add_command(label="关于", command=self.show_about_dialog)

    def import_tasks(self):
        """导入任务"""
        from tkinter import filedialog

        filename = filedialog.askopenfilename(
            title="选择任务文件",
            filetypes=[("JSON文件", "*.json"), ("CSV文件", "*.csv")]
        )

        if filename:
            try:
                if filename.endswith('.json'):
                    self._import_tasks_from_json(filename)
                elif filename.endswith('.csv'):
                    self._import_tasks_from_csv(filename)

                self.task_panel.update_display()
                messagebox.showinfo("成功", "任务导入成功")
            except Exception as e:
                messagebox.showerror("错误", f"导入任务失败: {e}")

    def _import_tasks_from_json(self, filename):
        """从JSON文件导入任务"""
        import json

        with open(filename, 'r', encoding='utf-8') as f:
            tasks_data = json.load(f)

        for task_data in tasks_data:
            self.task_manager.create_task(
                name=task_data['name'],
                numbers=task_data['numbers'],
                subject=task_data.get('subject', ''),
                content=task_data['content']
            )

    def _import_tasks_from_csv(self, filename):
        """从CSV文件导入任务"""
        from core.utils import import_data_from_csv

        data = import_data_from_csv(filename)
        for row in data:
            self.task_manager.create_task(
                name=row.get('name', '导入任务'),
                numbers=row.get('numbers', '').split(','),
                subject=row.get('subject', ''),
                content=row.get('content', '')
            )

    def export_tasks(self):
        """导出任务"""
        from tkinter import filedialog

        filename = filedialog.asksaveasfilename(
            title="保存任务文件",
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("CSV文件", "*.csv")]
        )

        if filename:
            try:
                if filename.endswith('.json'):
                    self._export_tasks_to_json(filename)
                elif filename.endswith('.csv'):
                    self._export_tasks_to_csv(filename)

                messagebox.showinfo("成功", "任务导出成功")
            except Exception as e:
                messagebox.showerror("错误", f"导出任务失败: {e}")

    def _export_tasks_to_json(self, filename):
        """导出任务到JSON文件"""
        import json

        tasks_data = []
        for task in self.task_manager.tasks.values():
            tasks_data.append({
                'name': task['name'],
                'numbers': task['numbers'],
                'subject': task['subject'],
                'content': task['content'],
                'created_time': task['created_time']
            })

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(tasks_data, f, ensure_ascii=False, indent=2)

    def _export_tasks_to_csv(self, filename):
        """导出任务到CSV文件"""
        from core.utils import export_data_to_csv

        tasks_data = []
        for task in self.task_manager.tasks.values():
            tasks_data.append({
                'name': task['name'],
                'numbers': ','.join(task['numbers']),
                'subject': task['subject'],
                'content': task['content'],
                'success': task['success'],
                'failed': task['failed'],
                'total': task['total'],
                'created_time': task['created_time']
            })

        headers = ['name', 'numbers', 'subject', 'content', 'success', 'failed', 'total', 'created_time']
        export_data_to_csv(tasks_data, filename, headers)

    def scan_ports(self):
        """重新扫描端口"""
        try:
            self.port_manager.scan_ports()
            self.port_panel.update_display()
            port_count = len(self.port_manager.ports)
            messagebox.showinfo("端口扫描", f"扫描完成，发现 {port_count} 个端口")
        except Exception as e:
            messagebox.showerror("错误", f"端口扫描失败: {e}")

    def clean_logs(self):
        """清理日志"""
        try:
            import os
            import glob

            log_files = glob.glob('logs/*.log')
            removed_count = 0

            for log_file in log_files:
                try:
                    os.remove(log_file)
                    removed_count += 1
                except:
                    pass

            messagebox.showinfo("清理日志", f"已清理 {removed_count} 个日志文件")
        except Exception as e:
            messagebox.showerror("错误", f"清理日志失败: {e}")

    def show_help(self):
        """显示帮助"""
        help_text = """
使用说明：

1. 端口管理：
   - 系统会自动扫描可用的串口
   - 点击端口状态按钮可启动/停止端口
   - 使用选择框可以批量操作端口

2. 任务管理：
   - 点击"添加任务"创建新的短信发送任务
   - 右键点击任务可进行操作（开始/停止/测试/删除）
   - 任务会自动分配到可用端口执行

3. 配置设置：
   - 在"工具"菜单中打开"系统配置"
   - 可以设置发送间隔、卡片更换等参数

4. 注意事项：
   - 仅供测试研究使用
   - 请确保遵守相关法律法规
        """

        help_window = tk.Toplevel(self.root)
        help_window.title("使用说明")
        help_window.geometry("500x400")
        help_window.resizable(False, False)

        text_widget = tk.Text(help_window, wrap=tk.WORD, padx=20, pady=20)
        text_widget.pack(fill='both', expand=True)
        text_widget.insert('1.0', help_text.strip())
        text_widget.config(state='disabled')