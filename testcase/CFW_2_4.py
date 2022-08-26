# -*- coding: UTF-8 -*-
import time
from source import CFW, check, check_res_code, ECS, CCN
from source.monkey_patch import get_env_from_user

from backend.MyClass.task import task, TaskSet
from backend.MyClass.users import User

sleep_time = 120
# 由于打流矿建问题，流量代码已注释

class CFW_2_4(CFW, ECS, CCN, TaskSet):
    """
    验证编辑CCN成员vpc，应不影响cfw原有功能
    """
    cfw = 'cfw-fo4lwf7lcixm'
    ccn = 'ccn-fo4lvcqy3den'
    ecs1 = 'ecs-fj1w8mkw8mry'  # ecs1---ecs2   ecs1--ecs3
    ecs2 = 'ecs-fj2ird1tglgm'
    ecs3 = 'ecs-fo4lwn3psobp'  # 172.25.136.119
    vpcs = ['vpc-fo4lwn3psst1', 'vpc-fo4lwn3psocw', 'vpc-fo4lwn3psod7']
    user: User

    def __init__(self, user):
        CFW.__init__(self)
        TaskSet.__init__(self, user)
        # 从user中获取环境变量
        get_env_from_user(self)
        # 从environment中获取配置
        self.init_cfg()
        # self.user.start_env_stream(self.stream_cfg, self.__class__.__name__)

    def on_stop(self):
        try:
            for k, v in self.streams.items():
                self.user.stop_stream(k, v)
        except Exception as e:
            self.logger.info(msg=str(e))
            pass

    @task
    def ccn_stream_old(self):
        # 先打原有流量，等30s，流量应存在
        self.logger.info(msg='==>step 1\n将ccn中原有ecs的流量打起来')
        # streams = self.ECS_Stream_nrg([self.ecs1, self.ecs2], 'CFW_2_4_1', 'CFW_2_4', serverPort="5010", vport="5010")
        time.sleep(sleep_time)
        # self.streams = streams

    @task
    def add_vpc(self):
        self.logger.info(msg='==>step 2\n将vpc加入ccn中，ccn对应cfw功能应不受影响')
        for vpc in self.vpcs:
            res = self.CCN_CreateCcnVpc(self.ccn, vpc)
            assert check_res_code(res), '绑定{} 到{} 失败'.format(vpc, self.ccn)
        # 检查vpc状态
        self.logger.info(msg='==>step 2\n检查ccn中vpc状态')

        @check(5, '检查ccn下vpc状态失败', 10, self)
        def check_ccn_vpc_status_(ccn, vpcs):
            self.check_ccn_vpc_status(ccn, vpcs)

        check_ccn_vpc_status_(self.ccn, self.vpcs)
        # 开始打流，等待一段时间，流量无异常
        # streams = self.ECS_Stream_nrg([self.ecs1, self.ecs3], taskId='CFW_2_4_2', taskname='CFW_2_4', serverPort='5002',
        #                               vport='5002', sleep_time=sleep_time)

    @task
    def del_vpc(self):
        self.logger.info(msg='==>step 3\n删除ccn下添加的vpc')
        # 将vpc从ccn下删除
        for vpc in self.vpcs:
            res = self.CCN_DeleteCcnVpc(self.ccn, vpc)
            assert check_res_code(res), '从{}中删除{}失败'.format(self.ccn, vpc)
        # 等待一段时间，没问题的话停止流量
        time.sleep(sleep_time)
        # for k, v in self.streams:
        #     res = self.user.stop_stream(k, v)
        #     self.logger.info(msg=res)
