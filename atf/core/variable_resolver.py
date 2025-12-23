# @time:    2024-08-23
# @author:  xiaoqq

import re
import importlib
from types import ModuleType
from typing import Any, Dict, Union
from atf.core.log_manager import log

class VariableResolver:
	"""
	解析YAML文件中的变量表达式'{{ *** }}'，根据变量表达式调用工具函数、获取全局、会话变量的值。
	1. 先判断变量中是否有"()"，如{{ tools.demo_func(a=2, b=1) }}，有则调用 atf.utils.helpers.py 中的函数，并传入参数；
	2. 再判断是否存在“.”，有则再判断测试用例局部变量session_vars中是否存在“.”前面第一个字符串，如果是则获取
	3. 如果不是则从全局变量获取
	4. 如果变量表达式以Global或GLOBAL开头，则直接从全局变量获取
	"""
	def __init__(self, session_vars: Dict[str, Any], global_vars: Dict[str, Any]):
		self.session_vars = session_vars
		self.global_vars = global_vars

	def resolve_variable(self, expression: str) -> Any:
		"""解析 {{ }} 表达式并返回其值"""
		expression = expression.strip()

		# 如果是函数调用形式
		if '(' in expression and ')' in expression:
			return self._resolve_function(expression)
		# 如果是多层次的变量引用形式
		elif '.' in expression or '[' in expression:
			return self._resolve_dot_expression(expression)
		else:
			raise ValueError(f"Unsupported expression format: {expression}")

	def _resolve_function(self, expression: str) -> Any:
		"""处理函数调用形式的表达式"""
		# 提取模块名和函数名
		module_name, func_call = expression.split('.', 1)
		module = self._import_module(module_name)

		# 提取函数名和参数
		func_name, args_str = re.match(r"(\w+)\((.*)\)", func_call).groups()
		func = getattr(module, func_name)

		# 解析参数
		args = self._parse_function_args(args_str)

		# 调用函数并返回结果
		return func(**args)

	def _import_module(self, module_name: str) -> ModuleType:
		"""导入模块"""
		try:
			return importlib.import_module(f'atf.utils.{module_name}')
		except ImportError as e:
			raise ImportError(f"Module {module_name} not found in atf.utils. Error: {e}")

	def _parse_function_args(self, args_str: str) -> Dict[str, Any]:
		"""解析函数参数"""
		return eval(f"dict({args_str})")

	def _resolve_dot_expression(self, expression: str) -> Any:
		"""处理以 '.' 分隔的变量引用形式"""
		keys = re.split(r'\.|\[|\]', expression)
		keys = [key for key in keys if key]  # 去掉空字符串
		
		root_key = keys[0]
		
		# 通过Global 或 GLOBAL 指定从全局变量获取，如{{Global.data.id}}
		use_global = root_key in ['Global', 'GLOBAL']
		
		if use_global:
			root_key = keys[1]
			value = self.global_vars[root_key]
		elif root_key in self.session_vars:
			value = self.session_vars[root_key]
		elif root_key in self.global_vars:
			value = self.global_vars[root_key]
		else:
			log.error(f"{root_key} not found in session_vars or global_vars")
			raise ValueError(f"{root_key} not found in session_vars or global_vars")
		
		for key in keys[1:]:
			if key.isdigit():  # 检查key是否为索引
				value = value[int(key)]
			else:
				try:
					value = value[key]
				except KeyError:
					log.error(f"Key '{key}' not found in {value}")
					raise ValueError(f"Key '{key}' not found in {value}")

		return value

	def process_value(self, value: Union[str, Dict, list]) -> Any:
		"""递归处理字典、列表或字符串中的 {{ }} 表达式"""
		if isinstance(value, str) and '{{' in value and '}}' in value:
			return self._process_string(value)
		elif isinstance(value, dict):
			return {k: self.process_value(v) for k, v in value.items()}
		elif isinstance(value, list):
			return [self.process_value(item) for item in value]
		else:
			return value
	
	def _process_string(self, value: str) -> any:
		"""解析字符串中的 {{ }} 表达式并替换"""
		# pattern = r'\{\{\s*(.*?)\s*\}\}'
		pattern = r'\{\{(.*?)}\}'
		matches = re.findall(pattern, value)
		
		for match in matches:
			match_stripped = match.strip()  # 去除表达式两侧的空格
			# 检查是否以Global/GLOBAL开头
			if match_stripped.startswith(('Global.', 'GLOBAL.')):
				resolved_value = self._resolve_dot_expression(match_stripped)
			else:
				resolved_value = self.resolve_variable(match_stripped)
			
			# resolved_value = self.resolve_variable(match_stripped)
			
			# 确定表达式的原始格式，并替换
			original_format = f'{{{{ {match_stripped} }}}}'
			if match.startswith(' ') and match.endswith(' '):
				new_format = original_format
			elif match.startswith(' '):
				new_format = f'{{{{ {match_stripped}}}}}'
			elif match.endswith(' '):
				new_format = f'{{{{{match_stripped} }}}}'
			else:
				new_format = f'{{{{{match_stripped}}}}}'
				
			# 如果解析出的值不是字符串，且原始表达式不是整个字符串，则保留原始类型
			if isinstance(resolved_value, (int, float, bool)) and value == new_format:
				return resolved_value
			# 否则，将其转换为字符串并替换掉原始表达式
			value = value.replace(new_format, str(resolved_value))
		
		return value

	def process_data(self, data: Any) -> Any:
		"""处理 YAML 数据并替换所有 {{ }} 表达式"""
		data_str = str(data)
		if '{{' in data_str:
			# log.info(f"开始解析并获取变量：{data}")
			log.info(f"开始解析并获取变量")
			return self.process_value(data)
		return data

if __name__ == '__main__':
	# 示例用法
	session_vars = {
		'step1': {
			'data': {
				'id': 123,
				'orderNo': 1020240906142034235893,
				'items': [
					{'id': 'item_0'},
					{'id': 'item_1'}
				]
			}
		}
	}
	
	global_vars = {
		'merchant': {
			'token': 'xyz-token'
		}
	}
	
	url = '/api/endpoint1/{{ tools.demo_get_id() }}'
	
	headers = {
		'Content-Type': 'application/json',
		'Authorization': '{{ merchant.token }}'
	}
	
	data = {
		'param1': '{{ step1.data.id }}',
		'param2': {
			'p_param': {
				'p_p_param1': '{{tools.demo_func(a=3, b=1, c=3) }}',
				'p_p_param2': '{{ tools.demo_func()}}',
				'p_p_param3': 333,
				'p_p_param4': ['/goods/detail/{{tools.demo_get_id()}}', "sss"],
				'p_p_param5': '{{step1.data.items[1].id}}'
			}
		}
	}
	asserts = [
		{
			"type": "equal",
			"field": "code",
			"expected": 0
		},
		{
			"type": "equal",
			"field": "message",
			"expected": "success"
		},
		{
			"type": "equal",
			"field": "data.orderNo",
			"expected": "{{step1.data.orderNo}}"
		}
	]
	
	resolver = VariableResolver(session_vars, global_vars)
	print(resolver.process_data(url))
	print(resolver.process_data(headers))
	print(resolver.process_data(data))
	print(resolver.process_data(asserts))