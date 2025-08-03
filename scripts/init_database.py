"""
数据库模型和操作模块 - 简化版本
"""
import os
import json
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import JSON, UUID
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

# 创建基类
Base = declarative_base()


class User(Base):
    """用户表"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, comment='用户名')
    email = Column(String(100), unique=True, nullable=False, comment='邮箱')
    password_hash = Column(String(255), nullable=False, comment='密码哈希')
    real_name = Column(String(100), comment='真实姓名')
    role = Column(String(20), default='user', comment='角色')
    status = Column(String(20), default='active', comment='状态')
    created_time = Column(DateTime, default=datetime.now, comment='创建时间')

    def set_password(self, password):
        """设置密码"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)


class Task(Base):
    """任务表"""
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, comment='任务名称')
    phone_numbers = Column(JSON, nullable=False, comment='目标号码列表')
    message_content = Column(Text, nullable=False, comment='短信内容')
    total_count = Column(Integer, default=0, comment='总号码数量')
    success_count = Column(Integer, default=0, comment='成功发送数量')
    failed_count = Column(Integer, default=0, comment='失败发送数量')
    status = Column(String(20), default='pending', comment='任务状态')
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False, comment='创建人ID')
    created_time = Column(DateTime, default=datetime.now, comment='创建时间')


class SendRecord(Base):
    """发送记录表"""
    __tablename__ = 'send_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=False, comment='所属任务ID')
    phone_number = Column(String(20), nullable=False, comment='目标号码')
    message_content = Column(Text, comment='实际发送内容')
    port_name = Column(String(50), comment='使用的端口')
    status = Column(String(20), nullable=False, comment='发送状态')
    send_time = Column(DateTime, comment='发送时间')
    created_time = Column(DateTime, default=datetime.now, comment='创建时间')


class Port(Base):
    """端口设备表"""
    __tablename__ = 'ports'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False, comment='端口名称')
    operator = Column(String(50), comment='运营商')
    status = Column(String(20), default='inactive', comment='端口状态')
    total_sent = Column(Integer, default=0, comment='总发送数量')
    success_sent = Column(Integer, default=0, comment='成功发送数量')
    created_time = Column(DateTime, default=datetime.now, comment='创建时间')


class DatabaseManager:
    """数据库管理器"""

    def __init__(self, database_url=None):
        """初始化数据库连接"""
        if database_url is None:
            database_url = os.getenv(
                'DATABASE_URL',
                'postgresql://sms_user:sms_password@localhost:5432/sms_pool_db'
            )

        self.database_url = database_url

        # 创建数据库引擎
        self.engine = create_engine(database_url, echo=False)

        # 创建会话工厂
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def create_tables(self):
        """创建所有表"""
        try:
            Base.metadata.create_all(self.engine)
            print("数据库表创建成功")
        except Exception as e:
            print(f"创建数据库表失败: {e}")

    def init_default_data(self):
        """初始化默认数据"""
        try:
            # 检查是否已有管理员用户
            admin_user = self.session.query(User).filter(User.username == 'admin').first()
            if not admin_user:
                admin_user = User(
                    username='admin',
                    email='admin@example.com',
                    real_name='系统管理员',
                    role='admin'
                )
                admin_user.set_password('admin123')  # 默认密码，生产环境需要更改
                self.session.add(admin_user)
                self.session.commit()
                print("默认管理员用户创建成功")
            else:
                print("管理员用户已存在")

            print("默认数据初始化完成")

        except Exception as e:
            print(f"初始化默认数据失败: {e}")
            self.session.rollback()

    def close(self):
        """关闭数据库连接"""
        if self.session:
            self.session.close()

    def create_user(self, username, email, password, **kwargs):
        """创建用户"""
        try:
            user = User(username=username, email=email, **kwargs)
            user.set_password(password)

            self.session.add(user)
            self.session.commit()

            return user.id
        except Exception as e:
            self.session.rollback()
            raise e

    def authenticate_user(self, username, password):
        """用户认证"""
        try:
            user = self.session.query(User).filter(
                User.username == username,
                User.status == 'active'
            ).first()

            if user and user.check_password(password):
                return user

            return None
        except Exception as e:
            return None

    def create_task(self, name, phone_numbers, message_content, created_by, **kwargs):
        """创建任务"""
        try:
            task = Task(
                name=name,
                phone_numbers=phone_numbers,
                message_content=message_content,
                total_count=len(phone_numbers),
                created_by=created_by,
                **kwargs
            )

            self.session.add(task)
            self.session.commit()

            return task.id
        except Exception as e:
            self.session.rollback()
            raise e

    def add_or_update_port(self, name, **kwargs):
        """添加或更新端口"""
        try:
            port = self.session.query(Port).filter(Port.name == name).first()

            if port:
                # 更新现有端口
                for key, value in kwargs.items():
                    if hasattr(port, key):
                        setattr(port, key, value)
            else:
                # 创建新端口
                port = Port(name=name, **kwargs)
                self.session.add(port)

            self.session.commit()
            return port.id
        except Exception as e:
            self.session.rollback()
            return None


# 全局数据库实例
db_manager = None


def get_db_manager():
    """获取数据库管理器实例"""
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager()
    return db_manager


def close_db():
    """关闭数据库连接"""
    global db_manager
    if db_manager:
        db_manager.close()
        db_manager = None