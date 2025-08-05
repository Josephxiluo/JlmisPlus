"""
主窗口 - 最小化版本
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any

class MainWindow:
    """主窗口类"""

    def __init__(self, user_info: Dict[str, Any]):
        """初始化主窗口"""
        self.user_info = user_info
        self.root = None

    def show(self):
        """显示主窗口"""
        self.root = tk.Tk()
        self.root.title(f"猫池短信系统 - {self.user_info.get('operators_real_name', '用户')}")
        self.root.geometry("1200x800")

        # 居中显示
        self.center_window()

        # 创建界面
        self.create_widgets()

        # 运行窗口
        self.root.mainloop()

    def center_window(self):
        """窗口居中"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def create_widgets(self):
        """创建界面组件"""
        # 状态栏
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(status_frame, text="猫池短信系统", font=("Microsoft YaHei", 12, "bold")).pack(side=tk.LEFT)

        user_label = ttk.Label(status_frame, text=f"用户: {self.user_info.get('operators_username', '')}")
        user_label.pack(side=tk.LEFT, padx=(20, 0))

        credit_label = ttk.Label(status_frame, text=f"余额: 积分{self.user_info.get('operators_available_credits', 0)}")
        credit_label.pack(side=tk.RIGHT)

        # 分隔线
        ttk.Separator(self.root, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10)

        # 主内容区域
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 左侧任务管理
        left_frame = ttk.LabelFrame(main_frame, text="任务管理", padding="10")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # 任务控制按钮
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(btn_frame, text="停止发送").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="添加任务", command=self.add_task).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="更多").pack(side=tk.LEFT)

        # 任务列表
        task_tree = ttk.Treeview(left_frame, columns=("progress", "success", "failed", "status"), show="tree headings")
        task_tree.heading("#0", text="任务名称")
        task_tree.heading("progress", text="进度")
        task_tree.heading("success", text="成功")
        task_tree.heading("failed", text="失败") 
        task_tree.heading("status", text="状态")
        task_tree.pack(fill=tk.BOTH, expand=True)

        # 右侧端口管理
        right_frame = ttk.LabelFrame(main_frame, text="端口管理", padding="10")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        # 端口控制按钮
        port_btn_frame = ttk.Frame(right_frame)
        port_btn_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(port_btn_frame, text="全选").pack(side=tk.LEFT, padx=(0, 2))
        ttk.Button(port_btn_frame, text="反选").pack(side=tk.LEFT, padx=(0, 2))
        ttk.Button(port_btn_frame, text="选项").pack(side=tk.LEFT, padx=(0, 2))
        ttk.Button(port_btn_frame, text="启动").pack(side=tk.LEFT, padx=(0, 2))
        ttk.Button(port_btn_frame, text="停止").pack(side=tk.LEFT)

        # 端口状态显示
        port_text = tk.Text(right_frame, height=20, state=tk.DISABLED)
        port_text.pack(fill=tk.BOTH, expand=True)

        # 插入示例端口信息
        port_text.config(state=tk.NORMAL)
        port_text.insert(tk.END, "端口扫描中...\n")
        port_text.insert(tk.END, "COM1  中国移动  60  0  可用\n")
        port_text.insert(tk.END, "COM2  中国联通  60  0  可用\n")
        port_text.insert(tk.END, "COM3  中国电信  60  0  离线\n")
        port_text.config(state=tk.DISABLED)

    def add_task(self):
        """添加任务"""
        messagebox.showinfo("提示", "添加任务功能正在开发中...")

    def destroy(self):
        """销毁窗口"""
        if self.root:
            try:
                self.root.quit()
                self.root.destroy()
            except:
                pass