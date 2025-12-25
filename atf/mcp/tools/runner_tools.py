"""
Test Runner Tools
测试执行工具（已整合：run_tests = run_testcase + run_testcases）
"""

import time
import uuid
from pathlib import Path
from typing import Literal

from mcp.server.fastmcp import FastMCP
from pydantic import ValidationError

from atf.core.log_manager import log
from atf.mcp.models import (
    AssertionResultModel,
    RunTestsResponse,
    GetTestResultsResponse,
    TestResultHistoryModel,
    TestResultModel,
)
from atf.mcp.tools.testcase_tools import format_validation_error
from atf.mcp.utils import (
    get_roots,
    load_yaml_file,
    parse_testcase_input,
    parse_unittest_input,
    resolve_tests_root,
    resolve_yaml_path,
    expected_py_path,
    detect_testcase_type,
)
from atf.mcp.executor import (
    execute_single_test,
    run_pytest,
    save_to_history,
    get_history,
)


def register_runner_tools(mcp: FastMCP) -> None:
    """注册测试执行工具"""

    @mcp.tool(
        name="run_tests",
        title="执行测试用例",
        description="执行单个或批量 YAML 测试用例，支持集成测试 testcase 和单元测试 unittest。\n\n"
        "**执行模式（自动识别）**:\n"
        "- 传入 `yaml_path` → 执行单个测试用例\n"
        "- 传入 `root_path` → 批量执行目录下的所有测试用例\n\n"
        "**参数说明**:\n"
        "- `yaml_path`: 单个测试用例路径（相对于 workspace），与 root_path 二选一\n"
        "- `root_path`: 测试目录路径，默认 tests\n"
        "- `test_type`: `all`(全部) | `integration`(集成) | `unit`(单元)，仅批量模式有效\n"
        "- `workspace`: **必须**，指定项目根目录\n"
        "- `python_path`: 可选，指定 Python 解释器路径，如 `/path/to/venv/bin/python`\n\n"
        "**返回值说明**:\n"
        "- `mode`: single=单个, batch=批量\n"
        "- 单个模式: test_name, yaml_path, py_path, result\n"
        "- 批量模式: total, passed, failed, skipped, duration, results\n\n"
        "**示例**:\n"
        "```json\n"
        "# 单个测试\n"
        "{\n"
        "  \"yaml_path\": \"tests/cases/auth_integration.yaml\",\n"
        "  \"workspace\": \"/Volumes/DATABASE/code/glam-cart/backend\"\n"
        "}\n\n"
        "# 批量测试\n"
        "{\n"
        "  \"root_path\": \"tests/cases\",\n"
        "  \"test_type\": \"integration\",\n"
        "  \"workspace\": \"/Volumes/DATABASE/code/glam-cart/backend\",\n"
        "  \"python_path\": \"/Volumes/DATABASE/code/glam-cart/backend/venv/bin/python\"\n"
        "}\n"
        "```",
    )
    def run_tests(
        yaml_path: str | None = None,
        root_path: str | None = None,
        test_type: Literal["all", "integration", "unit"] = "all",
        workspace: str | None = None,
        python_path: str | None = None,
    ) -> RunTestsResponse:
        """统一执行单个或批量测试用例"""
        # 判断执行模式
        is_single_mode = yaml_path is not None

        try:
            if is_single_mode:
                # ========== 单个测试模式 ==========
                yaml_full_path, yaml_relative_path, repo_root = resolve_yaml_path(yaml_path, workspace)
                yaml_data = load_yaml_file(yaml_full_path)

                testcase_type = detect_testcase_type(yaml_data)
                if testcase_type == "unittest":
                    testcase_model = parse_unittest_input(yaml_data)
                else:
                    testcase_model = parse_testcase_input(yaml_data)
                test_name = testcase_model.name

                py_full_path, py_relative_path = expected_py_path(
                    yaml_full_path=yaml_full_path,
                    testcase_name=test_name,
                    workspace=workspace,
                )

                if not py_full_path.exists():
                    return RunTestsResponse(
                        status="error",
                        mode="single",
                        test_name=test_name,
                        yaml_path=yaml_relative_path,
                        error_message=f"pytest 文件不存在: {py_relative_path}",
                        error_details={"error_type": "file_not_found", "py_path": py_relative_path},
                    )

                result_data = run_pytest(str(py_full_path), repo_root, python_path)
                result = TestResultModel(
                    test_name=result_data["test_name"],
                    status=result_data["status"],
                    duration=result_data["duration"],
                    assertions=[
                        AssertionResultModel(**a) for a in result_data.get("assertions", [])
                    ],
                    error_message=result_data.get("error_message"),
                    traceback=result_data.get("traceback"),
                )

                return RunTestsResponse(
                    status="ok",
                    mode="single",
                    test_name=test_name,
                    yaml_path=yaml_relative_path,
                    py_path=py_relative_path,
                    result=result,
                )

            else:
                # ========== 批量测试模式 ==========
                start_time = time.time()
                results = []

                repo_root, _, cases_root, _ = get_roots(workspace)
                cases_root_resolved = cases_root.resolve(strict=False)

                if root_path:
                    raw_path = Path(root_path)
                    if raw_path.is_absolute():
                        base_dir = raw_path.resolve(strict=False)
                    else:
                        base_dir = (repo_root / raw_path).resolve(strict=False)
                else:
                    base_dir = cases_root_resolved

                if not base_dir.exists():
                    return RunTestsResponse(
                        status="error",
                        mode="batch",
                        error_message=f"目录不存在: {base_dir}",
                        error_details={"error_type": "directory_not_found", "path": str(base_dir)},
                    )

                yaml_files = list(base_dir.rglob("*.yaml"))
                filtered_files = []
                for yaml_file in yaml_files:
                    if not yaml_file.is_relative_to(cases_root_resolved):
                        continue
                    try:
                        data = load_yaml_file(yaml_file)
                        is_unit = "unittest" in data
                        is_integration = "testcase" in data

                        if test_type == "all":
                            filtered_files.append(yaml_file)
                        elif test_type == "unit" and is_unit:
                            filtered_files.append(yaml_file)
                        elif test_type == "integration" and is_integration:
                            filtered_files.append(yaml_file)
                    except Exception:
                        continue

                log.info(f"找到 {len(filtered_files)} 个测试用例待执行")

                for yaml_file in filtered_files:
                    try:
                        yaml_relative = yaml_file.relative_to(repo_root).as_posix()
                        if yaml_file.is_dir():
                            for sub_yaml in yaml_file.rglob("*.yaml"):
                                if sub_yaml.is_relative_to(cases_root_resolved):
                                    result = execute_single_test(str(sub_yaml), repo_root, python_path)
                                    results.append(result)
                        else:
                            result = execute_single_test(yaml_relative, repo_root, python_path)
                            results.append(result)
                    except Exception as exc:
                        log.error(f"执行测试用例失败: {yaml_file}: {exc}")

                end_time = time.time()
                duration = round(end_time - start_time, 2)

                passed = sum(1 for r in results if r.status == "passed")
                failed = sum(1 for r in results if r.status == "failed")
                skipped = sum(1 for r in results if r.status == "skipped")

                run_id = str(uuid.uuid4())[:8]
                save_to_history(
                    run_id=run_id,
                    total=len(results),
                    passed=passed,
                    failed=failed,
                    skipped=skipped,
                    duration=duration,
                    test_names=[r.test_name for r in results],
                )

                return RunTestsResponse(
                    status="ok" if failed == 0 else "error",
                    mode="batch",
                    total=len(results),
                    passed=passed,
                    failed=failed,
                    skipped=skipped,
                    duration=duration,
                    results=results,
                )

        except ValidationError as exc:
            log.error(f"MCP 执行测试参数验证失败: {exc}")
            return RunTestsResponse(
                status="error",
                mode="single" if is_single_mode else "batch",
                error_message=f"参数验证失败: {exc}",
                error_details={"error_type": "validation_error", "details": format_validation_error(exc)},
            )
        except Exception as exc:
            log.error(f"MCP 执行测试失败: {exc}")
            return RunTestsResponse(
                status="error",
                mode="single" if is_single_mode else "batch",
                error_message=f"未知错误: {type(exc).__name__}: {str(exc)}",
                error_details={"error_type": "unknown_error", "exception_type": type(exc).__name__},
            )

    @mcp.tool(
        name="get_test_results",
        title="获取测试执行历史",
        description="获取测试执行历史记录，包括每次运行的统计信息和测试用例列表。\n\n"
        "**参数说明**:\n"
        "- `limit`: 可选，返回记录数量，默认 10 条\n\n"
        "示例:\n"
        "```json\n"
        "{\n"
        "  \"limit\": 20\n"
        "}\n"
        "```",
    )
    def get_test_results(
        limit: int = 10,
    ) -> GetTestResultsResponse:
        """获取测试执行历史"""
        try:
            recent = get_history(limit)

            results = [
                TestResultHistoryModel(
                    run_id=item["run_id"],
                    timestamp=item["timestamp"],
                    total=item["total"],
                    passed=item["passed"],
                    failed=item["failed"],
                    skipped=item["skipped"],
                    duration=item["duration"],
                    test_names=item["test_names"],
                )
                for item in recent
            ]

            return GetTestResultsResponse(status="ok", results=results)
        except Exception as exc:
            log.error(f"获取测试执行历史失败: {exc}")
            return GetTestResultsResponse(status="error", results=[])
