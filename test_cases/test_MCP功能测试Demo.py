# Auto-generated test module for MCP功能测试Demo
from atf.core.log_manager import log
from atf.core.globals import Globals
from atf.core.variable_resolver import VariableResolver
from atf.core.request_handler import RequestHandler
from atf.core.assert_handler import AssertHandler
import allure
import yaml

@allure.epic('mcp_test_demo.yaml')
class TestMcp功能测试demo:
    @classmethod
    def setup_class(cls):
        log.info('========== 开始执行测试用例：test_MCP功能测试Demo (测试MCP write_testcase功能是否正常) ==========')
        cls.test_case_data = cls.load_test_case_data()
        cls.steps_dict = {step['id']: step for step in cls.test_case_data['steps']}
        cls.session_vars = {}
        cls.global_vars = Globals.get_data()
        cls.VR = VariableResolver(global_vars=cls.global_vars, session_vars=cls.session_vars)
        log.info('Setup completed for TestMcp功能测试demo')

    @staticmethod
    def load_test_case_data():
        with open(r'tests/mcp_test_demo.yaml', 'r', encoding='utf-8') as file:
            test_case_data = yaml.safe_load(file)['testcase']
        return test_case_data

    @allure.story('MCP功能测试Demo')
    def test_MCP功能测试Demo(self):
        log.info('Starting test_MCP功能测试Demo')
        # Step: get_user
        log.info(f'开始执行 step: get_user')
        get_user = self.steps_dict.get('get_user')
        project_config = self.global_vars.get('mcp_test_demo.yaml')
        response = RequestHandler.send_request(
            method=get_user['method'],
            url=project_config['host'] + self.VR.process_data(get_user['path']),
            headers=self.VR.process_data(get_user.get('headers')),
            data=self.VR.process_data(get_user.get('data')),
            params=self.VR.process_data(get_user.get('params')),
            files=self.VR.process_data(get_user.get('files'))
        )
        log.info(f'get_user 请求结果为：{response}')
        self.session_vars['get_user'] = response
        db_config = project_config.get('mysql')
        AssertHandler().handle_assertion(
            asserts=self.VR.process_data(get_user['assert']),
            response=response,
            db_config=db_config
        )

        # Step: create_user
        log.info(f'开始执行 step: create_user')
        create_user = self.steps_dict.get('create_user')
        project_config = self.global_vars.get('mcp_test_demo.yaml')
        response = RequestHandler.send_request(
            method=create_user['method'],
            url=project_config['host'] + self.VR.process_data(create_user['path']),
            headers=self.VR.process_data(create_user.get('headers')),
            data=self.VR.process_data(create_user.get('data')),
            params=self.VR.process_data(create_user.get('params')),
            files=self.VR.process_data(create_user.get('files'))
        )
        log.info(f'create_user 请求结果为：{response}')
        self.session_vars['create_user'] = response
        db_config = project_config.get('mysql')
        AssertHandler().handle_assertion(
            asserts=self.VR.process_data(create_user['assert']),
            response=response,
            db_config=db_config
        )


        log.info(f"Test case test_MCP功能测试Demo completed.")
