# Auto-generated test module for washing_machine_ordering
from utils.log_manager import log
from utils.globals import Globals
from utils.variable_resolver import VariableResolver
from utils.request_handler import RequestHandler
from utils.assert_handler import AssertHandler
from utils.teardown_handler import TeardownHandler
from utils.project_login_handler import ProjectLoginHandler
import allure
import yaml

@allure.epic('C端')
@allure.feature('下单流程')
class TestWashingMachineOrdering:
    @classmethod
    def setup_class(cls):
        log.info('========== 开始执行测试用例：test_washing_machine_ordering (xxx下单) ==========')
        cls.test_case_data = cls.load_test_case_data()
        cls.login_handler = ProjectLoginHandler()
        cls.teardowns_dict = {teardown['id']: teardown for teardown in cls.test_case_data['teardowns']}
        for teardown in cls.test_case_data.get('teardowns', []):
            project = teardown.get('project')
            if project:
                cls.login_handler.check_and_login_project(project, Globals.get('env'))
        cls.steps_dict = {step['id']: step for step in cls.test_case_data['steps']}
        cls.session_vars = {}
        cls.global_vars = Globals.get_data()
        cls.VR = VariableResolver(global_vars=cls.global_vars, session_vars=cls.session_vars)
        log.info('Setup completed for TestWashingMachineOrdering')

    @staticmethod
    def load_test_case_data():
        with open(r'tests/user\test_washing_machine_ordering.yaml', 'r', encoding='utf-8') as file:
            test_case_data = yaml.safe_load(file)['testcase']
        return test_case_data

    @allure.story('xxx下单')
    def test_washing_machine_ordering(self):
        log.info('Starting test_washing_machine_ordering')
        # Step: slot_get
        log.info(f'开始执行 step: slot_get')
        slot_get = self.steps_dict.get('slot_get')
        project_config = self.global_vars.get('user')
        response = RequestHandler.send_request(
            method=slot_get['method'],
            url=project_config['host'] + self.VR.process_data(slot_get['path']),
            headers=self.VR.process_data(slot_get.get('headers')),
            data=self.VR.process_data(slot_get.get('data')),
            params=self.VR.process_data(slot_get.get('params')),
            files=self.VR.process_data(slot_get.get('files'))
        )
        log.info(f'slot_get 请求结果为：{response}')
        self.session_vars['slot_get'] = response
        db_config = project_config.get('mysql')
        AssertHandler().handle_assertion(
            asserts=self.VR.process_data(slot_get['assert']),
            response=response,
            db_config=db_config
        )

        # Step: position_nearPosition
        log.info(f'开始执行 step: position_nearPosition')
        position_nearPosition = self.steps_dict.get('position_nearPosition')
        project_config = self.global_vars.get('user')
        response = RequestHandler.send_request(
            method=position_nearPosition['method'],
            url=project_config['host'] + self.VR.process_data(position_nearPosition['path']),
            headers=self.VR.process_data(position_nearPosition.get('headers')),
            data=self.VR.process_data(position_nearPosition.get('data')),
            params=self.VR.process_data(position_nearPosition.get('params')),
            files=self.VR.process_data(position_nearPosition.get('files'))
        )
        log.info(f'position_nearPosition 请求结果为：{response}')
        self.session_vars['position_nearPosition'] = response
        db_config = project_config.get('mysql')
        AssertHandler().handle_assertion(
            asserts=self.VR.process_data(position_nearPosition['assert']),
            response=response,
            db_config=db_config
        )

        # Step: trade_underway_stateList
        log.info(f'开始执行 step: trade_underway_stateList')
        trade_underway_stateList = self.steps_dict.get('trade_underway_stateList')
        project_config = self.global_vars.get('user')
        response = RequestHandler.send_request(
            method=trade_underway_stateList['method'],
            url=project_config['host'] + self.VR.process_data(trade_underway_stateList['path']),
            headers=self.VR.process_data(trade_underway_stateList.get('headers')),
            data=self.VR.process_data(trade_underway_stateList.get('data')),
            params=self.VR.process_data(trade_underway_stateList.get('params')),
            files=self.VR.process_data(trade_underway_stateList.get('files'))
        )
        log.info(f'trade_underway_stateList 请求结果为：{response}')
        self.session_vars['trade_underway_stateList'] = response
        db_config = project_config.get('mysql')
        AssertHandler().handle_assertion(
            asserts=self.VR.process_data(trade_underway_stateList['assert']),
            response=response,
            db_config=db_config
        )

        # Step: position_positionDevice
        log.info(f'开始执行 step: position_positionDevice')
        position_positionDevice = self.steps_dict.get('position_positionDevice')
        project_config = self.global_vars.get('user')
        response = RequestHandler.send_request(
            method=position_positionDevice['method'],
            url=project_config['host'] + self.VR.process_data(position_positionDevice['path']),
            headers=self.VR.process_data(position_positionDevice.get('headers')),
            data=self.VR.process_data(position_positionDevice.get('data')),
            params=self.VR.process_data(position_positionDevice.get('params')),
            files=self.VR.process_data(position_positionDevice.get('files'))
        )
        log.info(f'position_positionDevice 请求结果为：{response}')
        self.session_vars['position_positionDevice'] = response
        db_config = project_config.get('mysql')
        AssertHandler().handle_assertion(
            asserts=self.VR.process_data(position_positionDevice['assert']),
            response=response,
            db_config=db_config
        )

        # Step: goods_scan
        log.info(f'开始执行 step: goods_scan')
        goods_scan = self.steps_dict.get('goods_scan')
        project_config = self.global_vars.get('user')
        response = RequestHandler.send_request(
            method=goods_scan['method'],
            url=project_config['host'] + self.VR.process_data(goods_scan['path']),
            headers=self.VR.process_data(goods_scan.get('headers')),
            data=self.VR.process_data(goods_scan.get('data')),
            params=self.VR.process_data(goods_scan.get('params')),
            files=self.VR.process_data(goods_scan.get('files'))
        )
        log.info(f'goods_scan 请求结果为：{response}')
        self.session_vars['goods_scan'] = response
        db_config = project_config.get('mysql')
        AssertHandler().handle_assertion(
            asserts=self.VR.process_data(goods_scan['assert']),
            response=response,
            db_config=db_config
        )

        # Step: appointment_goodsExist
        log.info(f'开始执行 step: appointment_goodsExist')
        appointment_goodsExist = self.steps_dict.get('appointment_goodsExist')
        project_config = self.global_vars.get('user')
        response = RequestHandler.send_request(
            method=appointment_goodsExist['method'],
            url=project_config['host'] + self.VR.process_data(appointment_goodsExist['path']),
            headers=self.VR.process_data(appointment_goodsExist.get('headers')),
            data=self.VR.process_data(appointment_goodsExist.get('data')),
            params=self.VR.process_data(appointment_goodsExist.get('params')),
            files=self.VR.process_data(appointment_goodsExist.get('files'))
        )
        log.info(f'appointment_goodsExist 请求结果为：{response}')
        self.session_vars['appointment_goodsExist'] = response
        db_config = project_config.get('mysql')
        AssertHandler().handle_assertion(
            asserts=self.VR.process_data(appointment_goodsExist['assert']),
            response=response,
            db_config=db_config
        )

        # Step: goods_normal_details
        log.info(f'开始执行 step: goods_normal_details')
        goods_normal_details = self.steps_dict.get('goods_normal_details')
        project_config = self.global_vars.get('user')
        response = RequestHandler.send_request(
            method=goods_normal_details['method'],
            url=project_config['host'] + self.VR.process_data(goods_normal_details['path']),
            headers=self.VR.process_data(goods_normal_details.get('headers')),
            data=self.VR.process_data(goods_normal_details.get('data')),
            params=self.VR.process_data(goods_normal_details.get('params')),
            files=self.VR.process_data(goods_normal_details.get('files'))
        )
        log.info(f'goods_normal_details 请求结果为：{response}')
        self.session_vars['goods_normal_details'] = response
        db_config = project_config.get('mysql')
        AssertHandler().handle_assertion(
            asserts=self.VR.process_data(goods_normal_details['assert']),
            response=response,
            db_config=db_config
        )

        # Step: goods_normal_items
        log.info(f'开始执行 step: goods_normal_items')
        goods_normal_items = self.steps_dict.get('goods_normal_items')
        project_config = self.global_vars.get('user')
        response = RequestHandler.send_request(
            method=goods_normal_items['method'],
            url=project_config['host'] + self.VR.process_data(goods_normal_items['path']),
            headers=self.VR.process_data(goods_normal_items.get('headers')),
            data=self.VR.process_data(goods_normal_items.get('data')),
            params=self.VR.process_data(goods_normal_items.get('params')),
            files=self.VR.process_data(goods_normal_items.get('files'))
        )
        log.info(f'goods_normal_items 请求结果为：{response}')
        self.session_vars['goods_normal_items'] = response
        db_config = project_config.get('mysql')
        AssertHandler().handle_assertion(
            asserts=self.VR.process_data(goods_normal_items['assert']),
            response=response,
            db_config=db_config
        )

        # Step: notice_getNoticeByShopId
        log.info(f'开始执行 step: notice_getNoticeByShopId')
        notice_getNoticeByShopId = self.steps_dict.get('notice_getNoticeByShopId')
        project_config = self.global_vars.get('user')
        response = RequestHandler.send_request(
            method=notice_getNoticeByShopId['method'],
            url=project_config['host'] + self.VR.process_data(notice_getNoticeByShopId['path']),
            headers=self.VR.process_data(notice_getNoticeByShopId.get('headers')),
            data=self.VR.process_data(notice_getNoticeByShopId.get('data')),
            params=self.VR.process_data(notice_getNoticeByShopId.get('params')),
            files=self.VR.process_data(notice_getNoticeByShopId.get('files'))
        )
        log.info(f'notice_getNoticeByShopId 请求结果为：{response}')
        self.session_vars['notice_getNoticeByShopId'] = response
        db_config = project_config.get('mysql')
        AssertHandler().handle_assertion(
            asserts=self.VR.process_data(notice_getNoticeByShopId['assert']),
            response=response,
            db_config=db_config
        )

        # Step: goods_stateList
        log.info(f'开始执行 step: goods_stateList')
        goods_stateList = self.steps_dict.get('goods_stateList')
        project_config = self.global_vars.get('user')
        response = RequestHandler.send_request(
            method=goods_stateList['method'],
            url=project_config['host'] + self.VR.process_data(goods_stateList['path']),
            headers=self.VR.process_data(goods_stateList.get('headers')),
            data=self.VR.process_data(goods_stateList.get('data')),
            params=self.VR.process_data(goods_stateList.get('params')),
            files=self.VR.process_data(goods_stateList.get('files'))
        )
        log.info(f'goods_stateList 请求结果为：{response}')
        self.session_vars['goods_stateList'] = response
        db_config = project_config.get('mysql')
        AssertHandler().handle_assertion(
            asserts=self.VR.process_data(goods_stateList['assert']),
            response=response,
            db_config=db_config
        )

        # Step: activity_queryAndExecute
        log.info(f'开始执行 step: activity_queryAndExecute')
        activity_queryAndExecute = self.steps_dict.get('activity_queryAndExecute')
        project_config = self.global_vars.get('user')
        response = RequestHandler.send_request(
            method=activity_queryAndExecute['method'],
            url=project_config['host'] + self.VR.process_data(activity_queryAndExecute['path']),
            headers=self.VR.process_data(activity_queryAndExecute.get('headers')),
            data=self.VR.process_data(activity_queryAndExecute.get('data')),
            params=self.VR.process_data(activity_queryAndExecute.get('params')),
            files=self.VR.process_data(activity_queryAndExecute.get('files'))
        )
        log.info(f'activity_queryAndExecute 请求结果为：{response}')
        self.session_vars['activity_queryAndExecute'] = response
        db_config = project_config.get('mysql')
        AssertHandler().handle_assertion(
            asserts=self.VR.process_data(activity_queryAndExecute['assert']),
            response=response,
            db_config=db_config
        )

        # Step: trade_scanOrderCreate
        log.info(f'开始执行 step: trade_scanOrderCreate')
        trade_scanOrderCreate = self.steps_dict.get('trade_scanOrderCreate')
        project_config = self.global_vars.get('user')
        response = RequestHandler.send_request(
            method=trade_scanOrderCreate['method'],
            url=project_config['host'] + self.VR.process_data(trade_scanOrderCreate['path']),
            headers=self.VR.process_data(trade_scanOrderCreate.get('headers')),
            data=self.VR.process_data(trade_scanOrderCreate.get('data')),
            params=self.VR.process_data(trade_scanOrderCreate.get('params')),
            files=self.VR.process_data(trade_scanOrderCreate.get('files'))
        )
        log.info(f'trade_scanOrderCreate 请求结果为：{response}')
        self.session_vars['trade_scanOrderCreate'] = response
        db_config = project_config.get('mysql')
        AssertHandler().handle_assertion(
            asserts=self.VR.process_data(trade_scanOrderCreate['assert']),
            response=response,
            db_config=db_config
        )

        # Step: trade_detail
        log.info(f'开始执行 step: trade_detail')
        trade_detail = self.steps_dict.get('trade_detail')
        project_config = self.global_vars.get('user')
        response = RequestHandler.send_request(
            method=trade_detail['method'],
            url=project_config['host'] + self.VR.process_data(trade_detail['path']),
            headers=self.VR.process_data(trade_detail.get('headers')),
            data=self.VR.process_data(trade_detail.get('data')),
            params=self.VR.process_data(trade_detail.get('params')),
            files=self.VR.process_data(trade_detail.get('files'))
        )
        log.info(f'trade_detail 请求结果为：{response}')
        self.session_vars['trade_detail'] = response
        db_config = project_config.get('mysql')
        AssertHandler().handle_assertion(
            asserts=self.VR.process_data(trade_detail['assert']),
            response=response,
            db_config=db_config
        )

        # Step: pay_checkstand
        log.info(f'开始执行 step: pay_checkstand')
        pay_checkstand = self.steps_dict.get('pay_checkstand')
        project_config = self.global_vars.get('user')
        response = RequestHandler.send_request(
            method=pay_checkstand['method'],
            url=project_config['host'] + self.VR.process_data(pay_checkstand['path']),
            headers=self.VR.process_data(pay_checkstand.get('headers')),
            data=self.VR.process_data(pay_checkstand.get('data')),
            params=self.VR.process_data(pay_checkstand.get('params')),
            files=self.VR.process_data(pay_checkstand.get('files'))
        )
        log.info(f'pay_checkstand 请求结果为：{response}')
        self.session_vars['pay_checkstand'] = response
        db_config = project_config.get('mysql')
        AssertHandler().handle_assertion(
            asserts=self.VR.process_data(pay_checkstand['assert']),
            response=response,
            db_config=db_config
        )

        # Step: trade_underway_preview_V2
        log.info(f'开始执行 step: trade_underway_preview_V2')
        trade_underway_preview_V2 = self.steps_dict.get('trade_underway_preview_V2')
        project_config = self.global_vars.get('user')
        response = RequestHandler.send_request(
            method=trade_underway_preview_V2['method'],
            url=project_config['host'] + self.VR.process_data(trade_underway_preview_V2['path']),
            headers=self.VR.process_data(trade_underway_preview_V2.get('headers')),
            data=self.VR.process_data(trade_underway_preview_V2.get('data')),
            params=self.VR.process_data(trade_underway_preview_V2.get('params')),
            files=self.VR.process_data(trade_underway_preview_V2.get('files'))
        )
        log.info(f'trade_underway_preview_V2 请求结果为：{response}')
        self.session_vars['trade_underway_preview_V2'] = response
        db_config = project_config.get('mysql')
        AssertHandler().handle_assertion(
            asserts=self.VR.process_data(trade_underway_preview_V2['assert']),
            response=response,
            db_config=db_config
        )

        # Step: activity_queryAndExecute_pre_pay
        log.info(f'开始执行 step: activity_queryAndExecute_pre_pay')
        activity_queryAndExecute_pre_pay = self.steps_dict.get('activity_queryAndExecute_pre_pay')
        project_config = self.global_vars.get('user')
        response = RequestHandler.send_request(
            method=activity_queryAndExecute_pre_pay['method'],
            url=project_config['host'] + self.VR.process_data(activity_queryAndExecute_pre_pay['path']),
            headers=self.VR.process_data(activity_queryAndExecute_pre_pay.get('headers')),
            data=self.VR.process_data(activity_queryAndExecute_pre_pay.get('data')),
            params=self.VR.process_data(activity_queryAndExecute_pre_pay.get('params')),
            files=self.VR.process_data(activity_queryAndExecute_pre_pay.get('files'))
        )
        log.info(f'activity_queryAndExecute_pre_pay 请求结果为：{response}')
        self.session_vars['activity_queryAndExecute_pre_pay'] = response
        db_config = project_config.get('mysql')
        AssertHandler().handle_assertion(
            asserts=self.VR.process_data(activity_queryAndExecute_pre_pay['assert']),
            response=response,
            db_config=db_config
        )

        # Step: shopConfig_list
        log.info(f'开始执行 step: shopConfig_list')
        shopConfig_list = self.steps_dict.get('shopConfig_list')
        project_config = self.global_vars.get('user')
        response = RequestHandler.send_request(
            method=shopConfig_list['method'],
            url=project_config['host'] + self.VR.process_data(shopConfig_list['path']),
            headers=self.VR.process_data(shopConfig_list.get('headers')),
            data=self.VR.process_data(shopConfig_list.get('data')),
            params=self.VR.process_data(shopConfig_list.get('params')),
            files=self.VR.process_data(shopConfig_list.get('files'))
        )
        log.info(f'shopConfig_list 请求结果为：{response}')
        self.session_vars['shopConfig_list'] = response
        db_config = project_config.get('mysql')
        AssertHandler().handle_assertion(
            asserts=self.VR.process_data(shopConfig_list['assert']),
            response=response,
            db_config=db_config
        )

        # Step: balance_unWithdraw_info
        log.info(f'开始执行 step: balance_unWithdraw_info')
        balance_unWithdraw_info = self.steps_dict.get('balance_unWithdraw_info')
        project_config = self.global_vars.get('user')
        response = RequestHandler.send_request(
            method=balance_unWithdraw_info['method'],
            url=project_config['host'] + self.VR.process_data(balance_unWithdraw_info['path']),
            headers=self.VR.process_data(balance_unWithdraw_info.get('headers')),
            data=self.VR.process_data(balance_unWithdraw_info.get('data')),
            params=self.VR.process_data(balance_unWithdraw_info.get('params')),
            files=self.VR.process_data(balance_unWithdraw_info.get('files'))
        )
        log.info(f'balance_unWithdraw_info 请求结果为：{response}')
        self.session_vars['balance_unWithdraw_info'] = response
        db_config = project_config.get('mysql')
        AssertHandler().handle_assertion(
            asserts=self.VR.process_data(balance_unWithdraw_info['assert']),
            response=response,
            db_config=db_config
        )

        # Step: goods_verify
        log.info(f'开始执行 step: goods_verify')
        goods_verify = self.steps_dict.get('goods_verify')
        project_config = self.global_vars.get('user')
        response = RequestHandler.send_request(
            method=goods_verify['method'],
            url=project_config['host'] + self.VR.process_data(goods_verify['path']),
            headers=self.VR.process_data(goods_verify.get('headers')),
            data=self.VR.process_data(goods_verify.get('data')),
            params=self.VR.process_data(goods_verify.get('params')),
            files=self.VR.process_data(goods_verify.get('files'))
        )
        log.info(f'goods_verify 请求结果为：{response}')
        self.session_vars['goods_verify'] = response
        db_config = project_config.get('mysql')
        AssertHandler().handle_assertion(
            asserts=self.VR.process_data(goods_verify['assert']),
            response=response,
            db_config=db_config
        )

        # Step: trade_underway_create
        log.info(f'开始执行 step: trade_underway_create')
        trade_underway_create = self.steps_dict.get('trade_underway_create')
        project_config = self.global_vars.get('user')
        response = RequestHandler.send_request(
            method=trade_underway_create['method'],
            url=project_config['host'] + self.VR.process_data(trade_underway_create['path']),
            headers=self.VR.process_data(trade_underway_create.get('headers')),
            data=self.VR.process_data(trade_underway_create.get('data')),
            params=self.VR.process_data(trade_underway_create.get('params')),
            files=self.VR.process_data(trade_underway_create.get('files'))
        )
        log.info(f'trade_underway_create 请求结果为：{response}')
        self.session_vars['trade_underway_create'] = response
        db_config = project_config.get('mysql')
        AssertHandler().handle_assertion(
            asserts=self.VR.process_data(trade_underway_create['assert']),
            response=response,
            db_config=db_config
        )

        # Step: pay_prePay
        log.info(f'开始执行 step: pay_prePay')
        pay_prePay = self.steps_dict.get('pay_prePay')
        project_config = self.global_vars.get('user')
        response = RequestHandler.send_request(
            method=pay_prePay['method'],
            url=project_config['host'] + self.VR.process_data(pay_prePay['path']),
            headers=self.VR.process_data(pay_prePay.get('headers')),
            data=self.VR.process_data(pay_prePay.get('data')),
            params=self.VR.process_data(pay_prePay.get('params')),
            files=self.VR.process_data(pay_prePay.get('files'))
        )
        log.info(f'pay_prePay 请求结果为：{response}')
        self.session_vars['pay_prePay'] = response
        db_config = project_config.get('mysql')
        AssertHandler().handle_assertion(
            asserts=self.VR.process_data(pay_prePay['assert']),
            response=response,
            db_config=db_config
        )

        # Step: pay_pay
        log.info(f'开始执行 step: pay_pay')
        pay_pay = self.steps_dict.get('pay_pay')
        project_config = self.global_vars.get('user')
        response = RequestHandler.send_request(
            method=pay_pay['method'],
            url=project_config['host'] + self.VR.process_data(pay_pay['path']),
            headers=self.VR.process_data(pay_pay.get('headers')),
            data=self.VR.process_data(pay_pay.get('data')),
            params=self.VR.process_data(pay_pay.get('params')),
            files=self.VR.process_data(pay_pay.get('files'))
        )
        log.info(f'pay_pay 请求结果为：{response}')
        self.session_vars['pay_pay'] = response
        db_config = project_config.get('mysql')
        AssertHandler().handle_assertion(
            asserts=self.VR.process_data(pay_pay['assert']),
            response=response,
            db_config=db_config
        )

        # Step: trade_detail_after_pay
        log.info(f'开始执行 step: trade_detail_after_pay')
        trade_detail_after_pay = self.steps_dict.get('trade_detail_after_pay')
        project_config = self.global_vars.get('user')
        response = RequestHandler.send_request(
            method=trade_detail_after_pay['method'],
            url=project_config['host'] + self.VR.process_data(trade_detail_after_pay['path']),
            headers=self.VR.process_data(trade_detail_after_pay.get('headers')),
            data=self.VR.process_data(trade_detail_after_pay.get('data')),
            params=self.VR.process_data(trade_detail_after_pay.get('params')),
            files=self.VR.process_data(trade_detail_after_pay.get('files'))
        )
        log.info(f'trade_detail_after_pay 请求结果为：{response}')
        self.session_vars['trade_detail_after_pay'] = response
        db_config = project_config.get('mysql')
        AssertHandler().handle_assertion(
            asserts=self.VR.process_data(trade_detail_after_pay['assert']),
            response=response,
            db_config=db_config
        )

        # Step: feedback_getFeedbackOrderReplayTotal
        log.info(f'开始执行 step: feedback_getFeedbackOrderReplayTotal')
        feedback_getFeedbackOrderReplayTotal = self.steps_dict.get('feedback_getFeedbackOrderReplayTotal')
        project_config = self.global_vars.get('user')
        response = RequestHandler.send_request(
            method=feedback_getFeedbackOrderReplayTotal['method'],
            url=project_config['host'] + self.VR.process_data(feedback_getFeedbackOrderReplayTotal['path']),
            headers=self.VR.process_data(feedback_getFeedbackOrderReplayTotal.get('headers')),
            data=self.VR.process_data(feedback_getFeedbackOrderReplayTotal.get('data')),
            params=self.VR.process_data(feedback_getFeedbackOrderReplayTotal.get('params')),
            files=self.VR.process_data(feedback_getFeedbackOrderReplayTotal.get('files'))
        )
        log.info(f'feedback_getFeedbackOrderReplayTotal 请求结果为：{response}')
        self.session_vars['feedback_getFeedbackOrderReplayTotal'] = response
        db_config = project_config.get('mysql')
        AssertHandler().handle_assertion(
            asserts=self.VR.process_data(feedback_getFeedbackOrderReplayTotal['assert']),
            response=response,
            db_config=db_config
        )

        # Step: trade_list
        log.info(f'开始执行 step: trade_list')
        trade_list = self.steps_dict.get('trade_list')
        project_config = self.global_vars.get('user')
        response = RequestHandler.send_request(
            method=trade_list['method'],
            url=project_config['host'] + self.VR.process_data(trade_list['path']),
            headers=self.VR.process_data(trade_list.get('headers')),
            data=self.VR.process_data(trade_list.get('data')),
            params=self.VR.process_data(trade_list.get('params')),
            files=self.VR.process_data(trade_list.get('files'))
        )
        log.info(f'trade_list 请求结果为：{response}')
        self.session_vars['trade_list'] = response
        db_config = project_config.get('mysql')
        AssertHandler().handle_assertion(
            asserts=self.VR.process_data(trade_list['assert']),
            response=response,
            db_config=db_config
        )

        # Step: account_getWechatPublicAccountSubscribeFlag
        log.info(f'开始执行 step: account_getWechatPublicAccountSubscribeFlag')
        account_getWechatPublicAccountSubscribeFlag = self.steps_dict.get('account_getWechatPublicAccountSubscribeFlag')
        project_config = self.global_vars.get('user')
        response = RequestHandler.send_request(
            method=account_getWechatPublicAccountSubscribeFlag['method'],
            url=project_config['host'] + self.VR.process_data(account_getWechatPublicAccountSubscribeFlag['path']),
            headers=self.VR.process_data(account_getWechatPublicAccountSubscribeFlag.get('headers')),
            data=self.VR.process_data(account_getWechatPublicAccountSubscribeFlag.get('data')),
            params=self.VR.process_data(account_getWechatPublicAccountSubscribeFlag.get('params')),
            files=self.VR.process_data(account_getWechatPublicAccountSubscribeFlag.get('files'))
        )
        log.info(f'account_getWechatPublicAccountSubscribeFlag 请求结果为：{response}')
        self.session_vars['account_getWechatPublicAccountSubscribeFlag'] = response
        db_config = project_config.get('mysql')
        AssertHandler().handle_assertion(
            asserts=self.VR.process_data(account_getWechatPublicAccountSubscribeFlag['assert']),
            response=response,
            db_config=db_config
        )

        # Step: trade_detail_after_pay_01
        log.info(f'开始执行 step: trade_detail_after_pay_01')
        trade_detail_after_pay_01 = self.steps_dict.get('trade_detail_after_pay_01')
        project_config = self.global_vars.get('user')
        response = RequestHandler.send_request(
            method=trade_detail_after_pay_01['method'],
            url=project_config['host'] + self.VR.process_data(trade_detail_after_pay_01['path']),
            headers=self.VR.process_data(trade_detail_after_pay_01.get('headers')),
            data=self.VR.process_data(trade_detail_after_pay_01.get('data')),
            params=self.VR.process_data(trade_detail_after_pay_01.get('params')),
            files=self.VR.process_data(trade_detail_after_pay_01.get('files'))
        )
        log.info(f'trade_detail_after_pay_01 请求结果为：{response}')
        self.session_vars['trade_detail_after_pay_01'] = response
        db_config = project_config.get('mysql')
        AssertHandler().handle_assertion(
            asserts=self.VR.process_data(trade_detail_after_pay_01['assert']),
            response=response,
            db_config=db_config
        )

        # Step: trade_allowFeedbackCount
        log.info(f'开始执行 step: trade_allowFeedbackCount')
        trade_allowFeedbackCount = self.steps_dict.get('trade_allowFeedbackCount')
        project_config = self.global_vars.get('user')
        response = RequestHandler.send_request(
            method=trade_allowFeedbackCount['method'],
            url=project_config['host'] + self.VR.process_data(trade_allowFeedbackCount['path']),
            headers=self.VR.process_data(trade_allowFeedbackCount.get('headers')),
            data=self.VR.process_data(trade_allowFeedbackCount.get('data')),
            params=self.VR.process_data(trade_allowFeedbackCount.get('params')),
            files=self.VR.process_data(trade_allowFeedbackCount.get('files'))
        )
        log.info(f'trade_allowFeedbackCount 请求结果为：{response}')
        self.session_vars['trade_allowFeedbackCount'] = response
        db_config = project_config.get('mysql')
        AssertHandler().handle_assertion(
            asserts=self.VR.process_data(trade_allowFeedbackCount['assert']),
            response=response,
            db_config=db_config
        )

        # Step: slot_get_after_pay
        log.info(f'开始执行 step: slot_get_after_pay')
        slot_get_after_pay = self.steps_dict.get('slot_get_after_pay')
        project_config = self.global_vars.get('user')
        response = RequestHandler.send_request(
            method=slot_get_after_pay['method'],
            url=project_config['host'] + self.VR.process_data(slot_get_after_pay['path']),
            headers=self.VR.process_data(slot_get_after_pay.get('headers')),
            data=self.VR.process_data(slot_get_after_pay.get('data')),
            params=self.VR.process_data(slot_get_after_pay.get('params')),
            files=self.VR.process_data(slot_get_after_pay.get('files'))
        )
        log.info(f'slot_get_after_pay 请求结果为：{response}')
        self.session_vars['slot_get_after_pay'] = response
        db_config = project_config.get('mysql')
        AssertHandler().handle_assertion(
            asserts=self.VR.process_data(slot_get_after_pay['assert']),
            response=response,
            db_config=db_config
        )

        # Step: activity_queryAndExecute_after_pay
        log.info(f'开始执行 step: activity_queryAndExecute_after_pay')
        activity_queryAndExecute_after_pay = self.steps_dict.get('activity_queryAndExecute_after_pay')
        project_config = self.global_vars.get('user')
        response = RequestHandler.send_request(
            method=activity_queryAndExecute_after_pay['method'],
            url=project_config['host'] + self.VR.process_data(activity_queryAndExecute_after_pay['path']),
            headers=self.VR.process_data(activity_queryAndExecute_after_pay.get('headers')),
            data=self.VR.process_data(activity_queryAndExecute_after_pay.get('data')),
            params=self.VR.process_data(activity_queryAndExecute_after_pay.get('params')),
            files=self.VR.process_data(activity_queryAndExecute_after_pay.get('files'))
        )
        log.info(f'activity_queryAndExecute_after_pay 请求结果为：{response}')
        self.session_vars['activity_queryAndExecute_after_pay'] = response
        db_config = project_config.get('mysql')
        AssertHandler().handle_assertion(
            asserts=self.VR.process_data(activity_queryAndExecute_after_pay['assert']),
            response=response,
            db_config=db_config
        )

    @classmethod
    def teardown_class(cls):
        log.info('Starting teardown for the TestWashingMachineOrdering')
        order_refund = cls.teardowns_dict.get('order_refund')
        project_config = cls.global_vars.get('merchant')
        response = RequestHandler.send_request(
            method=order_refund['method'],
            url=project_config['host'] + cls.VR.process_data(order_refund['path']),
            headers=cls.VR.process_data(order_refund.get('headers')),
            data=cls.VR.process_data(order_refund.get('data')),
            params=cls.VR.process_data(order_refund.get('params')),
            files=cls.VR.process_data(order_refund.get('files'))
        )
        log.info(f'order_refund 请求结果为：{response}')
        cls.session_vars['order_refund'] = response
        db_config = project_config.get('mysql')
        AssertHandler().handle_assertion(
            asserts=cls.VR.process_data(order_refund['assert']),
            response=response,
            db_config=db_config
        )

        trade_finishByOrder = cls.teardowns_dict.get('trade_finishByOrder')
        project_config = cls.global_vars.get('user')
        response = RequestHandler.send_request(
            method=trade_finishByOrder['method'],
            url=project_config['host'] + cls.VR.process_data(trade_finishByOrder['path']),
            headers=cls.VR.process_data(trade_finishByOrder.get('headers')),
            data=cls.VR.process_data(trade_finishByOrder.get('data')),
            params=cls.VR.process_data(trade_finishByOrder.get('params')),
            files=cls.VR.process_data(trade_finishByOrder.get('files'))
        )
        log.info(f'trade_finishByOrder 请求结果为：{response}')
        cls.session_vars['trade_finishByOrder'] = response
        db_config = project_config.get('mysql')
        AssertHandler().handle_assertion(
            asserts=cls.VR.process_data(trade_finishByOrder['assert']),
            response=response,
            db_config=db_config
        )

        log.info('Teardown completed for TestWashingMachineOrdering.')

        log.info(f"Test case test_washing_machine_ordering completed.")
