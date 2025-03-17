# Auto-generated test module for goods_list_and_statusTotals
from utils.log_manager import log
from utils.globals import Globals
from utils.variable_resolver import VariableResolver
from utils.request_handler import RequestHandler
from utils.assert_handler import AssertHandler
import allure
import yaml

@allure.epic('B端APP')
@allure.feature('设备管理')
class TestGoodsListAndStatustotals:
    @classmethod
    def setup_class(cls):
        log.info('========== 开始执行测试用例：test_goods_list_and_statusTotals (设备列表页接口) ==========')
        cls.test_case_data = cls.load_test_case_data()
        cls.steps_dict = {step['id']: step for step in cls.test_case_data['steps']}
        cls.session_vars = {}
        cls.global_vars = Globals.get_data()
        cls.VR = VariableResolver(global_vars=cls.global_vars, session_vars=cls.session_vars)
        log.info('Setup completed for TestGoodsListAndStatustotals')

    @staticmethod
    def load_test_case_data():
        with open(r'tests/merchant\device_management\test_goods_list_and_statusTotals.yaml', 'r', encoding='utf-8') as file:
            test_case_data = yaml.safe_load(file)['testcase']
        return test_case_data

    @allure.story('设备列表')
    def test_goods_list_and_statusTotals(self):
        log.info('Starting test_goods_list_and_statusTotals')
        # Step: goods_getGoodsCountPercentVOList
        log.info(f'开始执行 step: goods_getGoodsCountPercentVOList')
        goods_getGoodsCountPercentVOList = self.steps_dict.get('goods_getGoodsCountPercentVOList')
        project_config = self.global_vars.get('merchant')
        response = RequestHandler.send_request(
            method=goods_getGoodsCountPercentVOList['method'],
            url=project_config['host'] + self.VR.process_data(goods_getGoodsCountPercentVOList['path']),
            headers=self.VR.process_data(goods_getGoodsCountPercentVOList.get('headers')),
            data=self.VR.process_data(goods_getGoodsCountPercentVOList.get('data')),
            params=self.VR.process_data(goods_getGoodsCountPercentVOList.get('params')),
            files=self.VR.process_data(goods_getGoodsCountPercentVOList.get('files'))
        )
        log.info(f'goods_getGoodsCountPercentVOList 请求结果为：{response}')
        self.session_vars['goods_getGoodsCountPercentVOList'] = response
        db_config = project_config.get('mysql')
        AssertHandler().handle_assertion(
            asserts=self.VR.process_data(goods_getGoodsCountPercentVOList['assert']),
            response=response,
            db_config=db_config
        )

        # Step: goods_list_v2
        log.info(f'开始执行 step: goods_list_v2')
        goods_list_v2 = self.steps_dict.get('goods_list_v2')
        project_config = self.global_vars.get('merchant')
        response = RequestHandler.send_request(
            method=goods_list_v2['method'],
            url=project_config['host'] + self.VR.process_data(goods_list_v2['path']),
            headers=self.VR.process_data(goods_list_v2.get('headers')),
            data=self.VR.process_data(goods_list_v2.get('data')),
            params=self.VR.process_data(goods_list_v2.get('params')),
            files=self.VR.process_data(goods_list_v2.get('files'))
        )
        log.info(f'goods_list_v2 请求结果为：{response}')
        self.session_vars['goods_list_v2'] = response
        db_config = project_config.get('mysql')
        AssertHandler().handle_assertion(
            asserts=self.VR.process_data(goods_list_v2['assert']),
            response=response,
            db_config=db_config
        )

        # Step: goods_statusTotals_v3
        log.info(f'开始执行 step: goods_statusTotals_v3')
        goods_statusTotals_v3 = self.steps_dict.get('goods_statusTotals_v3')
        project_config = self.global_vars.get('merchant')
        response = RequestHandler.send_request(
            method=goods_statusTotals_v3['method'],
            url=project_config['host'] + self.VR.process_data(goods_statusTotals_v3['path']),
            headers=self.VR.process_data(goods_statusTotals_v3.get('headers')),
            data=self.VR.process_data(goods_statusTotals_v3.get('data')),
            params=self.VR.process_data(goods_statusTotals_v3.get('params')),
            files=self.VR.process_data(goods_statusTotals_v3.get('files'))
        )
        log.info(f'goods_statusTotals_v3 请求结果为：{response}')
        self.session_vars['goods_statusTotals_v3'] = response
        db_config = project_config.get('mysql')
        AssertHandler().handle_assertion(
            asserts=self.VR.process_data(goods_statusTotals_v3['assert']),
            response=response,
            db_config=db_config
        )


        log.info(f"Test case test_goods_list_and_statusTotals completed.")
