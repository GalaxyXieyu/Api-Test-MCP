from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

import yaml
from mcp.server import FastMCP
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from atf.case_generator import CaseGenerator
from atf.unit_case_generator import UnitCaseGenerator
from atf.core.log_manager import log


REPO_ROOT = Path(os.getenv("ATF_REPO_ROOT", Path(__file__).resolve().parent.parent))
TESTS_ROOT = REPO_ROOT / "tests"
TEST_CASES_ROOT = REPO_ROOT / "test_cases"
RESULTS_ROOT = REPO_ROOT / "test_results"

# 测试执行结果存储（内存中）
_test_execution_history: list[dict] = []

mcp = FastMCP(name="api-auto-test-mcp")
MCP_VERSION = "0.1.0"


class AssertionModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str
    field: str | None = None
    expected: Any | None = None
    container: Any | None = None
    query: str | None = None


class StepModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    id: str
    path: str
    method: str
    headers: dict | None = None
    data: Any | None = None
    params: dict | None = None
    files: dict | None = None
    project: str | None = None
    assert_: list[AssertionModel] | None = Field(default=None, alias="assert")

    @model_validator(mode="after")
    def validate_required(self) -> "StepModel":
        if not self.id:
            raise ValueError("steps.id 不能为空")
        if not self.path:
            raise ValueError("steps.path 不能为空")
        if not self.method:
            raise ValueError("steps.method 不能为空")
        return self


class TeardownModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    id: str
    operation_type: Literal["api", "db"]
    path: str | None = None
    method: str | None = None
    headers: dict | None = None
    data: Any | None = None
    params: dict | None = None
    files: dict | None = None
    project: str | None = None
    assert_: list[AssertionModel] | None = Field(default=None, alias="assert")
    query: str | None = None

    @model_validator(mode="after")
    def validate_operation(self) -> "TeardownModel":
        if self.operation_type == "api":
            missing = []
            if not self.path:
                missing.append("path")
            if not self.method:
                missing.append("method")
            if self.headers is None:
                missing.append("headers")
            if self.data is None:
                missing.append("data")
            if missing:
                raise ValueError(f"teardowns.api 缺少必填字段: {', '.join(missing)}")
        if self.operation_type == "db" and not self.query:
            raise ValueError("teardowns.db 缺少必填字段: query")
        return self


class AllureModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    epic: str | None = None
    feature: str | None = None
    story: str | None = None


# ==================== 单元测试模型 ====================


class MockModel(BaseModel):
    """Mock 配置模型"""
    model_config = ConfigDict(extra="forbid")

    target: str  # mock 目标路径，如 "app.services.user_service.UserRepository"
    method: str | None = None  # 方法名
    return_value: Any | None = None  # 返回值
    side_effect: Any | None = None  # 副作用（异常或可调用对象）


class UnitTestInputModel(BaseModel):
    """单元测试输入参数模型"""
    model_config = ConfigDict(extra="forbid")

    args: list[Any] | None = None  # 位置参数
    kwargs: dict[str, Any] | None = None  # 关键字参数


class UnitAssertionModel(BaseModel):
    """单元测试断言模型"""
    model_config = ConfigDict(extra="forbid")

    type: str  # equals, not_equals, contains, raises, called_once, called_with, etc.
    field: str | None = None  # JSONPath 字段路径
    expected: Any | None = None  # 期望值
    mock: str | None = None  # mock 名称（用于 mock 相关断言）
    args: list[Any] | None = None  # 期望的调用参数
    kwargs: dict[str, Any] | None = None  # 期望的关键字参数
    exception: str | None = None  # 期望的异常类型
    message: str | None = None  # 期望的异常消息


class UnitTestCaseModel(BaseModel):
    """单个单元测试用例模型"""
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    id: str
    description: str | None = None
    mocks: list[MockModel] | None = None
    inputs: UnitTestInputModel | None = None
    assert_: list[UnitAssertionModel] | None = Field(default=None, alias="assert")

    @model_validator(mode="after")
    def validate_required(self) -> "UnitTestCaseModel":
        if not self.id:
            raise ValueError("unittest.cases.id 不能为空")
        return self


