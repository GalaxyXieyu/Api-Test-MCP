# MCP 运行与安全优化配置（SSE/监控/稳定性）

## 目标
- 为 MCP 提供可服务化部署的配置模板
- 降低调用失败率并提升可观测性
- 提供最小可用的安全与限流方案

## 环境变量建议
| 变量 | 说明 | 默认值 |
| --- | --- | --- |
| `MCP_TRANSPORT` | 传输方式：`stdio` 或 `sse` | `stdio` |
| `MCP_HOST` | SSE 监听地址 | `127.0.0.1` |
| `MCP_PORT` | SSE 监听端口 | `8000` |
| `MCP_SSE_PATH` | SSE 路由路径 | `/mcp` |
| `MCP_AUTH_TOKEN` | SSE 鉴权 Token（可选） | 空 |
| `MCP_LOG_CALLS_ENABLED` | 是否记录调用日志 | `1` |
| `MCP_LOGS_ROOT` | 调用日志目录 | `atf/logs` |
| `MCP_CALLS_LOG` | 调用日志文件 | `mcp_calls.jsonl` |
| `PYTEST_TIMEOUT` | 测试超时（秒） | `300` |
| `MAX_ERROR_LENGTH` | 错误截断长度 | `500` |
| `MAX_HISTORY_SIZE` | 运行历史最大条数 | `1000` |
| `ATF_AUTO_INSTALL_DEPS` | 自动安装依赖 | `1` |

## SSE 运行方式（建议搭配网关）
```bash
export MCP_TRANSPORT=sse
export MCP_HOST=0.0.0.0
export MCP_PORT=8000
export MCP_SSE_PATH=/mcp
export MCP_AUTH_TOKEN=your-token

api-auto-test-mcp
```

## Nginx 反向代理示例（TLS + 限流）
```nginx
# 仅示例，需根据实际证书与域名调整
limit_req_zone $binary_remote_addr zone=mcp_req:10m rate=10r/s;
limit_conn_zone $binary_remote_addr zone=mcp_conn:10m;

server {
    listen 443 ssl;
    server_name mcp.example.com;

    ssl_certificate /etc/ssl/certs/your.crt;
    ssl_certificate_key /etc/ssl/private/your.key;

    location /mcp {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 3600;

        # 基础限流与连接限制
        limit_req zone=mcp_req burst=20 nodelay;
        limit_conn mcp_conn 20;

        # 鉴权（推荐网关层校验 Token）
        # auth_request /auth;
    }
}
```

## systemd 服务示例（可选）
```ini
[Unit]
Description=API Auto Test MCP Server
After=network.target

[Service]
Type=simple
Environment=MCP_TRANSPORT=sse
Environment=MCP_HOST=0.0.0.0
Environment=MCP_PORT=8000
Environment=MCP_SSE_PATH=/mcp
Environment=MCP_AUTH_TOKEN=your-token
Environment=MCP_LOG_CALLS_ENABLED=1
Environment=ATF_AUTO_INSTALL_DEPS=0
ExecStart=/usr/local/bin/api-auto-test-mcp
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

## 安全与稳定性建议
- SSE 必须走 TLS，避免中间人攻击。
- 鉴权建议放在网关层（JWT / API Key / mTLS）。
- 加入限流与并发限制，避免长连接耗尽资源。
- 生产环境建议关闭自动依赖安装：`ATF_AUTO_INSTALL_DEPS=0`。
- 定期归档/清理 `mcp_calls.jsonl`，避免日志无限增长。

## 调用指标与排障
- 使用 `get_mcp_metrics` 查看成功率、P95、错误分布。
- 结合 `request_id` 与 `atf/logs/mcp_calls.jsonl` 定位失败原因。

