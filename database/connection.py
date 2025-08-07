"""
猫池短信系统数据库连接管理 - tkinter版 (修复版)
Database connection management for SMS Pool System - tkinter version (Fixed)
"""

import os
import sys
import time
import threading
import psycopg2
import psycopg2.extras
from psycopg2 import pool, OperationalError, DatabaseError, IntegrityError
from typing import Optional, Dict, Any, List, Tuple, Union
from contextlib import contextmanager
from functools import wraps
from pathlib import Path
import atexit

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from config.settings import settings
    from config.logging_config import get_logger, log_database_action, log_error, log_info
except ImportError:
    # 如果无法导入配置，使用默认值和简单日志
    class MockSettings:
        DB_HOST = 'localhost'
        DB_PORT = 5432
        DB_NAME = 'sms_pool_db'
        DB_USER = 'postgres'
        DB_PASSWORD = 'password'
        DB_CHARSET = 'utf8'
        DB_POOL_SIZE = 5
        DB_POOL_TIMEOUT = 30
        CONNECTION_RETRY_COUNT = 3
        DEBUG = True
        SQL_DEBUG = False

    settings = MockSettings()

    # 简单的日志函数
    def get_logger(name='database'):
        import logging
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    def log_database_action(action, table=None, details=None, success=True):
        try:
            logger = get_logger()
            if success:
                logger.info(f"数据库操作: {action} {table or ''} {details or ''}")
            else:
                logger.error(f"数据库操作失败: {action} {table or ''} {details or ''}")
        except:
            # 忽略日志错误，避免程序退出时的异常
            pass

    def log_error(message, error=None):
        try:
            logger = get_logger()
            logger.error(f"{message}: {error}" if error else message)
        except:
            pass

    def log_info(message):
        try:
            logger = get_logger()
            logger.info(message)
        except:
            pass

logger = get_logger('database.connection')


def safe_log_info(message):
    """安全的日志记录函数，避免程序退出时的错误"""
    try:
        log_info(message)
    except (ValueError, OSError):
        # 忽略文件已关闭或I/O错误
        pass


def safe_log_error(message, error=None):
    """安全的错误日志记录函数"""
    try:
        log_error(message, error)
    except (ValueError, OSError):
        pass


def safe_log_database_action(action, table=None, details=None, success=True):
    """安全的数据库操作日志记录函数"""
    try:
        log_database_action(action, table, details, success)
    except (ValueError, OSError):
        pass


def retry_on_failure(max_retries: int = None, delay: float = 1.0):
    """数据库操作重试装饰器"""
    if max_retries is None:
        max_retries = getattr(settings, 'CONNECTION_RETRY_COUNT', 3)

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except (OperationalError, DatabaseError) as e:
                    last_exception = e
                    if attempt < max_retries:
                        safe_log_error(f"数据库操作失败，第{attempt + 1}次重试", error=e)
                        time.sleep(delay * (attempt + 1))
                    else:
                        safe_log_error(f"数据库操作失败，已达最大重试次数", error=e)
                        raise last_exception
                except Exception as e:
                    safe_log_error(f"数据库操作异常", error=e)
                    raise e
            raise last_exception
        return wrapper
    return decorator


