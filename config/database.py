"""
数据库连接配置模块
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class DatabaseConfig:
    """数据库配置类"""

    def __init__(self):
        self.load_config()

    def load_config(self):
        """加载数据库配置"""
        # 从环境变量获取配置
        self.DATABASE_URL = os.getenv('DATABASE_URL')

        # 如果没有完整的DATABASE_URL，则从分离的配置构建
        if not self.DATABASE_URL:
            self.DB_HOST = os.getenv('DB_HOST', 'localhost')
            self.DB_PORT = os.getenv('DB_PORT', '5432')
            self.DB_NAME = os.getenv('DB_NAME', 'sms_pool_db')
            self.DB_USER = os.getenv('DB_USER', 'sms_user')
            self.DB_PASSWORD = os.getenv('DB_PASSWORD', '')

            # 构建连接URL
            if self.DB_PASSWORD:
                self.DATABASE_URL = (
                    f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}"
                    f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
                )
            else:
                # 如果没有密码，使用默认配置
                self.DATABASE_URL = (
                    "postgresql://sms_user:sms_password@localhost:5432/sms_pool_db"
                )

        # 连接池配置
        self.DB_POOL_SIZE = int(os.getenv('DB_POOL_SIZE', '10'))
        self.DB_MAX_OVERFLOW = int(os.getenv('DB_MAX_OVERFLOW', '20'))
        self.DB_POOL_TIMEOUT = int(os.getenv('DB_POOL_TIMEOUT', '30'))
        self.DB_POOL_RECYCLE = int(os.getenv('DB_POOL_RECYCLE', '3600'))

        # 调试配置
        self.ENABLE_SQL_ECHO = os.getenv('ENABLE_SQL_ECHO', 'false').lower() == 'true'

    def get_database_url(self):
        """获取数据库连接URL"""
        return self.DATABASE_URL

    def get_engine_kwargs(self):
        """获取数据库引擎参数"""
        return {
            'echo': self.ENABLE_SQL_ECHO,
            'pool_size': self.DB_POOL_SIZE,
            'max_overflow': self.DB_MAX_OVERFLOW,
            'pool_timeout': self.DB_POOL_TIMEOUT,
            'pool_recycle': self.DB_POOL_RECYCLE,
            'pool_pre_ping': True,  # 连接前检测
        }

    def validate_config(self):
        """验证配置"""
        if not self.DATABASE_URL:
            raise ValueError("数据库连接配置缺失")

        return True


# 全局配置实例
db_config = DatabaseConfig()