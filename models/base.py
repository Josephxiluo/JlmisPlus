"""
猫池短信系统基础数据模型 - tkinter版 (修复版)
Base data models for SMS Pool System - tkinter version (Fixed)
"""

import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from decimal import Decimal

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from config.logging_config import get_logger
    logger = get_logger('models.base')
except ImportError:
    import logging
    logger = logging.getLogger('models.base')


class ModelValidationError(Exception):
    """模型验证异常"""
    pass


class ModelNotFoundError(Exception):
    """模型未找到异常"""
    pass


class DatabaseError(Exception):
    """数据库操作异常"""
    pass


@dataclass
class BaseModel:
    """基础数据模型类"""

    # 使用 field(default_factory=dict) 而不是默认的 {}
    _field_mappings: Dict[str, str] = field(default_factory=dict, init=False, repr=False)
    _table_name: str = field(default="", init=False, repr=False)
    _primary_key: str = field(default="id", init=False, repr=False)

    def __post_init__(self):
        """初始化后处理"""
        self._setup_field_mappings()

    def _setup_field_mappings(self):
        """设置字段映射关系"""
        # 子类可以重写此方法来设置具体的字段映射
        pass

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {}
        for field_name, value in self.__dict__.items():
            # 跳过私有字段
            if field_name.startswith('_'):
                continue

            # 处理特殊类型
            if isinstance(value, datetime):
                result[field_name] = value.isoformat()
            elif isinstance(value, Decimal):
                result[field_name] = float(value)
            elif value is None:
                result[field_name] = None
            else:
                result[field_name] = value

        return result

    def to_db_dict(self) -> Dict[str, Any]:
        """转换为数据库字段字典"""
        result = {}
        data = self.to_dict()

        for model_field, db_field in self._field_mappings.items():
            if model_field in data:
                result[db_field] = data[model_field]

        return result

    def from_dict(self, data: Dict[str, Any]) -> 'BaseModel':
        """从字典创建模型实例"""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
        return self

    def from_db_dict(self, data: Dict[str, Any]) -> 'BaseModel':
        """从数据库字段字典创建模型实例"""
        # 反向映射：数据库字段 -> 模型字段
        reverse_mappings = {v: k for k, v in self._field_mappings.items()}

        for db_field, value in data.items():
            model_field = reverse_mappings.get(db_field, db_field)
            if hasattr(self, model_field):
                setattr(self, model_field, value)

        return self

    def validate(self) -> bool:
        """验证模型数据"""
        # 基础验证逻辑，子类可以重写
        return True

    def get_create_sql(self) -> tuple:
        """获取创建记录的SQL语句和参数"""
        if not self._table_name:
            raise ValueError("表名未设置")

        db_data = self.to_db_dict()

        # 移除主键字段（如果是自增的）
        if self._primary_key in db_data and db_data[self._primary_key] is None:
            db_data.pop(self._primary_key)

        fields = list(db_data.keys())
        placeholders = ['%s'] * len(fields)
        values = list(db_data.values())

        sql = f"INSERT INTO {self._table_name} ({', '.join(fields)}) VALUES ({', '.join(placeholders)}) RETURNING {self._primary_key}"

        return sql, values

    def get_update_sql(self, condition_field: str = None) -> tuple:
        """获取更新记录的SQL语句和参数"""
        if not self._table_name:
            raise ValueError("表名未设置")

        condition_field = condition_field or self._primary_key
        db_data = self.to_db_dict()

        # 获取条件值
        condition_value = db_data.get(condition_field)
        if condition_value is None:
            raise ValueError(f"条件字段 {condition_field} 的值不能为空")

        # 移除条件字段
        update_data = {k: v for k, v in db_data.items() if k != condition_field}

        if not update_data:
            raise ValueError("没有需要更新的字段")

        set_clauses = [f"{field} = %s" for field in update_data.keys()]
        values = list(update_data.values()) + [condition_value]

        sql = f"UPDATE {self._table_name} SET {', '.join(set_clauses)} WHERE {condition_field} = %s"

        return sql, values

    def get_delete_sql(self, condition_field: str = None) -> tuple:
        """获取删除记录的SQL语句和参数"""
        if not self._table_name:
            raise ValueError("表名未设置")

        condition_field = condition_field or self._primary_key
        db_data = self.to_db_dict()

        condition_value = db_data.get(condition_field)
        if condition_value is None:
            raise ValueError(f"条件字段 {condition_field} 的值不能为空")

        sql = f"DELETE FROM {self._table_name} WHERE {condition_field} = %s"

        return sql, [condition_value]

    def get_select_sql(self, condition_field: str = None, condition_value: Any = None) -> tuple:
        """获取查询记录的SQL语句和参数"""
        if not self._table_name:
            raise ValueError("表名未设置")

        sql = f"SELECT * FROM {self._table_name}"
        params = []

        if condition_field and condition_value is not None:
            sql += f" WHERE {condition_field} = %s"
            params.append(condition_value)

        return sql, params

    @classmethod
    def create_from_dict(cls, data: Dict[str, Any]) -> 'BaseModel':
        """从字典创建模型实例（类方法）"""
        instance = cls()
        return instance.from_dict(data)

    @classmethod
    def create_from_db_dict(cls, data: Dict[str, Any]) -> 'BaseModel':
        """从数据库字段字典创建模型实例（类方法）"""
        instance = cls()
        return instance.from_db_dict(data)

    def __str__(self) -> str:
        """字符串表示"""
        return f"{self.__class__.__name__}({self.to_dict()})"

    def __repr__(self) -> str:
        """详细字符串表示"""
        return self.__str__()


