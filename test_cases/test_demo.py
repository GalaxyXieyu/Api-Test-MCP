# Auto-generated test module for demo
from atf.core.log_manager import log
from atf.core.globals import Globals
from atf.core.variable_resolver import VariableResolver
from atf.core.request_handler import RequestHandler
from atf.core.assert_handler import AssertHandler
import allure
import yaml

@allure.epic('demo_test.yaml')
class TestDemo:
    @classmethod
    def setup_class(cls):
        log.info('========== 开始执行测试用例：test_demo ==========')
        cls.test_case_data = cls.load_test_case_data()
        cls.steps_dict = {step['id']: step for step in cls.test_case_data['steps']}
        cls.session_vars = {}
        cls.global_vars = Globals.get_data()
        cls.VR = VariableResolver(global_vars=cls.global_vars, session_vars=cls.session_vars)
        log.info('Setup completed for TestDemo')

    @staticmethod
    def load_test_case_data():
        with open(r'tests/demo_test.yaml', 'r', encoding='utf-8') as file:
            test_case_data = yaml.safe_load(file)['testcase']
        return test_case_data

    @allure.story('demo')
    def test_demo(self):
        log.info('Starting test_demo')
        # Step: step1
        log.info(f'开始执行 step: step1')
        step1 = self.steps_dict.get('step1')
        project_config = self.global_vars.get('demo_test.yaml')
        response = RequestHandler.send_request(
            method=step1['method'],
            url=project_config['host'] + self.VR.process_data(step1['path']),
            headers=self.VR.process_data(step1.get('headers')),
            data=self.VR.process_data(step1.get('data')),
            params=self.VR.process_data(step1.get('params')),
            files=self.VR.process_data(step1.get('files'))
        )
        log.info(f'step1 请求结果为：{response}')
        self.session_vars['step1'] = response

        log.info(f"Test case test_demo completed.")
