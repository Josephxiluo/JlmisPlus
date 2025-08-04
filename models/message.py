"""
猫池短信系统消息模型 - tkinter版
Message models for SMS Pool System - tkinter version
"""

import sys
import re
from enum import Enum
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from .base import BaseModel, ModelManager
    from config.logging_config import get_logger, log_message_send, log_error
except ImportError:
    # 简化处理
    from base import BaseModel, ModelManager

    import logging


    def get_logger(name='models.message'):
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger


    def log_message_send(task_id, recipient, port, status, details=None):
        logger = get_logger()
        message = f"[消息发送] 任务ID={task_id} 接收号码={recipient} 端口={port} 状态={status}"
        if details:
            message += f" - {details}"

        if status == 'success':
            logger.info(message)
        elif status in ['failed', 'timeout']:
            logger.warning(message)
        else:
            logger.debug(message)


    def log_error(message, error=None):
        logger = get_logger()
        logger.error(f"{message}: {error}" if error else message)

logger = get_logger('models.message')


class MessageStatus(Enum):
    """消息状态枚举"""
    PENDING = "pending"  # 待发送
    SENDING = "sending"  # 发送中
    SUCCESS = "success"  # 发送成功
    FAILED = "failed"  # 发送失败
    TIMEOUT = "timeout"  # 发送超时
    CANCELLED = "cancelled"  # 已取消
    RETRY = "retry"  # 重试中

    @classmethod
    def get_choices(cls):
        """获取所有选择项"""
        return [status.value for status in cls]

    @classmethod
    def get_display_names(cls):
        """获取显示名称映射"""
        return {
            cls.PENDING.value: "待发送",
            cls.SENDING.value: "发送中",
            cls.SUCCESS.value: "发送成功",
            cls.FAILED.value: "发送失败",
            cls.TIMEOUT.value: "发送超时",
            cls.CANCELLED.value: "已取消",
            cls.RETRY.value: "重试中"
        }


class MessageCarrier(Enum):
    """运营商枚举"""
    MOBILE = "mobile"  # 中国移动
    UNICOM = "unicom"  # 中国联通
    TELECOM = "telecom"  # 中国电信
    UNKNOWN = "unknown"  # 未知

    @classmethod
    def get_choices(cls):
        """获取所有选择项"""
        return [carrier.value for carrier in cls]

    @classmethod
    def get_display_names(cls):
        """获取显示名称映射"""
        return {
            cls.MOBILE.value: "中国移动",
            cls.UNICOM.value: "中国联通",
            cls.TELECOM.value: "中国电信",
            cls.UNKNOWN.value: "未知"
        }


def detect_carrier(phone_number: str) -> str:
    """检测手机号码运营商"""
    # 移除国际前缀和特殊字符
    clean_phone = re.sub(r'[^\d]', '', phone_number)
    if clean_phone.startswith('86'):
        clean_phone = clean_phone[2:]

    if len(clean_phone) != 11 or not clean_phone.startswith('1'):
        return MessageCarrier.UNKNOWN.value

    # 号段规则（简化版）
    prefix = clean_phone[:3]

    # 中国移动
    mobile_prefixes = [
        '134', '135', '136', '137', '138', '139',  # 2G
        '147', '150', '151', '152', '157', '158', '159',  # 3G
        '178', '182', '183', '184', '187', '188',  # 4G
        '198',  # 5G
    ]

    # 中国联通
    unicom_prefixes = [
        '130', '131', '132',  # 2G
        '145', '155', '156',  # 3G
        '166', '175', '176', '185', '186',  # 4G
        '196',  # 5G
    ]

    # 中国电信
    telecom_prefixes = [
        '133', '153',  # 3G
        '173', '177', '180', '181', '189',  # 4G
        '191', '193', '199',  # 5G
    ]

    if prefix in mobile_prefixes:
        return MessageCarrier.MOBILE.value
    elif prefix in unicom_prefixes:
        return MessageCarrier.UNICOM.value
    elif prefix in telecom_prefixes:
        return MessageCarrier.TELECOM.value
    else:
        return MessageCarrier.UNKNOWN.value


