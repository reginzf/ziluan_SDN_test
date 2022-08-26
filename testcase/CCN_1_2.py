# -*- coding: UTF-8 -*-
import time
from backend.MyClass.task import task, TaskSet
from source import CCN, ECS
import requests
from backend.MyClass.users import User

requests.packages.urllib3.disable_warnings()


class CCN_1_2(CCN, ECS, TaskSet):
    """
    仅用来打流
    """
    ccn = 'ccn-fj2ird1tgkfx'
    vpcp = ''
    ecs = ['ecs-fj2ird1tglgm', 'ecs-fj1w8mkw8mry', 'ecs-e9ocyinq1gzl']
    user: User

    def __init__(self, user):
        CCN.__init__(self)
        TaskSet.__init__(self, user)
        self.init_cfg()
        self.user.start_env_stream(self.stream_cfg, self.__class__.__name__)

    def on_stop(self):
        try:
            for stream in self.streams:
                for name, cfg in stream.items():
                    self.user.stop_stream(name, cfg)
        except:
            pass

    @task
    def test_stream(self):
        """
        查询流状态=>如果流不存在则创建流，如果存在则 sleep=>如果流异常则停止脚本
        :return:
        """
        stream1 = self.ECS_Stream_nrg([self.ecs[0], self.ecs[1]], taskId='CCN_1_2-1', taskname=self.__class__.__name__,
                                      serverPort='6001', vport='6001')
        stream2 = self.ECS_Stream_nrg([self.ecs[1], self.ecs[2]], taskId='CCN_1_2-2', taskname=self.__class__.__name__,
                                      serverPort='6002', vport='6002')
        stream3 = self.ECS_Stream_nrg([self.ecs[2], self.ecs[0]], taskId='CCN_1_2-3', taskname=self.__class__.__name__,
                                      serverPort='6003', vport='6003')
        self.streams = [stream1, stream2, stream3]
        time.sleep(90)
