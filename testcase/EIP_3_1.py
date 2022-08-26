# -*- coding: UTF-8 -*-
from backend.MyClass.task import task, TaskSet
from source.monkey_patch import get_env_from_user, on_start
from source import EIP, ECS, NAT, VPC, ORDER, PRODUCT, func_instanceName, check, check_res_code
from source.EIP_module import check_eip_bind, check_eip_status
from source.NAT_module import check_nat
from jsonpath import jsonpath
from copy import deepcopy
import requests, os, logging
from backend.MyClass.users import User

requests.packages.urllib3.disable_warnings()


class EIP_3_1(EIP, NAT, VPC, ECS, ORDER, PRODUCT, TaskSet):
    """
    使用vpc创建nat，创建eip，将nat和eip绑定，然后删除所有的eip和nat
    """
    vpcs = []
    nats = []
    eips = []
    stream_cfg = None
    user: User

    def __init__(self, user):
        EIP.__init__(self)
        TaskSet.__init__(self, user)
        # 从user中获取环境信息
        get_env_from_user(self)
        # 从environment中获取配置
        self.init_cfg()

    def on_start(self):
        pass

    @task
    def create_nat(self):
        self.logger.info(msg='==>step 1\n使用vpc创建nat并检查状态')

        @check(5, '检查nat状态失败', 5, self)
        def check_nat_(nat, self):
            check_nat(nat, self)

        # 使用vpc创建nat
        for vpc in self.vpcs:
            vpc = self.VPC_describe(vpcId=vpc)['res'][0]
            vpc_name = vpc['instanceName']
            vpc_instance = vpc['instanceId']
            self.logger.info(msg='==>step 1\n使用vpc {}创建nat'.format(vpc_instance))
            res = self.NAT_create(func_instanceName(10), vpc_instance, vpc_name)
            nat = jsonpath(res, '$.res.resources..instanceId')[0]
            order_id = jsonpath(res, '$.res.orderId')[0]
            self.approve_order(order_id)
            # 检查nat状态
            check_nat_(nat, self)
            self.nats.append(nat)

    @task
    def create_eip(self):
        self.logger.info(msg='==>step 2\n创建eip，在第3步同创建的nat绑定')
        # 获取projectid
        res = self.getUserProjectList(productCode='BANDWIDTH_PUBLIC')
        self.resource_project_id = jsonpath(res, '$.res..resource_project_id')[0]
        # 创建nat 数量* 5个eip
        order_ids = []
        eips = []
        for i in range(len(self.nats)):
            res = self.EIP_create('T-nrg-EIP_3_1-' + func_instanceName(5), quantity=5, charge_type='postpaid',
                                  pay_type='DAY_MONTH')
            order_ids.append(jsonpath(res, '$.res.orderId')[0])
            eips.extend(jsonpath(res, '$.res.resources..EIP'))
        for order_id in order_ids:
            self.approve_order(order_id)

        # 检查eip状态
        @check(5, msg='check_eip_status failed', interval=10, self=self)
        def check_eip_status_(eips, self):
            for eip in eips:
                check_eip_status(eip, self)

        check_eip_status_(eips, self)
        self.eips = eips

    @task
    def bind_eip(self):
        self.logger.info(msg='==>step 3\n绑定eip，并检查绑定状态')

        @check(5, '检查eip绑定状态失败', 5, self)
        def check_eip_bind_(self, eip, parent_id):
            check_eip_bind(self, eip, parent_id)

        # 每个nat绑定5个eip，然后检查
        eips = deepcopy(self.eips)
        eip_nat = {}

        for nat in self.nats:
            for i in range(5):
                temp = eips.pop()
                res = self.NAT_bind_eips(nat, [temp])
                assert check_res_code(res), 'eip绑定nat失败'
                eip_nat[temp] = nat

        for eip in self.eips:
            check_eip_bind_(self, eip, eip_nat[eip])

    @task
    def delete_all(self):
        self.logger.info(msg='==>step 4\n删除创建的nat及eip')
        # 删除nat和eip
        for nat in self.nats:
            res = self.NAT_delete(nat)
            assert check_res_code(res), '删除nat {}失败'.format(nat)
        res = self.EIP_release(self.eips)
        assert check_res_code(res), '删除eips失败'
        # 手动初始化配置
        self.nats.clear()
        self.eips.clear()
        # 是否需要单独检查eip？
        # 是否需要检查vpc状态？怎么检查


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, filename='logs\\{}.log'.format(os.path.basename(__file__).split('.py')[0]),
                        filemode='w',
                        format='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s')

    eip_3_1 = EIP_3_1()

    eip_3_1.on_start()
    eip_3_1.create_nat()
    eip_3_1.create_eip()
    eip_3_1.bind_eip()
    eip_3_1.delete_all()
