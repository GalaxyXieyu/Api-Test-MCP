"""
Unittest Tools
单元测试工具
"""

from mcp.server.fastmcp import FastMCP
from pydantic import ValidationError

from atf.core.log_manager import log
from atf.mcp.models import GenerateResponse, UnitTestModel
from atf.mcp.tools.testcase_tools import format_validation_error
from atf.unit_case_generator import UnitCaseGenerator
from atf.mcp.utils import (
    build_unittest_yaml,
    expected_py_path,
    parse_unittest_input,
    resolve_yaml_path,
    yaml,
)


def register_unittest_tools(mcp: FastMCP) -> None:
    """注册单元测试工具"""

    @mcp.tool(
        name="write_unittest",
        title="写入单元测试用例并生成 pytest 脚本",
        description="根据输入的单元测试结构写入 YAML 文件，并生成对应的 pytest 单元测试脚本。\n\n"
        "**重要**: 必须传递 `workspace` 参数指定项目根目录，否则默认使用 api-auto-test 仓库。\n\n"
        "**unittest 格式说明**:\n"
        "```json\n"
        "{\n"
        "  \"name\": \"UserService 测试\",\n"
        "  \"target\": {\n"
        "    \"module\": \"app.services.user_service\",\n"
        "    \"class\": \"UserService\",  // 可选，测试类\n"
        "    \"function\": \"get_user\"   // 可选，测试函数\n"
        "  },\n"
        "  \"fixtures\": {\n"
        "    \"setup\": [{\"type\": \"patch\", \"target\": \"app.services.user_service.UserRepository\", \"return_value\": {\"id\": 1, \"name\": \"test\"}}],\n"
        "    \"teardown\": []\n"
        "  },\n"
        "  \"cases\": [\n"
        "    {\n"
        "      \"id\": \"test_get_user_success\",\n"
        "      \"description\": \"测试获取用户成功\",\n"
        "      \"inputs\": {\"args\": [1], \"kwargs\": {}},\n"
        "      \"assert\": [\n"
        "        {\"type\": \"equals\", \"field\": \"result.id\", \"expected\": 1},\n"
        "        {\"type\": \"equals\", \"field\": \"result.name\", \"expected\": \"test\"}\n"
        "      ]\n"
        "    }\n"
        "  ]\n"
        "}\n"
        "```\n\n"
        "**assert.type 支持的断言类型**:\n"
        "- `equals`: 精确匹配\n"
        "- `not_equals`: 不匹配\n"
        "- `contains`: 包含\n"
        "- `raises`: 期望抛出异常，exception 字段指定异常类型\n"
        "- `is_none`: 结果为 None\n"
        "- `is_not_none`: 结果不为 None\n"
        "- `called_once`: mock 被调用一次\n"
        "- `called_with`: mock 被特定参数调用",
    )
    def write_unittest(
        yaml_path: str,
        unittest: UnitTestModel | dict | str,
        overwrite: bool = False,
        workspace: str | None = None,
    ) -> GenerateResponse:
        try:
            unittest_model = parse_unittest_input(unittest)
            yaml_full_path, yaml_relative_path, repo_root = resolve_yaml_path(yaml_path, workspace)

            # 检查路径是否存在
            if not repo_root.exists() or not repo_root.is_dir():
                raise ValueError(f"工作目录不存在: {repo_root}")

            py_full_path, py_relative_path = expected_py_path(
                yaml_full_path=yaml_full_path,
                testcase_name=unittest_model.name,
                workspace=workspace,
            )

            if yaml_full_path.exists() and not overwrite:
                raise ValueError("YAML 文件已存在，未开启覆盖写入")
            if py_full_path.exists() and not overwrite:
                raise ValueError("pytest 文件已存在，未开启覆盖写入")

            yaml_full_path.parent.mkdir(parents=True, exist_ok=True)
            test_data = build_unittest_yaml(unittest_model)
            with yaml_full_path.open("w", encoding="utf-8") as file:
                yaml.safe_dump(test_data, file, allow_unicode=True, sort_keys=False)

            if overwrite and py_full_path.exists():
                py_full_path.unlink()

            result = UnitCaseGenerator().generate_unit_tests(yaml_relative_path)
            if not result:
                raise ValueError("pytest 文件未生成，请检查单元测试数据格式")

            return GenerateResponse(status="ok", written_files=[yaml_relative_path, py_relative_path])
        except ValidationError as exc:
            log.error(f"MCP 写入单元测试参数验证失败: {exc}")
            error_details = {
                "error_type": "validation_error",
                "message": "参数格式错误，请检查以下字段：",
                "details": format_validation_error(exc),
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
