"""
短信发送实现模块 - 兼容数据库版本
"""
import time
import threading
from datetime import datetime
from config.settings import settings


class MessageSender:
    """短信发送器 - 数据库兼容版本"""

    def __init__(self, port_manager, db_manager=None):
        self.port_manager = port_manager
        self.db_manager = db_manager
        self.send_lock = threading.Lock()
        self.last_send_time = {}  # 记录每个端口最后发送时间

    def send_message(self, port_name, phone_number, message, subject=""):
        """发送单条短信"""
        with self.send_lock:
            # 检查发送间隔
            current_time = time.time()
            last_time = self.last_send_time.get(port_name, 0)
            interval = settings.get('send_interval', 1000) / 1000.0  # 转换为秒

            if current_time - last_time < interval:
                time.sleep(interval - (current_time - last_time))

            # 获取设备
            device = None
            if hasattr(self.port_manager, 'devices'):
                device = self.port_manager.devices.get(port_name)

            if not device or not getattr(device, 'is_connected', False):
                print(f"端口 {port_name} 设备未连接")
                return False

            try:
                # 发送短信
                success = device.send_sms(phone_number, message)
                self.last_send_time[port_name] = time.time()

                if success:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] 发送成功: {phone_number} via {port_name}")
                else:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] 发送失败: {phone_number} via {port_name}")

                return success

            except Exception as e:
                print(f"发送短信异常 {phone_number} via {port_name}: {e}")
                return False

    def send_test_message(self, port_name, phone_number, message):
        """发送测试短信"""
        return self.send_message(port_name, phone_number, message)

    def send_batch_messages(self, task_id, phone_numbers, message, ports, callback=None):
        """批量发送短信"""
        if not ports:
            print("没有可用的端口")
            return False

        available_devices = []
        if hasattr(self.port_manager, 'get_available_devices'):
            available_devices = self.port_manager.get_available_devices(ports)

        if not available_devices:
            print("没有可用的设备连接")
            return False

        device_index = 0
        success_count = 0
        failed_count = 0

        for i, phone_number in enumerate(phone_numbers):
            device = available_devices[device_index % len(available_devices)]
            port_name = device.port_name

            try:
                success = self.send_message(port_name, phone_number, message)

                if success:
                    success_count += 1
                    if hasattr(self.port_manager, 'update_port_success'):
                        self.port_manager.update_port_success(port_name)
                else:
                    failed_count += 1

                # 记录到数据库
                if self.db_manager:
                    try:
                        self.db_manager.add_send_record(
                            task_id=int(task_id.replace('task_', '')) if isinstance(task_id, str) and task_id.startswith('task_') else int(task_id),
                            phone_number=phone_number,
                            message_content=message,
                            port_name=port_name,
                            status='success' if success else 'failed',
                            error_message=None if success else '发送失败',
                            response_time=150.0,  # 模拟响应时间
                            operator='未知',
                            signal_strength=85
                        )
                    except Exception as e:
                        print(f"记录发送结果到数据库失败: {e}")

                # 回调函数更新进度
                if callback:
                    callback(task_id, success_count, failed_count)

                device_index += 1

                # 检查卡片更换条件
                card_switch_limit = settings.get('card_switch', 60)
                if (i + 1) % card_switch_limit == 0:
                    print(f"达到卡片更换条件，已发送 {i + 1} 条")

            except Exception as e:
                print(f"发送异常 {phone_number}: {e}")
                failed_count += 1
                if callback:
                    callback(task_id, success_count, failed_count)

        print(f"批量发送完成: 成功 {success_count}, 失败 {failed_count}")
        return True

    def get_port_signal_info(self, port_name):
        """获取端口信号信息"""
        if not hasattr(self.port_manager, 'devices'):
            return {
                'signal_strength': -1,
                'operator': '未知',
                'status': 'disconnected'
            }

        device = self.port_manager.devices.get(port_name)
        if device and getattr(device, 'is_connected', False):
            try:
                signal_strength = device.get_signal_strength() if hasattr(device, 'get_signal_strength') else -1
                operator_info = device.get_operator_info() if hasattr(device, 'get_operator_info') else '未知'
                return {
                    'signal_strength': signal_strength,
                    'operator': operator_info,
                    'status': 'connected'
                }
            except Exception as e:
                print(f"获取端口 {port_name} 信号信息失败: {e}")

        return {
            'signal_strength': -1,
            'operator': '未知',
            'status': 'disconnected'
        }

    def validate_phone_number(self, phone_number):
        """验证手机号格式"""
        # 移除空格和特殊字符
        phone_number = phone_number.strip().replace(' ', '').replace('-', '')

        # 中国大陆手机号验证
        if len(phone_number) == 11 and phone_number.startswith('1') and phone_number.isdigit():
            return True

        # 国际号码格式验证（简单）
        if phone_number.startswith('+') and len(phone_number) > 10:
            return True

        return False

    def format_phone_number(self, phone_number, format_type='domestic'):
        """格式化手机号"""
        phone_number = phone_number.strip().replace(' ', '').replace('-', '')

        if format_type == 'domestic':
            # 国内格式
            if phone_number.startswith('+86'):
                phone_number = phone_number[3:]
            elif phone_number.startswith('86') and len(phone_number) == 13:
                phone_number = phone_number[2:]
        elif format_type == 'international':
            # 国际格式
            if not phone_number.startswith('+'):
                if phone_number.startswith('86'):
                    phone_number = '+' + phone_number
                else:
                    phone_number = '+86' + phone_number

        return phone_number

    def get_send_statistics(self):
        """获取发送统计信息"""
        total_success = 0
        active_ports = 0

        if hasattr(self.port_manager, 'ports'):
            total_success = sum(port.get('success', 0) for port in self.port_manager.ports.values())
            active_ports = len([p for p in self.port_manager.ports.values() if p.get('status') == 'running'])

        return {
            'total_success': total_success,
            'active_ports': active_ports,
            'last_send_times': self.last_send_time.copy()
        }


class MessageTemplate:
    """短信模板管理"""

    def __init__(self):
        self.templates = {}
        self._load_default_templates()

    def _load_default_templates(self):
        """加载默认模板"""
        self.templates = {
            'default': {
                'name': '默认模板',
                'content': '您好，这是一条测试短信。',
                'variables': []
            },
            'verification': {
                'name': '验证码模板',
                'content': '您的验证码是：{code}，请在5分钟内使用。',
                'variables': ['code']
            },
            'notification': {
                'name': '通知模板',
                'content': '尊敬的{name}，您有一条新消息：{message}',
                'variables': ['name', 'message']
            }
        }

    def add_template(self, template_id, name, content, variables=None):
        """添加模板"""
        self.templates[template_id] = {
            'name': name,
            'content': content,
            'variables': variables or []
        }

    def get_template(self, template_id):
        """获取模板"""
        return self.templates.get(template_id)

    def get_all_templates(self):
        """获取所有模板"""
        return self.templates

    def render_template(self, template_id, variables=None):
        """渲染模板"""
        template = self.get_template(template_id)
        if not template:
            return None

        content = template['content']
        if variables:
            try:
                content = content.format(**variables)
            except KeyError as e:
                print(f"模板变量缺失: {e}")
                return None

        return content

    def delete_template(self, template_id):
        """删除模板"""
        if template_id in self.templates:
            del self.templates[template_id]
            return True
        return False