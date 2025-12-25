# @time:    2024-09-10
# @author:  xiaoqq

import time
from datetime import datetime
from atf.core.globals import Globals
import pytest


# ==================== pytest-html 报告配置 ====================

def pytest_configure(config):
    """配置 pytest-html 元数据"""
    config._metadata = getattr(config, '_metadata', {}) or {}
    config._metadata["项目"] = "API Auto Test Framework"
    config._metadata["框架"] = "pytest + pytest-html"


def pytest_html_report_title(report):
    """设置报告标题"""
    report.title = "API 自动化测试报告"


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """为测试结果添加描述信息"""
    outcome = yield
    report = outcome.get_result()
    report.description = str(item.function.__doc__ or "")


# ==================== 测试结果收集 ====================

def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """
    获取用例执行结果，保存到全局变量
    """
    total = terminalreporter._numcollected
    passed = len([i for i in terminalreporter.stats.get("passed", []) if i.when != "teardown"])
    failed = len([i for i in terminalreporter.stats.get("failed", []) if i.when != "teardown"])
    error = len([i for i in terminalreporter.stats.get("error", []) if i.when != "teardown"])
    skipped = len([i for i in terminalreporter.stats.get("skipped", []) if i.when != "teardown"])
    _start_time = terminalreporter._sessionstarttime
    start_time = datetime.utcfromtimestamp(_start_time).strftime("%Y-%m-%d %H:%M:%S")
    duration = time.time() - _start_time

    conclusion = "执行通过"
    if failed and error:
        conclusion = "执行失败，包含失败用例和错误用例！"
    elif failed and not error:
        conclusion = "执行失败，包含失败用例！"
    elif not failed and error:
        conclusion = "执行失败，包含报错用例！"

    results = {
        "conclusion": conclusion,
        "total": total,
        "passed": passed,
        "failed": failed,
        "error": error,
        "skipped": skipped,
        "start_time": start_time,
        "duration": duration
    }
    Globals.set('test_results', results)
