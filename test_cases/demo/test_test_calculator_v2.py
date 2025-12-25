# Auto-generated unit test module

# 运行方式: source .venv/bin/activate && pytest test_cases/ -v

import pytest
from unittest.mock import patch, MagicMock, call
import allure
import yaml

from demo_calculator import Calculator

@allure.epic('单元测试')
@allure.feature('Calculator')
class TestTestCalculatorV2:
    """单元测试: 测试计算器 Multiply 功能"""

    @allure.story('test_calculator_v2')
    def test_multiply_positive(self):
        """测试正数相乘"""

        # 执行
        instance = Calculator()
        result = instance.multiply(3, 4)

        # 断言
        assert result == 12

