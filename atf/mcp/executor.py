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

# api-auto-test 包的安装目录（用于获取依赖列表）
_ATF_ROOT = Path(__file__).parent.parent.parent.parent


def _check_allure_available() -> bool:
    """检查 allure 命令是否可用"""
    return shutil.which("allure") is not None


def _install_allure() -> bool:
    """安装 allure 命令行工具"""
    log.info("正在安装 Allure 命令行工具...")

    # 尝试通过 npm 安装
    npm_path = shutil.which("npm")
    if npm_path:
        result = subprocess.run(
            [npm_path, "install", "-g", "allure-commandline"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            log.info("✅ Allure 安装成功（npm）")
            return True
        log.warning(f"Allure npm 安装失败: {result.stderr}")

    # 尝试通过 pip 安装
    python_path = sys.executable
    result = subprocess.run(
        [python_path, "-m", "pip", "install", "allure-pytest"],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode == 0:
        log.info("✅ Allure 安装成功（pip）")
        return True
    log.warning(f"Allure pip 安装失败: {result.stderr}")

    return False


def _ensure_allure_available() -> bool:
    """确保 allure 可用，不存在则自动安装

    Returns:
        bool: allure 是否可用
    """
    # 先检查 Java 是否可用（Allure 需要 Java）
    try:
        subprocess.run(["java", "-version"], capture_output=True, text=True, timeout=10)
    except FileNotFoundError:
        log.warning("⚠️ Java 未安装，Allure 报告需要 Java 运行环境")
        log.info("💡 安装方式: brew install openjdk@11 或 brew install openjdk")
        return False

    if _check_allure_available():
        return True
    log.warning("Allure 命令未找到，尝试自动安装...")
    return _install_allure()


def _check_python_has_dependencies(python_path: str, required_modules: list[str]) -> tuple[bool, list[str]]:
    """检查 Python 环境是否包含必要的依赖模块

    Args:
        python_path: Python 解释器路径
        required_modules: 需要检查的模块列表

    Returns:
        (是否全部存在, 缺失的模块列表)
    """
    missing = []
    for module in required_modules:
        result = subprocess.run(
            [python_path, "-c", f"import {module}"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            missing.append(module)
    return len(missing) == 0, missing


def _load_required_modules_from_requirements() -> list[str]:
    """返回需要检测的模块列表（写死配置）

    Returns:
        list[str]: 需要检测的模块名列表
    """
    # 直接定义需要检测的模块（运行测试脚本需要的基础依赖）
    # 注意：urllib3<2.0 因为 macOS 系统 Python 使用 LibreSSL，不兼容 v2 的 OpenSSL 要求
    return ["loguru", "yaml", "requests", "urllib3", "pytest", "mysql", "Crypto"]


def _install_missing_dependencies(python_path: str, missing_modules: list[str]) -> bool:
    """为指定的 Python 环境安装缺失的依赖

    Args:
        python_path: Python 解释器路径
        missing_modules: 缺失的模块列表

    Returns:
        bool: 安装是否成功
    """
    if not missing_modules:
        return True

    log.info(f"正在为 {python_path} 安装缺失依赖: {missing_modules}")

    # 包名到模块名的映射
    module_to_package = {
        "atf": "-e /Volumes/DATABASE/code/api-auto-test",
        "loguru": "loguru",
        "yaml": "pyyaml",
        "requests": "requests",
        "urllib3": "urllib3<2",  # urllib3 v2 需要 OpenSSL 1.1.1+，macOS 使用 LibreSSL 不兼容
        "pytest": "pytest",
        "allure_python_commons": "allure-python-commons",
        "mysql": "mysql-connector-python",
        "crypto": "pycryptodome",
        "pytest_html": "pytest-html",
        "dingtalkchatbot": "DingtalkChatbot",
    }

    # 映射模块名到包名
    packages = []
    for module in missing_modules:
        if module in module_to_package:
            packages.append(module_to_package[module])
        else:
            packages.append(module)

    if not packages:
        return True

    try:
        # 优先升级 pip 以支持现代安装方式
        log.info("升级 pip 以支持现代安装...")
        result = subprocess.run(
            [python_path, "-m", "pip", "install", "--upgrade", "pip"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            log.warning(f"pip 升级失败，继续尝试安装: {result.stderr}")

        # 安装依赖
        result = subprocess.run(
            [python_path, "-m", "pip", "install"] + packages,
            capture_output=True,
            text=True,
            timeout=180,
        )
        if result.returncode == 0:
            log.info(f"✅ 依赖安装成功: {packages}")
            return True
        else:
            log.warning(f"❌ 依赖安装失败: {result.stderr}")
            return False
    except Exception as exc:
        log.warning(f"安装依赖时出错: {exc}")
        return False


def get_python_path(repo_root: Path) -> str:
    """
    获取项目可用的 Python 解释器路径。

    优先级顺序:
    1. 检测项目 venv 依赖，缺失则自动安装到项目 venv
    2. 使用项目自身的 venv
    3. uv run (当项目包含 pyproject.toml 且 uv 可用时)
    4. 系统 Python 解释器作为回退

    Args:
        repo_root: 项目根目录路径

    Returns:
        str: Python 解释器路径
    """
    # 从 api-auto-test/requirements.txt 读取需要检测的依赖
    required_modules = _load_required_modules_from_requirements()

    # 查找项目 venv
    venv_paths = [
        repo_root / ".venv" / "bin" / "python",
        repo_root / "venv" / "bin" / "python",
    ]
    conda_paths = [
        repo_root / ".conda" / "bin" / "python",
        repo_root / "conda" / "bin" / "python",
    ]
    project_pythons = [p for p in venv_paths + conda_paths if p.exists() and os.access(p, os.X_OK)]

    # api-auto-test 的 venv（包含 atf 包）
    api_auto_test_venv = _ATF_ROOT / ".venv" / "bin" / "python"

    # 优先尝试项目自身的 venv
    for venv_python in project_pythons:
        has_deps, missing = _check_python_has_dependencies(str(venv_python), required_modules)
        if has_deps:
            log.info(f"使用项目 venv: {venv_python}")
            return str(venv_python)
        else:
            log.warning(f"项目 venv 缺少依赖: {missing}，正在自动安装...")
            # 自动安装缺失的依赖到项目 venv
            if _install_missing_dependencies(str(venv_python), missing):
                # 再次验证
                has_deps, _ = _check_python_has_dependencies(str(venv_python), required_modules)
                if has_deps:
                    log.info(f"✅ 依赖安装成功，使用项目 venv: {venv_python}")
                    return str(venv_python)

            # 如果安装失败，继续使用项目 venv（至少其他项目依赖可用）
            log.warning(f"⚠️ 部分依赖安装失败，继续使用项目 venv: {venv_python}")
            return str(venv_python)

    # 检查 api-auto-test 的 venv 是否可用（当项目没有 venv 时）
    if api_auto_test_venv.exists() and os.access(api_auto_test_venv, os.X_OK):
        has_deps, _ = _check_python_has_dependencies(str(api_auto_test_venv), required_modules)
        if has_deps:
            log.info(f"项目无 venv，使用 api-auto-test venv: {api_auto_test_venv}")
            return str(api_auto_test_venv)

    # 优先使用 uv run (需要 pyproject.toml 且 uv 可用时)
    if (repo_root / "pyproject.toml").exists():
        uv_path = shutil.which("uv")
        if uv_path:
            log.info(f"使用 uv 运行测试")
            return "uv"
        log.warning("pyproject.toml 存在但 uv 未安装")

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

        # 检查项目 venv 是否包含 atf 模块
        env = os.environ.copy()
        if python_path != "uv":
            has_atf, _ = _check_python_has_dependencies(python_path, ["atf"])
            if not has_atf:
                # 添加 api-auto-test 到 PYTHONPATH，让测试脚本能导入 atf 模块
                env["PYTHONPATH"] = f"{_ATF_ROOT}:{env.get('PYTHONPATH', '')}"
                log.info(f"项目 venv 缺少 atf 模块，通过 PYTHONPATH 添加 api-auto-test")

        # 构建 pytest 命令
        allure_dir = repo_root / "tests" / "allure-results"
        if python_path == "uv":
            cmd = ["uv", "run", "pytest", pytest_path, "-v", "--tb=short", "-q", "--alluredir", str(allure_dir)]
        else:
            cmd = [python_path, "-m", "pytest", pytest_path, "-v", "--tb=short", "-q", "--alluredir", str(allure_dir)]

        log.info(f"执行测试命令: {' '.join(cmd)}")

        process = subprocess.Popen(
            cmd,
            cwd=str(repo_root),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
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

        # 自动生成 Allure 报告
        if allure_dir.exists() and _ensure_allure_available():
            report_dir = repo_root / "tests" / "allure-report"
            try:
                subprocess.run(
                    ["allure", "generate", str(allure_dir), "-o", str(report_dir), "--clean"],
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                log.info(f"✅ Allure 报告已生成: {report_dir}")
            except Exception as exc:
                log.warning(f"Allure 报告生成失败: {exc}")

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
