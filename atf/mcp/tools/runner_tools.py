"""
Test Runner Tools
测试执行工具
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
    BatchRunResponse,
    GetTestResultsResponse,
    RunTestcaseResponse,
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
        name="run_testcase",
        title="执行测试用例",
        description="执行单个 YAML 测试用例（支持集成测试 testcase 和单元测试 unittest），返回执行结果和断言详情。\n\n**重要**: 必须传递 `workspace` 参数指定项目根目录，否则默认使用 api-auto-test 仓库。",
    )
    def run_testcase(
        yaml_path: str,
        workspace: str | None = None,
    ) -> RunTestcaseResponse:
        """执行单个测试用例（支持 testcase 和 unittest）"""
        try:
            yaml_full_path, yaml_relative_path, repo_root = resolve_yaml_path(yaml_path, workspace)
            yaml_data = load_yaml_file(yaml_full_path)

            # 使用统一的类型检测函数
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
                return RunTestcaseResponse(
                    status="error",
                    test_name=test_name,
                    yaml_path=yaml_relative_path,
                    py_path=None,
                    result=None,
                    error_message=f"pytest 文件不存在，请先调用 write_unittest 或 write_testcase 生成: {py_relative_path}",
                    error_details={"error_type": "file_not_found", "py_path": py_relative_path},
                )

            # 执行测试
            result_data = run_pytest(str(py_full_path), repo_root)

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

            return RunTestcaseResponse(
                status="ok",
                test_name=test_name,
                yaml_path=yaml_relative_path,
                py_path=py_relative_path,
                result=result,
            )
        except ValidationError as exc:
            log.error(f"MCP 执行测试用例参数验证失败: {exc}")
            return RunTestcaseResponse(
                status="error",
                test_name="",
                yaml_path=None,
                py_path=None,
                result=None,
                error_message=f"参数验证失败: {exc}",
                error_details={"error_type": "validation_error", "details": format_validation_error(exc)},
            )
        except Exception as exc:
            log.error(f"MCP 执行测试用例失败: {exc}")
            return RunTestcaseResponse(
                status="error",
                test_name="",
                yaml_path=None,
                py_path=None,
                result=None,
                error_message=f"未知错误: {type(exc).__name__}: {str(exc)}",
                error_details={"error_type": "unknown_error", "exception_type": type(exc).__name__},
            )

    @mcp.tool(
        name="run_testcases",
        title="批量执行测试用例",
        description="批量执行指定的 YAML 测试用例，支持目录和文件模式，返回汇总统计和每个用例的详细结果。\n\n**重要**: 必须传递 `workspace` 参数指定项目根目录，否则默认使用 api-auto-test 仓库。",
    )
    def run_testcases(
        root_path: str | None = None,
        test_type: Literal["all", "integration", "unit"] = "all",
        workspace: str | None = None,
    ) -> BatchRunResponse:
        """批量执行测试用例"""
        start_time = time.time()
        results = []

        try:
            repo_root, tests_root, _ = get_roots(workspace)
            tests_root_resolved = tests_root.resolve(strict=False)

            if root_path:
                raw_path = Path(root_path)
                if raw_path.is_absolute():
                    base_dir = raw_path.resolve(strict=False)
                else:
                    base_dir = (repo_root / raw_path).resolve(strict=False)
            else:
                base_dir = tests_root_resolved

            # 检查目录是否存在
            if not base_dir.exists():
                log.error(f"MCP 批量执行测试用例失败: 目录不存在 {base_dir}")
                return BatchRunResponse(
                    status="error",
                    total=0,
                    passed=0,
                    failed=0,
                    skipped=0,
                    duration=0.0,
                    results=[],
                )

            # 获取所有 YAML 文件
            yaml_files = list(base_dir.rglob("*.yaml"))

            # 根据类型过滤
            filtered_files = []
            for yaml_file in yaml_files:
                if not yaml_file.is_relative_to(tests_root_resolved):
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

            # 逐个执行测试
            for yaml_file in filtered_files:
                try:
                    yaml_relative = yaml_file.relative_to(repo_root).as_posix()

                    # 如果是目录，列出所有 YAML
                    if yaml_file.is_dir():
                        for sub_yaml in yaml_file.rglob("*.yaml"):
                            if sub_yaml.is_relative_to(tests_root_resolved):
                                result = execute_single_test(str(sub_yaml), repo_root)
                                results.append(result)
                    else:
                        result = execute_single_test(yaml_relative, repo_root)
                        results.append(result)
                except Exception as exc:
                    log.error(f"执行测试用例失败: {yaml_file}: {exc}")

        except Exception as exc:
            log.error(f"MCP 批量执行测试用例失败: {exc}")

        end_time = time.time()
        duration = round(end_time - start_time, 2)

        # 统计结果
        passed = sum(1 for r in results if r.status == "passed")
        failed = sum(1 for r in results if r.status == "failed")
        skipped = sum(1 for r in results if r.status == "skipped")

        # 保存到历史记录
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

        return BatchRunResponse(
            status="ok" if failed == 0 else "error",
            total=len(results),
            passed=passed,
            failed=failed,
            skipped=skipped,
            duration=duration,
            results=results,
        )

    @mcp.tool(
        name="get_test_results",
        title="获取测试执行历史",
        description="获取测试执行历史记录，包括每次运行的统计信息和测试用例列表。",
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
