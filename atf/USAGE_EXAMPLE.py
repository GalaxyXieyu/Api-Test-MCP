# API Test Framework 使用示例

# 方式1: 从主包导入（推荐）
from atf import CaseGenerator, run_tests
from atf.core import Globals, RequestHandler

# 方式2: 从子模块导入
from atf.core import ConfigManager, VariableResolver
from atf.handlers import ReportGenerator

# 生成测试用例
CG = CaseGenerator()
CG.generate_test_cases(project_yaml_list=["tests/"])

# 执行测试
run_tests(
    testcases=['test_cases/'],
    env='pre',
    report_type='pytest-html'
)

# 使用核心功能
globals = Globals.get_data()
config = ConfigManager.load_config()
