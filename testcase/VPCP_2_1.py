# -*- coding: UTF-8 -*-
from backend.MyClass.task import task, TaskSet
from backend.MyClass.users import User
from source.monkey_patch import on_start, get_env_from_user
from source import VPCP, func_instanceName, ORDER, PRODUCT, check, check_res_code, ECS
from source.VPCP_module import check_vpcp
from jsonpath import jsonpath
import requests, copy, time

requests.packages.urllib3.disable_warnings()


class VPCP_2_1(VPCP, PRODUCT, ORDER, ECS, TaskSet):
    # 需要初始化的资源和配置
    vpc1 = 'vpc-fj1xbwyrzwq1'
    vpc2 = 'vpc-fj2it8nfbin5'

    ecs = ['ecs-fj1xbwyrzwq9', 'ecs-fj1xbwyrzwrf']
    stream_cfg = {}

    user: User

    def __init__(self, user):
        VPCP.__init__(self)
        TaskSet.__init__(self, user)

        # 从user中获取环境变量
        self.name = self.__class__.__name__
        get_env_from_user(self)
        # 从environment中获取配置
        self.init_cfg()
        # self.user.start_env_stream(self.stream_cfg, self.__class__.__name__)

    @task
    def create_vpcp(self):
        # 创建vpcp实例，并检查状态
        self.logger.info(msg='==>step 1\n创建vpcp')
        res = self.VPCP_CreateVpcp(instanceName='nrg-VPCP_2_1-' + func_instanceName(5), vpcId=self.vpc1,
                                   toVpcId=self.vpc2)
        assert check_res_code(res), 'VPCP 下单失败 {} {}'.format(self.vpc1, self.vpc2)
        order = jsonpath(res, '$.res.orderId')[0]
        instanceId = jsonpath(res, '$.res.resources..instanceId')[0]
        res = self.approve_order(order)

        assert check_res_code(res), '提交vpcp订单失败'

        # 检查vpcp状态
        @check(5, '检查vpcp状态失败'.format(instanceId), 10, self)
        def check_vpcp(instanceId):
            res = self.VPCP_DescribeVpcp(instanceId)
            assert check_res_code(res), '检查vpcp {} 失败'.format(instanceId)
            status = jsonpath(res, '$.res.data..status')
            assert status and status[0] == "RUNNING", '检查vpcp {}状态失败，当前为{}'.format(instanceId, status)

        check_vpcp(instanceId)
        self.vpcp = instanceId

    @task
    def check_vpcp_stream(self):
        # 开始打流
        self.logger.info(msg='==>step 2\n使用ecs接口信息构造流量配置,打流1min后停止并删除')
        # self.ECS_Stream_nrg(self.ecs, self.__class__.__name__, self.__class__.__name__, sleep_time=120)
        time.sleep(10)

    @task
    def delete_vpcp(self):
        res = self.VPCP_DeleteVpcp(self.vpcp)
        assert check_res_code(res), '下发删除vpcp失败'

        # 检查vpcp删除没有
        @check(5, '删除vpcp {}失败'.format(self.vpcp), 10, self)
        def _check_vpcp(self, instanceId):
            try:
                check_vpcp(self, instanceId)
            except AssertionError as e:
                if '失败' not in str(e):
                    raise e


if __name__ == '__main__':
    vpcp = VPCP_2_1()
    vpcp.on_start()
    vpcp.create_vpcp()
    vpcp.check_vpcp_stream()
    vpcp.delete_vpcp()
