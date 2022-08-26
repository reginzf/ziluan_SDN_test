# -*- coding: UTF-8 -*-
from backend.MyClass.task import task, TaskSet
from source.monkey_patch import on_start, get_env_from_user
from source import VPCP, func_instanceName, ORDER, PRODUCT, check, check_res_code
from source.VPCP_module import check_vpcp, timeStap
from random import randint
from jsonpath import jsonpath
import requests

requests.packages.urllib3.disable_warnings()


class VPCP_3_1(VPCP, PRODUCT, ORDER, TaskSet):
    # 需要初始化的资源和配置
    vpcs = ["vpc-fj2iugjjrnj0",
            "vpc-fj2iugjjrnj5",
            "vpc-fj2iugjjrnka",
            "vpc-fj2iugjjrnkf",
            "vpc-fj2iugjjrnkk"]  # 5个vpc

    another_user = 'stableEnv'
    another_user_vpcs = ["vpc-fj10vx2y4b3d",
                         "vpc-fj10vx2y4b3i",
                         "vpc-fj10vx2y4b3n",
                         "vpc-fj10vx2y4b3s",
                         "vpc-fj10vx2y4b3x"]

    def __init__(self, user):
        VPCP.__init__(self)
        TaskSet.__init__(self, user)
        self.init_cfg()
        get_env_from_user(self)
        # 从user中获取环境变量
        self.name = self.__class__.__name__
        self.user.start_env_stream(self.stream_cfg, self.__class__.__name__)

    @task
    def create_vpcp(self):
        """
        每次选2个vpc创建vpcp,包含同账户和异账户
        :return:
        """
        self.cur_token = self.token
        self.cur_user_id = self.user_id
        self.setup(web_user="ad7725978af399afe0", web_password="ab6d2d968af9a9a5a7bfba", sql_host='172.25.50.25',
                   sql_user='moove', sql_password='unic-moove', sql_port='3306', username='stableEnv')
        self.another_token = self.token
        self.another_user_id = self.get_user_id(self.another_user)

        self.token = self.cur_token
        self.user_id = self.cur_user_id
        # 全部跨用户的vpcp
        self.logger.info(msg='==>step 1\n创建5个跨域的vpcp')

        vpcp_names = []
        for vpc1, vpc2 in zip(self.vpcs, self.another_user_vpcs):
            name = 'nrg-VPCP_3_1' + func_instanceName(3)
            res = self.VPCP_CreateVpcpAuth(name, vpc1, vpc2, toUserId=self.another_user_id)
            assert check_res_code(res), '创建vpcp 失败{} {}'.format(vpc1, vpc2)
            vpcp_names.append(name)
            # VPCP_CreateVpcpAuth接口返回没啥用的
            # order = jsonpath(res, '$.res.orderId')[0]
            # orders.append(order)
            # vpcps.append(jsonpath(res, '$.res.resources..instanceId')[0])
            # res = self.approve_order(order)
            # assert check_res_code(res), '提交vpcp订单失败'

        # 去另外账户下查询待授权的，给授权
        self.logger.info(msg='==>step 1\n切换到用户2，进行授权')
        self.token = self.another_token
        res = self.VPCP_DescribeVpcpAuth_wait()
        assert len(res) == len(vpcp_names), '在另一个用户下查询vpcp授权列表信息失败'
        ids = [data['id'] for data in res]
        # 进行授权
        for i in ids:
            res = self.VPCP_AgreeVpcpAuth(i)
            assert check_res_code(res), '授权vpcp失败,id:{}'.format(i)
        # 切换回当前用户
        self.logger.info(msg='==>step 1\n切换回当前用户')
        get_env_from_user(self)
        self.vpcp_names = vpcp_names

    @task
    def vpcp_status(self):
        # 检查vpcp状态，应该均为运行中
        self.logger.info(msg='==>step 2\n检查所有vpcp的运行状态')
        vpcps = []

        @check(5, '检查跨域VPCP运行状态失败', 10, self=self)
        def check_vpcp_status():
            for vpcp in self.vpcp_names:
                res = self.VPCP_DescribeVpcp(instanceName=vpcp)
                assert check_res_code(res), '查询vpcp失败'
                status = jsonpath(res, '$.res.data..status')[0]
                assert status == 'RUNNING', '检查vpcp状态失败'
                vpcps.append(jsonpath(res, '$.res.data..instanceId')[0])

        check_vpcp_status()
        self.vpcps = vpcps

    @task
    def del_vpcp(self):
        # 删除vpcp
        self.logger.info(msg='==>step 3\n删除vpcp')
        for vpcp in self.vpcps:
            res = self.VPCP_DeleteVpcp(vpcp)
            assert check_res_code(res), '删除vpcp {}失败'.format(vpcp)
        # 检查是否删除了
        self.logger.info(msg='==>step 3\n开始检查vpcp是否删除')

        @check(5, '检查vpcp是否删除失败', 5, self)
        def check_vpcp_not_exist(res, vpcp):
            assert int(jsonpath(res, '$.res.total')[0]) == 0, '{} 未删除'.format(vpcp)

        for vpcp in self.vpcps:
            res = self.VPCP_DescribeVpcp(vpcp)
            assert check_res_code(res), '检查{}是否被删除失败'.format(vpcp)
            check_vpcp_not_exist(res, vpcp)


if __name__ == '__main__':
    pass
