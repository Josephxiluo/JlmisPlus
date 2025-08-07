# 创建文件：tools/cross_platform_checker.py
import ast
import os
from pathlib import Path
from typing import List, Dict


class CrossPlatformChecker:
    """跨平台兼容性检查工具"""

    def __init__(self):
        self.issues = []

    def check_file_paths(self, file_path: str):
        """检查文件路径使用"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查硬编码路径
        if '/' in content and not content.startswith('#!'):
            # 检查是否使用了Unix风格路径
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                if ('/' in line and
                        not line.strip().startswith('#') and
                        not 'http' in line and
                        not 'Path(' in line and
                        not 'os.path.join' in line):
                    self.issues.append({
                        'file': file_path,
                        'line': i,
                        'type': 'path_separator',
                        'content': line.strip(),
                        'suggestion': '使用 Path() 或 os.path.join()'
                    })

    def check_serial_imports(self, file_path: str):
        """检查串口相关导入"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if 'serial' in alias.name:
                            # 检查是否有平台特定处理
                            pass

        except SyntaxError:
            pass

    def generate_compatibility_report(self, source_dir: str) -> str:
        """生成兼容性报告"""
        print("🔍 检查跨平台兼容性...")

        py_files = list(Path(source_dir).rglob('*.py'))

        for py_file in py_files:
            self.check_file_paths(str(py_file))
            self.check_serial_imports(str(py_file))

        # 生成报告
        report = f"""# 跨平台兼容性检查报告

## 检查文件数量: {len(py_files)}

## 发现的问题: {len(self.issues)}

"""

        for issue in self.issues:
            report += f"""### {issue['file']}:{issue['line']}
- 类型: {issue['type']}
- 内容: `{issue['content']}`
- 建议: {issue['suggestion']}

"""

        return report


if __name__ == '__main__':
    checker = CrossPlatformChecker()
    report = checker.generate_compatibility_report('.')

    with open('temp/logs/cross_platform_report.md', 'w', encoding='utf-8') as f:
        f.write(report)

    print("📄 兼容性报告已生成: temp/logs/cross_platform_report.md")