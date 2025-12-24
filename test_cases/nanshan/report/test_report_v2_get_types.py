# Auto-generated test module for report_v2_get_types
from atf.core.log_manager import log
from atf.core.globals import Globals
from atf.core.variable_resolver import VariableResolver
from atf.core.request_handler import RequestHandler
from atf.core.assert_handler import AssertHandler
import allure
import yaml

@allure.epic('nanshan')
class TestReportV2GetTypes:
    @classmethod
    def setup_class(cls):
        log.info('========== 开始执行测试用例：test_report_v2_get_types (获取支持的报告类型列表) ==========')
        cls.test_case_data = cls.load_test_case_data()
        cls.steps_dict = {step['id']: step for step in cls.test_case_data['steps']}
        cls.session_vars = {}
        cls.global_vars = Globals.get_data()
        cls.VR = VariableResolver(global_vars=cls.global_vars, session_vars=cls.session_vars)
        log.info('Setup completed for TestReportV2GetTypes')

    @staticmethod
    def load_test_case_data():
        with open(r'tests/nanshan/report/test_report_v2_types.yaml', 'r', encoding='utf-8') as file:
            test_case_data = yaml.safe_load(file)['testcase']
        return test_case_data

    @allure.story('report_v2_get_types')
    def test_report_v2_get_types(self):
        log.info('Starting test_report_v2_get_types')
        # Step: get_report_types
        log.info(f'开始执行 step: get_report_types')
        get_report_types = self.steps_dict.get('get_report_types')
        project_config = self.global_vars.get('nanshan')
        response = RequestHandler.send_request(
            method=get_report_types['method'],
            url=project_config['host'] + self.VR.process_data(get_report_types['path']),
            headers=self.VR.process_data(get_report_types.get('headers')),
            data=self.VR.process_data(get_report_types.get('data')),
            params=self.VR.process_data(get_report_types.get('params')),
            files=self.VR.process_data(get_report_types.get('files'))
        )
        log.info(f'get_report_types 请求结果为：{response}')
        self.session_vars['get_report_types'] = response
        db_config = project_config.get('mysql')
        AssertHandler().handle_assertion(
            asserts=self.VR.process_data(get_report_types['assert']),
            response=response,
            db_config=db_config
        )


        log.info(f"Test case test_report_v2_get_types completed.")