class UnitTestTargetModel(BaseModel):
    """被测目标模型"""
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    module: str  # 被测模块路径
    class_: str | None = Field(default=None, alias="class")  # 被测类名
    function: str | None = None  # 被测函数名

    @model_validator(mode="after")
    def validate_target(self) -> "UnitTestTargetModel":
        if not self.module:
            raise ValueError("unittest.target.module 不能为空")
        return self


class UnitTestFixtureModel(BaseModel):
    """测试夹具模型"""
    model_config = ConfigDict(extra="forbid")

    type: str  # patch, cleanup, setup_db, etc.
    target: str | None = None
    value: Any | None = None
    action: str | None = None


class UnitTestFixturesModel(BaseModel):
    """测试夹具集合模型"""
    model_config = ConfigDict(extra="forbid")

    setup: list[UnitTestFixtureModel] | None = None
    teardown: list[UnitTestFixtureModel] | None = None


class UnitTestModel(BaseModel):
    """单元测试模型"""
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    name: str
    description: str | None = None
    env_type: Literal["venv", "conda", "uv"] = "venv"  # 运行环境的虚拟环境类型
    target: UnitTestTargetModel
    allure: AllureModel | None = None
    cases: list[UnitTestCaseModel]
    fixtures: UnitTestFixturesModel | None = None

    @model_validator(mode="after")
    def validate_required(self) -> "UnitTestModel":
        if not self.name:
            raise ValueError("unittest.name 不能为空")
        if not self.cases:
            raise ValueError("unittest.cases 不能为空")
        return self


# ==================== 集成测试模型 ====================


class TestcaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    name: str
    description: str | None = None
    host: str | None = None  # 可选的测试服务地址
    allure: AllureModel | None = None
    steps: list[StepModel]
    teardowns: list[TeardownModel] | None = None

    @model_validator(mode="after")
    def validate_required(self) -> "TestcaseModel":
        if not self.name:
            raise ValueError("testcase.name 不能为空")
        if not self.steps:
            raise ValueError("testcase.steps 不能为空")
        return self


class GenerateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok", "error"]
    written_files: list[str]
    error_message: str | None = None
    error_details: dict | None = None  # 更详细的错误信息，用于大模型理解


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok", "error"]
    version: str
    repo_root: str
    tests_root: str
    test_cases_root: str


class ListTestcasesResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok", "error"]
    testcases: list[str]


class ReadTestcaseResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok", "error"]
    yaml_path: str
    mode: Literal["summary", "full"]
    testcase: dict[str, Any] | None


class ValidateTestcaseResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok", "error"]
    errors: list[str]


class RegenerateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok", "error"]
    written_files: list[str]


class DeleteTestcaseResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok", "error"]
    deleted_files: list[str]


# ==================== 测试执行结果模型 ====================


class AssertionResultModel(BaseModel):
    """断言结果模型"""
    model_config = ConfigDict(extra="forbid")

    assertion_type: str  # 断言类型: equals, contains, status_code, etc.
    field: str | None = None  # 字段路径
    expected: Any | None = None  # 期望值
    actual: Any | None = None  # 实际值
    passed: bool  # 是否通过
    message: str | None = None  # 失败时的消息


class TestResultModel(BaseModel):
    """单个测试用例执行结果"""
    model_config = ConfigDict(extra="forbid")

    test_name: str  # 测试名称
    status: Literal["passed", "failed", "error", "skipped"]  # 执行状态
    duration: float  # 执行时间（秒）
    assertions: list[AssertionResultModel]  # 断言结果列表
    error_message: str | None = None  # 错误信息
    traceback: str | None = None  # 错误堆栈


class RunTestcaseResponse(BaseModel):
    """单个测试用例执行响应"""
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok", "error"]
    test_name: str
    yaml_path: str | None = None
    py_path: str | None = None
    result: TestResultModel | None = None


class BatchRunResponse(BaseModel):
    """批量执行响应"""
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok", "error"]
    total: int  # 总数
    passed: int  # 通过
    failed: int  # 失败
    skipped: int  # 跳过
    duration: float  # 总耗时（秒）
    results: list[TestResultModel]  # 每个测试用例的结果


class TestResultHistoryModel(BaseModel):
    """测试结果历史记录"""
    model_config = ConfigDict(extra="forbid")

    run_id: str  # 运行ID
    timestamp: str  # 执行时间
    total: int
    passed: int
    failed: int
    skipped: int
    duration: float
    test_names: list[str]  # 执行的测试用例列表


