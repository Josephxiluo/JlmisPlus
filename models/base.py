"""
猫池短信系统基础数据模型 - tkinter版
Base data model for SMS Pool System - tkinter version
"""

import sys
import json
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, List, Optional, Union, Type
from dataclasses import dataclass, field, fields
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from database.connection import get_db_connection
    from config.logging_config import get_logger, log_database_action, log_error
except ImportError:
    # 简化的日志处理
    import logging


    def get_logger(name='models'):
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger


    def log_database_action(action, table=None, details=None, success=True):
        logger = get_logger()
        if success:
            logger.info(f"数据库操作: {action} {table or ''} {details or ''}")
        else:
            logger.error(f"数据库操作失败: {action} {table or ''} {details or ''}")


    def log_error(message, error=None):
        logger = get_logger()
        logger.error(f"{message}: {error}" if error else message)

logger = get_logger('models.base')


class ModelValidationError(Exception):
    """模型验证错误"""

    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"字段 '{field}' 验证失败: {message}")


class ModelNotFoundError(Exception):
    """模型未找到错误"""

    def __init__(self, model_name: str, identifier: Any):
        self.model_name = model_name
        self.identifier = identifier
        super().__init__(f"{model_name} 未找到: {identifier}")


class ModelConflictError(Exception):
    """模型冲突错误"""

    def __init__(self, model_name: str, message: str):
        self.model_name = model_name
        self.message = message
        super().__init__(f"{model_name} 冲突: {message}")


