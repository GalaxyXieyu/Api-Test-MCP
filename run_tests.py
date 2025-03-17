# @time:    2024-08-16
# @author:  xiaoqq

import os
import pytest
from utils.config_manager import ConfigManager
from utils.log_manager import logger
from utils.globals import Globals
from utils.log_manager import log
from utils.dingtalk_handler import DingTalkHandler
from utils.report_generator import ReportGenerator
from utils.project_login_handler import ProjectLoginHandler

def execute_test_cases(testcases, env, report_type):
    """
    根据传入的 testcases 参数执行指定的测试用例
    :param testcases: 测试用例路径列表（目录或文件）
    :param env: 环境名称
    """
    config_manager = ConfigManager()
    login_handler = ProjectLoginHandler()
    projects_config = {}

    # 当前执行环境存入全局变量
    Globals.set('env', env)

    # 遍历所有测试用例路径
    for testcase_path in testcases:
        if os.path.isdir(testcase_path):
            project_name = get_project_name_from_path(testcase_path)
            project_env_config = config_manager.get_project_env_config(project_name, env)
            if project_env_config is not None:
                projects_config.update(project_env_config)
            else:
                log.warning(f"{project_name} 的配置未找到，跳过该项目。")
        elif os.path.isfile(testcase_path):
            project_name = get_project_name_from_path(os.path.dirname(testcase_path))
            project_env_config = config_manager.get_project_env_config(project_name, env)
            if project_env_config is not None:
                projects_config.update(project_env_config)
            else:
                log.warning(f"{project_name} 的配置未找到，跳过该项目。")

    # 判断项目是否需要登录获取token，需要则登录获取token存入全局变量
    for project_name, project_config in projects_config.items():
        project_env_config = config_manager.get_project_env_config(project_name, env)
        token = login_handler.login_if_needed(project_name, project_env_config.get(project_name), env)
        if token:
            # 将 token 存入全局变量
            Globals.update(project_name, "token", token)

    log.info(f"工程配置信息更新：{Globals.get_data()}")

    # 测试报告处理，根据 report 类型准备报告目录和文件
    report_generator = ReportGenerator(report_type, env)
    if report_type == 'allure':
        report_generator.prepare_allure_report()
        pytest_args = [f'--alluredir={report_generator.allure_results_dir}']
    elif report_type == 'pytest-html':
        report_generator.prepare_pytest_html_report()
        pytest_args = [f'--html={report_generator.html_report_path}', '--self-contained-html']
    else:
        pytest_args = []

    for testcase_path in testcases:
        pytest_args.append(testcase_path)

    try:
        pytest.main(pytest_args)
        logger.info(f"所有测试用例执行完成。")
    except Exception as e:
        logger.error(f"执行所有测试用例时出错: {str(e)}")

    if report_type == 'allure':
        report_generator.generate_allure_report()

def get_project_name_from_path(path):
    """
    根据路径获取项目名称
    :param path: 路径字符串
    :return: 项目名称
    """
    parts = os.path.normpath(path).split(os.sep)
    # 确保有足够的部分返回项目名称
    if len(parts) > 1:
        return parts[1]
    elif len(parts) == 1:
        return parts[0]
    return None

def run_tests(testcases=None, env=None, report_type=None):
    """
    主运行函数，执行指定的测试用例
    :param testcases: 测试用例路径列表（目录或文件），默认为 None 则执行所有
    :param env: 执行环境，可选参数，默认为 None 则执行 test 环境
    :param report: 报告类型（allure 或 pytest-html），默认为 pytest-html
    """
    if testcases is None:
        # 获取所有嵌套的测试用例路径
        testcases = [os.path.join(root, file)
                     for root, dirs, files in os.walk('test_cases')
                     for file in files if file.endswith('.py')]
    elif testcases == ['test_cases/']:
        # 当指定为 test_cases/ 时，获取该目录下所有的子文件夹
        testcases = [os.path.join('test_cases', d)
                     for d in os.listdir('test_cases')
                     if os.path.isdir(os.path.join('test_cases', d))]
        
    if env is None:
        env = 'pre'
        
    if report_type is None:
        report_type = 'pytest-html'

    execute_test_cases(testcases, env, report_type)
    
    results = Globals.get('test_results')
    webhook = Globals.get('dingtalk').get('webhook')
    secret = Globals.get('dingtalk').get('secret')
    DingTalkHandler(webhook, secret).send_markdown_msg(
        conclusion=results['conclusion'],
        total=results['total'],
        passed=results['passed'],
        failed=results['failed'],
        error=results['error'],
        skipped=results['skipped'],
        start_time=results['start_time'],
        duration=results['duration']
    )


if __name__ == '__main__':
    # report_type 可以为allure、pytest-html，默认pytest-html
    run_tests(testcases=['test_cases/'], env='pre', report_type='allure')