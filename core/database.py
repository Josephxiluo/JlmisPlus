"""
数据库模型和操作模块 - SQLAlchemy 2.0兼容版本
"""
import os
import json
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, Float, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.dialects.postgresql import JSON, UUID
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

# 创建基类 - SQLAlchemy 2.0 语法
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
    subject = Column(String(200), comment='短信主题')
    total_count = Column(Integer, default=0, comment='总号码数量')
    success_count = Column(Integer, default=0, comment='成功发送数量')
    failed_count = Column(Integer, default=0, comment='失败发送数量')
    status = Column(String(20), default='pending', comment='任务状态')
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False, comment='创建人ID')
    created_time = Column(DateTime, default=datetime.now, comment='创建时间')
    started_time = Column(DateTime, comment='开始时间')
    completed_time = Column(DateTime, comment='完成时间')


class SendRecord(Base):
    """发送记录表"""
    __tablename__ = 'send_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=False, comment='所属任务ID')
    phone_number = Column(String(20), nullable=False, comment='目标号码')
    message_content = Column(Text, comment='实际发送内容')
    port_name = Column(String(50), comment='使用的端口')
    status = Column(String(20), nullable=False, comment='发送状态')
    error_message = Column(Text, comment='错误信息')
    send_time = Column(DateTime, comment='发送时间')
    response_time = Column(Float, comment='响应时间(毫秒)')
    retry_count = Column(Integer, default=0, comment='重试次数')
    operator = Column(String(50), comment='运营商')
    signal_strength = Column(Integer, comment='信号强度')
    created_time = Column(DateTime, default=datetime.now, comment='创建时间')


class Port(Base):
    """端口设备表"""
    __tablename__ = 'ports'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False, comment='端口名称')
    description = Column(String(200), comment='端口描述')
    operator = Column(String(50), comment='运营商')
    device_model = Column(String(100), comment='设备型号')
    status = Column(String(20), default='inactive', comment='端口状态')
    total_sent = Column(Integer, default=0, comment='总发送数量')
    success_sent = Column(Integer, default=0, comment='成功发送数量')
    failed_sent = Column(Integer, default=0, comment='失败发送数量')
    last_used_time = Column(DateTime, comment='最后使用时间')
    created_time = Column(DateTime, default=datetime.now, comment='创建时间')
    is_enabled = Column(Boolean, default=True, comment='是否启用')


class MessageTemplate(Base):
    """短信模板表"""
    __tablename__ = 'message_templates'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, comment='模板名称')
    content = Column(Text, nullable=False, comment='模板内容')
    variables = Column(JSON, comment='变量列表')
    category = Column(String(50), comment='模板分类')
    is_active = Column(Boolean, default=True, comment='是否启用')
    created_time = Column(DateTime, default=datetime.now, comment='创建时间')
    usage_count = Column(Integer, default=0, comment='使用次数')


class SystemLog(Base):
    """系统日志表"""
    __tablename__ = 'system_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    level = Column(String(20), nullable=False, comment='日志级别')
    message = Column(Text, nullable=False, comment='日志消息')
    module = Column(String(100), comment='模块名称')
    function = Column(String(100), comment='函数名称')
    task_id = Column(Integer, comment='关联任务ID')
    port_name = Column(String(50), comment='关联端口')
    created_time = Column(DateTime, default=datetime.now, comment='创建时间')
    user_id = Column(String(100), comment='用户ID')
    extra_data = Column(JSON, comment='额外数据')


