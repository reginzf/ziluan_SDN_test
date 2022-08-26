# -*- coding: UTF-8 -*-
from backend.MyClass.task import task, TaskSet
from backend.MyClass.users import User
from source.monkey_patch import get_env_from_user
from source import EIP, ECS, NAT, VPC, ORDER, func_instanceName, check, check_res_code
from jsonpath import jsonpath
from ipaddress import IPv4Address

from source.EIP_module import check_eip_bind, check_eip_unbind
import requests, os, logging

requests.packages.urllib3.disable_warnings()


class EIP_2_4(EIP, NAT, VPC, ECS, ORDER, TaskSet):
    """
    创建ecs、eni、bws、nat、slb、hvip等可以绑定eip的资源和一个固定eip作为背景资源
    使用固定eip绑定解绑资源，无异常
    创建eip2绑定解绑资源，无异常
    删除eip2，无异常
    """
    eip = ''  # 固定eip
    ecs = ''
    eni = ''
    nat = ''  # EIP_2_3使用的nat
    hvip = ''  # 新增hvip，已绑定实例
    stream_cfg = None
    user: User

    def __init__(self, user):
        EIP.__init__(self)
        TaskSet.__init__(self, user)
        # 从user中获取环境信息
        get_env_from_user(self)
        # 从environment中获取配置
        self.init_cfg()
        self.user.start_env_stream(self.stream_cfg, self.__class__.__name__)

    def on_start(self):
        self.ecs_eni = None
        pass

    def on_stop(self):
        pass

    def bind_eip(self, eip):
        self.logger.info(msg='step 1\n1、查询self.ecs的eni')
        res = self.ECS_avb_for_eip()
        ids = jsonpath(res, '$.res')[0]
        if ids:
            self.ecs_eni = [ele['id'] for ele in ids if ele['id'] == self.ecs][0]
        assert self.ecs_eni, '获取{}的eni 失败'.format(self.ecs)
        self.logger.info(msg='step 1\n2、ecs绑定eip')
        res = self.EIP_associate(eip, self.ecs, self.ecs_eni)
        assert check_res_code(res), self.logger.info('绑定eip 失败{} {}'.format(self.ecs, eip))
        self.logger.info(msg='step 1\n3、检查eip和ecs状态')

        # 检查eip和ecs状态
        self.logger.info(msg='step 2\n1、检查eip和ecs状态')

        @check(5, '检查eip {} ecs {}绑定状态失败'.format(eip, self.ecs), interval=10, self=self)
        def check_eip_bind_ecs(eip, parent_id):
            check_eip_bind(self, eip, parent_id)

        check_eip_bind_ecs(eip, self.ecs)
        self.check_eip_bind_ecs = check_eip_bind_ecs
        self.logger.info(msg='step 1\necs解绑eip')
        # ecs解绑eip：
        res = self.EIP_unassociate(eip, self.ecs)
        assert check_res_code(res), self.logger.info('解绑eip 失败 {} {}'.format(self.ecs, eip))

        @check(5, '检查eip {} ecs {}解绑失败'.format(eip, self.ecs), interval=10, self=self)
        def check_eip_unbind_(eip):
            check_eip_unbind(self, eip)

        check_eip_unbind_(eip)
        self.check_eip_unbind = check_eip_unbind_
        self.logger.info(msg='step 2\neni的绑定、编辑、解绑')

        # eni的绑定、编辑、解绑
        res = self.EIP_associate(eip, self.eni, self.eni, 'ENI')
        assert check_res_code(res), self.logger.info('绑定eip 失败 {} {}'.format(self.eni, eip))
        self.logger.info(msg='step 2\n检查eip状态')

        # 检查eip状态
        @check(5, '检查eip状态失败{} {}'.format(eip, self.eni), 10, self)
        def check_eip_bind_eni(eip, parent_id):
            check_eip_bind(self, eip, parent_id)

        check_eip_bind_eni(eip, self.eni)
        self.logger.info(msg='step 2\n编辑eni地址')
        # 编辑eni地址
        res = self.ECS_networkInterfaces(instanceId=self.eni)
        assert jsonpath(res, '$.code')[0] == '0' and jsonpath(res, '$.res.list')[0], self.logger.info(
            '查询eni {}信息失败'.format(self.eni))
        # 获取ipv4地址
        ipadd = jsonpath(res, '$..ipv4Addr')[0]
        # 修改地址
        res = self.ECS_ipAddress(self.eni, str(IPv4Address(ipadd) + 1))
        assert jsonpath(res, '$.code')[0] == '0', self.logger.info('修改eni {}地址失败'.format(self.eni))

        # 检查eni状态
        @check(200, '检查eni {}状态失败', interval=30, self=self)
        def check_eni_status(eni):
            res = self.ECS_networkInterfaces(eni)
            assert jsonpath(res, '$.code')[0] == '0' and jsonpath(res, '$.res.list')[0], self.logger.info(
                '查询eni {}信息失败'.format(self.eni))
            assert jsonpath(res, '$.res..status')[0] == 'RUNNING' and jsonpath(res, '$.res..ipv4Addr')[0] == str(
                IPv4Address(ipadd) + 1), self.logger.info('检查eni {}状态失败'.format(eni))

        check_eni_status(self.eni)

        # 修改回去
        res = self.ECS_ipAddress(self.eni, str(IPv4Address(ipadd)))
        assert jsonpath(res, '$.code')[0] == '0', self.logger.info('修改eni {}地址失败'.format(self.eni))

        # 检查eni状态
        @check(5, '检查eni {}状态失败', interval=10, self=self)
        def check_eni_status_(eni):
            res = self.ECS_networkInterfaces(eni)
            assert jsonpath(res, '$.code')[0] == '0' and jsonpath(res, '$.res.list')[0], self.logger.info(
                '查询eni {}信息失败'.format(self.eni))
            assert jsonpath(res, '$.res..status')[0] == 'RUNNING' and jsonpath(res, '$.res..ipv4Addr')[0] == str(
                IPv4Address(ipadd)), self.logger.info('检查eni {}状态失败'.format(eni))

        check_eni_status_(self.eni)
        # eip解绑eni
        res = self.EIP_unassociate(eip, self.eni)
        assert check_res_code(res), '解绑eip 失败{} {}'.format(eip, self.eni)

        # 检查eip状态
        check_eip_unbind_(eip)

        # eip绑定、解绑nat
        res = self.NAT_bind_eips(self.nat, [eip])
        assert check_res_code(res), 'nat 绑定eip失败'

        # 检查eip状态
        @check(5, '检查eip绑定nat 失败{}'.format(eip), interval=5, self=self)
        def check_eip_nat(eip, nat):
            check_eip_bind(self, eip, nat)

        check_eip_nat(eip, self.nat)
        # 解绑eip
        res = self.NAT_unbind_eips(self.nat, [eip])
        assert check_res_code(res), '解绑eip失败'
        # 检查eip状态
        check_eip_unbind_(eip)

        # eip绑定解绑hvip
        res = self.EIP_associate(eip, self.hvip, self.hvip, 'VIP')
        assert check_res_code(res), 'hvip {}绑定eip失败'.format(self.hvip)

        @check(5, '检查hvip绑定eip失败', 5, self)
        def check_eip_hvip(eip, hvip):
            check_eip_bind(self, eip, hvip)

        check_eip_hvip(eip, self.hvip)
        # eip解绑hvip
        res = self.EIP_unassociate(eip, self.hvip)
        assert check_res_code(res), 'hvip解绑eip失败'
        check_eip_unbind_(eip)

    @task
    def eip_bind(self):
        # eip绑定、解绑ecs
        # 查ecs的eni
        self.bind_eip(self.eip)

    @task
    def new_eip_bind(self):
        # 申请一个新的eip再来一次
        res = self.EIP_create('EIP_2_4-' + func_instanceName(5), quantity=1, charge_type='postpaid',
                              pay_type='DAY_MONTH')
        order_id = jsonpath(res, '$.res.orderId')[0]
        eip = jsonpath(res, '$.res.resources..EIP')[0]
        self.approve_order(order_id)
        self.check_eip_unbind(eip)
        self.bind_eip(eip)
        # 删除eip
        res = self.EIP_release(eip)
        assert check_res_code(res), '删除eip {}失败'.format(eip)

        @check(5, msg='删除eip失败', self=self)
        def check_eip_delete(eip):
            res = self.EIP_describe(instanceId=eip)
            data = jsonpath(res, '$.res.data')[0]
            assert not data, 'eip {}未删除'.format(eip)

        check_eip_delete(eip)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, filename='logs\\{}.log'.format(os.path.basename(__file__).split('.py')[0]),
                        filemode='w',
                        format='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s')

    eip_2_4 = EIP_2_4()
    eip_2_4.on_start()
    eip_2_4.eip_bind()
    eip_2_4.new_eip_bind()
    eip_2_4.on_stop()
