"""
Test Executor
测试执行逻辑
"""

import os
import shutil
import subprocess
import sys
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from atf.core.log_manager import log
from atf.mcp.models import (
    AssertionResultModel,
    TestResultModel,
)
from atf.mcp.utils import (
    PYTEST_TIMEOUT,
    MAX_ERROR_LENGTH,
    MAX_HISTORY_SIZE,
    get_roots,
    resolve_yaml_path,
    expected_py_path,
    load_yaml_file,
    parse_testcase_input,
    parse_unittest_input,
    detect_testcase_type,
    truncate_text,
)


# 测试执行结果存储（内存中）
_test_execution_history: list[dict] = []
_history_lock = threading.Lock()


def get_python_path(repo_root: Path) -> str:
    """
    获取项目可用的 Python 解释器路径。

    优先级顺序:
    1. uv run (当项目包含 pyproject.toml 且 uv 可用时)
    2. .venv/bin/python (venv 虚拟环境)
    3. .conda/bin/python (conda 虚拟环境)
    4. sys.executable (系统 Python 解释器作为回退)

    Args:
        repo_root: 项目根目录路径

    Returns:
        str: Python 解释器路径或 'uv' 命令字串
    """
    # 优先使用 uv run (需要 pyproject.toml 且 uv 可用)
    if (repo_root / "pyproject.toml").exists():
        uv_path = shutil.which("uv")
        if uv_path:
            log.info(f"使用 uv 运行测试")
            return "uv"
        log.warning("pyproject.toml 存在但 uv 未安装，回退到其他 Python 解释器")

    # 查找 venv 路径（检查 .venv 和 venv 两种常见命名）
    venv_paths = [
        repo_root / ".venv" / "bin" / "python",
        repo_root / "venv" / "bin" / "python",
    ]
    for venv_python in venv_paths:
        if venv_python.exists() and os.access(venv_python, os.X_OK):
            log.info(f"使用 venv Python: {venv_python}")
            return str(venv_python)

    # Conda 环境检测（检查 .conda 和 conda 两种常见命名）
    conda_paths = [
        repo_root / ".conda" / "bin" / "python",
        repo_root / "conda" / "bin" / "python",
    ]
    for conda_python in conda_paths:
        if conda_python.exists() and os.access(conda_python, os.X_OK):
            log.info(f"使用 conda Python: {conda_python}")
            return str(conda_python)

    # 回退到系统 Python
    log.warning(f"未找到项目 Python 解释器，回退到系统 Python: {sys.executable}")
    return sys.executable


