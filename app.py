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

# 检查Python版本
if sys.version_info < (3, 7):
    print("错误：需要Python 3.7或更高版本")
    sys.exit(1)

try:
    import tkinter as tk
    from tkinter import messagebox
except ImportError:
    print("错误：未找到tkinter模块，请安装Python的tkinter支持")
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
        self.services_initialized = False

    def initialize(self):
        """初始化应用组件"""
        try:
            # 首先初始化基本配置
            if not self._init_basic_config():
                return False

            # 初始化日志系统
            if not self._init_logging():
                return False

            self.logger.info("=" * 50)
            self.logger.info("猫池短信系统启动")
            self.logger.info("=" * 50)

            # 创建必要的目录
            self._create_directories()

            # 初始化服务（延迟加载，避免循环导入）
            if not self._init_services():
                self.logger.warning("部分服务初始化失败，某些功能可能不可用")
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

    def _init_basic_config(self):
        """初始化基本配置"""
        try:
            from config.settings import settings
            self.settings = settings
            return True
        except ImportError as e:
            print(f"无法加载配置模块: {e}")
            print("请检查config目录和依赖库是否正确安装")
            return False

    def _init_logging(self):
        """初始化日志系统"""
        try:
            from config.logging_config import setup_logging, get_logger
            setup_logging()
            self.logger = get_logger('app')
            return True
        except ImportError as e:
            print(f"无法加载日志模块: {e}")
            # 创建简单的控制台日志
            import logging
            logging.basicConfig(level=logging.INFO)
            self.logger = logging.getLogger('app')
            return True
        except Exception as e:
            print(f"日志系统初始化失败: {e}")
            return False

    def _create_directories(self):
        """创建必要的目录"""
        directories = [
            'temp',
            'temp/uploads',
            'temp/exports',
            'temp/logs'
        ]

        for directory in directories:
            dir_path = project_root / directory
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                self.logger.warning(f"创建目录 {directory} 失败: {e}")

        self.logger.info("目录结构检查完成")

    def _init_services(self):
        """初始化服务（延迟加载）"""
        try:
            # 延迟导入服务模块，避免循环导入
            from services import initialize_all_services
            service_results = initialize_all_services()

            # 检查服务初始化结果
            failed_services = [name for name, success in service_results.items() if not success]
            if failed_services:
                self.logger.warning(f"以下服务初始化失败: {failed_services}")
                return False
            else:
                self.services_initialized = True
                return True

        except ImportError as e:
            self.logger.error(f"无法导入服务模块: {e}")
            self.logger.error("应用将以有限功能模式运行")
            return False
        except Exception as e:
            self.logger.error(f"服务初始化异常: {e}")
            return False

    def show_login(self):
        """显示登录窗口"""
        try:
            # 延迟导入UI模块
            from ui.login_window import LoginWindow

            self.logger.info("显示登录窗口")
            self.login_window = LoginWindow()
            self.user_info = self.login_window.show()

            if self.user_info:
                self.logger.info(f"用户登录成功: {self.user_info.get('username', 'Unknown')}")
                return True
            else:
                self.logger.info("用户取消登录")
                return False

        except ImportError as e:
            error_msg = f"无法加载登录窗口: {str(e)}"
            self.logger.error(error_msg)
            messagebox.showerror("模块错误", error_msg)
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
            # 延迟导入UI模块
            from ui.main_window import MainWindow

            self.logger.info("显示主窗口")
            self.main_window = MainWindow(self.user_info)
            self.main_window.show()

        except ImportError as e:
            error_msg = f"无法加载主窗口: {str(e)}"
            self.logger.error(error_msg)
            messagebox.showerror("模块错误", error_msg)
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

            # 关闭服务
            if self.services_initialized:
                try:
                    from services import shutdown_all_services
                    shutdown_all_services()
                except Exception as e:
                    self.logger.error(f"关闭服务失败: {e}")

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
                messagebox.showerror("初始化失败", "应用初始化失败，请检查配置和依赖")
                return False

            # 显示登录窗口
            if not self.show_login():
                return False

            # 显示主窗口
            self.show_main_window()

            return True

        except KeyboardInterrupt:
            if self.logger:
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
        'pathlib',
        'datetime',
        'threading',
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
        'ui',
        'ui/components',
        'ui/dialogs'
    ]

    for directory in required_dirs:
        dir_path = project_root / directory
        if not dir_path.exists():
            errors.append(f"缺少目录: {directory}")

    # 检查核心配置文件
    required_files = [
        'config/settings.py',
        'config/logging_config.py',
        'ui/login_window.py',
        'ui/main_window.py'
    ]

    for file_path in required_files:
        file_full_path = project_root / file_path
        if not file_full_path.exists():
            errors.append(f"缺少核心文件: {file_path}")

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