class DatabaseConnection:
    """数据库连接管理类"""

    _instance = None
    _lock = threading.Lock()
    _cleanup_registered = False

    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DatabaseConnection, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化数据库连接"""
        if hasattr(self, '_initialized'):
            return

        self._initialized = True
        self._connection_pool: Optional[psycopg2.pool.ThreadedConnectionPool] = None
        self._pool_lock = threading.Lock()
        self._is_connected = False
        self._cleanup_done = False

        # 数据库连接信息
        self._connection_info = {
            'host': settings.DB_HOST,
            'port': settings.DB_PORT,
            'database': settings.DB_NAME,
            'user': settings.DB_USER,
            'password': settings.DB_PASSWORD,
            'options': f"-c client_encoding={settings.DB_CHARSET}",
            'connect_timeout': settings.DB_POOL_TIMEOUT
        }

        # 注册程序退出时的清理函数
        if not DatabaseConnection._cleanup_registered:
            atexit.register(self._cleanup_on_exit)
            DatabaseConnection._cleanup_registered = True

        # 尝试初始化连接池
        self._init_connection_pool()

    def _cleanup_on_exit(self):
        """程序退出时的清理函数"""
        if not self._cleanup_done:
            self._cleanup_done = True
            try:
                if self._connection_pool and not self._connection_pool.closed:
                    self._connection_pool.closeall()
                    # 使用print而不是logger，避免日志系统已关闭的问题
                    print("数据库连接池已安全关闭")
            except Exception:
                # 忽略清理过程中的任何错误
                pass

    def _init_connection_pool(self):
        """初始化连接池"""
        try:
            with self._pool_lock:
                if self._connection_pool is None:
                    safe_log_info("正在初始化数据库连接池...")

                    self._connection_pool = psycopg2.pool.ThreadedConnectionPool(
                        minconn=1,
                        maxconn=settings.DB_POOL_SIZE,
                        **self._connection_info
                    )

                    # 测试连接
                    test_conn = self._connection_pool.getconn()
                    test_conn.close()
                    self._connection_pool.putconn(test_conn)

                    self._is_connected = True
                    safe_log_info(f"数据库连接池初始化成功: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
                    safe_log_database_action("连接池初始化", details=f"池大小={settings.DB_POOL_SIZE}")

        except Exception as e:
            self._is_connected = False
            safe_log_error("数据库连接池初始化失败", error=e)
            self._connection_pool = None
            # 不抛出异常，允许应用继续运行

    @contextmanager
    def get_connection(self):
        """获取数据库连接（上下文管理器）"""
        if self._connection_pool is None:
            self._init_connection_pool()
            if self._connection_pool is None:
                raise Exception("数据库连接池初始化失败")

        connection = None
        try:
            connection = self._connection_pool.getconn()
            if connection is None:
                raise Exception("无法从连接池获取连接")

            # 检查连接状态
            if connection.closed:
                safe_log_error("连接已关闭，重新获取连接")
                self._connection_pool.putconn(connection, close=True)
                connection = self._connection_pool.getconn()

            yield connection

        except Exception as e:
            if connection and not connection.closed:
                connection.rollback()
            safe_log_error("数据库连接错误", error=e)
            raise
        finally:
            if connection:
                try:
                    self._connection_pool.putconn(connection)
                except Exception as e:
                    safe_log_error("归还连接失败", error=e)

    @contextmanager
    def get_cursor(self, commit: bool = True, dict_cursor: bool = False):
        """获取数据库游标（上下文管理器）"""
        with self.get_connection() as connection:
            cursor = None
            try:
                if dict_cursor:
                    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                else:
                    cursor = connection.cursor()

                yield cursor

                if commit:
                    connection.commit()

            except Exception as e:
                connection.rollback()
                safe_log_error("数据库操作错误", error=e)
                raise
            finally:
                if cursor:
                    cursor.close()

    @retry_on_failure()
    def execute_query(self, query: str, params: Union[tuple, dict] = None,
                     fetch_one: bool = False, dict_cursor: bool = False) -> Union[List[tuple], tuple, None]:
        """执行查询语句"""
        try:
            start_time = time.time()

            with self.get_cursor(commit=False, dict_cursor=dict_cursor) as cursor:
                cursor.execute(query, params)

                if fetch_one:
                    result = cursor.fetchone()
                    safe_log_database_action("查询", details=f"返回单条记录, 耗时={time.time()-start_time:.3f}s")
                    if settings.SQL_DEBUG:
                        safe_log_info(f"SQL: {query[:100]}...")
                    return result
                else:
                    result = cursor.fetchall()
                    safe_log_database_action("查询", details=f"返回{len(result)}条记录, 耗时={time.time()-start_time:.3f}s")
                    if settings.SQL_DEBUG:
                        safe_log_info(f"SQL: {query[:100]}...")
                    return result

        except Exception as e:
            safe_log_database_action("查询", details=f"SQL: {query[:100]}...", success=False)
            safe_log_error("查询执行失败", error=e)
            raise

    @retry_on_failure()
    def execute_update(self, query: str, params: Union[tuple, dict] = None) -> int:
        """执行更新语句"""
        try:
            start_time = time.time()

            with self.get_cursor(commit=True) as cursor:
                cursor.execute(query, params)
                rowcount = cursor.rowcount

                safe_log_database_action("更新", details=f"影响{rowcount}行, 耗时={time.time()-start_time:.3f}s")
                if settings.SQL_DEBUG:
                    safe_log_info(f"SQL: {query[:100]}...")
                return rowcount

        except IntegrityError as e:
            safe_log_database_action("更新", details=f"完整性约束错误: {e}", success=False)
            raise
        except Exception as e:
            safe_log_database_action("更新", details=f"SQL: {query[:100]}...", success=False)
            safe_log_error("更新执行失败", error=e)
            raise

    @retry_on_failure()
    def execute_many(self, query: str, params_list: List[Union[tuple, dict]]) -> int:
        """批量执行语句"""
        try:
            start_time = time.time()

            with self.get_cursor(commit=True) as cursor:
                cursor.executemany(query, params_list)
                rowcount = cursor.rowcount

                safe_log_database_action("批量更新", details=f"批次={len(params_list)}, 影响{rowcount}行, 耗时={time.time()-start_time:.3f}s")
                if settings.SQL_DEBUG:
                    safe_log_info(f"SQL: {query[:100]}...")
                return rowcount

        except Exception as e:
            safe_log_database_action("批量更新", details=f"批次={len(params_list)}", success=False)
            safe_log_error("批量执行失败", error=e)
            raise

    @retry_on_failure()
    def call_function(self, function_name: str, params: tuple = None) -> Any:
        """调用存储过程/函数"""
        try:
            start_time = time.time()

            with self.get_cursor(commit=True) as cursor:
                cursor.callproc(function_name, params or ())
                try:
                    result = cursor.fetchone()
                    if result:
                        ret_val = result[0] if len(result) == 1 else result
                        safe_log_database_action("函数调用", details=f"{function_name}, 耗时={time.time()-start_time:.3f}s")
                        return ret_val
                    return None
                except:
                    ret_val = cursor.rowcount
                    safe_log_database_action("存储过程调用", details=f"{function_name}, 影响{ret_val}行, 耗时={time.time()-start_time:.3f}s")
                    return ret_val

        except Exception as e:
            safe_log_database_action("函数调用", details=f"{function_name}", success=False)
            safe_log_error("函数调用失败", error=e)
            raise

    def execute_transaction(self, operations: List[Dict[str, Any]]) -> bool:
        """执行事务操作"""
        try:
            start_time = time.time()

            with self.get_connection() as connection:
                with connection.cursor() as cursor:
                    for operation in operations:
                        query = operation.get('query')
                        params = operation.get('params')
                        cursor.execute(query, params)

                    connection.commit()
                    safe_log_database_action("事务", details=f"包含{len(operations)}个操作, 耗时={time.time()-start_time:.3f}s")
                    return True

        except Exception as e:
            safe_log_database_action("事务", details=f"包含{len(operations)}个操作", success=False)
            safe_log_error("事务执行失败", error=e)
            return False

    def test_connection(self) -> bool:
        """测试数据库连接"""
        try:
            result = self.execute_query("SELECT 1", fetch_one=True)
            if result and result[0] == 1:
                safe_log_info("数据库连接测试成功")
                return True
            return False
        except Exception as e:
            safe_log_error("数据库连接测试失败", error=e)
            return False

    def get_server_version(self) -> str:
        """获取数据库版本"""
        try:
            result = self.execute_query("SELECT version()", fetch_one=True)
            return result[0] if result else "未知版本"
        except Exception as e:
            safe_log_error("获取数据库版本失败", error=e)
            return "获取失败"

    def get_database_size(self) -> str:
        """获取数据库大小"""
        try:
            query = "SELECT pg_size_pretty(pg_database_size(%s))"
            result = self.execute_query(query, (settings.DB_NAME,), fetch_one=True)
            return result[0] if result else "未知大小"
        except Exception as e:
            safe_log_error("获取数据库大小失败", error=e)
            return "获取失败"

    def get_table_count(self, table_name: str, where_clause: str = None, params: tuple = None) -> int:
        """获取表记录数"""
        try:
            query = f"SELECT COUNT(*) FROM {table_name}"
            query_params = None

            if where_clause:
                query += f" WHERE {where_clause}"
                query_params = params

            result = self.execute_query(query, query_params, fetch_one=True)
            return result[0] if result else 0
        except Exception as e:
            safe_log_error(f"获取表{table_name}记录数失败", error=e)
            return 0

    def check_table_exists(self, table_name: str) -> bool:
        """检查表是否存在"""
        try:
            query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = %s
            )
            """
            result = self.execute_query(query, (table_name,), fetch_one=True)
            return result[0] if result else False
        except Exception as e:
            safe_log_error(f"检查表{table_name}是否存在失败", error=e)
            return False

    def get_connection_stats(self) -> Dict[str, Any]:
        """获取连接池统计信息"""
        if not self._connection_pool:
            return {'error': '连接池未初始化', 'connected': False}

        try:
            stats = {
                'connected': self._is_connected,
                'minconn': self._connection_pool.minconn,
                'maxconn': self._connection_pool.maxconn,
                'closed': self._connection_pool.closed
            }

            # 获取活跃连接数
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT count(*) FROM pg_stat_activity 
                        WHERE datname = %s AND state = 'active'
                    """, (settings.DB_NAME,))
                    stats['active_connections'] = cursor.fetchone()[0]

                    cursor.execute("""
                        SELECT count(*) FROM pg_stat_activity 
                        WHERE datname = %s
                    """, (settings.DB_NAME,))
                    stats['total_connections'] = cursor.fetchone()[0]

            return stats
        except Exception as e:
            safe_log_error("获取连接统计失败", error=e)
            return {'error': str(e), 'connected': False}

    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._is_connected and self._connection_pool is not None

    def reconnect(self) -> bool:
        """重新连接数据库"""
        try:
            safe_log_info("尝试重新连接数据库...")
            self.close_pool()
            self._init_connection_pool()

            if self.test_connection():
                safe_log_info("数据库重连成功")
                return True
            else:
                safe_log_error("数据库重连失败")
                return False
        except Exception as e:
            safe_log_error("数据库重连异常", error=e)
            return False

    def close_pool(self):
        """关闭连接池"""
        if self._cleanup_done:
            return

        try:
            if self._connection_pool and not self._connection_pool.closed:
                self._connection_pool.closeall()
                safe_log_info("数据库连接池已关闭")
                safe_log_database_action("连接池关闭")
        except Exception as e:
            safe_log_error("关闭连接池失败", error=e)
        finally:
            self._connection_pool = None
            self._is_connected = False

    def __del__(self):
        """析构函数"""
        # 在析构函数中不记录日志，避免程序退出时的错误
        if not self._cleanup_done:
            try:
                if self._connection_pool and not self._connection_pool.closed:
                    self._connection_pool.closeall()
            except Exception:
                pass
            finally:
                self._cleanup_done = True


# 全局数据库连接实例
_db_connection = None
_db_lock = threading.Lock()


def get_db_connection() -> DatabaseConnection:
    """获取全局数据库连接实例"""
    global _db_connection
    if _db_connection is None:
        with _db_lock:
            if _db_connection is None:
                _db_connection = DatabaseConnection()
    return _db_connection


# 便捷函数
def execute_query(query: str, params: Union[tuple, dict] = None,
                 fetch_one: bool = False, dict_cursor: bool = False) -> Union[List[tuple], tuple, None]:
    """执行查询语句"""
    return get_db_connection().execute_query(query, params, fetch_one, dict_cursor)


def execute_update(query: str, params: Union[tuple, dict] = None) -> int:
    """执行更新语句"""
    return get_db_connection().execute_update(query, params)


def execute_many(query: str, params_list: List[Union[tuple, dict]]) -> int:
    """批量执行语句"""
    return get_db_connection().execute_many(query, params_list)


def call_function(function_name: str, params: tuple = None) -> Any:
    """调用存储过程/函数"""
    return get_db_connection().call_function(function_name, params)


def test_connection() -> bool:
    """测试数据库连接"""
    return get_db_connection().test_connection()


def get_database_info() -> Dict[str, Any]:
    """获取数据库信息"""
    db = get_db_connection()
    return {
        'connected': db.is_connected(),
        'version': db.get_server_version(),
        'size': db.get_database_size(),
        'connection_stats': db.get_connection_stats()
    }


def close_database():
    """关闭数据库连接"""
    global _db_connection
    if _db_connection:
        _db_connection.close_pool()
        _db_connection = None


def init_database() -> bool:
    """初始化数据库（检查连接和基础表）"""
    try:
        safe_log_info("开始初始化数据库...")

        # 测试连接
        db = get_db_connection()
        if not db.test_connection():
            safe_log_error("数据库连接失败，无法初始化")
            return False

        # 检查关键表是否存在
        required_tables = [
            'channel_operators',
            'tasks',
            'task_message_details'
        ]

        missing_tables = []
        for table in required_tables:
            if not db.check_table_exists(table):
                missing_tables.append(table)

        if missing_tables:
            safe_log_error(f"缺少必要的数据库表: {', '.join(missing_tables)}")
            safe_log_error("请确保数据库已正确初始化")
            return False

        safe_log_info("数据库初始化检查完成")
        safe_log_database_action("数据库初始化", details="所有必要表已存在")
        return True

    except Exception as e:
        safe_log_error("数据库初始化失败", error=e)
        return False