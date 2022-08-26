# -*- coding: UTF-8 -*-
import requests
from jsonpath import jsonpath

from source import CFW, check, check_res_code
from source.monkey_patch import get_env_from_user

from backend.MyClass.task import task, TaskSet
from backend.MyClass.users import User

requests.packages.urllib3.disable_warnings()

SCP_N = 200


class CFW_2_1(CFW, TaskSet):
    """
    验证编辑基于VPCP的CFW的SCP 控制面的稳定性
    """
    cfw = 'cfw-fj10y0kpe9tb'
    user: User

    def __init__(self, user):
        CFW.__init__(self)
        TaskSet.__init__(self, user)
        # 从user中获取环境变量
        get_env_from_user(self)
        # 从environment中获取配置
        self.init_cfg()
        self.user.start_env_stream(self.stream_cfg, self.__class__.__name__)

    def on_start(self):
        pass

    def on_stop(self):
        pass

    @task
    def create_scp(self):
        self.logger.info(msg=f'==>step 1\n在cfw下新建{SCP_N}条scp，并检查数量')
        # 先确认当前cfw下有多少条
        res = self.CFW_CfwScpList(self.cfw)
        assert check_res_code(res), '查询{} 下scp失败'.format(self.cfw)
        scp_num = int(jsonpath(res, '$,res.total')[0])

        # 在cfw下创建SCP_N条scp
        for i in range(SCP_N):
            res = self.CFW_genRandomScp(self.cfw, 'CFW_2_1-{}-'.format(i))
            assert check_res_code(res), '在{} 下创建scp失败'.format(self.cfw)
        res = self.CFW_CfwScpList(self.cfw)
        assert check_res_code(res), '查询{} 下scp失败'.format(self.cfw)
        scp_num_new = int(jsonpath(res, '$,res.total')[0])
        assert scp_num_new - scp_num == SCP_N, '检查{}下scp数量失败当前：{}，期望{}'.format(self.cfw, scp_num_new, scp_num + SCP_N)
        # 数量对了就获取所有scp详细信息
        all_scps = self.CFW_CfwScpList_all(self.cfw)
        self.scps = all_scps[-SCP_N:]  # 是否要切片？切后SCP_N条
        self.scp_num = scp_num
        # self.scp_num = 5

    @task
    def modify_scp(self):
        self.logger.info(msg='==>step 2\n将所有scp的mask+1')
        ip_o = lambda x: '{}/{}'.format(x[0], int(x[1]) + 1)
        for scp in self.scps:
            # 当策略为关闭状态时不能编辑
            if scp['status'] == 2:
                continue
            scp_id = scp['instanceId']
            n_src = ip_o(scp['srcIpAddress'].split('/'))
            n_dst = ip_o(scp['destIpAddress'].split('/'))
            res = self.CFW_ModifyCfwScp(self.cfw, scp_id, srcIpAddress=n_src, destIpAddress=n_dst)
            assert check_res_code(res), '修改{} 中的{} 失败'.format(self.cfw, scp_id)
        # 改回来
        self.logger.info(msg='==>step 2\n将所有scp的mask改回来')
        ip_o = lambda x: '{}/{}'.format(x[0], int(x[1]))
        for scp in self.scps:
            if scp['status'] == 2:
                continue
            scp_id = scp['instanceId']
            n_src = ip_o(scp['srcIpAddress'].split('/'))
            n_dst = ip_o(scp['destIpAddress'].split('/'))
            res = self.CFW_ModifyCfwScp(self.cfw, scp_id, srcIpAddress=n_src, destIpAddress=n_dst)
            assert check_res_code(res), '修改{} 中的{} 失败'.format(self.cfw, scp_id)

    @task
    def del_scp(self):
        self.logger.info(msg='==>step3\n删除之前创建的scp,检查scp数量')
        scp_instances = [scp['instanceId'] for scp in self.scps]
        res = self.CFW_DeleteCfwScp(self.cfw, scp_instances)
        assert check_res_code(res), '在{}下批量删除scp失败'.format(self.cfw)

        @check(5, '检查cfw下scp数量', 5, self)
        def check_cfw_scp_num(cfw, target_num: int):
            res = self.CFW_CfwScpList(cfw)
            assert check_res_code(res), '查询{} scp信息失败'.format(cfw)
            total = int(jsonpath(res, '$.res.total')[0])
            assert total == target_num, 'total:{} target_num:{}'.format(total, target_num)

        check_cfw_scp_num(self.cfw, self.scp_num)
