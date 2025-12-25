# Auto-generated unit test module

# 运行方式: uv run pytest test_cases/ -v

import pytest
from unittest.mock import patch, MagicMock, call
import allure
import yaml

from demo_calculator import add

@allure.epic('单元测试')
class TestTestCalculatorRemote:
    """单元测试: 远程测试计算器功能"""

    @allure.story('test_calculator_remote')
    def test_add_remote(self):
        """测试远程加法"""

        # 执行
        result = add(7, 3)

        # 断言
        assert result == 10

