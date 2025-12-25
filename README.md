#### 1. 架构图

```powershell
+-------------------+
|    config.yaml    | 配置文件，存储测试项目信息
+---------+---------+
          |
          v
+---------+---------+
|  Config Manager   | 读取配置文件，存储配置信息到全局变量
+---------+---------+
          |
          v
+---------+---------+  
| Global Variables  | 存储全局配置信息和 token
+---------+---------+
          |
          v
+---------+---------+  
|  Auth Module      | 执行登录请求，获取并存储 token
+---------+---------+
          |
          v
+---------+---------+         +-----------------+    +---------+---------+    +----------------+
|Test Case Runner   |<-------|  Generated Tests |<---|Test Case Generator|<---| Test Case Files |
|  执行测试用例       |          | 自动生成的测试类 |    | 自动生成测试模块     |      |  YAML 文件存储   |
+---------+---------+         +-----------------+    +---------+---------+    +----------------+
          |
          v
+---------+---------+         +-----------------+       +-----------------+
|  Request Handler  |<------->|  Variable Resolver |<-->| tools.py (外部函数) |
|  处理 HTTP 请求    |          |  处理变量调用     |      +-----------------+
+---------+---------+         +-----------------+
          |
          v
+---------+---------+
|  Assert Handler   | 处理断言
+---------+---------+
          |
          v
+---------+---------+
|  Teardown Handler   | 处理后置操作
+---------+---------+
          |
          v
+---------+---------+
|  Report Generator  | 生成测试报告
+---------+---------+
          |
          v
+---------+---------+
| DingTalk Handler  | 发送测试通知到钉钉
+---------+---------+
          |
          v
+---------+---------+
|   Log Manager     | 处理并存储日志信息
+-------------------+
```

#### 2. 架构图模块详述

**Test Case Generator（测试用例生成器）**

* 读取 YAML 测试用例文件，自动生成对应的 Python 测试模块文件。

* 自动编写 pytest 格式的测试类和测试方法。

**Config Manager（配置管理器）**

* 读取 config.yaml 文件，获取项目配置和DingTalk配置。

* 将配置信息存储到 Global Variables 中，供框架其他部分使用。

**Global Variables（全局变量）**

* 用于存储全局的配置信息和认证 token，在测试框架的各个模块之间共享。

**Auth Module（认证模块）**

* 负责处理认证逻辑，通过登录请求获取 token。

* 登录只执行一次，获取的 token 存储在 Global Variables 中。

* 包含两个模块：auth.py、report_login_handler.py。auth.py编写项目具体的登录方法，report_login_handler.py提供项目登录判断逻辑。

**Test Case Runner（测试用例执行）**

* 负责执行测试用例，运行由 Test Case Generator 生成的测试脚本。

**Request Handler（HTTP请求处理器）**

* 处理 HTTP 请求，执行接口调用。

**Variable Resolver（变量解析器）**

* 处理测试用例中的变量解析，包括全局变量、步骤变量，以及调用外部函数（如 tools.py 中的函数）。

* 变量表达式：'{{ *** }}'，如：调用tools.py中的函数获取'{{ tools.function_name(1, 2) }}'，全局变量获取'{{ merchant.token }}'，同一条测试用例中的请求步骤中获取'{{ step_id.data.id }}'

**Assert Handler（断言处理器）**

* 处理断言逻辑，校验测试结果是否符合预期。

**Teardown Handler（后置处理器）**

* 用于测试用例后置操作，如清除测试数据等。可调用接口，也可以操作数据库。

**Log Manager（日志管理器）**

* 负责处理和存储日志信息，日志文件保存在 log 目录中，帮助调试和分析。

**Report Generator（生成测试报告）**

* 支持生成Allure、pytest-html模版的HTML测试报告。

**DingTalk Handler（钉钉机器人）**

* 处理钉钉通知，将测试结果发送到指定的钉钉群。


#### 3. 目录结构

```powershell
super_api_auto_test/
├── config.yaml
├── globals.py
├── auth.py
├── case_generator.py
├── run_tests.py
├── utils/
│   ├── assert_handler.py
│   ├── config_manager.py
│   ├── dingtalk_handler.py
│   ├── globals.py
│   ├── log_manager.py
│   ├── request_handler.py
│   ├── variable_resolver.py
│   ├── project_login_handler.py
│   ├── teardown_handler.py
│   ├── report_generator.py
│   ├── tools.py
├── tests/
│   ├── project1/
│   │   ├── test_case_1.yaml
│   │   ├── test_case_2.yaml
│   │   ├── ... (more generated tests)
│   ├── project2/
│   │   ├── module
│   │   │   ├── test_case_3.yaml
│   │   │   ├── test_case_4.yaml
│   │   │   ├── ... (more generated tests)
├── test_cases/
│   ├── project1/
│   │   ├── test_case_1.py
│   │   ├── test_case_2.py
│   │   ├── ... (more test case files)
│   ├── project2/
│   │   ├── module
│   │   │   ├── test_case_3.py
│   │   │   ├── test_case_4.py
│   │   │   ├── ... (more test case files)
├── conftest.py
├── requirements.txt
└── README.md
```

