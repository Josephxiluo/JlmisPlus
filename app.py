#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
猫池短信系统 - 主程序入口
SMS Pool System - Main Application Entry Point
"""

import sys
import os
import traceback
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 设置工作目录
os.chdir(project_root)

try:
    import tkinter as tk
    from tkinter import messagebox
except ImportError:
    print("错误：未找到tkinter模块，请安装Python的tkinter支持")
    sys.exit(1)

try:
    # 导入配置模块
    from config.settings import Settings
    from config.logging_config import setup_logging, get_logger

    # 导入UI模块
    from ui.login_window import LoginWindow
    from ui.main_window import MainWindow

    # 导入服务模块
    from services import initialize_all_services, shutdown_all_services

except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请检查项目目录结构和依赖库是否正确安装")
    traceback.print_exc()
    sys.exit(1)


class Application:
    """主应用类"""

    def __init__(self):
        """初始化应用"""
        self.logger = None
        self.settings = None
        self.login_window = None
        self.main_window = None
        self.user_info = None

    def initialize(self):
        """初始化应用组件"""
        try:
            # 设置日志
            setup_logging()
            self.logger = get_logger('app')
            self.logger.info("=" * 50)
            self.logger.info("猫池短信系统启动")
            self.logger.info("=" * 50)

            # 加载设置
            self.settings = Settings()
            self.logger.info("配置加载完成")

            # 创建必要的目录
            self.create_directories()

            # 初始化服务
            self.logger.info("正在初始化服务...")
            service_results = initialize_all_services()

            # 检查服务初始化结果
            failed_services = [name for name, success in service_results.items() if not success]
            if failed_services:
                self.logger.warning(f"以下服务初始化失败: {failed_services}")
            else:
                self.logger.info("所有服务初始化成功")

            return True

        except Exception as e:
            error_msg = f"应用初始化失败: {str(e)}"
            if self.logger:
                self.logger.error(error_msg)
                self.logger.error(traceback.format_exc())
            else:
                print(error_msg)
                traceback.print_exc()
            return False

    def create_directories(self):
        """创建必要的目录"""
        directories = [
            'temp',
            'temp/uploads',
            'temp/exports',
            'temp/logs'
        ]

        for directory in directories:
            dir_path = project_root / directory
            dir_path.mkdir(parents=True, exist_ok=True)

        self.logger.info("目录结构检查完成")

    def show_login(self):
        """显示登录窗口"""
        try:
            self.logger.info("显示登录窗口")
            self.login_window = LoginWindow()
            self.user_info = self.login_window.show()

            if self.user_info:
                self.logger.info(f"用户登录成功: {self.user_info.get('username', 'Unknown')}")
                return True
            else:
                self.logger.info("用户取消登录")
                return False

        except Exception as e:
            error_msg = f"登录过程出错: {str(e)}"
            self.logger.error(error_msg)
            self.logger.error(traceback.format_exc())
            messagebox.showerror("登录错误", error_msg)
            return False
        finally:
            if self.login_window:
                self.login_window.destroy()
                self.login_window = None

    def show_main_window(self):
        """显示主窗口"""
        try:
            self.logger.info("显示主窗口")
            self.main_window = MainWindow(self.user_info)
            self.main_window.show()

        except Exception as e:
            error_msg = f"主窗口运行出错: {str(e)}"
            self.logger.error(error_msg)
            self.logger.error(traceback.format_exc())
            messagebox.showerror("运行错误", error_msg)
        finally:
            if self.main_window:
                self.main_window.destroy()
                self.main_window = None

    def cleanup(self):
        """清理资源"""
        try:
            self.logger.info("正在清理应用资源...")

            # 关闭所有服务
            shutdown_all_services()

            # 清理窗口资源
            if self.main_window:
                self.main_window.destroy()

            if self.login_window:
                self.login_window.destroy()

            self.logger.info("应用资源清理完成")
            self.logger.info("=" * 50)
            self.logger.info("猫池短信系统退出")
            self.logger.info("=" * 50)

        except Exception as e:
            if self.logger:
                self.logger.error(f"清理资源时出错: {str(e)}")
            else:
                print(f"清理资源时出错: {str(e)}")

    def run(self):
        """运行应用"""
        try:
            # 初始化应用
            if not self.initialize():
                return False

            # 显示登录窗口
            if not self.show_login():
                return False

            # 显示主窗口
            self.show_main_window()

            return True

        except KeyboardInterrupt:
            self.logger.info("用户中断程序")
            return False

        except Exception as e:
            error_msg = f"应用运行时出现未处理的异常: {str(e)}"
            if self.logger:
                self.logger.error(error_msg)
                self.logger.error(traceback.format_exc())
            else:
                print(error_msg)
                traceback.print_exc()
            return False

        finally:
            self.cleanup()


def check_environment():
    """检查运行环境"""
    errors = []

    # 检查Python版本
    if sys.version_info < (3, 7):
        errors.append("Python版本需要3.7或更高")

    # 检查必要模块
    required_modules = [
        'tkinter',
        'sqlite3',
        'threading',
        'datetime',
        'pathlib',
        'json',
        'uuid'
    ]

    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            errors.append(f"缺少必要模块: {module}")

    # 检查项目目录结构
    required_dirs = [
        'config',
        'database',
        'models',
        'services',
        'core',
        'ui',
        'ui/components',
        'ui/dialogs',
        'ui/styles'
    ]

    for directory in required_dirs:
        dir_path = project_root / directory
        if not dir_path.exists():
            errors.append(f"缺少目录: {directory}")

    return errors


def main():
    """主函数"""
    print("猫池短信系统 v1.0.0")
    print("=" * 50)

    # 检查运行环境
    print("正在检查运行环境...")
    env_errors = check_environment()

    if env_errors:
        print("环境检查失败:")
        for error in env_errors:
            print(f"  - {error}")
        print("\n请修复上述问题后重新运行程序")
        input("按回车键退出...")
        return 1

    print("环境检查通过")

    # 创建并运行应用
    app = Application()

    try:
        success = app.run()
        return 0 if success else 1

    except Exception as e:
        print(f"程序运行时发生严重错误: {str(e)}")
        traceback.print_exc()
        input("按回车键退出...")
        return 1


if __name__ == '__main__':
    # 设置异常处理
    def handle_exception(exc_type, exc_value, exc_traceback):
        """全局异常处理"""
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        error_msg = "程序发生未捕获的异常:\n"
        error_msg += ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))

        print(error_msg)

        # 尝试显示错误对话框
        try:
            root = tk.Tk()
            root.withdraw()  # 隐藏主窗口
            messagebox.showerror("严重错误", f"程序发生严重错误:\n{exc_value}\n\n请查看控制台获取详细信息")
            root.destroy()
        except:
            pass

    sys.excepthook = handle_exception

    # 运行程序
    exit_code = main()
    sys.exit(exit_code)