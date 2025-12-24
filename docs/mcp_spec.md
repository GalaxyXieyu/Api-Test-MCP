# MCP 规范与落地方案（api-auto-test）

## 目标

提供一个 MCP 服务，将大模型传入的测试用例结构写入 `tests/` 下的 YAML，并生成对应的 pytest 脚本到 `test_cases/`。服务端仅返回状态与路径，不回传 YAML/pytest 内容，避免占用 token。

## 工具清单

### write_testcase

**用途**：写入 YAML 测试用例并生成 pytest 脚本。

**输入结构（JSON）**

```json
{
  "yaml_path": "tests/merchant/module/test_device_bind.yaml",
  "testcase": {
    "name": "device_bind",
    "description": "绑定设备接口",
    "allure": {
      "epic": "merchant",
      "feature": "device",
      "story": "bind"
    },
    "steps": [
      {
        "id": "bind_device",
        "path": "/api/device/bind",
        "method": "POST",
        "headers": {
          "Content-Type": "application/json"
        },
        "data": {
          "sn": "SN-001"
        },
        "assert": [
          {
            "type": "equal",
            "field": "code",
            "expected": 0
          }
        ]
      }
    ],
    "teardowns": [
      {
        "id": "unbind_device",
        "operation_type": "api",
        "path": "/api/device/unbind",
        "method": "POST",
        "headers": {
          "Content-Type": "application/json"
        },
        "data": {
          "sn": "SN-001"
        }
      }
    ]
  },
  "overwrite": false
}
```

说明：

- `testcase` 既可以是对象，也可以是字符串（JSON/YAML 字符串）；字符串会在服务端解析并校验。
- `yaml_path` 支持绝对路径或相对路径，但必须落在 `tests/` 目录下。

**输出结构（JSON）**

```json
{
  "status": "ok",
  "written_files": [
    "tests/merchant/module/test_device_bind.yaml",
    "test_cases/merchant/module/test_device_bind.py"
  ]
}
```

当执行失败时：

```json
{
  "status": "error",
  "written_files": []
}
```

错误详情会记录在日志中。

### health_check

**用途**：检查服务状态与基础路径。

**输出结构（JSON）**

```json
{
  "status": "ok",
  "version": "0.1.0",
  "repo_root": "/Volumes/DATABASE/code/api-auto-test",
  "tests_root": "/Volumes/DATABASE/code/api-auto-test/tests",
  "test_cases_root": "/Volumes/DATABASE/code/api-auto-test/test_cases"
}
```

### list_testcases

**用途**：列出 `tests/` 目录下的 YAML 测试用例。

**输入结构（JSON）**

```json
{
  "root_path": "tests/merchant"
}
```

**输出结构（JSON）**

```json
{
  "status": "ok",
  "testcases": [
    "tests/merchant/demo/test_device_bind.yaml"
  ]
}
```

### read_testcase

**用途**：读取指定 YAML 测试用例，默认返回摘要。

**输入结构（JSON）**

```json
{
  "yaml_path": "tests/merchant/demo/test_device_bind.yaml",
  "mode": "summary"
}
```

**输出结构（JSON）**

```json
{
  "status": "ok",
  "yaml_path": "tests/merchant/demo/test_device_bind.yaml",
  "mode": "summary",
  "testcase": {
    "name": "device_bind",
    "description": "绑定设备",
    "steps": [
      {
        "id": "bind_device",
        "path": "/api/device/bind",
        "method": "POST"
      }
    ]
  }
}
```

### validate_testcase

**用途**：校验 YAML 测试用例结构。

**输入结构（JSON）**

```json
{
  "yaml_path": "tests/merchant/demo/test_device_bind.yaml"
}
```

**输出结构（JSON）**

```json
{
  "status": "ok",
  "errors": []
}
```

### regenerate_py

**用途**：基于 YAML 重新生成 pytest 文件。

**输入结构（JSON）**

```json
{
  "yaml_path": "tests/merchant/demo/test_device_bind.yaml",
  "overwrite": true
}
```

**输出结构（JSON）**

```json
{
  "status": "ok",
  "written_files": [
    "tests/merchant/demo/test_device_bind.yaml",
    "test_cases/merchant/demo/test_device_bind.py"
  ]
}
```

### delete_testcase

**用途**：删除 YAML 与对应的 pytest 文件。

**输入结构（JSON）**

```json
{
  "yaml_path": "tests/merchant/demo/test_device_bind.yaml",
  "delete_py": true
}
```

**输出结构（JSON）**

```json
{
  "status": "ok",
  "deleted_files": [
    "tests/merchant/demo/test_device_bind.yaml",
    "test_cases/merchant/demo/test_device_bind.py"
  ]
}
```

## 路径与安全规则

- `yaml_path` 可以是相对路径或绝对路径，但必须位于 `tests/` 目录下。
- `yaml_path` 必须以 `.yaml` 结尾。
- 服务端会拒绝任何绝对路径或越界路径（例如 `../`）。
- pytest 文件路径由服务端根据 YAML 路径与 `testcase.name` 计算，不允许客户端指定。

## 生成规则

- YAML 根节点固定为 `testcase`。
- `testcase.name` 对应 pytest 文件名 `test_<name>.py`。
- pytest 文件内容由现有 `CaseGenerator` 生成，确保与当前项目标准一致。

## 覆盖规则

- 默认 `overwrite=false`：若 YAML 或 pytest 文件已存在，直接返回 `error`。
- 当 `overwrite=true`：会覆盖 YAML，并删除已有 pytest 文件后重新生成。

## 运行方式

```bash
python -m atf.mcp_server
```

## 依赖说明

- 依赖 `mcp`（FastMCP）与 `pydantic`。
- 如需独立安装，可执行：

```bash
pip install -r requirements-mcp.txt
```