class GetTestResultsResponse(BaseModel):
    """获取测试执行历史响应"""
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok", "error"]
    results: list[TestResultHistoryModel]


def _get_roots(workspace: str | None) -> tuple[Path, Path, Path]:
    """根据 workspace 参数返回 (repo_root, tests_root, test_cases_root)"""
    if workspace:
        repo = Path(workspace).resolve(strict=False)
    else:
        repo = REPO_ROOT
    return repo, repo / "tests", repo / "test_cases"


def _resolve_yaml_path(yaml_path: str, workspace: str | None = None) -> tuple[Path, str, Path]:
    """返回 (yaml_full_path, yaml_relative_path, repo_root)"""
    repo_root, tests_root, _ = _get_roots(workspace)
    raw_path = Path(yaml_path)
    if raw_path.is_absolute():
        normalized = raw_path.resolve(strict=False)
    else:
        normalized = (repo_root / raw_path).resolve(strict=False)
    if not normalized.name.endswith(".yaml"):
        raise ValueError("yaml_path 必须以 .yaml 结尾")
    tests_root_resolved = tests_root.resolve(strict=False)
    if not normalized.is_relative_to(tests_root_resolved):
        raise ValueError(f"yaml_path 必须位于 {tests_root_resolved} 目录下")
    relative_path = normalized.relative_to(repo_root).as_posix()
    return normalized, relative_path, repo_root


def _build_testcase_yaml(testcase: TestcaseModel) -> dict[str, Any]:
    payload = testcase.model_dump(by_alias=True, exclude_none=True)
    return {"testcase": payload}


def _parse_testcase_input(raw_testcase: Any) -> TestcaseModel:
    if isinstance(raw_testcase, TestcaseModel):
        return raw_testcase

    data = raw_testcase
    if isinstance(raw_testcase, str):
        stripped = raw_testcase.strip()
        if not stripped:
            raise ValueError("testcase 不能为空")
        try:
            data = json.loads(stripped)
        except json.JSONDecodeError as json_err:
            log.debug(f"JSON 解析失败: {json_err}, 原始字符串: {stripped[:200]}")
            try:
                data = yaml.safe_load(stripped)
            except yaml.YAMLError as exc:
                raise ValueError(f"testcase 字符串解析失败, 原始内容: {stripped[:200]}") from exc

    if not isinstance(data, dict):
        raise ValueError("testcase 必须是对象")

    if "testcase" in data and isinstance(data["testcase"], dict):
        data = data["testcase"]

    return TestcaseModel.model_validate(data)


def _load_yaml_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ValueError("YAML 文件不存在")
    with path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)
    if data is None:
        raise ValueError("YAML 文件内容为空")
    if not isinstance(data, dict):
        raise ValueError("YAML 顶层必须是对象")
    return data


def _build_testcase_summary(testcase: TestcaseModel) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "name": testcase.name,
        "steps": [
            {"id": step.id, "path": step.path, "method": step.method}
            for step in testcase.steps
        ],
    }
    if testcase.description:
        summary["description"] = testcase.description
    if testcase.allure:
        summary["allure"] = testcase.allure.model_dump(exclude_none=True)
    if testcase.teardowns:
        summary["teardowns"] = [
            {"id": td.id, "operation_type": td.operation_type}
            for td in testcase.teardowns
        ]
    return summary


def _resolve_tests_root(root_path: str | None, workspace: str | None = None) -> tuple[Path, Path]:
    """返回 (resolved_tests_root, repo_root)"""
    repo_root, tests_root, _ = _get_roots(workspace)
    tests_root_resolved = tests_root.resolve(strict=False)
    if not root_path:
        return tests_root_resolved, repo_root
    raw_path = Path(root_path)
    if raw_path.is_absolute():
        normalized = raw_path.resolve(strict=False)
    else:
        normalized = (repo_root / raw_path).resolve(strict=False)
    if not normalized.is_relative_to(tests_root_resolved):
        raise ValueError(f"root_path 必须位于 {tests_root_resolved} 目录下")
    if not normalized.exists() or not normalized.is_dir():
        raise ValueError("root_path 必须是已存在的目录")
    return normalized, repo_root


