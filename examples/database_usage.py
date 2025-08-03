"""
数据库使用示例
展示如何在项目中使用数据库功能
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.database import get_db_manager
from datetime import datetime, timedelta


def example_user_management():
    """用户管理示例"""
    print("=== 用户管理示例 ===")

    db = get_db_manager()

    try:
        # 1. 创建用户
        print("1. 创建用户...")
        user_id = db.create_user(
            username='demo_user',
            email='demo@example.com',
            password='demo123',
            real_name='演示用户',
            role='user'
        )
        print(f"   创建用户ID: {user_id}")

        # 2. 用户认证
        print("2. 用户认证...")
        user = db.authenticate_user('demo_user', 'demo123', '192.168.1.100')
        if user:
            print(f"   认证成功: {user.username} (ID: {user.id})")

        # 3. 创建会话
        print("3. 创建用户会话...")
        session_token = 'demo_session_token_123456'
        session_id = db.create_user_session(
            user_id=user.id,
            session_token=session_token,
            ip_address='192.168.1.100',
            user_agent='SMS Manager Client'
        )
        print(f"   会话ID: {session_id}")

        # 4. 通过会话获取用户
        print("4. 通过会话获取用户...")
        session_user = db.get_user_by_session(session_token)
        if session_user:
            print(f"   会话用户: {session_user.username}")

        # 5. 注销会话
        print("5. 注销会话...")
        if db.invalidate_session(session_token):
            print("   会话注销成功")

    except Exception as e:
        print(f"用户管理示例错误: {e}")


def example_task_management():
    """任务管理示例"""
    print("\n=== 任务管理示例 ===")

    db = get_db_manager()

    try:
        # 获取或创建测试用户
        user = db.authenticate_user('demo_user', 'demo123')
        if not user:
            print("请先运行用户管理示例")
            return

        # 1. 创建任务
        print("1. 创建短信任务...")
        phone_numbers = ['13800138000', '13800138001', '13800138002']
        task_id = db.create_task(
            name='营销短信任务',
            phone_numbers=phone_numbers,
            message_content='亲爱的客户，我们有新产品上线，欢迎了解！',
            created_by=user.id,
            subject='产品推广',
            description='新产品营销推广短信',
            priority=7,
            schedule_type='immediate',
            send_config={
                'interval': 1000,
                'retry_count': 3,
                'timeout': 10
            }
        )
        print(f"   任务ID: {task_id}")

        # 2. 获取用户任务
        print("2. 获取用户任务列表...")
        user_tasks = db.get_user_tasks(user.id, limit=10)
        for task in user_tasks:
            print(f"   任务: {task.name} - 状态: {task.status} - 进度: {task.progress_percentage:.1f}%")

        # 3. 更新任务状态
        print("3. 启动任务...")
        if db.update_task_status(task_id, 'running', user_id=user.id):
            print("   任务启动成功")

        # 4. 添加发送记录
        print("4. 添加发送记录...")
        for i, phone in enumerate(phone_numbers):
            status = 'success' if i < 2 else 'failed'
            error_msg = None if status == 'success' else '号码无效'

            record_id = db.add_send_record(
                task_id=task_id,
                phone_number=phone,
                message_content='亲爱的客户，我们有新产品上线，欢迎了解！',
                port_name=f'COM{i + 1}',
                status=status,
                error_message=error_msg,
                response_time=150.5 + i * 10,
                operator='中国移动',
                signal_strength=85 - i * 5
            )
            print(f"   发送记录ID: {record_id} - {phone} - {status}")

        # 5. 获取发送记录
        print("5. 获取发送记录...")
        send_records = db.get_send_records(task_id=task_id)
        for record in send_records:
            print(f"   记录: {record.phone_number} - {record.status} - {record.response_time}ms")

        # 6. 完成任务
        print("6. 完成任务...")
        if db.update_task_status(task_id, 'completed', user_id=user.id):
            print("   任务完成")

    except Exception as e:
        print(f"任务管理示例错误: {e}")


def example_port_management():
    """端口管理示例"""
    print("\n=== 端口管理示例 ===")

    db = get_db_manager()

    try:
        # 1. 添加端口
        print("1. 添加端口设备...")
        ports_data = [
            {
                'name': 'COM1',
                'display_name': '移动端口1',
                'operator': '中国移动',
                'device_model': 'Huawei ME909s',
                'sim_number': '13800138000',
                'status': 'active',
                'daily_limit': 1000
            },
            {
                'name': 'COM2',
                'display_name': '联通端口1',
                'operator': '中国联通',
                'device_model': 'ZTE MF286',
                'sim_number': '13600136000',
                'status': 'active',
                'daily_limit': 800
            }
        ]

        for port_data in ports_data:
            port_id = db.add_or_update_port(**port_data)
            print(f"   端口: {port_data['name']} - ID: {port_id}")

        # 2. 获取可用端口
        print("2. 获取可用端口...")
        available_ports = db.get_available_ports()
        for port in available_ports:
            print(f"   可用端口: {port.name} - {port.operator} - 成功率: {port.success_rate:.1f}%")

        # 3. 更新端口统计
        print("3. 更新端口统计...")
        for port in available_ports:
            success_count = port.success_sent + 10
            total_count = port.total_sent + 12
            failed_count = total_count - success_count

            db.update_port_stats(
                port.name,
                total_sent=total_count,
                success_sent=success_count,
                failed_sent=failed_count
            )
            print(f"   更新端口: {port.name} - 总计: {total_count}")

    except Exception as e:
        print(f"端口管理示例错误: {e}")


def example_statistics():
    """统计分析示例"""
    print("\n=== 统计分析示例 ===")

    db = get_db_manager()

    try:
        # 获取测试用户
        user = db.authenticate_user('demo_user', 'demo123')
        if not user:
            print("请先运行用户管理示例")
            return

        # 1. 用户统计
        print("1. 获取用户统计...")
        user_stats = db.get_user_statistics(user.id)
        print(f"   用户任务统计:")
        print(f"     总任务数: {user_stats.get('total_tasks', 0)}")
        print(f"     完成任务: {user_stats.get('completed_tasks', 0)}")
        print(f"     运行任务: {user_stats.get('running_tasks', 0)}")
        print(f"     总发送数: {user_stats.get('total_sent', 0)}")
        print(f"     成功发送: {user_stats.get('success_sent', 0)}")
        print(f"     成功率: {user_stats.get('success_rate', 0):.1f}%")

        # 2. 系统统计
        print("2. 获取系统统计...")
        system_stats = db.get_system_statistics()
        print(f"   系统整体统计:")
        print(f"     总用户数: {system_stats.get('total_users', 0)}")
        print(f"     活跃用户: {system_stats.get('active_users', 0)}")
        print(f"     总任务数: {system_stats.get('total_tasks', 0)}")
        print(f"     总端口数: {system_stats.get('total_ports', 0)}")
        print(f"     活跃端口: {system_stats.get('active_ports', 0)}")
        print(f"     总发送数: {system_stats.get('total_sent', 0)}")
        print(f"     系统成功率: {system_stats.get('success_rate', 0):.1f}%")

    except Exception as e:
        print(f"统计分析示例错误: {e}")


def example_logging():
    """日志记录示例"""
    print("\n=== 日志记录示例 ===")

    db = get_db_manager()

    try:
        # 获取测试用户
        user = db.authenticate_user('demo_user', 'demo123')
        user_id = user.id if user else None

        # 1. 记录不同级别的日志
        print("1. 记录日志...")
        log_entries = [
            ('INFO', '用户登录', 'auth', 'login', user_id),
            ('WARNING', '发送频率过高', 'message_sender', 'send_message', user_id),
            ('ERROR', '端口连接失败', 'port_manager', 'connect_port', user_id),
            ('DEBUG', '任务状态检查', 'task_manager', 'check_status', user_id)
        ]

        for level, message, module, function, uid in log_entries:
            db.add_log(
                level=level,
                message=message,
                module=module,
                function=function,
                user_id=uid,
                ip_address='192.168.1.100'
            )
            print(f"   记录日志: {level} - {message}")

        # 2. 查询日志
        print("2. 查询日志记录...")
        recent_logs = db.get_logs(limit=10)
        for log in recent_logs:
            print(f"   日志: [{log.level}] {log.message} - {log.module}")

        # 3. 按条件查询日志
        print("3. 查询错误日志...")
        error_logs = db.get_logs(level='ERROR', limit=5)
        for log in error_logs:
            print(f"   错误: {log.message} - {log.created_time}")

    except Exception as e:
        print(f"日志记录示例错误: {e}")


def example_maintenance():
    """数据维护示例"""
    print("\n=== 数据维护示例 ===")

    db = get_db_manager()

    try:
        # 1. 清理旧数据
        print("1. 清理旧数据...")
        cleanup_result = db.cleanup_old_data(days=30)
        if cleanup_result:
            print(f"   清理结果:")
            print(f"     发送记录: {cleanup_result['send_records']} 条")
            print(f"     会话记录: {cleanup_result['sessions']} 条")
            print(f"     日志记录: {cleanup_result['logs']} 条")

        # 2. 数据库备份（示例）
        print("2. 数据库备份...")
        backup_file = db.backup_database()
        if backup_file:
            print(f"   备份文件: {backup_file}")

    except Exception as e:
        print(f"数据维护示例错误: {e}")


def main():
    """主函数 - 运行所有示例"""
    print("猫池短信管理系统 - 数据库使用示例")
    print("=" * 50)

    try:
        # 按顺序运行示例
        example_user_management()
        example_task_management()
        example_port_management()
        example_statistics()
        example_logging()
        example_maintenance()

        print("\n✅ 所有示例运行完成！")

    except Exception as e:
        print(f"\n❌ 示例运行出错: {e}")

    finally:
        # 清理测试数据
        print("\n清理测试数据...")
        try:
            from core.database import close_db
            close_db()
            print("数据库连接已关闭")
        except:
            pass


if __name__ == "__main__":
    main()