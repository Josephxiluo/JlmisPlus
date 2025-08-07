"""
集成认证的现代化登录窗口 - CustomTkinter版本 (修复DPI问题版)
Enhanced modern login window with real authentication - CustomTkinter version (DPI Fixed)
"""
import customtkinter as ctk
from tkinter import messagebox
from typing import Optional, Dict, Any
import sys
import os
import threading

# 修复CustomTkinter的DPI缩放问题
def fix_ctk_dpi_issues():
    """修复CustomTkinter的DPI相关问题"""
    try:
        # 禁用DPI感知
        import tkinter as tk
        try:
            # 方法1: 设置固定的缩放比例
            ctk.set_widget_scaling(1.0)
            ctk.set_window_scaling(1.0)
        except:
            pass

        try:
            # 方法2: 设置tkinter的缩放
            test_root = tk.Tk()
            test_root.tk.call('tk', 'scaling', 1.0)
            test_root.withdraw()
            test_root.destroy()
        except:
            pass

        try:
            # 方法3: 设置外观模式和主题
            ctk.set_appearance_mode("light")
            ctk.set_default_color_theme("blue")
        except:
            pass

    except Exception as e:
        print(f"DPI修复警告: {e}")

# 执行DPI修复
fix_ctk_dpi_issues()

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from services.auth_service import auth_service, get_mac_address
    from config.logging_config import get_logger

    logger = get_logger('ui.login')
    REAL_AUTH_AVAILABLE = True

except ImportError as e:
    print(f"警告: 认证服务导入失败: {e}")
    REAL_AUTH_AVAILABLE = False

    # 创建模拟认证函数
    def get_mac_address():
        import uuid
        try:
            mac = uuid.getnode()
            return ':'.join(('%012X' % mac)[i:i+2] for i in range(0, 12, 2))
        except:
            return "00:00:00:00:00:00"

    class MockAuthService:
        def authenticate_user(self, username, password, mac_address=None):
            # 模拟认证逻辑
            if username == "operator001" and password == "123456":
                return {
                    'success': True,
                    'message': '登录成功',
                    'user_data': {
                        'operators_id': 1,
                        'operators_username': username,
                        'operators_real_name': '测试操作员',
                        'operators_total_credits': 10000,
                        'operators_used_credits': 0,
                        'operators_available_credits': 10000,
                        'channel_users_id': 1
                    }
                }
            else:
                return {
                    'success': False,
                    'message': '用户名或密码错误',
                    'error_code': 'INVALID_CREDENTIALS'
                }

    auth_service = MockAuthService()

    import logging
    logger = logging.getLogger('ui.login')

try:
    from ui.styles import get_color, get_font, get_spacing
except ImportError:
    # 如果导入失败，使用基础配置
    def get_color(name):
        colors = {
            'primary': '#FF7043',
            'background': '#FAFAFA',
            'card_bg': '#FFFFFF',
            'text': '#212121',
            'success': '#4CAF50',
            'warning': '#FF9800',
            'danger': '#F44336'
        }
        return colors.get(name, '#000000')

    def get_font(name):
        fonts = {
            'title': ('Microsoft YaHei', 18, 'bold'),
            'default': ('Microsoft YaHei', 12),
            'small': ('Microsoft YaHei', 10),
            'button': ('Microsoft YaHei', 12, 'bold')
        }
        return fonts.get(name, ('Microsoft YaHei', 12))

    def get_spacing(name):
        return {'xs': 4, 'sm': 8, 'md': 16, 'lg': 24, 'xl': 32}.get(name, 8)


