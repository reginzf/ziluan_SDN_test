# -*- coding: UTF-8 -*-
import ipaddress
import random

from jsonpath import jsonpath

from source.PRODUCT_module import PRODUCT
from source.VPC_module import VPC
from source.locust_methods import timeStap, randomIP, func_instanceName

SCP_NUM = 99
OUT_Type = ['IP_VRF', 'CIDR_VRF']
SRC_Type = ['ALL', 'CIDR', 'IP', 'SUBNET']
PROTOCOL = ['ALL', 'TCP', 'UDP', 'ICMP']
PROTOCOL_TYPE = {'ALL': 'ANY', 'TCP': random.choice(['TCP', 'TCP_ALL']), 'UDP': random.choice(['UDP', 'UDP_ALL']),
                 'ICMP': 'ICMP'}
DEST_Port = {'TCP': random.randint(1, 65535), 'UDP': random.randint(1, 65535)}
CIDR_Type = ['ALL', 'CIDR', 'SUBNET', 'CIDR_VRF']

outsideNetwork = 'outsideNetwork'  # 云外网络ID

VPCS = {}


class BFW(PRODUCT):
    def BFW_CreateBfwRuleSet(self, instanceName, priority, fwType='VPC', srcVpcId='', destVpcId='', srcType='ALL',
                             srcSubnetCidrs=None, srcVmIp=None,
                             destType='ALL', destSubnetCidrs=None, destVmIp=None, protocol='ALL', protocolType='ANY',
                             strategy='ALLOW',
                             destVmPort=None, regionId=None, userId=None, description='', projectId=None, azoneId=None,
                             **kwargs):
        """
        创建新的bfw策略，只传入srcVpcId和destVpcId时将创建all-permit的策略
        :param fwType: ”VPC“
        :param instanceName:
        :param priority: str:1~100
        :param srcVpcId:
        :param destVpcId: outsideNetwork：云外
        :param srcType: 源地址类型 ALL,CIDR，SUBNET,IP，  ALL,CIDR,SUBNET时需要填写srcSubnetCidrs
        :param srcSubnetCidrs: list
        :param srcVmIp:
        :param destType:源地址类型 ALL:所有,IP_VRF：单个地址 CIDR_VRF:网段
        :param destSubnetCidrs:list
        :param destVmIp: str 目的类型为IP_VRF时填写
        :param protocol: 地址类型 ALL：所有 TCP
        :param protocolType: "ANY"，"TCP_ALL","TCP"(需要填写destVmPort参数)
        :param strategy: "ALLOW","DENY"
        :param destVmPort:
        :param regionId: 默认填None，自动从框架中获取
        :param userId: 默认填None，自动从框架中获取
        :param description:
        :param projectId:默认填None，自动从框架中获取
        :param azoneId:默认填None，自动从框架中获取
        :return:{"res":{"bfwId":"bfw-fo4l2k61yis7"},"msg":"创建边界防火墙规则集成功","code":"Network.Success"}
        """
        api = 'api/networks/bfw'
        action = 'CreateBfwRuleSet'
        method = 'post'
        # 处理默认参数
        azoneId = self.azone_id if azoneId == None else azoneId
        regionId = self.region[0] if regionId == None else regionId
        projectId = self.project_id_(productCode='VPC_FW') if projectId == None else projectId
        userId = self.user_id if userId == None else userId
        # 当只传入vpcId时，自己去获取下cidr
        if not (srcSubnetCidrs or srcVmIp or destSubnetCidrs or destVmIp):
            srcSubnetCidrs = []
            destSubnetCidrs = []
            srcSubnetCidrs.append(jsonpath(VPC.VPC_describe(self, srcVpcId), '$.res..cidr')[0])  # 0为总的，之后的为分的
            destSubnetCidrs.append(jsonpath(VPC.VPC_describe(self, destVpcId), '$.res..cidr')[0])
        data = {"azoneId": azoneId, "fwType": fwType, "instanceName": instanceName,
                "description": description, "priority": priority, "srcVpcId": srcVpcId, "srcType": srcType,
                "srcSubnetCidrs": srcSubnetCidrs, "srcVmIp": srcVmIp, "destVpcId": destVpcId, "destType": destType,
                "destSubnetCidrs": destSubnetCidrs, "destVmIp": destVmIp, "protocol": protocol,
                "protocolType": protocolType,
                "strategy": strategy, "destVmPort": destVmPort, "regionId": regionId,
                "userId": userId, "projectId": projectId}
        res = self.send_request(api, method, data, Action=action, t=timeStap(), **kwargs)
        return res

    def BFW_DescribeBfwRuleSet(self, instanceId=None, instanceName=None, srcVpcId=None, destVpcId=None, destVmPort=None,
                               regionId=None,
                               page=1, size=10, **kwargs):
        """
        查询bfw策略
        :param instanceId:
        :param instanceName:
        :param srcVpcId:
        :param destVpcId:
        :param destVmPort:
        :param page: 1
        :param size: 10
        :param kwargs:
        :return:{
                  "res": {
                    "page": 1,
                    "size": 10,
                    "total": 1,
                    "data": [
                      {
                        "instanceId": "bfw-fo4l2k61yvtj",
                        "instanceName": "test",
                        "fwType": "VPC",
                        "description": "",
                        "azoneId": "cd-unicloud-region-az1",
                        "destSubnetCidrs": null,
                        "destVmIp": null,
                        "destVmPort": null,
                        "destType": "ALL",
                        "destVpcId": "vpc-fo4l0l5xwd5r",
                        "priority": 11,
                        "protocol": "ALL",
                        "protocolType": "ANY",
                        "srcSubnetCidrs": null,
                        "srcVmIp": null,
                        "srcVmPort": null,
                        "srcType": "ALL",
                        "srcVpcId": "vpc-fo4l0l5xweac",
                        "strategy": "ALLOW",
                        "userId": "4160c253-1818-4d8a-8763-fce26b08b5ad",
                        "projectId": "1525391227128643584",
                        "regionId": "cd-unicloud-region",
                        "createTime": "2022-06-09T11:31:51.000+08:00"
                      }
                    ]
                  },
                  "msg": "查询边界防火墙规则集成功",
                  "code": "Network.Success"
                }
        """
        api = 'api/networks/bfw'
        action = 'DescribeBfwRuleSet'
        method = 'get'
        regionId = self.region[0] if regionId == None else regionId
        data = {}
        ARGS = ['instanceId', 'instanceName', 'srcVpcId', 'destVpcId', 'destVmPort']
        for a in ARGS:
            temp = locals().get(a, False)
            if temp:
                kwargs[a] = temp
        res = self.send_request(api, method, data, Action=action, page=page, size=size, regionId=regionId, t=timeStap(),
                                **kwargs)
        return res

    def BFW_DeleteBfwRuleSet(self, bfwIds: list, **kwargs):
        """
        删除bfw规则
        :param bfwIds:
        :param kwargs:
        :return:{"res":null,"msg":"删除边界防火墙规则集成功","code":"Network.Success"}
        """
        api = 'api/networks/bfw'
        action = 'DeleteBfwRuleSet'
        method = 'post'
        bfwIds = [bfwIds] if type(bfwIds) != list else bfwIds
        data = bfwIds
        res = self.send_request(api, method, data, Action=action, t=timeStap(), **kwargs)
        return res

    def BFW_ModifyBfwRuleSet(self, instanceId=None, instanceName=None, priority=None, fwType=None, srcVpcId=None,
                             destVpcId=None, srcType=None, srcSubnetCidrs=None, srcVmIp=None,
                             destType=None, destSubnetCidrs=None, destVmIp=None, protocol=None, protocolType=None,
                             strategy=None, destVmPort=None, regionId=None, userId=None, description=None,
                             projectId=None, azoneId=None, data=None, DescribeBfwRuleSet=True, **kwargs):
        """
        编辑bfw 策略，如果传入data，则不检查其他参数.未传入data的，先获取配置，再编辑
        :param DescribeBfwRuleSet:为False时不通过查询bfw 策略补充信息
        :param instanceName: 可修改
        :param priority:可修改
        :param fwType:
        :param srcVpcId:
        :param destVpcId:
        :param srcType:
        :param srcSubnetCidrs:
        :param srcVmIp:
        :param destType:
        :param destSubnetCidrs:
        :param destVmIp:
        :param protocol:可修改
        :param protocolType:可修改
        :param strategy:可修改
        :param destVmPort:
        :param regionId:
        :param userId:
        :param description:
        :param projectId:
        :param azoneId:
        :param data:直接传入data时，传入其他参数无效
        :param kwargs:
        :return:{"res":null,"msg":"修改边界防火墙规则集成功","code":"Network.Success"}
        """

        api = 'api/networks/bfw'
        action = 'ModifyBfwRuleSet'
        method = 'put'
        if data:
            return self.send_request(api, method, data, Action=action, t=timeStap(), **kwargs)
        # 如果没有instanceId弹出异常
        if not instanceId:
            raise ValueError('instanceId 或 data 必须选择一个传入')
        # 查询对应信息：
        data = {}
        if DescribeBfwRuleSet:
            res = self.BFW_DescribeBfwRuleSet(instanceId=instanceId)
            data_ = jsonpath(res, '$.res.data')[0]
            assert data_, '请输入存在的instanceId'
            data = data_[0]
            # 传回来的data中携带了createTime参数，需要去掉
            data.pop('createTime', None)
            # 将传入的有值的给data
            ARGS = ['instanceId', 'instanceName', 'priority', 'fwType', 'srcVpcId', 'destVpcId', 'srcType',
                    'srcSubnetCidrs', 'srcVmIp', 'destType', 'destSubnetCidrs', 'destVmIp',
                    'protocol', 'protocolType', 'strategy', 'destVmPort', 'regionId', 'userId', 'description',
                    'projectId', 'azoneId']
            for ele in ARGS:
                temp = locals().get(ele, False)
                if temp != None:
                    data[ele] = temp
        else:
            data = {"azoneId": azoneId, "fwType": fwType, "instanceName": instanceName,
                    "description": description, "priority": priority, "srcVpcId": srcVpcId, "srcType": srcType,
                    "srcSubnetCidrs": srcSubnetCidrs, "srcVmIp": srcVmIp, "destVpcId": destVpcId, "destType": destType,
                    "destSubnetCidrs": destSubnetCidrs, "destVmIp": destVmIp, "protocol": protocol,
                    "protocolType": protocolType,
                    "strategy": strategy, "destVmPort": destVmPort, "regionId": regionId,
                    "userId": userId, "projectId": projectId}
        data['instanceId'] = instanceId
        res = self.send_request(api, method, data, Action=action, t=timeStap(), **kwargs)
        return res

    def BFW_CreateBfwRuleSet_Random_nrg(self, name_prefix, priority, src_vpc, dst_vpc):
        """
        输入名称前缀，优先级，源目VPC，随机创建BFW策略
        :param name_prefix:
        :param priority:
        :param src_vpc:
        :param dst_vpc:
        :return:
        """
        # 获取vpc地址池信息,这里会一直保存，如果vpc一直变的话会有泄露
        src_vpc_struct = VPCS.get(src_vpc, VPC_struct(self, src_vpc))
        dst_vpc_struct = VPCS.get(dst_vpc, VPC_struct(self, dst_vpc))
        VPCS[src_vpc] = src_vpc_struct
        VPCS[dst_vpc] = dst_vpc_struct
        priority = priority if type(priority) == str else str(priority)

        name = name_prefix + func_instanceName(5)
        # 处理源
        if src_vpc == outsideNetwork:
            srcType = random.choice(OUT_Type)
        else:
            srcType = random.choice(SRC_Type)
        srcSubnetCidrs = None
        srcVmIp = None
        if srcType in CIDR_Type:
            srcSubnetCidrs = [src_vpc_struct.__getattribute__(srcType)]
        else:
            srcVmIp = src_vpc_struct.__getattribute__(srcType)
        # 处理目的
        if dst_vpc == outsideNetwork:
            destType = random.choice(OUT_Type)
        else:
            destType = random.choice(SRC_Type)
        destSubnetCidrs = None
        destVmIp = None
        if destType in CIDR_Type:
            destSubnetCidrs = [dst_vpc_struct.__getattribute__(destType)]
        else:
            destVmIp = dst_vpc_struct.__getattribute__(destType)
        # 处理protocol
        protocol = random.choice(PROTOCOL)
        protocolType = PROTOCOL_TYPE[protocol]

        destVmPort = DEST_Port.get(protocolType, None)
        strategy = random.choice(['ALLOW', 'DENY'])
        res = self.BFW_CreateBfwRuleSet(instanceName=name, priority=priority, srcVpcId=src_vpc,
                                        destVpcId=dst_vpc, srcType=srcType, srcSubnetCidrs=srcSubnetCidrs,
                                        srcVmIp=srcVmIp, destType=destType, destSubnetCidrs=destSubnetCidrs,
                                        destVmIp=destVmIp, protocol=protocol, protocolType=protocolType,
                                        strategy=strategy, destVmPort=destVmPort, description=func_instanceName(20))
        return res


class VPC_struct:
    def __init__(self, struct, vpcId):
        self.struct = struct
        if vpcId == outsideNetwork:
            pass
        else:
            self.vpcId = vpcId
            self.cidrs = jsonpath(VPC.VPC_describe(struct, self.vpcId), '$.res..cidr')
            self.cidr, self.mask = self.cidrs[0].split('/')
            self.subnets = self.cidrs[1:]
            self.mask = int(self.mask)
            self.start = int(ipaddress.IPv4Address(self.cidr))
            self.end = self.start + 2 ** (32 - self.mask)

    @property
    def ALL(self):
        return '{}/{}'.format(self.cidr, self.mask)

    @property
    def SUBNET(self):
        return random.choice(self.subnets)

    @property
    def CIDR(self):
        return str(ipaddress.ip_network(
            '{}/{}'.format(ipaddress.IPv4Address(random.randint(self.start, self.end)), random.randint(self.mask, 31)),
            False))

    @property
    def IP(self):
        return str(ipaddress.IPv4Address(random.randint(self.start, self.end)))

    @property
    def IP_VRF(self):
        return randomIP()

    @property
    def CIDR_VRF(self):
        return '{}/{}'.format(randomIP(), random.randint(16, 31))
