# @time:    2024-09-10
# @author:  xiaoqq

import time
from datetime import datetime
from utils.config_manager import Globals

def pytest_terminal_summary(terminalreporter, exitstatus, config):
    '''
    获取用例执行结果，并发送钉钉消息
    :param terminalreporter:
    :param exitstatus:
    :param config:
    :return:
    '''
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

    # 将测试结果保存到全局变量 Globals 以供 `run_tests.py` 使用
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