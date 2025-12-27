"""
API Auto Test MCP Server
MCP 服务器主入口

架构说明:
- mcp/models.py: 所有 Pydantic 数据模型
- mcp/utils.py: 工具函数
- mcp/executor.py: 测试执行逻辑
- mcp/tools/*.py: 各功能工具实现
"""

from __future__ import annotations

import argparse
import inspect
import json
import os
import sys

from mcp.server import FastMCP

from atf.core.log_manager import log
# 导入各工具注册函数
from atf.mcp.tools.health_tool import register_health_tool
from atf.mcp.tools.metrics_tools import register_metrics_tools
from atf.mcp.tools.testcase_tools import register_testcase_tools
from atf.mcp.tools.unittest_tools import register_unittest_tools
from atf.mcp.tools.runner_tools import register_runner_tools


# 创建 MCP 服务器实例
mcp = FastMCP(name="api-auto-test-mcp")


def register_all_tools() -> None:
    """注册所有 MCP 工具"""
    register_health_tool(mcp)
    register_metrics_tools(mcp)
    register_testcase_tools(mcp)
    register_unittest_tools(mcp)
    register_runner_tools(mcp)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="API Auto Test MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default=os.getenv("MCP_TRANSPORT", "stdio"),
        help="传输方式，默认 stdio",
    )
    parser.add_argument(
        "--host",
        default=os.getenv("MCP_HOST", "127.0.0.1"),
        help="SSE 监听地址（仅 sse 生效）",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("MCP_PORT", "8000")),
        help="SSE 监听端口（仅 sse 生效）",
    )
    parser.add_argument(
        "--sse-path",
        default=os.getenv("MCP_SSE_PATH", "/mcp"),
        help="SSE 路由路径（仅 sse 生效）",
    )
    parser.add_argument(
        "--auth-token",
        default=os.getenv("MCP_AUTH_TOKEN"),
        help="SSE 鉴权 Token（仅 sse 生效，建议使用网关/反代统一鉴权）",
    )
    return parser


def _filter_run_kwargs(kwargs: dict[str, object]) -> dict[str, object]:
    try:
        signature = inspect.signature(mcp.run)
    except (TypeError, ValueError):
        return kwargs

    if any(param.kind == inspect.Parameter.VAR_KEYWORD for param in signature.parameters.values()):
        return kwargs

    allowed = {name for name in signature.parameters.keys()}
    filtered = {key: value for key, value in kwargs.items() if key in allowed}
    unsupported = set(kwargs) - set(filtered)
    if unsupported:
        log.warning(f"SSE 参数未被当前 mcp 版本支持，将忽略: {sorted(unsupported)}")
    return filtered


def main() -> None:
    """MCP 服务器入口函数，支持 uv run mcp install"""
    # 检查是否有 install 子命令
    if len(sys.argv) > 1 and sys.argv[1] == "install":
        install_mcp_config()
        return

    # 注册所有工具
    register_all_tools()

    parser = _build_parser()
    args = parser.parse_args()

    if args.transport == "stdio":
        mcp.run("stdio")
        return

    if not args.auth_token:
        log.warning("SSE 模式未设置 auth token，建议在网关或反代层做鉴权")

    run_kwargs = {
        "host": args.host,
        "port": args.port,
        "path": args.sse_path,
    }
    if args.auth_token:
        run_kwargs["auth_token"] = args.auth_token

    try:
        mcp.run("sse", **_filter_run_kwargs(run_kwargs))
    except TypeError as exc:
        log.error(f"SSE 启动失败，请检查 mcp 版本与参数兼容性: {exc}")
        raise


def install_mcp_config() -> None:
    """安装 MCP 配置到 Claude Code"""
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


if __name__ == "__main__":
    main()
