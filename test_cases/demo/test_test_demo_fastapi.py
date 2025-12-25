# Auto-generated test module for test_demo_fastapi
from atf.core.log_manager import log
from atf.core.globals import Globals
from atf.core.variable_resolver import VariableResolver
from atf.core.request_handler import RequestHandler
from atf.core.assert_handler import AssertHandler
import allure
import yaml

@allure.epic('demo')
class TestTestDemoFastapi:
    @classmethod
    def setup_class(cls):
        log.info('========== 开始执行测试用例：test_test_demo_fastapi (测试 FastAPI 计算器接口) ==========')
        cls.test_case_data = cls.load_test_case_data()
        cls.steps_dict = {step['id']: step for step in cls.test_case_data['steps']}
        cls.session_vars = {}
        cls.global_vars = Globals.get_data()
        cls.testcase_host = 'http://localhost:48080'
        cls.VR = VariableResolver(global_vars=cls.global_vars, session_vars=cls.session_vars)
        log.info('Setup completed for TestTestDemoFastapi')

    @staticmethod
    def load_test_case_data():
        with open(r'tests/demo/test_demo_fastapi.yaml', 'r', encoding='utf-8') as file:
            test_case_data = yaml.safe_load(file)['testcase']
        return test_case_data

    @allure.story('test_demo_fastapi')
    def test_test_demo_fastapi(self):
        log.info('Starting test_test_demo_fastapi')
        # Step: health_check
        log.info(f'开始执行 step: health_check')
        health_check = self.steps_dict.get('health_check')
        step_host = self.testcase_host
        response = RequestHandler.send_request(
            method=health_check['method'],
            url=step_host + self.VR.process_data(health_check['path']),
            headers=self.VR.process_data(health_check.get('headers')),
            data=self.VR.process_data(health_check.get('data')),
            params=self.VR.process_data(health_check.get('params')),
            files=self.VR.process_data(health_check.get('files'))
        )
        log.info(f'health_check 请求结果为：{response}')
        self.session_vars['health_check'] = response
        db_config = None
        AssertHandler().handle_assertion(
            asserts=self.VR.process_data(health_check['assert']),
            response=response,
            db_config=db_config
        )

        # Step: add_calculation
        log.info(f'开始执行 step: add_calculation')
        add_calculation = self.steps_dict.get('add_calculation')
        step_host = self.testcase_host
        response = RequestHandler.send_request(
            method=add_calculation['method'],
            url=step_host + self.VR.process_data(add_calculation['path']),
            headers=self.VR.process_data(add_calculation.get('headers')),
            data=self.VR.process_data(add_calculation.get('data')),
            params=self.VR.process_data(add_calculation.get('params')),
            files=self.VR.process_data(add_calculation.get('files'))
        )
        log.info(f'add_calculation 请求结果为：{response}')
        self.session_vars['add_calculation'] = response
        db_config = None
        AssertHandler().handle_assertion(
            asserts=self.VR.process_data(add_calculation['assert']),
            response=response,
            db_config=db_config
        )

        # Step: subtract_calculation
        log.info(f'开始执行 step: subtract_calculation')
        subtract_calculation = self.steps_dict.get('subtract_calculation')
        step_host = self.testcase_host
        response = RequestHandler.send_request(
            method=subtract_calculation['method'],
            url=step_host + self.VR.process_data(subtract_calculation['path']),
            headers=self.VR.process_data(subtract_calculation.get('headers')),
            data=self.VR.process_data(subtract_calculation.get('data')),
            params=self.VR.process_data(subtract_calculation.get('params')),
            files=self.VR.process_data(subtract_calculation.get('files'))
        )
        log.info(f'subtract_calculation 请求结果为：{response}')
        self.session_vars['subtract_calculation'] = response
        db_config = None
        AssertHandler().handle_assertion(
            asserts=self.VR.process_data(subtract_calculation['assert']),
            response=response,
            db_config=db_config
        )

        # Step: get_users
        log.info(f'开始执行 step: get_users')
        get_users = self.steps_dict.get('get_users')
        step_host = self.testcase_host
        response = RequestHandler.send_request(
            method=get_users['method'],
            url=step_host + self.VR.process_data(get_users['path']),
            headers=self.VR.process_data(get_users.get('headers')),
            data=self.VR.process_data(get_users.get('data')),
            params=self.VR.process_data(get_users.get('params')),
            files=self.VR.process_data(get_users.get('files'))
        )
        log.info(f'get_users 请求结果为：{response}')
        self.session_vars['get_users'] = response
        db_config = None
        AssertHandler().handle_assertion(
            asserts=self.VR.process_data(get_users['assert']),
            response=response,
            db_config=db_config
        )


        log.info(f"Test case test_test_demo_fastapi completed.")
