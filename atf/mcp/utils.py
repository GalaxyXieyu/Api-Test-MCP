"""
MCP Server Utilities
工具函数集合
"""

import json
import os
from pathlib import Path
from typing import Any, Literal

import yaml as _yaml
from pydantic import ValidationError

from atf.core.log_manager import log
from atf.mcp.models import (
    TestcaseModel,
    UnitTestModel,
)

# 统一导出 yaml 模块，供其他模块使用
yaml = _yaml

# ==================== 常量定义 ====================
REPO_ROOT = Path(os.getenv("ATF_REPO_ROOT", Path(__file__).resolve().parent.parent.parent))
TESTS_ROOT = REPO_ROOT / "tests"
TEST_CASES_ROOT = REPO_ROOT / "test_cases"

# pytest 执行常量
PYTEST_TIMEOUT = 300  # 5分钟超时
MAX_ERROR_LENGTH = 500  # 错误信息最大长度
MAX_HISTORY_SIZE = 1000  # 历史记录最大条数


def get_roots(workspace: str | None = None) -> tuple[Path, Path, Path]:
    """根据 workspace 参数返回 (repo_root, tests_root, test_cases_root)"""
    if workspace:
        repo = Path(workspace).resolve(strict=False)
    else:
        repo = REPO_ROOT
    return repo, repo / "tests", repo / "test_cases"


def resolve_yaml_path(
    yaml_path: str, workspace: str | None = None
) -> tuple[Path, str, Path]:
    """返回 (yaml_full_path, yaml_relative_path, repo_root)"""
    repo_root, tests_root, _ = get_roots(workspace)
    raw_path = Path(yaml_path)
    if raw_path.is_absolute():
        normalized = raw_path.resolve(strict=False)
    else:
        normalized = (repo_root / raw_path).resolve(strict=False)
    if not normalized.name.endswith(".yaml"):
        raise ValueError("yaml_path 必须以 .yaml 结尾")
    # 支持任意路径，不限制必须在 tests 目录下
    if not normalized.is_relative_to(repo_root):
        raise ValueError(f"yaml_path 必须在项目目录 {repo_root} 下")
    relative_path = normalized.relative_to(repo_root).as_posix()
    return normalized, relative_path, repo_root


def resolve_tests_root(
    root_path: str | None = None, workspace: str | None = None
) -> tuple[Path, Path]:
    """返回 (resolved_tests_root, repo_root)"""
    repo_root, tests_root, _ = get_roots(workspace)
    tests_root_resolved = tests_root.resolve(strict=False)
    if not root_path:
        return tests_root_resolved, repo_root
    raw_path = Path(root_path)
    if raw_path.is_absolute():
        normalized = raw_path.resolve(strict=False)
    else:
        normalized = (repo_root / raw_path).resolve(strict=False)
    # 支持任意路径，不限制必须在 tests 目录下
    if not normalized.is_relative_to(repo_root):
        raise ValueError(f"root_path 必须在项目目录 {repo_root} 下")
    if not normalized.exists() or not normalized.is_dir():
        raise ValueError("root_path 必须是已存在的目录")
    return normalized, repo_root


def expected_py_path(
    yaml_full_path: Path, testcase_name: str, workspace: str | None = None
) -> tuple[Path, str]:
    """返回 (py_full_path, py_relative_path)"""
    _, tests_root, test_cases_root = get_roots(workspace)
    repo_root = tests_root.parent

    # 计算 directory_path：YAML 文件相对于 repo_root 的父目录
    # 例如：tests/integration_auth.yaml → directory_path = "tests"
    if yaml_full_path.is_relative_to(tests_root):
        # YAML 在 tests 目录下，使用 tests 下的相对路径
        relative_to_tests = yaml_full_path.relative_to(tests_root)
        directory_path = relative_to_tests.parent
        # 如果 relative_to_tests 只有一层（如 tests/foo.yaml），parent 是 Path('.')
        if str(directory_path) == '.':
            directory_path = tests_root.name  # 使用 tests 作为目录名
        else:
            directory_path = Path(tests_root.name) / directory_path
    else:
        # YAML 不在 tests 目录下
        relative_to_repo = yaml_full_path.relative_to(repo_root)
        directory_path = relative_to_repo.parent

    py_filename = f"test_{testcase_name}.py"
    py_full_path = (test_cases_root / directory_path / py_filename).resolve(strict=False)
    py_relative_path = py_full_path.relative_to(repo_root).as_posix()
    return py_full_path, py_relative_path


def load_yaml_file(path: Path) -> dict[str, Any]:
    """加载 YAML 文件"""
    if not path.exists():
        raise ValueError("YAML 文件不存在")
    with path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)
    if data is None:
        raise ValueError("YAML 文件内容为空")
    if not isinstance(data, dict):
        raise ValueError("YAML 顶层必须是对象")
    return data


def build_testcase_yaml(testcase: TestcaseModel) -> dict[str, Any]:
    """构建测试用例 YAML 数据"""
    payload = testcase.model_dump(by_alias=True, exclude_none=True)
    return {"testcase": payload}


def build_unittest_yaml(unittest: UnitTestModel) -> dict[str, Any]:
    """构建单元测试 YAML 数据"""
    payload = unittest.model_dump(by_alias=True, exclude_none=True)
    return {"unittest": payload}


def parse_testcase_input(raw_testcase: Any) -> TestcaseModel:
    """解析测试用例输入"""
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


def parse_unittest_input(raw_unittest: Any) -> UnitTestModel:
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


def build_testcase_summary(testcase: TestcaseModel) -> dict[str, Any]:
    """构建测试用例摘要"""
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


def format_validation_error(exc: ValidationError) -> list[str]:
    """格式化 Pydantic 验证错误"""
    return [
        f"{'.'.join(str(l) for l in err['loc'])}: {err['msg']} (类型: {err.get('type', 'unknown')})"
        for err in exc.errors()
    ]


def detect_testcase_type(data: dict) -> Literal["unittest", "testcase"]:
    """检测测试用例类型"""
    if "unittest" in data:
        return "unittest"
    elif "testcase" in data:
        return "testcase"
    raise ValueError("未知的测试用例格式: YAML 文件既不是 unittest 也不是 testcase 格式")


def truncate_text(text: str, max_length: int = MAX_ERROR_LENGTH) -> str:
    """截断文本到指定长度"""
    if not text:
        return ""
    return text[-max_length:] if len(text) > max_length else text


__all__ = [
    "REPO_ROOT",
    "TESTS_ROOT",
    "TEST_CASES_ROOT",
    "PYTEST_TIMEOUT",
    "MAX_ERROR_LENGTH",
    "MAX_HISTORY_SIZE",
    "yaml",
    "get_roots",
    "resolve_yaml_path",
    "resolve_tests_root",
    "expected_py_path",
    "load_yaml_file",
    "build_testcase_yaml",
    "build_unittest_yaml",
    "parse_testcase_input",
    "parse_unittest_input",
    "build_testcase_summary",
    "format_validation_error",
    "detect_testcase_type",
    "truncate_text",
]
