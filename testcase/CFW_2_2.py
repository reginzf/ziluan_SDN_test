# -*- coding: UTF-8 -*-
import random
import time

import requests

from source import CFW, check, check_res_code, func_instanceName
from source.monkey_patch import get_env_from_user

from backend.MyClass.task import task, TaskSet
from backend.MyClass.users import User

requests.packages.urllib3.disable_warnings()
MODIDY_ARGS = ["name", "description", "srcIpAddress", "destIpAddress"]

modify_str = ('name', 'description')
modify_addr = ('srcIpAddress', 'destIpAddress')
SCP_N = 200
sleep_time = 60


class CFW_2_2(CFW, TaskSet):
    """
    验证基于ccn的cfw编辑scp的稳定性
    """
    cfw = 'cfw-fo4lwf7lcixm'

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
    def modify_scp(self):
        # 编辑原有的scp，改变优先级，mask等，等待60s，流量应不中断
        self.logger.info(msg='==>step 1\n获取原scp，保存,然后编辑')
        self.scps = self.CFW_CfwScpList_all(self.cfw)
        # 随机选一个参数去编辑
        ip_o = lambda x: '{}/{}'.format(x[0], int(x[1]) + 1)
        for scp in self.scps:
            # 如果为关闭状态则跳过
            if scp['status'] == 2:
                continue
            scp_id = scp['instanceId']
            to_modify = random.choice(MODIDY_ARGS)
            value = ''
            if to_modify in modify_str:
                value = func_instanceName(15)
            elif to_modify in modify_addr:
                value = ip_o(scp[to_modify].split('/'))
            temp = {to_modify: value}
            res = self.CFW_ModifyCfwScp(self.cfw, scp_id, **temp)
            assert check_res_code(res), '编辑{} {}属性失败'.format(scp_id, to_modify)
        time.sleep(sleep_time)  # 等60s，看有没有流量停止信息过来
        self.logger.info(msg='==>step 1\n将scp改回去')
        for scp in self.scps:
            if scp['status'] == 2:
                continue
            res = self.CFW_ModifyCfwScp(**scp)
            assert check_res_code(res), '修改{}'.format(self.cfw)

    @task
    def add_delete_scp(self):
        # 增加200条随机策略：
        self.logger.info(msg=f'==>step 2\n增加{SCP_N}调策略，应不影响流量')
        name_prefix = 'CFW_2_2'
        for i in range(SCP_N):
            res = self.CFW_genRandomScp(self.cfw, '{}-{}'.format(name_prefix, i))
            assert check_res_code(res), '在{} 下创建scp失败'.format(self.cfw)
        time.sleep(sleep_time)
        # 查名字匹配到的策略，并删除
        scps = self.CFW_CfwScpList_all(self.cfw, name=name_prefix)
        scp_ids = [scp['instanceId'] for scp in scps]
        self.CFW_DeleteCfwScp(self.cfw, scp_ids)
        time.sleep(sleep_time)
