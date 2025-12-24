# Auto-generated test module for report_v2_get_report_by_task
from atf.core.log_manager import log
from atf.core.globals import Globals
from atf.core.variable_resolver import VariableResolver
from atf.core.request_handler import RequestHandler
from atf.core.assert_handler import AssertHandler
import allure
import yaml

@allure.epic('nanshan')
class TestReportV2GetReportByTask:
    @classmethod
    def setup_class(cls):
        log.info('========== 开始执行测试用例：test_report_v2_get_report_by_task (根据 task_id 获取报告详情) ==========')
        cls.test_case_data = cls.load_test_case_data()
        cls.steps_dict = {step['id']: step for step in cls.test_case_data['steps']}
        cls.session_vars = {}
        cls.global_vars = Globals.get_data()
        cls.VR = VariableResolver(global_vars=cls.global_vars, session_vars=cls.session_vars)
        log.info('Setup completed for TestReportV2GetReportByTask')

    @staticmethod
    def load_test_case_data():
        with open(r'tests/nanshan/report/test_report_v2_get_by_task.yaml', 'r', encoding='utf-8') as file:
            test_case_data = yaml.safe_load(file)['testcase']
        return test_case_data

    @allure.story('report_v2_get_report_by_task')
    def test_report_v2_get_report_by_task(self):
        log.info('Starting test_report_v2_get_report_by_task')
        # Step: get_report_by_task
        log.info(f'开始执行 step: get_report_by_task')
        get_report_by_task = self.steps_dict.get('get_report_by_task')
        project_config = self.global_vars.get('nanshan')
        response = RequestHandler.send_request(
            method=get_report_by_task['method'],
            url=project_config['host'] + self.VR.process_data(get_report_by_task['path']),
            headers=self.VR.process_data(get_report_by_task.get('headers')),
            data=self.VR.process_data(get_report_by_task.get('data')),
            params=self.VR.process_data(get_report_by_task.get('params')),
            files=self.VR.process_data(get_report_by_task.get('files'))
        )
        log.info(f'get_report_by_task 请求结果为：{response}')
        self.session_vars['get_report_by_task'] = response
        db_config = project_config.get('mysql')
        AssertHandler().handle_assertion(
            asserts=self.VR.process_data(get_report_by_task['assert']),
            response=response,
            db_config=db_config
        )


        log.info(f"Test case test_report_v2_get_report_by_task completed.")
