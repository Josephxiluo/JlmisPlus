"""
猫池短信系统模拟服务
Simulator service for SMS Pool System
集成端口模拟器和短信模拟器，提供统一的模拟服务接口
"""

import sys
import time
import threading
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import settings
from config.logging_config import get_logger, log_info, log_error, log_task_action
from core.simulator.port_simulator import port_simulator, SimulatedPort
from core.simulator.sms_simulator import sms_simulator, SimulatedMessage, SendPriority
from models.task import TaskStatus
from models.message import MessageStatus

logger = get_logger('services.simulator')


class SimulatorService:
    """模拟服务管理类"""

    def __init__(self):
        """初始化模拟服务"""
        self.port_simulator = port_simulator
        self.sms_simulator = sms_simulator
        self._lock = threading.Lock()
        self.is_initialized = False

        # 任务执行状态
        self.running_tasks: Dict[int, Dict[str, Any]] = {}
        self.task_statistics: Dict[int, Dict[str, int]] = {}

        # 配置参数
        self.simulation_mode = getattr(settings, 'SIMULATION_MODE', True)
        self.default_success_rate = 0.7  # 默认70%成功率
        self.default_send_interval = getattr(settings, 'DEFAULT_SEND_INTERVAL', 1000)
        self.max_concurrent_tasks = getattr(settings, 'MAX_CONCURRENT_TASKS', 3)

        # 积分相关配置
        self.sms_rate = getattr(settings, 'SMS_RATE', 1.0)
        self.mms_rate = getattr(settings, 'MMS_RATE', 3.0)

        log_info("模拟服务初始化")

    def initialize(self) -> bool:
        """初始化服务"""
        try:
            if not self.simulation_mode:
                log_info("非模拟模式，跳过模拟服务初始化")
                return False

            # 自动连接一些端口
            connected_count = self._auto_connect_ports(10)  # 自动连接10个端口

            # 启动短信模拟器
            self.sms_simulator.start()

            # 添加回调
            self.sms_simulator.add_callback(self._on_message_event)

            self.is_initialized = True
            log_info(f"模拟服务初始化完成，已连接{connected_count}个虚拟端口")
            return True

        except Exception as e:
            log_error(f"模拟服务初始化失败: {e}")
            return False

    def shutdown(self):
        """关闭服务"""
        try:
            # 停止短信模拟器
            self.sms_simulator.stop()

            # 断开所有端口
            for port_name in self.port_simulator.get_all_ports():
                self.port_simulator.disconnect_port(port_name)

            # 清理数据
            self.running_tasks.clear()
            self.task_statistics.clear()

            self.is_initialized = False
            log_info("模拟服务已关闭")

        except Exception as e:
            log_error(f"模拟服务关闭失败: {e}")

    def _auto_connect_ports(self, count: int) -> int:
        """自动连接指定数量的端口"""
        connected = 0
        available_ports = self.port_simulator.scan_ports()

        for i, port_name in enumerate(available_ports[:count]):
            if self.port_simulator.connect_port(port_name):
                connected += 1
                # 设置不同的成功率，模拟端口质量差异
                success_rate = 0.6 + (i % 5) * 0.08  # 60% - 92%
                self.port_simulator.set_success_rate(port_name, success_rate)

        return connected

    def start_task(self, task_id: int, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        启动任务执行
        """
        try:
            # 检查并发限制
            if len(self.running_tasks) >= self.max_concurrent_tasks:
                return {
                    'success': False,
                    'message': f'已达到最大并发任务数({self.max_concurrent_tasks})'
                }

            # 检查任务是否已在运行
            if task_id in self.running_tasks:
                return {
                    'success': False,
                    'message': '任务已在运行中'
                }

            # 初始化任务统计
            self.task_statistics[task_id] = {
                'total': task_data.get('total_count', 0),
                'sent': 0,
                'success': 0,
                'failed': 0,
                'pending': task_data.get('total_count', 0),
                'credits_used': 0
            }

            # 记录运行任务
            self.running_tasks[task_id] = {
                'task_id': task_id,
                'status': TaskStatus.RUNNING.value,
                'start_time': datetime.now(),
                'task_data': task_data
            }

            # 创建任务执行线程
            task_thread = threading.Thread(
                target=self._execute_task,
                args=(task_id, task_data),
                daemon=True
            )
            task_thread.start()

            log_task_action(task_id, task_data.get('title', ''), "启动模拟任务")

            return {
                'success': True,
                'message': '任务启动成功',
                'task_id': task_id
            }

        except Exception as e:
            log_error(f"启动任务{task_id}失败: {e}")
            return {
                'success': False,
                'message': f'启动失败: {str(e)}'
            }

    def pause_task(self, task_id: int) -> Dict[str, Any]:
        """暂停任务"""
        try:
            if task_id in self.running_tasks:
                self.running_tasks[task_id]['status'] = TaskStatus.PAUSED.value
                log_task_action(task_id, "", "暂停模拟任务")
                return {'success': True, 'message': '任务已暂停'}

            return {'success': False, 'message': '任务不存在或未运行'}

        except Exception as e:
            log_error(f"暂停任务{task_id}失败: {e}")
            return {'success': False, 'message': f'暂停失败: {str(e)}'}

    def resume_task(self, task_id: int) -> Dict[str, Any]:
        """恢复任务"""
        try:
            if task_id in self.running_tasks:
                if self.running_tasks[task_id]['status'] == TaskStatus.PAUSED.value:
                    self.running_tasks[task_id]['status'] = TaskStatus.RUNNING.value
                    log_task_action(task_id, "", "恢复模拟任务")
                    return {'success': True, 'message': '任务已恢复'}

            return {'success': False, 'message': '任务不存在或未暂停'}

        except Exception as e:
            log_error(f"恢复任务{task_id}失败: {e}")
            return {'success': False, 'message': f'恢复失败: {str(e)}'}

    def stop_task(self, task_id: int) -> Dict[str, Any]:
        """停止任务"""
        try:
            if task_id in self.running_tasks:
                self.running_tasks[task_id]['status'] = TaskStatus.CANCELLED.value
                log_task_action(task_id, "", "停止模拟任务")

                # 等待任务线程结束
                time.sleep(0.5)

                # 清理任务
                if task_id in self.running_tasks:
                    del self.running_tasks[task_id]

                return {'success': True, 'message': '任务已停止'}

            return {'success': False, 'message': '任务不存在'}

        except Exception as e:
            log_error(f"停止任务{task_id}失败: {e}")
            return {'success': False, 'message': f'停止失败: {str(e)}'}

    def _execute_task(self, task_id: int, task_data: Dict[str, Any]):
        """执行任务（在独立线程中）"""
        try:
            log_info(f"开始执行模拟任务{task_id}")

            # 获取任务参数
            phone_numbers = task_data.get('phone_numbers', [])
            content = task_data.get('content', '')
            mode = task_data.get('mode', 'sms')
            priority = task_data.get('priority', SendPriority.NORMAL.value)

            # 批量添加消息到队列
            for i, phone in enumerate(phone_numbers):
                # 检查任务状态
                if task_id not in self.running_tasks:
                    break

                task_status = self.running_tasks[task_id]['status']

                # 暂停等待
                while task_status == TaskStatus.PAUSED.value:
                    time.sleep(1)
                    if task_id in self.running_tasks:
                        task_status = self.running_tasks[task_id]['status']
                    else:
                        break

                # 任务被取消
                if task_status == TaskStatus.CANCELLED.value:
                    break

                # 发送消息
                message_id = task_id * 10000 + i  # 生成消息ID
                self.sms_simulator.send_message(
                    message_id=message_id,
                    task_id=task_id,
                    phone=phone,
                    content=content,
                    priority=priority
                )

                # 控制发送速度
                time.sleep(0.01)  # 10ms间隔

            # 等待所有消息处理完成
            self._wait_for_task_completion(task_id)

            # 任务完成
            if task_id in self.running_tasks:
                self.running_tasks[task_id]['status'] = TaskStatus.COMPLETED.value
                log_task_action(task_id, "", "模拟任务完成")

                # 延迟清理
                time.sleep(5)
                if task_id in self.running_tasks:
                    del self.running_tasks[task_id]

        except Exception as e:
            log_error(f"执行任务{task_id}异常: {e}")
            if task_id in self.running_tasks:
                self.running_tasks[task_id]['status'] = TaskStatus.FAILED.value

    def _wait_for_task_completion(self, task_id: int, timeout: int = 300):
        """等待任务完成"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            stats = self.task_statistics.get(task_id, {})

            # 检查是否所有消息都已处理
            if stats.get('sent', 0) >= stats.get('total', 0):
                break

            # 检查任务是否被取消
            if task_id not in self.running_tasks:
                break

            if self.running_tasks[task_id]['status'] == TaskStatus.CANCELLED.value:
                break

            time.sleep(1)

    def _on_message_event(self, event: str, message: SimulatedMessage):
        """消息事件回调"""
        try:
            task_id = message.task_id

            if task_id not in self.task_statistics:
                return

            stats = self.task_statistics[task_id]

            # 获取端口信息
            port_info = None
            if message.port_name:
                port = self.port_simulator.get_port(message.port_name)
                if port:
                    port_info = {
                        'port_name': port.port_name,
                        'carrier': port.carrier,
                        'send_count': port.send_count
                    }

            if event == 'success':
                stats['sent'] += 1
                stats['success'] += 1
                stats['pending'] = max(0, stats['pending'] - 1)

                # 计算积分消耗
                rate = self.sms_rate  # 这里简化处理，实际应根据消息类型
                stats['credits_used'] += rate

                # 更新数据库中的消息明细
                if port_info:
                    self._update_message_detail(
                        message.message_id,
                        'success',
                        port_info
                    )

            elif event == 'failed':
                stats['sent'] += 1
                stats['failed'] += 1
                stats['pending'] = max(0, stats['pending'] - 1)

                # 更新数据库中的消息明细
                if port_info:
                    self._update_message_detail(
                        message.message_id,
                        'failed',
                        port_info,
                        error_message=message.error_message
                    )

            # 更新任务进度（这里可以通知UI更新）
            self._update_task_progress(task_id, stats)

        except Exception as e:
            log_error(f"处理消息事件异常: {e}")

    def _update_message_detail(self, message_id: int, status: str,
                               port_info: Dict, error_message: str = None):
        """更新消息明细的端口信息"""
        try:
            from database.connection import execute_update
            from datetime import datetime

            # 生成模拟的发送号码（基于端口名）
            port_number = port_info['port_name'].replace('COM', '')
            sender_number = f"1000{port_number.zfill(4)}"  # 如：10000001

            # 更新消息明细
            query = """
            UPDATE task_message_details 
            SET details_status = %s,
                sender_number = %s,
                details_sender_port = %s,
                details_operator_name = %s,
                details_failure_reason = %s,
                send_time = %s,
                delivery_time = %s,
                response_time = %s
            WHERE details_id = %s
            """

            params = (
                status,
                sender_number,
                port_info['port_name'],
                port_info['carrier'],
                error_message,
                datetime.now(),
                datetime.now() if status == 'success' else None,
                1500,  # 模拟响应时间1.5秒
                message_id
            )

            execute_update(query, params)

            print(f"[DEBUG] 更新消息{message_id}端口信息: {port_info['port_name']}")

        except Exception as e:
            log_error(f"更新消息明细失败: {e}")

    def _update_task_progress(self, task_id: int, stats: Dict[str, int]):
        """更新任务进度"""
        try:
            # 这里可以调用回调函数通知UI更新
            # 或者更新数据库中的任务状态

            progress = 0
            if stats['total'] > 0:
                progress = (stats['sent'] / stats['total']) * 100

            log_info(f"任务{task_id}进度: {progress:.1f}% "
                     f"(成功:{stats['success']}, 失败:{stats['failed']}, "
                     f"待发:{stats['pending']})")

        except Exception as e:
            log_error(f"更新任务进度异常: {e}")

    def get_task_statistics(self, task_id: int) -> Dict[str, Any]:
        """获取任务统计信息"""
        if task_id in self.task_statistics:
            stats = self.task_statistics[task_id].copy()

            # 计算成功率
            if stats['sent'] > 0:
                stats['success_rate'] = round((stats['success'] / stats['sent']) * 100, 2)
            else:
                stats['success_rate'] = 0

            # 计算进度
            if stats['total'] > 0:
                stats['progress'] = round((stats['sent'] / stats['total']) * 100, 2)
            else:
                stats['progress'] = 0

            return stats

        return {}

    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        return {
            'initialized': self.is_initialized,
            'simulation_mode': self.simulation_mode,
            'running_tasks': len(self.running_tasks),
            'task_ids': list(self.running_tasks.keys()),
            'sms_simulator': self.sms_simulator.get_statistics(),
            'port_simulator': self.port_simulator.get_port_statistics()
        }

    def test_send(self, phone: str, content: str, port_name: str = None) -> Dict[str, Any]:
        """测试发送（不消耗积分）"""
        try:
            # 如果指定端口，确保端口已连接
            if port_name:
                port = self.port_simulator.get_port(port_name)
                if not port or not port.is_connected:
                    # 尝试连接端口
                    if not self.port_simulator.connect_port(port_name):
                        return {
                            'success': False,
                            'message': f'端口{port_name}连接失败'
                        }
            else:
                # 自动选择一个可用端口
                available_ports = [p for p in self.port_simulator.ports.values()
                                   if p.is_connected and p.can_send()]
                if not available_ports:
                    return {
                        'success': False,
                        'message': '没有可用的端口'
                    }
                port = available_ports[0]
                port_name = port.port_name

            # 直接发送测试消息
            port = self.port_simulator.get_port(port_name)
            success, message, duration = port.send_sms(phone, content)

            return {
                'success': success,
                'message': message,
                'port': port_name,
                'duration': duration,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            log_error(f"测试发送失败: {e}")
            return {
                'success': False,
                'message': f'测试失败: {str(e)}'
            }

    def retry_failed_messages(self, task_id: int) -> Dict[str, Any]:
        """重试失败的消息"""
        try:
            # 获取失败的消息
            failed_messages = []
            for msg in self.sms_simulator.message_queue.failed_messages:
                if msg.task_id == task_id:
                    failed_messages.append(msg)

            retry_count = 0
            for msg in failed_messages:
                # 重置消息状态
                msg.retry_count = 0
                msg.success = None
                msg.error_message = None

                # 重新入队
                if self.sms_simulator.message_queue.enqueue(msg):
                    retry_count += 1

            log_info(f"任务{task_id}重试{retry_count}条失败消息")

            return {
                'success': True,
                'message': f'已重试{retry_count}条消息',
                'retry_count': retry_count
            }

        except Exception as e:
            log_error(f"重试失败消息异常: {e}")
            return {
                'success': False,
                'message': f'重试失败: {str(e)}'
            }

    def set_success_rate(self, rate: float):
        """设置成功率"""
        self.default_success_rate = max(0.0, min(1.0, rate))
        self.sms_simulator.set_success_rate(self.default_success_rate)
        log_info(f"模拟成功率设置为{self.default_success_rate:.2%}")

    def get_port_list(self) -> List[Dict[str, Any]]:
        """获取端口列表"""
        ports = []
        for port_name, port in self.port_simulator.ports.items():
            ports.append(port.get_status_info())
        return ports

    def update_port_config(self, port_name: str, config: Dict[str, Any]) -> bool:
        """更新端口配置"""
        port = self.port_simulator.get_port(port_name)
        if port:
            # 更新配置
            if 'send_interval' in config:
                port.send_interval = config['send_interval']
            if 'send_limit' in config:
                port.send_limit = config['send_limit']
            if 'success_rate' in config:
                port.success_rate = config['success_rate']

            log_info(f"端口{port_name}配置已更新")
            return True

        return False


# 全局模拟服务实例
simulator_service = SimulatorService()

if __name__ == "__main__":
    # 测试代码
    print("=" * 50)
    print("模拟服务测试")
    print("=" * 50)

    # 初始化服务
    print("\n初始化模拟服务...")
    if simulator_service.initialize():
        print("初始化成功")

        # 测试发送
        print("\n测试发送...")
        result = simulator_service.test_send("13800138000", "测试短信内容")
        print(f"测试结果: {result}")

        # 创建测试任务
        print("\n创建测试任务...")
        task_data = {
            'title': '测试任务',
            'total_count': 10,
            'phone_numbers': [f'1380013800{i}' for i in range(10)],
            'content': '这是一条测试短信，用于验证模拟服务功能。',
            'mode': 'sms'
        }

        result = simulator_service.start_task(1, task_data)
        print(f"启动任务结果: {result}")

        # 等待一段时间查看进度
        import time

        for i in range(5):
            time.sleep(2)
            stats = simulator_service.get_task_statistics(1)
            if stats:
                print(f"\n任务进度 [{i + 1}/5]:")
                print(f"  总数: {stats.get('total', 0)}")
                print(f"  已发送: {stats.get('sent', 0)}")
                print(f"  成功: {stats.get('success', 0)}")
                print(f"  失败: {stats.get('failed', 0)}")
                print(f"  进度: {stats.get('progress', 0)}%")
                print(f"  成功率: {stats.get('success_rate', 0)}%")
                print(f"  消耗积分: {stats.get('credits_used', 0)}")

        # 获取服务状态
        print("\n服务状态:")
        status = simulator_service.get_status()
        print(f"  初始化: {status['initialized']}")
        print(f"  运行任务数: {status['running_tasks']}")
        print(f"  队列大小: {status['sms_simulator']['queue']['queue_size']}")
        print(f"  连接端口数: {status['port_simulator']['connected_ports']}")

        # 关闭服务
        print("\n关闭模拟服务...")
        simulator_service.shutdown()
        print("服务已关闭")