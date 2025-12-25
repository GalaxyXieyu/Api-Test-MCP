# Auto-generated unit test module

# 运行方式: source .venv/bin/activate && pytest test_cases/ -v

import pytest
from unittest.mock import patch, MagicMock, call
import allure
import yaml

from demo_calculator import add

@allure.epic('单元测试')
class TestTestCalculator:
    """单元测试: 测试计算器功能"""

    @allure.story('test_calculator')
    def test_add_positive(self):
        """测试正数相加"""

        # 执行
        result = add(5, 3)

        # 断言
        assert result == 8

    @allure.story('test_calculator')
    def test_add_negative(self):
        """测试负数相加"""

        # 执行
        result = add(-5, -3)

        # 断言
        assert result == -8

    @allure.story('test_calculator')
    def test_add_mixed(self):
        """测试正负数相加"""

        # 执行
        result = add(10, -4)

        # 断言
        assert result == 6

    @allure.story('test_calculator')
    def test_subtract(self):
        """测试减法函数"""

        # 执行
        result = add(10, 4)

        # 断言
        assert result == 6

