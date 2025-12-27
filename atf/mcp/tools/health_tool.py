"""
Health Check Tool
MCP 服务健康检查工具
"""

import time

from mcp.server.fastmcp import FastMCP

from atf.mcp.models import HealthResponse
from atf.mcp.utils import (
    REPO_ROOT,
    TESTS_ROOT,
    TEST_CASES_ROOT,
    new_request_id,
    log_tool_call,
)


MCP_VERSION = "0.1.0"


def register_health_tool(mcp: FastMCP) -> None:
    """注册健康检查工具"""

    @mcp.tool(
        name="health_check",
        title="MCP 服务健康检查",
        description="返回服务版本与基础路径信息。",
    )
    def health_check() -> HealthResponse:
        request_id = new_request_id()
        start_time = time.perf_counter()
        try:
            response = HealthResponse(
                status="ok",
                request_id=request_id,
                version=MCP_VERSION,
                repo_root=str(REPO_ROOT),
                tests_root=str(TESTS_ROOT),
                test_cases_root=str(TEST_CASES_ROOT),
            )
        except Exception as exc:
            response = HealthResponse(
                status="error",
                request_id=request_id,
                version=MCP_VERSION,
                repo_root=str(REPO_ROOT),
                tests_root=str(TESTS_ROOT),
                test_cases_root=str(TEST_CASES_ROOT),
                error_code="MCP_HEALTH_ERROR",
                retryable=False,
                error_message=str(exc),
                error_details={"error_type": "health_check_failed"},
            )
        latency_ms = int((time.perf_counter() - start_time) * 1000)
        log_tool_call("health_check", request_id, response.status, latency_ms, response.error_code)
        return response
