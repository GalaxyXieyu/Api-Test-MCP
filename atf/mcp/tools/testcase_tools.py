"""
Testcase CRUD Tools
测试用例读写工具
"""

import time
from pathlib import Path
from typing import Any, Literal

from mcp.server.fastmcp import FastMCP
from pydantic import ValidationError

from atf.case_generator import CaseGenerator
from atf.core.log_manager import log
from atf.mcp.models import (
    GenerateResponse,
    GetTestcaseResponse,
    ListTestcasesResponse,
    ReadTestcaseResponse,
    DeleteTestcaseResponse,
    TestcaseModel,
    ValidateTestcaseResponse,
)
from atf.mcp.utils import (
    build_testcase_summary,
    build_testcase_yaml,
    build_error_payload,
    contains_chinese,
    format_validation_error,
    load_yaml_file,
    log_tool_call,
    new_request_id,
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
        "【给 AI 助手的强制规则】\n"
        "- 只要用户想“创建/修改/生成用例”，不要在对话里手写完整 YAML 作为最终结果；应调用 `write_testcase` 写入到 `tests/cases/` 并生成 `tests/scripts/` 脚本。\n"
        "- 当你不确定 YAML 是否存在时，优先调用本工具列出用例，再决定是更新还是新建。\n\n"
        "示例:\n"
        "```json\n"
        "{\n"
        "  \"root_path\": \"tests/cases\",\n"
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
        request_id = new_request_id()
        start_time = time.perf_counter()
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

            response = ListTestcasesResponse(
                status="ok",
                request_id=request_id,
                testcases=testcases,
            )
        except ValueError as exc:
            log.error(f"MCP 列出测试用例参数验证失败: {exc}")
            payload = build_error_payload(
                code="MCP_INVALID_PATH",
                message=str(exc),
                retryable=False,
                details={"error_type": "value_error"},
            )
            response = ListTestcasesResponse(
                status="error",
                request_id=request_id,
                testcases=[],
                **payload,
            )
        except Exception as exc:
            log.error(f"MCP 列出测试用例失败: {exc}")
            payload = build_error_payload(
                code="MCP_LIST_TESTCASES_ERROR",
                message=f"未知错误: {type(exc).__name__}: {str(exc)}",
                retryable=False,
                details={"error_type": "unknown_error", "exception_type": type(exc).__name__},
            )
            response = ListTestcasesResponse(
                status="error",
                request_id=request_id,
                testcases=[],
                **payload,
            )
        latency_ms = int((time.perf_counter() - start_time) * 1000)
        log_tool_call(
            "list_testcases",
            request_id,
            response.status,
            latency_ms,
            response.error_code,
            meta={"root_path": root_path, "test_type": test_type},
        )
        return response

    @mcp.tool(
        name="get_testcase",
        title="获取测试用例",
        description="获取指定 YAML 测试用例内容，同时返回校验结果（整合读取 + 校验）。\n\n"
        "**功能特点**:\n"
        "- 读取测试用例内容（摘要或完整）\n"
        "- 自动校验用例结构是否规范\n"
        "- 返回内容与校验状态，一次调用获取全部信息\n\n"
        "**参数说明**:\n"
        "- `yaml_path`: YAML 文件路径（相对于 workspace）\n"
        "- `mode`: `summary`(摘要，只返回 name/steps/teardowns) | `full`(完整，返回原始 YAML)\n"
        "- `workspace`: **必须**，指定项目根目录\n\n"
        "**返回值说明**:\n"
        "- `is_valid`: 是否通过校验\n"
        "- `errors`: 校验错误列表（空数组表示通过）\n\n"
        "【给 AI 助手的强制规则】\n"
        "- 当用户要“修改现有用例”时，必须先调用本工具读取（建议 mode=summary）确认现状，再调用 `write_testcase` 覆盖写入；不要凭空臆造现有 YAML。\n"
        "- 除非用户明确要求展示完整 YAML，否则优先用 summary，避免在对话中输出大段 YAML。\n\n"
        "示例:\n"
        "```json\n"
        "{\n"
        "  \"yaml_path\": \"tests/cases/auth_integration.yaml\",\n"
        "  \"mode\": \"summary\",\n"
        "  \"workspace\": \"/Volumes/DATABASE/code/glam-cart/backend\"\n"
        "}\n"
        "```",
    )
    def get_testcase(
        yaml_path: str,
        mode: Literal["summary", "full"] = "summary",
        workspace: str | None = None,
    ) -> GetTestcaseResponse:
        """获取测试用例内容并校验结构"""
        validation_errors: list[str] = []
        testcase_content: dict[str, Any] | None = None
        request_id = new_request_id()
        start_time = time.perf_counter()

        try:
            yaml_full_path, yaml_relative_path, _ = resolve_yaml_path(yaml_path, workspace)
            raw_data = load_yaml_file(yaml_full_path)

            # 尝试解析和校验
            try:
                testcase_model = parse_testcase_input(raw_data)
                if mode == "summary":
                    testcase_content = build_testcase_summary(testcase_model)
                else:
                    testcase_content = raw_data
                validation_errors = []
                is_valid = True
            except ValidationError as exc:
                validation_errors = format_validation_error(exc)
                is_valid = False
                if mode == "summary":
                    testcase_content = None
                else:
                    testcase_content = raw_data

            response = GetTestcaseResponse(
                status="ok" if is_valid else "error",
                request_id=request_id,
                yaml_path=yaml_relative_path,
                mode=mode,
                testcase=testcase_content,
                is_valid=is_valid,
                errors=validation_errors,
                error_code=None if is_valid else "MCP_TESTCASE_INVALID",
                retryable=False if not is_valid else None,
            )

        except ValidationError as exc:
            log.error(f"MCP 获取测试用例参数验证失败: {exc}")
            payload = build_error_payload(
                code="MCP_VALIDATION_ERROR",
                message=f"参数验证失败: {exc}",
                retryable=False,
                details={"error_type": "validation_error", "details": format_validation_error(exc)},
            )
            response = GetTestcaseResponse(
                status="error",
                request_id=request_id,
                yaml_path=yaml_path,
                mode=mode,
                testcase=None,
                is_valid=False,
                errors=format_validation_error(exc),
                **payload,
            )
        except Exception as exc:
            log.error(f"MCP 获取测试用例失败: {exc}")
            payload = build_error_payload(
                code="MCP_GET_TESTCASE_ERROR",
                message=f"未知错误: {type(exc).__name__}: {str(exc)}",
                retryable=False,
                details={"error_type": "unknown_error", "exception_type": type(exc).__name__},
            )
            response = GetTestcaseResponse(
                status="error",
                request_id=request_id,
                yaml_path=yaml_path,
                mode=mode,
                testcase=None,
                is_valid=False,
                errors=[str(exc)],
                **payload,
            )
        latency_ms = int((time.perf_counter() - start_time) * 1000)
        log_tool_call(
            "get_testcase",
            request_id,
            response.status,
            latency_ms,
            response.error_code,
            meta={"yaml_path": yaml_path, "mode": mode},
        )
        return response

    @mcp.tool(
        name="write_testcase",
        title="写入/生成测试用例",
        description="写入 YAML 测试用例并生成 pytest 脚本，或仅重新生成已存在 YAML 对应的 pytest 脚本。\n\n"
        "【给 AI 助手的强制规则（非常重要）】\n"
        "- 只要用户的意图是“创建/修改/生成 YAML 用例”，你必须调用本工具完成落盘与脚本生成；不要在对话里直接手写完整 YAML 作为最终交付物。\n"
        "- 只有当工具不可用/调用失败，或用户明确要求“只给 YAML 文本、不调用工具”时，才允许在对话里输出 YAML。\n"
        "- 每次调用都必须显式传 `workspace`（项目根目录）。\n\n"
        "**命名规范**:\n"
        "- `name` 字段**不能使用中文**，必须使用英文命名\n"
        "- `description` 字段可以使用中文描述\n\n"
        "**两种模式**:\n"
        "1. **写入模式**（传入 testcase）: 创建/更新 YAML 文件并生成 pytest 脚本\n"
        "2. **重新生成模式**（不传 testcase）: 仅基于已存在的 YAML 重新生成 pytest 脚本\n\n"
        "**重要提醒**:\n"
        "- 必须传递 `workspace` 参数指定项目根目录\n"
        "- **强烈建议**传入 `host` 参数指定 API 服务地址，否则需要配置全局变量\n\n"
        "**testcase 完整格式**:\n"
        "```json\n"
        "{\n"
        "  \"name\": \"test_user_login\",  // 必须使用英文，不能包含中文\n"
        "  \"description\": \"用户登录测试\",  // 描述可以使用中文\n"
        "  \"host\": \"http://localhost:8000\",\n"
        "  \"steps\": [\n"
        "    {\n"
        "      \"id\": \"step1\",\n"
        "      \"method\": \"POST\",\n"
        "      \"path\": \"/api/users/login\",\n"
        "      \"data\": {\"username\": \"testuser\", \"password\": \"testpass\"},\n"
        "      \"headers\": {\"Content-Type\": \"application/json\"},\n"
        "      \"assert\": [\n"
        "        {\"type\": \"status_code\", \"expected\": 200},\n"
        "        {\"type\": \"equals\", \"field\": \"data.code\", \"expected\": 0}\n"
        "      ]\n"
        "    }\n"
        "  ]\n"
        "}\n"
        "```\n\n"
        "**参数说明**:\n"
        "- `yaml_path`: YAML 文件路径（相对于 workspace），**必须**\n"
        "- `testcase`: 可选，测试用例数据，不传则仅重新生成 py\n"
        "- `overwrite`: 默认 true，覆盖已存在的文件\n"
        "- `dry_run`: 默认 false，设为 true 时仅预览生成的代码，不实际写入文件\n"
        "- `workspace`: **必须**，指定项目根目录\n\n"
        "**返回值增强**:\n"
        "- `name_mapping`: 名称转换信息 {original, safe, class}\n"
        "- `syntax_valid`: 生成代码是否通过语法校验\n"
        "- `syntax_errors`: 语法错误列表\n"
        "- `code_preview`: dry_run 模式下的代码预览\n\n"
        "**目录结构**:\n"
        "- YAML 文件保存在: `tests/cases/`\n"
        "- py 脚本生成在: `tests/scripts/`\n\n"
        "**示例**:\n"
        "```json\n"
        "# 写入 + 生成\n"
        "{\n"
        "  \"yaml_path\": \"tests/cases/auth_test.yaml\",\n"
        "  \"testcase\": {\n"
        "    \"name\": \"test_user_login\",\n"
        "    \"description\": \"用户登录测试\",\n"
        "    \"steps\": [...]\n"
        "  },\n"
        "  \"workspace\": \"/Volumes/DATABASE/code/glam-cart/backend\"\n"
        "}\n\n"
        "# 重新生成 py（当 YAML 已存在时）\n"
        "{\n"
        "  \"yaml_path\": \"tests/cases/auth_test.yaml\",\n"
        "  \"workspace\": \"/Volumes/DATABASE/code/glam-cart/backend\"\n"
        "}\n"
        "```\n\n"
        "**提示**: 如果测试用例需要访问特定的 API 服务器，请务必在 `host` 字段中填写完整地址（如 `http://localhost:8000`）。如果不指定 `host`，测试将依赖项目的全局环境配置。",
    )
    def write_testcase(
        yaml_path: str,
        testcase: TestcaseModel | dict | str | None = None,
        overwrite: bool = True,
        dry_run: bool = False,
        workspace: str | None = None,
    ) -> GenerateResponse:
        request_id = new_request_id()
        start_time = time.perf_counter()
        try:
            yaml_full_path, yaml_relative_path, repo_root = resolve_yaml_path(yaml_path, workspace)

            # 判断执行模式
            is_write_mode = testcase is not None

            if is_write_mode:
                # ========== 写入模式 ==========
                testcase_model = parse_testcase_input(testcase)

                # 验证 name 字段不能包含中文
                if contains_chinese(testcase_model.name):
                    raise ValueError(
                        f"测试用例 name 字段不能包含中文字符: '{testcase_model.name}'\n"
                        "请使用英文命名，例如: test_user_login, get_product_list"
                    )
            else:
                # ========== 重新生成模式 ==========
                if not yaml_full_path.exists():
                    raise ValueError(f"YAML 文件不存在: {yaml_relative_path}")
                yaml_data = load_yaml_file(yaml_full_path)
                testcase_model = parse_testcase_input(yaml_data)
                log.info(f"[MCP] 重新生成模式: 读取现有 YAML 文件")

            # 检查路径是否存在
            if not repo_root.exists() or not repo_root.is_dir():
                raise ValueError(f"工作目录不存在: {repo_root}")

            # 写入模式且非 dry_run：检查文件存在性
            if is_write_mode and not dry_run:
                if yaml_full_path.exists() and not overwrite:
                    raise ValueError("YAML 文件已存在，未开启覆盖写入")

            # 写入模式且非 dry_run：写入 YAML
            if is_write_mode and not dry_run:
                yaml_full_path.parent.mkdir(parents=True, exist_ok=True)
                test_data = build_testcase_yaml(testcase_model)
                with yaml_full_path.open("w", encoding="utf-8") as file:
                    yaml.safe_dump(test_data, file, allow_unicode=True, sort_keys=False)

            # base_dir 应该是 cases 目录，这样相对路径计算才正确
            base_dir = str(repo_root / "tests" / "cases")
            yaml_absolute_path = str(yaml_full_path)
            output_dir = str(repo_root / "tests" / "scripts")

            log.info(f"[MCP] write_testcase: mode={'写入' if is_write_mode else '重新生成'}, dry_run={dry_run}")

            # 使用新的 generate_single 方法
            result = CaseGenerator().generate_single(
                yaml_file=yaml_absolute_path,
                output_dir=output_dir,
                base_dir=base_dir,
                dry_run=dry_run
            )

            if not result["success"]:
                payload = build_error_payload(
                    code="MCP_GENERATION_FAILED",
                    message=str(result.get("error")),
                    retryable=False,
                    details={
                        "error_type": "generation_failed",
                        "name_mapping": result.get("name_mapping"),
                        "syntax_errors": result.get("syntax_errors"),
                    },
                )
                response = GenerateResponse(
                    status="error",
                    request_id=request_id,
                    written_files=[],
                    name_mapping=result.get("name_mapping"),
                    syntax_valid=result.get("syntax_valid"),
                    syntax_errors=result.get("syntax_errors"),
                    code_preview=result.get("code_preview"),
                    **payload,
                )
                latency_ms = int((time.perf_counter() - start_time) * 1000)
                log_tool_call(
                    "write_testcase",
                    request_id,
                    response.status,
                    latency_ms,
                    response.error_code,
                    meta={"yaml_path": yaml_path, "dry_run": dry_run},
                )
                return response

            py_relative_path = str(Path(result["file_path"]).relative_to(repo_root)) if result["file_path"] else None

            response = GenerateResponse(
                status="ok",
                request_id=request_id,
                written_files=[yaml_relative_path, py_relative_path] if not dry_run else [],
                name_mapping=result.get("name_mapping"),
                syntax_valid=result.get("syntax_valid"),
                syntax_errors=result.get("syntax_errors"),
                dry_run=dry_run,
                code_preview=result.get("code_preview") if dry_run else None
            )
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
            payload = build_error_payload(
                code="MCP_VALIDATION_ERROR",
                message=f"参数验证失败: {exc}",
                retryable=False,
                details=error_details,
            )
            response = GenerateResponse(
                status="error",
                request_id=request_id,
                written_files=[],
                **payload,
            )
        except ValueError as exc:
            log.error(f"MCP 写入测试用例业务验证失败: {exc}")
            payload = build_error_payload(
                code="MCP_VALUE_ERROR",
                message=str(exc),
                retryable=False,
                details={"error_type": "value_error", "message": str(exc)},
            )
            response = GenerateResponse(
                status="error",
                request_id=request_id,
                written_files=[],
                **payload,
            )
        except Exception as exc:
            log.error(f"MCP 写入测试用例失败: {exc}")
            payload = build_error_payload(
                code="MCP_WRITE_TESTCASE_ERROR",
                message=f"未知错误: {type(exc).__name__}: {str(exc)}",
                retryable=False,
                details={"error_type": "unknown_error", "exception_type": type(exc).__name__},
            )
            response = GenerateResponse(
                status="error",
                request_id=request_id,
                written_files=[],
                **payload,
            )
        latency_ms = int((time.perf_counter() - start_time) * 1000)
        log_tool_call(
            "write_testcase",
            request_id,
            response.status,
            latency_ms,
            response.error_code,
            meta={"yaml_path": yaml_path, "dry_run": dry_run},
        )
        return response

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
        "  \"yaml_path\": \"tests/cases/auth_integration.yaml\",\n"
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
        request_id = new_request_id()
        start_time = time.perf_counter()
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
            response = DeleteTestcaseResponse(
                status="ok",
                request_id=request_id,
                deleted_files=deleted_files,
            )
        except ValidationError as exc:
            log.error(f"MCP 删除测试用例参数验证失败: {exc}")
            payload = build_error_payload(
                code="MCP_VALIDATION_ERROR",
                message=f"参数验证失败: {exc}",
                retryable=False,
                details={"error_type": "validation_error", "details": format_validation_error(exc)},
            )
            response = DeleteTestcaseResponse(
                status="error",
                request_id=request_id,
                deleted_files=[],
                **payload,
            )
        except ValueError as exc:
            log.error(f"MCP 删除测试用例业务验证失败: {exc}")
            payload = build_error_payload(
                code="MCP_VALUE_ERROR",
                message=str(exc),
                retryable=False,
                details={"error_type": "value_error", "message": str(exc)},
            )
            response = DeleteTestcaseResponse(
                status="error",
                request_id=request_id,
                deleted_files=[],
                **payload,
            )
        except Exception as exc:
            log.error(f"MCP 删除测试用例失败: {exc}")
            payload = build_error_payload(
                code="MCP_DELETE_TESTCASE_ERROR",
                message=f"未知错误: {type(exc).__name__}: {str(exc)}",
                retryable=False,
                details={"error_type": "unknown_error", "exception_type": type(exc).__name__},
            )
            response = DeleteTestcaseResponse(
                status="error",
                request_id=request_id,
                deleted_files=[],
                **payload,
            )
        latency_ms = int((time.perf_counter() - start_time) * 1000)
        log_tool_call(
            "delete_testcase",
            request_id,
            response.status,
            latency_ms,
            response.error_code,
            meta={"yaml_path": yaml_path, "delete_py": delete_py},
        )
        return response
