# -*- coding: UTF-8 -*-
from backend.MyClass.task import task, TaskSet
from source.monkey_patch import get_env_from_user
from source import EIP, ORDER, PRODUCT, check, NAT, ECS
from jsonpath import jsonpath
import requests, logging, os
from backend.MyClass.users import User

requests.packages.urllib3.disable_warnings()


class EIP_2_2(NAT, EIP, PRODUCT, ORDER, ECS, TaskSet):
    """
    反复创建dnat，修改dnat接口，删除dnat，应该不影响其他流量
    """
    vpc = ''
    nat = ' '
    ecs = ''
    port_pub = ''
    port_private = ''
    eip = ''
    stream_cfg = False

    user: User

    def __init__(self, user):
        EIP.__init__(self)
        TaskSet.__init__(self, user)
        # 从user中获取环境信息
        get_env_from_user(self)
        # 从environment中获取配置
        self.init_cfg()
        # self.user.start_env_stream(self.stream_cfg, self.__class__.__name__)

    def on_start(self):
        pass

    def on_stop(self):
        pass

    @task
    def add_dnat(self):
        self.logger.info(msg='step 1 创建dnat\n查询vpc下对应ecs的eni信息')
        eni = []
        for ele in self.ECS_AvbByVpcAndSubnetIds(self.vpc):
            if ele[0] == self.ecs:
                eni = ele[2]
                break
        self.logger.info(msg='使用eni创建dnat')
        if eni:
            res = self.DNAT_create(self.nat, self.eip, self.port_pub, eni, self.port_private, protpcal='tcp', )
            code = jsonpath(res, '$.code')
            print(code)
            assert code and code[0] == "Network.Success", '创建DNAT 接口未返回code {} {} {},{} {},{}'.format(self.nat,
                                                                                                      self.eip,
                                                                                                      self.port_pub,
                                                                                                      self.ecs,
                                                                                                      self.port_private,
                                                                                                      'tcp')
            dnatId = jsonpath(res, '$.res.dnatId')[0]
        else:
            self.logger.info(msg='未查询到ecs{}的网卡id '.format(self.ecs))
            raise Exception('未查询到ecs{}的网卡id '.format(self.ecs))

        self.logger.info(msg='检查dnat状态')
        msg = '创建dnat：检查nat {} dnat {} 状态失败'.format(self.nat, dnatId)

        @check(5, msg=msg, interval=5)
        def check_dnat(nat, dnatId):
            res = self.DNAT_describe(nat)
            dnat = jsonpath(res, '$.res.data..dnatId')
            assert dnat and dnatId in dnat, '未创建nat {} dnat {}'.format(nat, dnatId)
            status = jsonpath(res, '$.res.data..status')
            flag = True

            for _dnat, _status in zip(dnat, status):
                if _dnat == dnatId:
                    flag = False
                    assert _status == 'RUNNING', "dnat {} 状态为 {}".format(_dnat, _status)
                    break
            if flag:
                raise KeyError('未在nat {} 找到 dnat {}'.format(nat, dnatId))

        check_dnat(self.nat, dnatId)
        self.dnatId = dnatId
        self.check_dnat = check_dnat

    @task
    def modify_dnat(self):
        # 编辑dnat
        res = self.DNAT_update(self.dnatId, self.port_pub, self.port_private)
        code = jsonpath(res, '$.code')
        assert code and code[0] == "Network.Success", "编辑dnat {}失败,msg: {}".format(self.dnatId,
                                                                                   jsonpath(res, '$.msg')[0])
        # 检查dnat状态
        msg = '编辑dnat：检查nat {} dnat {} 状态失败'
        self.check_dnat(self.nat, self.dnatId)
        del msg

    @task
    def delete_dnat(self):
        res = self.DNAT_delete(self.dnatId)
        code = jsonpath(res, '$.code')
        assert code and code[0] == "Network.Success", '删除dnat {}失败msg： {}'.format(self.dnatId,
                                                                                  jsonpath(res, '$.msg')[0])

        flag = True
        msg = '删除dnat：检查nat {} dnat {} 状态失败'
        try:
            self.check_dnat(self.nat, self.dnatId)
        except AssertionError as e:
            flag = '失败' in str(e)
        assert flag, '删除dnat，dnat {} 依然存在, nat {}'.format(self.dnatId, self.nat)


# EIP_2_2.on_start = on_start
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, filename='logs\\{}.log'.format(os.path.basename(__file__).split('.')[0]),
                        filemode='w',
                        format='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s')
    eip = EIP_2_2(None)

    eip.on_start()
    eip.add_dnat()
    eip.modify_dnat()
    eip.delete_dnat()
    eip.on_stop()