def _expected_py_path(yaml_full_path: Path, testcase_name: str, workspace: str | None = None) -> tuple[Path, str]:
    _, tests_root, test_cases_root = _get_roots(workspace)
    repo_root = tests_root.parent
    relative_to_tests = yaml_full_path.relative_to(tests_root)
    directory_path = relative_to_tests.parent
    py_filename = f"test_{testcase_name}.py"
    py_full_path = (test_cases_root / directory_path / py_filename).resolve(strict=False)
    py_relative_path = py_full_path.relative_to(repo_root).as_posix()
    return py_full_path, py_relative_path


# ==================== 单元测试辅助函数 ====================


def _parse_unittest_input(raw_unittest: Any) -> UnitTestModel:
    """解析单元测试输入"""
    if isinstance(raw_unittest, UnitTestModel):
        return raw_unittest

    data = raw_unittest
    if isinstance(raw_unittest, str):
        stripped = raw_unittest.strip()
        if not stripped:
            raise ValueError("unittest 不能为空")
        try:
            data = json.loads(stripped)
        except json.JSONDecodeError:
            try:
                data = yaml.safe_load(stripped)
            except yaml.YAMLError as exc:
                raise ValueError(f"unittest 字符串解析失败") from exc

    if not isinstance(data, dict):
        raise ValueError("unittest 必须是对象")

    if "unittest" in data and isinstance(data["unittest"], dict):
        data = data["unittest"]

    return UnitTestModel.model_validate(data)


def _build_unittest_yaml(unittest: UnitTestModel) -> dict[str, Any]:
    """构建单元测试 YAML 数据"""
    payload = unittest.model_dump(by_alias=True, exclude_none=True)
    return {"unittest": payload}


@mcp.tool(
    name="health_check",
    title="MCP 服务健康检查",
    description="返回服务版本与基础路径信息。",
)
def health_check() -> HealthResponse:
    return HealthResponse(
        status="ok",
        version=MCP_VERSION,
        repo_root=str(REPO_ROOT),
        tests_root=str(TESTS_ROOT),
        test_cases_root=str(TEST_CASES_ROOT),
    )


@mcp.tool(
    name="list_testcases",
    title="列出测试用例 YAML",
    description="列出 tests 目录下的 YAML 测试用例文件，可指定子目录和测试类型过滤。",
)
def list_testcases(
    root_path: str | None = None,
    test_type: Literal["all", "integration", "unit"] = "all",
    workspace: str | None = None,
) -> ListTestcasesResponse:
    try:
        base_dir, repo_root = _resolve_tests_root(root_path, workspace)
        all_yaml_files = list(base_dir.rglob("*.yaml"))

        if test_type == "all":
            testcases = sorted(
                path.relative_to(repo_root).as_posix()
                for path in all_yaml_files
            )
        else:
            testcases = []
            for path in all_yaml_files:
                try:
                    data = _load_yaml_file(path)
                    is_unit = "unittest" in data
                    is_integration = "testcase" in data

                    if test_type == "unit" and is_unit:
                        testcases.append(path.relative_to(repo_root).as_posix())
                    elif test_type == "integration" and is_integration:
                        testcases.append(path.relative_to(repo_root).as_posix())
                except Exception:
                    continue
            testcases = sorted(testcases)

        return ListTestcasesResponse(status="ok", testcases=testcases)
    except Exception as exc:
        log.error(f"MCP 列出测试用例失败: {exc}")
        return ListTestcasesResponse(status="error", testcases=[])


@mcp.tool(
    name="read_testcase",
    title="读取测试用例内容",
    description="读取指定 YAML 测试用例内容，默认返回摘要。",
)
def read_testcase(
    yaml_path: str,
    mode: Literal["summary", "full"] = "summary",
    workspace: str | None = None,
) -> ReadTestcaseResponse:
    try:
        yaml_full_path, yaml_relative_path, _ = _resolve_yaml_path(yaml_path, workspace)
        raw_data = _load_yaml_file(yaml_full_path)
        if mode == "full":
            return ReadTestcaseResponse(
                status="ok",
                yaml_path=yaml_relative_path,
                mode=mode,
                testcase=raw_data,
            )
        testcase_model = _parse_testcase_input(raw_data)
        summary = _build_testcase_summary(testcase_model)
        return ReadTestcaseResponse(
            status="ok",
            yaml_path=yaml_relative_path,
            mode=mode,
            testcase=summary,
        )
    except Exception as exc:
        log.error(f"MCP 读取测试用例失败: {exc}")
        return ReadTestcaseResponse(
            status="error",
            yaml_path=yaml_path,
            mode=mode,
            testcase=None,
        )


