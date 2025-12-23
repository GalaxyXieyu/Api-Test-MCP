# @time:    2024-09-14
# @author:  xiaoqq

import subprocess
import os
import shutil
import json
import platform
from datetime import datetime
from atf.core.log_manager import log


class ReportGenerator:
    """
    测试报告生成器，支持生成 Allure 报告和 pytest-html 报告。
    """

    def __init__(self, report_type, env):
        """
        初始化 ReportGenerator 实例，设置报告类型和测试环境。

        :param report_type: 报告类型 ('allure' 或 'html')
        :param env: 测试环境名称
        """
        self.report_type = report_type
        self.env = env
        self.day_timestamp = datetime.now().strftime('%Y%m%d')
        self.sec_timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        self.reports_dir = os.path.join('html-reports', f'{self.day_timestamp}')
        os.makedirs(self.reports_dir, exist_ok=True)

        # 定义测试结果数据目录和历史数据目录
        self.allure_results_dir = os.path.join('html-reports', 'allure-results')
        self.allure_history_dir = os.path.join('html-reports', 'allure-history')
        os.makedirs(self.allure_results_dir, exist_ok=True)
        os.makedirs(self.allure_history_dir, exist_ok=True)
        self.allure_report_dir = None
        self.html_report_path = None

    def prepare_report(self):
        """
        准备生成报告的环境，根据报告类型调用相应的准备方法。
        """
        if self.report_type == 'allure':
            self.prepare_allure_report()
        elif self.report_type == 'html':
            self.prepare_pytest_html_report()
        else:
            raise ValueError(f"不支持的报告类型: {self.report_type}")

    def prepare_allure_report(self):
        """
        准备 Allure 报告所需的目录和文件。
        """
        self.allure_report_dir = os.path.join(self.reports_dir, f'report_{self.sec_timestamp}_allure')
        os.makedirs(self.allure_report_dir, exist_ok=True)
        self.clean_allure_results()
        self.write_environment_file()
        self.write_executor_file()
        self.write_categories_file()

    def prepare_pytest_html_report(self):
        """
        准备 pytest-html 报告的路径。
        """
        self.html_report_path = os.path.join(self.reports_dir, f'report_{self.sec_timestamp}.html')

    def clean_allure_results(self):
        """
        清除旧的 Allure 测试结果数据。
        """
        for filename in os.listdir(self.allure_results_dir):
            file_path = os.path.join(self.allure_results_dir, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                log.error(f'删除文件 {file_path} 时出错: {e}')

    def write_environment_file(self):
        """
        生成 environment.properties 文件，用于 Allure 报告中显示环境信息。
        """
        environment_file = os.path.join(self.allure_results_dir, 'environment.properties')
        with open(environment_file, 'w') as f:
            f.write(f"Environment={self.env}\n")
            f.write(f"PythonVersion={platform.python_version()}\n")
            f.write(f"Platform={platform.system()}\n")
            f.write(f"PlatformVersion={platform.version()}\n")

    def write_executor_file(self):
        """
        生成 executor.json 文件。
        """
        executor_file = os.path.join(self.allure_results_dir, 'executor.json')
        executor_info = {
            "name": "Local Machine",  # 或者是 Jenkins、GitLab CI 等
            "type": "local",  # 本地执行，或者是 Jenkins 等工具
            "reportName": "Allure Report",
            "buildUrl": "http://localhost:8080",  # 如果有 CI/CD 工具，可以填写其 URL
            "buildId": "12345",  # 如果有 Jenkins 之类的，填写 Build ID
            "reportUrl": "http://localhost:8080/allure-report"  # 报告 URL
        }
        with open(executor_file, 'w') as f:
            json.dump(executor_info, f, indent=4)

    def write_categories_file(self):
        """
        生成 categories.json 文件。
        """
        categories_file = os.path.join(self.allure_results_dir, 'categories.json')
        categories = [
            {"name": "Test Failures", "matchedStatuses": ["failed"]},
            {"name": "Broken Tests", "matchedStatuses": ["broken"]},
            {"name": "Skipped Tests", "matchedStatuses": ["skipped"]}
        ]
        with open(categories_file, 'w') as f:
            json.dump(categories, f, indent=4)

    def copytree(self, src, dst):
        """
        兼容旧版本的 shutil.copytree 方法，不使用 dirs_exist_ok 参数。
        :param src: 源目录
        :param dst: 目标目录
        """
        if os.path.exists(dst):
            shutil.rmtree(dst)  # 如果目标目录存在，先删除
        shutil.copytree(src, dst)  # 复制源目录到目标

    def generate_allure_report(self):
        """
        生成 Allure HTML 报告。
        """
        log.info(f'正在生成 Allure 测试报告......')
        allure_exe = r'D:\download-dir\allure-2.30.0\allure-2.30.0\bin\allure.bat'
        html_report = os.path.join(self.allure_report_dir, 'html')

        # 如果历史数据存在，则拷贝历史数据到结果目录
        history_dir = os.path.join(self.allure_results_dir, 'history')
        if os.path.exists(os.path.join(self.allure_history_dir, 'history')):
            self.copytree(os.path.join(self.allure_history_dir, 'history'), history_dir)

        # 生成 Allure 报告
        subprocess.run([allure_exe, 'generate', self.allure_results_dir, '-o', html_report, '--clean'], check=True)

        # 复制生成后的历史数据
        generated_history_dir = os.path.join(html_report, 'history')
        if os.path.exists(generated_history_dir):
            self.copytree(generated_history_dir, os.path.join(self.allure_history_dir, 'history'))

        log.info(f"生成的报告位于: {html_report}")

    # def generate_pytest_html_report(self):
    #     """
    #     生成 pytest-html 报告。
    #     """
    #     log.info(f'正在生成 pytest-html 测试报告......')
    #     # 生成 pytest-html 报告的具体实现逻辑，省略...