"""
猫池短信系统文件处理器 - tkinter版
File handler for SMS Pool System - tkinter version
"""

import os
import re
import csv
import sys
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Union, Tuple
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from config.settings import settings
    from config.logging_config import get_logger, log_file_action, log_error, log_info
    from .utils import (
        ensure_directory, get_file_size, get_file_extension,
        format_file_size, get_safe_filename, validate_phone_number,
        clean_phone_number, extract_numbers_from_text
    )
except ImportError:
    # 简化处理
    class MockSettings:
        MAX_UPLOAD_SIZE = 10 * 1024 * 1024
        SUPPORTED_FILE_FORMATS = ['xlsx', 'xls', 'csv', 'txt']
        MAX_PHONE_COUNT = 10000
        UPLOADS_DIR = Path('temp/uploads')
        EXPORTS_DIR = Path('temp/exports')
        DEFAULT_EXPORT_FORMAT = 'xlsx'


    settings = MockSettings()

    import logging


    def get_logger(name='core.file_handler'):
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger


    def log_file_action(action, filename, details=None, success=True):
        logger = get_logger()
        status = "成功" if success else "失败"
        message = f"[文件操作] {action} 文件={filename} {status}"
        if details:
            message += f" - {details}"
        if success:
            logger.info(message)
        else:
            logger.error(message)


    def log_error(message, error=None):
        logger = get_logger()
        logger.error(f"{message}: {error}" if error else message)


    def log_info(message):
        logger = get_logger()
        logger.info(message)


    # 简化的工具函数
    def ensure_directory(path):
        Path(path).mkdir(parents=True, exist_ok=True)
        return Path(path)


    def get_file_size(file_path):
        try:
            return Path(file_path).stat().st_size
        except:
            return 0


    def get_file_extension(file_path):
        return Path(file_path).suffix.lower()


    def format_file_size(size_bytes):
        if size_bytes == 0:
            return "0 B"
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        size = float(size_bytes)
        while size >= 1024.0 and i < len(size_names) - 1:
            size /= 1024.0
            i += 1
        return f"{size:.1f} {size_names[i]}"


    def get_safe_filename(filename):
        return re.sub(r'[<>:"/\\|?*]', '_', filename)


    def validate_phone_number(phone, international=False):
        import re
        if international:
            return bool(re.match(r'^\+\d{8,15}$', phone))
        else:
            return bool(re.match(r'^1[3-9]\d{9}$', phone))


    def clean_phone_number(phone):
        if not phone:
            return ""
        cleaned = re.sub(r'[^\d+]', '', phone)
        if cleaned.startswith('+86') and len(cleaned) == 14:
            cleaned = cleaned[3:]
        return cleaned


    def extract_numbers_from_text(text):
        if not text:
            return []
        patterns = [
            r'\+\d{8,15}',
            r'1[3-9]\d{9}',
            r'\d{3}[-\s]?\d{4}[-\s]?\d{4}'
        ]
        numbers = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            numbers.extend(matches)

        cleaned_numbers = []
        seen = set()
        for number in numbers:
            clean_num = clean_phone_number(number)
            if clean_num and clean_num not in seen:
                if validate_phone_number(clean_num) or validate_phone_number(clean_num, international=True):
                    cleaned_numbers.append(clean_num)
                    seen.add(clean_num)
        return cleaned_numbers

logger = get_logger('core.file_handler')


class FileValidationResult:
    """文件验证结果类"""

    def __init__(self, valid: bool = False, message: str = "",
                 phone_count: int = 0, file_info: Dict[str, Any] = None):
        self.valid = valid
        self.message = message
        self.phone_count = phone_count
        self.file_info = file_info or {}
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def add_error(self, error: str):
        """添加错误信息"""
        self.errors.append(error)
        self.valid = False

    def add_warning(self, warning: str):
        """添加警告信息"""
        self.warnings.append(warning)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'valid': self.valid,
            'message': self.message,
            'phone_count': self.phone_count,
            'file_info': self.file_info,
            'errors': self.errors,
            'warnings': self.warnings
        }