@mcp.tool(
    name="validate_testcase",
    title="校验测试用例结构",
    description="校验指定 YAML 测试用例结构是否符合规范。",
)
def validate_testcase(
    yaml_path: str,
    workspace: str | None = None,
) -> ValidateTestcaseResponse:
    errors: list[str] = []
    try:
        yaml_full_path, _, _ = _resolve_yaml_path(yaml_path, workspace)
        raw_data = _load_yaml_file(yaml_full_path)
        _parse_testcase_input(raw_data)
    except ValidationError as exc:
        errors = [
            f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}"
            for err in exc.errors()
        ]
    except Exception as exc:
        errors = [str(exc)]

    if errors:
        log.error(f"MCP 校验测试用例失败: {errors}")
        return ValidateTestcaseResponse(status="error", errors=errors)
    return ValidateTestcaseResponse(status="ok", errors=[])


@mcp.tool(
    name="regenerate_py",
    title="重新生成 pytest 文件",
    description="根据已存在的 YAML 测试用例重新生成 pytest 脚本。",
)
def regenerate_py(
    yaml_path: str,
    overwrite: bool = True,
    workspace: str | None = None,
) -> RegenerateResponse:
    try:
        yaml_full_path, yaml_relative_path, repo_root = _resolve_yaml_path(yaml_path, workspace)
        os.chdir(repo_root)
        if not yaml_full_path.exists():
            raise ValueError("YAML 文件不存在")
        testcase_model = _parse_testcase_input(_load_yaml_file(yaml_full_path))
        py_full_path, py_relative_path = _expected_py_path(
            yaml_full_path=yaml_full_path,
            testcase_name=testcase_model.name,
            workspace=workspace,
        )
        if overwrite and py_full_path.exists():
            py_full_path.unlink()
        CaseGenerator().generate_test_cases(project_yaml_list=[yaml_relative_path])
        if not py_full_path.exists():
            raise ValueError("pytest 文件未生成")
        return RegenerateResponse(
            status="ok",
            written_files=[yaml_relative_path, py_relative_path],
        )
    except Exception as exc:
        log.error(f"MCP 重新生成 pytest 失败: {exc}")
        return RegenerateResponse(status="error", written_files=[])


@mcp.tool(
    name="delete_testcase",
    title="删除测试用例",
    description="删除 YAML 与对应的 pytest 文件。",
)
def delete_testcase(
    yaml_path: str,
    delete_py: bool = True,
    workspace: str | None = None,
) -> DeleteTestcaseResponse:
    deleted_files: list[str] = []
    try:
        yaml_full_path, yaml_relative_path, _ = _resolve_yaml_path(yaml_path, workspace)
        if not yaml_full_path.exists():
            raise ValueError("YAML 文件不存在")
        testcase_model = _parse_testcase_input(_load_yaml_file(yaml_full_path))
        py_full_path, py_relative_path = _expected_py_path(
            yaml_full_path=yaml_full_path,
            testcase_name=testcase_model.name,
            workspace=workspace,
        )
        yaml_full_path.unlink()
        deleted_files.append(yaml_relative_path)
        if delete_py and py_full_path.exists():
            py_full_path.unlink()
            deleted_files.append(py_relative_path)
        return DeleteTestcaseResponse(status="ok", deleted_files=deleted_files)
    except Exception as exc:
        log.error(f"MCP 删除测试用例失败: {exc}")
        return DeleteTestcaseResponse(status="error", deleted_files=[])


