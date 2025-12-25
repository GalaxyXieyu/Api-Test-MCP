"""
Health Check Tool
MCP 服务健康检查工具
"""

from mcp.server.fastmcp import FastMCP

from atf.mcp.models import HealthResponse
from atf.mcp.utils import REPO_ROOT, TESTS_ROOT, TEST_CASES_ROOT


MCP_VERSION = "0.1.0"


def register_health_tool(mcp: FastMCP) -> None:
    """注册健康检查工具"""

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
