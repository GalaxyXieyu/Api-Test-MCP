# Auto-generated test module for report_api_v2
from atf.core.log_manager import log
from atf.core.globals import Globals
from atf.core.variable_resolver import VariableResolver
from atf.core.request_handler import RequestHandler
from atf.core.assert_handler import AssertHandler
import allure
import yaml

@allure.epic('merchant')
class TestReportApiV2:
    @classmethod
    def setup_class(cls):
        log.info('========== 开始执行测试用例：test_report_api_v2 ==========')
        cls.test_case_data = cls.load_test_case_data()
        cls.steps_dict = {step['id']: step for step in cls.test_case_data['steps']}
        cls.session_vars = {}
        cls.global_vars = Globals.get_data()
        cls.VR = VariableResolver(global_vars=cls.global_vars, session_vars=cls.session_vars)
        log.info('Setup completed for TestReportApiV2')

    @staticmethod
    def load_test_case_data():
        with open(r'tests/merchant/demo/test_report_api_v2.yaml', 'r', encoding='utf-8') as file:
            test_case_data = yaml.safe_load(file)['testcase']
        return test_case_data

    @allure.story('report_api_v2')
    def test_report_api_v2(self):
        log.info('Starting test_report_api_v2')
        # Step: get_report
        log.info(f'开始执行 step: get_report')
        get_report = self.steps_dict.get('get_report')
        project_config = self.global_vars.get('merchant')
        response = RequestHandler.send_request(
            method=get_report['method'],
            url=project_config['host'] + self.VR.process_data(get_report['path']),
            headers=self.VR.process_data(get_report.get('headers')),
            data=self.VR.process_data(get_report.get('data')),
            params=self.VR.process_data(get_report.get('params')),
            files=self.VR.process_data(get_report.get('files'))
        )
        log.info(f'get_report 请求结果为：{response}')
        self.session_vars['get_report'] = response
        db_config = project_config.get('mysql')
        AssertHandler().handle_assertion(
            asserts=self.VR.process_data(get_report['assert']),
            response=response,
            db_config=db_config
        )


        log.info(f"Test case test_report_api_v2 completed.")