@mcp.tool(
    name="write_testcase",
    title="写入测试用例并生成 pytest 脚本",
    description="根据输入的测试用例结构写入 YAML 文件，并生成对应的 pytest 用例脚本。",
)
def write_testcase(
    yaml_path: str,
    testcase: TestcaseModel | dict | str,
    overwrite: bool = False,
    workspace: str | None = None,
) -> GenerateResponse:
    try:
        testcase_model = _parse_testcase_input(testcase)
        yaml_full_path, yaml_relative_path, repo_root = _resolve_yaml_path(yaml_path, workspace)
        os.chdir(repo_root)
        py_full_path, py_relative_path = _expected_py_path(
            yaml_full_path=yaml_full_path,
            testcase_name=testcase_model.name,
            workspace=workspace,
        )

        if yaml_full_path.exists() and not overwrite:
            raise ValueError("YAML 文件已存在，未开启覆盖写入")
        if py_full_path.exists() and not overwrite:
            raise ValueError("pytest 文件已存在，未开启覆盖写入")

        yaml_full_path.parent.mkdir(parents=True, exist_ok=True)
        test_data = _build_testcase_yaml(testcase_model)
        with yaml_full_path.open("w", encoding="utf-8") as file:
            yaml.safe_dump(test_data, file, allow_unicode=True, sort_keys=False)

        if overwrite and py_full_path.exists():
            py_full_path.unlink()

        CaseGenerator().generate_test_cases(project_yaml_list=[yaml_relative_path])
        if not py_full_path.exists():
            raise ValueError("pytest 文件未生成，请检查测试用例数据格式")

        return GenerateResponse(status="ok", written_files=[yaml_relative_path, py_relative_path])
    except ValidationError as exc:
        # Pydantic 验证错误，返回详细字段级别信息
        log.error(f"MCP 写入测试用例参数验证失败: {exc}")
        errors = []
        for err in exc.errors():
            loc = ".".join(str(l) for l in err["loc"]) if err["loc"] else "unknown"
            errors.append(f"  - {loc}: {err['msg']} (输入类型: {err.get('type', 'unknown')})")
        error_details = {
            "error_type": "validation_error",
            "message": "参数格式错误，请检查以下字段：",
            "details": errors,
            "hints": [
                "assert.type 应该是: equals, not_equals, contains",
                "assert.field 应该为具体的响应字段名，如 status, result 等",
                "step.method 应该是: GET, POST, PUT, DELETE, PATCH 等 HTTP 方法"
            ]
        }
        return GenerateResponse(
            status="error",
            written_files=[],
            error_message=f"参数验证失败: {exc}",
            error_details=error_details
        )
    except ValueError as exc:
        log.error(f"MCP 写入测试用例业务验证失败: {exc}")
        return GenerateResponse(
            status="error",
            written_files=[],
            error_message=str(exc),
            error_details={"error_type": "value_error", "message": str(exc)}
        )
    except Exception as exc:
        log.error(f"MCP 写入测试用例失败: {exc}")
        return GenerateResponse(
            status="error",
            written_files=[],
            error_message=f"未知错误: {type(exc).__name__}: {str(exc)}",
            error_details={"error_type": "unknown_error", "exception_type": type(exc).__name__}
        )


# ==================== 单元测试 MCP 工具 ====================


@mcp.tool(
    name="write_unittest",
    title="写入单元测试用例并生成 pytest 脚本",
    description="根据输入的单元测试结构写入 YAML 文件，并生成对应的 pytest 单元测试脚本。",
)
def write_unittest(
    yaml_path: str,
    unittest: UnitTestModel | dict | str,
    overwrite: bool = False,
    workspace: str | None = None,
) -> GenerateResponse:
    try:
        unittest_model = _parse_unittest_input(unittest)
        yaml_full_path, yaml_relative_path, repo_root = _resolve_yaml_path(yaml_path, workspace)
        os.chdir(repo_root)
        py_full_path, py_relative_path = _expected_py_path(
            yaml_full_path=yaml_full_path,
            testcase_name=unittest_model.name,
            workspace=workspace,
        )

        if yaml_full_path.exists() and not overwrite:
            raise ValueError("YAML 文件已存在，未开启覆盖写入")
        if py_full_path.exists() and not overwrite:
            raise ValueError("pytest 文件已存在，未开启覆盖写入")

        yaml_full_path.parent.mkdir(parents=True, exist_ok=True)
        test_data = _build_unittest_yaml(unittest_model)
        with yaml_full_path.open("w", encoding="utf-8") as file:
            yaml.safe_dump(test_data, file, allow_unicode=True, sort_keys=False)

        if overwrite and py_full_path.exists():
            py_full_path.unlink()

        result = UnitCaseGenerator().generate_unit_tests(yaml_relative_path)
        if not result:
            raise ValueError("pytest 文件未生成，请检查单元测试数据格式")

        return GenerateResponse(status="ok", written_files=[yaml_relative_path, py_relative_path])
    except ValidationError as exc:
        # Pydantic 验证错误，返回详细字段级别信息
        log.error(f"MCP 写入单元测试参数验证失败: {exc}")
        errors = []
        for err in exc.errors():
            loc = ".".join(str(l) for l in err["loc"]) if err["loc"] else "unknown"
            errors.append(f"  - {loc}: {err['msg']} (输入类型: {err.get('type', 'unknown')})")
        error_details = {
            "error_type": "validation_error",
            "message": "参数格式错误，请检查以下字段：",
            "details": errors,
            "hints": [
                "assert.type 应该是: equals, not_equals, contains, raises, called_once, called_with, not_called, is_none, is_not_none",
                "assert.field 应该为 result 或者不传",
                "fixtures 格式暂不支持 function 类型，当前仅支持 patch 类型"
            ]
        }
        return GenerateResponse(
            status="error",
            written_files=[],
            error_message=f"参数验证失败: {exc}",
            error_details=error_details
        )
    except ValueError as exc:
        log.error(f"MCP 写入单元测试业务验证失败: {exc}")
        return GenerateResponse(
            status="error",
            written_files=[],
            error_message=str(exc),
            error_details={"error_type": "value_error", "message": str(exc)}
        )
    except Exception as exc:
        log.error(f"MCP 写入单元测试失败: {exc}")
        return GenerateResponse(
            status="error",
            written_files=[],
            error_message=f"未知错误: {type(exc).__name__}: {str(exc)}",
            error_details={"error_type": "unknown_error", "exception_type": type(exc).__name__}
        )


