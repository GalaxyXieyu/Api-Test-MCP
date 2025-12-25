from __future__ import annotations

import json
import os
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
    except Exception as exc:
        log.error(f"MCP 写入测试用例失败: {exc}")
        return GenerateResponse(status="error", written_files=[])


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
    except Exception as exc:
        log.error(f"MCP 写入单元测试失败: {exc}")
        return GenerateResponse(status="error", written_files=[])


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
