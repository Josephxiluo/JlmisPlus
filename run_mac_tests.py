#Mac开发专用测试运行器
import os
import sys
import subprocess
import threading
import time
from pathlib import Path


class MacTestRunner:
    def __init__(self):
        self.simulator_process = None
        self.test_results = []

    def setup_environment(self):
        """设置Mac测试环境"""
        print("🍎 设置Mac测试环境...")

        # 确保使用Mac配置
        if Path('.env.mac').exists():
            import shutil
            shutil.copy('.env.mac', '.env')
            print("✅ 已切换到Mac开发配置")

        # 创建必要目录
        directories = [
            'tests/mock', 'temp/test_data', 'temp/mock_ports',
            'temp/uploads/test', 'temp/exports/test', 'temp/logs'
        ]

        for dir_path in directories:
            Path(dir_path).mkdir(parents=True, exist_ok=True)

        print("✅ 测试目录创建完成")

    def start_simulator(self):
        """启动Mac串口模拟器"""
        print("🚀 启动串口模拟器...")

        try:
            # 在后台启动模拟器
            self.simulator_process = subprocess.Popen([
                sys.executable, 'tests/mac_serial_simulator.py'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # 等待模拟器启动
            time.sleep(2)

            if self.simulator_process.poll() is None:
                print("✅ 串口模拟器启动成功")
                return True
            else:
                print("❌ 串口模拟器启动失败")
                return False

        except Exception as e:
            print(f"❌ 启动模拟器时出错: {e}")
            return False

    def run_test_batch(self, batch_name: str, test_files: list):
        """运行测试批次"""
        print(f"\n🧪 运行测试批次: {batch_name}")
        print("=" * 50)

        batch_results = []

        for test_file in test_files:
            if Path(test_file).exists():
                print(f"▶️  运行: {test_file}")

                try:
                    result = subprocess.run([
                        sys.executable, '-m', 'pytest', test_file, '-v'
                    ], capture_output=True, text=True, timeout=60)

                    success = result.returncode == 0
                    batch_results.append({
                        'file': test_file,
                        'success': success,
                        'output': result.stdout,
                        'error': result.stderr
                    })

                    status = "✅ 通过" if success else "❌ 失败"
                    print(f"   {status}: {test_file}")

                    if not success:
                        print(f"   错误: {result.stderr[:200]}")

                except subprocess.TimeoutExpired:
                    batch_results.append({
                        'file': test_file,
                        'success': False,
                        'output': '',
                        'error': 'Test timeout'
                    })
                    print(f"   ⏰ 超时: {test_file}")

            else:
                print(f"   ⚠️  文件不存在: {test_file}")
                batch_results.append({
                    'file': test_file,
                    'success': False,
                    'output': '',
                    'error': 'File not found'
                })

        self.test_results.append({
            'batch': batch_name,
            'results': batch_results
        })

        # 批次结果统计
        total = len(batch_results)
        passed = sum(1 for r in batch_results if r['success'])
        print(f"\n📊 {batch_name} 结果: {passed}/{total} 通过")

        return passed == total

    def generate_report(self):
        """生成测试报告"""
        print("\n📋 生成测试报告...")

        report_lines = [
            "# Mac开发环境测试报告",
            f"生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"平台: macOS ({os.uname().machine})",
            ""
        ]

        total_tests = 0
        total_passed = 0

        for batch in self.test_results:
            batch_name = batch['batch']
            batch_results = batch['results']

            batch_total = len(batch_results)
            batch_passed = sum(1 for r in batch_results if r['success'])

            total_tests += batch_total
            total_passed += batch_passed

            report_lines.extend([
                f"## {batch_name}",
                f"通过率: {batch_passed}/{batch_total} ({batch_passed / batch_total * 100:.1f}%)",
                ""
            ])

            for result in batch_results:
                status = "✅" if result['success'] else "❌"
                report_lines.append(f"- {status} {result['file']}")

                if not result['success'] and result['error']:
                    report_lines.append(f"  错误: {result['error'][:100]}...")

            report_lines.append("")

        # 总体统计
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        report_lines.insert(4, f"总体通过率: {total_passed}/{total_tests} ({success_rate:.1f}%)")
        report_lines.insert(5, "")

        # 保存报告
        report_content = '\n'.join(report_lines)
        report_file = f"temp/logs/mac_test_report_{int(time.time())}.md"

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)

        print(f"📄 测试报告已保存: {report_file}")
        return report_file

    def cleanup(self):
        """清理资源"""
        if self.simulator_process:
            print("🛑 停止模拟器...")
            self.simulator_process.terminate()
            self.simulator_process.wait()

    def run_all_tests(self):
        """运行完整测试流程"""
        print("🍎 Mac开发环境完整测试开始")
        print("=" * 60)

        try:
            # 1. 设置环境
            self.setup_environment()

            # 2. 启动模拟器
            if not self.start_simulator():
                return False

            # 3. 运行测试批次
            test_batches = [
                ("基础环境", [
                    "tests/test_database.py",
                    "tests/test_config.py",
                    "tests/test_logging.py"
                ]),
                ("平台适配", [
                    "tests/test_mac_platform.py",
                    "tests/test_port_scanner.py"
                ]),
                ("用户认证", [
                    "tests/test_auth_service.py",
                    "tests/test_user_model.py"
                ]),
                ("界面框架", [
                    "tests/test_main_window.py",
                    "tests/test_ui_components.py"
                ]),
                ("任务管理", [
                    "tests/test_task_service.py",
                    "tests/test_task_model.py"
                ])
            ]

            overall_success = True

            for batch_name, test_files in test_batches:
                batch_success = self.run_test_batch(batch_name, test_files)
                overall_success &= batch_success

            # 4. 生成报告
            report_file = self.generate_report()

            # 5. 显示最终结果
            print("\n🎉 Mac开发环境测试完成!")
            status = "✅ 成功" if overall_success else "❌ 有失败项"
            print(f"总体状态: {status}")
            print(f"详细报告: {report_file}")

            return overall_success

        finally:
            self.cleanup()


if __name__ == '__main__':
    runner = MacTestRunner()
    success = runner.run_all_tests()
    sys.exit(0 if success else 1)