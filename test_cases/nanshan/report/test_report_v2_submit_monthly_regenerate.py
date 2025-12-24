# Auto-generated test module for report_v2_submit_monthly_regenerate
from atf.core.log_manager import log
from atf.core.globals import Globals
from atf.core.variable_resolver import VariableResolver
from atf.core.request_handler import RequestHandler
from atf.core.assert_handler import AssertHandler
import allure
import yaml

@allure.epic('nanshan')
class TestReportV2SubmitMonthlyRegenerate:
    @classmethod
    def setup_class(cls):
        log.info('========== 开始执行测试用例：test_report_v2_submit_monthly_regenerate (提交月报生成任务(regenerate模式)) ==========')
        cls.test_case_data = cls.load_test_case_data()
        cls.steps_dict = {step['id']: step for step in cls.test_case_data['steps']}
        cls.session_vars = {}
        cls.global_vars = Globals.get_data()
        cls.VR = VariableResolver(global_vars=cls.global_vars, session_vars=cls.session_vars)
        log.info('Setup completed for TestReportV2SubmitMonthlyRegenerate')

    @staticmethod
    def load_test_case_data():
        with open(r'tests/nanshan/report/test_report_v2_submit_monthly_regenerate.yaml', 'r', encoding='utf-8') as file:
            test_case_data = yaml.safe_load(file)['testcase']
        return test_case_data

    @allure.story('report_v2_submit_monthly_regenerate')
    def test_report_v2_submit_monthly_regenerate(self):
        log.info('Starting test_report_v2_submit_monthly_regenerate')
        # Step: submit_monthly_regenerate
        log.info(f'开始执行 step: submit_monthly_regenerate')
        submit_monthly_regenerate = self.steps_dict.get('submit_monthly_regenerate')
        project_config = self.global_vars.get('nanshan')
        response = RequestHandler.send_request(
            method=submit_monthly_regenerate['method'],
            url=project_config['host'] + self.VR.process_data(submit_monthly_regenerate['path']),
            headers=self.VR.process_data(submit_monthly_regenerate.get('headers')),
            data=self.VR.process_data(submit_monthly_regenerate.get('data')),
            params=self.VR.process_data(submit_monthly_regenerate.get('params')),
            files=self.VR.process_data(submit_monthly_regenerate.get('files'))
        )
        log.info(f'submit_monthly_regenerate 请求结果为：{response}')
        self.session_vars['submit_monthly_regenerate'] = response
        db_config = project_config.get('mysql')
        AssertHandler().handle_assertion(
            asserts=self.VR.process_data(submit_monthly_regenerate['assert']),
            response=response,
            db_config=db_config
        )


        log.info(f"Test case test_report_v2_submit_monthly_regenerate completed.")