@dataclass
class BaseModel(ABC):
    """基础数据模型类"""

    # 主键ID（所有模型都有）
    id: Optional[int] = field(default=None)

    # 公共时间字段
    created_at: Optional[datetime] = field(default=None)
    updated_at: Optional[datetime] = field(default=None)

    # 类属性：表名（子类必须定义）
    _table_name: str = ""

    # 类属性：字段映射（数据库字段名 -> 模型字段名）
    _field_mappings: Dict[str, str] = {}

    # 类属性：验证规则
    _validation_rules: Dict[str, Dict[str, Any]] = {}

    def __post_init__(self):
        """初始化后处理"""
        if not self._table_name:
            raise ValueError(f"{self.__class__.__name__} 必须定义 _table_name")

        # 自动设置时间字段
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

    @classmethod
    def get_table_name(cls) -> str:
        """获取表名"""
        return cls._table_name

    @classmethod
    def get_field_mappings(cls) -> Dict[str, str]:
        """获取字段映射"""
        return cls._field_mappings or {}

    @classmethod
    def get_validation_rules(cls) -> Dict[str, Dict[str, Any]]:
        """获取验证规则"""
        return cls._validation_rules or {}

    def validate(self) -> List[str]:
        """验证模型数据"""
        errors = []

        # 获取验证规则
        rules = self.get_validation_rules()

        for field_name, rule in rules.items():
            value = getattr(self, field_name, None)
            field_errors = self._validate_field(field_name, value, rule)
            errors.extend(field_errors)

        return errors

    def _validate_field(self, field_name: str, value: Any, rule: Dict[str, Any]) -> List[str]:
        """验证单个字段"""
        errors = []

        # 必填验证
        if rule.get('required', False) and (value is None or value == ''):
            errors.append(f"字段 '{field_name}' 是必填的")
            return errors  # 必填验证失败后不再进行其他验证

        # 如果值为空且不是必填，跳过后续验证
        if value is None or value == '':
            return errors

        # 类型验证
        expected_type = rule.get('type')
        if expected_type and not isinstance(value, expected_type):
            errors.append(f"字段 '{field_name}' 类型错误，期望 {expected_type.__name__}，实际 {type(value).__name__}")

        # 长度验证
        if isinstance(value, str):
            min_length = rule.get('min_length')
            max_length = rule.get('max_length')
            if min_length and len(value) < min_length:
                errors.append(f"字段 '{field_name}' 长度不能少于 {min_length} 个字符")
            if max_length and len(value) > max_length:
                errors.append(f"字段 '{field_name}' 长度不能超过 {max_length} 个字符")

        # 数值范围验证
        if isinstance(value, (int, float)):
            min_value = rule.get('min_value')
            max_value = rule.get('max_value')
            if min_value is not None and value < min_value:
                errors.append(f"字段 '{field_name}' 值不能小于 {min_value}")
            if max_value is not None and value > max_value:
                errors.append(f"字段 '{field_name}' 值不能大于 {max_value}")

        # 选择值验证
        choices = rule.get('choices')
        if choices and value not in choices:
            errors.append(f"字段 '{field_name}' 值必须是 {choices} 中的一个")

        # 正则表达式验证
        pattern = rule.get('pattern')
        if pattern and isinstance(value, str):
            import re
            if not re.match(pattern, value):
                errors.append(f"字段 '{field_name}' 格式不正确")

        # 自定义验证函数
        validator = rule.get('validator')
        if validator and callable(validator):
            try:
                if not validator(value):
                    custom_message = rule.get('message', f"字段 '{field_name}' 验证失败")
                    errors.append(custom_message)
            except Exception as e:
                errors.append(f"字段 '{field_name}' 验证异常: {str(e)}")

        return errors

    def is_valid(self) -> bool:
        """检查模型是否有效"""
        return len(self.validate()) == 0

    def to_dict(self, include_none: bool = False, db_fields: bool = False) -> Dict[str, Any]:
        """转换为字典"""
        result = {}
        field_mappings = self.get_field_mappings()

        for field_obj in fields(self):
            field_name = field_obj.name
            field_value = getattr(self, field_name)

            # 跳过None值（如果不包含None）
            if not include_none and field_value is None:
                continue

            # 处理datetime类型
            if isinstance(field_value, datetime):
                field_value = field_value.isoformat()

            # 使用数据库字段名或模型字段名
            if db_fields and field_name in field_mappings:
                key = field_mappings[field_name]
            else:
                key = field_name

            result[key] = field_value

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any], from_db: bool = False) -> 'BaseModel':
        """从字典创建模型实例"""
        field_mappings = cls.get_field_mappings()

        # 创建字段映射的反向映射（数据库字段名 -> 模型字段名）
        if from_db:
            reverse_mappings = {v: k for k, v in field_mappings.items()}
        else:
            reverse_mappings = {}

        # 转换字段名
        model_data = {}
        for key, value in data.items():
            # 从数据库来的数据需要转换字段名
            if from_db and key in reverse_mappings:
                field_name = reverse_mappings[key]
            else:
                field_name = key

            # 处理datetime字段
            if isinstance(value, str) and field_name in ['created_at', 'updated_at']:
                try:
                    value = datetime.fromisoformat(value.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    pass

            model_data[field_name] = value

        return cls(**model_data)

    def to_json(self, **kwargs) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(**kwargs), ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> 'BaseModel':
        """从JSON字符串创建模型实例"""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def copy(self, **changes) -> 'BaseModel':
        """创建副本并应用更改"""
        data = self.to_dict(include_none=True)
        data.update(changes)
        # 创建副本时重置ID和时间
        data['id'] = None
        data['created_at'] = None
        data['updated_at'] = None
        return self.__class__.from_dict(data)

    def get_db_connection(self):
        """获取数据库连接"""
        try:
            return get_db_connection()
        except Exception as e:
            log_error("获取数据库连接失败", error=e)
            raise

    def save(self) -> bool:
        """保存模型到数据库"""
        try:
            # 验证数据
            validation_errors = self.validate()
            if validation_errors:
                raise ModelValidationError("validation", "; ".join(validation_errors))

            db = self.get_db_connection()

            if self.id is None:
                # 新增记录
                return self._insert(db)
            else:
                # 更新记录
                return self._update(db)

        except Exception as e:
            log_error(f"保存 {self.__class__.__name__} 失败", error=e)
            return False

    def _insert(self, db) -> bool:
        """插入新记录"""
        try:
            # 获取所有非None字段
            data = self.to_dict(include_none=False, db_fields=True)

            # 移除ID字段（由数据库自动生成）
            data.pop('id', None)

            # 设置时间字段
            current_time = datetime.now()
            if 'created_at' in self.get_field_mappings().values():
                data[self.get_field_mappings().get('created_at', 'created_at')] = current_time
            if 'updated_at' in self.get_field_mappings().values():
                data[self.get_field_mappings().get('updated_at', 'updated_at')] = current_time

            # 构建SQL
            columns = list(data.keys())
            placeholders = ['%s'] * len(columns)

            query = f"""
                INSERT INTO {self.get_table_name()} ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
                RETURNING id
            """

            # 执行插入
            result = db.execute_query(query, tuple(data.values()), fetch_one=True)

            if result:
                self.id = result[0]
                self.created_at = current_time
                self.updated_at = current_time
                log_database_action("插入", self.get_table_name(), f"ID={self.id}")
                return True

            return False

        except Exception as e:
            log_error(f"插入 {self.__class__.__name__} 记录失败", error=e)
            return False

    def _update(self, db) -> bool:
        """更新记录"""
        try:
            # 获取所有非None字段（排除ID）
            data = self.to_dict(include_none=False, db_fields=True)
            data.pop('id', None)

            # 设置更新时间
            current_time = datetime.now()
            if 'updated_at' in self.get_field_mappings().values():
                data[self.get_field_mappings().get('updated_at', 'updated_at')] = current_time

            # 构建SQL
            set_clauses = [f"{column} = %s" for column in data.keys()]

            query = f"""
                UPDATE {self.get_table_name()}
                SET {', '.join(set_clauses)}
                WHERE id = %s
            """

            # 执行更新
            params = list(data.values()) + [self.id]
            rowcount = db.execute_update(query, tuple(params))

            if rowcount > 0:
                self.updated_at = current_time
                log_database_action("更新", self.get_table_name(), f"ID={self.id}")
                return True

            return False

        except Exception as e:
            log_error(f"更新 {self.__class__.__name__} 记录失败", error=e)
            return False

    def delete(self) -> bool:
        """删除记录"""
        try:
            if self.id is None:
                return False

            db = self.get_db_connection()
            query = f"DELETE FROM {self.get_table_name()} WHERE id = %s"

            rowcount = db.execute_update(query, (self.id,))

            if rowcount > 0:
                log_database_action("删除", self.get_table_name(), f"ID={self.id}")
                return True

            return False

        except Exception as e:
            log_error(f"删除 {self.__class__.__name__} 记录失败", error=e)
            return False

    @classmethod
    def find_by_id(cls, record_id: int) -> Optional['BaseModel']:
        """根据ID查找记录"""
        try:
            db = get_db_connection()
            query = f"SELECT * FROM {cls.get_table_name()} WHERE id = %s"

            result = db.execute_query(query, (record_id,), fetch_one=True, dict_cursor=True)

            if result:
                return cls.from_dict(dict(result), from_db=True)

            return None

        except Exception as e:
            log_error(f"根据ID查找 {cls.__name__} 失败", error=e)
            return None

    @classmethod
    def find_all(cls, where: str = None, params: tuple = None,
                 order_by: str = None, limit: int = None, offset: int = None) -> List['BaseModel']:
        """查找所有记录"""
        try:
            db = get_db_connection()

            query = f"SELECT * FROM {cls.get_table_name()}"

            if where:
                query += f" WHERE {where}"

            if order_by:
                query += f" ORDER BY {order_by}"

            if limit:
                query += f" LIMIT {limit}"

            if offset:
                query += f" OFFSET {offset}"

            results = db.execute_query(query, params, dict_cursor=True)

            return [cls.from_dict(dict(row), from_db=True) for row in results]

        except Exception as e:
            log_error(f"查找 {cls.__name__} 记录失败", error=e)
            return []

    @classmethod
    def find_one(cls, where: str, params: tuple = None) -> Optional['BaseModel']:
        """查找单个记录"""
        results = cls.find_all(where=where, params=params, limit=1)
        return results[0] if results else None

    @classmethod
    def count(cls, where: str = None, params: tuple = None) -> int:
        """统计记录数"""
        try:
            db = get_db_connection()

            query = f"SELECT COUNT(*) FROM {cls.get_table_name()}"

            if where:
                query += f" WHERE {where}"

            result = db.execute_query(query, params, fetch_one=True)

            return result[0] if result else 0

        except Exception as e:
            log_error(f"统计 {cls.__name__} 记录失败", error=e)
            return 0

    @classmethod
    def exists(cls, where: str, params: tuple = None) -> bool:
        """检查记录是否存在"""
        return cls.count(where=where, params=params) > 0

    @classmethod
    def bulk_insert(cls, models: List['BaseModel']) -> bool:
        """批量插入"""
        try:
            if not models:
                return True

            # 验证所有模型
            for model in models:
                validation_errors = model.validate()
                if validation_errors:
                    raise ModelValidationError("validation", f"模型验证失败: {'; '.join(validation_errors)}")

            db = get_db_connection()

            # 获取字段信息（使用第一个模型作为模板）
            first_model = models[0]
            data = first_model.to_dict(include_none=False, db_fields=True)
            data.pop('id', None)  # 移除ID字段

            columns = list(data.keys())
            placeholders = ['%s'] * len(columns)

            query = f"""
                INSERT INTO {cls.get_table_name()} ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
            """

            # 准备批量数据
            batch_data = []
            current_time = datetime.now()

            for model in models:
                model_data = model.to_dict(include_none=False, db_fields=True)
                model_data.pop('id', None)

                # 设置时间字段
                if 'created_at' in first_model.get_field_mappings().values():
                    model_data[first_model.get_field_mappings().get('created_at', 'created_at')] = current_time
                if 'updated_at' in first_model.get_field_mappings().values():
                    model_data[first_model.get_field_mappings().get('updated_at', 'updated_at')] = current_time

                batch_data.append(tuple(model_data.get(col) for col in columns))

            # 执行批量插入
            rowcount = db.execute_many(query, batch_data)

            if rowcount > 0:
                log_database_action("批量插入", cls.get_table_name(), f"插入{rowcount}条记录")
                return True

            return False

        except Exception as e:
            log_error(f"批量插入 {cls.__name__} 记录失败", error=e)
            return False

    @classmethod
    def bulk_update(cls, updates: List[Dict[str, Any]], where_field: str = 'id') -> bool:
        """批量更新"""
        try:
            if not updates:
                return True

            db = get_db_connection()
            current_time = datetime.now()

            # 构建批量更新的SQL
            # 这里使用CASE WHEN的方式实现批量更新
            where_values = [update[where_field] for update in updates]

            # 获取要更新的字段（除了where_field）
            update_fields = set()
            for update in updates:
                update_fields.update(update.keys())
            update_fields.discard(where_field)

            if not update_fields:
                return True

            # 构建CASE WHEN语句
            set_clauses = []
            for field in update_fields:
                case_when_parts = []
                for update in updates:
                    if field in update:
                        case_when_parts.append(f"WHEN {where_field} = %s THEN %s")

                if case_when_parts:
                    set_clauses.append(f"{field} = CASE {' '.join(case_when_parts)} ELSE {field} END")

            # 添加更新时间
            if 'updated_at' in cls.get_field_mappings().values():
                updated_at_field = cls.get_field_mappings().get('updated_at', 'updated_at')
                set_clauses.append(f"{updated_at_field} = %s")

            query = f"""
                UPDATE {cls.get_table_name()}
                SET {', '.join(set_clauses)}
                WHERE {where_field} IN ({', '.join(['%s'] * len(where_values))})
            """

            # 准备参数
            params = []
            for field in update_fields:
                for update in updates:
                    if field in update:
                        params.extend([update[where_field], update[field]])

            # 添加更新时间参数
            if 'updated_at' in cls.get_field_mappings().values():
                params.append(current_time)

            # 添加WHERE条件参数
            params.extend(where_values)

            rowcount = db.execute_update(query, tuple(params))

            if rowcount > 0:
                log_database_action("批量更新", cls.get_table_name(), f"更新{rowcount}条记录")
                return True

            return False

        except Exception as e:
            log_error(f"批量更新 {cls.__name__} 记录失败", error=e)
            return False

    def __str__(self) -> str:
        """字符串表示"""
        return f"{self.__class__.__name__}(id={self.id})"

    def __repr__(self) -> str:
        """调试字符串表示"""
        fields_str = ", ".join([f"{field.name}={getattr(self, field.name)}"
                                for field in fields(self)[:5]])  # 只显示前5个字段
        return f"{self.__class__.__name__}({fields_str})"

    def __eq__(self, other) -> bool:
        """相等比较"""
        if not isinstance(other, self.__class__):
            return False

        if self.id is not None and other.id is not None:
            return self.id == other.id

        # 如果没有ID，比较所有字段
        for field_obj in fields(self):
            if getattr(self, field_obj.name) != getattr(other, field_obj.name):
                return False

        return True

    def __hash__(self) -> int:
        """哈希值"""
        if self.id is not None:
            return hash((self.__class__.__name__, self.id))

        # 如果没有ID，使用所有字段的哈希
        field_values = tuple(getattr(self, field.name) for field in fields(self))
        return hash((self.__class__.__name__, field_values))


class ModelManager:
    """模型管理器"""

    def __init__(self, model_class: Type[BaseModel]):
        self.model_class = model_class

    def create(self, **kwargs) -> BaseModel:
        """创建新模型实例"""
        return self.model_class(**kwargs)

    def get_or_create(self, defaults: Dict[str, Any] = None, **kwargs) -> Tuple[BaseModel, bool]:
        """获取或创建模型实例"""
        # 构建查询条件
        where_parts = []
        params = []

        for key, value in kwargs.items():
            where_parts.append(f"{key} = %s")
            params.append(value)

        where_clause = " AND ".join(where_parts)

        # 尝试查找现有记录
        existing = self.model_class.find_one(where_clause, tuple(params))

        if existing:
            return existing, False

        # 创建新记录
        create_data = kwargs.copy()
        if defaults:
            create_data.update(defaults)

        new_instance = self.create(**create_data)
        if new_instance.save():
            return new_instance, True

        raise Exception("创建模型实例失败")

    def filter(self, **kwargs) -> List[BaseModel]:
        """过滤查询"""
        if not kwargs:
            return self.model_class.find_all()

        where_parts = []
        params = []

        for key, value in kwargs.items():
            where_parts.append(f"{key} = %s")
            params.append(value)

        where_clause = " AND ".join(where_parts)
        return self.model_class.find_all(where_clause, tuple(params))

    def get(self, **kwargs) -> BaseModel:
        """获取单个模型实例"""
        results = self.filter(**kwargs)

        if not results:
            raise ModelNotFoundError(self.model_class.__name__, kwargs)

        if len(results) > 1:
            raise ModelConflictError(self.model_class.__name__, f"找到多个匹配的记录: {kwargs}")

        return results[0]

    def all(self) -> List[BaseModel]:
        """获取所有记录"""
        return self.model_class.find_all()

    def count(self, **kwargs) -> int:
        """统计记录数"""
        if not kwargs:
            return self.model_class.count()

        where_parts = []
        params = []

        for key, value in kwargs.items():
            where_parts.append(f"{key} = %s")
            params.append(value)

        where_clause = " AND ".join(where_parts)
        return self.model_class.count(where_clause, tuple(params))

    def exists(self, **kwargs) -> bool:
        """检查记录是否存在"""
        return self.count(**kwargs) > 0