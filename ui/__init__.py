"""
UI模块 - 最小化版本
"""

# 延迟导入，避免循环导入问题
def get_login_window():
    """获取登录窗口类"""
    try:
        from .login_window import LoginWindow
        return LoginWindow
    except ImportError as e:
        print(f"警告: 无法导入登录窗口: {e}")
        return None

def get_main_window():
    """获取主窗口类"""
    try:
        from .main_window import MainWindow
        return MainWindow
    except ImportError as e:
        print(f"警告: 无法导入主窗口: {e}")
        return None

__all__ = ['get_login_window', 'get_main_window']
