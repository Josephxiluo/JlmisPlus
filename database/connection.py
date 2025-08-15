"""
数据库连接模块 - 使用环境配置版本
Database connection module with environment configuration
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional, Any, List, Dict, Union
import threading
from pathlib import Path
from dotenv import load_dotenv

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 加载环境变量
env_path = project_root / '.env'
load_dotenv(env_path)

# 尝试导入设置模块，如果失败则直接使用环境变量
try:
    from config.settings import settings

    # 从settings对象获取配置
    DB_CONFIG = {
        'host': settings.DB_HOST,
        'port': settings.DB_PORT,
        'database': settings.DB_NAME,
        'user': settings.DB_USER,
        'password': settings.DB_PASSWORD,
        'options': f"-c client_encoding={settings.DB_CHARSET}",
        'connect_timeout': settings.DB_POOL_TIMEOUT
    }

    CONNECTION_RETRY_COUNT = settings.CONNECTION_RETRY_COUNT
    CONNECTION_RETRY_DELAY = settings.CONNECTION_RETRY_DELAY
    DEBUG = settings.DEBUG
    SQL_DEBUG = settings.SQL_DEBUG

except ImportError:
    # 如果无法导入settings，直接从环境变量读取
    DB_CONFIG = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 5432)),
        'database': os.getenv('DB_NAME', 'sms_pool_db'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'password'),
        'options': f"-c client_encoding={os.getenv('DB_CHARSET', 'utf8')}",
        'connect_timeout': int(os.getenv('DB_POOL_TIMEOUT', 30))
    }

    CONNECTION_RETRY_COUNT = int(os.getenv('CONNECTION_RETRY_COUNT', 3))
    CONNECTION_RETRY_DELAY = float(os.getenv('CONNECTION_RETRY_DELAY', 1.0))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    SQL_DEBUG = os.getenv('SQL_DEBUG', 'False').lower() == 'true'

# 全局连接池
_connection_pool = []
_pool_lock = threading.Lock()

# 日志函数
def log_info(message):
    """记录信息日志"""
    if DEBUG:
        print(f"[INFO] {message}")

def log_error(message, error=None):
    """记录错误日志"""
    if error:
        print(f"[ERROR] {message}: {error}")
    else:
        print(f"[ERROR] {message}")

def log_sql(query, params=None):
    """记录SQL日志"""
    if SQL_DEBUG:
        if params:
            print(f"[SQL] {query[:200]}... | Params: {params}")
        else:
            print(f"[SQL] {query[:200]}...")

def get_connection():
    """获取数据库连接"""
    try:
        # 移除options中的空值
        conn_params = {k: v for k, v in DB_CONFIG.items() if v is not None}

        log_info(f"连接数据库: {conn_params.get('host')}:{conn_params.get('port')}/{conn_params.get('database')}")
        conn = psycopg2.connect(**conn_params)
        return conn
    except Exception as e:
        log_error(f"数据库连接失败", e)
        raise

def execute_query(query: str, params: Union[tuple, dict] = None,
                 fetch_one: bool = False, dict_cursor: bool = False):
    """执行查询语句"""
    conn = None
    cursor = None

    # 重试逻辑
    for attempt in range(CONNECTION_RETRY_COUNT):
        try:
            conn = get_connection()
            if dict_cursor:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
            else:
                cursor = conn.cursor()

            log_sql(query, params)
            cursor.execute(query, params)

            if fetch_one:
                result = cursor.fetchone()
                log_info(f"查询返回单条记录")
            else:
                result = cursor.fetchall()
                log_info(f"查询返回 {len(result)} 条记录")

            return result

        except (psycopg2.OperationalError, psycopg2.DatabaseError) as e:
            log_error(f"查询执行失败 (尝试 {attempt + 1}/{CONNECTION_RETRY_COUNT})", e)
            if attempt < CONNECTION_RETRY_COUNT - 1:
                import time
                time.sleep(CONNECTION_RETRY_DELAY * (attempt + 1))
            else:
                raise
        except Exception as e:
            log_error(f"查询执行异常", e)
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

def execute_update(query: str, params: Union[tuple, dict] = None) -> Optional[int]:
    """
    执行更新语句（INSERT/UPDATE/DELETE）
    对于INSERT语句，返回新插入记录的ID
    """
    conn = None
    cursor = None

    for attempt in range(CONNECTION_RETRY_COUNT):
        try:
            conn = get_connection()
            cursor = conn.cursor()

            log_sql(query, params)
            cursor.execute(query, params)

            # 如果是INSERT语句且包含RETURNING子句，获取返回的ID
            if 'RETURNING' in query.upper():
                result = cursor.fetchone()
                if result:
                    conn.commit()
                    log_info(f"插入成功，返回ID: {result[0]}")
                    return result[0]

            # 对于其他情况，返回影响的行数
            affected_rows = cursor.rowcount
            conn.commit()

            # 对于INSERT语句没有RETURNING的情况，尝试获取lastval
            if query.strip().upper().startswith('INSERT') and affected_rows > 0:
                try:
                    cursor.execute("SELECT lastval()")
                    result = cursor.fetchone()
                    if result:
                        log_info(f"插入成功，返回ID: {result[0]}")
                        return result[0]
                except:
                    pass

            log_info(f"更新成功，影响 {affected_rows} 行")
            return affected_rows

        except psycopg2.IntegrityError as e:
            if conn:
                conn.rollback()
            log_error(f"数据完整性错误", e)
            raise
        except (psycopg2.OperationalError, psycopg2.DatabaseError) as e:
            if conn:
                conn.rollback()
            log_error(f"更新执行失败 (尝试 {attempt + 1}/{CONNECTION_RETRY_COUNT})", e)
            if attempt < CONNECTION_RETRY_COUNT - 1:
                import time
                time.sleep(CONNECTION_RETRY_DELAY * (attempt + 1))
            else:
                raise
        except Exception as e:
            if conn:
                conn.rollback()
            log_error(f"更新执行异常", e)
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

def execute_many(query: str, params_list: List[tuple]) -> int:
    """批量执行语句"""
    conn = None
    cursor = None

    for attempt in range(CONNECTION_RETRY_COUNT):
        try:
            conn = get_connection()
            cursor = conn.cursor()

            log_sql(f"批量执行 {len(params_list)} 条: {query}", None)
            cursor.executemany(query, params_list)
            affected_rows = cursor.rowcount
            conn.commit()

            log_info(f"批量执行成功，影响 {affected_rows} 行")
            return affected_rows

        except (psycopg2.OperationalError, psycopg2.DatabaseError) as e:
            if conn:
                conn.rollback()
            log_error(f"批量执行失败 (尝试 {attempt + 1}/{CONNECTION_RETRY_COUNT})", e)
            if attempt < CONNECTION_RETRY_COUNT - 1:
                import time
                time.sleep(CONNECTION_RETRY_DELAY * (attempt + 1))
            else:
                raise
        except Exception as e:
            if conn:
                conn.rollback()
            log_error(f"批量执行异常", e)
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

def execute_transaction(operations: List[Dict[str, Any]]) -> bool:
    """
    执行事务操作
    operations: 操作列表，每个操作包含 'query' 和 'params'
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # 开始事务
        conn.autocommit = False
        log_info(f"开始事务，包含 {len(operations)} 个操作")

        for i, operation in enumerate(operations):
            query = operation.get('query')
            params = operation.get('params')
            log_sql(f"事务操作 {i+1}: {query}", params)
            cursor.execute(query, params)

        # 提交事务
        conn.commit()
        log_info("事务提交成功")
        return True

    except Exception as e:
        if conn:
            conn.rollback()
        log_error(f"事务执行失败", e)
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def test_connection() -> bool:
    """测试数据库连接"""
    try:
        result = execute_query("SELECT 1", fetch_one=True)
        if result and result[0] == 1:
            log_info("数据库连接测试成功")
            return True
        return False
    except Exception as e:
        log_error("数据库连接测试失败", e)
        return False

