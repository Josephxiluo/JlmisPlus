"""
猫池短信管理系统 - 主程序入口
"""
import tkinter as tk
from ui.main_window import SmsPoolManager


def main():
    """主函数"""
    root = tk.Tk()

    # 设置程序图标（如果有的话）
    try:
        # root.iconbitmap('icon.ico')  # 如果有图标文件
        pass
    except:
        pass

    app = SmsPoolManager(root)

    # 加载配置
    app.load_config()

    # 启动后台任务
    app.start_background_tasks()

    # 设置程序关闭事件
    root.protocol("WM_DELETE_WINDOW", app.on_closing)

    # 启动GUI主循环
    root.mainloop()


if __name__ == "__main__":
    main()