# ==================== 测试执行 MCP 工具 ====================


def _get_python_path(repo_root: Path) -> str:
    """获取项目 venv 的 Python 路径"""
    # 优先使用 uv run
    if (repo_root / "pyproject.toml").exists():
        return "uv"

    # 查找 venv 路径
    venv_python = repo_root / ".venv" / "bin" / "python"
    if venv_python.exists():
        return str(venv_python)

    # 回退到系统 Python
    return sys.executable


def _run_pytest(pytest_path: str, repo_root: Path) -> dict:
    """执行 pytest 并返回结果"""
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
        # 获取正确的 Python 路径
        python_path = _get_python_path(repo_root)

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
        stdout, stderr = process.communicate()
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
            # 提取错误信息
            if stderr:
                result_data["error_message"] = stderr[-500:] if len(stderr) > 500 else stderr
            if stdout:
                result_data["traceback"] = stdout[-500:] if len(stdout) > 500 else stdout

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


@mcp.tool(
    name="run_testcase",
    title="执行测试用例",
    description="执行单个 YAML 测试用例（支持集成测试 testcase 和单元测试 unittest），返回执行结果和断言详情。",
)
def run_testcase(
    yaml_path: str,
    workspace: str | None = None,
) -> RunTestcaseResponse:
    """执行单个测试用例（支持 testcase 和 unittest）"""
    try:
        yaml_full_path, yaml_relative_path, repo_root = _resolve_yaml_path(yaml_path, workspace)
        yaml_data = _load_yaml_file(yaml_full_path)

        # 自动检测类型
        if "unittest" in yaml_data:
            # 单元测试
            testcase_model = _parse_unittest_input(yaml_data)
            test_name = testcase_model.name
        elif "testcase" in yaml_data:
            # 集成测试
            testcase_model = _parse_testcase_input(yaml_data)
            test_name = testcase_model.name
        else:
            return RunTestcaseResponse(
                status="error",
                test_name="",
                yaml_path=None,
                py_path=None,
                result=None,
            )

        py_full_path, py_relative_path = _expected_py_path(
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
            )

        # 执行测试
        result_data = _run_pytest(str(py_full_path), repo_root)

        # 转换为 Pydantic 模型
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
    except Exception as exc:
        log.error(f"MCP 执行测试用例失败: {exc}")
        return RunTestcaseResponse(
            status="error",
            test_name="",
            yaml_path=None,
            py_path=None,
            result=None,
        )


