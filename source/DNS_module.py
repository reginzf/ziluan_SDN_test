# -*- coding: UTF-8 -*-
import ipaddress
import random
from typing import List

from jsonpath import jsonpath

from source.PRODUCT_module import PRODUCT
from source.locust_methods import timeStap, func_instanceName, check_res_code

LDNS = {}
projectIds = {}


class DNS(PRODUCT):
    def DNS_CreateLDns(self, instanceName: str, description='', azoneId=None, regionId=None, projectId=None, **kwargs):
        """
        创建内网云解析
        :param instanceName:
        :param description:
        :param azoneId:
        :param regionId:
        :param projectId:
        :param kwargs:
        :return:
        {
  "res": {
    "instanceId": "dns-fpmhed21id40",
    "instanceName": "1.2.3.com.",
    "userId": "6757cd7f-ccd1-4b79-a9ff-c2d4634bb6fa",
    "projectId": "1515973385144762368",
    "regionId": "hz-base-region",
    "vpcId": "",
    "ttl": 300,
    "desc": "",
    "status": "RUNNING",
    "createTime": null,
    "updateTime": null,
    "isDeleted": 0,
    "ldnsRsvCount": null
  },
  "msg": "创建内网DNS成功",
  "code": "Network.Success"
}
        """
        api = 'api/networks/dns'
        action = 'CreateLDns'
        method = 'post'

        azoneId = self.azone_id if azoneId == None else azoneId
        regionId = self.region[0] if regionId == None else regionId
        projectId = self.project_id_(productCode='DNS') if projectId == None else projectId

        data = {"projectId": projectId, "instanceName": instanceName, "description": description}
        res = self.send_request(api, method, data, Action=action, regionId=regionId, azoneId=azoneId,
                                t=timeStap(), **kwargs)
        return res

    def DNS_ModifyLDns(self, instanceId, desc='', regionId=None, **kwargs):
        """
        编辑内网云解析，只能修改描述信息
        :param instanceId:
        :param desc:
        :param regionId:
        :param kwargs:
        :return:{"res":null,"msg":"修改内网DNS成功","code":"Network.Success"}
        """
        api = 'api/networks/dns'
        action = 'ModifyLDns'
        method = 'put'
        regionId = self.region[0] if regionId is None else regionId
        data = {"instanceId": instanceId, "desc": desc}
        res = self.send_request(api, method, data, Action=action, regionId=regionId, **kwargs)
        return res

    def DNS_DeleteLDns(self, instanceIds: List, regionId=None, **kwargs):
        """
        删除内网云解析
        :param instanceIds: List
        :param regionId:
        :param kwargs:
        :return:{"res":null,"msg":"删除内网DNS成功","code":"Network.Success"}
        """
        api = 'api/networks/dns'
        action = 'DeleteLDns'
        method = 'delete'
        instanceIds = [instanceIds] if type(instanceIds) != list else instanceIds
        regionId = self.region[0] if regionId is None else regionId
        data = {"instanceIds": instanceIds}
        res = self.send_request(api, method, data, Action=action, regionId=regionId, t=timeStap(), **kwargs)
        return res

    def DNS_GetLDnsPage(self, instanceId='', instanceName='', page=1, size=10, regionId=None, **kwargs):
        """
        查询内网云解析
        :param instanceId:
        :param instanceName:
        :param page:1
        :param size:10
        :param regionId:
        :param kwargs:
        :return:
{
  "res": {
    "page": 1,
    "size": 10,
    "total": 1,
    "data": [
      {
        "instanceId": "dns-faha8dil12u7",
        "instanceName": "bb.com.",
        "userId": "6757cd7f-ccd1-4b79-a9ff-c2d4634bb6fa",
        "projectId": "1515973385144762368",
        "regionId": "hz-base-region",
        "vpcId": "",
        "ttl": 300,
        "desc": "",
        "status": "RUNNING",
        "createTime": "2022-07-09T10:57:14.000+08:00",
        "updateTime": "2022-07-09T10:57:14.000+08:00",
        "isDeleted": 0,
        "ldnsRsvCount": 0
      }
    ]
  },
  "msg": "获取内网DNS成功",
  "code": "Network.Success"
}        """
        ARGS = ['page', 'size', 'instanceId', 'instanceName']
        for arg in ARGS:
            temp = locals().get(arg, None)
            if temp:
                kwargs[arg] = temp
        api = 'api/networks/dns'
        action = 'GetLDnsPage'
        method = 'get'
        regionId = self.region[0] if regionId is None else regionId
        data = {}
        res = self.send_request(api, method, data, Action=action, regionId=regionId, t=timeStap(), **kwargs)
        return res

    def DNS_CreateLDnsResolve(self, ldnsId, instanceName, target: List, type_c, ttl='300', description='',
                              regionId=None,
                              **kwargs):
        """
        创建内网云解析记录
        :param ldnsId:
        :param instanceName:
        :param target: list
        :param type: A,AAAA,CNAME
        :param ttl:
        :param description:
        :param regionId:
        :param kwargs:
        :return:
        """
        api = 'api/networks/dns'
        action = 'CreateLDnsResolve'
        method = 'post'
        if type(target) != list:
            target = [target]
        regionId = self.region[0] if regionId == None else regionId
        data = {"ldnsId": ldnsId, "instanceName": instanceName, "target": target, "type": type_c, "ttl": ttl,
                "description": description}
        res = self.send_request(api, method, data, Action=action, regionId=regionId, t=timeStap(), **kwargs)
        return res

    def DNS_CreateLDnsResolve_nrg(self, ldnsId, instanceName=None, **kwargs):
        """随机生成解析记录"""

        # 如果未传入name则为随机值

        if instanceName is None:
            instanceName = func_instanceName(random.randint(1, 63))
        ttl = str(random.randint(300, 2147483647))
        type_c = random.choice(list(dns_types.keys())) if not kwargs.get('type_c', None) else kwargs['type_c']
        target = dns_types[type_c]()
        description = func_instanceName(random.randint(0, 64))

        res = self.DNS_CreateLDnsResolve(ldnsId=ldnsId, instanceName=instanceName, target=target, type_c=type_c,
                                         ttl=ttl,
                                         description=description, **kwargs)
        return res

    def DNS_ModifyLDnsResolve(self, instanceId, ldnsId, instanceName='', type='', addValues=None, rmvValues=None,
                              ttl='300', desc='',
                              regionId=None, data=None, **kwargs):
        """
        编辑内网云解析记录
        :param instanceId:解析记录id
        :param ldnsId:云解析实例id
        :param instanceName:
        :param type: A,AAAA,CNAME  当type和当前不一样的时候，rmvValues=[]
        :param addValues:
        :param rmvValues:
        :param ttl: str
        :param desc: description
        :param regionId:
        :param kwargs:
        :return:{"res":null,"msg":"修改内网DNS解析记录成功","code":"Network.Success"}
        """
        api = 'api/networks/dns'
        action = 'ModifyLDnsResolve'
        method = 'put'
        regionId = self.region[0] if regionId == None else regionId
        if not data:
            addValues = [addValues] if type(addValues) != list else addValues
            rmvValues = [rmvValues] if type(rmvValues) != list else rmvValues
            data = {"instanceId": instanceId, "ldnsId": ldnsId, "instanceName": instanceName, "type": type,
                    "ttl": ttl, "desc": desc, "addValues": addValues, "rmvValues": rmvValues}
        res = self.send_request(api, method, data, Action=action, regionId=regionId, t=timeStap(), **kwargs)
        return res

    def DNS_ModifyLDnsResolve_nrg(self, instanceId, ldnsId, instanceName=None, type_c=None, target=None,
                                  ttl=None, desc=None, regionId=None, ldns_renew=False, **kwargs):
        """
        修改云解析记录
        1、先获取域名，如果本地没保存则从接口获取，并更新获取updateTime
        :param instanceId: 解析记录实例ID
        :param ldnsId: 云解析实例ID
        :param instanceName:
        :param type: A，AAAA，CNAME
        :param target: 值，list
        :param ttl:
        :param desc:描述
        :param regionId:
        :param ldns_renew:为True时，从接口刷新instanceName
        :param kwargs:
        :return:
        """
        # 先获取云解析的域名
        dns_instanceName = None
        if not instanceName or ldns_renew:  # 当本地未存储，且未指定instanceName，需要更新本地
            if LDNS.get(ldnsId, None):
                dns_instanceName = LDNS.get(ldnsId, None)
            else:
                res = self.DNS_GetLDnsPage(instanceId=ldnsId)
                data = jsonpath(res, '$.res.data')[0]
                if data:
                    data = data[0]
                    dns_instanceName = data['instanceName']
                    dns_updateTime = data['updateTime']
                    LDNS[ldnsId] = {'instanceName': dns_instanceName, 'updateTime': dns_updateTime}
                else:
                    raise KeyError('不存在云解析{}'.format(ldnsId))
        else:
            pass

        res = self.DNS_GetLDnsResolvePage(dnsId=ldnsId, instanceId=instanceId)
        data = jsonpath(res, '$.res.data')[0]

        if data:
            data = data[0]
            # 处理target
            if target is not None:
                if type_c is None or type_c == data['type']:  # 当target不为空，且type不变
                    data_target = set(data['target'].split(','))
                    addValues = list(set(target).difference(data_target)) if type(target) == list else list(
                        {target}.difference(data_target))
                    rmvValues = list(data_target.difference(set(target)))
                elif type_c != data['type']:  # 当target不为空且type发生变化
                    rmvValues = []
                    addValues = target if type(target) == list else [target]
                else:
                    rmvValues = []
                    addValues = []
        else:
            raise KeyError('云解析{}下无解析记录{}'.format(ldnsId, instanceId))
        keys = ['instanceId', 'ldnsId', 'ttl', 'desc']
        temp = {}
        for key in keys:
            _ = locals().get(key, None)
            temp[key] = data[key] if not _ else _
        temp['type'] = data['type'] if not type_c else type_c
        if dns_instanceName:
            instanceName = data['instanceName'][:-1 - len(dns_instanceName)]
        temp['instanceName'] = instanceName
        temp['rmvValues'] = rmvValues
        temp['addValues'] = addValues
        res = self.DNS_ModifyLDnsResolve(instanceId=instanceId, ldnsId=ldnsId, data=temp, regionId=regionId,
                                         **kwargs)
        return res

    def DNS_ModifyLDnsResolve_nrg_random(self, ldns, resolve_id):
        """
        随机修改传入的云解析记录
        :param ldns:
        :param resolve_id:
        :return:
        """
        instanceName = func_instanceName(random.randint(5, 20))
        ttl = str(random.randint(300, 2147483647))
        type_c = random.choice(list(dns_types.keys()))
        target = dns_types[type_c]()
        description = func_instanceName(random.randint(0, 64))

        res = self.DNS_ModifyLDnsResolve_nrg(ldnsId=ldns, instanceId=resolve_id, instanceName=instanceName,
                                             type_c=type_c,
                                             target=target, ttl=ttl, desc=description)
        return res

    def DNS_DeleteLDnsResolve(self, ldnsId, instanceIds: List, regionId=None, **kwargs):
        """
        删除内网云解析记录
        :param ldnsId:
        :param instanceIds:list
        :param regionId:
        :param kwargs:
        :return:{"res":null,"msg":"删除内网DNS解析记录成功","code":"Network.Success"}
        """
        api = 'api/networks/dns'
        action = 'DeleteLDnsResolve'
        method = 'delete'
        instanceIds = [instanceIds] if type(instanceIds) != list else instanceIds
        regionId = self.region[0] if regionId == None else regionId
        data = {"ldnsId": ldnsId, "instanceIds": instanceIds}
        res = self.send_request(api, method, data, Action=action, regionId=regionId, t=timeStap(), **kwargs)
        return res

    def DNS_GetLDnsResolvePage(self, dnsId, instanceId='', instanceName='', regionId=None, page=1, size=10, **kwargs):
        """
        :param dnsId:
        :param instanceId:
        :param instanceName:
        :param regionId:
        :param page: 1
        :param size: 10
        :param kwargs:
        :return:
        {
  "res": {
    "page": 1,
    "size": 10,
    "total": 1,
    "data": [
      {
        "instanceId": "dns-faha75mhluta",
        "instanceName": "cc.1.2.3.com.",
        "type": "CNAME",
        "ttl": 300,
        "desc": "",
        "status": "RUNNING",
        "ldnsId": "dns-fpmhed21id40",
        "target": "aa.com",   多个值用 ','分割
        "createTime": "2022-07-08T16:59:00.000+08:00",
        "updateTime": "2022-07-08T16:59:37.000+08:00",
        "isDeleted": 0
      }
    ]
  },
  "msg": "获取内网DNS解析记录成功",
  "code": "Network.Success"
}
        """
        ARGS = ['instanceId', 'instanceName', 'page', 'size']
        for arg in ARGS:
            temp = locals().get(arg, None)
            if temp:
                kwargs[arg] = temp
        api = 'api/networks/dns'
        action = 'GetLDnsResolvePage'
        method = 'get'
        regionId = self.region[0] if regionId is None else regionId
        data = {}
        res = self.send_request(api, method, data, Action=action, dnsId=dnsId, regionId=regionId, t=timeStap(),
                                **kwargs)
        return res

    def DNS_CreateLDnsPtr(self, ipAddress, ipType, cname, description='', ttl='300', projectId=None, regionId=None,
                          **kwargs):
        """
        创建反向解析
        :param ipAddress:ipv4,ipv6地址
        :param ipType:ipv4,ipv6
        :param cname:str
        :param description:
        :param ttl:
        :param projectId:
        :param regionId:
        :param kwargs:
        :return:
{
  "res": {
    "instanceId": "dns-faha8dil12u9",
    "userId": "6757cd7f-ccd1-4b79-a9ff-c2d4634bb6fa",
    "projectId": "1515973385144762368",
    "regionId": "hz-base-region",
    "vpcId": "",
    "type": "ipv6",
    "ipAddress": "fe80:0:0:0:0:0:0:1",
    "cname": "a.a.a.com.",
    "ttl": 300,
    "desc": "bbbbbb",
    "status": "RUNNING",
    "createTime": null,
    "updateTime": null,
    "isDeleted": 0
  },
  "msg": "创建内网DNS反向解析成功",
  "code": "Network.Success"
}
        """

        api = 'api/networks/dns'
        action = 'CreateLDnsPtr'
        method = 'post'
        regionId = self.region[0] if regionId is None else regionId
        projectId = self.project_id_(productCode='DNS') if projectId == None else projectId
        data = {"cname": cname, "ipAddress": ipAddress, "ipType": ipType, "ttl": ttl, "description": description,
                "projectId": projectId}
        res = self.send_request(api, method, data, Action=action, regionId=regionId, t=timeStap(), **kwargs)
        return res

    def DNS_GetLDnsPtrPage(self, instanceId='', cname='', ipAddress='', addr_type='', page=1, size=10, regionId=None,
                           **kwargs):
        """
        查询反向解析列表
        :param instanceId:
        :param cname:
        :param ipAddress:
        :param addr_type:
        :param page:1
        :param size:10
        :param regionId:
        :param kwargs:
        :return:
{
  "res": {
    "page": 1,
    "size": 10,
    "total": 1,
    "data": [
      {
        "instanceId": "dns-fpmhely5ym99",
        "userId": "6757cd7f-ccd1-4b79-a9ff-c2d4634bb6fa",
        "projectId": "1515973385144762368",
        "regionId": "hz-base-region",
        "vpcId": "",
        "type": "ipv4",
        "ipAddress": "1.1.1.1",
        "cname": "aa.com.",
        "ttl": 300,
        "desc": "aaaaaa",
        "status": "RUNNING",
        "createTime": "2022-07-09T11:03:31.000+08:00",
        "updateTime": "2022-07-09T11:03:31.000+08:00",
        "isDeleted": 0
      }
    ]
  },
  "msg": "获取内网DNS反向解析成功",
  "code": "Network.Success"
}
        """
        ARGS = ['instanceId', 'cname', 'ipAddress', 'addr_type', 'page', 'size']
        for arg in ARGS:
            temp = locals().get(arg, None)
            if temp:
                kwargs[arg] = temp
        api = 'api/networks/dns'
        action = 'GetLDnsPtrPage'
        method = 'get'
        regionId = self.region[0] if regionId is None else regionId
        data = None
        res = self.send_request(api, method, data, Action=action, regionId=regionId, t=timeStap(), **kwargs)
        return res

    def DNS_ModifyLDnsPtr(self, instanceId, cname='', ipAddress='', type='', ttl='', desc='', data=None, regionId=None,
                          **kwargs):
        """
        编辑反向云解析
        :param instanceId:
        :param cname:
        :param ipAddress:
        :param type:
        :param ttl:
        :param desc:
        :param data:
        :param regionId:
        :param kwargs:
        :return:
        """
        api = 'api/networks/dns'
        action = 'ModifyLDnsPtr'
        method = 'put'
        regionId = self.region[0] if regionId is None else regionId
        if not data:
            data = {"instanceId": instanceId, "cname": cname, "ipAddress": ipAddress, "type": type,
                    "ttl": ttl, "desc": desc}
        res = self.send_request(api, method, data, Action=action, regionId=regionId, t=timeStap(), **kwargs)
        return res

    def DNS_ModifyLDnsPtr_nrg(self, instanceId, cname=None, ipAddress=None, type_c=None, ttl=None, desc=None, data=None,
                              regionId=None, **kwargs):
        """
        编辑反向云解析，只改变有值的部分
        """
        res = self.DNS_GetLDnsPtrPage(instanceId=instanceId)
        data = jsonpath(res, '$.res.data')[0]
        if data:
            data = data[0]
            keys = ['instanceId', 'ipAddress', 'ttl', 'desc']
            temp = {}
            for key in keys:
                _ = locals().get(key, None)
                temp[key] = data[key] if not _ else _
            temp['type'] = data['type'] if not type_c else type_c
            temp['cname'] = cname if cname else data['cname'][:-1]
            res = self.DNS_ModifyLDnsPtr(instanceId=instanceId, data=temp, regionId=regionId, **kwargs)
            return res
        else:
            raise KeyError('未查询到实例:{}'.format(instanceId))

    def DNS_DeleteLDnsPtr(self, instanceIds: List, regionId=None, **kwargs):
        """
        删除反向云解析
        :param instanceIds:List
        :param regionId:
        :param kwargs:
        :return:{"res":null,"msg":"删除内网DNS反向解析成功","code":"Network.Success"}
        """
        api = 'api/networks/dns'
        action = 'DeleteLDnsPtr'
        method = 'delete'
        regionId = self.region[0] if regionId is None else regionId
        instanceIds = [instanceIds] if type(instanceIds) != list else instanceIds
        data = {"instanceIds": instanceIds}
        res = self.send_request(api, method, data, Action=action, regionId=regionId, t=timeStap(), **kwargs)
        return res

    def check_LDns_status(self, instancdId):
        """
        检查内部云解析是否存在，状态是否为Running
        :param instancdId:内部云解析实例Id
        :return:
        """
        res = self.DNS_GetLDnsPage(instanceId=instancdId)
        assert check_res_code(res), '检查是否存在内部云解析实例{} 发送失败'.format(instancdId)
        data = jsonpath(res, '$.res.data')[0]
        assert data, '未查询到内部云解析实例{}'.format(instancdId)
        instance = data[0]
        assert instance['instancdId'] == instancdId and instance['status'] == 'RUNNING', '云解析实例{}状态为{}'.format(
            instance['instancdId'], instance['status'])
        return True


