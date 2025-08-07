# 创建文件：tests/mac_serial_simulator.py
import threading
import socket
import time
import random
from typing import Dict, List, Optional
import json
from dataclasses import dataclass


@dataclass
class MockModemInfo:
    port_name: str
    operator: str  # 移动、联通、电信
    imei: str
    signal_strength: int  # 1-31
    success_rate: float  # 0.0-1.0
    current_status: str  # idle, busy, error
    send_count: int = 0
    error_count: int = 0
    last_active: float = 0


class MacSerialSimulator:
    """Mac平台串口模拟器"""

    def __init__(self):
        self.modems = self._create_mock_modems()
        self.socket_server = None
        self.is_running = False
        self.clients = {}  # port_name -> socket

    def _create_mock_modems(self) -> Dict[str, MockModemInfo]:
        """创建模拟猫池设备"""
        modems = {}
        operators = ['移动', '联通', '电信']

        for i in range(1, 9):  # 创建8个模拟端口
            port_name = f"/dev/ttys{i:03d}"  # Mac风格端口名
            operator = operators[i % 3]

            modems[port_name] = MockModemInfo(
                port_name=port_name,
                operator=operator,
                imei=f"86012345678901{i:02d}",
                signal_strength=random.randint(15, 31),
                success_rate=random.uniform(0.85, 0.98),
                current_status='idle'
            )

        return modems

    def start_simulator(self, host='localhost', port=8888):
        """启动模拟器服务"""
        self.socket_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket_server.bind((host, port))
        self.socket_server.listen(10)

        self.is_running = True

        print(f"🚀 Mac串口模拟器启动在 {host}:{port}")
        print(f"📱 模拟设备数量: {len(self.modems)}")

        # 打印模拟设备信息
        for modem in self.modems.values():
            print(f"  📲 {modem.port_name} [{modem.operator}] 信号:{modem.signal_strength}/31")

        # 启动服务线程
        threading.Thread(target=self._handle_connections, daemon=True).start()

        # 启动状态监控线程
        threading.Thread(target=self._status_monitor, daemon=True).start()

    def _handle_connections(self):
        """处理客户端连接"""
        while self.is_running:
            try:
                client_socket, address = self.socket_server.accept()
                print(f"📞 新连接来自: {address}")

                # 为每个连接启动处理线程
                threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, address),
                    daemon=True
                ).start()
            except Exception as e:
                if self.is_running:
                    print(f"❌ 连接处理错误: {e}")

    def _handle_client(self, client_socket, address):
        """处理单个客户端"""
        try:
            while self.is_running:
                # 接收AT指令
                data = client_socket.recv(1024).decode('utf-8', errors='ignore')
                if not data:
                    break

                # 解析并响应AT指令
                response = self._process_at_command(data.strip(), address)
                client_socket.send(response.encode('utf-8'))

        except Exception as e:
            print(f"❌ 客户端处理错误 {address}: {e}")
        finally:
            client_socket.close()
            print(f"📴 连接断开: {address}")

    def _process_at_command(self, command: str, address) -> str:
        """处理AT指令"""
        # 基本的AT指令响应
        at_responses = {
            'AT': 'OK',
            'ATI': 'Mock Modem v1.0',
            'AT+CIMI': '460001234567890',  # 模拟IMSI
            'AT+CGSN': '860123456789012',  # 模拟IMEI
            'AT+CSQ': '+CSQ: 25,99',  # 模拟信号强度
            'AT+CREG?': '+CREG: 0,1',  # 模拟网络注册状态
        }

        # 短信发送指令
        if command.startswith('AT+CMGS='):
            return self._simulate_sms_send(command, address)

        # 返回标准响应
        return at_responses.get(command, 'ERROR')

    def _simulate_sms_send(self, command: str, address) -> str:
        """模拟短信发送"""
        # 随机选择一个模拟设备
        modem = random.choice(list(self.modems.values()))

        # 更新设备状态
        modem.current_status = 'busy'
        modem.last_active = time.time()

        # 模拟发送延迟
        time.sleep(random.uniform(0.5, 2.0))

        # 模拟发送结果
        success = random.random() < modem.success_rate

        if success:
            modem.send_count += 1
            modem.current_status = 'idle'
            message_id = f"MSG{int(time.time())}{random.randint(1000, 9999)}"
            return f'+CMGS: {message_id}\nOK'
        else:
            modem.error_count += 1
            modem.current_status = 'error'
            error_codes = ['300', '301', '302', '303', '304']  # CMS错误码
            error_code = random.choice(error_codes)
            return f'+CMS ERROR: {error_code}'

    def _status_monitor(self):
        """状态监控线程"""
        while self.is_running:
            time.sleep(10)  # 每10秒更新一次状态

            # 随机更新设备状态
            for modem in self.modems.values():
                if modem.current_status == 'error':
                    # 错误状态有概率恢复
                    if random.random() < 0.3:
                        modem.current_status = 'idle'

                # 更新信号强度
                modem.signal_strength = max(1, min(31,
                                                   modem.signal_strength + random.randint(-2, 2)))

    def get_status(self) -> dict:
        """获取所有设备状态"""
        status = {
            'total_modems': len(self.modems),
            'active_modems': sum(1 for m in self.modems.values() if m.current_status == 'idle'),
            'busy_modems': sum(1 for m in self.modems.values() if m.current_status == 'busy'),
            'error_modems': sum(1 for m in self.modems.values() if m.current_status == 'error'),
            'total_sent': sum(m.send_count for m in self.modems.values()),
            'total_errors': sum(m.error_count for m in self.modems.values()),
            'modems': []
        }

        for modem in self.modems.values():
            status['modems'].append({
                'port': modem.port_name,
                'operator': modem.operator,
                'status': modem.current_status,
                'signal': modem.signal_strength,
                'sent': modem.send_count,
                'errors': modem.error_count
            })

        return status

    def stop_simulator(self):
        """停止模拟器"""
        self.is_running = False
        if self.socket_server:
            self.socket_server.close()
        print("🛑 Mac串口模拟器已停止")


# 模拟器启动脚本
if __name__ == '__main__':
    simulator = MacSerialSimulator()

    try:
        simulator.start_simulator()

        print("\n📋 可用命令:")
        print("  status - 查看设备状态")
        print("  quit   - 退出模拟器")

        while True:
            cmd = input("\n> ").strip().lower()
            if cmd == 'quit':
                break
            elif cmd == 'status':
                status = simulator.get_status()
                print(f"\n📊 设备状态:")
                print(f"  总设备: {status['total_modems']}")
                print(f"  空闲: {status['active_modems']}")
                print(f"  忙碌: {status['busy_modems']}")
                print(f"  错误: {status['error_modems']}")
                print(f"  总发送: {status['total_sent']}")
                print(f"  总错误: {status['total_errors']}")
            else:
                print("❓ 未知命令")

    except KeyboardInterrupt:
        pass
    finally:
        simulator.stop_simulator()