@dataclass
class TimestampMixin:
    """时间戳混入类"""
    created_time: Optional[datetime] = None
    updated_time: Optional[datetime] = None

    def set_create_time(self):
        """设置创建时间"""
        self.created_time = datetime.now()

    def set_update_time(self):
        """设置更新时间"""
        self.updated_time = datetime.now()


@dataclass
class BaseEntity(BaseModel, TimestampMixin):
    """带时间戳的基础实体类"""

    def __post_init__(self):
        """初始化后处理"""
        super().__post_init__()

        # 如果是新创建的实体，设置创建时间
        if self.created_time is None:
            self.set_create_time()


# 工具函数
def validate_required_fields(model: BaseModel, required_fields: List[str]) -> bool:
    """验证必填字段"""
    model_dict = model.to_dict()

    for field in required_fields:
        if field not in model_dict or model_dict[field] is None or model_dict[field] == '':
            raise ModelValidationError(f"必填字段 {field} 不能为空")

    return True


def validate_field_length(model: BaseModel, field_lengths: Dict[str, int]) -> bool:
    """验证字段长度"""
    model_dict = model.to_dict()

    for field, max_length in field_lengths.items():
        if field in model_dict and model_dict[field] is not None:
            value = str(model_dict[field])
            if len(value) > max_length:
                raise ModelValidationError(f"字段 {field} 长度不能超过 {max_length} 个字符")

    return True


def validate_field_type(model: BaseModel, field_types: Dict[str, type]) -> bool:
    """验证字段类型"""
    model_dict = model.to_dict()

    for field, expected_type in field_types.items():
        if field in model_dict and model_dict[field] is not None:
            if not isinstance(model_dict[field], expected_type):
                raise ModelValidationError(f"字段 {field} 类型错误，期望 {expected_type.__name__}")

    return True


def validate_field_range(model: BaseModel, field_ranges: Dict[str, tuple]) -> bool:
    """验证数值字段范围"""
    model_dict = model.to_dict()

    for field, (min_val, max_val) in field_ranges.items():
        if field in model_dict and model_dict[field] is not None:
            value = model_dict[field]
            if not (min_val <= value <= max_val):
                raise ModelValidationError(f"字段 {field} 值必须在 {min_val} 到 {max_val} 之间")

    return True