def gen_ipv4_target():
    return [str(ipaddress.IPv4Address(random.randint(0, 4294967295))) for _ in range(random.randint(1, 50))]


def gen_ipv6_target():
    return [str(ipaddress.IPv6Address(random.randint(0, 340282366920938463463374607431768211455))) for _ in
            range(random.randint(1, 50))]


def gen_cname_target():
    return func_instanceName(random.randint(5, 10)) + '.' + func_instanceName(random.randint(5, 10))


dns_types = {'A': gen_ipv4_target, 'AAAA': gen_ipv6_target, 'CNAME': gen_cname_target}


def get_queryperf_data(target_f, res_f):
    """
    获取queryperf需要的data文件
    :param target_f: 在授权服务器使用pdnsutil list-zone default.rpz，将结果复制到target_f中
    :param res_f:结果文件，将文件拷贝到客户机上使用 ./queryperf  -d res_f -s 100.66.1.136 -l 120 测试
    :return:
    """
    f = open(target_f, 'r')
    res_f = open(res_f, 'w')
    RES = set()  # 去重用

    def A(context):
        return context[:-12]

    def AAAA(context):
        return context[:-12]

    def CNAME(context):
        return context[:-12]

    def PTR(context):
        return context[:-12]

    temp = {'A': A, 'AAAA': AAAA, 'CNAME': CNAME, 'PTR': PTR}
    for line in f.readlines():
        if line:
            line = line.split()
            try:
                if line[3] in temp.keys():  # 仅处理目前支持的
                    RES.add(temp[line[3]](line[0]) + ' ' + line[3] + '\n')
            except:
                pass

    res_f.writelines(RES)
    f.close()
    res_f.close()
    return list(RES)


def get_pdnsutil_delete_rrset(target_f):
    """
    使用pdnsutil list-zone ZONE获取解析记录，复制到target_中，生成删除解析记录的命令行
    :param target_f:
    :return:
    """
    temp = list()
    with open(target_f, 'r') as f:
        for line in f.readlines():
            line = line.split()
            temp.append('pdnsutil delete-rrset default.rpz {} {}'.format(line[0][:-12], line[3]))
            # print('pdnsutil delete-rrset default.rpz {} {}'.format(line[0][:-12], line[3]))
    temp = set(temp)
    for line in temp:
        print(line)
