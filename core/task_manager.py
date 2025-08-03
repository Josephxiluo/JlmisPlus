"""
短信任务管理模块 - 兼容数据库版本
"""
from datetime import datetime
import threading
import time


class TaskManager:
    """任务管理器 - 数据库兼容版本"""

    def __init__(self, db_manager=None):
        """初始化任务管理器"""
        self.db_manager = db_manager
        self.tasks = {}  # 内存中的任务缓存
        self.running_tasks = set()  # 正在运行的任务
        self.task_counter = 0  # 任务计数器

        # 如果有数据库管理器，从数据库加载任务
        if self.db_manager:
            self.load_tasks_from_db()

    def load_tasks_from_db(self):
        """从数据库加载任务"""
        try:
            if hasattr(self.db_manager, 'session'):
                from core.database import Task
                db_tasks = self.db_manager.session.query(Task).all()

                for db_task in db_tasks:
                    self.tasks[str(db_task.id)] = {
                        'id': str(db_task.id),
                        'name': db_task.name,
                        'numbers': db_task.phone_numbers,
                        'message_content': db_task.message_content,
                        'subject': getattr(db_task, 'subject', ''),
                        'total_count': db_task.total_count,
                        'success_count': db_task.success_count,
                        'failed_count': db_task.failed_count,
                        'status': db_task.status,
                        'progress': self.calculate_progress(db_task.success_count, db_task.failed_count,
                                                            db_task.total_count),
                        'created_time': db_task.created_time.isoformat() if db_task.created_time else None,
                        'started_time': db_task.started_time.isoformat() if db_task.started_time else None,
                        'completed_time': db_task.completed_time.isoformat() if db_task.completed_time else None,
                        'created_by': db_task.created_by
                    }

                    if db_task.status == 'running':
                        self.running_tasks.add(str(db_task.id))

                self.task_counter = max([int(task_id) for task_id in self.tasks.keys()] + [0])
                print(f"从数据库加载了 {len(self.tasks)} 个任务")

        except Exception as e:
            print(f"从数据库加载任务失败: {e}")

    def calculate_progress(self, success_count, failed_count, total_count):
        """计算进度"""
        if total_count == 0:
            return "0.00% (0/0)"

        completed = success_count + failed_count
        percentage = (completed / total_count) * 100
        return f"{percentage:.2f}% ({completed}/{total_count})"

    def create_task(self, name, numbers, subject, content, template=None, options=None):
        """创建新任务"""
        try:
            # 如果有数据库管理器，保存到数据库
            if self.db_manager:
                # 获取当前用户ID（这里简化处理，实际应该从session获取）
                created_by = 1  # 默认管理员用户ID

                task_id = self.db_manager.create_task(
                    name=name,
                    phone_numbers=numbers,
                    message_content=content,
                    created_by=created_by,
                    subject=subject
                )

                # 创建内存中的任务对象
                task_data = {
                    'id': str(task_id),
                    'name': name,
                    'numbers': numbers,
                    'message_content': content,
                    'subject': subject,
                    'template': template,
                    'options': options,
                    'progress': f'0.00% (0/{len(numbers)})',
                    'success_count': 0,
                    'failed_count': 0,
                    'total_count': len(numbers),
                    'status': 'pending',
                    'created_time': datetime.now().isoformat(),
                    'created_by': created_by
                }

                self.tasks[str(task_id)] = task_data
                return str(task_id)

            else:
                # 原始的内存模式
                self.task_counter += 1
                task_id = f"task_{self.task_counter}"

                self.tasks[task_id] = {
                    'id': task_id,
                    'name': name,
                    'numbers': numbers,
                    'message_content': content,
                    'subject': subject,
                    'template': template,
                    'options': options,
                    'progress': f'0.00% (0/{len(numbers)})',
                    'success_count': 0,
                    'failed_count': 0,
                    'total_count': len(numbers),
                    'status': 'pending',
                    'created_time': datetime.now().isoformat()
                }

                return task_id

        except Exception as e:
            print(f"创建任务失败: {e}")
            return None

    def get_task(self, task_id):
        """获取任务信息"""
        return self.tasks.get(task_id)

    def get_all_tasks(self):
        """获取所有任务"""
        return self.tasks

    def update_task_progress(self, task_id, success=None, failed=None):
        """更新任务进度"""
        try:
            if task_id not in self.tasks:
                return False

            task = self.tasks[task_id]

            if success is not None:
                task['success_count'] = success
            if failed is not None:
                task['failed_count'] = failed

            completed = task['success_count'] + task['failed_count']
            total = task['total_count']

            if total > 0:
                progress = (completed / total) * 100
                task['progress'] = f"{progress:.2f}% ({completed}/{total})"

            # 如果任务完成，自动停止
            if completed >= total:
                self.stop_task(task_id)

            # 同步到数据库
            if self.db_manager:
                self.db_manager.update_task_status(
                    int(task_id.replace('task_', '')),
                    task['status'],
                    success_count=task['success_count'],
                    failed_count=task['failed_count']
                )

            return True

        except Exception as e:
            print(f"更新任务进度失败: {e}")
            return False

    def start_task(self, task_id):
        """启动任务"""
        if task_id in self.tasks:
            self.tasks[task_id]['status'] = 'running'
            self.running_tasks.add(task_id)

            # 同步到数据库
            if self.db_manager:
                try:
                    db_task_id = int(task_id.replace('task_', '')) if task_id.startswith('task_') else int(task_id)
                    self.db_manager.update_task_status(db_task_id, 'running')
                except:
                    pass

            return True
        return False

    def stop_task(self, task_id):
        """停止任务"""
        if task_id in self.tasks:
            # 如果任务完成，标记为completed，否则为stopped
            task = self.tasks[task_id]
            completed = task['success_count'] + task['failed_count']

            if completed >= task['total_count']:
                self.tasks[task_id]['status'] = 'completed'
            else:
                self.tasks[task_id]['status'] = 'stopped'

            self.running_tasks.discard(task_id)

            # 同步到数据库
            if self.db_manager:
                try:
                    db_task_id = int(task_id.replace('task_', '')) if task_id.startswith('task_') else int(task_id)
                    self.db_manager.update_task_status(db_task_id, self.tasks[task_id]['status'])
                except:
                    pass

            return True
        return False

    def delete_task(self, task_id):
        """删除任务"""
        if task_id in self.tasks:
            self.stop_task(task_id)
            del self.tasks[task_id]

            # 从数据库删除（这里简化处理，实际可能需要软删除）
            # 注意：实际项目中可能不想直接删除数据库记录

            return True
        return False

    def stop_all_tasks(self):
        """停止所有任务"""
        for task_id in list(self.running_tasks):
            self.stop_task(task_id)

    def get_running_tasks(self):
        """获取正在运行的任务"""
        return [self.tasks[task_id] for task_id in self.running_tasks if task_id in self.tasks]

    def is_task_running(self, task_id):
        """检查任务是否正在运行"""
        return task_id in self.running_tasks

    def get_task_by_name(self, name):
        """根据名称获取任务"""
        for task_id, task in self.tasks.items():
            if task['name'] == name:
                return task_id, task
        return None, None

    def update_task_info(self, task_id, **kwargs):
        """更新任务信息"""
        if task_id not in self.tasks:
            return False

        task = self.tasks[task_id]
        for key, value in kwargs.items():
            if key in task:
                task[key] = value

        # 如果更新了号码列表，需要重新计算total和progress
        if 'numbers' in kwargs:
            phone_list = kwargs['numbers']
            if isinstance(phone_list, str):
                phone_list = [num.strip() for num in phone_list.split('\n') if num.strip()]

            task['numbers'] = phone_list
            task['total_count'] = len(phone_list)

            # 重新计算进度
            completed = task['success_count'] + task['failed_count']
            if task['total_count'] > 0:
                progress = (completed / task['total_count']) * 100
                task['progress'] = f"{progress:.2f}% ({completed}/{task['total_count']})"

        return True


