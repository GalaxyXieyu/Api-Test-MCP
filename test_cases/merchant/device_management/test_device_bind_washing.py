# Auto-generated test module for device_bind_washing
from utils.log_manager import log
from utils.globals import Globals
from utils.variable_resolver import VariableResolver
from utils.request_handler import RequestHandler
from utils.assert_handler import AssertHandler
import allure
import yaml

@allure.epic('B端APP')
@allure.feature('设备管理')
class TestDeviceBindWashing:
    @classmethod
    def setup_class(cls):
        log.info('========== 开始执行测试用例：test_device_bind_washing (新增xxx) ==========')
        cls.test_case_data = cls.load_test_case_data()
        cls.steps_dict = {step['id']: step for step in cls.test_case_data['steps']}
        cls.session_vars = {}
        cls.global_vars = Globals.get_data()
        cls.VR = VariableResolver(global_vars=cls.global_vars, session_vars=cls.session_vars)
        log.info('Setup completed for TestDeviceBindWashing')

    @staticmethod
    def load_test_case_data():
        with open(r'tests/merchant\device_management\test_device_bind_washing.yaml', 'r', encoding='utf-8') as file:
            test_case_data = yaml.safe_load(file)['testcase']
        return test_case_data

    @allure.story('新增xxx')
    def test_device_bind_washing(self):
        log.info('Starting test_device_bind_washing')
        # Step: spu_deviceType
        log.info(f'开始执行 step: spu_deviceType')
        spu_deviceType = self.steps_dict.get('spu_deviceType')
        project_config = self.global_vars.get('merchant')
        response = RequestHandler.send_request(
            method=spu_deviceType['method'],
            url=project_config['host'] + self.VR.process_data(spu_deviceType['path']),
            headers=self.VR.process_data(spu_deviceType.get('headers')),
            data=self.VR.process_data(spu_deviceType.get('data')),
            params=self.VR.process_data(spu_deviceType.get('params')),
            files=self.VR.process_data(spu_deviceType.get('files'))
        )
        log.info(f'spu_deviceType 请求结果为：{response}')
        self.session_vars['spu_deviceType'] = response
        db_config = project_config.get('mysql')
        AssertHandler().handle_assertion(
            asserts=self.VR.process_data(spu_deviceType['assert']),
            response=response,
            db_config=db_config
        )

        # Step: shop_shopSelectList_v2
        log.info(f'开始执行 step: shop_shopSelectList_v2')
        shop_shopSelectList_v2 = self.steps_dict.get('shop_shopSelectList_v2')
        project_config = self.global_vars.get('merchant')
        response = RequestHandler.send_request(
            method=shop_shopSelectList_v2['method'],
            url=project_config['host'] + self.VR.process_data(shop_shopSelectList_v2['path']),
            headers=self.VR.process_data(shop_shopSelectList_v2.get('headers')),
            data=self.VR.process_data(shop_shopSelectList_v2.get('data')),
            params=self.VR.process_data(shop_shopSelectList_v2.get('params')),
            files=self.VR.process_data(shop_shopSelectList_v2.get('files'))
        )
        log.info(f'shop_shopSelectList_v2 请求结果为：{response}')
        self.session_vars['shop_shopSelectList_v2'] = response
        db_config = project_config.get('mysql')
        AssertHandler().handle_assertion(
            asserts=self.VR.process_data(shop_shopSelectList_v2['assert']),
            response=response,
            db_config=db_config
        )

        # Step: spu_list_split
        log.info(f'开始执行 step: spu_list_split')
        spu_list_split = self.steps_dict.get('spu_list_split')
        project_config = self.global_vars.get('merchant')
        response = RequestHandler.send_request(
            method=spu_list_split['method'],
            url=project_config['host'] + self.VR.process_data(spu_list_split['path']),
            headers=self.VR.process_data(spu_list_split.get('headers')),
            data=self.VR.process_data(spu_list_split.get('data')),
            params=self.VR.process_data(spu_list_split.get('params')),
            files=self.VR.process_data(spu_list_split.get('files'))
        )
        log.info(f'spu_list_split 请求结果为：{response}')
        self.session_vars['spu_list_split'] = response
        db_config = project_config.get('mysql')
        AssertHandler().handle_assertion(
            asserts=self.VR.process_data(spu_list_split['assert']),
            response=response,
            db_config=db_config
        )

        # Step: position_getDetail
        log.info(f'开始执行 step: position_getDetail')
        position_getDetail = self.steps_dict.get('position_getDetail')
        project_config = self.global_vars.get('merchant')
        response = RequestHandler.send_request(
            method=position_getDetail['method'],
            url=project_config['host'] + self.VR.process_data(position_getDetail['path']),
            headers=self.VR.process_data(position_getDetail.get('headers')),
            data=self.VR.process_data(position_getDetail.get('data')),
            params=self.VR.process_data(position_getDetail.get('params')),
            files=self.VR.process_data(position_getDetail.get('files'))
        )
        log.info(f'position_getDetail 请求结果为：{response}')
        self.session_vars['position_getDetail'] = response
        db_config = project_config.get('mysql')
        AssertHandler().handle_assertion(
            asserts=self.VR.process_data(position_getDetail['assert']),
            response=response,
            db_config=db_config
        )

        # Step: spu_sku_v2
        log.info(f'开始执行 step: spu_sku_v2')
        spu_sku_v2 = self.steps_dict.get('spu_sku_v2')
        project_config = self.global_vars.get('merchant')
        response = RequestHandler.send_request(
            method=spu_sku_v2['method'],
            url=project_config['host'] + self.VR.process_data(spu_sku_v2['path']),
            headers=self.VR.process_data(spu_sku_v2.get('headers')),
            data=self.VR.process_data(spu_sku_v2.get('data')),
            params=self.VR.process_data(spu_sku_v2.get('params')),
            files=self.VR.process_data(spu_sku_v2.get('files'))
        )
        log.info(f'spu_sku_v2 请求结果为：{response}')
        self.session_vars['spu_sku_v2'] = response
        db_config = project_config.get('mysql')
        AssertHandler().handle_assertion(
            asserts=self.VR.process_data(spu_sku_v2['assert']),
            response=response,
            db_config=db_config
        )

        # Step: device_bind
        log.info(f'开始执行 step: device_bind')
        device_bind = self.steps_dict.get('device_bind')
        project_config = self.global_vars.get('merchant')
        response = RequestHandler.send_request(
            method=device_bind['method'],
            url=project_config['host'] + self.VR.process_data(device_bind['path']),
            headers=self.VR.process_data(device_bind.get('headers')),
            data=self.VR.process_data(device_bind.get('data')),
            params=self.VR.process_data(device_bind.get('params')),
            files=self.VR.process_data(device_bind.get('files'))
        )
        log.info(f'device_bind 请求结果为：{response}')
        self.session_vars['device_bind'] = response
        db_config = project_config.get('mysql')
        AssertHandler().handle_assertion(
            asserts=self.VR.process_data(device_bind['assert']),
            response=response,
            db_config=db_config
        )

        # Step: goods_delete
        log.info(f'开始执行 step: goods_delete')
        goods_delete = self.steps_dict.get('goods_delete')
        project_config = self.global_vars.get('merchant')
        response = RequestHandler.send_request(
            method=goods_delete['method'],
            url=project_config['host'] + self.VR.process_data(goods_delete['path']),
            headers=self.VR.process_data(goods_delete.get('headers')),
            data=self.VR.process_data(goods_delete.get('data')),
            params=self.VR.process_data(goods_delete.get('params')),
            files=self.VR.process_data(goods_delete.get('files'))
        )
        log.info(f'goods_delete 请求结果为：{response}')
        self.session_vars['goods_delete'] = response
        db_config = project_config.get('mysql')
        AssertHandler().handle_assertion(
            asserts=self.VR.process_data(goods_delete['assert']),
            response=response,
            db_config=db_config
        )


        log.info(f"Test case test_device_bind_washing completed.")
