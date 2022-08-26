# -*- coding: UTF-8 -*-
import random
import time

from backend.MyClass.task import task, TaskSet
from backend.MyClass.users import User
from source import BFW, VPC, ECS, check_res_code

from source.monkey_patch import get_env_from_user
import requests
from jsonpath import jsonpath

requests.packages.urllib3.disable_warnings()
SCP_NUM = 99  # 要创建的scp数量
SLEEP_TIME = 2  # sleep的时间

outsideNetwork = 'outsideNetwork'
STRATEGY = {'ALLOW': 'DENY', 'DENY': 'ALLOW'}


class BFW_2_1(BFW, VPC, ECS, TaskSet):
    """
    1、验证：存在多条src dst vpc相同的策略时，编辑一条，防火墙上会删除所有，再重新创建，有没有可能某一时间permit不生效？
    2、多次修改控制面、管理面的稳定性
    3、接口测试？
    """
    src_vpc = 'vpc-e9ocyarmlknp'
    dst_vpc = 'outsideNetwork'
    scp_id = ''  # vpc到云下允许的策略，优先级设置为1，不修改
    # ecs = ['ecs-fo4lwn3psobp', 'ecs-fj1xall1anml']  # 云上和云下打流
    user: User

    def __init__(self, user):
        BFW.__init__(self)
        TaskSet.__init__(self, user)
        self.init_cfg()
        get_env_from_user(self)
        self.user.start_env_stream(self.stream_cfg, self.__class__.__name__)

    # def on_start(self):
    #     # 开始的时候先尝试把流打起来，手动打也行？
    #     try:
    #         self.streams = self.ECS_Stream_nrg(self.ecs, 'BFW_2_1', 'BFW_2_1')
    #     except Exception:
    #         pass

    @task
    def create_scp(self):
        # 1、创建src 和dst相同的策略 SCP_NUM 条，编辑其中一条，流量应该不会中断
        self.logger.info(msg='==>step 1\n打流，然后创建99条随机策略，打流不应中断')
        scps = []
        for i in range(SCP_NUM):
            res = self.BFW_CreateBfwRuleSet_Random_nrg(f'nrg-BFW_2_1-{i + 100 - SCP_NUM}-', str(i + 100 - SCP_NUM),
                                                       self.src_vpc,
                                                       self.dst_vpc)
            assert check_res_code(res), '创建scp失败'
            scp_id = jsonpath(res, '$.res.bfwId')
            assert scp_id, '获取scp id失败'
            scps.append(scp_id[0])
        time.sleep(SLEEP_TIME)
        self.scps = scps

    @task
    def modify_scp(self):
        # 先查一次，目的带端口的改端口，不带的改策略,不应断流
        self.logger.info(msg='==>step 2\n将step 1创建的策略都编辑一次，不应断流')
        for scp in self.scps:
            scp_ = self.BFW_DescribeBfwRuleSet(scp)
            assert check_res_code(scp_), '查询{} 失败'.format(scp)
            scp_ = jsonpath(scp_, '$.res.data')[0][0]
            if scp_['destVmPort']:
                scp_['destVmPort'] = str(int(scp_['destVmPort']) + 1)
            else:
                scp_['strategy'] = STRATEGY[scp_['strategy']]
            scp_['instanceId'] = scp
            self.BFW_ModifyBfwRuleSet(data=scp_)
        time.sleep(SLEEP_TIME)

    @task
    def delete_scp(self):
        # 删除创建的策略，不应断流,这里一条一条的删
        self.logger.info(msg='==>step 3\n一条一条的删除策略')
        for scp in self.scps:
            res = self.BFW_DeleteBfwRuleSet([scp])
            assert check_res_code(res), '删除{}失败'

    @task
    def create_delete_scp(self):
        # 创建 SCP_NUM 条，然后一次性删除
        self.logger.info(msg='==>step 4\n创建 {} 条策略，然后一次性删除'.format(SCP_NUM))
        scps = []
        for i in range(SCP_NUM):
            res = self.BFW_CreateBfwRuleSet_Random_nrg(f'nrg-BFW_2_1-{i + 100 - SCP_NUM}-', str(i + 100 - SCP_NUM),
                                                       self.src_vpc,
                                                       self.dst_vpc)
            assert check_res_code(res), '创建scp失败'
            scp_id = jsonpath(res, '$.res.bfwId')
            assert scp_id, '获取scp id失败'
            scps.append(scp_id[0])
        res = self.BFW_DeleteBfwRuleSet(scps)
        assert check_res_code(res), '批量删除scp失败'
        time.sleep(1)

    # def on_stop(self):
    #     # 强制停止流量
    #     try:
    #         for k, v in self.streams.items():
    #             self.user.stop_stream(k, v)
    #     except Exception:
    #         pass