class DatabaseManager:
    """数据库管理器 - SQLAlchemy 2.0兼容版本"""

    def __init__(self, database_url=None):
        """初始化数据库连接"""
        # 导入配置
        from config.database import db_config

        if database_url is None:
            database_url = db_config.get_database_url()

        engine_kwargs = db_config.get_engine_kwargs()

        self.database_url = database_url

        # 验证配置
        db_config.validate_config()

        # 创建数据库引擎
        self.engine = create_engine(database_url, **engine_kwargs)

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
                print("创建默认管理员用户")

            # 检查是否已有默认模板
            if self.session.query(MessageTemplate).count() == 0:
                default_templates = [
                    MessageTemplate(
                        name='默认模板',
                        content='您好，这是一条测试短信。',
                        category='default'
                    ),
                    MessageTemplate(
                        name='验证码模板',
                        content='您的验证码是：{code}，请在5分钟内使用。',
                        variables=['code'],
                        category='verification'
                    ),
                    MessageTemplate(
                        name='通知模板',
                        content='尊敬的{name}，您有一条新消息：{message}',
                        variables=['name', 'message'],
                        category='notification'
                    )
                ]

                for template in default_templates:
                    self.session.add(template)
                print("创建默认模板")

            self.session.commit()
            print("默认数据初始化完成")

        except Exception as e:
            print(f"初始化默认数据失败: {e}")
            self.session.rollback()

    def close(self):
        """关闭数据库连接"""
        if self.session:
            self.session.close()

    # 用户管理
    def create_user(self, username, email, password, role='user', **kwargs):
        """创建用户"""
        try:
            # 检查用户名和邮箱是否已存在
            if self.session.query(User).filter(User.username == username).first():
                raise ValueError("用户名已存在")

            if self.session.query(User).filter(User.email == email).first():
                raise ValueError("邮箱已存在")

            user = User(
                username=username,
                email=email,
                role=role,
                **kwargs
            )
            user.set_password(password)

            self.session.add(user)
            self.session.commit()

            # 记录日志
            self.add_log('INFO', f'创建用户: {username}', 'user_manager', user_id=str(user.id))

            return user.id
        except Exception as e:
            self.session.rollback()
            self.add_log('ERROR', f'创建用户失败: {e}', 'user_manager')
            raise e

    def authenticate_user(self, username, password, ip_address=None):
        """用户认证"""
        try:
            user = self.session.query(User).filter(
                User.username == username,
                User.status == 'active'
            ).first()

            if user and user.check_password(password):
                self.add_log('INFO', f'用户登录: {username}', 'auth', user_id=str(user.id))
                return user

            self.add_log('WARNING', f'登录失败: {username}', 'auth')
            return None
        except Exception as e:
            self.add_log('ERROR', f'用户认证失败: {e}', 'auth')
            return None

    # 任务管理
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

            self.add_log('INFO', f'创建任务: {name}', 'task_manager', 
                        user_id=str(created_by), task_id=task.id)

            return task.id
        except Exception as e:
            self.session.rollback()
            self.add_log('ERROR', f'创建任务失败: {e}', 'task_manager', 
                        user_id=str(created_by))
            raise e

    def get_task(self, task_id):
        """获取任务"""
        return self.session.query(Task).filter(Task.id == task_id).first()

    def update_task_status(self, task_id, status, **kwargs):
        """更新任务状态"""
        try:
            task = self.get_task(task_id)
            if task:
                old_status = task.status
                task.status = status

                # 更新其他字段
                for key, value in kwargs.items():
                    if hasattr(task, key):
                        setattr(task, key, value)

                # 设置时间戳
                if status == 'running' and not task.started_time:
                    task.started_time = datetime.now()
                elif status in ['completed', 'stopped', 'failed']:
                    task.completed_time = datetime.now()

                self.session.commit()

                self.add_log('INFO', f'任务状态更新: {task.name} {old_status} -> {status}', 
                           'task_manager', task_id=task_id)
                return True
        except Exception as e:
            self.session.rollback()
            self.add_log('ERROR', f'更新任务状态失败: {e}', 'task_manager', task_id=task_id)
            return False

    # 发送记录管理
    def add_send_record(self, task_id, phone_number, message_content, port_name, status, **kwargs):
        """添加发送记录"""
        try:
            record = SendRecord(
                task_id=task_id,
                phone_number=phone_number,
                message_content=message_content,
                port_name=port_name,
                status=status,
                send_time=datetime.now(),
                **kwargs
            )

            self.session.add(record)
            self.session.commit()

            return record.id
        except Exception as e:
            self.session.rollback()
            self.add_log('ERROR', f'添加发送记录失败: {e}', 'message_sender', task_id=task_id)
            return None

    # 端口管理
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
            self.add_log('ERROR', f'添加/更新端口失败: {e}', 'port_manager')
            return None

    def get_port(self, name):
        """获取端口信息"""
        return self.session.query(Port).filter(Port.name == name).first()

    # 日志管理
    def add_log(self, level, message, module, function=None, task_id=None, 
               port_name=None, user_id='system', extra_data=None):
        """添加日志"""
        try:
            log = SystemLog(
                level=level,
                message=message,
                module=module,
                function=function,
                task_id=task_id,
                port_name=port_name,
                user_id=user_id,
                extra_data=extra_data
            )

            self.session.add(log)
            self.session.commit()
        except Exception as e:
            # 日志记录失败不应该影响主要功能
            print(f"记录日志失败: {e}")


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
