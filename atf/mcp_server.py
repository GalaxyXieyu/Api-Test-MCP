from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Literal

import yaml
from mcp.server import FastMCP
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from atf.case_generator import CaseGenerator
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


def _expected_py_path(yaml_full_path: Path, testcase_name: str) -> tuple[Path, str]:
    relative_to_tests = yaml_full_path.relative_to(TESTS_ROOT)
    directory_path = relative_to_tests.parent
    py_filename = f"test_{testcase_name}.py"
    py_full_path = (TEST_CASES_ROOT / directory_path / py_filename).resolve(strict=False)
    py_relative_path = py_full_path.relative_to(REPO_ROOT).as_posix()
    return py_full_path, py_relative_path


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
    description="列出 tests 目录下的 YAML 测试用例文件，可指定子目录。",
)
def list_testcases(root_path: str | None = None) -> ListTestcasesResponse:
    try:
        base_dir = _resolve_tests_root(root_path)
        testcases = sorted(
            path.relative_to(REPO_ROOT).as_posix()
            for path in base_dir.rglob("*.yaml")
        )
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
) -> ReadTestcaseResponse:
    try:
        yaml_full_path, yaml_relative_path = _resolve_yaml_path(yaml_path)
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
def validate_testcase(yaml_path: str) -> ValidateTestcaseResponse:
    errors: list[str] = []
    try:
        yaml_full_path, _ = _resolve_yaml_path(yaml_path)
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
) -> RegenerateResponse:
    try:
        os.chdir(REPO_ROOT)
        yaml_full_path, yaml_relative_path = _resolve_yaml_path(yaml_path)
        if not yaml_full_path.exists():
            raise ValueError("YAML 文件不存在")
        testcase_model = _parse_testcase_input(_load_yaml_file(yaml_full_path))
        py_full_path, py_relative_path = _expected_py_path(
            yaml_full_path=yaml_full_path,
            testcase_name=testcase_model.name,
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
) -> DeleteTestcaseResponse:
    deleted_files: list[str] = []
    try:
        yaml_full_path, yaml_relative_path = _resolve_yaml_path(yaml_path)
        if not yaml_full_path.exists():
            raise ValueError("YAML 文件不存在")
        testcase_model = _parse_testcase_input(_load_yaml_file(yaml_full_path))
        py_full_path, py_relative_path = _expected_py_path(
            yaml_full_path=yaml_full_path,
            testcase_name=testcase_model.name,
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
) -> GenerateResponse:
    try:
        os.chdir(REPO_ROOT)
        testcase_model = _parse_testcase_input(testcase)
        yaml_full_path, yaml_relative_path = _resolve_yaml_path(yaml_path)
        py_full_path, py_relative_path = _expected_py_path(
            yaml_full_path=yaml_full_path,
            testcase_name=testcase_model.name,
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


if __name__ == "__main__":
    mcp.run("stdio")
