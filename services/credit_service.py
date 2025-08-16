"""
猫池短信系统积分管理服务
Credit management service for SMS Pool System
"""

import sys
import threading
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import settings
from config.logging_config import get_logger
from database.connection import execute_query, execute_update, execute_transaction

logger = get_logger('services.credit')


class CreditService:
    """积分管理服务"""

    def __init__(self):
        """初始化积分服务"""
        self._lock = threading.Lock()

        # 积分费率配置
        self.sms_rate = settings.SMS_RATE  # 短信费率
        self.mms_rate = settings.MMS_RATE  # 彩信费率

        # 预扣除记录（任务ID -> 预扣除数量）
        self.pre_deductions: Dict[int, int] = {}

        logger.info(f"积分服务初始化完成，短信费率: {self.sms_rate}，彩信费率: {self.mms_rate}")

    def check_balance(self, operator_id: int, required_count: int,
                     message_type: str = 'sms') -> Dict[str, Any]:
        """检查积分余额是否充足"""
        try:
            # 计算所需积分
            rate = self.sms_rate if message_type == 'sms' else self.mms_rate
            required_credits = int(required_count * rate)

            # 查询当前余额
            balance = self._get_operator_balance(operator_id)

            if balance is None:
                return {'success': False, 'message': '获取余额失败'}

            if balance < required_credits:
                return {
                    'success': False,
                    'message': f'积分不足：需要 {required_credits} 积分，当前余额 {balance} 积分',
                    'required': required_credits,
                    'balance': balance
                }

            return {
                'success': True,
                'message': '余额充足',
                'required': required_credits,
                'balance': balance
            }

        except Exception as e:
            logger.error(f"检查余额失败: {e}")
            return {'success': False, 'message': str(e)}

    def pre_deduct(self, operator_id: int, count: int, task_id: int,
                   message_type: str = 'sms') -> Dict[str, Any]:
        """预扣除积分（任务开始时）"""
        try:
            with self._lock:
                # 计算积分
                rate = self.sms_rate if message_type == 'sms' else self.mms_rate
                credits = int(count * rate)

                # 获取当前余额
                balance = self._get_operator_balance(operator_id)
                if balance is None or balance < credits:
                    return {'success': False, 'message': '余额不足'}

                # 执行预扣除
                query = """
                    UPDATE channel_operators
                    SET operators_used_credits = operators_used_credits + %s
                    WHERE operators_id = %s
                    AND operators_total_credits - operators_used_credits >= %s
                """

                affected = execute_update(query, (credits, operator_id, credits))

                if affected:
                    # 记录预扣除
                    self.pre_deductions[task_id] = credits

                    # 记录日志
                    self._log_credit_change(
                        operator_id=operator_id,
                        change_type='pre_deduct',
                        amount=-credits,
                        task_id=task_id,
                        description=f'任务 {task_id} 预扣除 {count} 条消息积分'
                    )

                    logger.info(f"预扣除成功：用户 {operator_id}，任务 {task_id}，积分 {credits}")
                    return {'success': True, 'message': '预扣除成功', 'credits': credits}
                else:
                    return {'success': False, 'message': '预扣除失败'}

        except Exception as e:
            logger.error(f"预扣除失败: {e}")
            return {'success': False, 'message': str(e)}

    def actual_deduct(self, operator_id: int, count: int, task_id: int,
                     message_id: Optional[int] = None, message_type: str = 'sms') -> Dict[str, Any]:
        """实际扣除积分（消息发送成功时）"""
        try:
            # 计算积分
            rate = self.sms_rate if message_type == 'sms' else self.mms_rate
            credits = int(count * rate)

            # 记录实际消费日志
            self._log_credit_change(
                operator_id=operator_id,
                change_type='consume',
                amount=-credits,
                task_id=task_id,
                message_id=message_id,
                description=f'发送成功，消费 {count} 条消息积分'
            )

            # 更新预扣除记录
            if task_id in self.pre_deductions:
                self.pre_deductions[task_id] -= credits
                if self.pre_deductions[task_id] <= 0:
                    del self.pre_deductions[task_id]

            logger.debug(f"实际扣除：用户 {operator_id}，任务 {task_id}，积分 {credits}")
            return {'success': True, 'message': '扣除成功', 'credits': credits}

        except Exception as e:
            logger.error(f"实际扣除失败: {e}")
            return {'success': False, 'message': str(e)}

    def rollback(self, operator_id: int, count: int, task_id: int,
                message_type: str = 'sms') -> Dict[str, Any]:
        """回退积分（发送失败或任务取消时）"""
        try:
            with self._lock:
                # 计算积分
                rate = self.sms_rate if message_type == 'sms' else self.mms_rate
                credits = int(count * rate)

                # 回退积分
                query = """
                    UPDATE channel_operators
                    SET operators_used_credits = GREATEST(0, operators_used_credits - %s)
                    WHERE operators_id = %s
                """

                affected = execute_update(query, (credits, operator_id))

                if affected:
                    # 更新预扣除记录
                    if task_id in self.pre_deductions:
                        self.pre_deductions[task_id] -= credits
                        if self.pre_deductions[task_id] <= 0:
                            del self.pre_deductions[task_id]

                    # 记录日志
                    self._log_credit_change(
                        operator_id=operator_id,
                        change_type='rollback',
                        amount=credits,
                        task_id=task_id,
                        description=f'任务 {task_id} 回退 {count} 条消息积分'
                    )

                    logger.info(f"回退成功：用户 {operator_id}，任务 {task_id}，积分 {credits}")
                    return {'success': True, 'message': '回退成功', 'credits': credits}
                else:
                    return {'success': False, 'message': '回退失败'}

        except Exception as e:
            logger.error(f"回退积分失败: {e}")
            return {'success': False, 'message': str(e)}

    def recharge(self, operator_id: int, amount: int, admin_id: int,
                description: str = None) -> Dict[str, Any]:
        """充值积分（管理员操作）"""
        try:
            with self._lock:
                # 更新积分
                query = """
                    UPDATE channel_operators
                    SET operators_total_credits = operators_total_credits + %s
                    WHERE operators_id = %s
                """

                affected = execute_update(query, (amount, operator_id))

                if affected:
                    # 记录日志
                    self._log_credit_change(
                        operator_id=operator_id,
                        change_type='recharge',
                        amount=amount,
                        operator_id_param=admin_id,
                        description=description or f'管理员 {admin_id} 充值'
                    )

                    logger.info(f"充值成功：用户 {operator_id}，金额 {amount}")
                    return {'success': True, 'message': '充值成功', 'amount': amount}
                else:
                    return {'success': False, 'message': '充值失败'}

        except Exception as e:
            logger.error(f"充值失败: {e}")
            return {'success': False, 'message': str(e)}

    def get_balance(self, operator_id: int) -> Dict[str, Any]:
        """获取用户余额信息"""
        try:
            query = """
                SELECT operators_total_credits as total,
                       operators_used_credits as used,
                       operators_total_credits - operators_used_credits as available
                FROM channel_operators
                WHERE operators_id = %s
            """

            result = execute_query(query, (operator_id,), fetch_one=True, dict_cursor=True)

            if result:
                return {
                    'success': True,
                    'total': result['total'],
                    'used': result['used'],
                    'available': result['available']
                }
            else:
                return {'success': False, 'message': '用户不存在'}

        except Exception as e:
            logger.error(f"获取余额失败: {e}")
            return {'success': False, 'message': str(e)}

    def get_credit_logs(self, operator_id: int, limit: int = 50) -> Dict[str, Any]:
        """获取积分变动日志"""
        try:
            query = """
                SELECT change_type, change_amount, description, created_time
                FROM operator_credit_logs
                WHERE operators_id = %s
                ORDER BY created_time DESC
                LIMIT %s
            """

            logs = execute_query(query, (operator_id, limit), dict_cursor=True)

            return {
                'success': True,
                'logs': [dict(log) for log in logs] if logs else []
            }

        except Exception as e:
            logger.error(f"获取积分日志失败: {e}")
            return {'success': False, 'message': str(e), 'logs': []}

    def refresh_all_balances(self) -> Dict[str, Any]:
        """刷新所有用户余额（定时任务调用）"""
        try:
            # 这里可以实现余额同步逻辑
            # 例如：从外部系统同步余额数据

            logger.info("刷新所有用户余额")
            return {'success': True, 'message': '余额刷新完成'}

        except Exception as e:
            logger.error(f"刷新余额失败: {e}")
            return {'success': False, 'message': str(e)}

    def _get_operator_balance(self, operator_id: int) -> Optional[int]:
        """获取操作员可用余额"""
        try:
            query = """
                SELECT operators_total_credits - operators_used_credits as available
                FROM channel_operators
                WHERE operators_id = %s
            """

            result = execute_query(query, (operator_id,), fetch_one=True)
            return result[0] if result else None

        except Exception as e:
            logger.error(f"获取操作员余额失败: {e}")
            return None

    def _log_credit_change(self, operator_id: int, change_type: str, amount: int,
                          task_id: Optional[int] = None,
                          message_id: Optional[int] = None,
                          operator_id_param: Optional[int] = None,
                          description: str = None):
        """记录积分变动日志"""
        try:
            # 获取变动前余额
            balance = self._get_operator_balance(operator_id)
            if balance is None:
                balance = 0

            # 获取渠道用户ID
            channel_query = """
                SELECT channel_users_id
                FROM channel_operators
                WHERE operators_id = %s
            """
            channel_result = execute_query(channel_query, (operator_id,), fetch_one=True)
            channel_users_id = channel_result[0] if channel_result else None

            # 插入日志
            insert_query = """
                INSERT INTO operator_credit_logs (
                    operators_id, channel_users_id, change_type, change_amount,
                    before_balance, after_balance, related_task_id, related_message_id,
                    operator_type, operator_by, description, created_time
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            params = (
                operator_id,
                channel_users_id,
                change_type,
                amount,
                balance,
                balance + amount,
                task_id,
                message_id,
                'system' if not operator_id_param else 'admin',
                operator_id_param,
                description,
                datetime.now()
            )

            execute_update(insert_query, params)

        except Exception as e:
            logger.error(f"记录积分日志失败: {e}")

    def get_statistics(self, operator_id: int,
                       start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """获取积分统计信息"""
        try:
            # 构建查询条件
            where_conditions = ["operators_id = %s"]
            params = [operator_id]

            if start_date:
                where_conditions.append("created_time >= %s")
                params.append(start_date)

            if end_date:
                where_conditions.append("created_time <= %s")
                params.append(end_date)

            where_clause = " AND ".join(where_conditions)

            # 统计查询
            query = f"""
                SELECT 
                    change_type,
                    COUNT(*) as count,
                    SUM(ABS(change_amount)) as total_amount
                FROM operator_credit_logs
                WHERE {where_clause}
                GROUP BY change_type
            """

            results = execute_query(query, tuple(params), dict_cursor=True)

            # 处理结果
            stats = {
                'total_recharge': 0,
                'total_consume': 0,
                'total_rollback': 0,
                'transaction_count': 0
            }

            for row in results:
                change_type = row['change_type']
                count = row['count']
                amount = row['total_amount']

                if change_type == 'recharge':
                    stats['total_recharge'] = amount
                elif change_type in ['consume', 'pre_deduct']:
                    stats['total_consume'] += amount
                elif change_type == 'rollback':
                    stats['total_rollback'] = amount

                stats['transaction_count'] += count

            # 获取当前余额
            balance_info = self.get_balance(operator_id)
            if balance_info['success']:
                stats.update({
                    'current_total': balance_info['total'],
                    'current_used': balance_info['used'],
                    'current_available': balance_info['available']
                })

            return {'success': True, 'statistics': stats}

        except Exception as e:
            logger.error(f"获取积分统计失败: {e}")
            return {'success': False, 'message': str(e), 'statistics': {}}

    def cleanup_pre_deductions(self):
        """清理预扣除记录（定期维护）"""
        try:
            # 清理超过24小时的预扣除记录
            # 实际项目中应该根据任务状态来清理
            self.pre_deductions.clear()
            logger.info("清理预扣除记录完成")

        except Exception as e:
            logger.error(f"清理预扣除记录失败: {e}")


# 全局积分服务实例
credit_service = CreditService()

# 将积分服务注入到任务执行器
from core.task_executor import task_executor
task_executor.set_credit_service(credit_service)