# -*- coding: UTF-8 -*-
import logging
import os
import time

import requests
from jsonpath import jsonpath

from source import CCN, check, check_res_code, ORDER
from source.monkey_patch import get_env_from_user
from backend.MyClass.task import task, TaskSet
from backend.MyClass.users import User
from collections import defaultdict

requests.packages.urllib3.disable_warnings()


class CCN_3_1(CCN, ORDER, TaskSet):
    # 背景资源配置
    vpcs = []  # 需要15个
    N = 3  # ccn数量
    user: User

    def __init__(self, user):
        CCN.__init__(self)
        TaskSet.__init__(self, user)
        # 从user中获取环境变量
        get_env_from_user(self)
        # 从environment中获取配置
        self.init_cfg()
        self.user.start_env_stream(self.stream_cfg, self.__class__.__name__)

    @task
    def create_ccn(self):
        # 创建3个ccn并检查状态
        self.logger.info(msg='==>step 1\n创建3个ccn')

        order_ids = []
        ccns = []
        for i in range(self.N):
            res = self.CCN_Create('CCN_3_1-{}'.format(i))
            assert check_res_code(res), self.logger.error(msg='创建ccn订单失败！')
            order_ids.append(jsonpath(res, '$.res.orderId')[0])
            ccns.append(jsonpath(res, '$.res.resources..instanceId')[0])
        for order in order_ids:
            res = self.approve_order(order)
            assert check_res_code(res), self.logger.error(msg='提交ccn订单{}失败'.format(order))

        # 检查3个ccn的状态
        self.logger.info(msg='==>step 1\n检查ccn状态')

        @check(5, msg='检查CCN状态失败', interval=15, self=self)
        def check_ccn_status_(ccn):
            self.check_ccn_status(ccn)

        for ccn in ccns:
            check_ccn_status_(ccn)
        self.ccns = ccns

    @task
    def add_vpcs2ccn(self):
        # 将vpc添加到ccn中
        self.logger.info(msg='==>step 2\n将vpc添加到ccn中')
        ccn_vpc = defaultdict(lambda: [])
        for i, ccn in enumerate(self.ccns):
            for j in range(5):
                n = i * 5 + j
                res = self.CCN_CreateCcnVpc(ccn, self.vpcs[n])
                assert check_res_code(res), '{} 绑定 {} 失败'.format(self.vpcs[n], ccn)
                ccn_vpc[ccn].append(self.vpcs[n])
        self.logger.info(msg='==>step 2\n检查添加到ccn中vpc状态')
        for ccn in self.ccns:
            res = self.CCN_DescribeCcnVpc(ccn)
            status = set(jsonpath(res, '$.res.data..vpcStatus'))
            assert len(status) == 1 and status.pop() == 'RUNNING', self.logger.error(msg='检查{}下vpc状态失败'.format(ccn))
        self.ccn_vpc = ccn_vpc

    @task
    def conflict_vpc(self):
        # 测试添加已被使用的vpc，应返回失败
        self.logger.info(msg='==>step 3\n再次将vpc添加到ccn中，由于冲突，应返回失败')
        for vpc in self.vpcs:
            try:
                self.CCN_CreateCcnVpc(self.ccns[0], vpc)
            except Exception as e:
                if '请求失败' in str(e):
                    pass
                else:
                    self.logger.error(msg='添加已被使用的{},返回成功'.format(vpc))
                    raise e

    @task
    def del_vpc2ccn(self):
        @check(5, '检查ccn 下ecs 是否删除失败', 10, self=self)
        def check_sql_ecs_stat(ccn, self):
            sql_conn_uni_network_basic = self.c_sql.connect_db('uni_network_basic').cursor()
            sql_conn_uni_compute = self.c_sql.connect_db('uni_network_basic').cursor()
            sql_conn_uni_network_basic.execute(
                '''SELECT ecs_id FROM tbl_base_ecs_resource a WHERE instance_id='{}';'''.format(ccn))
            ecs = [ele['ecs_id'] for ele in sql_conn_uni_network_basic.fetchall()]
            assert len(ecs) == 2, '查询{}下ecs失败'.format(ccn)
            for e in ecs:
                sql_conn_uni_compute.execute(
                    '''SELECT is_deleted FROM uni_compute.tbl_domain WHERE domain_uuid='{}' '''.format(e))
                res = sql_conn_uni_compute.fetchall()
                assert res and res[0]['is_deleted'] == '1', '检查{}是否删除失败'.format(e)

        # 解绑vpc,并删除ccn
        self.logger.info(msg='==>step 4\n解绑vpc')
        for ccn, vpcs in self.ccn_vpc.items():
            for vpc in vpcs:
                res = self.CCN_DeleteCcnVpc(ccn, vpc)
                assert check_res_code(res), '从{}中删除{}失败'.format(ccn, vpc)
            res = self.CCN_DeleteCcn(ccn)
            assert check_res_code(res), '删除{}失败'.format(ccn)
            # 查询数据库，对应实例应该是stop状态
            check_sql_ecs_stat(ccn, self)