#### 4. 目录结构说明

* config.yaml：配置文件，存储项目信息（环境、host、mysql、登录信息等）、DingTalk、WeChat Work、Feishu等配置信息。
* auth.py：认证模块，测试项目如果需要登录获取 token，则在本模块定义登录函数。
* run_tests.py：主执行文件，用于运行测试并触发钩子函数。
* conftest.py：存储 pytest 的钩子函数，将测试结果存储到 Globals 中。
* requirements.txt：项目依赖包管理
* utils/
    * globals.py：全局变量管理器 Globals，用于存储和访问全局数据（如项目配置、DingTalk 配置、测试结果等）。
    * log_manager.py：日志管理器，负责记录框架中的日志信息。
    * dingtalk_handler.py：DingTalk 消息发送工具类，处理和发送 DingTalk 通知。
    * config_manager.py：读取配置文件信息，存储至全局变量。
    * assert_handler.py：断言处理，执行测试用例时，负责处理用例数据中的assert字段。
    * request_handler.py：HTTP请求处理。
    * variable_resolver.py：变量解析，执行测试用例时，负责处理用例数据中的变量表达式。
    * project_login_handler.py：项目登录处理，获取 token 或 cookie。1.用例执行前，本次测试用例涉及到的需要登录的项目；2. 处理后置方法中，登录需要登录的项目
    * teardown_handler.py：测试用例后置方法处理。
    * report_generator.py：测试报告处理，支持 Allure、pytest-html 模版。
    * tools.py：自定义工具函数，可用于处理用例数据获取或其他。
* tests/
    * project_01/：被测项目1的测试数据配置，一个`.yaml`文件对应一条测试用例数据。
        * test_case_1.yaml：
    * project_02/
        * module：被测项目2中模块 module 的测试用例配置
            * test_case_2.yaml。
* test_cases/
    * project_01/
        * test_case_1.py：被项目1的测试用例脚本（由GenerateTestcaseManager获取tests/project_01/test_case_1.yaml测试用例数据生成）。
    * project_02/
        * module
            * test_case_2.py：被测项目2中模块 module 的测试用例脚本。
* logs/：日志文件存储目录
* html-reports/：测试报告存储目录

#### 5. 使用步骤
* **1). 注册项目**（如果需要）
    * `config.yaml`用于存储测试项目配置信息，需要将被测项目的信息按照目前格式添加至该文件中。
    * 可以加入第三方测试项目，但需要做改动，暂时不兼容。
* **2). 登录调试**（如果需要）
    * `auth.py`用于编写被测项目的登录方法。如果被测项目需要登录获取token，则需要先在这里编写对应方法并调试通过。
* **3). 创建测试数据文件**
    * `tests/`负责存储测试数据文件，在对应的项目（没有对应项目则先新建项目，测试用例文件会在`test_cases/`该项目下生成）下新建 yaml 测试数据文件，文件名为`test_+功能.yaml`，如merchant/test_device_bind_washing.yaml。
    * 文件内容要以`testcase:`开头，这样才能被识别为测试数据文件。
    * 具体格式及字段见 demo
    * 生成对应的测试用例文件后，数据文件名不能改动，否则执行用例时会因为找不到该数据文件而无法读取测试数据。如果改名，则需要重新生成测试用例文件。
    * 数据文件中修改了 name、id、project 这些字段后，则需要删除该文件对应的测试用例文件，重新生成新的测试用例文件，否则用例执行失败。
* **4). 生成测试用例文件**
    * `case_generator.py`负责生成测试用例，会根据传入的测试用例数据文件生成测试用例文件。
    * 用例文件名为`test_name`.py，其中`name`为数据文件中的name字段。
    * 指定数据文件生成，如：["tests/merchant/test_goods_delete_washing.yaml"]，会生成该数据文件对应的测试用例。
    * 指定项目生成，如：["tests/merchant/"]，会针对 merchant/ 中所有的数据文件生成测试用例（自动去重）。
    * 也可以不指定文件及项目，则传入：["tests/"]，会针对 tests/ 中所有项目下的所有数据文件生成测试用例（自动去重）。