def validate_phone_number(phone: str, international: bool = False) -> bool:
    """验证手机号码格式"""
    if international:
        # 国际号码格式：+国家代码+号码
        pattern = r'^\+\d{8,15}'
        return bool(re.match(pattern, phone))
    else:
        # 国内号码格式：11位数字，1开头
        pattern = r'^1[3-9]\d{9}'
        return bool(re.match(pattern, phone))


@dataclass
class TaskMessage(BaseModel):
    """任务消息明细模型"""

    # 表名
    _table_name: str = "task_message_details"

    # 字段映射（模型字段名 -> 数据库字段名）
    _field_mappings: Dict[str, str] = field(default_factory=lambda: {
        'id': 'detail_id',
        'task_id': 'tasks_id',
        'recipient_number': 'recipient_number',
        'sender_number': 'sender_number',
        'message_content': 'message_content',
        'send_port': 'send_port',
        'carrier': 'carrier',
        'status': 'send_status',
        'retry_count': 'retry_count',
        'max_retry': 'max_retry',
        'send_time': 'send_time',
        'receive_time': 'receive_time',
        'response_content': 'response_content',
        'error_code': 'error_code',
        'error_message': 'error_message',
        'cost': 'cost',
        'priority': 'priority',
        'scheduled_time': 'scheduled_time',
        'remark': 'remark',
        'created_at': 'created_at',
        'updated_at': 'updated_at'
    })

    # 验证规则
    _validation_rules: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        'task_id': {
            'required': True,
            'type': int,
            'min_value': 1,
            'message': '任务ID必须是正整数'
        },
        'recipient_number': {
            'required': True,
            'type': str,
            'min_length': 8,
            'max_length': 20,
            'message': '接收号码长度必须在8-20位之间'
        },
        'message_content': {
            'required': True,
            'type': str,
            'min_length': 1,
            'max_length': 1000,
            'message': '消息内容必须在1-1000个字符之间'
        },
        'status': {
            'required': True,
            'type': str,
            'choices': MessageStatus.get_choices(),
            'message': '消息状态无效'
        },
        'carrier': {
            'type': str,
            'choices': MessageCarrier.get_choices(),
            'message': '运营商类型无效'
        },
        'retry_count': {
            'type': int,
            'min_value': 0,
            'message': '重试次数不能为负数'
        },
        'max_retry': {
            'type': int,
            'min_value': 0,
            'max_value': 10,
            'message': '最大重试次数必须在0-10之间'
        },
        'cost': {
            'type': float,
            'min_value': 0,
            'message': '费用不能为负数'
        },
        'priority': {
            'type': int,
            'min_value': 1,
            'max_value': 10,
            'message': '优先级必须在1-10之间'
        }
    })

    # 关联信息
    task_id: int = 0

    # 号码信息
    recipient_number: str = ""
    sender_number: Optional[str] = field(default=None)
    carrier: str = MessageCarrier.UNKNOWN.value

    # 消息内容
    message_content: str = ""

    # 发送信息
    send_port: Optional[str] = field(default=None)
    status: str = MessageStatus.PENDING.value

    # 重试控制
    retry_count: int = 0
    max_retry: int = 3

    # 时间信息
    send_time: Optional[datetime] = field(default=None)
    receive_time: Optional[datetime] = field(default=None)
    scheduled_time: Optional[datetime] = field(default=None)

    # 响应信息
    response_content: Optional[str] = field(default=None)
    error_code: Optional[str] = field(default=None)
    error_message: Optional[str] = field(default=None)

    # 其他信息
    cost: float = 0.0
    priority: int = 5
    remark: Optional[str] = field(default=None)

    def __post_init__(self):
        """初始化后处理"""
        super().__post_init__()

        # 自动检测运营商
        if self.carrier == MessageCarrier.UNKNOWN.value and self.recipient_number:
            self.carrier = detect_carrier(self.recipient_number)

    def get_status_display(self) -> str:
        """获取状态显示名称"""
        return MessageStatus.get_display_names().get(self.status, self.status)

    def get_carrier_display(self) -> str:
        """获取运营商显示名称"""
        return MessageCarrier.get_display_names().get(self.carrier, self.carrier)

    def is_pending(self) -> bool:
        """是否为待发送状态"""
        return self.status == MessageStatus.PENDING.value

    def is_sending(self) -> bool:
        """是否为发送中状态"""
        return self.status == MessageStatus.SENDING.value

    def is_success(self) -> bool:
        """是否发送成功"""
        return self.status == MessageStatus.SUCCESS.value

    def is_failed(self) -> bool:
        """是否发送失败"""
        return self.status in [MessageStatus.FAILED.value, MessageStatus.TIMEOUT.value]

    def is_cancelled(self) -> bool:
        """是否已取消"""
        return self.status == MessageStatus.CANCELLED.value

    def can_retry(self) -> bool:
        """是否可以重试"""
        return (self.is_failed() and
                self.retry_count < self.max_retry and
                self.status != MessageStatus.CANCELLED.value)

    def can_cancel(self) -> bool:
        """是否可以取消"""
        return self.status in [MessageStatus.PENDING.value, MessageStatus.RETRY.value]

    def update_status(self, new_status: str, port: str = None,
                      error_code: str = None, error_message: str = None,
                      response: str = None, auto_save: bool = True) -> bool:
        """更新消息状态"""
        try:
            old_status = self.status
            self.status = new_status
            current_time = datetime.now()

            # 设置时间戳和相关信息
            if new_status == MessageStatus.SENDING.value:
                self.send_time = current_time
                if port:
                    self.send_port = port

            elif new_status == MessageStatus.SUCCESS.value:
                self.receive_time = current_time
                if response:
                    self.response_content = response
                # 清除错误信息
                self.error_code = None
                self.error_message = None

            elif new_status in [MessageStatus.FAILED.value, MessageStatus.TIMEOUT.value]:
                self.receive_time = current_time
                if error_code:
                    self.error_code = error_code
                if error_message:
                    self.error_message = error_message

            elif new_status == MessageStatus.RETRY.value:
                self.retry_count += 1
                # 清除之前的错误信息
                self.error_code = None
                self.error_message = None

            # 记录日志
            log_message_send(
                task_id=self.task_id,
                recipient=self.recipient_number,
                port=self.send_port or "未知",
                status=new_status,
                details=f"状态变更: {old_status} -> {new_status}"
            )

            # 自动保存
            if auto_save:
                return self.save()

            return True

        except Exception as e:
            log_error("更新消息状态失败", error=e)
            return False

    def mark_as_sending(self, port: str) -> bool:
        """标记为发送中"""
        return self.update_status(MessageStatus.SENDING.value, port=port)

    def mark_as_success(self, response: str = None) -> bool:
        """标记为发送成功"""
        return self.update_status(MessageStatus.SUCCESS.value, response=response)

    def mark_as_failed(self, error_code: str = None, error_message: str = None) -> bool:
        """标记为发送失败"""
        return self.update_status(
            MessageStatus.FAILED.value,
            error_code=error_code,
            error_message=error_message
        )

    def mark_as_timeout(self) -> bool:
        """标记为发送超时"""
        return self.update_status(
            MessageStatus.TIMEOUT.value,
            error_code="TIMEOUT",
            error_message="发送超时"
        )

    def mark_as_cancelled(self) -> bool:
        """标记为已取消"""
        return self.update_status(MessageStatus.CANCELLED.value)

    def retry_send(self) -> bool:
        """重试发送"""
        if not self.can_retry():
            return False

        return self.update_status(MessageStatus.RETRY.value)

    def get_duration(self) -> Optional[float]:
        """获取发送耗时（秒）"""
        if not self.send_time or not self.receive_time:
            return None

        duration = self.receive_time - self.send_time
        return duration.total_seconds()

    def validate_phone_number(self, international: bool = False) -> bool:
        """验证接收号码格式"""
        return validate_phone_number(self.recipient_number, international)

    def format_phone_number(self) -> str:
        """格式化显示号码"""
        phone = self.recipient_number

        # 国内号码格式化：138****1234
        if len(phone) == 11 and phone.startswith('1'):
            return f"{phone[:3]}****{phone[-4:]}"

        # 国际号码简单处理
        if phone.startswith('+'):
            if len(phone) > 8:
                return f"{phone[:4]}****{phone[-4:]}"

        return phone

    def get_summary(self) -> Dict[str, Any]:
        """获取消息摘要"""
        return {
            'id': self.id,
            'task_id': self.task_id,
            'recipient': self.recipient_number,
            'recipient_formatted': self.format_phone_number(),
            'sender': self.sender_number,
            'carrier': self.carrier,
            'carrier_display': self.get_carrier_display(),
            'status': self.status,
            'status_display': self.get_status_display(),
            'send_port': self.send_port,
            'retry_count': self.retry_count,
            'max_retry': self.max_retry,
            'cost': self.cost,
            'priority': self.priority,
            'timing': {
                'send_time': self.send_time.isoformat() if self.send_time else None,
                'receive_time': self.receive_time.isoformat() if self.receive_time else None,
                'scheduled_time': self.scheduled_time.isoformat() if self.scheduled_time else None,
                'duration': self.get_duration()
            },
            'error': {
                'error_code': self.error_code,
                'error_message': self.error_message
            } if self.error_code else None
        }

    @classmethod
    def find_by_task(cls, task_id: int, status: str = None) -> List['TaskMessage']:
        """根据任务ID查找消息"""
        where = "tasks_id = %s"
        params = [task_id]

        if status:
            where += " AND send_status = %s"
            params.append(status)

        return cls.find_all(where, tuple(params), order_by="created_at ASC")

    @classmethod
    def find_pending_messages(cls, task_id: int = None, limit: int = None) -> List['TaskMessage']:
        """查找待发送的消息"""
        where = "send_status IN %s"
        params = [(MessageStatus.PENDING.value, MessageStatus.RETRY.value)]

        if task_id:
            where += " AND tasks_id = %s"
            params.append(task_id)

        return cls.find_all(
            where, tuple(params),
            order_by="priority DESC, scheduled_time ASC, created_at ASC",
            limit=limit
        )

    @classmethod
    def find_failed_messages(cls, task_id: int = None) -> List['TaskMessage']:
        """查找发送失败的消息"""
        where = "send_status IN %s"
        params = [(MessageStatus.FAILED.value, MessageStatus.TIMEOUT.value)]

        if task_id:
            where += " AND tasks_id = %s"
            params.append(task_id)

        return cls.find_all(where, tuple(params))

    @classmethod
    def find_by_phone(cls, phone_number: str, task_id: int = None) -> List['TaskMessage']:
        """根据手机号码查找消息"""
        where = "recipient_number = %s"
        params = [phone_number]

        if task_id:
            where += " AND tasks_id = %s"
            params.append(task_id)

        return cls.find_all(where, tuple(params), order_by="created_at DESC")

    @classmethod
    def get_task_statistics(cls, task_id: int) -> Dict[str, Any]:
        """获取任务消息统计"""
        try:
            from database.connection import get_db_connection
            db = get_db_connection()

            query = f"""
                SELECT 
                    send_status,
                    carrier,
                    COUNT(*) as count,
                    AVG(cost) as avg_cost,
                    SUM(cost) as total_cost
                FROM {cls.get_table_name()}
                WHERE tasks_id = %s
                GROUP BY send_status, carrier
            """

            results = db.execute_query(query, (task_id,), dict_cursor=True)

            stats = {
                'total_count': 0,
                'by_status': {},
                'by_carrier': {},
                'total_cost': 0.0,
                'avg_cost': 0.0
            }

            total_cost = 0.0
            total_count = 0

            for row in results:
                status = row['send_status']
                carrier = row['carrier']
                count = row['count'] or 0
                avg_cost = float(row['avg_cost'] or 0)
                cost = float(row['total_cost'] or 0)

                total_count += count
                total_cost += cost

                # 按状态统计
                if status not in stats['by_status']:
                    stats['by_status'][status] = 0
                stats['by_status'][status] += count

                # 按运营商统计
                if carrier not in stats['by_carrier']:
                    stats['by_carrier'][carrier] = 0
                stats['by_carrier'][carrier] += count

            stats['total_count'] = total_count
            stats['total_cost'] = round(total_cost, 2)
            stats['avg_cost'] = round(total_cost / total_count, 2) if total_count > 0 else 0.0

            return stats

        except Exception as e:
            log_error("获取任务消息统计失败", error=e)
            return {}

    @classmethod
    def bulk_create_from_phones(cls, task_id: int, phone_numbers: List[str],
                                message_content: str, **kwargs) -> bool:
        """批量创建消息"""
        try:
            messages = []

            for phone in phone_numbers:
                # 检测运营商
                carrier = detect_carrier(phone)

                message = cls(
                    task_id=task_id,
                    recipient_number=phone,
                    message_content=message_content,
                    carrier=carrier,
                    status=MessageStatus.PENDING.value,
                    **kwargs
                )

                messages.append(message)

            # 批量插入
            return cls.bulk_insert(messages)

        except Exception as e:
            log_error("批量创建消息失败", error=e)
            return False


