# -*- coding: UTF-8 -*-
from backend.MyClass.task import task, TaskSet
from backend.MyClass.users import User
from source.monkey_patch import get_env_from_user
from source import EIP, check, NAT, VPC, func_instanceName
from jsonpath import jsonpath
from ipaddress import IPv4Address
from functools import reduce
import requests

requests.packages.urllib3.disable_warnings()


class EIP_2_3(EIP, NAT, VPC, TaskSet):
    """
    create_snat:创建snat，无异常
    modify_snat:编辑create_snat创建的snat，无异常
    delete_snat:删除创建的所有资源，无异常
    下发返回后等待0.2s
    """
    vpc = ''
    nat = ''
    snat = ''
    used_eip = ''  # snat使用的eip
    unused_eip = ''  # 172.25.129.49
    stream_cfg = None

    user: User

    def __init__(self, user):
        EIP.__init__(self)
        TaskSet.__init__(self, user)
        get_env_from_user(self)
        self.init_cfg()
        # self.user.start_env_stream(self.stream_cfg, self.__class__.__name__)

    def on_start(self):
        pass

    def on_stop(self):
        pass

    @task
    def create_snat(self):
        # 查询vpc的cidr和subnet，创建新subnet,mask默认为24
        res = self.VPC_describe(vpcId=self.vpc)
        data = jsonpath(res, '$.res')[0][0]
        used_subnet = reduce(lambda a, b: [str(max(IPv4Address(a[0]), IPv4Address(b[0]))), '24'],
                             [subnet['cidr'].split('/') for subnet in data['subnets']])
        # 创建一个新的subnet
        new_subnet_cidr = str(IPv4Address(used_subnet[0]) + 256) + '/' + used_subnet[1]
        res = self.VPC_create_subnet(self.vpc, func_instanceName(10), cidr=new_subnet_cidr)
        code = jsonpath(res, '$.code')
        assert code and code[0] == "Network.Success", '创建subnet失败'
        subnet_id = jsonpath(res, '$.res.Id')[0]
        self.new_subnet_cidr = new_subnet_cidr
        # 创建snat
        res = self.SNAT_create(self.nat, [subnet_id], self.unused_eip, self.vpc)
        code = jsonpath(res, '$.code')

        assert code and code[0] == "Network.Success", '创建snat失败'
        snat = jsonpath(res, '$.res.snatId')[0]

        self.snat_2 = snat

        # 检查snat状态
        def check_snat(nat, snat):
            res = self.SNAT_describe(nat)
            code = jsonpath(res, '$.code')
            assert code and code[0] == "Network.Success", '查询snat失败'
            data = jsonpath(res, '$.res.data')[0]
            for ele in data:
                if ele['snatId'] == snat:
                    assert ele['status'] == 'RUNNING', '检查snat {} 状态失败'.format(snat)
                    return
            assert False, 'nat {} 下不存在snat {}'.format(nat, snat)

        @check(5, 'snat {} 状态不为RUNNING'.format(snat), interval=5)
        def _check_snat(nat, snat):
            check_snat(nat, snat)

        _check_snat(self.nat, snat)
        self.check_snat = check_snat
        self.subnet = subnet_id

    @task
    def modify_snat(self):
        # 再创建一个subnet
        address, mask = self.new_subnet_cidr.split('/')
        self.new_subnet_cidr = str(IPv4Address(address) + 256) + '/' + mask
        res = self.VPC_create_subnet(self.vpc, func_instanceName(10), cidr=self.new_subnet_cidr)
        code = jsonpath(res, '$.code')
        assert code and code[0] == "Network.Success", '创建subnet失败'
        subnet_id_1 = jsonpath(res, '$.res.Id')[0]
        # 创建第二个subnet
        address, mask = self.new_subnet_cidr.split('/')
        self.new_subnet_cidr = str(IPv4Address(address) + 256) + '/' + mask
        res = self.VPC_create_subnet(self.vpc, func_instanceName(10), cidr=self.new_subnet_cidr)
        code = jsonpath(res, '$.code')
        assert code and code[0] == "Network.Success", '创建subnet失败'
        subnet_id_2 = jsonpath(res, '$.res.Id')[0]
        # 将第一个subnet加入环境中已有的snat中
        res1 = self.SNAT_update(self.snat, self.vpc, [subnet_id_1])
        res2 = self.SNAT_update(self.snat_2, self.vpc, [subnet_id_2])
        code = jsonpath(res1, '$.code')
        assert code and code[0] == "Network.Success", '编辑snat {}失败'.format(self.snat)
        code = jsonpath(res2, '$.code')
        assert code and code[0] == "Network.Success", '编辑snat {}失败'.format(self.snat_2)

        # 检查snat状态
        @check(n=5, msg='检查snat {} 状态失败'.format(self.snat))
        def _check_snat_1(nat, snat):
            self.check_snat(nat, snat)

        _check_snat_1(self.nat, self.snat)

        @check(n=5, msg='检查snat {} 状态失败'.format(self.snat_2))
        def _check_snat_2(nat, snat):
            self.check_snat(nat, snat)

        _check_snat_2(self.nat, self.snat_2)
        # 移除snat
        res1 = self.SNAT_update(self.snat, self.vpc, remove_subnet_ids=[subnet_id_1])
        res2 = self.SNAT_update(self.snat_2, self.vpc, remove_subnet_ids=[subnet_id_2])
        code = jsonpath(res1, '$.code')
        assert code and code[0] == "Network.Success", '编辑snat {}失败'.format(self.snat)
        code = jsonpath(res2, '$.code')
        assert code and code[0] == "Network.Success", '编辑snat {}失败'.format(self.snat_2)
        # 检查snat状态
        _check_snat_1(self.nat, self.snat)
        _check_snat_2(self.nat, self.snat_2)

        self.subnet_1 = subnet_id_1
        self.subnet_2 = subnet_id_2

    @task
    def delete_snat(self):
        # 先删除snat，再删除subnet,删除接口直接返回成功，不用再检查
        res = self.SNAT_delete(self.snat_2)
        code = jsonpath(res, '$.code')
        assert code and code[0] == "Network.Success", '删除snat {}失败'.format(self.snat_2)
        # 删除subnet
        res1 = self.VPC_delete_subnet(self.vpc, self.subnet_1)
        res2 = self.VPC_delete_subnet(self.vpc, self.subnet_2)
        res = self.VPC_delete_subnet(self.vpc, self.subnet)

        code = jsonpath(res1, '$.code')
        assert code and code[0] == "Network.Success", '删除subnet {}失败'.format(self.subnet_1)
        code = jsonpath(res2, '$.code')
        assert code and code[0] == "Network.Success", '删除subnet {}失败'.format(self.subnet_2)
        code = jsonpath(res, '$.code')
        assert code and code[0] == "Network.Success", '删除subnet {}失败'.format(self.subnet)


if __name__ == '__main__':
    # logging.basicConfig(level=logging.DEBUG, filename='logs\\{}.log'.format(os.path.basename(__file__).split('.')[0]),
    #                     filemode='w',
    #                     format='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s')
    user = User(None)
    eip = EIP_2_3(user)

    eip.on_start()
    eip.create_snat()
    eip.modify_snat()
    eip.delete_snat()
    eip.on_stop()
