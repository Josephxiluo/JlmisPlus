"""
猫池短信系统积分管理服务 - tkinter版
Credit management service for SMS Pool System - tkinter version
"""

import sys
import threading
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Callable
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from models.user import ChannelOperator
    from config.settings import settings
    from config.logging_config import get_logger, log_credit_action, log_error, log_info, log_timer_action
except ImportError:
    # 简化处理
    class MockChannelOperator:
        def __init__(self):
            self.available_credits = 1000
            self.used_credits = 0
            self.total_credits = 1000

        def refresh_credits_from_db(self):
            return True

        def consume_credits(self, amount, description=None):
            if self.available_credits >= amount:
                self.available_credits -= amount
                self.used_credits += amount
                return True
            return False

        def has_sufficient_credits(self, amount):
            return self.available_credits >= amount

    ChannelOperator = MockChannelOperator

    class MockSettings:
        CREDIT_REFRESH_INTERVAL = 300
        SMS_RATE = 1.0
        MMS_RATE = 3.0

    settings = MockSettings()

    import logging
    def get_logger(name='services.credit'):
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    def log_credit_action(user_id, action, amount, balance, details=None):
        logger = get_logger()
        message = f"[积分操作] 用户ID={user_id} {action} 金额={amount} 余额={balance}"
        if details:
            message += f" - {details}"
        logger.info(message)

    def log_error(message, error=None):
        logger = get_logger()
        logger.error(f"{message}: {error}" if error else message)

    def log_info(message):
        logger = get_logger()
        logger.info(message)

    def log_timer_action(timer_name, action, interval=None):
        logger = get_logger()
        message = f"[定时器] {timer_name} {action}"
        if interval:
            message += f" 间隔={interval}秒"
        logger.debug(message)

logger = get_logger('services.credit')