# 消息管理器
class TaskMessageManager(ModelManager):
    """任务消息管理器"""

    def __init__(self):
        super().__init__(TaskMessage)

    def create_messages_from_file(self, task_id: int, file_path: str,
                                  message_content: str) -> bool:
        """从文件创建消息"""
        try:
            phone_numbers = self._parse_phone_file(file_path)

            if not phone_numbers:
                log_error("文件中没有找到有效的手机号码")
                return False

            return TaskMessage.bulk_create_from_phones(
                task_id=task_id,
                phone_numbers=phone_numbers,
                message_content=message_content
            )

        except Exception as e:
            log_error("从文件创建消息失败", error=e)
            return False

    def _parse_phone_file(self, file_path: str) -> List[str]:
        """解析手机号码文件"""
        phone_numbers = []
        file_path = Path(file_path)

        try:
            if file_path.suffix.lower() in ['.xlsx', '.xls']:
                # Excel文件
                phone_numbers = self._parse_excel_file(file_path)
            elif file_path.suffix.lower() == '.csv':
                # CSV文件
                phone_numbers = self._parse_csv_file(file_path)
            elif file_path.suffix.lower() == '.txt':
                # 文本文件
                phone_numbers = self._parse_text_file(file_path)

            # 去重和验证
            valid_phones = []
            seen = set()

            for phone in phone_numbers:
                phone = phone.strip()
                if phone and phone not in seen:
                    if validate_phone_number(phone) or validate_phone_number(phone, international=True):
                        valid_phones.append(phone)
                        seen.add(phone)

            return valid_phones

        except Exception as e:
            log_error("解析手机号码文件失败", error=e)
            return []

    def _parse_excel_file(self, file_path: Path) -> List[str]:
        """解析Excel文件"""
        try:
            import pandas as pd

            # 读取Excel文件
            df = pd.read_excel(file_path, dtype=str)

            phone_numbers = []

            # 遍历所有列，查找手机号码
            for column in df.columns:
                for value in df[column].dropna():
                    value = str(value).strip()
                    # 简单的手机号码模式匹配
                    if re.match(r'^[\+]?[1-9]\d{7,14}', value):
                        phone_numbers.append(value)

            return phone_numbers

        except ImportError:
            log_error("需要安装pandas库来读取Excel文件")
            return []
        except Exception as e:
            log_error("解析Excel文件失败", error=e)
            return []

    def _parse_csv_file(self, file_path: Path) -> List[str]:
        """解析CSV文件"""
        try:
            import csv

            phone_numbers = []

            with open(file_path, 'r', encoding='utf-8-sig') as f:
                # 尝试自动检测分隔符
                sample = f.read(1024)
                f.seek(0)

                sniffer = csv.Sniffer()
                delimiter = sniffer.sniff(sample).delimiter

                reader = csv.reader(f, delimiter=delimiter)

                for row in reader:
                    for cell in row:
                        cell = cell.strip()
                        if re.match(r'^[\+]?[1-9]\d{7,14}', cell):
                            phone_numbers.append(cell)

            return phone_numbers

        except Exception as e:
            log_error("解析CSV文件失败", error=e)
            return []

    def _parse_text_file(self, file_path: Path) -> List[str]:
        """解析文本文件"""
        try:
            phone_numbers = []

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

                # 使用正则表达式提取手机号码
                patterns = [
                    r'\+\d{8,15}',  # 国际号码
                    r'1[3-9]\d{9}',  # 国内号码
                ]

                for pattern in patterns:
                    matches = re.findall(pattern, content)
                    phone_numbers.extend(matches)

            return phone_numbers

        except Exception as e:
            log_error("解析文本文件失败", error=e)
            return []

    def get_task_messages(self, task_id: int, status: str = None,
                          page: int = 1, page_size: int = 50) -> Dict[str, Any]:
        """分页获取任务消息"""
        try:
            where = "tasks_id = %s"
            params = [task_id]

            if status:
                where += " AND send_status = %s"
                params.append(status)

            # 计算偏移量
            offset = (page - 1) * page_size

            # 查询消息
            messages = self.model_class.find_all(
                where=where,
                params=tuple(params),
                order_by="priority DESC, created_at ASC",
                limit=page_size,
                offset=offset
            )

            # 统计总数
            total_count = self.model_class.count(where, tuple(params))

            return {
                'messages': messages,
                'total_count': total_count,
                'page': page,
                'page_size': page_size,
                'total_pages': (total_count + page_size - 1) // page_size
            }

        except Exception as e:
            log_error("获取任务消息失败", error=e)
            return {'messages': [], 'total_count': 0, 'page': page, 'page_size': page_size, 'total_pages': 0}

    def retry_failed_messages(self, task_id: int) -> int:
        """重试失败的消息"""
        try:
            failed_messages = TaskMessage.find_failed_messages(task_id)

            retry_count = 0
            for message in failed_messages:
                if message.can_retry() and message.retry_send():
                    retry_count += 1

            return retry_count

        except Exception as e:
            log_error("重试失败消息失败", error=e)
            return 0

    def cancel_pending_messages(self, task_id: int) -> int:
        """取消待发送的消息"""
        try:
            pending_messages = TaskMessage.find_pending_messages(task_id)

            cancel_count = 0
            for message in pending_messages:
                if message.can_cancel() and message.mark_as_cancelled():
                    cancel_count += 1

            return cancel_count

        except Exception as e:
            log_error("取消待发送消息失败", error=e)
            return 0

    def export_messages(self, task_id: int, status: str = None,
                        file_format: str = 'xlsx') -> Optional[str]:
        """导出消息到文件"""
        try:
            messages = TaskMessage.find_by_task(task_id, status)

            if not messages:
                return None

            # 准备导出数据
            export_data = []
            for message in messages:
                export_data.append({
                    '接收号码': message.recipient_number,
                    '发送号码': message.sender_number or '',
                    '运营商': message.get_carrier_display(),
                    '发送端口': message.send_port or '',
                    '状态': message.get_status_display(),
                    '重试次数': message.retry_count,
                    '发送时间': message.send_time.strftime('%Y-%m-%d %H:%M:%S') if message.send_time else '',
                    '接收时间': message.receive_time.strftime('%Y-%m-%d %H:%M:%S') if message.receive_time else '',
                    '错误信息': message.error_message or '',
                    '费用': message.cost,
                    '备注': message.remark or ''
                })

            # 生成文件名
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            status_suffix = f"_{status}" if status else ""
            filename = f"task_{task_id}_messages{status_suffix}_{timestamp}.{file_format}"

            # 导出文件
            if file_format == 'xlsx':
                return self._export_to_excel(export_data, filename)
            elif file_format == 'csv':
                return self._export_to_csv(export_data, filename)
            else:
                log_error(f"不支持的导出格式: {file_format}")
                return None

        except Exception as e:
            log_error("导出消息失败", error=e)
            return None

    def _export_to_excel(self, data: List[Dict], filename: str) -> Optional[str]:
        """导出到Excel文件"""
        try:
            import pandas as pd
            from config.settings import settings

            # 创建DataFrame
            df = pd.DataFrame(data)

            # 保存文件
            file_path = settings.EXPORTS_DIR / filename
            df.to_excel(file_path, index=False, engine='openpyxl')

            return str(file_path)

        except ImportError:
            log_error("需要安装pandas和openpyxl库来导出Excel文件")
            return None
        except Exception as e:
            log_error("导出Excel文件失败", error=e)
            return None

    def _export_to_csv(self, data: List[Dict], filename: str) -> Optional[str]:
        """导出到CSV文件"""
        try:
            import csv
            from config.settings import settings

            if not data:
                return None

            file_path = settings.EXPORTS_DIR / filename

            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)

            return str(file_path)

        except Exception as e:
            log_error("导出CSV文件失败", error=e)
            return None


# 全局消息管理器实例
task_message_manager = TaskMessageManager()