def run_pytest(pytest_path: str, repo_root: Path, python_path: str | None = None) -> dict:
    """执行 pytest 并返回结果

    Args:
        pytest_path: pytest 文件路径
        repo_root: 项目根目录
        python_path: 可选的 Python 解释器路径，如果不指定则自动检测
    """
    start_time = time.time()
    result_data = {
        "test_name": "",
        "status": "error",
        "duration": 0.0,
        "assertions": [],
        "error_message": None,
        "traceback": None,
    }

    try:
        # 如果指定了 Python 路径则使用它，否则自动检测
        if python_path:
            log.info(f"使用指定的 Python: {python_path}")
        else:
            python_path = get_python_path(repo_root)

        # 构建 pytest 命令
        if python_path == "uv":
            cmd = ["uv", "run", "pytest", pytest_path, "-v", "--tb=short", "-q"]
        else:
            cmd = [python_path, "-m", "pytest", pytest_path, "-v", "--tb=short", "-q"]

        log.info(f"执行测试命令: {' '.join(cmd)}")

        process = subprocess.Popen(
            cmd,
            cwd=str(repo_root),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            stdout, stderr = process.communicate(timeout=PYTEST_TIMEOUT)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            result_data["error_message"] = "测试执行超时（超过5分钟）"
            result_data["traceback"] = "进程被强制终止"
            end_time = time.time()
            result_data["duration"] = round(end_time - start_time, 2)
            return result_data
        finally:
            # 确保进程已终止并清理资源
            if process.returncode is None:
                process.kill()
            process.wait()
            if process.stdout:
                process.stdout.close()
            if process.stderr:
                process.stderr.close()

        end_time = time.time()
        duration = round(end_time - start_time, 2)

        # 从路径提取测试名称
        test_name = Path(pytest_path).stem.replace("test_", "")

        result_data["test_name"] = test_name
        result_data["duration"] = duration

        # 解析测试结果
        if process.returncode == 0:
            result_data["status"] = "passed"
        else:
            result_data["status"] = "failed"
            # 提取错误信息（使用常量截断）
            result_data["error_message"] = truncate_text(stderr)
            result_data["traceback"] = truncate_text(stdout)

            # 尝试解析断言失败信息
            if "FAILED" in stdout or "AssertionError" in stderr:
                result_data["assertions"] = [
                    AssertionResultModel(
                        assertion_type="unknown",
                        passed=False,
                        message=f"测试失败，返回码: {process.returncode}"
                    ).model_dump()
                ]

        # 尝试从 stdout 提取统计信息
        if "passed" in stdout.lower() or "failed" in stdout.lower():
            # 简化处理：创建一个通用的断言结果
            result_data["assertions"] = [
                AssertionResultModel(
                    assertion_type="execution",
                    passed=process.returncode == 0,
                    message=stdout.strip()[-200:] if stdout else "执行完成"
                ).model_dump()
            ]

    except Exception as exc:
        result_data["error_message"] = str(exc)
        log.error(f"执行 pytest 失败: {exc}")

    return result_data


def execute_single_test(yaml_path: str, repo_root: Path, python_path: str | None = None) -> TestResultModel:
    """执行单个测试用例并返回结果

    Args:
        yaml_path: YAML 文件路径
        repo_root: 项目根目录
        python_path: 可选的 Python 解释器路径
    """
    try:
        # 必须传递 workspace 参数，确保路径解析正确
        workspace = str(repo_root)
        yaml_full_path, yaml_relative_path, _ = resolve_yaml_path(yaml_path, workspace)

        log.info(f"[execute_single_test] yaml_path={yaml_path}, workspace={workspace}")
        log.info(f"[execute_single_test] yaml_full_path={yaml_full_path}")

        data = load_yaml_file(yaml_full_path)

        # 使用统一的类型检测函数
        testcase_type = detect_testcase_type(data)

        # 解析测试用例
        if testcase_type == "unittest":
            testcase_model = parse_unittest_input(data)
        else:
            testcase_model = parse_testcase_input(data)
        test_name = testcase_model.name

        py_full_path, _ = expected_py_path(yaml_full_path, test_name, workspace)
        log.info(f"[execute_single_test] py_full_path={py_full_path}")

        if not py_full_path.exists():
            return TestResultModel(
                test_name=test_name,
                status="error",
                duration=0.0,
                assertions=[],
                error_message="pytest 文件不存在，请先生成",
            )

        # 执行测试（传入自定义 Python 路径）
        result_data = run_pytest(str(py_full_path), repo_root, python_path)

        return TestResultModel(
            test_name=result_data["test_name"],
            status=result_data["status"],
            duration=result_data["duration"],
            assertions=[
                AssertionResultModel(**a) for a in result_data.get("assertions", [])
            ],
            error_message=result_data.get("error_message"),
            traceback=result_data.get("traceback"),
        )
    except Exception as exc:
        log.error(f"执行单个测试失败: {exc}")
        return TestResultModel(
            test_name=Path(yaml_path).stem,
            status="error",
            duration=0.0,
            assertions=[],
            error_message=str(exc),
        )


def save_to_history(
    run_id: str,
    total: int,
    passed: int,
    failed: int,
    skipped: int,
    duration: float,
    test_names: list[str],
) -> None:
    """保存执行结果到历史记录"""
    global _test_execution_history
    with _history_lock:
        _test_execution_history.append({
            "run_id": run_id,
            "timestamp": datetime.now().isoformat(),
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "duration": duration,
            "test_names": test_names,
        })
        # 使用常量添加容量限制，防止内存溢出
        if len(_test_execution_history) > MAX_HISTORY_SIZE:
            _test_execution_history = _test_execution_history[-MAX_HISTORY_SIZE:]


def get_history(limit: int = 10) -> list[dict]:
    """获取历史记录"""
    global _test_execution_history
    with _history_lock:
        return _test_execution_history[-limit:] if limit > 0 else _test_execution_history


__all__ = [
    "get_python_path",
    "run_pytest",
    "execute_single_test",
    "save_to_history",
    "get_history",
]