class TaskWorker:
    """任务执行器 - 兼容数据库版本"""

    def __init__(self, task_manager, port_manager, message_sender):
        self.task_manager = task_manager
        self.port_manager = port_manager
        self.message_sender = message_sender
        self.is_running = False
        self.worker_thread = None

    def start(self):
        """启动任务执行器"""
        if not self.is_running:
            self.is_running = True
            self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self.worker_thread.start()

    def stop(self):
        """停止任务执行器"""
        self.is_running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=1)

    def _worker_loop(self):
        """工作循环"""
        while self.is_running:
            try:
                running_tasks = self.task_manager.get_running_tasks()

                for task in running_tasks:
                    if not self.is_running:
                        break

                    # 获取可用端口
                    available_ports = self.port_manager.get_running_ports() if hasattr(self.port_manager,
                                                                                       'get_running_ports') else []
                    if not available_ports:
                        continue

                    # 处理任务
                    self._process_task(task, available_ports)

                time.sleep(0.1)  # 短暂休息

            except Exception as e:
                print(f"任务执行器错误: {e}")
                time.sleep(1)

    def _process_task(self, task, available_ports):
        """处理单个任务"""
        task_id = task['id']

        # 检查任务是否还需要处理
        completed = task['success_count'] + task['failed_count']
        if completed >= task['total_count']:
            self.task_manager.stop_task(task_id)
            return

        # 获取下一个要发送的号码
        if completed < len(task['numbers']):
            phone_number = task['numbers'][completed]

            # 选择一个端口
            port_name = available_ports[completed % len(available_ports)]

            # 发送短信
            success = False
            if hasattr(self.message_sender, 'send_message'):
                success = self.message_sender.send_message(
                    port_name=port_name,
                    phone_number=phone_number,
                    message=task['message_content'],
                    subject=task.get('subject', '')
                )

            # 更新任务进度
            if success:
                self.task_manager.update_task_progress(task_id, task['success_count'] + 1, task['failed_count'])
                if hasattr(self.port_manager, 'update_port_success'):
                    self.port_manager.update_port_success(port_name)
            else:
                self.task_manager.update_task_progress(task_id, task['success_count'], task['failed_count'] + 1)