@mcp.tool(
    name="run_testcases",
    title="批量执行测试用例",
    description="批量执行指定的 YAML 测试用例，支持目录和文件模式，返回汇总统计和每个用例的详细结果。",
)
def run_testcases(
    root_path: str | None = None,
    test_type: Literal["all", "integration", "unit"] = "all",
    workspace: str | None = None,
) -> BatchRunResponse:
    """批量执行测试用例"""
    global _test_execution_history

    start_time = time.time()
    results: list[TestResultModel] = []

    try:
        repo_root, tests_root, _ = _get_roots(workspace)
        tests_root_resolved = tests_root.resolve(strict=False)

        if root_path:
            raw_path = Path(root_path)
            if raw_path.is_absolute():
                base_dir = raw_path.resolve(strict=False)
            else:
                base_dir = (repo_root / raw_path).resolve(strict=False)
        else:
            base_dir = tests_root_resolved

        # 获取所有 YAML 文件
        yaml_files = list(base_dir.rglob("*.yaml"))

        # 根据类型过滤
        filtered_files = []
        for yaml_file in yaml_files:
            if not yaml_file.is_relative_to(tests_root_resolved):
                continue
            try:
                data = _load_yaml_file(yaml_file)
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
                            result = _execute_single_test(str(sub_yaml), repo_root)
                            results.append(result)
                else:
                    result = _execute_single_test(yaml_relative, repo_root)
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
    _test_execution_history.append({
        "run_id": run_id,
        "timestamp": datetime.now().isoformat(),
        "total": len(results),
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "duration": duration,
        "test_names": [r.test_name for r in results],
    })

    return BatchRunResponse(
        status="ok" if failed == 0 else "error",
        total=len(results),
        passed=passed,
        failed=failed,
        skipped=skipped,
        duration=duration,
        results=results,
    )


def _execute_single_test(yaml_path: str, repo_root: Path) -> TestResultModel:
    """执行单个测试用例并返回结果"""
    try:
        yaml_full_path, yaml_relative_path, _ = _resolve_yaml_path(yaml_path)
        data = _load_yaml_file(yaml_full_path)

        # 解析测试用例
        if "testcase" in data:
            testcase_model = _parse_testcase_input(data)
        elif "unittest" in data:
            testcase_model = _parse_unittest_input(data)
        else:
            raise ValueError("未知的测试用例格式")

        py_full_path, _ = _expected_py_path(yaml_full_path, testcase_model.name)

        if not py_full_path.exists():
            return TestResultModel(
                test_name=testcase_model.name,
                status="error",
                duration=0.0,
                assertions=[],
                error_message="pytest 文件不存在，请先生成",
            )

        # 执行测试
        result_data = _run_pytest(str(py_full_path), repo_root)

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


@mcp.tool(
    name="get_test_results",
    title="获取测试执行历史",
    description="获取测试执行历史记录，包括每次运行的统计信息和测试用例列表。",
)
def get_test_results(
    limit: int = 10,
) -> GetTestResultsResponse:
    """获取测试执行历史"""
    global _test_execution_history

    try:
        # 返回最近的记录
        recent = _test_execution_history[-limit:] if limit > 0 else _test_execution_history

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


def main():
    """MCP 服务器入口函数，支持 uv run mcp install"""
    import sys
    import json
    import os

    # 检查是否有 install 子命令
    if len(sys.argv) > 1 and sys.argv[1] == "install":
        mcp_config = {
            "command": "api-auto-test-mcp",
            "args": ["--workspace", "${workspace}"]
        }

        # 尝试找到 Claude Code 的 MCP 配置文件
        config_path = None
        for path in [
            os.path.expanduser("~/.claude/.mcp.json"),
            os.path.expanduser("~/.config/claude/mcp_settings.json"),
        ]:
            if os.path.exists(path):
                config_path = path
                break

        if config_path:
            with open(config_path, 'r') as f:
                try:
                    config = json.load(f)
                except:
                    config = {}
        else:
            config_path = os.path.expanduser("~/.claude/.mcp.json")
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            config = {}

        mcp_servers = config.get("mcpServers", {})
        mcp_servers["api-auto-test-mcp"] = mcp_config
        config["mcpServers"] = mcp_servers

        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)

        print(f"已配置 MCP 服务器到: {config_path}")
        print(f"配置内容: {json.dumps(mcp_config, indent=2)}")
        print("\n请重启 Claude Code 以加载新的 MCP 服务器")
        return

    # 默认运行 stdio 模式 (MCP 协议)
    mcp.run("stdio")


if __name__ == "__main__":
    main()
