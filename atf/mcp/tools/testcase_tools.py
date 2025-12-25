"""
Testcase CRUD Tools
测试用例读写工具
"""

from typing import Literal

from mcp.server.fastmcp import FastMCP
from pydantic import ValidationError

from atf.case_generator import CaseGenerator
from atf.core.log_manager import log
from atf.mcp.models import (
    GenerateResponse,
    ListTestcasesResponse,
    ReadTestcaseResponse,
    RegenerateResponse,
    DeleteTestcaseResponse,
    TestcaseModel,
    ValidateTestcaseResponse,
)
from atf.mcp.utils import (
    build_testcase_summary,
    build_testcase_yaml,
    format_validation_error,
    load_yaml_file,
    parse_testcase_input,
    resolve_tests_root,
    resolve_yaml_path,
    expected_py_path,
    yaml,
)


def register_testcase_tools(mcp: FastMCP) -> None:
    """注册测试用例相关工具"""

    @mcp.tool(
        name="list_testcases",
        title="列出测试用例 YAML",
        description="列出指定目录下的 YAML 测试用例文件，支持以下类型：\n\n"
        "- **集成测试 (testcase)**: API 接口测试，YAML 顶层为 `testcase`\n"
        "- **单元测试 (unittest)**: 单元测试，YAML 顶层为 `unittest`\n\n"
        "**参数说明**:\n"
        "- `root_path`: 可选，指定扫描目录，默认扫描 workspace/tests\n"
        "- `test_type`: `all`(全部) | `integration`(集成) | `unit`(单元)\n"
        "- `workspace`: **必须**，指定项目根目录\n\n"
        "示例:\n"
        "```json\n"
        "{\n"
        "  \"root_path\": \"tests\",\n"
        "  \"test_type\": \"integration\",\n"
        "  \"workspace\": \"/Volumes/DATABASE/code/glam-cart/backend\"\n"
        "}\n"
        "```",
    )
    def list_testcases(
        root_path: str | None = None,
        test_type: Literal["all", "integration", "unit"] = "all",
        workspace: str | None = None,
    ) -> ListTestcasesResponse:
        try:
            base_dir, repo_root = resolve_tests_root(root_path, workspace)
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
                        data = load_yaml_file(path)
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
            return ListTestcasesResponse(
                status="error",
                testcases=[],
                error_message=f"未知错误: {type(exc).__name__}: {str(exc)}",
                error_details={"error_type": "unknown_error", "exception_type": type(exc).__name__},
            )

    @mcp.tool(
        name="read_testcase",
        title="读取测试用例内容",
        description="读取指定 YAML 测试用例内容，返回摘要或完整结构。\n\n"
        "**参数说明**:\n"
        "- `yaml_path`: YAML 文件路径（相对于 workspace）\n"
        "- `mode`: `summary`(摘要，只返回 name/steps/teardowns) | `full`(完整，返回原始 YAML)\n"
        "- `workspace`: **必须**，指定项目根目录\n\n"
        "示例:\n"
        "```json\n"
        "{\n"
        "  \"yaml_path\": \"tests/auth_integration.yaml\",\n"
        "  \"mode\": \"summary\",\n"
        "  \"workspace\": \"/Volumes/DATABASE/code/glam-cart/backend\"\n"
        "}\n"
        "```",
    )
    def read_testcase(
        yaml_path: str,
        mode: Literal["summary", "full"] = "summary",
        workspace: str | None = None,
    ) -> ReadTestcaseResponse:
        try:
            yaml_full_path, yaml_relative_path, _ = resolve_yaml_path(yaml_path, workspace)
            raw_data = load_yaml_file(yaml_full_path)
            if mode == "full":
                return ReadTestcaseResponse(
                    status="ok",
                    yaml_path=yaml_relative_path,
                    mode=mode,
                    testcase=raw_data,
                )
            testcase_model = parse_testcase_input(raw_data)
            summary = build_testcase_summary(testcase_model)
            return ReadTestcaseResponse(
                status="ok",
                yaml_path=yaml_relative_path,
                mode=mode,
                testcase=summary,
            )
        except ValidationError as exc:
            log.error(f"MCP 读取测试用例参数验证失败: {exc}")
            return ReadTestcaseResponse(
                status="error",
                yaml_path=yaml_path,
                mode=mode,
                testcase=None,
                error_message=f"参数验证失败: {exc}",
                error_details={"error_type": "validation_error", "details": format_validation_error(exc)},
            )
        except Exception as exc:
            log.error(f"MCP 读取测试用例失败: {exc}")
            return ReadTestcaseResponse(
                status="error",
                yaml_path=yaml_path,
                mode=mode,
                testcase=None,
                error_message=f"未知错误: {type(exc).__name__}: {str(exc)}",
                error_details={"error_type": "unknown_error", "exception_type": type(exc).__name__},
            )

    @mcp.tool(
        name="validate_testcase",
        title="校验测试用例结构",
        description="校验指定 YAML 测试用例结构是否符合规范，返回错误列表。\n\n"
        "**参数说明**:\n"
        "- `yaml_path`: YAML 文件路径（相对于 workspace）\n"
        "- `workspace`: **必须**，指定项目根目录\n\n"
        "**返回值**:\n"
        "- `status: ok`: 校验通过\n"
        "- `status: error`: 校验失败，errors 数组包含具体错误信息\n\n"
        "示例:\n"
        "```json\n"
        "{\n"
        "  \"yaml_path\": \"tests/auth_integration.yaml\",\n"
        "  \"workspace\": \"/Volumes/DATABASE/code/glam-cart/backend\"\n"
        "}\n"
        "```",
    )
    def validate_testcase(
        yaml_path: str,
        workspace: str | None = None,
    ) -> ValidateTestcaseResponse:
        errors: list[str] = []
        try:
            yaml_full_path, _, _ = resolve_yaml_path(yaml_path, workspace)
            raw_data = load_yaml_file(yaml_full_path)
            parse_testcase_input(raw_data)
        except ValidationError as exc:
            errors = format_validation_error(exc)
        except Exception as exc:
            errors = [str(exc)]

        if errors:
            log.error(f"MCP 校验测试用例失败: {errors}")
            return ValidateTestcaseResponse(status="error", errors=errors)
        return ValidateTestcaseResponse(status="ok", errors=[])

    @mcp.tool(
        name="write_testcase",
        title="写入测试用例并生成 pytest 脚本",
        description="根据输入的测试用例结构写入 YAML 文件，并生成对应的 pytest 用例脚本。\n\n"
        "**重要**: 必须传递 `workspace` 参数指定项目根目录，否则默认使用 api-auto-test 仓库。\n\n"
        "**testcase 格式说明**:\n"
        "```json\n"
        "{\n"
        "  \"name\": \"测试用例名称\",\n"
        "  \"description\": \"可选描述\",\n"
        "  \"steps\": [\n"
        "    {\n"
        "      \"id\": \"步骤唯一标识\",\n"
        "      \"method\": \"GET|POST|PUT|DELETE|PATCH\",\n"
        "      \"path\": \"/api/users\",\n"
        "      \"data\": {\"key\": \"value\"},  // POST/PUT 请求体\n"
        "      \"headers\": {\"Authorization\": \"Bearer token\"},  // 可选请求头\n"
        "      \"assert\": [\n"
        "        {\"type\": \"status_code\", \"expected\": 200},\n"
        "        {\"type\": \"equals\", \"field\": \"data.id\", \"expected\": 1},\n"
        "        {\"type\": \"contains\", \"field\": \"data.name\", \"expected\": \"John\"},\n"
        "        {\"type\": \"length\", \"field\": \"data\", \"expected\": 10}\n"
        "      ]\n"
        "    }\n"
        "  ]\n"
        "}\n"
        "```\n\n"
        "**assert.type 支持的断言类型**:\n"
        "- `status_code`: 状态码断言，expected 为数字如 200, 201, 401, 404\n"
        "- `equals`: 精确匹配，field 为响应字段路径，expected 为期望值\n"
        "- `not_equals`: 不匹配，field 为响应字段路径，expected 为不期望的值\n"
        "- `contains`: 包含，field 为响应字段路径，expected 为期望包含的值\n"
        "- `length`: 长度断言，field 为响应字段路径，expected 为期望长度\n\n"
        "**变量引用**: 支持使用 `{{上一个步骤id.response.字段路径}}` 引用前序响应数据",
    )
    def write_testcase(
        yaml_path: str,
        testcase: TestcaseModel | dict | str,
        overwrite: bool = False,
        workspace: str | None = None,
    ) -> GenerateResponse:
        try:
            testcase_model = parse_testcase_input(testcase)
            yaml_full_path, yaml_relative_path, repo_root = resolve_yaml_path(yaml_path, workspace)

            # 检查路径是否存在
            if not repo_root.exists() or not repo_root.is_dir():
                raise ValueError(f"工作目录不存在: {repo_root}")

            py_full_path, py_relative_path = expected_py_path(
                yaml_full_path=yaml_full_path,
                testcase_name=testcase_model.name,
                workspace=workspace,
            )

            if yaml_full_path.exists() and not overwrite:
                raise ValueError("YAML 文件已存在，未开启覆盖写入")
            if py_full_path.exists() and not overwrite:
                raise ValueError("pytest 文件已存在，未开启覆盖写入")

            yaml_full_path.parent.mkdir(parents=True, exist_ok=True)
            test_data = build_testcase_yaml(testcase_model)
            with yaml_full_path.open("w", encoding="utf-8") as file:
                yaml.safe_dump(test_data, file, allow_unicode=True, sort_keys=False)

            if overwrite and py_full_path.exists():
                py_full_path.unlink()

            # 使用 repo_root 作为 base_dir，确保 CaseGenerator 能正确计算相对路径
            base_dir = str(repo_root)

            CaseGenerator().generate_test_cases(
                project_yaml_list=[yaml_relative_path],
                base_dir=base_dir
            )
            if not py_full_path.exists():
                raise ValueError("pytest 文件未生成，请检查测试用例数据格式")

            return GenerateResponse(status="ok", written_files=[yaml_relative_path, py_relative_path])
        except ValidationError as exc:
            log.error(f"MCP 写入测试用例参数验证失败: {exc}")
            error_details = {
                "error_type": "validation_error",
                "message": "参数格式错误，请检查以下字段：",
                "details": format_validation_error(exc),
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

    @mcp.tool(
        name="regenerate_py",
        title="重新生成 pytest 文件",
        description="根据已存在的 YAML 测试用例重新生成 pytest 脚本。\n\n"
        "**使用场景**:\n"
        "- YAML 文件已存在但 py 脚本丢失或损坏\n"
        "- 修改了 YAML 需要重新生成对应的 pytest 脚本\n\n"
        "**参数说明**:\n"
        "- `yaml_path`: YAML 文件路径（相对于 workspace）\n"
        "- `overwrite`: 默认 true，覆盖已存在的 py 文件\n"
        "- `workspace`: **必须**，指定项目根目录\n\n"
        "示例:\n"
        "```json\n"
        "{\n"
        "  \"yaml_path\": \"tests/auth_integration.yaml\",\n"
        "  \"overwrite\": true,\n"
        "  \"workspace\": \"/Volumes/DATABASE/code/glam-cart/backend\"\n"
        "}\n"
        "```",
    )
    def regenerate_py(
        yaml_path: str,
        overwrite: bool = True,
        workspace: str | None = None,
    ) -> RegenerateResponse:
        try:
            yaml_full_path, yaml_relative_path, repo_root = resolve_yaml_path(yaml_path, workspace)
            if not yaml_full_path.exists():
                raise ValueError(f"YAML 文件不存在: {yaml_relative_path}")
            raw_data = load_yaml_file(yaml_full_path)
            testcase_model = parse_testcase_input(raw_data)
            py_full_path, py_relative_path = expected_py_path(
                yaml_full_path=yaml_full_path,
                testcase_name=testcase_model.name,
                workspace=workspace,
            )
            if overwrite and py_full_path.exists():
                py_full_path.unlink()
            CaseGenerator().generate_test_cases(project_yaml_list=[yaml_relative_path])
            if not py_full_path.exists():
                raise ValueError("pytest 文件未生成，请检查测试用例数据格式是否正确")
            return RegenerateResponse(
                status="ok",
                written_files=[yaml_relative_path, py_relative_path],
            )
        except ValidationError as exc:
            log.error(f"MCP 重新生成 pytest 参数验证失败: {exc}")
            return RegenerateResponse(
                status="error",
                written_files=[],
                error_message=f"参数验证失败: {exc}",
                error_details={"error_type": "validation_error", "details": format_validation_error(exc)},
            )
        except ValueError as exc:
            log.error(f"MCP 重新生成 pytest 业务验证失败: {exc}")
            return RegenerateResponse(
                status="error",
                written_files=[],
                error_message=str(exc),
                error_details={"error_type": "value_error", "message": str(exc)},
            )
        except Exception as exc:
            log.error(f"MCP 重新生成 pytest 失败: {exc}")
            return RegenerateResponse(
                status="error",
                written_files=[],
                error_message=f"未知错误: {type(exc).__name__}: {str(exc)}",
                error_details={"error_type": "unknown_error", "exception_type": type(exc).__name__},
            )

    @mcp.tool(
        name="delete_testcase",
        title="删除测试用例",
        description="删除 YAML 与对应的 pytest 文件。\n\n"
        "**注意**:\n"
        "- 删除操作不可恢复，请确认后再执行\n"
        "- 默认同时删除 YAML 和生成的 py 文件\n\n"
        "**参数说明**:\n"
        "- `yaml_path`: YAML 文件路径（相对于 workspace）\n"
        "- `delete_py`: 默认 true，同时删除对应的 py 文件\n"
        "- `workspace`: **必须**，指定项目根目录\n\n"
        "示例:\n"
        "```json\n"
        "{\n"
        "  \"yaml_path\": \"tests/auth_integration.yaml\",\n"
        "  \"delete_py\": true,\n"
        "  \"workspace\": \"/Volumes/DATABASE/code/glam-cart/backend\"\n"
        "}\n"
        "```",
    )
    def delete_testcase(
        yaml_path: str,
        delete_py: bool = True,
        workspace: str | None = None,
    ) -> DeleteTestcaseResponse:
        deleted_files: list[str] = []
        try:
            yaml_full_path, yaml_relative_path, _ = resolve_yaml_path(yaml_path, workspace)
            if not yaml_full_path.exists():
                raise ValueError(f"YAML 文件不存在: {yaml_relative_path}")
            raw_data = load_yaml_file(yaml_full_path)
            testcase_model = parse_testcase_input(raw_data)
            py_full_path, py_relative_path = expected_py_path(
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
        except ValidationError as exc:
            log.error(f"MCP 删除测试用例参数验证失败: {exc}")
            return DeleteTestcaseResponse(
                status="error",
                deleted_files=[],
                error_message=f"参数验证失败: {exc}",
                error_details={"error_type": "validation_error", "details": format_validation_error(exc)},
            )
        except ValueError as exc:
            log.error(f"MCP 删除测试用例业务验证失败: {exc}")
            return DeleteTestcaseResponse(
                status="error",
                deleted_files=[],
                error_message=str(exc),
                error_details={"error_type": "value_error", "message": str(exc)},
            )
        except Exception as exc:
            log.error(f"MCP 删除测试用例失败: {exc}")
            return DeleteTestcaseResponse(
                status="error",
                deleted_files=[],
                error_message=f"未知错误: {type(exc).__name__}: {str(exc)}",
                error_details={"error_type": "unknown_error", "exception_type": type(exc).__name__},
            )