def get_db_connection():
    """兼容性函数 - 返回连接对象"""
    return DatabaseConnectionWrapper()


class DatabaseConnectionWrapper:
    """数据库连接包装器 - 提供兼容的接口"""

    def __init__(self):
        self._conn = None
        self._in_transaction = False

    def cursor(self):
        """获取游标 - 兼容原生连接接口"""
        if not self._conn:
            self._conn = get_connection()
        return self._conn.cursor()

    def commit(self):
        """提交事务"""
        if self._conn:
            self._conn.commit()

    def rollback(self):
        """回滚事务"""
        if self._conn:
            self._conn.rollback()

    def close(self):
        """关闭连接"""
        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        if exc_type:
            self.rollback()
        else:
            self.commit()
        self.close()
        return False

    def execute_query(self, query, params=None, fetch_one=False, dict_cursor=False):
        return execute_query(query, params, fetch_one, dict_cursor)

    def execute_update(self, query, params=None):
        return execute_update(query, params)

    def execute_many(self, query, params_list):
        return execute_many(query, params_list)

    def test_connection(self):
        return test_connection()

    def check_table_exists(self, table_name):
        """检查表是否存在"""
        query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = %s
        )
        """
        result = execute_query(query, (table_name,), fetch_one=True)
        return result[0] if result else False

    def is_connected(self):
        """检查是否已连接"""
        return test_connection()

    def get_connection_stats(self):
        """获取连接统计信息"""
        try:
            query = """
            SELECT count(*) as total, 
                   sum(case when state = 'active' then 1 else 0 end) as active,
                   sum(case when state = 'idle' then 1 else 0 end) as idle
            FROM pg_stat_activity 
            WHERE datname = %s
            """
            result = execute_query(query, (DB_CONFIG['database'],), fetch_one=True)
            if result:
                return {
                    'total_connections': result[0],
                    'active_connections': result[1],
                    'idle_connections': result[2]
                }
        except:
            pass
        return {'total_connections': 0, 'active_connections': 0, 'idle_connections': 0}

# 初始化数据库连接
def init_database():
    """初始化数据库"""
    try:
        log_info("=" * 50)
        log_info("开始初始化数据库")
        log_info(f"数据库配置: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
        log_info(f"用户: {DB_CONFIG['user']}")
        log_info("=" * 50)

        # 测试连接
        if not test_connection():
            log_error("数据库连接失败")
            return False

        # 检查必要的表
        db = DatabaseConnectionWrapper()
        required_tables = ['tasks', 'task_message_details', 'channel_operators', 'message_templates']

        missing_tables = []
        for table in required_tables:
            if not db.check_table_exists(table):
                missing_tables.append(table)
                log_error(f"缺少必要的表: {table}")

        if missing_tables:
            log_error(f"缺少以下必要的表: {', '.join(missing_tables)}")
            log_error("请先执行数据库初始化脚本创建表结构")
            return False

        # 获取连接统计
        stats = db.get_connection_stats()
        log_info(f"连接统计: 总连接数={stats['total_connections']}, "
                f"活动连接={stats['active_connections']}, "
                f"空闲连接={stats['idle_connections']}")

        log_info("数据库初始化成功")
        return True

    except Exception as e:
        log_error(f"数据库初始化失败", e)
        return False


def close_database():
    """关闭数据库连接（兼容性函数）"""
    global _connection_pool
    try:
        with _pool_lock:
            # 关闭连接池中的所有连接
            for conn in _connection_pool:
                try:
                    if conn and not conn.closed:
                        conn.close()
                except Exception as e:
                    log_error(f"关闭连接失败", e)

            # 清空连接池
            _connection_pool.clear()

        log_info("数据库连接池已关闭")
        return True
    except Exception as e:
        log_error(f"关闭数据库失败", e)
        return False

# 如果直接运行此模块，测试连接
if __name__ == "__main__":
    print("数据库连接模块测试")
    print("=" * 50)

    # 显示配置信息
    print(f"环境配置文件: {env_path}")
    print(f"数据库主机: {DB_CONFIG['host']}")
    print(f"数据库端口: {DB_CONFIG['port']}")
    print(f"数据库名称: {DB_CONFIG['database']}")
    print(f"数据库用户: {DB_CONFIG['user']}")
    print(f"重试次数: {CONNECTION_RETRY_COUNT}")
    print(f"重试延迟: {CONNECTION_RETRY_DELAY}秒")
    print(f"调试模式: {DEBUG}")
    print(f"SQL调试: {SQL_DEBUG}")
    print("=" * 50)

    # 初始化数据库
    if init_database():
        print("\n✅ 数据库初始化成功")

        # 测试查询
        print("\n测试查询任务表...")
        try:
            result = execute_query("SELECT COUNT(*) FROM tasks", fetch_one=True)
            print(f"任务表中有 {result[0]} 条记录")
        except Exception as e:
            print(f"查询失败: {e}")
    else:
        print("\n❌ 数据库初始化失败")