class EnhancedLoginWindow:
    """集成认证的现代化登录窗口类 - 修复DPI问题版"""

    def __init__(self):
        """初始化登录窗口"""
        self.root = None
        self.username_var = None
        self.password_var = None
        self.remember_var = None
        self.result = None

        # 控制元素
        self.login_button = None
        self.status_label = None
        self.mac_info_label = None

        # 状态标志
        self.is_authenticating = False
        self.mac_address = ""
        self._window_closed = False

        # 获取当前机器的MAC地址
        try:
            self.mac_address = get_mac_address()
            if logger:
                logger.info(f"当前机器MAC地址: {self.mac_address}")
        except Exception as e:
            if logger:
                logger.error(f"获取MAC地址失败: {e}")
            self.mac_address = "00:00:00:00:00:00"

    def show(self) -> Optional[Dict[str, Any]]:
        """显示现代化登录窗口"""
        try:
            # 初始化认证服务
            if REAL_AUTH_AVAILABLE:
                auth_service.initialize()

            # 创建主窗口 - 使用更安全的方式
            self.root = ctk.CTk()
            self.root.title("用户登录 - JlmisPlus 猫池短信系统")
            self.root.geometry("450x650")
            self.root.resizable(False, False)

            try:
                self.root.configure(fg_color=get_color('background'))
            except:
                self.root.configure(fg_color='#FAFAFA')

            # 设置窗口关闭协议
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

            # 居中显示
            self.center_window()

            # 延迟创建界面组件，避免DPI问题
            self.root.after(50, self.create_widgets_safe)

            # 运行窗口
            self.root.mainloop()

            return self.result

        except Exception as e:
            if logger:
                logger.error(f"显示登录窗口失败: {e}")
            else:
                print(f"显示登录窗口失败: {e}")

            try:
                if self.root:
                    messagebox.showerror("错误", f"登录窗口初始化失败：{str(e)}")
            except:
                print(f"登录窗口初始化失败：{str(e)}")
            return None

    def create_widgets_safe(self):
        """安全地创建界面组件"""
        try:
            # 创建现代化界面
            self.create_widgets()

            # 延迟绑定事件，避免冲突
            self.root.after(100, self.bind_events)

        except Exception as e:
            if logger:
                logger.error(f"创建界面组件失败: {e}")
            else:
                print(f"创建界面组件失败: {e}")

    def bind_events(self):
        """绑定键盘和其他事件"""
        try:
            if self._window_closed:
                return

            # 绑定键盘事件
            self.root.bind('<Return>', lambda e: self.login())
            self.root.bind('<Escape>', lambda e: self.cancel_login())

            # 设置焦点
            if self.username_var and self.username_var.get():
                if self.password_entry:
                    self.password_entry.focus_set()
            else:
                if self.username_entry:
                    self.username_entry.focus_set()

        except Exception as e:
            if logger:
                logger.error(f"绑定事件失败: {e}")

    def center_window(self):
        """窗口居中"""
        try:
            self.root.update_idletasks()
            width = self.root.winfo_width()
            height = self.root.winfo_height()
            x = (self.root.winfo_screenwidth() // 2) - (width // 2)
            y = (self.root.winfo_screenheight() // 2) - (height // 2)
            self.root.geometry(f"{width}x{height}+{x}+{y}")
        except Exception as e:
            if logger:
                logger.warning(f"窗口居中失败: {e}")

    def create_widgets(self):
        """创建现代化界面组件"""
        # 主容器
        main_container = ctk.CTkFrame(self.root, fg_color='transparent')
        main_container.pack(fill='both', expand=True, padx=30, pady=30)

        # 登录卡片
        try:
            login_card = ctk.CTkFrame(
                main_container,
                fg_color=get_color('card_bg'),
                corner_radius=15,
                border_width=1,
                border_color='#E0E0E0'
            )
        except:
            login_card = ctk.CTkFrame(
                main_container,
                fg_color='white',
                corner_radius=15
            )

        login_card.pack(fill='both', expand=True)

        # 卡片内容
        self.create_card_content(login_card)

    def create_card_content(self, parent):
        """创建卡片内容"""
        content_frame = ctk.CTkFrame(parent, fg_color='transparent')
        content_frame.pack(fill='both', expand=True, padx=25, pady=25)

        # Logo和标题
        self.create_header(content_frame)

        # 系统信息
        self.create_system_info(content_frame)

        # 表单
        self.create_form(content_frame)

        # 状态显示
        self.create_status_display(content_frame)

        # 按钮
        self.create_buttons(content_frame)

        # 底部信息
        self.create_footer(content_frame)

    def create_header(self, parent):
        """创建头部"""
        header_frame = ctk.CTkFrame(parent, fg_color='transparent')
        header_frame.pack(fill='x', pady=(0, 20))

        # 主标题
        try:
            title_label = ctk.CTkLabel(
                header_frame,
                text="JlmisPlus 猫池短信系统",
                font=get_font('title'),
                text_color=get_color('text')
            )
        except:
            title_label = ctk.CTkLabel(
                header_frame,
                text="JlmisPlus 猫池短信系统",
                font=('Microsoft YaHei', 18, 'bold'),
                text_color='#212121'
            )
        title_label.pack(pady=(10, 5))

    def create_system_info(self, parent):
        """创建系统信息显示"""
        try:
            info_frame = ctk.CTkFrame(
                parent,
                fg_color='#F5F5F5',
                corner_radius=8
            )
            info_frame.pack(fill='x', pady=(0, 20))

            # MAC地址信息
            mac_display = self.mac_address[:17] if len(self.mac_address) > 17 else self.mac_address
            self.mac_info_label = ctk.CTkLabel(
                info_frame,
                text=f"MAC地址: {mac_display}",
                font=('Microsoft YaHei', 9),
                text_color='#666666'
            )
            self.mac_info_label.pack(pady=5)

            # 认证状态信息
            auth_status = "✅ 真实认证" if REAL_AUTH_AVAILABLE else "⚠️ 模拟认证"
            try:
                auth_color = get_color('success') if REAL_AUTH_AVAILABLE else get_color('warning')
            except:
                auth_color = '#4CAF50' if REAL_AUTH_AVAILABLE else '#FF9800'

            auth_status_label = ctk.CTkLabel(
                info_frame,
                text=auth_status,
                font=('Microsoft YaHei', 9),
                text_color=auth_color
            )
            auth_status_label.pack(pady=(0, 5))
        except Exception as e:
            if logger:
                logger.warning(f"创建系统信息失败: {e}")

    def create_form(self, parent):
        """创建表单"""
        form_frame = ctk.CTkFrame(parent, fg_color='transparent')
        form_frame.pack(fill='x', pady=(0, 15))

        # 用户名
        username_label = ctk.CTkLabel(
            form_frame,
            text="👤 用户名",
            font=('Microsoft YaHei', 12),
            text_color='#212121'
        )
        username_label.pack(anchor='w', pady=(0, 5))

        self.username_var = ctk.StringVar(value="operator001")
        self.username_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text="请输入渠道操作用户名",
            textvariable=self.username_var,
            height=40,
            corner_radius=8,
            border_width=2,
            border_color='#E0E0E0',
            font=('Microsoft YaHei', 12)
        )
        self.username_entry.pack(fill='x', pady=(0, 15))

        # 密码
        password_label = ctk.CTkLabel(
            form_frame,
            text="🔒 密码",
            font=('Microsoft YaHei', 12),
            text_color='#212121'
        )
        password_label.pack(anchor='w', pady=(0, 5))

        self.password_var = ctk.StringVar(value="123456")
        self.password_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text="请输入密码",
            textvariable=self.password_var,
            show="*",
            height=40,
            corner_radius=8,
            border_width=2,
            border_color='#E0E0E0',
            font=('Microsoft YaHei', 12)
        )
        self.password_entry.pack(fill='x')

    def create_status_display(self, parent):
        """创建状态显示区域"""
        status_frame = ctk.CTkFrame(parent, fg_color='transparent')
        status_frame.pack(fill='x', pady=(15, 0))

        # 状态标签
        try:
            self.status_label = ctk.CTkLabel(
                status_frame,
                text="",
                font=('Microsoft YaHei', 10),
                text_color=get_color('text'),
                wraplength=350
            )
        except:
            self.status_label = ctk.CTkLabel(
                status_frame,
                text="",
                font=('Microsoft YaHei', 10),
                text_color='#212121'
            )
        self.status_label.pack()

    def create_buttons(self, parent):
        """创建按钮"""
        button_frame = ctk.CTkFrame(parent, fg_color='transparent')
        button_frame.pack(fill='x', pady=(5, 0))

        # 登录按钮
        try:
            self.login_button = ctk.CTkButton(
                button_frame,
                text="🚀 登录系统",
                command=self.login,
                height=45,
                corner_radius=10,
                fg_color=get_color('primary'),
                hover_color='#FF5722',
                font=get_font('button')
            )
        except:
            self.login_button = ctk.CTkButton(
                button_frame,
                text="🚀 登录系统",
                command=self.login,
                height=45,
                corner_radius=10,
                fg_color='#FF7043',
                hover_color='#FF5722',
                font=('Microsoft YaHei', 12, 'bold')
            )
        self.login_button.pack(fill='x', pady=(0, 10))

        # 选项区域
        options_frame = ctk.CTkFrame(button_frame, fg_color='transparent')
        options_frame.pack(fill='x', pady=(15, 0))

        self.remember_var = ctk.BooleanVar(value=True)
        remember_check = ctk.CTkCheckBox(
            options_frame,
            text="记住用户名",
            variable=self.remember_var,
            font=('Microsoft YaHei', 10),
            text_color='#757575'
        )
        remember_check.pack(side='left')

    def create_footer(self, parent):
        """创建底部信息"""
        footer_frame = ctk.CTkFrame(parent, fg_color='transparent')
        footer_frame.pack(side='bottom', fill='x', pady=(20, 0))

        # 版本信息
        version_label = ctk.CTkLabel(
            footer_frame,
            text="版本 1.015 - ⚠️ 仅供技术研究学习使用，严禁用于违法违规用途",
            font=('Microsoft YaHei', 9),
            text_color='#9E9E9E'
        )
        version_label.pack()

    def update_status(self, message: str, status_type: str = 'info'):
        """更新状态显示"""
        try:
            if not self.status_label or self._window_closed:
                return

            color_map = {
                'info': '#2196F3',
                'success': get_color('success') if 'get_color' in globals() else '#4CAF50',
                'warning': get_color('warning') if 'get_color' in globals() else '#FF9800',
                'error': get_color('danger') if 'get_color' in globals() else '#F44336'
            }

            color = color_map.get(status_type, '#2196F3')
            self.status_label.configure(text=message, text_color=color)

            # 安全地更新界面
            if self.root and not self._window_closed:
                self.root.update_idletasks()

        except Exception as e:
            print(f"更新状态显示失败: {e}")

    def set_login_button_state(self, enabled: bool):
        """设置登录按钮状态"""
        try:
            if self.login_button and not self._window_closed:
                if enabled:
                    try:
                        primary_color = get_color('primary')
                    except:
                        primary_color = '#FF7043'

                    self.login_button.configure(
                        state='normal',
                        text="🚀 登录系统",
                        fg_color=primary_color
                    )
                else:
                    self.login_button.configure(
                        state='disabled',
                        text="🔄 认证中...",
                        fg_color='#BDBDBD'
                    )
        except Exception as e:
            print(f"设置按钮状态失败: {e}")

    def login(self):
        """登录处理 - 集成真实认证"""
        if self.is_authenticating or self._window_closed:
            return

        username = self.username_var.get().strip()
        password = self.password_var.get().strip()

        # 基本验证
        if not username or not password:
            self.update_status("❌ 请输入用户名和密码", 'error')
            return

        # 开始认证过程
        self.is_authenticating = True
        self.set_login_button_state(False)
        self.update_status("🔍 正在验证用户信息...", 'info')

        # 在后台线程进行认证，避免界面冻结
        auth_thread = threading.Thread(target=self._authenticate_user, args=(username, password))
        auth_thread.daemon = True
        auth_thread.start()

    def _authenticate_user(self, username: str, password: str):
        """后台认证处理"""
        try:
            if self._window_closed:
                return

            # 显示MAC地址验证状态
            if self.root and not self._window_closed:
                self.root.after(0, lambda: self.update_status(f"🔐 验证设备授权 (MAC: {self.mac_address[:17]})", 'info'))

            # 调用认证服务
            auth_result = auth_service.authenticate_user(username, password, self.mac_address)

            # 在主线程中处理认证结果
            if self.root and not self._window_closed:
                self.root.after(0, lambda: self._handle_auth_result(auth_result, username))

        except Exception as e:
            if logger:
                logger.error(f"认证过程异常: {e}")
            error_message = f"❌ 认证过程发生异常: {str(e)}"
            if self.root and not self._window_closed:
                self.root.after(0, lambda: self._handle_auth_error(error_message))

    def _handle_auth_result(self, auth_result: Dict[str, Any], username: str):
        """处理认证结果"""
        try:
            if self._window_closed:
                return

            self.is_authenticating = False
            self.set_login_button_state(True)

            if auth_result['success']:
                # 认证成功
                user_data = auth_result.get('user_data', {})

                # 显示成功信息
                real_name = user_data.get('operators_real_name', username)
                balance = user_data.get('operators_available_credits', 0)

                self.update_status(f"✅ 登录成功！欢迎 {real_name}，余额: {balance} 积分", 'success')

                # 保存认证结果
                self.result = user_data

                # 延迟关闭窗口，让用户看到成功信息
                if self.root and not self._window_closed:
                    self.root.after(1500, self._close_window)

            else:
                # 认证失败
                error_code = auth_result.get('error_code', '')
                message = auth_result.get('message', '认证失败')

                # 根据错误类型设置不同的显示
                if error_code == 'INVALID_CREDENTIALS':
                    self.update_status("❌ 用户名或密码错误，请检查后重试", 'error')
                elif error_code == 'MAC_ADDRESS_NOT_AUTHORIZED':
                    self.update_status(f"🚫 设备未授权\n{message}", 'error')
                elif error_code == 'ACCOUNT_DISABLED':
                    self.update_status("⛔ 账户已被禁用，请联系管理员", 'error')
                elif error_code == 'ACCOUNT_SUSPENDED':
                    self.update_status("⏸️ 账户已被暂停，请联系管理员", 'error')
                else:
                    self.update_status(f"❌ {message}", 'error')

                # 清空密码
                if self.password_var and not self._window_closed:
                    self.password_var.set("")
                    if self.password_entry:
                        self.password_entry.focus_set()

        except Exception as e:
            if logger:
                logger.error(f"处理认证结果异常: {e}")
            self.update_status(f"❌ 处理认证结果异常: {str(e)}", 'error')
            self.is_authenticating = False
            self.set_login_button_state(True)

    def _handle_auth_error(self, error_message: str):
        """处理认证错误"""
        self.update_status(error_message, 'error')
        self.is_authenticating = False
        self.set_login_button_state(True)

    def _close_window(self):
        """关闭窗口"""
        try:
            if self.root and not self._window_closed:
                self._window_closed = True
                self.root.quit()
                self.root.destroy()
        except Exception as e:
            print(f"关闭窗口失败: {e}")

    def cancel_login(self):
        """取消登录"""
        if self.is_authenticating:
            self.update_status("⏹️ 正在取消认证...", 'warning')
            return

        self.result = None
        self._close_window()

    def on_closing(self):
        """窗口关闭事件处理"""
        if self.is_authenticating:
            self.update_status("⏹️ 正在取消认证...", 'warning')
            return

        self._close_window()

    def destroy(self):
        """销毁窗口"""
        self._window_closed = True
        if self.root:
            try:
                self.root.destroy()
            except:
                pass


# 为了保持兼容性，创建别名
LoginWindow = EnhancedLoginWindow


def main():
    """测试集成认证的登录窗口"""
    print("启动集成认证的登录窗口测试")
    print(f"认证服务可用: {REAL_AUTH_AVAILABLE}")

    login_window = EnhancedLoginWindow()
    result = login_window.show()

    if result:
        print("登录成功！用户信息：")
        for key, value in result.items():
            print(f"  {key}: {value}")
    else:
        print("登录取消或失败")


if __name__ == '__main__':
    main()