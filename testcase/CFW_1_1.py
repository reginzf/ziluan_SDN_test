# -*- coding: UTF-8 -*-
import logging
import os
import time

import requests
from jsonpath import jsonpath

from source import CFW, func_instanceName, ORDER, check, ECS
from source.monkey_patch import get_env_from_user
from backend.MyClass.task import task, TaskSet
from backend.MyClass.users import User

requests.packages.urllib3.disable_warnings()


class CFW_1_1(CFW, ECS, TaskSet):
    """
    VPCP CFW 流量测试
    用来监控流量，当本用例异常时，请检查CFW应流量
    ecs1<-->ecs2
    ecs1、2之间打流，每隔3min下发一次配置（liubo框架未提供查询接口，只能等流量异常通知
    """
    cfw = 'cfw-fj10y0kpe9tb'
    vpc1 = 'vpc-fj1xd3v0h6wp'  # nrg-CFW_1_1-1  172.16.0.0/24
    ecs1 = 'ecs-fj2ivrwagxmj'  # nrg-CFW_1_1-1  172.25.131.152
    vpc2 = 'vpc-fj1xd3v0h6xa'  # nrg-CFW_1_1-2  172.16.1.0/24
    ecs2 = 'ecs-fj2ivrwagxm8'  # nrg-CFW_1_1-2  172.25.131.33
    user: User

    def __init__(self, user):
        CFW.__init__(self)
        TaskSet.__init__(self, user)
        # 从user中获取环境变量
        get_env_from_user(self)
        # 从environment中获取配置
        self.init_cfg()
        self.user.start_env_stream(self.stream_cfg, self.__class__.__name__)

    @task
    def vpcp_streams(self):
        stream_cfgs = self.ECS_Stream_nrg([self.ecs1, self.ecs2], taskId='CFW_1_1', taskname='CFW_1_1')
        self.stream_cfg = stream_cfgs
        time.sleep(180)

    def on_stop(self):
        try:
            for taskId, cfg in self.stream_cfg.items():
                self.user.stop_stream(taskId, cfg)
        except Exception as e:
            self.logger.error(msg=str(e))
            pass
