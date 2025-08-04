#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目完整性检查脚本
Project integrity check script
"""

import os
import sys
from pathlib import Path


def check_project_structure():
    """检查项目结构完整性"""
    print("猫池短信系统 - 项目结构检查")
    print("=" * 50)

    project_root = Path(__file__).parent

    # 定义完整的项目结构
    project_structure = {
        # 根目录文件
        'files': [
            'app.py',
            'README.md',
            'requirements.txt',
            '.gitignore',
            'test_startup.py',
            'project_check.py'
        ],

        # 目录和子文件
        'directories': {
            'config': [
                '__init__.py',
                'settings.py',
                'logging_config.py'
            ],
            'database': [
                '__init__.py',
                'connection.py'
            ],
            'models': [
                '__init__.py',
                'base.py',
                'user.py',
                'task.py',
                'message.py',
                'port.py'
            ],
            'services': [
                '__init__.py',
                'auth_service.py',
                'task_service.py',
                'port_service.py',
                'message_service.py',
                'credit_service.py',
                'export_service.py'
            ],
            'core': [
                '__init__.py',
                'port_scanner.py',
                'task_executor.py',
                'message_sender.py',
                'monitor_detector.py',
                'file_handler.py',
                'utils.py'
            ],
            'ui': [
                '__init__.py',
                'login_window.py',
                'main_window.py'
            ],
            'ui/components': [
                '__init__.py',
                'status_bar.py',
                'task_list_widget.py',
                'port_grid_widget.py',
                'timer_widget.py'
            ],
            'ui/dialogs': [
                '__init__.py',
                'add_task_dialog.py',
                'task_test_dialog.py',
                'task_edit_dialog.py',
                'config_dialog.py',
                'export_dialog.py'
            ],
            'ui/styles': [
                '__init__.py',
                'orange_theme.qss'
            ],
            'static/icons': [],
            'temp': [],
            'temp/logs': [],
            'temp/uploads': [],
            'temp/exports': [],
            'tests': [
                '__init__.py',
                'test_basic.py'
            ]
        }
    }

    # 检查根目录文件
    print("检查根目录文件:")
    missing_files = []
    for file_name in project_structure['files']:
        file_path = project_root / file_name
        if file_path.exists():
            print(f"✅ {file_name}")
        else:
            print(f"❌ {file_name}")
            missing_files.append(file_name)

    # 检查目录结构
    print("\n检查目录结构:")
    missing_dirs = []
    missing_dir_files = []

    for dir_name, files in project_structure['directories'].items():
        dir_path = project_root / dir_name
        if dir_path.exists():
            print(f"✅ {dir_name}/")

            # 检查目录中的文件
            for file_name in files:
                file_path = dir_path / file_name
                if file_path.exists():
                    print(f"  ✅ {file_name}")
                else:
                    print(f"  ❌ {file_name}")
                    missing_dir_files.append(f"{dir_name}/{file_name}")
        else:
            print(f"❌ {dir_name}/")
            missing_dirs.append(dir_name)

    # 创建缺失的目录
    print("\n创建缺失的目录:")
    for dir_name in missing_dirs:
        try:
            dir_path = project_root / dir_name
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"✅ 创建目录: {dir_name}/")
        except Exception as e:
            print(f"❌ 创建目录失败 {dir_name}/: {e}")

    # 创建基本的 __init__.py 文件
    print("\n创建缺失的 __init__.py 文件:")
    init_files = [
        'config/__init__.py',
        'database/__init__.py',
        'models/__init__.py',
        'services/__init__.py',
        'core/__init__.py',
        'ui/__init__.py',
        'ui/components/__init__.py',
        'ui/dialogs/__init__.py',
        'ui/styles/__init__.py',
        'tests/__init__.py'
    ]

    for init_file in init_files:
        init_path = project_root / init_file
        if not init_path.exists():
            try:
                init_path.parent.mkdir(parents=True, exist_ok=True)
                init_path.write_text('"""模块初始化文件"""\n', encoding='utf-8')
                print(f"✅ 创建: {init_file}")
            except Exception as e:
                print(f"❌ 创建失败 {init_file}: {e}")

    # 生成报告
    print("\n" + "=" * 50)
    print("检查报告:")
    print(f"✅ 根目录文件: {len(project_structure['files']) - len(missing_files)}/{len(project_structure['files'])}")
    print(
        f"✅ 目录结构: {len(project_structure['directories']) - len(missing_dirs)}/{len(project_structure['directories'])}")

    if missing_files:
        print(f"❌ 缺失根目录文件: {len(missing_files)}")
        for file in missing_files:
            print(f"   - {file}")

    if missing_dir_files:
        print(f"❌ 缺失目录文件: {len(missing_dir_files)}")
        for file in missing_dir_files[:10]:  # 只显示前10个
            print(f"   - {file}")
        if len(missing_dir_files) > 10:
            print(f"   ... 还有 {len(missing_dir_files) - 10} 个文件")

    # 检查关键文件内容
    print("\n检查关键文件:")
    key_files = ['app.py', 'config/settings.py', 'ui/login_window.py']
    for file_name in key_files:
        file_path = project_root / file_name
        if file_path.exists():
            try:
                content = file_path.read_text(encoding='utf-8')
                if len(content) > 100:  # 文件有实际内容
                    print(f"✅ {file_name} (有内容)")
                else:
                    print(f"⚠️  {file_name} (内容较少)")
            except Exception as e:
                print(f"❌ {file_name} (读取失败: {e})")
        else:
            print(f"❌ {file_name} (不存在)")

    print("\n" + "=" * 50)
    print("项目结构检查完成!")

    if not missing_files and not missing_dirs and not missing_dir_files:
        print("🎉 项目结构完整!")
        return True
    else:
        print("⚠️  项目结构不完整，但程序仍可运行")
        return False


def create_missing_core_files():
    """创建缺失的核心文件"""
    print("\n创建缺失的核心文件:")

    project_root = Path(__file__).parent

    # 创建基础的核心文件
    core_files = {
        'core/__init__.py': '"""核心功能模块"""\n',
        'core/utils.py': '''"""工具函数模块"""

def get_mac_address():
    """获取MAC地址"""
    import uuid
    return ':'.join(['{:02x}'.format((uuid.getnode() >> ele) & 0xff) 
                     for ele in range(0,8*6,8)][::-1])

def format_phone_number(phone):
    """格式化手机号"""
    phone = str(phone).strip()
    if len(phone) == 11 and phone.startswith('1'):
        return phone
    return None

def validate_sms_content(content):
    """验证短信内容"""
    if not content or len(content.strip()) == 0:
        return False, "内容不能为空"
    if len(content) > 500:
        return False, "内容过长"
    return True, "内容有效"
''',
        'tests/test_basic.py': '''"""基础功能测试"""

import unittest
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class TestBasic(unittest.TestCase):
    """基础测试类"""

    def test_import_modules(self):
        """测试模块导入"""
        try:
            import config.settings
            import ui.login_window
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"模块导入失败: {e}")

if __name__ == '__main__':
    unittest.main()
'''
    }

    for file_path, content in core_files.items():
        full_path = project_root / file_path
        if not full_path.exists():
            try:
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(content, encoding='utf-8')
                print(f"✅ 创建: {file_path}")
            except Exception as e:
                print(f"❌ 创建失败 {file_path}: {e}")


def main():
    """主函数"""
    try:
        # 检查项目结构
        is_complete = check_project_structure()

        # 创建缺失的核心文件
        create_missing_core_files()

        print("\n" + "=" * 50)
        if is_complete:
            print("🚀 项目准备就绪! 可以运行: python app.py")
        else:
            print("⚠️  项目结构不完整，但仍可尝试运行: python app.py")
            print("💡 建议先运行: python test_startup.py")

        print("\n测试账号:")
        print("用户名: test_user")
        print("密码: 123456")

    except Exception as e:
        print(f"检查过程出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()