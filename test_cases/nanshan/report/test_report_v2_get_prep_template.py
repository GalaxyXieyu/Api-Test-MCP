# Auto-generated test module for report_v2_get_prep_template
from atf.core.log_manager import log
from atf.core.globals import Globals
from atf.core.variable_resolver import VariableResolver
from atf.core.request_handler import RequestHandler
from atf.core.assert_handler import AssertHandler
import allure
import yaml

@allure.epic('nanshan')
class TestReportV2GetPrepTemplate:
    @classmethod
    def setup_class(cls):
        log.info('========== 开始执行测试用例：test_report_v2_get_prep_template (获取前期报告模板) ==========')
        cls.test_case_data = cls.load_test_case_data()
        cls.steps_dict = {step['id']: step for step in cls.test_case_data['steps']}
        cls.session_vars = {}
        cls.global_vars = Globals.get_data()
        cls.VR = VariableResolver(global_vars=cls.global_vars, session_vars=cls.session_vars)
        log.info('Setup completed for TestReportV2GetPrepTemplate')

    @staticmethod
    def load_test_case_data():
        with open(r'tests/nanshan/report/test_report_v2_template_prep.yaml', 'r', encoding='utf-8') as file:
            test_case_data = yaml.safe_load(file)['testcase']
        return test_case_data

    @allure.story('report_v2_get_prep_template')
    def test_report_v2_get_prep_template(self):
        log.info('Starting test_report_v2_get_prep_template')
        # Step: get_prep_template
        log.info(f'开始执行 step: get_prep_template')
        get_prep_template = self.steps_dict.get('get_prep_template')
        project_config = self.global_vars.get('nanshan')
        response = RequestHandler.send_request(
            method=get_prep_template['method'],
            url=project_config['host'] + self.VR.process_data(get_prep_template['path']),
            headers=self.VR.process_data(get_prep_template.get('headers')),
            data=self.VR.process_data(get_prep_template.get('data')),
            params=self.VR.process_data(get_prep_template.get('params')),
            files=self.VR.process_data(get_prep_template.get('files'))
        )
        log.info(f'get_prep_template 请求结果为：{response}')
        self.session_vars['get_prep_template'] = response
        db_config = project_config.get('mysql')
        AssertHandler().handle_assertion(
            asserts=self.VR.process_data(get_prep_template['assert']),
            response=response,
            db_config=db_config
        )


        log.info(f"Test case test_report_v2_get_prep_template completed.")
