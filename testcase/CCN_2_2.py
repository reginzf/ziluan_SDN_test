# -*- coding: UTF-8 -*-
import copy
import time

import requests
from jsonpath import jsonpath

from source import CCN, check, check_res_code, ECS
from source.monkey_patch import get_env_from_user
from backend.MyClass.task import task, TaskSet
from backend.MyClass.users import User

requests.packages.urllib3.disable_warnings()
STREAM_TEMPLATE = {"serverIp": "",
                   "serverPort": "",
                   "clientIp": "",
                   "streamType": "udp",
                   "speed": "500",
                   "action": "start",
                   "vip": "",
                   "vport": "5001",
                   "taskId": "",
                   "callback": "http://172.25.18.51:10001/stop_taskset/CCN_2_2"}


class CCN_2_2(CCN, ECS, TaskSet):
    """
    当前仅验证同账户
    1、CCN下添加2个VPC
    2、检查2个VPC内ecs流量
    """
    ccn = 'ccn-fo4mc30zk9ea'
    vpcs = ['vpc-fo4mdrpcxyzf', 'vpc-fo4mem9uqofh']
    ecs = ['ecs-fo4mdrpcxyzk', 'ecs-fo4mdrpcxyzo']
    user: User

    def __init__(self, user):
        CCN.__init__(self)
        TaskSet.__init__(self, user)
        # 从user中获取环境变量
        get_env_from_user(self)
        # 从environment中获取配置
        self.init_cfg()
        self.user.start_env_stream(self.stream_cfg, self.__class__.__name__)
        self.streams = {}

    def on_stop(self):
        try:
            for name, cfg in self.streams:
                self.user.stop_stream(name, cfg)
            for name in ('CCN_2_21', 'CCN_2_22'):
                cfg = self.user.environment.streams.get(name, False)
                if cfg:
                    self.user.start_stream(name, cfg)
        except:
            pass

    @task
    def add_vpc_to_ccn(self):
        # 将vpc添加到ccn中，并检查状态
        self.logger.info(msg='==>step 1\n将vpc添加到ccn中，并检查状态')
        for vpc in self.vpcs:
            res = self.CCN_CreateCcnVpc(self.ccn, vpc)
            assert check_res_code(res), self.logger.warning(msg='下发绑定vpc 失败 {} {}'.format(self.ccn, self.vpcs))

        @check(5, '在CCN {}检查{} 运行状态失败', 10, self)
        def check_ccn_vpc_status(ccn, vpcs):
            self.check_ccn_vpc_status(ccn, vpcs)

        check_ccn_vpc_status(self.ccn, self.vpcs)

    @task
    def check_streams(self):
        # 开始打流，并检查流状态
        # 获取ecs私网和公网地址
        self.logger.info(msg='==>step 2\n获取ecs的接口信息，拼接打流配置，然后打流,等5min，没异常的话发送stop流量')
        streams = self.ECS_Stream_nrg(self.ecs, 'CCN_2_2', self.__class__.__name__, sleep_time=120)
        for name, cfg in streams.items():
            self.user.environment.streams[name] = cfg
        self.streams = streams

    def unbind_vpc_to_ccn(self):
        # 将之前的vpc从ccn中删除
        self.logger.info(msg='==>step 3\n将step 1绑定的vpc从ccn中删除')
        for vpc in self.vpcs:
            res = self.CCN_DeleteCcnVpc(self.ccn, vpc)
            assert check_res_code(res), '从ccn {} 中移除 vpc {} 失败'.format(self.ccn, vpc)

        # 检查ccn
        @check(5, '检查ccn vpc状态失败', 10, self)
        def check_vpc_deleted(ccn, vpcs):
            res = self.CCN_DescribeCcn(ccn)
            assert check_res_code(res)
            vpcs_ = jsonpath(res, '$.res.data..VpcId')
            for vpc in vpcs:
                assert vpc not in vpcs_, 'CCN {}下{}未删除'.format(ccn, vpc)

        check_vpc_deleted(self.ccn, self.vpcs)


if __name__ == '__main__':
    ccn_2_2 = CCN_2_2()
    ccn_2_2.on_start()
    ccn_2_2.add_vpc_to_ccn()
    ccn_2_2.check_streams()
    ccn_2_2.unbind_vpc_to_ccn()