def safe_convert_type(value: Any, target_type: type, default: Any = None) -> Any:
    """安全类型转换"""
    if value is None:
        return default

    try:
        if target_type == datetime and isinstance(value, str):
            # 尝试解析ISO格式的日期时间字符串
            return datetime.fromisoformat(value.replace('Z', '+00:00'))
        elif target_type == Decimal:
            return Decimal(str(value))
        else:
            return target_type(value)
    except (ValueError, TypeError) as e:
        logger.warning(f"类型转换失败: {value} -> {target_type.__name__}, 错误: {e}")
        return default


def get_table_fields(table_name: str) -> List[str]:
    """获取表的字段列表（需要数据库连接）"""
    try:
        from database.connection import execute_query

        query = """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = %s 
        ORDER BY ordinal_position
        """

        result = execute_query(query, (table_name,))
        return [row[0] for row in result] if result else []

    except Exception as e:
        logger.error(f"获取表 {table_name} 字段失败: {e}")
        return []


def create_model_from_table(table_name: str, class_name: str = None) -> type:
    """从数据库表动态创建模型类"""
    if not class_name:
        # 将表名转换为类名（snake_case -> PascalCase）
        class_name = ''.join(word.capitalize() for word in table_name.split('_'))

    fields = get_table_fields(table_name)

    # 创建dataclass字段
    annotations = {}
    defaults = {}

    for field_name in fields:
        annotations[field_name] = Optional[Any]
        defaults[field_name] = None

    # 动态创建类
    attrs = {
        '__annotations__': annotations,
        '_table_name': field(default=table_name, init=False, repr=False),
        '_field_mappings': field(default_factory=lambda: {f: f for f in fields}, init=False, repr=False),
        **defaults
    }

    # 创建新的模型类
    model_class = type(class_name, (BaseModel,), attrs)

    # 应用dataclass装饰器
    return dataclass(model_class)


# 常用的字段验证规则
COMMON_VALIDATIONS = {
    'username': {
        'required': True,
        'max_length': 50,
        'type': str
    },
    'password': {
        'required': True,
        'min_length': 6,
        'max_length': 255,
        'type': str
    },
    'email': {
        'required': False,
        'max_length': 100,
        'type': str,
        'pattern': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    },
    'phone': {
        'required': False,
        'max_length': 20,
        'type': str,
        'pattern': r'^[0-9+\-\s()]+$'
    },
    'credits': {
        'required': False,
        'type': int,
        'min_value': 0
    }
}


def apply_common_validation(model: BaseModel, field_name: str) -> bool:
    """应用常用验证规则"""
    if field_name not in COMMON_VALIDATIONS:
        return True

    rules = COMMON_VALIDATIONS[field_name]
    model_dict = model.to_dict()
    value = model_dict.get(field_name)

    # 必填验证
    if rules.get('required', False) and (value is None or value == ''):
        raise ModelValidationError(f"字段 {field_name} 是必填的")

    # 如果值为空且非必填，跳过后续验证
    if value is None or value == '':
        return True

    # 类型验证
    if 'type' in rules and not isinstance(value, rules['type']):
        raise ModelValidationError(f"字段 {field_name} 类型错误，期望 {rules['type'].__name__}")

    # 长度验证
    if isinstance(value, str):
        if 'max_length' in rules and len(value) > rules['max_length']:
            raise ModelValidationError(f"字段 {field_name} 长度不能超过 {rules['max_length']} 个字符")

        if 'min_length' in rules and len(value) < rules['min_length']:
            raise ModelValidationError(f"字段 {field_name} 长度不能少于 {rules['min_length']} 个字符")

    # 数值范围验证
    if isinstance(value, (int, float)):
        if 'min_value' in rules and value < rules['min_value']:
            raise ModelValidationError(f"字段 {field_name} 值不能小于 {rules['min_value']}")

        if 'max_value' in rules and value > rules['max_value']:
            raise ModelValidationError(f"字段 {field_name} 值不能大于 {rules['max_value']}")

    # 正则表达式验证
    if 'pattern' in rules and isinstance(value, str):
        import re
        if not re.match(rules['pattern'], value):
            raise ModelValidationError(f"字段 {field_name} 格式不正确")

    return True