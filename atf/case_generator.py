# @time:    2024-08-13
# @author:  xiaoqq

import os
import re
import yaml
from atf.core.log_manager import log


def sanitize_name(name: str) -> str:
	"""
	将名称转换为安全的 Python 标识符
	- 空格/连字符 -> 下划线
	- 中文 -> 保留中文，使用下划线连接
	- 特殊字符 -> 移除
	"""
	# 替换空格和连字符为下划线
	result = re.sub(r'[\s\-]+', '_', name)
	# 保留中文，只移除其他非 ASCII 字符
	result = re.sub(r'[^\w\u4e00-\u9fff]+', '', result)
	# 移除非法字符（保留字母、数字、下划线、中文）
	result = re.sub(r'[^\w]+', '', result)
	# 移除开头的数字
	result = re.sub(r'^[0-9]+', '', result)
	# 移除连续下划线
	result = re.sub(r'_+', '_', result)
	# 移除首尾下划线
	result = result.strip('_')
	# 如果结果为空，使用默认名称
	if not result:
		result = 'unnamed_test'
	return result.lower()


def to_class_name(name: str) -> str:
	"""
	将名称转换为 PascalCase 类名
	"health check api" -> "HealthCheckApi"
	"product_list_test" -> "ProductListTest"
	"""
	safe_name = sanitize_name(name)
	# 按下划线分割，每个部分首字母大写
	parts = safe_name.split('_')
	return ''.join(part.capitalize() for part in parts if part)


def check_python_syntax(code: str) -> tuple[bool, list[str]]:
	"""
	检查 Python 代码语法
	返回 (是否有效, 错误列表)
	"""
	import ast
	try:
		ast.parse(code)
		return True, []
	except SyntaxError as e:
		error_msg = f"Line {e.lineno}: {e.msg}"
		if e.text:
			error_msg += f" -> {e.text.strip()}"
		return False, [error_msg]


