# -*- coding: UTF-8 -*-
import ipaddress
import random
import time

from jsonpath import jsonpath

from source.PRODUCT_module import PRODUCT
from source.locust_methods import timeStap, func_instanceName, check_res_code, randomIP

PROTOCOL = {'any': 4, 'TCP': 0, 'UDP': 1, 'ICMP': 2}


class CFW(PRODUCT):
    productCode_CFW = 'CFW'
    SCP_STATUS = [False, True]

    def CFW_createCfwOrder(self, instanceName, vpcpId=None, cloudConnectNetworkId=None, destVpcId='', srcVpcId='',
                           chargeType='prepaid',
                           specificationCode='cfw.spec.lite', projectId=None, azoneId=None,
                           instanceCode='CloudFirewall', renewType="notrenew", rentUnit='month',
                           orderCategory='NEW', payType='YEAR_MONTH', quantity=1, rentCount=1,
                           **kwargs):
        """
        使用vpcp或ccn创建cfw
        :param instanceName:
        :param cloudConnectNetworkId: ccn_id
        :param vpcpId: vpcp_id
        :param destVpcId:
        :param srcVpcId:
        :param chargeType:
        :param specificationCode:cfw.spec.code cfw.spec.lite
        :param instanceCode:
        :param orderCategory:
        :param payType:
        :param quantity:
        :param renewType:
        :param rentCount:
        :param kwargs:
        :return:{
                  "res": {
                    "orderId": "712374751867336455",
                    "resources": [
                      {
                        "product": "CFW",
                        "instanceId": "cfw-fo4l15es18be"
                      }
                    ]
                  },
                  "msg": "创建订单成功",
                  "code": "Network.Success"
                }
        """
        api = 'api/networks/cfw'
        action = 'CreateCfwOrder'
        method = 'post'
        projectId = self.project_id_(projectId, self.productCode_CFW)
        azoneId = self.azone_id if azoneId == None else azoneId

        if cloudConnectNetworkId:
            productProperties = {'cloudConnectNetworkId': cloudConnectNetworkId}
        elif vpcpId:
            productProperties = {"destVpcId": destVpcId, "srcVpcId": srcVpcId, "vpcpId": vpcpId}
        else:
            raise AttributeError('Must have vpcpId or cloudConnectNetworkId')
        data = {"projectId": projectId, "trial": False, "azoneId": azoneId,
                "chargeType": chargeType, "componentProperty": {"specificationCode": specificationCode},
                "instanceCode": instanceCode, "instanceName": instanceName, "orderCategory": orderCategory,
                "payType": payType,
                "productProperties": [productProperties],
                "quantity": quantity, "renewType": renewType, "rentCount": rentCount, "rentUnit": rentUnit}
        res = self.send_request(api, method, data, Action=action, regionId=self.region_dict[self.target_region_name],
                                t=timeStap(), **kwargs)
        return res

    def CFW_DeleteCfw(self, cfw_ids: list, type='VPCP', **kwargs):
        """
        删除cfw实例
        :param cfw_ids: cfw_id列表
        :param type: VPCP | CCN
        :return:{"res":null,"msg":"删除虚拟防火墙成功","code":"Network.Success"}
        """
        api = 'api/networks/cfw'
        action = 'DeleteCfw'
        method = 'post'
        data = {"type": type, "instanceIds": cfw_ids}
        res = self.send_request(api, method, data, Action=action, regionId=self.region_dict[self.target_region_name],
                                t=timeStap(), **kwargs)
        return res

    def check_ecs_is_deleted(self, cfw_id):
        """
        通过检查sql，确认对应虚机是否被删除
        :param cfw_id:
        :return:
        """
        sql_conn_uni_network_basic = self.c_sql.connect_db('uni_network_basic').cursor()
        sql_conn_uni_compute = self.c_sql.connect_db('uni_network_basic').cursor()

        sql_conn_uni_network_basic.execute(
            f'''SELECT ecs_id FROM tbl_base_ecs_resource a WHERE instance_id='{cfw_id}';''')
        ecs = [ele['ecs_id'] for ele in sql_conn_uni_network_basic.fetchall()]
        self.logger.info(msg='{} 下的ecs：{}'.format(cfw_id, ecs))
        for e in ecs:
            sql_conn_uni_compute.execute(
                '''SELECT is_deleted FROM uni_compute.tbl_domain WHERE domain_uuid='{}' '''.format(e))
            res = sql_conn_uni_compute.fetchall()
            assert res and res[0]['is_deleted'] == '1', '{}下的{}未删除,状态:{}'.format(cfw_id, e, res)
        sql_conn_uni_network_basic.close()
        sql_conn_uni_compute.close()

    def CFW_CfwList(self, instanceId=None, instanceName=None, type='VPCP', page=1, size=10, **kwargs):
        """
        获取cfw
        :param instanceId:
        :param instanceName:
        :param kwargs:
        :return:

    res: data: [{instanceId: "cfw-ecb1v6hzmg1n", instanceName: "CFW_3_1", instanceCode: "cfw.spec.lite",…}]
    0: {instanceId: "cfw-ecb1v6hzmg1n", instanceName: "CFW_3_1", instanceCode: "cfw.spec.lite",…}
    instanceId: "cfw-ecb1v6hzmg1n"
    instanceName: "CFW_3_1"
    instanceCode: "cfw.spec.lite"
    userId: "e9e4ef62-47df-4349-bee8-a64254f146b4"
    regionId: "cd-unicloud-region"
    azId: "cd-unicloud-az1"
    vpcpId: "vpcp-ecb1v6hzmg1l"
    srcVpcId: "vpc-ecb1vqpqqffn"
    destVpcId: "vpc-ecb1vitl96ij"
    rgId: "rg092429885444"
    status: "CREATING"
    specificationClassCode: "cfw.spec"
    componentCode: "CloudFirewall"
    specificationCode: "cfw.spec.lite"
    componentProperty: {specificationCode: "cfw.spec.lite"}
    msg: "获取虚拟防火墙列表成功"
    code: "Network.Success"
        """
        ARGS = ['instanceId', 'instanceName', 'page', 'size']
        for arg in ARGS:
            temp = locals().get(arg, None)
            if temp:
                kwargs[arg] = temp
        api = 'api/networks/cfw'
        action = 'CfwList'
        method = 'get'
        data = {}

        res = self.send_request(api, method, data, Action=action, regionId=self.region_dict[self.target_region_name],
                                type=type, **kwargs)
        # status = jsonpath(res, '$.res.data..status')
        return res

    def CFW_cfwAvbVpcpList(self, **kwargs):
        """
        :param kwargs:
        :return:
        """
        api = 'api/iam/cfw'
        action = 'cfwAvbVpcpList'
        method = 'get'
        data = {}
        res = self.send_request(api, method, data, Action=action, azoneId=self.azone_id, t=timeStap(), **kwargs)
        return res

    def CFW_CfwAvbInstanceList(self, **kwargs):
        """
        查询可用的CCN实例
        :param kwargs:
        :return:{
                  "res": [
                    {
                      "instanceId": "ccn-fo4l0d9tgb5h",
                      "instanceName": "测试接口用",
                      "vpcId": null,
                      "toVpcId": null,
                      "toUserId": null,
                      "userId": "4160c253-1818-4d8a-8763-fce26b08b5ad",
                      "vpcName": null,
                      "toVpcName": null
                    }
                  ],
                  "msg": "获取可用实例列表成功",
                  "code": "Network.Success"
                }
        """
        api = 'api/networks/cfw'
        action = 'CfwAvbInstanceList'
        method = 'get'
        data = {}
        res = self.send_request(api, method, data, Action=action, regionId=self.region_dict[self.target_region_name],
                                azoneId=self.azone_id,
                                type='CCN', t=timeStap(), **kwargs)
        return res

    def CFW_CfwScpList(self, cfwId, instanceId='', name='', page=1, size=10, **kwargs):
        """
        获取指定cfw下的scp
        :param cfwId:
        :param instanceId: scp的实例Id
        :param name:名称
        :param page:1
        :param size:10
        :param kwargs:
        :return:{
    "res": {
    "page": 1,
    "size": 10,
    "total": 2,
    "data": [
      {
        "name": "permitAll",
        "instanceId": "scp-fj1xebr4yau3",
        "cfwId": "cfw-fj10y0kpe9tb",
        "description": "",
        "srcNetwork": null,
        "destNetwork": null,
        "srcIpAddress": "0.0.0.0/0",
        "destIpAddress": "0.0.0.0/0",
        "protocol": 4,
        "srcVmPortStart": null,
        "srcVmPortEnd": null,
        "destVmPortStart": null,
        "destVmPortEnd": null,
        "priority": 1,
        "index": 101,
        "strategy": 2,
        "hitCount": 6093,
        "status": 0, 0为关闭，2为开启
        "vpcId": null
      },
    ]
    },
    "msg": "获取安全策略列表成功",
    "code": "Network.Success"
    }
        """
        ARGS = ['instanceId', 'name', 'page', 'size']
        for arg in ARGS:
            if locals().get(arg, False):
                kwargs[arg] = locals()[arg]
        api = 'api/networks/cfw'
        action = 'CfwScpList'
        method = 'get'
        data = {}
        res = self.send_request(api, method, data, Action=action, cfwId=cfwId,
                                regionId=self.region_dict[self.target_region_name], t=timeStap(),
                                **kwargs)
        # name = jsonpath(res, '$.res.data..name')
        return res

    def CFW_CfwScpList_all(self, cfwId, **kwargs) -> list:
        ret = []
        page = 1
        size = 100
        s_time = time.time()
        while time.time() - s_time <= 300:
            res = self.CFW_CfwScpList(cfwId, page=page, size=size, **kwargs)
            total = int(jsonpath(res, '$.res.total')[0])
            ret.extend(jsonpath(res, '$.res.data')[0])
            if page * size >= total:
                break
            page += 1
        return ret

    def CFW_CreateCfwScp_random(self, cfw, name_prefix='', direction=1, network_strict=False, **kwargs):
        """
        在cfw下创建随机scp，direction默认为1，放在最后
        :param cfw: cfw实例id
        :param name_prefix:名称前缀
        :param network_strict:Flase 源目随机，True 源目为网络位
        :param kwargs:
        :return: 返回CFW_CreateCfwScp接口的返回
        """
        scp_name = name_prefix + func_instanceName(25 - len(name_prefix))
        src = '{}/{}'.format(randomIP(), random.randint(16, 25))
        dst = '{}/{}'.format(randomIP(), random.randint(16, 25))
        if network_strict:
            src = str(ipaddress.ip_network(src, strict=False))
            dst = str(ipaddress.ip_network(dst, strict=False))
        protocol = PROTOCOL[random.choice(list(PROTOCOL.keys()))]
        strategy = random.choice([1, 2])
        # direction = 1   放在最后，不影响当前业务
        enable = random.choice(self.SCP_STATUS)
        if protocol in [0, 1]:
            srcVmPortStart = random.randint(1, 60000)
            srcVmPortEnd = random.randint(srcVmPortStart, 65535)
            destVmPortStart = random.randint(1, 60000)
            destVmPortEnd = random.randint(destVmPortStart, 65535)
            res = self.CFW_CreateCfwScp(cfw, scp_name, src, dst, protocol, func_instanceName(18), str(srcVmPortStart),
                                        str(srcVmPortEnd), str(destVmPortStart), str(destVmPortEnd), strategy,
                                        direction,
                                        enable, **kwargs)
        else:
            res = self.CFW_CreateCfwScp(cfw, scp_name, src, dst, protocol, func_instanceName(18), strategy=strategy,
                                        direction=direction,
                                        enable=enable, **kwargs)
        return res

    def CFW_CreateCfwScp(self, cfwId, scp_name, srcIpAddress, destIpAddress, protocol, description='',
                         srcVmPortStart='', srcVmPortEnd='', destVmPortStart='', destVmPortEnd='', strategy=2,
                         direction=1, enable=True, **kwargs):
        """
        创建scp
        :param cfwId:
        :param name:策略名称
        :param description:描述
        :param srcIpAddress:源地址 etc: 0.0.0.0/0
        :param destIpAddress:目的地址
        :param protocol: any:4 TCP:0 UDP:1 ICMP:2
        :param srcVmPortStart: str etc:'123'
        :param srcVmPortEnd:
        :param destVmPortStart:
        :param destVmPortEnd:
        :param strategy: 允许：2 禁止：1
        :param direction: 最后：1 最前：0
        :param enable: 启用：True，关闭False
        :return:{"res":null,"msg":"创建安全策略成功","code":"Network.Success"}
        """
        api = 'api/networks/cfw'
        action = 'CreateCfwScp'
        method = 'post'
        data = {"cfwId": cfwId, "name": scp_name, "description": description, "srcIpAddress": srcIpAddress,
                "destIpAddress": destIpAddress, "protocol": protocol, "srcVmPortStart": srcVmPortStart,
                "srcVmPortEnd": srcVmPortEnd, "destVmPortStart": destVmPortStart, "destVmPortEnd": destVmPortEnd,
                "strategy": strategy, "direction": direction, "enable": enable}
        res = self.send_request(api, method, data, Action=action, regionId=self.region_dict[self.target_region_name],
                                t=timeStap(), **kwargs)
        return res

    def CFW_DeleteCfwScp(self, cfwId, instanceIds: list, **kwargs):
        """
        删除cfw下的scp，支持多条操作
        :param cfwId:
        :param instanceIds:
        :param kwargs:
        :return:{"res":null,"msg":"删除安全策略成功","code":"Network.Success"}
        """
        api = 'api/networks/cfw'
        action = 'DeleteCfwScp'
        method = 'post'
        instanceIds = [instanceIds] if type(instanceIds) == str else instanceIds
        data = {"cfwId": cfwId, "instanceIds": instanceIds}
        res = self.send_request(api, method, data, Action=action, regionId=self.region_dict[self.target_region_name],
                                t=timeStap(), **kwargs)
        return res

    def CFW_StopCfwScp(self, cfwId, instanceIds: list, **kwargs):
        """
        关闭cfw下的scp，支持多条操作
        :param cfwId:
        :param instanceIds:
        :param kwargs:
        :return:{"res":null,"msg":"关停安全策略成功","code":"Network.Success"}
        """
        api = 'api/networks/cfw'
        action = 'StopCfwScp'
        method = 'post'
        instanceIds = [instanceIds] if type(instanceIds) == str else instanceIds
        data = {"cfwId": cfwId, "instanceIds": instanceIds}
        res = self.send_request(api, method, data, Action=action, regionId=self.region_dict[self.target_region_name],
                                t=timeStap(), **kwargs)
        return res

    def CFW_StartCfwScp(self, cfwId, instanceIds: list, **kwargs):
        """
        开启cfw下的scp，支持多条操作
        :param cfwId:
        :param instanceIds:
        :param kwargs:
        :return:{"res":null,"msg":"开启安全策略成功","code":"Network.Success"}
        """
        api = 'api/networks/cfw'
        action = 'StartCfwScp'
        method = 'post'
        instanceIds = [instanceIds] if type(instanceIds) == str else instanceIds
        data = {"cfwId": cfwId, "instanceIds": instanceIds}
        res = self.send_request(api, method, data, Action=action, regionId=self.region_dict[self.target_region_name],
                                t=timeStap(), **kwargs)
        return res

    def CFW_scp_log_list(self, cfw_id, page=1, size=10, startTime=-1, endTime=-1, protocol=-1, stragegy=-1,
                         securityPolicyName=-1, **kwargs):
        for key, value in locals().items():
            if key in ('kwargs', 'self'):
                continue
            if value != -1:
                kwargs[key] = value
        api = 'api/iam/cfw'
        method = 'get'
        data = {}
        action = 'cfwScpLogList'
        res = self.send_request(api, method, data, Action=action, t=timeStap(), azoneId=self.azone_id, cfwId=cfw_id,
                                **kwargs)
        return res

    def CFW_ChangeCfwScpPriority(self, cfwId, scpId, targetId, direction, **kwargs):
        """
        调整scp顺序
        :param cfwId:
        :param scpId:
        :param targetId:
        :param direction: 0：调整到targetId之前  1：调整到targetId之后
        :param kwargs:
        :return:{"res":null,"msg":"调整安全策略的优先级成功","code":"Network.Success"}
        """
        api = 'api/networks/cfw'
        action = 'ChangeCfwScpPriority'
        method = 'post'
        data = {"cfwId": cfwId, "direction": direction, "instanceId": scpId, "targetId": targetId}
        res = self.send_request(api, method, data, Action=action, regionId=self.region_dict[self.target_region_name],
                                t=timeStap(), **kwargs)
        return res

    def CFW_CfwScpSessionList(self, cfwId, scpId, page=1, size=10, **kwargs):
        """
        查询scp命中信息
        :param cfwId:
        :param scpId:
        :param kwargs:
        :return:
        """
        api = 'api/networks/cfw'
        action = 'CfwScpSessionList'
        method = 'get'
        data = {}
        res = self.send_request(api, method, data, Action=action, regionId=self.region_dict[self.target_region_name],
                                page=page, size=size,
                                cfwId=cfwId, instanceId=scpId, **kwargs)
        return res

    def __CFW_ModifyCfwScp(self, cfwId='', scpId='', name='', srcIpAddress='', destIpAddress='', protocol='',
                           description='',
                           srcVmPortStart=None,
                           srcVmPortEnd=None, destVmPortStart=None, destVmPortEnd=None, strategy=2, direction=1,
                           data=None,
                           **kwargs):
        """
        参数和创建scp接口一致,建议读取scp信息后再编辑
        :return:{"res":null,"msg":"修改安全策略成功","code":"Network.Success"}
        """
        api = 'api/networks/cfw'
        action = 'ModifyCfwScp'
        method = 'post'
        if not data:
            data = {"instanceId": scpId, "cfwId": cfwId, "name": name, "description": description,
                    "srcIpAddress": srcIpAddress, "destIpAddress": destIpAddress, "protocol": protocol,
                    "srcVmPortStart": srcVmPortStart,
                    "srcVmPortEnd": srcVmPortEnd, "destVmPortStart": destVmPortStart,
                    "destVmPortEnd": destVmPortEnd,
                    "strategy": strategy, "direction": direction}
        res = self.send_request(api, method, data, Action=action, regionId=self.region_dict[self.target_region_name],
                                t=timeStap(), **kwargs)
        return res

    def CFW_ModifyCfwScp(self, cfwId, instanceId, **kwargs):
        """
        查询scp信息，先赋值给模板，然后本地有值再替换。
        :param cfwId:
        :param instanceId:
        :param kwargs:
        :return:
        """
        res = self.CFW_CfwScpList(cfwId, instanceId)
        temp = jsonpath(res, '$.res.data')[0]
        if temp:
            temp = temp[0]
        else:
            return False
        template = {"instanceId": "", "cfwId": "", "name": "", "description": "",
                    "srcIpAddress": "", "destIpAddress": "", "protocol": 0, "srcVmPortStart": "",
                    "srcVmPortEnd": "", "destVmPortStart": "", "destVmPortEnd": "", "strategy": 1,
                    "direction": 1}
        for key in template.keys():
            template[key] = temp.get(key, template[key])
        for key, value in kwargs.items():
            template[key] = kwargs[key]
        res = self.__CFW_ModifyCfwScp(data=template)
        return res

    def check_cfw_scp_num(self, cfw, target_num: int):
        """
        检查cfw下的scp数量
        :param cfw:
        :param target_num:
        :return:
        """
        res = self.CFW_CfwScpList(cfw)
        assert check_res_code(res), '查询{} scp信息失败'.format(cfw)
        total = int(jsonpath(res, '$.res.total')[0])
        assert total == target_num

    def check_cfw_status(self, cfw):
        """
        检查cfw的状态是否为running
        :param cfw:
        :return:
        """
        for k, v in cfw.items():
            res = self.CFW_CfwList(instanceId=k, type=v)
            assert check_res_code(res), '查询{} 信息失败'.format(cfw)
            status = jsonpath(res, '$.res.data..status')
            assert status and status[0] == 'RUNNING', '检查{}状态失败，当前状态为{}'.format(cfw, status)
