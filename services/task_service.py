"""
任务服务 - 集成任务执行器和UI
Task service - Integrate task executor with UI
"""

import sys
import threading
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import settings
from config.logging_config import get_logger
from core.task_executor import task_executor
from services.credit_service import credit_service
from database.connection import execute_query, execute_update

logger = get_logger('services.task')


class TaskService:
    """任务服务类 - 桥接UI和执行器"""

    def __init__(self):
        """初始化任务服务"""
        self.executor = task_executor
        self.credit_service = credit_service

        # UI更新回调
        self.ui_update_callback: Optional[Callable] = None

        # 确保执行器设置了积分服务
        if not self.executor.credit_service:
            try:
                self.executor.set_credit_service(credit_service)
                print("[DEBUG] 任务执行器已注入积分服务")
            except Exception as e:
                print(f"[WARNING] 无法注入积分服务: {e}")

        # 设置回调
        self.executor.progress_callback = self._on_progress
        self.executor.status_callback = self._on_status_change

        logger.info("任务服务初始化完成")

    def create_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建新任务"""
        try:
            # 验证积分余额
            operator_id = task_data.get('operators_id')
            target_count = len(task_data.get('targets', []))
            mode = task_data.get('mode', 'sms')

            balance_check = self.credit_service.check_balance(
                operator_id, target_count, mode
            )

            if not balance_check['success']:
                return balance_check

            # 插入任务
            insert_query = """
                INSERT INTO tasks (
                    tasks_title, tasks_mode, tasks_subject_name, 
                    tasks_message_content, templates_id,
                    tasks_total_count, tasks_pending_count, tasks_status,
                    operators_id, channel_users_id, created_time
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING tasks_id
            """

            params = (
                task_data.get('title'),
                mode,
                task_data.get('subject', ''),
                task_data.get('message_content'),
                task_data.get('templates_id'),
                target_count,
                target_count,
                'draft',
                operator_id,
                task_data.get('channel_users_id', 1),
                datetime.now()
            )

            task_id = execute_update(insert_query, params)

            if task_id:
                # 批量插入消息详情
                for phone in task_data.get('targets', []):
                    msg_query = """
                        INSERT INTO task_message_details (
                            tasks_id, recipient_number, details_status,
                            created_time, priority
                        ) VALUES (%s, %s, %s, %s, %s)
                    """
                    execute_update(msg_query, (task_id, phone, 'pending', datetime.now(), 5))

                logger.info(f"任务创建成功: ID={task_id}, 消息数={target_count}")
                return {
                    'success': True,
                    'task_id': task_id,
                    'message': '任务创建成功'
                }
            else:
                return {'success': False, 'message': '任务创建失败'}

        except Exception as e:
            logger.error(f"创建任务失败: {e}")
            return {'success': False, 'message': str(e)}

    def start_task(self, task_id: int) -> Dict[str, Any]:
        """启动任务 - 修复版，添加端口检查"""
        try:
            # 检查是否有可用端口
            from services.port_service import port_service
            ports_result = port_service.get_ports()

            if ports_result.get('success'):
                ports = ports_result.get('ports', [])
                connected_ports = [p for p in ports if p.get('is_connected', False)]

                if not connected_ports:
                    return {
                        'success': False,
                        'message': '没有可用的端口，请先启动至少一个端口'
                    }

                print(f"[DEBUG] 找到 {len(connected_ports)} 个已连接端口")

            # 在新线程中启动任务，避免阻塞UI
            def start_in_thread():
                result = self.executor.start_task(task_id)
                if self.ui_update_callback:
                    self.ui_update_callback('task_started', task_id, result)

            thread = threading.Thread(target=start_in_thread, daemon=True)
            thread.start()

            return {'success': True, 'message': '任务启动中...'}

        except Exception as e:
            logger.error(f"启动任务失败: {e}")
            return {'success': False, 'message': str(e)}

    def pause_task(self, task_id: int) -> Dict[str, Any]:
        """暂停任务"""
        try:
            if self.executor.current_task and self.executor.current_task['id'] == task_id:
                return self.executor.pause_task()
            else:
                # 直接更新数据库状态
                query = "UPDATE tasks SET tasks_status = 'paused' WHERE tasks_id = %s"
                execute_update(query, (task_id,))
                return {'success': True, 'message': '任务已暂停'}

        except Exception as e:
            logger.error(f"暂停任务失败: {e}")
            return {'success': False, 'message': str(e)}

    def resume_task(self, task_id: int) -> Dict[str, Any]:
        """恢复任务"""
        try:
            if self.executor.current_task and self.executor.current_task['id'] == task_id:
                return self.executor.resume_task()
            else:
                # 重新启动任务
                return self.start_task(task_id)

        except Exception as e:
            logger.error(f"恢复任务失败: {e}")
            return {'success': False, 'message': str(e)}

    def stop_task(self, task_id: int) -> Dict[str, Any]:
        """停止任务"""
        try:
            if self.executor.current_task and self.executor.current_task['id'] == task_id:
                return self.executor.stop_task()
            else:
                # 直接更新数据库状态
                query = "UPDATE tasks SET tasks_status = 'cancelled' WHERE tasks_id = %s"
                execute_update(query, (task_id,))
                return {'success': True, 'message': '任务已停止'}

        except Exception as e:
            logger.error(f"停止任务失败: {e}")
            return {'success': False, 'message': str(e)}

    def delete_task(self, task_id: int) -> Dict[str, Any]:
        """删除任务"""
        try:
            # 检查任务状态
            query = "SELECT tasks_status FROM tasks WHERE tasks_id = %s"
            result = execute_query(query, (task_id,), fetch_one=True)

            if not result:
                return {'success': False, 'message': '任务不存在'}

            status = result[0]
            if status in ['running', 'sending']:
                return {'success': False, 'message': '不能删除正在执行的任务'}

            # 删除消息详情
            execute_update("DELETE FROM task_message_details WHERE tasks_id = %s", (task_id,))

            # 删除任务
            execute_update("DELETE FROM tasks WHERE tasks_id = %s", (task_id,))

            logger.info(f"任务删除成功: ID={task_id}")
            return {'success': True, 'message': '任务已删除'}

        except Exception as e:
            logger.error(f"删除任务失败: {e}")
            return {'success': False, 'message': str(e)}

    def retry_failed(self, task_id: int) -> Dict[str, Any]:
        """重试失败的消息"""
        try:
            result = self.executor.retry_failed_messages(task_id)
            return result

        except Exception as e:
            logger.error(f"重试失败消息失败: {e}")
            return {'success': False, 'message': str(e)}

    def get_user_tasks(self, user_id: int, status: str = None,
                      page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """获取用户任务列表"""
        try:
            # 构建查询条件
            where_parts = ["operators_id = %s"]
            params = [user_id]

            if status:
                where_parts.append("tasks_status = %s")
                params.append(status)

            where_clause = " AND ".join(where_parts)

            # 计算偏移量
            offset = (page - 1) * page_size

            # 查询总数
            count_query = f"""
                SELECT COUNT(*) 
                FROM tasks 
                WHERE {where_clause}
            """
            count_result = execute_query(count_query, tuple(params), fetch_one=True)
            total_count = count_result[0] if count_result else 0

            # 查询任务列表
            query = f"""
                SELECT 
                    tasks_id as id,
                    tasks_title as title,
                    tasks_status as status,
                    tasks_total_count as total,
                    tasks_success_count as success_count,
                    tasks_failed_count as failed_count,
                    tasks_pending_count as pending_count,
                    tasks_mode as mode,
                    tasks_message_content as content,
                    created_time,
                    updated_time
                FROM tasks 
                WHERE {where_clause}
                ORDER BY created_time DESC
                LIMIT %s OFFSET %s
            """

            params.extend([page_size, offset])
            results = execute_query(query, tuple(params), dict_cursor=True)

            # 转换数据格式
            tasks = []
            for row in results:
                # 计算已发送数量和进度
                sent = row['success_count'] + row['failed_count']
                progress = 0
                if row['total'] > 0:
                    progress = (sent / row['total']) * 100

                task = {
                    'id': row['id'],
                    'title': row['title'] or f"任务{row['id']}",
                    'status': row['status'] or 'draft',
                    'total': row['total'] or 0,
                    'sent': sent,
                    'success_count': row['success_count'] or 0,
                    'failed_count': row['failed_count'] or 0,
                    'pending_count': row['pending_count'] or 0,
                    'progress': round(progress, 1),
                    'mode': row['mode'] or 'sms',
                    'content': row['content'] or '',
                    'created_time': row['created_time'],
                    'updated_time': row['updated_time']
                }
                tasks.append(task)

            return {
                'success': True,
                'tasks': tasks,
                'total_count': total_count,
                'page': page,
                'page_size': page_size,
                'total_pages': (total_count + page_size - 1) // page_size if total_count > 0 else 0
            }

        except Exception as e:
            logger.error(f"获取任务列表失败: {e}")
            return {
                'success': False,
                'message': str(e),
                'tasks': [],
                'total_count': 0
            }

    def test_task(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """测试任务（不消耗积分）"""
        try:
            # 模拟发送
            test_phone = data.get('test_phone', '13800138000')
            test_content = data.get('content', '测试短信')

            # 使用模拟器发送
            from core.simulator.port_simulator import port_simulator

            # 连接一个端口
            port_name = "COM1"
            port_simulator.connect_port(port_name)

            # 发送测试
            success, message, duration = port_simulator.send_sms(
                port_name, test_phone, test_content
            )

            return {
                'success': success,
                'message': message,
                'send_time': datetime.now().strftime('%H:%M:%S'),
                'duration': duration
            }

        except Exception as e:
            logger.error(f"测试任务失败: {e}")
            return {'success': False, 'message': str(e)}

    def update_task_content(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新任务内容"""
        try:
            task_id = data.get('task_id')
            content = data.get('content')

            query = """
                UPDATE tasks 
                SET tasks_message_content = %s, updated_time = %s
                WHERE tasks_id = %s
            """

            execute_update(query, (content, datetime.now(), task_id))

            # 同时更新消息详情
            msg_query = """
                UPDATE task_message_details
                SET message_content = %s
                WHERE tasks_id = %s AND details_status = 'pending'
            """

            execute_update(msg_query, (content, task_id))

            return {'success': True, 'message': '任务内容已更新'}

        except Exception as e:
            logger.error(f"更新任务内容失败: {e}")
            return {'success': False, 'message': str(e)}

    def stop_all_tasks(self, user_id: int) -> Dict[str, Any]:
        """停止所有任务"""
        try:
            # 停止当前执行的任务
            if self.executor.current_task:
                self.executor.stop_task()

            # 更新数据库中所有运行中的任务
            query = """
                UPDATE tasks 
                SET tasks_status = 'paused' 
                WHERE operators_id = %s AND tasks_status = 'running'
            """

            affected = execute_update(query, (user_id,))

            return {'success': True, 'count': affected or 0}

        except Exception as e:
            logger.error(f"停止所有任务失败: {e}")
            return {'success': False, 'message': str(e)}

    def start_all_tasks(self, user_id: int) -> Dict[str, Any]:
        """开始所有任务"""
        try:
            query = """
                UPDATE tasks 
                SET tasks_status = 'pending' 
                WHERE operators_id = %s AND tasks_status IN ('draft', 'paused')
            """

            affected = execute_update(query, (user_id,))

            return {'success': True, 'count': affected or 0}

        except Exception as e:
            logger.error(f"开始所有任务失败: {e}")
            return {'success': False, 'message': str(e)}

    def clear_completed_tasks(self, user_id: int) -> Dict[str, Any]:
        """清理完成的任务"""
        try:
            # 先删除消息详情
            msg_query = """
                DELETE FROM task_message_details
                WHERE tasks_id IN (
                    SELECT tasks_id FROM tasks
                    WHERE operators_id = %s AND tasks_status = 'completed'
                )
            """
            execute_update(msg_query, (user_id,))

            # 删除任务
            query = """
                DELETE FROM tasks 
                WHERE operators_id = %s AND tasks_status = 'completed'
            """

            affected = execute_update(query, (user_id,))

            return {'success': True, 'count': affected or 0}

        except Exception as e:
            logger.error(f"清理完成任务失败: {e}")
            return {'success': False, 'message': str(e)}

    def _on_progress(self, task_id: int, stats: Dict[str, Any]):
        """进度更新回调"""
        if self.ui_update_callback:
            self.ui_update_callback('progress', task_id, stats)

    def _on_status_change(self, task_id: int, new_status: str):
        """状态变更回调"""
        if self.ui_update_callback:
            self.ui_update_callback('status', task_id, {'status': new_status})

    def set_ui_callback(self, callback: Callable):
        """设置UI更新回调"""
        self.ui_update_callback = callback


# 全局任务服务实例
task_service = TaskService()