class CaseGenerator:
	"""
	测试用例文件生成器
	"""
	
	def generate_single(self, yaml_file: str, output_dir: str = None, base_dir: str = None, dry_run: bool = False) -> dict:
		"""
		生成单个测试用例，返回详细结果

		Args:
			yaml_file: YAML 文件路径
			output_dir: 输出目录
			base_dir: 基准目录
			dry_run: 是否仅预览，不实际写入

		Returns:
			{
				"success": bool,
				"file_path": str,
				"name_mapping": {"original": str, "safe": str, "class": str},
				"syntax_valid": bool,
				"syntax_errors": list[str],
				"code_preview": str (dry_run 模式),
				"error": str (失败时)
			}
		"""
		result = {
			"success": False,
			"file_path": None,
			"name_mapping": None,
			"syntax_valid": None,
			"syntax_errors": None,
			"code_preview": None,
			"error": None
		}

		try:
			# 计算基准目录
			if base_dir is None:
				base_dir = 'tests/cases'

			# 计算相对路径（用于生成的代码中）
			relative_yaml_path = os.path.relpath(yaml_file, base_dir)

			# 加载 YAML
			test_data_raw = self.load_test_data(yaml_file)
			if not test_data_raw:
				result["error"] = f"无法加载 YAML 文件: {yaml_file}"
				return result

			if not self.validate_test_data(test_data_raw):
				result["error"] = "YAML 数据校验不通过"
				return result

			test_data = test_data_raw['testcase']
			raw_name = test_data['name']

			# 名称处理
			safe_name = sanitize_name(raw_name)
			class_name = to_class_name(raw_name)
			result["name_mapping"] = {
				"original": raw_name,
				"safe": safe_name,
				"class": class_name
			}

			# 生成代码，使用相对路径
			code = self._generate_code(test_data, relative_yaml_path)
			
			# 语法校验
			syntax_valid, syntax_errors = check_python_syntax(code)
			result["syntax_valid"] = syntax_valid
			result["syntax_errors"] = syntax_errors
			
			if not syntax_valid:
				result["error"] = f"生成的代码存在语法错误: {syntax_errors}"
				result["code_preview"] = code[:500] + "..." if len(code) > 500 else code
				return result
			
			# 计算输出路径
			if base_dir is None:
				base_dir = 'tests/cases'
			relative_path = os.path.relpath(yaml_file, base_dir)
			path_components = relative_path.split(os.sep)
			if path_components:
				path_components.pop()
			directory_path = os.path.join(*path_components) if path_components else ""
			
			file_name = f'test_{safe_name}.py'
			if output_dir:
				file_path = os.path.join(output_dir, directory_path, file_name)
			else:
				file_path = os.path.join('tests', 'scripts', directory_path, file_name)
			
			result["file_path"] = file_path
			
			if dry_run:
				result["success"] = True
				result["code_preview"] = code
				return result
			
			# 写入文件
			os.makedirs(os.path.dirname(file_path), exist_ok=True)
			with open(file_path, 'w', encoding='utf-8') as f:
				f.write(code)
			
			result["success"] = True
			log.info(f"已生成测试用例文件: {file_path}")
			
		except Exception as e:
			result["error"] = str(e)
			log.error(f"生成测试用例失败: {e}")
		
		return result
	
	def _generate_code(self, test_data: dict, relative_yaml_path: str) -> str:
		"""生成 Python 测试代码字符串，使用相对路径"""
		import io

		raw_name = test_data['name']
		module_name = sanitize_name(raw_name)
		module_class_name = to_class_name(raw_name)
		description = test_data.get('description')
		case_name = f"test_{module_name} ({description})" if description else f"test_{module_name}"

		teardowns = test_data.get('teardowns')
		validate_teardowns = self.validate_teardowns(teardowns)

		# 计算 project_name（从相对路径中提取）
		path_components = relative_yaml_path.split(os.sep)
		if len(path_components) > 1:
			project_name = path_components[0]
		else:
			project_name = "default"
		
		allure_epic = test_data.get("allure", {}).get("epic", project_name)
		allure_feature = test_data.get("allure", {}).get("feature")
		allure_story = test_data.get("allure", {}).get("story", module_name)
		testcase_host = test_data.get('host')
		
		# 使用 StringIO 生成代码
		f = io.StringIO()

		f.write(f"# Auto-generated test module for {module_name}\n")
		f.write(f"import os\n")
		f.write(f"import re\n")
		f.write(f"from atf.core.log_manager import log\n")
		f.write(f"from atf.core.globals import Globals\n")
		f.write(f"from atf.core.variable_resolver import VariableResolver\n")
		f.write(f"from atf.core.request_handler import RequestHandler\n")
		f.write(f"from atf.core.assert_handler import AssertHandler\n")
		if validate_teardowns:
			f.write(f"from atf.handlers.teardown_handler import TeardownHandler\n")
			f.write(f"from atf.core.login_handler import LoginHandler\n")
		f.write(f"import allure\n")
		f.write(f"import yaml\n\n")
		
		f.write(f"@allure.epic('{allure_epic}')\n")
		if allure_feature:
			f.write(f"@allure.feature('{allure_feature}')\n")
		f.write(f"class Test{module_class_name}:\n")
		
		f.write(f"    @classmethod\n")
		f.write(f"    def setup_class(cls):\n")
		f.write(f"        log.info('========== 开始执行测试用例：{case_name} ==========')\n")
		f.write(f"        cls.test_case_data = cls.load_test_case_data()\n")
		
		if validate_teardowns:
			f.write(f"        cls.login_handler = LoginHandler()\n")
			f.write(f"        cls.teardowns_dict = {{teardown['id']: teardown for teardown in cls.test_case_data['teardowns']}}\n")
			f.write(f"        for teardown in cls.test_case_data.get('teardowns', []):\n")
			f.write(f"            project = teardown.get('project')\n")
			f.write(f"            if project:\n")
			f.write(f"                cls.login_handler.check_and_login_project(project, Globals.get('env'))\n")
		
		f.write(f"        cls.steps_dict = {{step['id']: step for step in cls.test_case_data['steps']}}\n")
		f.write(f"        cls.session_vars = {{}}\n")
		f.write(f"        cls.global_vars = Globals.get_data()\n")
		
		if testcase_host:
			f.write(f"        cls.testcase_host = '{testcase_host}'\n")
		
		f.write(f"        cls.VR = VariableResolver(global_vars=cls.global_vars, session_vars=cls.session_vars)\n")
		f.write(f"        log.info('Setup completed for Test{module_class_name}')\n\n")
		
		f.write(f"    @staticmethod\n")
		f.write(f"    def load_test_case_data():\n")
		# 计算相对路径部分：tests/scripts/ -> tests/cases/
		yaml_dir = os.path.dirname(relative_yaml_path)
		yaml_basename = os.path.basename(relative_yaml_path)
		if yaml_dir:
			f.write(f"        yaml_path = os.path.join(os.path.dirname(__file__), '..', 'cases', '{yaml_dir}', '{yaml_basename}')\n")
		else:
			f.write(f"        yaml_path = os.path.join(os.path.dirname(__file__), '..', 'cases', '{yaml_basename}')\n")
		f.write(f"        with open(yaml_path, 'r', encoding='utf-8') as file:\n")
		f.write(f"            test_case_data = yaml.safe_load(file)['testcase']\n")
		f.write(f"        return test_case_data\n\n")
		
		f.write(f"    @allure.story('{allure_story}')\n")
		f.write(f"    def test_{module_name}(self):\n")
		f.write(f"        log.info('Starting test_{module_name}')\n")
		
		for step in test_data['steps']:
			step_id = step['id']
			step_project = step.get("project")
			f.write(f"        # Step: {step_id}\n")
			f.write(f"        log.info(f'开始执行 step: {step_id}')\n")
			f.write(f"        {step_id} = self.steps_dict.get('{step_id}')\n")
			
			if testcase_host:
				f.write(f"        step_host = self.testcase_host\n")
			elif step_project:
				f.write(f"        project_config = self.global_vars.get('{step_project}')\n")
				f.write(f"        step_host = project_config['host'] if project_config else ''\n")
			else:
				f.write(f"        project_config = self.global_vars.get('{project_name}')\n")
				f.write(f"        step_host = project_config['host'] if project_config else ''\n")
			
			f.write(f"        response = RequestHandler.send_request(\n")
			f.write(f"            method={step_id}['method'],\n")
			f.write(f"            url=step_host + self.VR.process_data({step_id}['path']),\n")
			f.write(f"            headers=self.VR.process_data({step_id}.get('headers')),\n")
			f.write(f"            data=self.VR.process_data({step_id}.get('data')),\n")
			f.write(f"            params=self.VR.process_data({step_id}.get('params')),\n")
			f.write(f"            files=self.VR.process_data({step_id}.get('files'))\n")
			f.write(f"        )\n")
			f.write(f"        log.info(f'{step_id} 请求结果为：{{response}}')\n")
			f.write(f"        self.session_vars['{step_id}'] = response\n")
			
			if 'assert' in step:
				if not testcase_host:
					f.write(f"        db_config = project_config.get('mysql')\n")
				else:
					f.write(f"        db_config = None\n")
				f.write(f"        AssertHandler().handle_assertion(\n")
				f.write(f"            asserts=self.VR.process_data({step_id}['assert']),\n")
				f.write(f"            response=response,\n")
				f.write(f"            db_config=db_config\n")
				f.write(f"        )\n\n")
		
		# teardown 处理
		if validate_teardowns:
			f.write(f"    @classmethod\n")
			f.write(f"    def teardown_class(cls):\n")
			f.write(f"        log.info('Starting teardown for the Test{module_class_name}')\n")
			for teardown_step in teardowns:
				teardown_step_id = teardown_step['id']
				teardown_step_project = teardown_step.get("project")
				f.write(f"        {teardown_step_id} = cls.teardowns_dict.get('{teardown_step_id}')\n")
				
				if teardown_step_project:
					f.write(f"        project_config = cls.global_vars.get('{teardown_step_project}')\n")
				else:
					f.write(f"        project_config = cls.global_vars.get('{project_name}')\n")
				
				if teardown_step['operation_type'] == 'api':
					f.write(f"        response = RequestHandler.send_request(\n")
					f.write(f"            method={teardown_step_id}['method'],\n")
					f.write(f"            url=project_config['host'] + cls.VR.process_data({teardown_step_id}['path']),\n")
					f.write(f"            headers=cls.VR.process_data({teardown_step_id}.get('headers')),\n")
					f.write(f"            data=cls.VR.process_data({teardown_step_id}.get('data')),\n")
					f.write(f"            params=cls.VR.process_data({teardown_step_id}.get('params')),\n")
					f.write(f"            files=cls.VR.process_data({teardown_step_id}.get('files'))\n")
					f.write(f"        )\n")
					f.write(f"        log.info(f'{teardown_step_id} 请求结果为：{{response}}')\n")
					f.write(f"        cls.session_vars['{teardown_step_id}'] = response\n")
					
					if 'assert' in teardown_step:
						f.write(f"        db_config = project_config.get('mysql')\n")
						f.write(f"        AssertHandler().handle_assertion(\n")
						f.write(f"            asserts=cls.VR.process_data({teardown_step_id}['assert']),\n")
						f.write(f"            response=response,\n")
						f.write(f"            db_config=db_config\n")
						f.write(f"        )\n\n")
				elif teardown_step['operation_type'] == 'db':
					f.write(f"        db_config = project_config.get('mysql')\n")
					f.write(f"        TeardownHandler().handle_teardown(\n")
					f.write(f"            asserts=cls.VR.process_data({teardown_step_id}),\n")
					f.write(f"            db_config=db_config\n")
					f.write(f"        )\n\n")
					f.write(f"        pass\n")
				else:
					f.write(f"        pass\n")
			
			f.write(f"        log.info('Teardown completed for Test{module_class_name}.')\n")
		
		f.write(f"\n        log.info(f\"Test case test_{module_name} completed.\")\n")
		
		return f.getvalue()
	
	def generate_test_cases(self, project_yaml_list=None, output_dir=None, base_dir=None):
		"""
		根据YAML文件生成测试用例并保存到指定目录
		:param project_yaml_list: 列表形式，项目名称或YAML文件路径
		:param output_dir: 测试用例文件生成目录，默认 'tests/scripts'
		:param base_dir: 基准目录，用于计算相对路径，默认 'tests/cases'
		"""
		# 如果没有传入project_yaml_list，默认遍历 tests/cases 目录下所有 YAML
		if not project_yaml_list:
			project_yaml_list = ["tests/cases/"]

		# 基准目录，用于计算相对路径
		if base_dir is None:
			base_dir = 'tests/cases'

		# 遍历传入的project_yaml_list
		for item in project_yaml_list:
			if os.path.isdir(item):  # 如果是项目目录，如 tests/merchant
				self._process_project_dir(item, output_dir, base_dir)
			elif os.path.isfile(item) and item.endswith('.yaml'):  # 如果是单个YAML文件
				self._process_single_yaml(item, output_dir, base_dir)
			else:  # 如果是项目名称，如 merchant
				project_dir = os.path.join("tests", "cases", item)
				self._process_project_dir(project_dir, output_dir, base_dir)
		
		log.info("Test automation framework execution completed")
	
	def _process_project_dir(self, project_dir, output_dir, base_dir='tests/cases'):
		"""
		处理项目目录，遍历项目下所有YAML文件生成测试用例
		:param project_dir: 项目目录路径
		:param output_dir: 测试用例文件生成目录
		:param base_dir: 基准目录，用于计算相对路径
		"""
		for root, dirs, files in os.walk(project_dir):
			for file in files:
				if file.endswith('.yaml'):
					yaml_file = os.path.join(root, file)
					self._process_single_yaml(yaml_file, output_dir, base_dir)
	
	def _process_single_yaml(self, yaml_file, output_dir, base_dir='tests/cases'):
		"""
		处理单个YAML文件，生成对应的测试用例文件
		:param yaml_file: YAML文件路径
		:param output_dir: 测试用例文件生成目录
		:param base_dir: 基准目录，用于计算相对路径
		"""
		log.info(f"[CaseGenerator] _process_single_yaml called:")
		log.info(f"[CaseGenerator]   yaml_file={yaml_file}")
		log.info(f"[CaseGenerator]   output_dir={output_dir}")
		log.info(f"[CaseGenerator]   base_dir={base_dir}")

		# 读取YAML文件内容
		_test_data = self.load_test_data(yaml_file)
		validate_test_data = self.validate_test_data(_test_data)
		if not validate_test_data:
			log.warning(f"{yaml_file} 数据校验不通过，跳过生成测试用例。")
			return
		test_data = _test_data['testcase']
		teardowns = test_data.get('teardowns')
		validate_teardowns = self.validate_teardowns(teardowns)

		# 计算 relative_path（YAML 相对于 base_dir 的路径）
		relative_path = os.path.relpath(yaml_file, base_dir)
		path_components = relative_path.split(os.sep)

		# 分离目录和文件名
		if len(path_components) > 1:
			# YAML 在子目录中，如 backend/settings_api.yaml
			relative_dir = os.path.join(*path_components[:-1])  # backend/
			yaml_filename = path_components[-1]  # settings_api.yaml
			project_name = path_components[0]  # 使用第一级目录名作为 project_name
		else:
			# YAML 在 base_dir 根目录
			relative_dir = ""
			yaml_filename = path_components[0] if path_components else os.path.basename(yaml_file)
			project_name = "default"  # 使用默认 project_name
		# 移除最后一个组件（文件名）
		if path_components:
			path_components.pop()  # 移除最后一个元素
		directory_path = os.path.join(*path_components) if path_components else ""
		directory_path = directory_path.rstrip(os.sep)	# 确保路径不以斜杠结尾

		log.info(f"[CaseGenerator] Path calculation:")
		log.info(f"[CaseGenerator]   relative_path={relative_path}")
		log.info(f"[CaseGenerator]   path_components={path_components}")
		log.info(f"[CaseGenerator]   project_name={project_name}")
		log.info(f"[CaseGenerator]   directory_path={directory_path}")
		
		raw_name = test_data['name']
		description = test_data.get('description')
		
		# 安全处理名称：支持中文、空格等
		module_name = sanitize_name(raw_name)
		module_class_name = to_class_name(raw_name)
		
		# 日志记录中的测试用例名称
		case_name = f"test_{module_name} ({description})" if description is not None else f"test_{module_name}"
		file_name = f'test_{module_name}.py'
		
		log.info(f"[CaseGenerator] Name processing: '{raw_name}' -> module='{module_name}', class='{module_class_name}'")
		
		# 生成文件路径
		if output_dir:
			file_path = os.path.join(output_dir, directory_path, file_name)
		else:
			file_path = os.path.join('tests', 'scripts', directory_path, file_name)

		log.info(f"[CaseGenerator] File path generation:")
		log.info(f"[CaseGenerator]   file_name={file_name}")
		log.info(f"[CaseGenerator]   file_path={file_path}")
		log.info(f"[CaseGenerator]   dirname={os.path.dirname(file_path)}")

		# 检查test_cases中对应的.py文件是否存在，存在则跳过生成
		if os.path.exists(file_path):
			log.info(f"测试用例文件已存在，跳过生成: {file_path}")
			return
		
		# 创建目录
		os.makedirs(os.path.dirname(file_path), exist_ok=True)
		
		allure_epic = test_data.get("allure", {}).get("epic", project_name)
		allure_feature = test_data.get("allure", {}).get("feature")
		allure_story = test_data.get("allure", {}).get("story", module_name)
		
		with open(file_path, 'w', encoding='utf-8') as f:
			f.write(f"# Auto-generated test module for {module_name}\n")
			f.write(f"import os\n")
			f.write(f"import re\n")
			f.write(f"from atf.core.log_manager import log\n")
			f.write(f"from atf.core.globals import Globals\n")
			f.write(f"from atf.core.variable_resolver import VariableResolver\n")
			f.write(f"from atf.core.request_handler import RequestHandler\n")
			f.write(f"from atf.core.assert_handler import AssertHandler\n")
			if validate_teardowns:
				f.write(f"from atf.handlers.teardown_handler import TeardownHandler\n")
				f.write(f"from atf.core.login_handler import LoginHandler\n")
			f.write(f"import allure\n")
			f.write(f"import yaml\n\n")
			
			f.write(f"@allure.epic('{allure_epic}')\n")
			if allure_feature:
				f.write(f"@allure.feature('{allure_feature}')\n")
			f.write(f"class Test{module_class_name}:\n")
			
			f.write(f"    @classmethod\n")
			f.write(f"    def setup_class(cls):\n")
			f.write(f"        log.info('========== 开始执行测试用例：{case_name} ==========')\n")
			f.write(f"        cls.test_case_data = cls.load_test_case_data()\n")	# 获取测试数据
			# 如果存在teardowns，则将步骤列表转换为字典， 在下面的测试方法中通过 id 查找步骤的信息
			if validate_teardowns:
				f.write(f"        cls.login_handler = LoginHandler()\n")
				f.write(f"        cls.teardowns_dict = {{teardown['id']: teardown for teardown in cls.test_case_data['teardowns']}}\n")
				f.write(f"        for teardown in cls.test_case_data.get('teardowns', []):\n")
				f.write(f"            project = teardown.get('project')\n")
				f.write(f"            if project:\n")
				f.write(f"                cls.login_handler.check_and_login_project(project, Globals.get('env'))\n")
			
			# 将步骤列表转换为字典， 在下面的测试方法中通过 id 查找步骤的信息
			f.write(f"        cls.steps_dict = {{step['id']: step for step in cls.test_case_data['steps']}}\n")
			
			f.write(f"        cls.session_vars = {{}}\n")
			f.write(f"        cls.global_vars = Globals.get_data()\n")  # 获取全局变量
			# f.write(f"        cls.db_config = cls.global_vars.get('mysql')\n")	# 获取数据库配置

			# 处理 testcase 级别的 host 配置
			testcase_host = test_data.get('host')
			if testcase_host:
				f.write(f"        cls.testcase_host = '{testcase_host}'\n")
			
			# 创建VariableResolver实例并保存在类变量中
			f.write(f"        cls.VR = VariableResolver(global_vars=cls.global_vars, session_vars=cls.session_vars)\n")
			
			f.write(f"        log.info('Setup completed for Test{module_class_name}')\n\n")
			
			f.write(f"    @staticmethod\n")
			f.write(f"    def load_test_case_data():\n")
			if relative_dir:
				f.write(f"        yaml_path = os.path.join(os.path.dirname(__file__), '..', 'cases', '{relative_dir}', '{yaml_filename}')\n")
			else:
				f.write(f"        yaml_path = os.path.join(os.path.dirname(__file__), '..', 'cases', '{yaml_filename}')\n")
			f.write(f"        with open(yaml_path, 'r', encoding='utf-8') as file:\n")
			f.write(f"            test_case_data = yaml.safe_load(file)['testcase']\n")
			f.write(f"        return test_case_data\n\n")
			
			f.write(f"    @allure.story('{allure_story}')\n")
			f.write(f"    def test_{module_name}(self):\n")
			f.write(f"        log.info('Starting test_{module_name}')\n")
			
			for step in test_data['steps']:
				step_id = step['id']
				step_project = step.get("project") # 场景测试用例可能会请求不同项目的接口，需要在每个step中指定对应的project
				f.write(f"        # Step: {step_id}\n")
				f.write(f"        log.info(f'开始执行 step: {step_id}')\n")
				f.write(f"        {step_id} = self.steps_dict.get('{step_id}')\n")

				# 如果 testcase 有 host 配置，使用它；否则使用 project 配置
				if testcase_host:
					f.write(f"        step_host = self.testcase_host\n")
				elif step_project:
					f.write(f"        project_config = self.global_vars.get('{step_project}')\n")
					f.write(f"        step_host = project_config['host'] if project_config else ''\n")
				else:
					f.write(f"        project_config = self.global_vars.get('{project_name}')\n")
					f.write(f"        step_host = project_config['host'] if project_config else ''\n")

				f.write(f"        response = RequestHandler.send_request(\n")
				f.write(f"            method={step_id}['method'],\n")
				f.write(f"            url=step_host + self.VR.process_data({step_id}['path']),\n")
				f.write(f"            headers=self.VR.process_data({step_id}.get('headers')),\n")
				f.write(f"            data=self.VR.process_data({step_id}.get('data')),\n")
				f.write(f"            params=self.VR.process_data({step_id}.get('params')),\n")
				f.write(f"            files=self.VR.process_data({step_id}.get('files'))\n")
				f.write(f"        )\n")
				f.write(f"        log.info(f'{step_id} 请求结果为：{{response}}')\n")
				f.write(f"        self.session_vars['{step_id}'] = response\n")

				if 'assert' in step:
					# 只有在真正使用 project_config 时才获取 db_config
					if not testcase_host:
						f.write(f"        db_config = project_config.get('mysql')\n")
					else:
						f.write(f"        db_config = None\n")
					f.write(f"        AssertHandler().handle_assertion(\n")
					f.write(f"            asserts=self.VR.process_data({step_id}['assert']),\n")
					f.write(f"            response=response,\n")
					f.write(f"            db_config=db_config\n")
					f.write(f"        )\n\n")
			
			# teardown处理
			if validate_teardowns:
				f.write(f"    @classmethod\n")
				f.write(f"    def teardown_class(cls):\n")
				f.write(f"        log.info('Starting teardown for the Test{module_class_name}')\n")
				for teardown_step in teardowns:
					teardown_step_id = teardown_step['id']
					teardown_step_project = teardown_step.get("project")
					f.write(f"        {teardown_step_id} = cls.teardowns_dict.get('{teardown_step_id}')\n")

					if teardown_step_project:
						f.write(f"        project_config = cls.global_vars.get('{teardown_step_project}')\n")
					else:
						f.write(f"        project_config = cls.global_vars.get('{project_name}')\n")

					# 如果是请求接口操作
					if teardown_step['operation_type'] == 'api':
						f.write(f"        response = RequestHandler.send_request(\n")
						f.write(f"            method={teardown_step_id}['method'],\n")
						f.write(f"            url=project_config['host'] + cls.VR.process_data({teardown_step_id}['path']),\n")
						f.write(f"            headers=cls.VR.process_data({teardown_step_id}.get('headers')),\n")
						f.write(f"            data=cls.VR.process_data({teardown_step_id}.get('data')),\n")
						f.write(f"            params=cls.VR.process_data({teardown_step_id}.get('params')),\n")
						f.write(f"            files=cls.VR.process_data({teardown_step_id}.get('files'))\n")
						f.write(f"        )\n")
						f.write(f"        log.info(f'{teardown_step_id} 请求结果为：{{response}}')\n")
						f.write(f"        cls.session_vars['{teardown_step_id}'] = response\n")

						if 'assert' in teardown_step:
							# if any(assertion['type'].startswith('mysql') for assertion in teardown_step['assert']):
							# 	f.write(f"        db_config = project_config.get('mysql')\n")
							f.write(f"        db_config = project_config.get('mysql')\n")
							f.write(f"        AssertHandler().handle_assertion(\n")
							f.write(f"            asserts=cls.VR.process_data({teardown_step_id}['assert']),\n")
							f.write(f"            response=response,\n")
							f.write(f"            db_config=db_config\n")
							f.write(f"        )\n\n")

					# 如果是数据库操作，暂时未补充逻辑
					elif teardown_step['operation_type'] == 'db':
						f.write(f"        db_config = project_config.get('mysql')\n")
						f.write(f"        TeardownHandler().handle_teardown(\n")
						f.write(f"            asserts=cls.VR.process_data({teardown_step_id}),\n")
						f.write(f"            db_config=db_config\n")
						f.write(f"        )\n\n")
						f.write(f"        pass\n")
					else:
						log.info(f"未知的 operation_type: {teardown_step['operation_type']}")
						f.write(f"        pass\n")
				
				f.write(f"        log.info('Teardown completed for Test{module_class_name}.')\n")
					
			f.write(f"\n        log.info(f\"Test case test_{module_name} completed.\")\n")
		
		log.info(f"已生成测试用例文件: {file_path}")
		
	
	@staticmethod
	def load_test_data(test_data_file):
		try:
			with open(test_data_file, 'r', encoding='utf-8') as file:
				test_data = yaml.safe_load(file)
			return test_data
		except FileNotFoundError:
			log.error(f"未找到测试数据文件: {test_data_file}")
		except yaml.YAMLError as e:
			log.error(f"YAML配置文件解析错误: {e}，{test_data_file} 跳过生成测试用例。")
	
	@staticmethod
	def validate_test_data(test_data):
		"""
		校验测试数据是否符合基本要求
		:param test_data: 测试数据
		:return:
		"""
		if not test_data:
			log.error("test_data 不能为空.")
			return False
		
		if not test_data.get('testcase'):
			log.error("test_data 必须包含 'testcase' 键.")
			return False
		
		if not test_data['testcase'].get('name'):
			log.error("'testcase' 下的 'name' 字段不能为空.")
			return False
		
		steps = test_data['testcase'].get('steps')
		if not steps:
			log.error("'testcase' 下的 'steps' 字段不能为空.")
			return False
		
		for step in steps:
			if not all(key in step for key in ['id', 'path', 'method']):
				log.error("每个步骤必须包含 'id', 'path', 和 'method' 字段.")
				return False
			
			if not step['id']:
				log.error("步骤中的 'id' 字段不能为空.")
				return False
			if not step['path']:
				log.error("步骤中的 'path' 字段不能为空.")
				return False
			if not step['method']:
				log.error("步骤中的 'method' 字段不能为空.")
				return False
		
		return True
	
	@staticmethod
	def validate_teardowns(teardowns):
		"""
		验证 teardowns 数据是否符合要求
		:param teardowns: teardowns 列表
		:return: True 如果验证成功，否则 False
		"""
		if not teardowns:
			# log.warning("testcase 下的 'teardowns' 字段为空.")
			return False
		
		for teardown in teardowns:
			if not all(key in teardown for key in ['id', 'operation_type']):
				log.warning("teardown 必须包含 'id' 和 'operation_type' 字段.")
				return False
			
			if not teardown['id']:
				log.warning("teardown 中的 'id' 字段为空.")
				return False
			if not teardown['operation_type']:
				log.warning("teardown 中的 'operation_type' 字段为空.")
				return False
			
			if teardown['operation_type'] == 'api':
				required_api_keys = ['path', 'method', 'headers', 'data']
				if not all(key in teardown for key in required_api_keys):
					log.warning("对于 API 类型的 teardown，必须包含 'path', 'method', 'headers', 'data' 字段.")
					return False
				
				if not teardown['path']:
					log.warning("teardown 中的 'path' 字段为空.")
					return False
				if not teardown['method']:
					log.warning("teardown 中的 'method' 字段为空.")
					return False
			
			elif teardown['operation_type'] == 'db':
				if 'query' not in teardown or not teardown['query']:
					log.warning("对于数据库类型的 teardown，'query' 字段不能为空.")
					return False
		
		return True


if __name__ == '__main__':
	CG = CaseGenerator()
	CG.generate_test_cases(project_yaml_list=["tests/cases/"])