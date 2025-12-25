# @time:    2024-12-25
# @author:  auto-generated

import os
from pathlib import Path

import yaml

from atf.core.log_manager import log


class UnitCaseGenerator:
    """单元测试用例文件生成器"""

    def generate_unit_tests(self, yaml_file: str, output_dir: str | None = None) -> str | None:
        """
        根据 YAML 文件生成单元测试用例
        :param yaml_file: YAML 文件路径
        :param output_dir: 输出目录
        :return: 生成的文件路径
        """
        test_data = self._load_yaml(yaml_file)
        if not test_data:
            return None

        if not self._validate_unittest_data(test_data):
            log.warning(f"{yaml_file} 数据校验不通过，跳过生成。")
            return None

        unittest_data = test_data["unittest"]
        file_path = self._get_output_path(yaml_file, unittest_data["name"], output_dir)

        if os.path.exists(file_path):
            log.info(f"测试用例文件已存在，跳过生成: {file_path}")
            return None

        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        self._generate_file(file_path, yaml_file, unittest_data)
        log.info(f"已生成单元测试文件: {file_path}")
        return file_path

    def _load_yaml(self, yaml_file: str) -> dict | None:
        """加载 YAML 文件"""
        try:
            with open(yaml_file, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            log.error(f"未找到文件: {yaml_file}")
        except yaml.YAMLError as e:
            log.error(f"YAML 解析错误: {e}")
        return None

    def _validate_unittest_data(self, data: dict) -> bool:
        """校验单元测试数据"""
        if not data.get("unittest"):
            log.error("数据必须包含 'unittest' 键")
            return False

        ut = data["unittest"]
        if not ut.get("name"):
            log.error("unittest.name 不能为空")
            return False

        if not ut.get("target") or not ut["target"].get("module"):
            log.error("unittest.target.module 不能为空")
            return False

        if not ut.get("cases"):
            log.error("unittest.cases 不能为空")
            return False

        for case in ut["cases"]:
            if not case.get("id"):
                log.error("unittest.cases.id 不能为空")
                return False

        return True

    def _get_output_path(self, yaml_file: str, name: str, output_dir: str | None) -> str:
        """获取输出文件路径"""
        relative_path = os.path.relpath(yaml_file, "tests")
        path_parts = relative_path.split(os.sep)
        if path_parts:
            path_parts.pop()  # 移除文件名
        dir_path = os.path.join(*path_parts) if path_parts else ""

        file_name = f"test_{name}.py"
        base_dir = output_dir or "test_cases"
        return os.path.join(base_dir, dir_path, file_name)

    def _generate_file(self, file_path: str, yaml_file: str, ut: dict) -> None:
        """生成测试文件"""
        with open(file_path, "w", encoding="utf-8") as f:
            self._write_imports(f, ut)
            self._write_class_header(f, ut)
            self._write_test_methods(f, ut, yaml_file)

    def _write_imports(self, f, ut: dict) -> None:
        """写入导入语句"""
        f.write("# Auto-generated unit test module\n\n")

        # 写入运行方式注释（根据 env_type）
        env_type = ut.get("env_type", "venv")
        if env_type == "venv":
            f.write("# 运行方式: source .venv/bin/activate && pytest test_cases/ -v\n\n")
        elif env_type == "conda":
            f.write("# 运行方式: conda activate <env_name> && pytest test_cases/ -v\n\n")
        elif env_type == "uv":
            f.write("# 运行方式: uv run pytest test_cases/ -v\n\n")

        f.write("import pytest\n")
        f.write("from unittest.mock import patch, MagicMock, call\n")
        f.write("import allure\n")
        f.write("import yaml\n\n")

        # 导入被测模块
        target = ut["target"]
        module = target["module"]
        class_name = target.get("class")
        func_name = target.get("function")

        if class_name:
            f.write(f"from {module} import {class_name}\n\n")
        elif func_name:
            f.write(f"from {module} import {func_name}\n\n")
        else:
            f.write(f"import {module}\n\n")

    def _write_class_header(self, f, ut: dict) -> None:
        """写入类定义和装饰器"""
        name = ut["name"]
        class_name = "".join(s.capitalize() for s in name.split("_"))
        allure_cfg = ut.get("allure", {})

        epic = allure_cfg.get("epic", "单元测试")
        feature = allure_cfg.get("feature")

        f.write(f"@allure.epic('{epic}')\n")
        if feature:
            f.write(f"@allure.feature('{feature}')\n")
        f.write(f"class Test{class_name}:\n")
        f.write(f'    """单元测试: {ut.get("description", name)}"""\n\n')

    def _write_test_methods(self, f, ut: dict, yaml_file: str) -> None:
        """写入测试方法"""
        target = ut["target"]
        allure_cfg = ut.get("allure", {})
        story = allure_cfg.get("story", ut["name"])

        for case in ut["cases"]:
            self._write_single_test(f, case, target, story)

    def _write_single_test(self, f, case: dict, target: dict, story: str) -> None:
        """写入单个测试方法"""
        case_id = case["id"]
        desc = case.get("description", case_id)
        mocks = case.get("mocks", [])

        # 写入装饰器
        f.write(f"    @allure.story('{story}')\n")
        self._write_mock_decorators(f, mocks)

        # 写入方法签名
        mock_params = self._get_mock_params(mocks)
        f.write(f"    def {case_id}(self{mock_params}):\n")
        f.write(f'        """{desc}"""\n')

        # 写入 mock 配置
        self._write_mock_setup(f, mocks)

        # 写入执行代码
        self._write_execution(f, case, target)

        # 写入断言
        self._write_assertions(f, case, mocks)

        f.write("\n")

    def _write_mock_decorators(self, f, mocks: list) -> None:
        """写入 mock 装饰器"""
        for mock in reversed(mocks):
            target = mock["target"]
            method = mock.get("method")
            if method:
                f.write(f"    @patch('{target}.{method}')\n")
            else:
                f.write(f"    @patch('{target}')\n")

    def _get_mock_params(self, mocks: list) -> str:
        """获取 mock 参数列表"""
        if not mocks:
            return ""
        params = []
        for mock in mocks:
            name = self._get_mock_var_name(mock)
            params.append(name)
        return ", " + ", ".join(params)

    def _get_mock_var_name(self, mock: dict) -> str:
        """获取 mock 变量名"""
        target = mock["target"]
        method = mock.get("method")
        if method:
            return f"mock_{method.lower()}"
        parts = target.split(".")
        return f"mock_{parts[-1].lower()}"

    def _write_mock_setup(self, f, mocks: list) -> None:
        """写入 mock 配置"""
        for mock in mocks:
            var_name = self._get_mock_var_name(mock)
            ret_val = mock.get("return_value")
            side_effect = mock.get("side_effect")

            if ret_val is not None:
                f.write(f"        {var_name}.return_value = {repr(ret_val)}\n")
            if side_effect is not None:
                f.write(f"        {var_name}.side_effect = {repr(side_effect)}\n")

    def _write_execution(self, f, case: dict, target: dict) -> None:
        """写入执行代码"""
        inputs = case.get("inputs", {})
        args = inputs.get("args", [])
        kwargs = inputs.get("kwargs", {})

        class_name = target.get("class")
        func_name = target.get("function")

        f.write("\n        # 执行\n")

        # 构建参数字符串
        args_str = ", ".join(repr(a) for a in args)
        kwargs_str = ", ".join(f"{k}={repr(v)}" for k, v in kwargs.items())
        all_args = ", ".join(filter(None, [args_str, kwargs_str]))

        if class_name and func_name:
            f.write(f"        instance = {class_name}()\n")
            f.write(f"        result = instance.{func_name}({all_args})\n")
        elif class_name:
            f.write(f"        result = {class_name}({all_args})\n")
        elif func_name:
            f.write(f"        result = {func_name}({all_args})\n")
        else:
            f.write(f"        result = None  # TODO: 补充执行逻辑\n")

    def _write_assertions(self, f, case: dict, mocks: list) -> None:
        """写入断言"""
        asserts = case.get("assert", [])
        if not asserts:
            return

        f.write("\n        # 断言\n")
        mock_var_map = {self._get_mock_key(m): self._get_mock_var_name(m) for m in mocks}

        for assertion in asserts:
            self._write_single_assertion(f, assertion, mock_var_map)

    def _get_mock_key(self, mock: dict) -> str:
        """获取 mock 键名"""
        target = mock["target"]
        method = mock.get("method")
        parts = target.split(".")
        if method:
            return f"{parts[-1]}.{method}"
        return parts[-1]

    def _write_single_assertion(self, f, assertion: dict, mock_var_map: dict) -> None:
        """写入单个断言"""
        assert_type = assertion["type"]
        field = assertion.get("field")
        expected = assertion.get("expected")
        mock_name = assertion.get("mock")
        args = assertion.get("args", [])
        kwargs = assertion.get("kwargs", {})
        exception = assertion.get("exception")
        message = assertion.get("message")

        if assert_type == "equals":
            if field:
                f.write(f"        assert result{self._parse_field(field)} == {repr(expected)}\n")
            else:
                f.write(f"        assert result == {repr(expected)}\n")

        elif assert_type == "not_equals":
            if field:
                f.write(f"        assert result{self._parse_field(field)} != {repr(expected)}\n")
            else:
                f.write(f"        assert result != {repr(expected)}\n")

        elif assert_type == "contains":
            f.write(f"        assert {repr(expected)} in result\n")

        elif assert_type == "is_none":
            f.write(f"        assert result is None\n")

        elif assert_type == "is_not_none":
            f.write(f"        assert result is not None\n")

        elif assert_type == "called_once" and mock_name:
            var = mock_var_map.get(mock_name, f"mock_{mock_name.lower()}")
            f.write(f"        {var}.assert_called_once()\n")

        elif assert_type == "called_with" and mock_name:
            var = mock_var_map.get(mock_name, f"mock_{mock_name.lower()}")
            args_str = ", ".join(repr(a) for a in args)
            kwargs_str = ", ".join(f"{k}={repr(v)}" for k, v in kwargs.items())
            all_args = ", ".join(filter(None, [args_str, kwargs_str]))
            f.write(f"        {var}.assert_called_with({all_args})\n")

        elif assert_type == "not_called" and mock_name:
            var = mock_var_map.get(mock_name, f"mock_{mock_name.lower()}")
            f.write(f"        {var}.assert_not_called()\n")

        elif assert_type == "raises" and exception:
            match_str = f", match={repr(message)}" if message else ""
            f.write(f"        # 注意: raises 断言需要包裹执行代码\n")
            f.write(f"        # with pytest.raises({exception}{match_str}):\n")
            f.write(f"        #     执行代码\n")

    def _parse_field(self, field: str) -> str:
        """解析字段路径为 Python 访问语法"""
        if not field:
            return ""
        if field.startswith("$."):
            field = field[2:]
        parts = field.split(".")
        result = ""
        for part in parts:
            if part.isdigit():
                result += f"[{part}]"
            else:
                result += f"['{part}']"
        return result
