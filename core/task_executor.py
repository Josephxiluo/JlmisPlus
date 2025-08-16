"""
修复版任务执行器 - 最小修改实现业务功能
Task executor with minimal fixes for business logic
"""

import sys
import time
import threading
import queue
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import settings
from config.logging_config import get_logger
from database.connection import execute_query, execute_update

logger = get_logger('core.task_executor')


class TaskExecutor:
    """任务执行器 - 简化版"""

    def __init__(self):
        """初始化任务执行器"""
        self.current_task = None
        self.is_running = False
        self.is_paused = False
        self._lock = threading.Lock()
        self.worker_thread = None

        # 积分服务（稍后注入）
        self.credit_service = None

        # 回调函数
        self.progress_callback = None
        self.status_callback = None

        logger.info("任务执行器初始化完成")

    def set_credit_service(self, credit_service):
        """设置积分服务"""
        self.credit_service = credit_service
        logger.info("积分服务已注入")

    def start_task(self, task_id: int) -> Dict[str, Any]:
        """开始执行任务"""
        try:
            with self._lock:
                if self.is_running:
                    return {'success': False, 'message': '已有任务正在执行'}

                # 加载任务信息
                task = self._load_task(task_id)
                if not task:
                    return {'success': False, 'message': '任务不存在'}

                # 检查任务状态
                if task['status'] not in ['draft', 'pending', 'paused']:
                    return {'success': False, 'message': f'任务状态不允许启动: {task["status"]}'}

                # 检查积分余额并预扣除
                if self.credit_service:
                    # 获取待发送数量
                    pending_count = task.get('pending_count', 0)
                    if pending_count > 0:
                        # 检查余额
                        balance_check = self.credit_service.check_balance(
                            task['operators_id'],
                            pending_count,
                            task.get('mode', 'sms')
                        )
                        if not balance_check['success']:
                            return balance_check

                        # 预扣除积分
                        pre_deduct = self.credit_service.pre_deduct(
                            task['operators_id'],
                            pending_count,
                            task_id,
                            task.get('mode', 'sms')
                        )
                        if not pre_deduct['success']:
                            return pre_deduct

                # 设置当前任务
                self.current_task = task
                self.is_running = True
                self.is_paused = False

                # 更新任务状态为运行中
                self._update_task_status(task_id, 'running')

                # 启动工作线程
                self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
                self.worker_thread.start()

                logger.info(f"任务 {task_id} 开始执行，待发送: {task.get('pending_count', 0)} 条")
                return {'success': True, 'message': '任务开始执行'}

        except Exception as e:
            logger.error(f"启动任务失败: {e}")
            return {'success': False, 'message': str(e)}

    def pause_task(self) -> Dict[str, Any]:
        """暂停任务"""
        try:
            with self._lock:
                if not self.is_running:
                    return {'success': False, 'message': '没有正在执行的任务'}

                self.is_paused = True

                if self.current_task:
                    self._update_task_status(self.current_task['id'], 'paused')

                logger.info(f"任务 {self.current_task['id']} 已暂停")
                return {'success': True, 'message': '任务已暂停'}

        except Exception as e:
            logger.error(f"暂停任务失败: {e}")
            return {'success': False, 'message': str(e)}

    def resume_task(self) -> Dict[str, Any]:
        """恢复任务"""
        try:
            with self._lock:
                if not self.is_paused:
                    return {'success': False, 'message': '任务未暂停'}

                self.is_paused = False

                if self.current_task:
                    self._update_task_status(self.current_task['id'], 'running')

                logger.info(f"任务 {self.current_task['id']} 已恢复")
                return {'success': True, 'message': '任务已恢复'}

        except Exception as e:
            logger.error(f"恢复任务失败: {e}")
            return {'success': False, 'message': str(e)}

    def stop_task(self) -> Dict[str, Any]:
        """停止任务"""
        try:
            with self._lock:
                if not self.is_running:
                    return {'success': False, 'message': '没有执行中的任务'}

                self.is_running = False

                # 回退未使用的积分
                if self.current_task and self.credit_service:
                    # 查询剩余未发送数量
                    query = """
                        SELECT COUNT(*) as pending_count
                        FROM task_message_details
                        WHERE tasks_id = %s AND details_status IN ('pending', 'retry')
                    """
                    result = execute_query(query, (self.current_task['id'],), fetch_one=True, dict_cursor=True)

                    if result and result['pending_count'] > 0:
                        self.credit_service.rollback(
                            self.current_task['operators_id'],
                            result['pending_count'],
                            self.current_task['id'],
                            self.current_task.get('mode', 'sms')
                        )

                # 更新任务状态
                if self.current_task:
                    self._update_task_status(self.current_task['id'], 'stopped')

                self.current_task = None

                logger.info("任务已停止")
                return {'success': True, 'message': '任务已停止'}

        except Exception as e:
            logger.error(f"停止任务失败: {e}")
            return {'success': False, 'message': str(e)}

    def retry_failed_messages(self, task_id: int) -> Dict[str, Any]:
        """重试失败的消息"""
        try:
            # 重置失败消息状态
            update_query = """
                UPDATE task_message_details
                SET details_status = 'pending', retry_count = retry_count + 1
                WHERE tasks_id = %s AND details_status IN ('failed', 'timeout')
            """
            affected = execute_update(update_query, (task_id,))

            # 更新任务的待发送数量
            if affected and affected > 0:
                update_task_query = """
                    UPDATE tasks
                    SET tasks_pending_count = tasks_pending_count + %s
                    WHERE tasks_id = %s
                """
                execute_update(update_task_query, (affected, task_id))

            return {
                'success': True,
                'message': f'已重试 {affected or 0} 条失败消息',
                'count': affected or 0
            }

        except Exception as e:
            logger.error(f"重试失败消息失败: {e}")
            return {'success': False, 'message': str(e)}

    def _worker_loop(self):
        """工作线程主循环"""
        logger.info(f"工作线程启动，任务ID: {self.current_task['id']}")

        while self.is_running and self.current_task:
            try:
                # 暂停状态下等待
                if self.is_paused:
                    time.sleep(1)
                    continue

                # 获取一条待发送消息
                message = self._get_next_message()
                if not message:
                    # 没有更多消息，任务完成
                    self._on_task_complete()
                    break

                # 发送消息
                success = self._send_message(message)

                # 更新统计和进度
                if success:
                    self._on_message_success(message['details_id'])
                else:
                    self._on_message_failed(message['details_id'])

                # 发送间隔（避免过快）
                time.sleep(0.1)  # 100ms间隔

            except Exception as e:
                logger.error(f"工作线程错误: {e}")
                time.sleep(1)

        logger.info("工作线程结束")

    def _get_next_message(self) -> Optional[Dict[str, Any]]:
        """获取下一条待发送消息 - 修正版"""
        try:
            # 查询待发送消息，包含重试次数和优先级
            # 同时从tasks表获取消息内容
            query = """
                SELECT 
                    d.details_id,
                    d.recipient_number,
                    d.details_status,
                    COALESCE(d.retry_count, 0) as retry_count,
                    COALESCE(d.priority, 5) as priority,
                    t.tasks_message_content as message_content
                FROM task_message_details d
                INNER JOIN tasks t ON d.tasks_id = t.tasks_id
                WHERE d.tasks_id = %s 
                    AND d.details_status IN ('pending', 'retry')
                ORDER BY d.priority DESC, d.details_id ASC
                LIMIT 1
                FOR UPDATE SKIP LOCKED
            """

            result = execute_query(
                query,
                (self.current_task['id'],),
                fetch_one=True,
                dict_cursor=True
            )

            if result:
                # 立即更新为发送中状态，避免重复获取
                update_query = """
                    UPDATE task_message_details
                    SET details_status = 'sending', updated_time = %s
                    WHERE details_id = %s
                """
                execute_update(update_query, (datetime.now(), result['details_id']))

                # 返回消息数据
                return {
                    'details_id': result['details_id'],
                    'recipient_number': result['recipient_number'],
                    'message_content': result['message_content'],  # 从tasks表获取的内容
                    'retry_count': result['retry_count'],
                    'priority': result['priority']
                }

            return None

        except Exception as e:
            logger.error(f"获取待发送消息失败: {e}")
            return None

    def _send_message(self, message: Dict[str, Any]):
        """发送单条消息 - 修复版，记录端口信息"""
        try:
            msg_id = message['details_id']
            phone = message['recipient_number']
            content = message.get('message_content', '')

            # 更新消息状态为发送中
            self._update_message_status(msg_id, 'sending')

            # 使用模拟器发送，并获取端口信息
            success, port_info = self._simulate_send_with_port_info(phone, content)

            if success:
                # 发送成功，记录端口信息
                self._update_message_with_port_info(msg_id, port_info, 'success')
                self._on_message_success(msg_id)
            else:
                # 发送失败
                retry_count = message.get('retry_count', 0)
                if retry_count < self.retry_count:
                    # 重试
                    message['retry_count'] = retry_count + 1
                    self._add_message_to_queue(message)
                    self._update_message_status(msg_id, 'retry')
                else:
                    # 最终失败
                    self._update_message_with_port_info(msg_id, port_info, 'failed')
                    self._on_message_failed(msg_id)

        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            self._update_message_status(message['details_id'], 'failed')
            self._on_message_failed(message['details_id'])

    def _simulate_send_with_port_info(self, phone: str, content: str) -> Tuple[bool, Dict]:
        """模拟发送并返回端口信息"""
        try:
            import random
            from core.simulator.port_simulator import port_simulator

            # 获取所有已连接的端口
            connected_ports = []
            for port_name in port_simulator.get_all_ports():
                port = port_simulator.get_port(port_name)
                if port and port.is_connected:
                    # 检查端口是否达到上限
                    if port.send_count < port.send_limit:
                        connected_ports.append(port_name)

            if not connected_ports:
                logger.error("没有可用的端口（所有端口都达到上限或未连接）")
                return False, {'port_name': None, 'error': '无可用端口'}

            # 随机选择一个端口
            port_name = random.choice(connected_ports)

            # 连接端口（如果需要）
            if not port_simulator.ports[port_name].is_connected:
                port_simulator.connect_port(port_name)

            # 发送短信
            success, message, duration = port_simulator.send_sms(port_name, phone, content)

            # 获取端口信息
            port = port_simulator.get_port(port_name)
            port_info = {
                'port_name': port_name,
                'sender_number': port.sim_number if hasattr(port, 'sim_number') else f"SIM_{port_name}",
                'operator_name': port.carrier if hasattr(port, 'carrier') else 'unknown',
                'send_count': port.send_count if hasattr(port, 'send_count') else 0,
                'send_limit': port.send_limit if hasattr(port, 'send_limit') else 60
            }

            # 更新端口发送计数
            if success and hasattr(port, 'send_count'):
                port.send_count += 1
                if success:
                    port.success_count = getattr(port, 'success_count', 0) + 1
                else:
                    port.failed_count = getattr(port, 'failed_count', 0) + 1

                logger.info(f"端口 {port_name} 发送计数: {port.send_count}/{port.send_limit}")

                # 如果达到上限，自动断开连接
                if port.send_count >= port.send_limit:
                    logger.warning(f"端口 {port_name} 已达到发送上限，自动断开")
                    port_simulator.disconnect_port(port_name)

            return success, port_info

        except Exception as e:
            logger.error(f"模拟发送失败: {e}")
            return False, {'port_name': None, 'error': str(e)}

    def _update_message_with_port_info(self, msg_id: int, port_info: Dict, status: str):
        """更新消息状态并记录端口信息"""
        try:
            query = """
                UPDATE task_message_details
                SET details_status = %s,
                    details_sender_port = %s,
                    sender_number = %s,
                    details_operator_name = %s,
                    send_time = %s,
                    updated_time = %s
                WHERE details_id = %s
            """

            params = (
                status,
                port_info.get('port_name'),
                port_info.get('sender_number'),
                port_info.get('operator_name'),
                datetime.now(),
                datetime.now(),
                msg_id
            )

            execute_update(query, params)

            logger.debug(f"消息 {msg_id} 更新成功，端口: {port_info.get('port_name')}, 状态: {status}")

        except Exception as e:
            logger.error(f"更新消息端口信息失败: {e}")

    def _on_message_success(self, msg_id: int):
        """消息发送成功处理"""
        try:
            # 更新消息状态
            update_msg = """
                UPDATE task_message_details
                SET details_status = 'success', send_time = %s, updated_time = %s
                WHERE details_id = %s
            """
            execute_update(update_msg, (datetime.now(), datetime.now(), msg_id))

            # 更新任务统计
            update_task = """
                UPDATE tasks
                SET tasks_success_count = tasks_success_count + 1,
                    tasks_pending_count = GREATEST(0, tasks_pending_count - 1),
                    updated_time = %s
                WHERE tasks_id = %s
            """
            execute_update(update_task, (datetime.now(), self.current_task['id']))

            # 实际扣除积分
            if self.credit_service:
                self.credit_service.actual_deduct(
                    self.current_task['operators_id'],
                    1,
                    self.current_task['id'],
                    msg_id,
                    self.current_task.get('mode', 'sms')
                )

            # 触发进度回调
            if self.progress_callback:
                self._trigger_progress_callback()

        except Exception as e:
            logger.error(f"处理成功消息失败: {e}")

    def _on_message_failed(self, msg_id: int):
        """消息发送失败处理 - 修正版，使用retry_count字段"""
        try:
            # 获取消息的重试次数
            query = "SELECT COALESCE(retry_count, 0) as retry_count FROM task_message_details WHERE details_id = %s"
            result = execute_query(query, (msg_id,), fetch_one=True)

            retry_count = result[0] if result else 0
            max_retry = 3  # 最大重试次数

            if retry_count < max_retry:
                # 增加重试次数，标记为待重试
                update_retry = """
                    UPDATE task_message_details
                    SET details_status = 'pending', 
                        retry_count = COALESCE(retry_count, 0) + 1,
                        updated_time = %s
                    WHERE details_id = %s
                """
                execute_update(update_retry, (datetime.now(), msg_id))

                logger.info(f"消息 {msg_id} 标记为重试，当前重试次数: {retry_count + 1}")
            else:
                # 超过最大重试次数，标记为最终失败
                update_failed = """
                    UPDATE task_message_details
                    SET details_status = 'failed', updated_time = %s
                    WHERE details_id = %s
                """
                execute_update(update_failed, (datetime.now(), msg_id))

                # 更新任务失败计数
                update_task = """
                    UPDATE tasks
                    SET tasks_failed_count = tasks_failed_count + 1,
                        tasks_pending_count = GREATEST(0, tasks_pending_count - 1),
                        updated_time = %s
                    WHERE tasks_id = %s
                """
                execute_update(update_task, (datetime.now(), self.current_task['id']))

                # 回退积分
                if self.credit_service:
                    self.credit_service.rollback(
                        self.current_task['operators_id'],
                        1,
                        self.current_task['id'],
                        self.current_task.get('mode', 'sms')
                    )

                logger.info(f"消息 {msg_id} 最终失败，已尝试 {retry_count} 次")

            # 触发进度回调
            if self.progress_callback:
                self._trigger_progress_callback()

        except Exception as e:
            logger.error(f"处理失败消息失败: {e}")

    def _on_task_complete(self):
        """任务完成处理"""
        try:
            if not self.current_task:
                return

            # 更新任务状态
            self._update_task_status(self.current_task['id'], 'completed')

            logger.info(f"任务 {self.current_task['id']} 执行完成")

            # 触发完成回调
            if self.status_callback:
                self.status_callback(self.current_task['id'], 'completed')

            # 清理
            self.is_running = False
            self.current_task = None

        except Exception as e:
            logger.error(f"任务完成处理失败: {e}")

    def _trigger_progress_callback(self):
        """触发进度回调"""
        try:
            if not self.current_task or not self.progress_callback:
                return

            # 查询最新统计
            query = """
                SELECT tasks_total_count as total,
                       tasks_success_count as success,
                       tasks_failed_count as failed,
                       tasks_pending_count as pending
                FROM tasks
                WHERE tasks_id = %s
            """
            result = execute_query(
                query,
                (self.current_task['id'],),
                fetch_one=True,
                dict_cursor=True
            )

            if result:
                stats = {
                    'total': result['total'],
                    'sent': result['success'] + result['failed'],
                    'success_count': result['success'],
                    'failed_count': result['failed'],
                    'pending_count': result['pending'],
                    'progress': round((result['success'] + result['failed']) / result['total'] * 100, 1) if result['total'] > 0 else 0
                }

                self.progress_callback(self.current_task['id'], stats)

        except Exception as e:
            logger.error(f"触发进度回调失败: {e}")

    def _load_task(self, task_id: int) -> Optional[Dict[str, Any]]:
        """加载任务信息"""
        try:
            query = """
                SELECT tasks_id as id, tasks_title as title, tasks_status as status,
                       tasks_mode as mode, tasks_total_count as total_count,
                       tasks_success_count as success_count,
                       tasks_failed_count as failed_count,
                       tasks_pending_count as pending_count,
                       operators_id
                FROM tasks
                WHERE tasks_id = %s
            """

            result = execute_query(query, (task_id,), fetch_one=True, dict_cursor=True)
            return dict(result) if result else None

        except Exception as e:
            logger.error(f"加载任务失败: {e}")
            return None

    def _update_task_status(self, task_id: int, status: str):
        """更新任务状态"""
        try:
            query = """
                UPDATE tasks
                SET tasks_status = %s, updated_time = %s
                WHERE tasks_id = %s
            """
            execute_update(query, (status, datetime.now(), task_id))

        except Exception as e:
            logger.error(f"更新任务状态失败: {e}")

    def get_status(self) -> Dict[str, Any]:
        """获取执行器状态"""
        return {
            'is_running': self.is_running,
            'is_paused': self.is_paused,
            'current_task': self.current_task['id'] if self.current_task else None
        }

    def _update_message_status(self, msg_id: int, status: str):
        """更新消息状态"""
        try:
            query = """
                UPDATE task_message_details
                SET details_status = %s, updated_time = %s
                WHERE details_id = %s
            """
            execute_update(query, (status, datetime.now(), msg_id))
            logger.debug(f"消息 {msg_id} 状态更新为: {status}")
        except Exception as e:
            logger.error(f"更新消息状态失败: {e}")

    def _update_message_with_port_info(self, msg_id: int, port_info: Dict, status: str):
        """更新消息状态并记录端口信息"""
        try:
            query = """
                UPDATE task_message_details
                SET details_status = %s,
                    details_sender_port = %s,
                    sender_number = %s,
                    details_operator_name = %s,
                    send_time = %s,
                    updated_time = %s
                WHERE details_id = %s
            """

            params = (
                status,
                port_info.get('port_name'),
                port_info.get('sender_number'),
                port_info.get('operator_name'),
                datetime.now(),
                datetime.now(),
                msg_id
            )

            execute_update(query, params)

            logger.debug(f"消息 {msg_id} 更新成功，端口: {port_info.get('port_name')}, 状态: {status}")

        except Exception as e:
            logger.error(f"更新消息端口信息失败: {e}")

    def _simulate_send(self, phone: str, content: str) -> bool:
        """模拟发送（使用模拟器）- 简化版"""
        try:
            # 随机选择一个端口
            import random
            from core.simulator.port_simulator import port_simulator

            # 获取可用端口
            available_ports = port_simulator.get_available_ports()
            if not available_ports:
                # 如果没有可用端口，尝试获取所有连接的端口
                connected_ports = port_simulator.get_connected_ports()
                if not connected_ports:
                    logger.error("没有可用的端口")
                    return False
                port_name = random.choice(connected_ports)
            else:
                port_name = random.choice(available_ports)

            # 发送短信
            success, message, duration = port_simulator.send_sms(port_name, phone, content)

            logger.debug(f"模拟发送到 {phone}: {message}")
            return success

        except Exception as e:
            logger.error(f"模拟发送失败: {e}")
            return False

    def _simulate_send_with_port_info(self, phone: str, content: str) -> Tuple[bool, Dict]:
        """模拟发送并返回端口信息"""
        try:
            import random
            from core.simulator.port_simulator import port_simulator

            # 获取所有已连接的端口
            connected_ports = []
            for port_name in port_simulator.get_all_ports():
                port = port_simulator.get_port(port_name)
                if port and port.is_connected:
                    # 检查端口是否达到上限
                    if port.send_count < port.send_limit:
                        connected_ports.append(port_name)

            if not connected_ports:
                # 尝试获取所有已连接的端口（即使达到上限）
                for port_name in port_simulator.get_all_ports():
                    port = port_simulator.get_port(port_name)
                    if port and port.is_connected:
                        connected_ports.append(port_name)

                if not connected_ports:
                    logger.error("没有已连接的端口")
                    return False, {'port_name': None, 'error': '无可用端口'}

                # 选择一个端口并清除其计数（临时解决方案）
                port_name = random.choice(connected_ports)
                port = port_simulator.get_port(port_name)
                logger.warning(f"端口 {port_name} 已达上限，尝试继续使用")
            else:
                # 随机选择一个可用端口
                port_name = random.choice(connected_ports)

            # 发送短信
            success, message, duration = port_simulator.send_sms(port_name, phone, content)

            # 获取端口信息
            port = port_simulator.get_port(port_name)
            port_info = {
                'port_name': port_name,
                'sender_number': getattr(port, 'sim_number', f"SIM_{port_name}"),
                'operator_name': getattr(port, 'carrier', 'unknown'),
                'send_count': getattr(port, 'send_count', 0),
                'send_limit': getattr(port, 'send_limit', 60)
            }

            logger.info(f"端口 {port_name} 发送{'成功' if success else '失败'}, "
                        f"计数: {port_info['send_count']}/{port_info['send_limit']}")

            return success, port_info

        except Exception as e:
            logger.error(f"模拟发送失败: {e}")
            import traceback
            traceback.print_exc()
            return False, {'port_name': None, 'error': str(e)}

    def _add_message_to_queue(self, message: Dict[str, Any]):
        """添加消息到队列"""
        try:
            priority = message.get('priority', 5)
            # 优先级队列：数字越小优先级越高
            import time
            priority_key = (10 - priority, time.time())
            self.message_queue.put((priority_key, message))
        except queue.Full:
            logger.warning("消息队列已满")
        except Exception as e:
            logger.error(f"添加消息到队列失败: {e}")

    def _send_message(self, message: Dict[str, Any]):
        """发送单条消息 - 完整版"""
        try:
            msg_id = message['details_id']
            phone = message['recipient_number']
            content = message.get('message_content', '')

            # 更新消息状态为发送中
            self._update_message_status(msg_id, 'sending')

            # 使用模拟器发送，并获取端口信息
            success, port_info = self._simulate_send_with_port_info(phone, content)

            if success:
                # 发送成功，记录端口信息
                self._update_message_with_port_info(msg_id, port_info, 'success')
                self._on_message_success(msg_id)
            else:
                # 发送失败，检查重试
                retry_count = message.get('retry_count', 0)
                if retry_count < 3:  # 最大重试3次
                    # 重试
                    message['retry_count'] = retry_count + 1
                    self._add_message_to_queue(message)
                    self._update_message_status(msg_id, 'retry')
                    logger.info(f"消息 {msg_id} 加入重试队列，重试次数: {retry_count + 1}")
                else:
                    # 最终失败
                    self._update_message_with_port_info(msg_id, port_info, 'failed')
                    self._on_message_failed(msg_id)
                    logger.info(f"消息 {msg_id} 最终失败")

        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            import traceback
            traceback.print_exc()

            # 确保更新消息状态
            try:
                self._update_message_status(message['details_id'], 'failed')
                self._on_message_failed(message['details_id'])
            except:
                pass


# 全局任务执行器实例
task_executor = TaskExecutor()