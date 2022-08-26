# -*- coding: UTF-8 -*-
import logging
import os
import time

import requests
from jsonpath import jsonpath

from source import EIP, func_instanceName, ORDER, check, ECS
from source.monkey_patch import get_env_from_user
from backend.MyClass.task import task, TaskSet
from backend.MyClass.users import User

requests.packages.urllib3.disable_warnings()


class EIP_2_1(EIP, ORDER, ECS, TaskSet):
    """
    验证绑定解绑eip、升降级对控制面的影响，原有流量应不受影响
    """
    eips = None
    eni = []
    ecs = []
    stream_cfg = {}
    user: User

    def __init__(self, user):
        EIP.__init__(self)
        TaskSet.__init__(self, user)
        # 从user中获取环境变量
        get_env_from_user(self)
        # 从environment中获取配置
        self.init_cfg()
        self.user.start_env_stream(self.stream_cfg, self.__class__.__name__)

    def on_stop(self):
        try:
            for k, v in self.streams.items():
                self.user.stop_stream(k, v)
        except Exception as e:
            self.logger.error(msg=str(e))
            pass

    @task
    def create_eip(self):
        # 开始打流
        self.streams = self.ECS_Stream_nrg(self.ecs, 'EIP_2_1', 'EIP_2_1')

        # 创建多个eip
        order_ids = []
        eips = []
        for i in range(10):
            res = self.EIP_create('eip' + func_instanceName(8), charge_type='postpaid', pay_type='DAY_MONTH')
            order_id = jsonpath(res, '$.res.orderId')[0]
            eip = jsonpath(res, '$.res.resources..EIP')
            order_ids.append(order_id)
            eips.extend(eip)
        for order_id in order_ids:
            self.approve_order(order_id)
        self.eips = eips

        # 检查eip状态
        @check(5, msg='check_eip_status failed', interval=10, self=self)
        def check_eip_status(eips):
            for eip in eips:
                res = self.EIP_describe(instanceId=eip)
                status = jsonpath(res, '$.res.data..status')
                # if status: status = status[0]
                assert status and status[0] == 'RUNNING'

        check_eip_status(self.eips)

    @task
    def bind_eip(self):
        # 绑定eip到eni
        bind = {}
        if self.eips:
            len_eni = len(self.eni)
            for n, eip in enumerate(self.eips):
                if n < len_eni:
                    res = self.EIP_associate(eip, self.eni[n], self.eni[n], 'ENI')
                    code = jsonpath(res, '$.code')
                    if code:
                        assert code[0] == "Network.Success", '绑定eip失败'
                        bind[eip] = self.eni[n]
                else:
                    break

        # 完成之后检查绑定状态,检查5次
        @check(5, msg='check eip binding status failed', self=self)
        def check_eip_status(bind: dict):
            for eip, eni in bind.items():
                res = self.EIP_describe(instanceId=eip)
                status = jsonpath(res, '$.res.data..status')
                if status:
                    assert status[0] == 'RUNNING', 'eip {} 状态为：{}'.format(eip, status[0])
                else:

                    assert status, '查询eip {}绑定状态失败'.format(eip)

        check_eip_status(bind)
        self.bind = bind

    @task
    def upgrade_eip(self):
        bandwidth = 20
        for eip in self.eips:
            res = self.EIP_modify_eip_bandwidth(bandwidth=bandwidth, instance_id=eip)
            order = jsonpath(res, '$.res.orderId')[0]
            # 订单接口返回没啥用
            self.approve_order(order)

        # 检查带宽
        @check(5, msg='eip升级/降级，检查带宽失败', self=self)
        def check_eip_bandwidth(eips, bandwidth, msg):
            for eip in eips:
                res = self.EIP_describe(eip)
                _bandwidth = jsonpath(res, '$.res.data..bandwidth')
                assert _bandwidth and _bandwidth[0] == bandwidth, 'eip {} {} bandwidth检查失败'.format(eip, msg)

        self.check_eip_bandwidth = check_eip_bandwidth
        self.check_eip_bandwidth(self.eips, bandwidth, '升级')
        time.sleep(600)

    @task
    def downgrade_eip(self):
        bandwidth = 1
        for eip in self.eips:
            res = self.EIP_modify_eip_bandwidth(bandwidth=bandwidth, instance_id=eip, order_category='DOWNGRADE')
            order = jsonpath(res, '$.res.orderId')[0]
            # 订单接口返回没啥用
            self.approve_order(order)
        self.check_eip_bandwidth(self.eips, bandwidth, '降级')

    @task
    def unbind(self):
        # 将eip和eni解绑
        for eip, eni in self.bind.items():
            res = self.EIP_unassociate(eip, eni)
            code = jsonpath(res, '$.code')
            if code:
                assert code[0] == "Network.Success", '解绑eip {}，eni {}失败'.format(eip, eni)
            else:
                assert code, '解绑eip {}, eni {}，未获取到code'.format(eip, eni)

        # 检查状态
        @check(5, msg='eip和eni解绑失败', self=self)
        def check_eip_unbind(eips):
            for eip in eips:
                res = self.EIP_describe(instanceId=eip)
                parentType = jsonpath(res, '$.res.data..parentType')
                parentInstanceId = jsonpath(res, '$.res.data..parentInstanceId')
                parentType = parentType[0] if parentType else None
                parentInstanceId = parentInstanceId[0] if parentInstanceId else None
                assert not (parentType or parentInstanceId), '解绑eip {}失败'.format(eip)

        check_eip_unbind(list(self.bind.keys()))

    @task
    def delete_eip(self):
        for eip in self.eips:
            res = self.EIP_release(eip)
            code = jsonpath(res, '$.code')
            assert code and code[0] == "Network.Success"

        # 检查删除状态
        @check(5, msg='删除eip失败', self=self)
        def check_eip_delete(eips):
            for eip in eips:
                res = self.EIP_describe(instanceId=eip)
                data = jsonpath(res, '$.res.data')[0]
                assert not data, 'eip {}未删除'.format(eip)

        check_eip_delete(self.eips)


if __name__ == '__main__':
    eip = EIP_2_1()
    logging.basicConfig(level=logging.DEBUG,
                        filename='logs\\{}.log'.format(os.path.basename(__file__).split('.py')[0]),
                        filemode='w',
                        format='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s')
    while True:
        eip.on_start()
        eip.create_eip()
        eip.bind_eip()
        eip.upgrade_eip()
        eip.downgrade_eip()
        eip.unbind()
        eip.delete_eip()
        eip.on_stop()