* **5). 运行测试用例**
    * `run_tests.py`负责测试用例的执行，执行指定的测试用例。
    * testcases 参数，指定执行测试用例
        * 指定执行具体的测试用例文件，如：["test_cases/merchant/test_goods_delete_washing.py"]，会执行该测试用例。
        * 指定执行项目中的所有测试用例，如：["test_cases/merchant/"]，会执行 merchant/ 中所有的测试用例。
        * 也可以不指定文件及项目，则传入：["tests/"]，会执行 tests/ 中所有项目下的所有测试用例。
    * env 参数，指定执行测试环境
        * test，暂时不对测试环境进行测试。且测试环境与预发或生产环境的测试数据不一致，即不能共用一套测试数据文件，所以需要新建工程单独处理。
        * pre，预发环境
        * online，线上环境（或生产环境）
    * report_type 参数，目前支持 Allure、pytest-html 两种HTML模版。

#### 6. 注意事项
* 1). 先安装项目依赖，具体见requirements.txt文件。
* 2). 本地调试生成生成 Allure 报告时，本地需要配置好 Allure 工具。
* 3). 在一条测试用例中，如果存在同一个接口需要调用多次时（调用多个接口的场景测试用例），测试数据文件（tests/ 目录下）中该接口的 id 不能同名，否则会报错。
* 4). 修改了 tests/ 中的测试数据后，如果该测试数据已经在 test_cases/ 中生成了测试用例文件，则需要删除原来的测试用例文件，重新生成。ps：修改用例数据中某个 step 或 teardown 接口的请求参数、断言，不需要重新生成。

---

## MCP Server 安装与使用

### 安装方式

#### 方式一：发布到 PyPI 后安装（推荐）

```bash
# 1. 发布到 PyPI（开发者操作）
# twine upload --repository pypi dist/*

# 2. 用户安装
pipx install api-auto-test
```

#### 方式二：从 GitHub 安装（发布前开发测试用）

```bash
# 1. 安装 uv（如果没有）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. 从 GitHub 安装
pipx install git+https://github.com/your-username/api-auto-test.git

# 3. 注册到 Claude Code
api-auto-test-mcp install
```

#### 方式三：本地开发模式

```bash
cd /path/to/api-auto-test
uv run mcp install atf/mcp_server.py --name "api-auto-test"
```

**安装完成后**，Claude Code 会自动提示你重启，重启后 MCP 服务器即可使用。

#### 方式四：pipx

```bash
pipx install api-auto-test
```

#### 方式五：pip

```bash
pip install api-auto-test
```

### Claude Code 配置

安装后会自动配置 `.mcp.json`，或手动添加：

```json
{
  "command": "api-auto-test-mcp",
  "args": ["--workspace", "${workspace}"]
}
```

### MCP 工具

| 工具 | 说明 |
|------|------|
| `write_testcase` | 写入测试用例并生成 pytest 脚本 |
| `write_unittest` | 写入单元测试并生成 pytest 脚本 |
| `read_testcase` | 读取测试用例内容 |
| `list_testcases` | 列出测试用例 |
| `regenerate_py` | 重新生成 pytest |
| `delete_testcase` | 删除测试用例 |

### 集成测试示例

```yaml
# tests/demo_api_test.yaml
testcase:
  name: demo_api_test
  steps:
    - id: get_user
      path: /api/users/1
      method: GET
      assert:
        - type: status_code
          expected: 200
```

### 单元测试示例

```yaml
# tests/unit/demo_service_test.yaml
unittest:
  name: demo_service_test
  env_type: venv  # 可选: venv(默认) | conda | uv
  target:
    module: src.service.demo_service  # 被测模块路径
    class: DemoService                # 可选：类名
    function: get_user                # 可选：函数名
  cases:
    - id: test_get_user
      description: 测试获取用户
      inputs:
        args: [1]
      assert:
        - type: equals
          expected: "expected_value"
```

**生成的测试脚本**：

```python
# 运行方式: source .venv/bin/activate && pytest test_cases/ -v

import pytest
from unittest.mock import patch, MagicMock, call
import allure
import yaml

from src.service.demo_service import DemoService  # ← 根据 target 生成
```

### 运行测试

```bash
# venv
source .venv/bin/activate && pytest test_cases/ -v

# conda
conda activate <env_name> && pytest test_cases/ -v

# uv
uv run pytest test_cases/ -v
```

---

## 在现有项目中使用 MCP

### 完整流程

假设你有一个现有项目 `my-project`，结构如下：

