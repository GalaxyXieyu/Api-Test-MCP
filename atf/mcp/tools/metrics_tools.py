"""
MCP Metrics Tools
MCP 调用指标与统计工具
"""

from __future__ import annotations

import json
import time
from collections import Counter, deque
from datetime import datetime, timedelta
from typing import Any

from mcp.server.fastmcp import FastMCP

from atf.core.log_manager import log
from atf.mcp.models import McpMetricsResponse
from atf.mcp.utils import MCP_CALLS_LOG, build_error_payload, log_tool_call, new_request_id


def _parse_timestamp(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _load_recent_records(limit: int, since_minutes: int | None) -> list[dict[str, Any]]:
    if not MCP_CALLS_LOG.exists():
        return []

    cutoff = None
    if since_minutes is not None and since_minutes > 0:
        cutoff = datetime.now().astimezone() - timedelta(minutes=since_minutes)

    records: deque[dict[str, Any]] = deque(maxlen=limit if limit > 0 else None)

    with MCP_CALLS_LOG.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if cutoff:
                ts = _parse_timestamp(record.get("timestamp", ""))
                if ts is None or ts < cutoff:
                    continue
            records.append(record)

    return list(records)


def register_metrics_tools(mcp: FastMCP) -> None:
    """注册 MCP 指标工具"""

    @mcp.tool(
        name="get_mcp_metrics",
        title="获取 MCP 调用指标",
        description="返回最近 MCP 工具调用的成功率、耗时与错误分布。",
    )
    def get_mcp_metrics(
        limit: int = 500,
        since_minutes: int | None = None,
    ) -> McpMetricsResponse:
        request_id = new_request_id()
        start_time = time.perf_counter()
        try:
            records = _load_recent_records(limit, since_minutes)
            total = len(records)
            if total == 0:
                response = McpMetricsResponse(
                    status="ok",
                    request_id=request_id,
                    total=0,
                    success=0,
                    error=0,
                    success_rate=1.0,
                    avg_latency_ms=0.0,
                    p95_latency_ms=0.0,
                    error_codes={},
                    window_minutes=since_minutes,
                )
            else:
                success = sum(1 for r in records if r.get("status") == "ok")
                error = total - success
                latencies = sorted(int(r.get("latency_ms", 0)) for r in records)
                avg_latency = round(sum(latencies) / total, 2) if total else 0.0
                p95_index = max(0, int(total * 0.95) - 1)
                p95_latency = latencies[p95_index] if latencies else 0.0
                error_codes = Counter(
                    r.get("error_code") for r in records if r.get("status") != "ok" and r.get("error_code")
                )

                response = McpMetricsResponse(
                    status="ok",
                    request_id=request_id,
                    total=total,
                    success=success,
                    error=error,
                    success_rate=round(success / total, 4) if total else 1.0,
                    avg_latency_ms=avg_latency,
                    p95_latency_ms=p95_latency,
                    error_codes=dict(error_codes),
                    window_minutes=since_minutes,
                )
        except Exception as exc:
            log.error(f"获取 MCP 指标失败: {exc}")
            payload = build_error_payload(
                code="MCP_METRICS_ERROR",
                message=str(exc),
                retryable=False,
                details={"error_type": "unknown_error"},
            )
            response = McpMetricsResponse(
                status="error",
                request_id=request_id,
                **payload,
            )

        latency_ms = int((time.perf_counter() - start_time) * 1000)
        log_tool_call(
            "get_mcp_metrics",
            request_id,
            response.status,
            latency_ms,
            response.error_code,
            meta={"limit": limit, "since_minutes": since_minutes},
        )
        return response
