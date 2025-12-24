# Auto-generated test module for report_v2_list_reports_by_type_prep
from atf.core.log_manager import log
from atf.core.globals import Globals
from atf.core.variable_resolver import VariableResolver
from atf.core.request_handler import RequestHandler
from atf.core.assert_handler import AssertHandler
import allure
import yaml

@allure.epic('nanshan')
class TestReportV2ListReportsByTypePrep:
    @classmethod
    def setup_class(cls):
        log.info('========== 开始执行测试用例：test_report_v2_list_reports_by_type_prep (按报告类型筛选报告列表-前期报告) ==========')
        cls.test_case_data = cls.load_test_case_data()
        cls.steps_dict = {step['id']: step for step in cls.test_case_data['steps']}
        cls.session_vars = {}
        cls.global_vars = Globals.get_data()
        cls.VR = VariableResolver(global_vars=cls.global_vars, session_vars=cls.session_vars)
        log.info('Setup completed for TestReportV2ListReportsByTypePrep')

    @staticmethod
    def load_test_case_data():
        with open(r'tests/nanshan/report/test_report_v2_list_reports_prep.yaml', 'r', encoding='utf-8') as file:
            test_case_data = yaml.safe_load(file)['testcase']
        return test_case_data

    @allure.story('report_v2_list_reports_by_type_prep')
    def test_report_v2_list_reports_by_type_prep(self):
        log.info('Starting test_report_v2_list_reports_by_type_prep')
        # Step: list_prep_reports
        log.info(f'开始执行 step: list_prep_reports')
        list_prep_reports = self.steps_dict.get('list_prep_reports')
        project_config = self.global_vars.get('nanshan')
        response = RequestHandler.send_request(
            method=list_prep_reports['method'],
            url=project_config['host'] + self.VR.process_data(list_prep_reports['path']),
            headers=self.VR.process_data(list_prep_reports.get('headers')),
            data=self.VR.process_data(list_prep_reports.get('data')),
            params=self.VR.process_data(list_prep_reports.get('params')),
            files=self.VR.process_data(list_prep_reports.get('files'))
        )
        log.info(f'list_prep_reports 请求结果为：{response}')
        self.session_vars['list_prep_reports'] = response
        db_config = project_config.get('mysql')
        AssertHandler().handle_assertion(
            asserts=self.VR.process_data(list_prep_reports['assert']),
            response=response,
            db_config=db_config
        )


        log.info(f"Test case test_report_v2_list_reports_by_type_prep completed.")