```
my-project/
├── src/
│   └── service/
│       └── user_service.py   # 你想测试的代码
├── tests/                    # 测试目录（需要新建）
├── test_cases/              # 生成的测试脚本（自动创建）
└── pyproject.toml           # 项目配置
```

#### 步骤 1：安装 MCP 服务器

```bash
# 方式一：从 GitHub 安装
pipx install git+https://github.com/你的用户名/api-auto-test.git

# 方式二：发布到 PyPI 后
pipx install api-auto-test

# 注册到 Claude Code
api-auto-test-mcp install
```

**重启 Claude Code** 使 MCP 生效。

#### 步骤 2：在 Claude Code 中使用 MCP 工具

在 Claude Code 中，你可以使用以下 MCP 工具：

| 工具 | 用途 |
|------|------|
| `write_unittest` | 创建单元测试 |
| `write_testcase` | 创建集成测试（API） |
| `list_testcases` | 列出现有测试 |
| `read_testcase` | 查看测试内容 |
| `regenerate_py` | 重新生成测试脚本 |
| `delete_testcase` | 删除测试 |

#### 步骤 3：创建单元测试示例

在 Claude Code 中调用 MCP 工具：

```python
# 告诉 Claude：
"创建一个单元测试，测试 src/service/user_service.py 中的 UserService.get_user 方法"
```

Claude 会使用 `write_unittest` 工具，生成类似这样的 YAML：

```yaml
# tests/unit/user_service_test.yaml
unittest:
  name: user_service_test
  env_type: venv
  target:
    module: src.service.user_service
    class: UserService
    function: get_user
  cases:
    - id: test_get_user_normal
      description: 正常获取用户
      inputs:
        args: [1]
      assert:
        - type: equals
          expected: "expected_value"
```

**自动生成**的测试脚本：

```python
# test_cases/unit/test_user_service_test.py
# 运行方式: source .venv/bin/activate && pytest test_cases/ -v

import pytest
from unittest.mock import patch, MagicMock, call
import allure
import yaml

from src.service.user_service import UserService


class TestUserService:
    @allure.story("user_service_test")
    def test_get_user_normal(self):
        """正常获取用户"""
        # 执行
        instance = UserService()
        result = instance.get_user(1)

        # 断言
        assert result == "expected_value"
```

#### 步骤 4：执行测试

```bash
# 方式一：在终端手动执行
cd my-project
source .venv/bin/activate
pytest test_cases/ -v

# 方式二：让 MCP 执行（如果 MCP 有 run_test 工具）
# 或告诉 Claude："运行这个测试"
```

### 目录结构变化

使用 MCP 后，你的项目会变成：

```
my-project/
├── src/
│   └── service/
│       └── user_service.py
├── tests/                          # MCP 工具读取的位置
│   └── unit/
│       └── user_service_test.yaml  # 你创建的测试定义
├── test_cases/                     # 自动生成的测试脚本
│   └── unit/
│       └── test_user_service_test.py
├── pyproject.toml
└── .venv/                          # 虚拟环境
```

### 集成测试 vs 单元测试

| 类型 | 用途 | YAML 根节点 |
|------|------|-------------|
| **集成测试** | 测试 API 接口 | `testcase` |
| **单元测试** | 测试单个函数/类 | `unittest` |

**集成测试示例**：

```yaml
# tests/api/user_api_test.yaml
testcase:
  name: user_api_test
  steps:
    - id: get_user
      path: /api/users/1
      method: GET
      assert:
        - type: status_code
          expected: 200
```

**生成的脚本**：

```python
# test_cases/api/test_user_api_test.py
# 运行方式: source .venv/bin/activate && pytest test_cases/ -v

from atf.core.request_handler import RequestHandler

class TestUserApiTest:
    def test_user_api_test(self):
        response = RequestHandler.send_request(
            method="GET",
            url=project_config["host"] + "/api/users/1",
            headers=None,
            data=None,
            params=None,
            files=None
        )
        assert response.status_code == 200
```

### 常见问题

**Q: 测试脚本生成在哪里？**
A: 默认生成到 `test_cases/` 目录，与 `tests/` 平行。

**Q: 怎么运行测试？**
A: 在项目根目录执行 `pytest test_cases/ -v`

**Q: MCP 能帮我运行测试吗？**
A: 目前 MCP 负责创建测试脚本，运行测试需要在终端手动执行。未来可以添加 `run_test` 工具。

**Q: 需要把 `api-auto-test` 作为依赖吗？**
A: 是的，用户项目需要安装 `api-auto-test` 包，才能导入 atf 框架。