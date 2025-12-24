# MCP 服务开发文档（api-auto-test）

## 1. 背景与目标

目标是提供一个 MCP 服务，接受大模型传入的测试用例结构与 YAML 路径，在本仓库 `tests/` 目录写入 YAML，并复用现有 `CaseGenerator` 生成对应的 pytest 脚本到 `test_cases/`。服务端只返回写入状态与路径列表，不回传内容以降低 token 消耗。

## 2. 架构选择

### 2.1 架构风格

- 轻量单体服务（FastMCP）：减少依赖、快速落地、适配 MCP 客户端。
- 业务逻辑内聚：路径校验、结构校验、写入与生成分层清晰。

### 2.2 技术选型

- MCP 服务框架：`mcp`（FastMCP）
- 数据模型校验：`pydantic`
- YAML 写入：`PyYAML`
- pytest 生成：复用 `atf.case_generator.CaseGenerator`

### 2.3 数据流（核心路径）

```
LLM -> MCP Tool(write_testcase) -> 校验(yaml_path/testcase)
    -> 写入 tests/*.yaml -> 调用 CaseGenerator 生成 test_cases/*.py
    -> 返回 status + written_files
```

## 3. 代码结构设计

建议结构如下（已落地）：

```
atf/
  mcp_server.py         # MCP 服务入口与核心逻辑
docs/
  mcp_spec.md           # MCP 调用规范
  mcp_dev_guide.md      # 开发文档（本文件）
requirements-mcp.txt    # MCP 依赖清单
```

### 3.1 服务入口：`atf/mcp_server.py`

- `FastMCP`：注册工具 `write_testcase`
- 数据模型：
  - `TestcaseModel` / `StepModel` / `TeardownModel` / `AssertionModel`
- 路径与安全校验：
  - `yaml_path` 必须相对路径、以 `.yaml` 结尾、且位于 `tests/` 内
- 写入策略：
  - `overwrite=false` 默认不覆盖
  - `overwrite=true` 覆盖 YAML，删除同名 pytest 文件再生成

## 4. MCP 工具设计

### 4.1 工具：`write_testcase`

**输入参数**
- `yaml_path`：相对路径（必须在 `tests/`）
- `testcase`：测试用例结构（按项目标准）
- `overwrite`：是否覆盖（默认 false）

**输出参数**
- `status`：`ok` 或 `error`
- `written_files`：写入/生成文件路径列表

### 4.2 闭环工具补充

- `health_check`：健康检查与路径信息
- `list_testcases`：列出 `tests/` 下 YAML 文件
- `read_testcase`：读取 YAML，支持摘要/全量
- `validate_testcase`：结构校验
- `regenerate_py`：基于 YAML 重新生成 pytest
- `delete_testcase`：删除 YAML 与 pytest

### 4.2 校验策略

1. **路径校验**
   - 允许绝对路径或相对路径
   - 禁止越界（`../`）
   - 必须落在 `tests/` 目录
2. **结构校验**
   - `testcase.name` 必填
   - `steps` 至少 1 条
   - 每条 step 必须包含 `id/path/method`
   - teardown 若为 `api`，必须包含 `path/method/headers/data`
   - teardown 若为 `db`，必须包含 `query`
3. **生成校验**
   - 写入 YAML 后生成 pytest
   - 若 pytest 文件未生成，返回 `error`

## 5. 详细开发步骤

### 5.1 第一步：定义输入/输出协议

根据 `docs/mcp_spec.md` 固化结构：
- 输入包含 `yaml_path` 与 `testcase`
- 输出仅 `status` 与 `written_files`

### 5.2 第二步：设计数据模型

使用 Pydantic 构建模型：
- `TestcaseModel` 作为顶层主体
- `StepModel` / `TeardownModel` 内置校验规则

### 5.3 第三步：路径安全与规范化

实现 `_resolve_yaml_path`：
- 合法性检查
- 转换到仓库内的绝对路径
- 返回相对路径用于 `CaseGenerator` 调用

### 5.4 第四步：写入 YAML

使用 `yaml.safe_dump`：
- 保持键顺序 `sort_keys=False`
- UTF-8 输出

### 5.5 第五步：生成 pytest

复用 `CaseGenerator().generate_test_cases(project_yaml_list=[yaml_relative_path])`
- 避免重复造轮子
- 保持与现有框架一致

### 5.6 第六步：错误处理与日志

所有异常捕获后：
- 记录日志（loguru）
- 返回 `status=error`

## 6. 验证逻辑设计

### 6.1 结构验证（Pydantic）

验证点：
- 必填字段缺失时报错
- 多余字段（未知字段）禁止

### 6.2 路径验证（服务端）

验证点：
- `yaml_path` 必须是 `tests/` 内相对路径
- 禁止绝对路径与目录穿越

### 6.3 生成验证（业务结果）

验证点：
- YAML 文件写入成功
- pytest 文件生成成功
- 若生成失败，立即返回 `error`

## 7. 开发与运行指引

### 7.1 安装依赖

```bash
pip install -r requirements-mcp.txt
```

### 7.2 启动服务

```bash
python -m atf.mcp_server
```

### 7.3 调用验证（示例流程）

1. 调用 `write_testcase` 写入 `tests/<project>/...yaml`
2. 调用 `validate_testcase` 校验结构
3. 调用 `read_testcase`（summary）确认关键字段
4. 必要时调用 `regenerate_py` 重新生成 pytest

## 8. 可选增强（后续迭代）

- 增加 `project` 白名单校验（基于 `config.yaml`）
- 返回错误码（如 `E_PATH_INVALID`、`E_SCHEMA_INVALID`）
- 提供 dry-run 模式（仅校验不写入）
- 在日志中输出调用方 request_id 便于追踪

## 9. 常见问题与处理建议

- **pytest 文件未生成**：检查 `testcase.name` 与 `yaml_path` 是否匹配，确认 YAML 格式符合要求。
- **覆盖失败**：确认 `overwrite=true` 且路径准确。
- **路径校验失败**：检查是否写到 `tests/` 目录内，并确保路径为相对路径。
