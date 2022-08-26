# -*- coding: UTF-8 -*-
from jsonpath import jsonpath
from source import CFW, check, check_res_code, func_instanceName, ECS, CCN, VPCP, ORDER
from source.monkey_patch import get_env_from_user

from backend.MyClass.task import task, TaskSet
from backend.MyClass.users import User

RANDOM_SCP_NUM = 200  # 随机生成的scp的数量
STREAM_SLEEP = 30


class CFW_3_2(CFW, CCN, VPCP, ORDER, ECS, TaskSet):
    """
    创建各类型的cfw，在cfw下随机创建scp，然后删除
    """
    vpcp_vpcs = ['vpc-fo4l0d9tgcjy', 'vpc-fo4l15es19ss']
    ccn_vpc_1 = ['vpc-fo4l0l5xwd5e', 'vpc-fo4l15es19tx']  # 创建cfw之前就加入ccn中
    ccn_vpc_2 = ['vpc-fo4l0l5xwd5r']  # 创建cfw后加入ccn中
    ecs_vpcp = []
    ecs_ccn = []
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
    def create_vpcp_ccn(self):
        # 使用vpc创建vpcp和ccn
        self.logger.info(msg='==>step 1\n使用vpc创建vpcp和ccn')
        # 创建vpcp
        res = self.VPCP_CreateVpcp('nrg_CFW_3_2_VPCP', self.vpcp_vpcs[0], self.vpcp_vpcs[1])
        assert check_res_code(res), f'创建vpcp订单失败 {self.vpcp_vpcs[0]} {self.vpcp_vpcs[1]}'
        vpcp_id = jsonpath(res, '$.res.resources..instanceId')[0]
        order_id = jsonpath(res, '$.res.orderId')[0]
        res = self.approve_order(order_id)
        assert check_res_code(res), f'支付创建vpcp {vpcp_id}订单失败'
        self.vpcp_id = vpcp_id

        # 创建ccn
        res = self.CCN_Create('nrg_CFW_3_2_CCN')
        assert check_res_code(res), '创建ccn订单失败'
        ccn_id = jsonpath(res, '$.res.resources..instanceId')[0]
        order_id = jsonpath(res, '$.res.orderId')[0]
        res = self.approve_order(order_id)
        assert check_res_code(res), f'支付创建ccn {ccn_id}订单失败'

        # 检查ccn状态为running

        @check(10, '检查{}状态失败', 30, self)
        def check_ccn_status_(ccn_id):
            self.check_ccn_status(ccn_id)

        check_ccn_status_(ccn_id)
        self.ccn_id = ccn_id

        self.logger.info(msg='==>step 1\n将vpc加入到ccn中')
        for vpc in self.ccn_vpc_1:
            res = self.CCN_CreateCcnVpc(self.ccn_id, vpc)
            assert check_res_code(res), f'{vpc} 加入 {self.ccn_id}失败'
        self.logger.info(msg=f'==>step 1\n检查{self.ccn_id}下vpc状态')
        self.check_ccn_vpc_status(self.ccn_id, self.ccn_vpc_1)

    @task
    def create_cfw(self):
        # 使用step 1的ccn，vpcp创建cfw
        self.logger.info(msg='==>step 2\n使用step 1 的vpcp、ccn创建cfw')
        # 创建基于vpcp的cfw
        self.logger.info(msg=f'创建基于{self.vpcp_id} 的cfw')
        res = self.CFW_createCfwOrder('nrg_CFW_3_2_VPCP', self.vpcp_id, srcVpcId=self.vpcp_vpcs[0],
                                      destVpcId=self.vpcp_vpcs[1])
        assert check_res_code(res), f'使用{self.vpcp_id} 创建cfw失败'
        cfw_vpcp_id = jsonpath(res, '$.res.resources..instanceId')[0]
        order_id = jsonpath(res, '$.res.orderId')[0]
        res = self.approve_order(order_id)
        assert check_res_code(res), f'支付创建{cfw_vpcp_id}失败'
        self.cfw_vpcp_id = cfw_vpcp_id

        # 创建基于ccn的cfw
        self.logger.info(msg=f'==>step 2\n创建基于{self.ccn_id} 的cfw')
        res = self.CFW_createCfwOrder('nrg_CFW_3_2_CCN', cloudConnectNetworkId=self.ccn_id)
        assert check_res_code(res), f'使用{self.ccn_id} 创建cfw失败'
        cfw_ccn_id = jsonpath(res, '$.res.resources..instanceId')[0]
        order_id = jsonpath(res, '$.res.orderId')[0]
        res = self.approve_order(order_id)
        assert check_res_code(res), f'支付创建{cfw_vpcp_id}失败'
        self.cfw_ccn_id = cfw_ccn_id

        # 检查这两个cfw均处于运行中，再开始下一步
        @check(10, msg='检查ccn状态失败', interval=30, self=self)
        def check_cfw_status_(cfws):
            for cfw in cfws:
                self.check_cfw_status(cfw)

        check_cfw_status_([{self.cfw_ccn_id: 'CCN'}, {self.cfw_vpcp_id: 'VPCP'}])

    @task
    def create_scp(self):
        # 在cfw下随机创建RANDOM_SCP_NUM条scp
        self.logger.info(msg='==>step 3\n先创建允许流量通过的策略，然后在cfw下创建900条scp')
        # 允许通过的策略
        for cfw in [self.cfw_ccn_id, self.cfw_vpcp_id]:
            res = self.CFW_CreateCfwScp(cfw, func_instanceName(10), srcIpAddress='0.0.0.0/0', destIpAddress='0.0.0.0/0',
                                        protocol=4)
            assert check_res_code(res), '创建策略失败'
            for i in range(RANDOM_SCP_NUM):
                res = self.CFW_genRandomScp(cfw, 'nrg_3_2-')
                assert check_res_code(res), '创建策略失败'
        # 此时流量应该是通的,STREAM_SLEEP时间内流量不应异常
        # stream_1 = self.ECS_Stream_nrg(self.ecs_ccn, taskId='CFW_3_2_CCN', taskname=self.__class__.__name__)
        # stream_2 = self.ECS_Stream_nrg(self.ecs_vpcp, taskId='CFW_3_2_VPCP', taskname=self.__class__.__class__)
        # time.sleep(STREAM_SLEEP)
        # for k, v in stream_1.items():
        #     self.user.stop_stream(k, v)
        # for k, v in stream_2.items():
        #     self.user.stop_stream(k, v)

    @task
    def delete_cfw(self):
        # 直接删除所有的cfw，vpcp对应的虚拟机应该被删除，ccn的被保留
        self.logger.info(msg='==step 4\n删除所有cfw，并检查虚拟机是否正常删除')
        res = self.CFW_DeleteCfw([self.cfw_vpcp_id], type='VPCP')
        assert check_res_code(res), '删除cfw {} {}失败'.format(self.cfw_vpcp_id, self.cfw_ccn_id)
        res = self.CFW_DeleteCfw([self.cfw_ccn_id], type='CCN')
        assert check_res_code(res), '删除cfw {} {}失败'.format(self.cfw_vpcp_id, self.cfw_ccn_id)

        # 检查VPCP CFW虚拟机应该被删除
        @check(10, '检查cfw\ccn的虚拟机是否被删除失败', 20, self)
        def check_ecs_is_deleted_(cfw_id):
            self.check_ecs_is_deleted(cfw_id)

        check_ecs_is_deleted_(self.cfw_vpcp_id)
        # 删除CCN和VPCP
        self.logger.info(msg='==>step 4\n删除{}和{}'.format(self.ccn_id, self.vpcp_id))
        res = self.CCN_DeleteCcn(self.ccn_id)
        assert check_res_code(res), '删除{}失败'.format(self.ccn_id)
        res = self.VPCP_DeleteVpcp(self.vpcp_id)
        assert check_res_code(res), '删除{}失败'.format(self.vpcp_id)
        check_ecs_is_deleted_(self.ccn_id)
