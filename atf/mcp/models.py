"""
Pydantic Models for MCP Server
所有数据模型定义，用于输入验证和响应格式化
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator


class AssertionModel(BaseModel):
    """断言模型"""
    model_config = ConfigDict(extra="forbid")

    type: str
    field: str | None = None
    expected: Any | None = None
    container: Any | None = None
    query: str | None = None


class StepModel(BaseModel):
    """测试步骤模型"""
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    id: str
    path: str
    method: str
    headers: dict | None = None
    data: Any | None = None
    params: dict | None = None
    files: dict | None = None
    project: str | None = None
    assert_: list[AssertionModel] | None = Field(default=None, alias="assert")

    @model_validator(mode="after")
    def validate_required(self) -> "StepModel":
        if not self.id:
            raise ValueError("steps.id 不能为空")
        if not self.path:
            raise ValueError("steps.path 不能为空")
        if not self.method:
            raise ValueError("steps.method 不能为空")
        return self


class TeardownModel(BaseModel):
    """清理步骤模型"""
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    id: str
    operation_type: Literal["api", "db"]
    path: str | None = None
    method: str | None = None
    headers: dict | None = None
    data: Any | None = None
    params: dict | None = None
    files: dict | None = None
    project: str | None = None
    assert_: list[AssertionModel] | None = Field(default=None, alias="assert")
    query: str | None = None

    @model_validator(mode="after")
    def validate_operation(self) -> "TeardownModel":
        if self.operation_type == "api":
            missing = []
            if not self.path:
                missing.append("path")
            if not self.method:
                missing.append("method")
            if self.headers is None:
                missing.append("headers")
            if self.data is None:
                missing.append("data")
            if missing:
                raise ValueError(f"teardowns.api 缺少必填字段: {', '.join(missing)}")
        if self.operation_type == "db" and not self.query:
            raise ValueError("teardowns.db 缺少必填字段: query")
        return self


class AllureModel(BaseModel):
    """Allure 报告配置模型"""
    model_config = ConfigDict(extra="forbid")

    epic: str | None = None
    feature: str | None = None
    story: str | None = None


# ==================== 单元测试模型 ====================


class MockModel(BaseModel):
    """Mock 配置模型"""
    model_config = ConfigDict(extra="forbid")

    target: str  # mock 目标路径，如 "app.services.user_service.UserRepository"
    method: str | None = None  # 方法名
    return_value: Any | None = None  # 返回值
    side_effect: Any | None = None  # 副作用（异常或可调用对象）


class UnitTestInputModel(BaseModel):
    """单元测试输入参数模型"""
    model_config = ConfigDict(extra="forbid")

    args: list[Any] | None = None  # 位置参数
    kwargs: dict[str, Any] | None = None  # 关键字参数


class UnitAssertionModel(BaseModel):
    """单元测试断言模型"""
    model_config = ConfigDict(extra="forbid")

    type: str  # equals, not_equals, contains, raises, called_once, called_with, etc.
    field: str | None = None  # JSONPath 字段路径
    expected: Any | None = None  # 期望值
    mock: str | None = None  # mock 名称（用于 mock 相关断言）
    args: list[Any] | None = None  # 期望的调用参数
    kwargs: dict[str, Any] | None = None  # 期望的关键字参数
    exception: str | None = None  # 期望的异常类型
    message: str | None = None  # 期望的异常消息


class UnitTestCaseModel(BaseModel):
    """单个单元测试用例模型"""
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    id: str
    description: str | None = None
    mocks: list[MockModel] | None = None
    inputs: UnitTestInputModel | None = None
    assert_: list[UnitAssertionModel] | None = Field(default=None, alias="assert")

    @model_validator(mode="after")
    def validate_required(self) -> "UnitTestCaseModel":
        if not self.id:
            raise ValueError("unittest.cases.id 不能为空")
        return self


class UnitTestTargetModel(BaseModel):
    """被测目标模型"""
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    module: str  # 被测模块路径
    class_: str | None = Field(default=None, alias="class")  # 被测类名
    function: str | None = None  # 被测函数名

    @model_validator(mode="after")
    def validate_target(self) -> "UnitTestTargetModel":
        if not self.module:
            raise ValueError("unittest.target.module 不能为空")
        return self


class UnitTestFixtureModel(BaseModel):
    """测试夹具模型"""
    model_config = ConfigDict(extra="forbid")

    type: str  # patch, cleanup, setup_db, etc.
    target: str | None = None
    value: Any | None = None
    action: str | None = None


class UnitTestFixturesModel(BaseModel):
    """测试夹具集合模型"""
    model_config = ConfigDict(extra="forbid")

    setup: list[UnitTestFixtureModel] | None = None
    teardown: list[UnitTestFixtureModel] | None = None


class UnitTestModel(BaseModel):
    """单元测试模型"""
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    name: str
    description: str | None = None
    env_type: Literal["venv", "conda", "uv"] = "venv"  # 运行环境的虚拟环境类型
    target: UnitTestTargetModel
    allure: AllureModel | None = None
    cases: list[UnitTestCaseModel]
    fixtures: UnitTestFixturesModel | None = None

    @model_validator(mode="after")
    def validate_required(self) -> "UnitTestModel":
        if not self.name:
            raise ValueError("unittest.name 不能为空")
        if not self.cases:
            raise ValueError("unittest.cases 不能为空")
        return self


# ==================== 集成测试模型 ====================


class TestcaseModel(BaseModel):
    """集成测试用例模型"""
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    name: str
    description: str | None = None
    host: str | None = None  # 可选的测试服务地址
    allure: AllureModel | None = None
    steps: list[StepModel]
    teardowns: list[TeardownModel] | None = None

    @model_validator(mode="after")
    def validate_required(self) -> "TestcaseModel":
        if not self.name:
            raise ValueError("testcase.name 不能为空")
        if not self.steps:
            raise ValueError("testcase.steps 不能为空")
        return self


# ==================== 响应模型 ====================


class GenerateResponse(BaseModel):
    """生成操作响应"""
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok", "error"]
    written_files: list[str]
    error_message: str | None = None
    error_details: dict | None = None  # 更详细的错误信息，用于大模型理解


class HealthResponse(BaseModel):
    """健康检查响应"""
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok", "error"]
    version: str
    repo_root: str
    tests_root: str
    test_cases_root: str


class ListTestcasesResponse(BaseModel):
    """列出测试用例响应"""
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok", "error"]
    testcases: list[str]
    error_message: str | None = None
    error_details: dict | None = None


class ReadTestcaseResponse(BaseModel):
    """读取测试用例响应"""
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok", "error"]
    yaml_path: str
    mode: Literal["summary", "full"]
    testcase: dict[str, Any] | None
    error_message: str | None = None
    error_details: dict | None = None


class ValidateTestcaseResponse(BaseModel):
    """校验测试用例响应"""
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok", "error"]
    errors: list[str]


class RegenerateResponse(BaseModel):
    """重新生成响应"""
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok", "error"]
    written_files: list[str]
    error_message: str | None = None
    error_details: dict | None = None


class DeleteTestcaseResponse(BaseModel):
    """删除测试用例响应"""
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok", "error"]
    deleted_files: list[str]
    error_message: str | None = None
    error_details: dict | None = None


# ==================== 测试执行结果模型 ====================


class AssertionResultModel(BaseModel):
    """断言结果模型"""
    model_config = ConfigDict(extra="forbid")

    assertion_type: str  # 断言类型: equals, contains, status_code, etc.
    field: str | None = None  # 字段路径
    expected: Any | None = None  # 期望值
    actual: Any | None = None  # 实际值
    passed: bool  # 是否通过
    message: str | None = None  # 失败时的消息


class TestResultModel(BaseModel):
    """单个测试用例执行结果"""
    model_config = ConfigDict(extra="forbid")

    test_name: str  # 测试名称
    status: Literal["passed", "failed", "error", "skipped"]  # 执行状态
    duration: float  # 执行时间（秒）
    assertions: list[AssertionResultModel]  # 断言结果列表
    error_message: str | None = None  # 错误信息
    traceback: str | None = None  # 错误堆栈


class RunTestcaseResponse(BaseModel):
    """单个测试用例执行响应"""
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok", "error"]
    test_name: str
    yaml_path: str | None = None
    py_path: str | None = None
    result: TestResultModel | None = None
    error_message: str | None = None
    error_details: dict | None = None


class BatchRunResponse(BaseModel):
    """批量执行响应"""
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok", "error"]
    total: int  # 总数
    passed: int  # 通过
    failed: int  # 失败
    skipped: int  # 跳过
    duration: float  # 总耗时（秒）
    results: list[TestResultModel]  # 每个测试用例的结果


class TestResultHistoryModel(BaseModel):
    """测试结果历史记录"""
    model_config = ConfigDict(extra="forbid")

    run_id: str  # 运行ID
    timestamp: str  # 执行时间
    total: int
    passed: int
    failed: int
    skipped: int
    duration: float
    test_names: list[str]  # 执行的测试用例列表


class GetTestResultsResponse(BaseModel):
    """获取测试执行历史响应"""
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok", "error"]
    results: list[TestResultHistoryModel]


__all__ = [
    # Models
    "AssertionModel",
    "StepModel",
    "TeardownModel",
    "AllureModel",
    "MockModel",
    "UnitTestInputModel",
    "UnitAssertionModel",
    "UnitTestCaseModel",
    "UnitTestTargetModel",
    "UnitTestFixtureModel",
    "UnitTestFixturesModel",
    "UnitTestModel",
    "TestcaseModel",
    # Responses
    "GenerateResponse",
    "HealthResponse",
    "ListTestcasesResponse",
    "ReadTestcaseResponse",
    "ValidateTestcaseResponse",
    "RegenerateResponse",
    "DeleteTestcaseResponse",
    "AssertionResultModel",
    "TestResultModel",
    "RunTestcaseResponse",
    "BatchRunResponse",
    "TestResultHistoryModel",
    "GetTestResultsResponse",
]