class PhoneNumberExtractor:
    """手机号码提取器类"""

    def __init__(self):
        """初始化提取器"""
        # 手机号码正则模式
        self.patterns = {
            'domestic': r'1[3-9]\d{9}',  # 国内手机号
            'international': r'\+\d{8,15}',  # 国际号码
            'formatted': r'\d{3}[-\s]?\d{4}[-\s]?\d{4}'  # 带分隔符的号码
        }

    def extract_from_text(self, text: str) -> List[str]:
        """从文本中提取手机号码"""
        try:
            if not text:
                return []

            numbers = []

            # 使用不同模式提取
            for pattern_name, pattern in self.patterns.items():
                matches = re.findall(pattern, text)
                numbers.extend(matches)

            # 清理和去重
            return self._clean_and_deduplicate(numbers)

        except Exception as e:
            log_error("从文本提取手机号码失败", error=e)
            return []

    def extract_from_csv(self, file_path: str) -> List[str]:
        """从CSV文件提取手机号码"""
        try:
            numbers = []

            with open(file_path, 'r', encoding='utf-8-sig', newline='') as f:
                # 自动检测分隔符
                sample = f.read(1024)
                f.seek(0)

                sniffer = csv.Sniffer()
                try:
                    delimiter = sniffer.sniff(sample).delimiter
                except:
                    delimiter = ','

                reader = csv.reader(f, delimiter=delimiter)

                for row_num, row in enumerate(reader, 1):
                    for col_num, cell in enumerate(row):
                        if cell and isinstance(cell, str):
                            cell_numbers = self.extract_from_text(cell.strip())
                            numbers.extend(cell_numbers)

            return self._clean_and_deduplicate(numbers)

        except Exception as e:
            log_error(f"从CSV文件{file_path}提取手机号码失败", error=e)
            return []

    def extract_from_excel(self, file_path: str) -> List[str]:
        """从Excel文件提取手机号码"""
        try:
            import pandas as pd

            numbers = []

            # 读取所有工作表
            excel_file = pd.ExcelFile(file_path)

            for sheet_name in excel_file.sheet_names:
                try:
                    df = pd.read_excel(file_path, sheet_name=sheet_name, dtype=str)

                    # 遍历所有列和行
                    for column in df.columns:
                        for value in df[column].dropna():
                            if pd.notna(value):
                                cell_numbers = self.extract_from_text(str(value).strip())
                                numbers.extend(cell_numbers)

                except Exception as e:
                    log_error(f"处理工作表{sheet_name}失败", error=e)
                    continue

            return self._clean_and_deduplicate(numbers)

        except ImportError:
            log_error("需要安装pandas库来处理Excel文件")
            return []
        except Exception as e:
            log_error(f"从Excel文件{file_path}提取手机号码失败", error=e)
            return []

    def extract_from_txt(self, file_path: str) -> List[str]:
        """从文本文件提取手机号码"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return self.extract_from_text(content)

        except Exception as e:
            log_error(f"从文本文件{file_path}提取手机号码失败", error=e)
            return []

    def _clean_and_deduplicate(self, numbers: List[str]) -> List[str]:
        """清理和去重手机号码"""
        try:
            cleaned_numbers = []
            seen = set()

            for number in numbers:
                # 清理号码
                clean_num = clean_phone_number(number)

                if not clean_num or clean_num in seen:
                    continue

                # 验证号码格式
                if validate_phone_number(clean_num) or validate_phone_number(clean_num, international=True):
                    cleaned_numbers.append(clean_num)
                    seen.add(clean_num)

            return cleaned_numbers

        except Exception as e:
            log_error("清理手机号码失败", error=e)
            return []


class FileHandler:
    """文件处理器类"""

    def __init__(self):
        """初始化文件处理器"""
        self.phone_extractor = PhoneNumberExtractor()

        # 配置参数
        self.max_upload_size = getattr(settings, 'MAX_UPLOAD_SIZE', 10 * 1024 * 1024)
        self.supported_formats = getattr(settings, 'SUPPORTED_FILE_FORMATS', ['xlsx', 'xls', 'csv', 'txt'])
        self.max_phone_count = getattr(settings, 'MAX_PHONE_COUNT', 10000)
        self.uploads_dir = getattr(settings, 'UPLOADS_DIR', Path('temp/uploads'))
        self.exports_dir = getattr(settings, 'EXPORTS_DIR', Path('temp/exports'))
        self.default_export_format = getattr(settings, 'DEFAULT_EXPORT_FORMAT', 'xlsx')

        # 确保目录存在
        ensure_directory(self.uploads_dir)
        ensure_directory(self.exports_dir)

        # 统计信息
        self.files_processed = 0
        self.total_phones_extracted = 0
        self.files_exported = 0

    def initialize(self) -> bool:
        """初始化处理器"""
        try:
            log_info("文件处理器初始化开始")

            # 创建必要的目录
            ensure_directory(self.uploads_dir)
            ensure_directory(self.exports_dir)

            log_info(f"文件处理器初始化完成，支持格式: {', '.join(self.supported_formats)}")
            return True

        except Exception as e:
            log_error("文件处理器初始化失败", error=e)
            return False

    def get_status(self) -> Dict[str, Any]:
        """获取处理器状态"""
        return {
            'supported_formats': self.supported_formats,
            'max_upload_size': self.max_upload_size,
            'max_upload_size_mb': round(self.max_upload_size / (1024 * 1024), 2),
            'max_phone_count': self.max_phone_count,
            'uploads_dir': str(self.uploads_dir),
            'exports_dir': str(self.exports_dir),
            'files_processed': self.files_processed,
            'total_phones_extracted': self.total_phones_extracted,
            'files_exported': self.files_exported
        }

    def validate_upload_file(self, file_path: str) -> FileValidationResult:
        """验证上传文件"""
        try:
            file_path = Path(file_path)

            # 检查文件是否存在
            if not file_path.exists():
                result = FileValidationResult(message="文件不存在")
                result.add_error("指定的文件不存在")
                return result

            # 检查文件大小
            file_size = get_file_size(file_path)
            if file_size > self.max_upload_size:
                result = FileValidationResult(message="文件过大")
                result.add_error(
                    f"文件大小{format_file_size(file_size)}超过限制{format_file_size(self.max_upload_size)}")
                return result

            # 检查文件格式
            file_ext = get_file_extension(file_path).lstrip('.')
            if file_ext.lower() not in [fmt.lower() for fmt in self.supported_formats]:
                result = FileValidationResult(message="不支持的文件格式")
                result.add_error(f"文件格式'{file_ext}'不受支持，支持的格式: {', '.join(self.supported_formats)}")
                return result

            # 基本信息
            file_info = {
                'name': file_path.name,
                'size': file_size,
                'size_formatted': format_file_size(file_size),
                'extension': file_ext,
                'last_modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
            }

            # 预览提取手机号码
            try:
                phone_numbers = self.extract_phone_numbers(str(file_path))
                phone_count = len(phone_numbers)

                # 检查号码数量
                if phone_count > self.max_phone_count:
                    result = FileValidationResult(
                        valid=False,
                        message="手机号码数量超过限制",
                        phone_count=phone_count,
                        file_info=file_info
                    )
                    result.add_error(f"文件包含{phone_count}个号码，超过限制{self.max_phone_count}")
                    return result

                if phone_count == 0:
                    result = FileValidationResult(
                        valid=False,
                        message="文件中未找到有效的手机号码",
                        phone_count=0,
                        file_info=file_info
                    )
                    result.add_error("文件中未找到有效的手机号码")
                    return result

                # 验证成功
                result = FileValidationResult(
                    valid=True,
                    message=f"文件验证通过，包含{phone_count}个有效号码",
                    phone_count=phone_count,
                    file_info=file_info
                )

                # 添加一些警告
                if phone_count > 5000:
                    result.add_warning("号码数量较多，处理可能需要较长时间")

                if file_size > 5 * 1024 * 1024:  # 5MB
                    result.add_warning("文件较大，上传可能需要较长时间")

                return result

            except Exception as e:
                result = FileValidationResult(
                    valid=False,
                    message="文件内容解析失败",
                    file_info=file_info
                )
                result.add_error(f"解析文件内容时出错: {str(e)}")
                return result

        except Exception as e:
            log_error(f"验证文件{file_path}失败", error=e)
            result = FileValidationResult(message="文件验证异常")
            result.add_error(f"文件验证过程中出现异常: {str(e)}")
            return result

    def extract_phone_numbers(self, file_path: str) -> List[str]:
        """从文件提取手机号码"""
        try:
            file_path = Path(file_path)

            if not file_path.exists():
                log_error(f"文件{file_path}不存在")
                return []

            file_ext = get_file_extension(file_path).lstrip('.').lower()

            # 根据文件类型选择提取方法
            if file_ext in ['xlsx', 'xls']:
                numbers = self.phone_extractor.extract_from_excel(str(file_path))
            elif file_ext == 'csv':
                numbers = self.phone_extractor.extract_from_csv(str(file_path))
            elif file_ext == 'txt':
                numbers = self.phone_extractor.extract_from_txt(str(file_path))
            else:
                log_error(f"不支持的文件格式: {file_ext}")
                return []

            # 更新统计
            self.files_processed += 1
            self.total_phones_extracted += len(numbers)

            log_file_action(
                "提取手机号码",
                file_path.name,
                f"提取到{len(numbers)}个号码",
                success=True
            )

            return numbers

        except Exception as e:
            log_error(f"从文件{file_path}提取手机号码失败", error=e)
            log_file_action(
                "提取手机号码",
                Path(file_path).name,
                str(e),
                success=False
            )
            return []

    def save_uploaded_file(self, source_path: str, filename: str = None) -> Dict[str, Any]:
        """保存上传的文件"""
        try:
            source_path = Path(source_path)

            if not source_path.exists():
                return {
                    'success': False,
                    'message': '源文件不存在',
                    'error_code': 'SOURCE_NOT_FOUND'
                }

            # 生成安全的文件名
            if filename is None:
                filename = source_path.name

            safe_filename = get_safe_filename(filename)

            # 添加时间戳避免重名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            name_parts = safe_filename.rsplit('.', 1)
            if len(name_parts) > 1:
                safe_filename = f"{name_parts[0]}_{timestamp}.{name_parts[1]}"
            else:
                safe_filename = f"{safe_filename}_{timestamp}"

            # 目标路径
            target_path = self.uploads_dir / safe_filename

            # 复制文件
            import shutil
            shutil.copy2(source_path, target_path)

            # 获取文件信息
            file_info = {
                'original_name': filename,
                'saved_name': safe_filename,
                'saved_path': str(target_path),
                'size': get_file_size(target_path),
                'size_formatted': format_file_size(get_file_size(target_path)),
                'extension': get_file_extension(target_path),
                'upload_time': datetime.now().isoformat()
            }

            log_file_action(
                "保存上传文件",
                safe_filename,
                f"大小: {file_info['size_formatted']}",
                success=True
            )

            return {
                'success': True,
                'message': '文件保存成功',
                'file_info': file_info
            }

        except Exception as e:
            log_error(f"保存上传文件失败", error=e)
            return {
                'success': False,
                'message': f'保存失败: {str(e)}',
                'error_code': 'SAVE_FAILED'
            }

    def export_phone_numbers(self, phone_numbers: List[str], filename: str = None,
                             file_format: str = None, additional_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """导出手机号码到文件"""
        try:
            if not phone_numbers:
                return {
                    'success': False,
                    'message': '没有要导出的手机号码',
                    'error_code': 'NO_DATA'
                }

            # 使用默认格式
            if file_format is None:
                file_format = self.default_export_format

            # 生成文件名
            if filename is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"phone_numbers_{timestamp}.{file_format}"

            safe_filename = get_safe_filename(filename)
            export_path = self.exports_dir / safe_filename

            # 根据格式导出
            if file_format.lower() in ['xlsx', 'xls']:
                result = self._export_to_excel(phone_numbers, export_path, additional_data)
            elif file_format.lower() == 'csv':
                result = self._export_to_csv(phone_numbers, export_path, additional_data)
            elif file_format.lower() == 'txt':
                result = self._export_to_txt(phone_numbers, export_path, additional_data)
            else:
                return {
                    'success': False,
                    'message': f'不支持的导出格式: {file_format}',
                    'error_code': 'UNSUPPORTED_FORMAT'
                }

            if result['success']:
                self.files_exported += 1
                log_file_action("导出手机号码", safe_filename, f"导出{len(phone_numbers)}个号码", success=True)

            return result

        except Exception as e:
            log_error("导出手机号码失败", error=e)
            return {
                'success': False,
                'message': f'导出失败: {str(e)}',
                'error_code': 'EXPORT_FAILED'
            }

    def _export_to_excel(self, phone_numbers: List[str], file_path: Path,
                         additional_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """导出到Excel文件"""
        try:
            import pandas as pd

            # 准备数据
            data = {'手机号码': phone_numbers}

            # 添加附加数据
            if additional_data:
                for key, value in additional_data.items():
                    if isinstance(value, list) and len(value) == len(phone_numbers):
                        data[key] = value
                    elif not isinstance(value, list):
                        data[key] = [value] * len(phone_numbers)

            # 创建DataFrame
            df = pd.DataFrame(data)

            # 导出到Excel
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='手机号码', index=False)

                # 设置列宽
                worksheet = writer.sheets['手机号码']
                for column in df.columns:
                    column_width = max(df[column].astype(str).map(len).max(), len(column)) + 2
                    col_letter = chr(65 + df.columns.get_loc(column))
                    worksheet.column_dimensions[col_letter].width = min(column_width, 50)

            file_info = {
                'file_path': str(file_path),
                'filename': file_path.name,
                'size': get_file_size(file_path),
                'size_formatted': format_file_size(get_file_size(file_path)),
                'format': 'Excel',
                'record_count': len(phone_numbers),
                'export_time': datetime.now().isoformat()
            }

            return {
                'success': True,
                'message': f'成功导出{len(phone_numbers)}个号码到Excel文件',
                'file_info': file_info
            }

        except ImportError:
            return {
                'success': False,
                'message': '需要安装pandas和openpyxl库来导出Excel文件',
                'error_code': 'MISSING_DEPENDENCY'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'导出Excel文件失败: {str(e)}',
                'error_code': 'EXCEL_EXPORT_FAILED'
            }

    def _export_to_csv(self, phone_numbers: List[str], file_path: Path,
                       additional_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """导出到CSV文件"""
        try:
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)

                # 写入表头
                headers = ['手机号码']
                if additional_data:
                    headers.extend(additional_data.keys())
                writer.writerow(headers)

                # 写入数据
                for i, phone in enumerate(phone_numbers):
                    row = [phone]
                    if additional_data:
                        for key, value in additional_data.items():
                            if isinstance(value, list) and i < len(value):
                                row.append(value[i])
                            elif not isinstance(value, list):
                                row.append(value)
                            else:
                                row.append('')
                    writer.writerow(row)

            file_info = {
                'file_path': str(file_path),
                'filename': file_path.name,
                'size': get_file_size(file_path),
                'size_formatted': format_file_size(get_file_size(file_path)),
                'format': 'CSV',
                'record_count': len(phone_numbers),
                'export_time': datetime.now().isoformat()
            }

            return {
                'success': True,
                'message': f'成功导出{len(phone_numbers)}个号码到CSV文件',
                'file_info': file_info
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'导出CSV文件失败: {str(e)}',
                'error_code': 'CSV_EXPORT_FAILED'
            }

    def _export_to_txt(self, phone_numbers: List[str], file_path: Path,
                       additional_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """导出到文本文件"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                # 写入导出信息
                f.write(f"# 手机号码导出文件\n")
                f.write(f"# 导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# 号码数量: {len(phone_numbers)}\n")
                f.write(f"# ================================\n\n")

                # 写入手机号码
                for phone in phone_numbers:
                    f.write(f"{phone}\n")

            file_info = {
                'file_path': str(file_path),
                'filename': file_path.name,
                'size': get_file_size(file_path),
                'size_formatted': format_file_size(get_file_size(file_path)),
                'format': 'TXT',
                'record_count': len(phone_numbers),
                'export_time': datetime.now().isoformat()
            }

            return {
                'success': True,
                'message': f'成功导出{len(phone_numbers)}个号码到文本文件',
                'file_info': file_info
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'导出文本文件失败: {str(e)}',
                'error_code': 'TXT_EXPORT_FAILED'
            }

    def export_task_results(self, task_data: Dict[str, Any],
                            filename: str = None, file_format: str = None) -> Dict[str, Any]:
        """导出任务结果"""
        try:
            # 使用默认格式
            if file_format is None:
                file_format = self.default_export_format

            # 生成文件名
            if filename is None:
                task_name = task_data.get('task_name', 'task')
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{task_name}_results_{timestamp}.{file_format}"

            safe_filename = get_safe_filename(filename)
            export_path = self.exports_dir / safe_filename

            # 准备导出数据
            messages = task_data.get('messages', [])
            if not messages:
                return {
                    'success': False,
                    'message': '没有要导出的任务结果',
                    'error_code': 'NO_DATA'
                }

            # 根据格式导出
            if file_format.lower() in ['xlsx', 'xls']:
                result = self._export_task_results_to_excel(task_data, export_path)
            elif file_format.lower() == 'csv':
                result = self._export_task_results_to_csv(task_data, export_path)
            else:
                return {
                    'success': False,
                    'message': f'不支持的导出格式: {file_format}',
                    'error_code': 'UNSUPPORTED_FORMAT'
                }

            if result['success']:
                self.files_exported += 1
                log_file_action("导出任务结果", safe_filename, f"导出{len(messages)}条记录", success=True)

            return result

        except Exception as e:
            log_error("导出任务结果失败", error=e)
            return {
                'success': False,
                'message': f'导出失败: {str(e)}',
                'error_code': 'EXPORT_FAILED'
            }

    def _export_task_results_to_excel(self, task_data: Dict[str, Any], file_path: Path) -> Dict[str, Any]:
        """导出任务结果到Excel"""
        try:
            import pandas as pd

            messages = task_data.get('messages', [])

            # 准备表格数据
            export_data = []
            for msg in messages:
                export_data.append({
                    '接收号码': msg.get('recipient_number', ''),
                    '发送号码': msg.get('sender_number', ''),
                    '运营商': msg.get('carrier_display', ''),
                    '发送端口': msg.get('send_port', ''),
                    '状态': msg.get('status_display', ''),
                    '重试次数': msg.get('retry_count', 0),
                    '发送时间': msg.get('send_time', ''),
                    '接收时间': msg.get('receive_time', ''),
                    '错误信息': msg.get('error_message', ''),
                    '费用': msg.get('cost', 0),
                    '备注': msg.get('remark', '')
                })

            # 创建DataFrame
            df = pd.DataFrame(export_data)

            # 导出到Excel
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                # 任务摘要
                summary_data = {
                    '项目': ['任务名称', '总数量', '成功数量', '失败数量', '成功率', '导出时间'],
                    '值': [
                        task_data.get('task_name', ''),
                        task_data.get('total_count', 0),
                        task_data.get('success_count', 0),
                        task_data.get('failed_count', 0),
                        f"{task_data.get('success_rate', 0)}%",
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    ]
                }
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='任务摘要', index=False)

                # 详细数据
                df.to_excel(writer, sheet_name='发送明细', index=False)

                # 设置列宽
                for sheet_name in writer.sheets:
                    worksheet = writer.sheets[sheet_name]
                    for column in worksheet.columns:
                        max_length = 0
                        column_letter = column[0].column_letter
                        for cell in column:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(str(cell.value))
                            except:
                                pass
                        adjusted_width = min(max_length + 2, 50)
                        worksheet.column_dimensions[column_letter].width = adjusted_width

            file_info = {
                'file_path': str(file_path),
                'filename': file_path.name,
                'size': get_file_size(file_path),
                'size_formatted': format_file_size(get_file_size(file_path)),
                'format': 'Excel',
                'record_count': len(messages),
                'export_time': datetime.now().isoformat()
            }

            return {
                'success': True,
                'message': f'成功导出任务结果到Excel文件，包含{len(messages)}条记录',
                'file_info': file_info
            }

        except ImportError:
            return {
                'success': False,
                'message': '需要安装pandas和openpyxl库来导出Excel文件',
                'error_code': 'MISSING_DEPENDENCY'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'导出Excel文件失败: {str(e)}',
                'error_code': 'EXCEL_EXPORT_FAILED'
            }

    def _export_task_results_to_csv(self, task_data: Dict[str, Any], file_path: Path) -> Dict[str, Any]:
        """导出任务结果到CSV"""
        try:
            messages = task_data.get('messages', [])

            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)

                # 写入任务摘要
                writer.writerow(['# 任务摘要'])
                writer.writerow(['任务名称', task_data.get('task_name', '')])
                writer.writerow(['总数量', task_data.get('total_count', 0)])
                writer.writerow(['成功数量', task_data.get('success_count', 0)])
                writer.writerow(['失败数量', task_data.get('failed_count', 0)])
                writer.writerow(['成功率', f"{task_data.get('success_rate', 0)}%"])
                writer.writerow(['导出时间', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
                writer.writerow([])  # 空行

                # 写入表头
                headers = ['接收号码', '发送号码', '运营商', '发送端口', '状态', '重试次数',
                           '发送时间', '接收时间', '错误信息', '费用', '备注']
                writer.writerow(headers)

                # 写入数据
                for msg in messages:
                    row = [
                        msg.get('recipient_number', ''),
                        msg.get('sender_number', ''),
                        msg.get('carrier_display', ''),
                        msg.get('send_port', ''),
                        msg.get('status_display', ''),
                        msg.get('retry_count', 0),
                        msg.get('send_time', ''),
                        msg.get('receive_time', ''),
                        msg.get('error_message', ''),
                        msg.get('cost', 0),
                        msg.get('remark', '')
                    ]
                    writer.writerow(row)

            file_info = {
                'file_path': str(file_path),
                'filename': file_path.name,
                'size': get_file_size(file_path),
                'size_formatted': format_file_size(get_file_size(file_path)),
                'format': 'CSV',
                'record_count': len(messages),
                'export_time': datetime.now().isoformat()
            }

            return {
                'success': True,
                'message': f'成功导出任务结果到CSV文件，包含{len(messages)}条记录',
                'file_info': file_info
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'导出CSV文件失败: {str(e)}',
                'error_code': 'CSV_EXPORT_FAILED'
            }

    def cleanup_old_files(self, days: int = 7) -> Dict[str, Any]:
        """清理旧文件"""
        try:
            cutoff_time = datetime.now().timestamp() - (days * 24 * 3600)

            cleaned_uploads = 0
            cleaned_exports = 0

            # 清理上传文件
            for file_path in self.uploads_dir.glob('*'):
                if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                    try:
                        file_path.unlink()
                        cleaned_uploads += 1
                        log_file_action("清理旧文件", file_path.name, success=True)
                    except Exception as e:
                        log_error(f"删除文件{file_path}失败", error=e)

            # 清理导出文件
            for file_path in self.exports_dir.glob('*'):
                if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                    try:
                        file_path.unlink()
                        cleaned_exports += 1
                        log_file_action("清理旧文件", file_path.name, success=True)
                    except Exception as e:
                        log_error(f"删除文件{file_path}失败", error=e)

            total_cleaned = cleaned_uploads + cleaned_exports

            return {
                'success': True,
                'message': f'清理了{total_cleaned}个旧文件',
                'cleaned_uploads': cleaned_uploads,
                'cleaned_exports': cleaned_exports,
                'total_cleaned': total_cleaned,
                'days': days
            }

        except Exception as e:
            log_error("清理旧文件失败", error=e)
            return {
                'success': False,
                'message': f'清理失败: {str(e)}',
                'error_code': 'CLEANUP_FAILED'
            }

    def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """获取文件信息"""
        try:
            file_path = Path(file_path)

            if not file_path.exists():
                return None

            stat = file_path.stat()

            return {
                'name': file_path.name,
                'path': str(file_path),
                'size': stat.st_size,
                'size_formatted': format_file_size(stat.st_size),
                'extension': get_file_extension(file_path),
                'created_time': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'modified_time': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'is_file': file_path.is_file(),
                'is_directory': file_path.is_dir()
            }

        except Exception as e:
            log_error(f"获取文件{file_path}信息失败", error=e)
            return None

    def list_uploaded_files(self) -> List[Dict[str, Any]]:
        """列出已上传的文件"""
        try:
            files = []

            for file_path in self.uploads_dir.glob('*'):
                if file_path.is_file():
                    file_info = self.get_file_info(str(file_path))
                    if file_info:
                        files.append(file_info)

            # 按修改时间排序（最新的在前）
            files.sort(key=lambda x: x['modified_time'], reverse=True)

            return files

        except Exception as e:
            log_error("列出上传文件失败", error=e)
            return []

    def list_exported_files(self) -> List[Dict[str, Any]]:
        """列出已导出的文件"""
        try:
            files = []

            for file_path in self.exports_dir.glob('*'):
                if file_path.is_file():
                    file_info = self.get_file_info(str(file_path))
                    if file_info:
                        files.append(file_info)

            # 按修改时间排序（最新的在前）
            files.sort(key=lambda x: x['modified_time'], reverse=True)

            return files

        except Exception as e:
            log_error("列出导出文件失败", error=e)
            return []

    def delete_file(self, file_path: str) -> Dict[str, Any]:
        """删除文件"""
        try:
            file_path = Path(file_path)

            if not file_path.exists():
                return {
                    'success': False,
                    'message': '文件不存在',
                    'error_code': 'FILE_NOT_FOUND'
                }

            # 检查文件是否在允许的目录中
            if not (file_path.is_relative_to(self.uploads_dir) or file_path.is_relative_to(self.exports_dir)):
                return {
                    'success': False,
                    'message': '只能删除上传或导出目录中的文件',
                    'error_code': 'PERMISSION_DENIED'
                }

            file_info = self.get_file_info(str(file_path))
            file_path.unlink()

            log_file_action("删除文件", file_path.name, success=True)

            return {
                'success': True,
                'message': f'文件{file_path.name}删除成功',
                'deleted_file': file_info
            }

        except Exception as e:
            log_error(f"删除文件{file_path}失败", error=e)
            return {
                'success': False,
                'message': f'删除失败: {str(e)}',
                'error_code': 'DELETE_FAILED'
            }

    def get_directory_info(self) -> Dict[str, Any]:
        """获取目录信息"""
        try:
            def get_dir_stats(directory: Path) -> Dict[str, Any]:
                if not directory.exists():
                    return {'file_count': 0, 'total_size': 0, 'total_size_formatted': '0 B'}

                files = [f for f in directory.glob('*') if f.is_file()]
                total_size = sum(f.stat().st_size for f in files)

                return {
                    'file_count': len(files),
                    'total_size': total_size,
                    'total_size_formatted': format_file_size(total_size)
                }

            uploads_stats = get_dir_stats(self.uploads_dir)
            exports_stats = get_dir_stats(self.exports_dir)

            return {
                'uploads_directory': {
                    'path': str(self.uploads_dir),
                    'exists': self.uploads_dir.exists(),
                    **uploads_stats
                },
                'exports_directory': {
                    'path': str(self.exports_dir),
                    'exists': self.exports_dir.exists(),
                    **exports_stats
                },
                'total_files': uploads_stats['file_count'] + exports_stats['file_count'],
                'total_size': uploads_stats['total_size'] + exports_stats['total_size'],
                'total_size_formatted': format_file_size(uploads_stats['total_size'] + exports_stats['total_size'])
            }

        except Exception as e:
            log_error("获取目录信息失败", error=e)
            return {}


# 全局文件处理器实例
file_handler = FileHandler()