class CreditService:
    """积分管理服务类"""

    def __init__(self):
        """初始化积分服务"""
        self.current_user: Optional[ChannelOperator] = None
        self._lock = threading.Lock()
        self._refresh_timer: Optional[threading.Timer] = None
        self._credit_change_callbacks: list = []
        self._last_refresh_time: Optional[datetime] = None
        self.is_initialized = False

        # 积分费率配置
        self.sms_rate = getattr(settings, 'SMS_RATE', 1.0)
        self.mms_rate = getattr(settings, 'MMS_RATE', 3.0)

        # 刷新间隔（秒）
        self.refresh_interval = getattr(settings, 'CREDIT_REFRESH_INTERVAL', 300)  # 5分钟

    def initialize(self) -> bool:
        """初始化服务"""
        try:
            log_info("积分服务初始化开始")

            # 启动定时刷新
            self._start_auto_refresh()

            self.is_initialized = True
            log_info(f"积分服务初始化完成，刷新间隔: {self.refresh_interval}秒")
            return True

        except Exception as e:
            log_error("积分服务初始化失败", error=e)
            return False

    def shutdown(self):
        """关闭服务"""
        try:
            log_info("积分服务开始关闭")

            # 停止定时刷新
            self._stop_auto_refresh()

            # 清除回调
            self._credit_change_callbacks.clear()

            self.current_user = None
            self.is_initialized = False
            log_info("积分服务关闭完成")

        except Exception as e:
            log_error("积分服务关闭失败", error=e)

    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        return {
            'running': self.is_initialized,
            'current_user': self.current_user.id if self.current_user else None,
            'last_refresh': self._last_refresh_time.isoformat() if self._last_refresh_time else None,
            'refresh_interval': self.refresh_interval,
            'auto_refresh_active': self._refresh_timer is not None,
            'sms_rate': self.sms_rate,
            'mms_rate': self.mms_rate,
            'message': '积分服务正常运行' if self.is_initialized else '积分服务未初始化'
        }

    def set_current_user(self, user: ChannelOperator) -> bool:
        """设置当前用户"""
        try:
            with self._lock:
                old_user_id = self.current_user.id if self.current_user else None
                self.current_user = user

                # 立即刷新一次积分
                if user:
                    self.refresh_credits()

                log_info(f"积分服务用户切换: {old_user_id} -> {user.id if user else None}")
                return True

        except Exception as e:
            log_error("设置当前用户失败", error=e)
            return False

    def get_current_credits(self) -> Dict[str, Any]:
        """获取当前用户积分信息"""
        try:
            if not self.current_user:
                return {
                    'available': 0,
                    'used': 0,
                    'total': 0,
                    'usage_rate': 0.0,
                    'can_send_sms': False,
                    'can_send_mms': False,
                    'last_update': None
                }

            return {
                **self.current_user.get_credit_summary(),
                'last_update': self._last_refresh_time.isoformat() if self._last_refresh_time else None
            }

        except Exception as e:
            log_error("获取积分信息失败", error=e)
            return {
                'available': 0,
                'used': 0,
                'total': 0,
                'usage_rate': 0.0,
                'can_send_sms': False,
                'can_send_mms': False,
                'last_update': None,
                'error': str(e)
            }

    def refresh_credits(self) -> bool:
        """刷新积分信息"""
        try:
            if not self.current_user:
                log_error("刷新积分失败：当前用户为空")
                return False

            with self._lock:
                old_credits = self.current_user.available_credits

                # 从数据库刷新积分信息
                if self.current_user.refresh_credits_from_db():
                    self._last_refresh_time = datetime.now()

                    # 如果积分有变化，触发回调
                    if old_credits != self.current_user.available_credits:
                        self._notify_credit_change(old_credits, self.current_user.available_credits)

                    log_info(f"积分刷新成功，余额: {self.current_user.available_credits}")
                    return True
                else:
                    log_error("从数据库刷新积分失败")
                    return False

        except Exception as e:
            log_error("刷新积分异常", error=e)
            return False

    def consume_credits(self, amount: int, message_type: str = 'sms', description: str = None) -> Dict[str, Any]:
        """消费积分"""
        try:
            if not self.current_user:
                return {
                    'success': False,
                    'message': '当前用户为空',
                    'error_code': 'NO_USER'
                }

            # 计算实际消费金额
            if message_type == 'mms':
                actual_amount = int(amount * self.mms_rate)
            else:
                actual_amount = int(amount * self.sms_rate)

            # 检查余额
            if not self.current_user.has_sufficient_credits(actual_amount):
                return {
                    'success': False,
                    'message': f'积分余额不足，需要{actual_amount}积分，当前余额{self.current_user.available_credits}积分',
                    'error_code': 'INSUFFICIENT_CREDITS',
                    'required': actual_amount,
                    'available': self.current_user.available_credits
                }

            with self._lock:
                old_credits = self.current_user.available_credits

                # 消费积分
                if self.current_user.consume_credits(actual_amount, description):
                    # 触发积分变化回调
                    self._notify_credit_change(old_credits, self.current_user.available_credits)

                    log_credit_action(
                        user_id=self.current_user.id,
                        action="消费积分",
                        amount=-actual_amount,
                        balance=self.current_user.available_credits,
                        details=f"{message_type.upper()}: {description}"
                    )

                    return {
                        'success': True,
                        'message': f'成功消费{actual_amount}积分',
                        'consumed': actual_amount,
                        'remaining': self.current_user.available_credits
                    }
                else:
                    return {
                        'success': False,
                        'message': '积分消费失败',
                        'error_code': 'CONSUME_FAILED'
                    }

        except Exception as e:
            log_error("消费积分异常", error=e)
            return {
                'success': False,
                'message': f'消费积分异常: {str(e)}',
                'error_code': 'SYSTEM_ERROR'
            }

    def check_sufficient_credits(self, amount: int, message_type: str = 'sms') -> Dict[str, Any]:
        """检查积分是否充足"""
        try:
            if not self.current_user:
                return {
                    'sufficient': False,
                    'message': '当前用户为空',
                    'required': 0,
                    'available': 0
                }

            # 计算需要的积分
            if message_type == 'mms':
                required_credits = int(amount * self.mms_rate)
            else:
                required_credits = int(amount * self.sms_rate)

            available_credits = self.current_user.available_credits
            sufficient = available_credits >= required_credits

            return {
                'sufficient': sufficient,
                'required': required_credits,
                'available': available_credits,
                'shortage': max(0, required_credits - available_credits),
                'message': '积分充足' if sufficient else f'积分不足，还需要{required_credits - available_credits}积分'
            }

        except Exception as e:
            log_error("检查积分充足性异常", error=e)
            return {
                'sufficient': False,
                'required': 0,
                'available': 0,
                'shortage': 0,
                'message': f'检查失败: {str(e)}'
            }

    def calculate_sending_cost(self, sms_count: int = 0, mms_count: int = 0) -> Dict[str, Any]:
        """计算发送成本"""
        try:
            sms_cost = int(sms_count * self.sms_rate)
            mms_cost = int(mms_count * self.mms_rate)
            total_cost = sms_cost + mms_cost

            current_credits = self.current_user.available_credits if self.current_user else 0

            return {
                'sms_count': sms_count,
                'mms_count': mms_count,
                'sms_cost': sms_cost,
                'mms_cost': mms_cost,
                'total_cost': total_cost,
                'current_credits': current_credits,
                'sufficient': current_credits >= total_cost,
                'shortage': max(0, total_cost - current_credits)
            }

        except Exception as e:
            log_error("计算发送成本异常", error=e)
            return {
                'sms_count': sms_count,
                'mms_count': mms_count,
                'sms_cost': 0,
                'mms_cost': 0,
                'total_cost': 0,
                'current_credits': 0,
                'sufficient': False,
                'shortage': 0,
                'error': str(e)
            }

    def get_credit_usage_stats(self, days: int = 30) -> Dict[str, Any]:
        """获取积分使用统计"""
        try:
            if not self.current_user:
                return {
                    'total_used': 0,
                    'daily_average': 0,
                    'usage_trend': [],
                    'message': '当前用户为空'
                }

            # 这里可以从数据库获取详细的使用统计
            # 暂时返回基础信息
            total_used = self.current_user.used_credits
            daily_average = total_used / max(days, 1)

            return {
                'total_used': total_used,
                'total_available': self.current_user.available_credits,
                'total_credits': self.current_user.total_credits,
                'daily_average': round(daily_average, 2),
                'usage_rate': round(total_used / self.current_user.total_credits * 100, 2) if self.current_user.total_credits > 0 else 0,
                'days_remaining': round(self.current_user.available_credits / max(daily_average, 1), 1) if daily_average > 0 else float('inf'),
                'last_refresh': self._last_refresh_time.isoformat() if self._last_refresh_time else None
            }

        except Exception as e:
            log_error("获取积分使用统计异常", error=e)
            return {
                'total_used': 0,
                'daily_average': 0,
                'usage_trend': [],
                'error': str(e)
            }

    def add_credit_change_callback(self, callback: Callable[[int, int], None]):
        """添加积分变化回调函数"""
        try:
            if callable(callback):
                self._credit_change_callbacks.append(callback)
                log_info(f"添加积分变化回调函数，当前回调数量: {len(self._credit_change_callbacks)}")
        except Exception as e:
            log_error("添加积分变化回调失败", error=e)

    def remove_credit_change_callback(self, callback: Callable[[int, int], None]):
        """移除积分变化回调函数"""
        try:
            if callback in self._credit_change_callbacks:
                self._credit_change_callbacks.remove(callback)
                log_info(f"移除积分变化回调函数，当前回调数量: {len(self._credit_change_callbacks)}")
        except Exception as e:
            log_error("移除积分变化回调失败", error=e)

    def set_refresh_interval(self, interval_seconds: int):
        """设置刷新间隔"""
        try:
            if interval_seconds < 30:  # 最小30秒
                interval_seconds = 30
            elif interval_seconds > 3600:  # 最大1小时
                interval_seconds = 3600

            old_interval = self.refresh_interval
            self.refresh_interval = interval_seconds

            # 重启定时器
            if self.is_initialized:
                self._stop_auto_refresh()
                self._start_auto_refresh()

            log_info(f"积分刷新间隔已更新: {old_interval}秒 -> {interval_seconds}秒")

        except Exception as e:
            log_error("设置刷新间隔失败", error=e)

    def force_refresh(self) -> Dict[str, Any]:
        """强制刷新积分"""
        try:
            log_info("执行强制积分刷新")

            if self.refresh_credits():
                return {
                    'success': True,
                    'message': '积分刷新成功',
                    'credits': self.get_current_credits(),
                    'refresh_time': self._last_refresh_time.isoformat() if self._last_refresh_time else None
                }
            else:
                return {
                    'success': False,
                    'message': '积分刷新失败',
                    'error_code': 'REFRESH_FAILED'
                }

        except Exception as e:
            log_error("强制刷新积分异常", error=e)
            return {
                'success': False,
                'message': f'刷新异常: {str(e)}',
                'error_code': 'SYSTEM_ERROR'
            }

    def _start_auto_refresh(self):
        """启动自动刷新"""
        try:
            if self._refresh_timer:
                self._refresh_timer.cancel()

            self._refresh_timer = threading.Timer(self.refresh_interval, self._auto_refresh_callback)
            self._refresh_timer.daemon = True
            self._refresh_timer.start()

            log_timer_action("积分自动刷新", "启动", self.refresh_interval)

        except Exception as e:
            log_error("启动自动刷新失败", error=e)

    def _stop_auto_refresh(self):
        """停止自动刷新"""
        try:
            if self._refresh_timer:
                self._refresh_timer.cancel()
                self._refresh_timer = None
                log_timer_action("积分自动刷新", "停止")

        except Exception as e:
            log_error("停止自动刷新失败", error=e)

    def _auto_refresh_callback(self):
        """自动刷新回调"""
        try:
            if self.current_user and self.is_initialized:
                self.refresh_credits()

            # 重新启动定时器
            if self.is_initialized:
                self._start_auto_refresh()

        except Exception as e:
            log_error("自动刷新回调异常", error=e)
            # 即使出错也要重新启动定时器
            if self.is_initialized:
                self._start_auto_refresh()

    def _notify_credit_change(self, old_credits: int, new_credits: int):
        """通知积分变化"""
        try:
            for callback in self._credit_change_callbacks:
                try:
                    callback(old_credits, new_credits)
                except Exception as e:
                    log_error("积分变化回调执行失败", error=e)

        except Exception as e:
            log_error("通知积分变化失败", error=e)

    def get_low_credit_warning(self, threshold: int = 100) -> Optional[Dict[str, Any]]:
        """获取低积分警告"""
        try:
            if not self.current_user:
                return None

            available_credits = self.current_user.available_credits

            if available_credits <= threshold:
                # 计算还能发送多少条消息
                sms_remaining = int(available_credits / self.sms_rate)
                mms_remaining = int(available_credits / self.mms_rate)

                return {
                    'warning': True,
                    'available_credits': available_credits,
                    'threshold': threshold,
                    'sms_remaining': sms_remaining,
                    'mms_remaining': mms_remaining,
                    'message': f'积分余额不足！当前余额: {available_credits}积分，还可发送{sms_remaining}条短信或{mms_remaining}条彩信',
                    'severity': 'critical' if available_credits <= threshold // 2 else 'warning'
                }

            return None

        except Exception as e:
            log_error("获取低积分警告异常", error=e)
            return None


# 全局积分服务实例
credit_service = CreditService()