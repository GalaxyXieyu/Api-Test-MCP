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

import json
import os
import sys

from mcp.server import FastMCP

# 导入各工具注册函数
from atf.mcp.tools.health_tool import register_health_tool
from atf.mcp.tools.testcase_tools import register_testcase_tools
from atf.mcp.tools.unittest_tools import register_unittest_tools
from atf.mcp.tools.runner_tools import register_runner_tools


# 创建 MCP 服务器实例
mcp = FastMCP(name="api-auto-test-mcp")


def register_all_tools() -> None:
    """注册所有 MCP 工具"""
    register_health_tool(mcp)
    register_testcase_tools(mcp)
    register_unittest_tools(mcp)
    register_runner_tools(mcp)


def main() -> None:
    """MCP 服务器入口函数，支持 uv run mcp install"""
    # 检查是否有 install 子命令
    if len(sys.argv) > 1 and sys.argv[1] == "install":
        install_mcp_config()
        return

    # 注册所有工具
    register_all_tools()

    # 默认运行 stdio 模式 (MCP 协议)
    mcp.run("stdio")


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
