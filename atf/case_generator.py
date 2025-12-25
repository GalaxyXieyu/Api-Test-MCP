# @time:    2024-08-13
# @author:  xiaoqq

import os
import yaml
from atf.core.log_manager import log


class CaseGenerator:
	"""
	测试用例文件生成器
	"""
	def generate_test_cases(self, project_yaml_list=None, output_dir=None, base_dir=None):
		"""
		根据YAML文件生成测试用例并保存到指定目录
		:param project_yaml_list: 列表形式，项目名称或YAML文件路径
		:param output_dir: 测试用例文件生成目录
		:param base_dir: 基准目录，用于计算相对路径，默认 'tests'
		"""
		# 如果没有传入project_yaml_list，默认遍历tests目录下所有project
		if not project_yaml_list:
			project_yaml_list = ["tests/"]

		# 基准目录，用于计算相对路径
		if base_dir is None:
			base_dir = 'tests'

		# 遍历传入的project_yaml_list
		for item in project_yaml_list:
			if os.path.isdir(item):  # 如果是项目目录，如 tests/merchant
				self._process_project_dir(item, output_dir, base_dir)
			elif os.path.isfile(item) and item.endswith('.yaml'):  # 如果是单个YAML文件
				self._process_single_yaml(item, output_dir, base_dir)
			else:  # 如果是项目名称，如 merchant
				project_dir = os.path.join("tests", item)
				self._process_project_dir(project_dir, output_dir, base_dir)
		
		log.info("Test automation framework execution completed")
	
	def _process_project_dir(self, project_dir, output_dir, base_dir='tests'):
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
	
	def _process_single_yaml(self, yaml_file, output_dir, base_dir='tests'):
		"""
		处理单个YAML文件，生成对应的测试用例文件
		:param yaml_file: YAML文件路径
		:param output_dir: 测试用例文件生成目录
		:param base_dir: 基准目录，用于计算相对路径
		"""
		# 读取YAML文件内容
		_test_data = self.load_test_data(yaml_file)
		validate_test_data = self.validate_test_data(_test_data)
		if not validate_test_data:
			log.warning(f"{yaml_file} 数据校验不通过，跳过生成测试用例。")
			return
		test_data = _test_data['testcase']
		teardowns = test_data.get('teardowns')
		validate_teardowns = self.validate_teardowns(teardowns)

		# 生成测试用例文件的相对路径。yaml文件路径有多个层级时，获取项目名称，以及base_dir后、yaml文件名前的路径
		relative_path = os.path.relpath(yaml_file, base_dir)
		path_components = relative_path.split(os.sep)
		project_name = path_components[0] if path_components[0] else path_components[1]
		# 移除最后一个组件（文件名）
		if path_components:
			path_components.pop()  # 移除最后一个元素
		directory_path = os.path.join(*path_components) if path_components else ""
		directory_path = directory_path.rstrip(os.sep)	# 确保路径不以斜杠结尾
		
		
		
		module_name = test_data['name']
		description = test_data.get('description')
		# 日志记录中的测试用例名称
		case_name = f"test_{module_name} ({description})" if description is not None else f"test_{module_name}"
		
		# 判断test_data中的name是否存在"_"，存在则去掉将首字母大写组成一个新的字符串，否则首字母大写
		module_class_name = (''.join(s.capitalize() for s in module_name.split('_'))
							 if '_' in module_name else module_name.capitalize())
		file_name = f'test_{module_name}.py'
		
		# 生成文件路径
		if output_dir:
			file_path = os.path.join(output_dir, directory_path, file_name)
		else:
			file_path = os.path.join('test_cases', directory_path, file_name)
		
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
			f.write(f"        with open(r'{yaml_file}', 'r', encoding='utf-8') as file:\n")
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
	CG.generate_test_cases(project_yaml_list=["tests/"])