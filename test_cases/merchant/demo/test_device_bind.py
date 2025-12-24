# Auto-generated test module for device_bind
from atf.core.log_manager import log
from atf.core.globals import Globals
from atf.core.variable_resolver import VariableResolver
from atf.core.request_handler import RequestHandler
from atf.core.assert_handler import AssertHandler
import allure
import yaml

@allure.epic('merchant')
class TestDeviceBind:
    @classmethod
    def setup_class(cls):
        log.info('========== 开始执行测试用例：test_device_bind (绑定设备) ==========')
        cls.test_case_data = cls.load_test_case_data()
        cls.steps_dict = {step['id']: step for step in cls.test_case_data['steps']}
        cls.session_vars = {}
        cls.global_vars = Globals.get_data()
        cls.VR = VariableResolver(global_vars=cls.global_vars, session_vars=cls.session_vars)
        log.info('Setup completed for TestDeviceBind')

    @staticmethod
    def load_test_case_data():
        with open(r'tests/merchant/demo/test_device_bind.yaml', 'r', encoding='utf-8') as file:
            test_case_data = yaml.safe_load(file)['testcase']
        return test_case_data

    @allure.story('device_bind')
    def test_device_bind(self):
        log.info('Starting test_device_bind')
        # Step: bind_device
        log.info(f'开始执行 step: bind_device')
        bind_device = self.steps_dict.get('bind_device')
        project_config = self.global_vars.get('merchant')
        response = RequestHandler.send_request(
            method=bind_device['method'],
            url=project_config['host'] + self.VR.process_data(bind_device['path']),
            headers=self.VR.process_data(bind_device.get('headers')),
            data=self.VR.process_data(bind_device.get('data')),
            params=self.VR.process_data(bind_device.get('params')),
            files=self.VR.process_data(bind_device.get('files'))
        )
        log.info(f'bind_device 请求结果为：{response}')
        self.session_vars['bind_device'] = response
        db_config = project_config.get('mysql')
        AssertHandler().handle_assertion(
            asserts=self.VR.process_data(bind_device['assert']),
            response=response,
            db_config=db_config
        )


        log.info(f"Test case test_device_bind completed.")
