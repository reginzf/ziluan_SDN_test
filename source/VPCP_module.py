# -*- coding: UTF-8 -*-
import time

from jsonpath import jsonpath

from source.locust_methods import Agent_SDN_nolocust, timeStap, check_res_code


class VPCP(Agent_SDN_nolocust):
    def __init__(self):
        super(VPCP, self).__init__()
        self.VPCP_set_default_code()

    def VPCP_set_default_code(self):
        """
        VPCP产品的默认参数，使用VPCP产品的话记得初始化
        :return:
        """
        self.instanceCode_normal = "vpcpeer.normal.local"
        self.specificationCode_normal = 'vpcpeer.normal.local'

    def VPCP_DeleteVpcp(self, vpcpId, **kwargs):
        """
        :param vpcpId:
        :param kwargs:
        :return:{"res":null,"msg":"对等连接被使用","code":"Network.VPCP.IsUsed"}
        """
        api = 'api/networks/vpcp'
        method = 'delete'
        action = 'DeleteVpcp'
        data = {}
        res = self.send_request(api, method, data, Action=action, vpcpId=vpcpId,
                                regionId=self.region_dict[self.target_region_name], t=timeStap(),
                                **kwargs)
        return res

    def VPCP_CreateVpcp(self, instanceName, vpcId, toVpcId, toUserId=None, quantity=1, renewType="notrenew",
                        rentCount=1, rentUnit="month", azoneId=None, chargeType="postpaid",
                        bandwidth=0, specificationCode="vpcpeer.normal.local", instanceCode='vpcpeer.normal.local',
                        orderCategory='NEW', payType="CHARGING_HOURS", **kwargs):
        """
        :param instanceName:
        :param vpcId:
        :param toVpcId:
        :param toUserId:
        :param quantity:
        :param renewType:
        :param rentCount:
        :param rentUnit:
        :param azoneId:
        :param chargeType: postpaid
        :param bandwidth:
        :param specificationCode:
        :param instanceCode:
        :param orderCategory:
        :param payType: CHARGING_HOURS
        :param kwargs:
        :return:{"res":{"orderId":"533978577943667267","resources":[{"product":"VPCP","instanceId":"vpcp-ecb1v6hzmg1y"}]},"msg":"购买VPC对等连接下单成功","code":"Network.Success"}
        """
        api = 'api/networks/vpcp'
        method = 'post'
        action = 'CreateVpcp'
        if not toUserId:
            toUserId = self.user_id
        azoneId = self.azone_id if azoneId == None else azoneId
        data = {"azoneId": azoneId, "chargeType": chargeType,
                "commonProperties": {"vpcId": vpcId, "toVpcId": toVpcId,
                                     "toUserId": toUserId, "bandwidth": bandwidth},
                "componentProperty": {"specificationCode": specificationCode},
                "instanceCode": instanceCode, "instanceName": instanceName, "orderCategory": orderCategory,
                "payType": payType,
                "productDescription": "{\"name\":\"{" + instanceName + "\",\"conf\":{\"实例名称\":\"" +
                                      instanceName +
                                      "\",\"本端地域\":\"成都研发测试主AZ节点\",\"本端VPC\":\"" +
                                      "VPC测试组（172.16.0.0/16）\",\"对端地域\":\"成都研发测试主AZ节点\",\"对端VPC\":\"pc2wip（192.168.0.0/16）\"}}",
                "productProperties": [], "quantity": quantity, "renewType": renewType, "rentCount": rentCount,
                "rentUnit": rentUnit}
        res = self.send_request(api, method, data, Action=action, regionId=self.region_dict[self.target_region_name],
                                t=timeStap(), **kwargs)
        return res

    def VPCP_DescribeVpcp(self, instanceId=None, instanceName=None, page=1, size=10, **kwargs):
        """

        :param instanceId:
        :param instanceName:
        :param page:
        :param size:
        :param kwargs:
        :return:
res: {page: 1, size: 10, total: 1,…}
page: 1
size: 10
total: 1
data: [{instanceId: "vpcp-ecb1v6hzmg1y", instanceName: "斯蒂芬斯蒂芬", instanceCode: "vpcpeer.normal.local",…}]
0: {instanceId: "vpcp-ecb1v6hzmg1y", instanceName: "斯蒂芬斯蒂芬", instanceCode: "vpcpeer.normal.local",…}
instanceId: "vpcp-ecb1v6hzmg1y"
instanceName: "斯蒂芬斯蒂芬"
instanceCode: "vpcpeer.normal.local"
vpcId: "vpc-ecb1u21dddey"
vpc: {userId: null, cidr: null, instanceId: "vpc-ecb1u21dddey", instanceName: "VPC测试组", instanceCode: null,…}
regionId: "cd-unicloud-region"
userId: "e9e4ef62-47df-4349-bee8-a64254f146b4"
userName: "account1"
regionName: "成都研发测试主AZ节点"
toVpcId: "vpc-ecb1vitl9049"
azoneId: "cd-unicloud-az1"
toVpc: {userId: null, cidr: null, instanceId: "vpc-ecb1vitl9049", instanceName: "pc2wip", instanceCode: null,…}
toRegionId: "cd-unicloud-region"
toUserId: "e9e4ef62-47df-4349-bee8-a64254f146b4"
toUserName: "account1"
toRegionName: "成都研发测试主AZ节点"
bandwidth: 0
status: "RUNNING"
instanceOperationType: {specificationClassCode: "vpcpeer.normal", componentCode: "PeeringConnection",…}
instanceOperationInfo: {operationStatus: 2, orderId: 533978577943667260, rentUnit: "month", chargeType: 0,…}
msg: "查询VPC对等连接成功"
code: "Network.Success"
        """
        ARGS = ['instanceId', 'instanceName']
        for arg in ARGS:
            temp = locals().get(arg, None)
            if temp:
                kwargs[arg] = temp
        api = 'api/networks/vpcp'
        method = 'get'
        action = 'DescribeVpcp'
        data = {}
        res = self.send_request(api, method, data, Action=action, regionId=self.region_dict[self.target_region_name],
                                t=timeStap(), **kwargs)
        return res

    def VPCP_AgreeVpcpAuth(self, id, **kwargs):
        """
        跨域授权
        :param id: 通过DescribeVpcpAuth 查到的id
        :param kwargs:
        :return:{"res":null,"msg":"同意VPC对等体跨账户申请成功","code":"Network.Success"}
        """
        api = 'api/networks/vpcp'
        action = 'AgreeVpcpAuth'
        method = 'put'
        data = {}
        res = self.send_request(api, method, data, Action=action, id=id,
                                regionId=self.region_dict[self.target_region_name], t=timeStap(),
                                **kwargs)
        return res

    def VPCP_DescribeVpcpAuth(self, page=1, size=10, **kwargs):
        """
        查询跨域授权列表
        :param kwargs:
        :return: res: {page: 1, size: 10, total: 1,
        data: [{id: 1, status: "agreed",…}]
            id: 1
            status: "agreed"
            context: {instanceCode: "vpcpeer.normal.local", rentCount: 1, productProperties: [], quantity: 1,…}
            instanceCode: "vpcpeer.normal.local"
            rentCount: 1
            productProperties: []
            quantity: 1
            instanceName: "test"
            rentUnit: "month"
            chargeType: "postpaid"
            renewType: "notrenew"
            trial: false
            componentProperty: {specificationCode: "vpcpeer.normal.local"}
            specificationCode: "vpcpeer.normal.local"
            commonProperties: {toVpcId: "vpc-e9ocxe64sf0f", bandwidth: 0, vpcId: "vpc-fj1xadpwubxw",…}
            toVpcId: "vpc-e9ocxe64sf0f"
            bandwidth: 0
            vpcId: "vpc-fj1xadpwubxw"
            toUserId: "314ea507-43e5-4e27-9531-153f8069a50c"
            azoneId: "cd-unicloud-region-az1"
            payType: "CHARGING_HOURS"
            orderCategory: "NEW"
            regionId: "cd-unicloud-region"
            userId: "4160c253-1818-4d8a-8763-fce26b08b5ad"
            toUserId: "314ea507-43e5-4e27-9531-153f8069a50c"
            createTime: "2022-05-27T14:10:30.000+08:00"
            updateTime: "2022-05-27T14:11:30.000+08:00"
    msg: "查询VPC对等体跨账户申请成功"
    code: "Network.Success"
        """
        api = 'api/networks/vpcp'
        action = 'DescribeVpcpAuth'
        method = 'get'
        data = {}
        res = self.send_request(api, method, data, Action=action, regionId=self.region_dict[self.target_region_name],
                                t=timeStap(), page=page,
                                size=size, **kwargs)
        # id = jsonpath(res,'$.res.data..id')
        return res

    def VPCP_DescribeVpcpAuth_wait(self) -> list:
        """
        获取所有等待处理的授权，返回待授权列表
        :return:[
        {
              "id": 8,
              "status": "wait",
              "context": {
                "instanceCode": "vpcpeer.normal.local",
                "rentCount": 1,
                "productProperties": [],
                "quantity": 1,
                "instanceName": "nrg-VPCP_3_1ZTG",
                "rentUnit": "month",
                "chargeType": "postpaid",
                "renewType": "notrenew",
                "trial": false,
                "componentProperty": {
                  "specificationCode": "vpcpeer.normal.local"
                },
                "commonProperties": {
                  "toVpcId": "vpc-fj10vx2y4b3d",
                  "bandwidth": 0,
                  "vpcId": "vpc-fj2iugjjrnj0",
                  "toUserId": "314ea507-43e5-4e27-9531-153f8069a50c"
                },
                "azoneId": "cd-unicloud-region-az1",
                "payType": "CHARGING_HOURS",
                "orderCategory": "NEW",
                "productDescription": "{\"name\":\"{nrg-VPCP_3_1ZTG\",\"conf\":{\"实例名称\":\"nrg-VPCP_3_1ZTG\",\"本端地域\":\"成都研发测试主AZ节点\",\"本端VPC\":\"VPC测试组（172.16.0.0/16）\",\"对端地域\":\"成都研发测试主AZ节点\",\"对端VPC\":\"pc2wip（192.168.0.0/16）\"}}"
              },
              "regionId": "cd-unicloud-region",
              "userId": "4160c253-1818-4d8a-8763-fce26b08b5ad",
              "toUserId": "314ea507-43e5-4e27-9531-153f8069a50c",
              "createTime": "2022-05-27T16:30:27.000+08:00",
              "updateTime": "2022-05-27T16:30:27.000+08:00"
            }
        ]
        """
        page, size = 1, 100
        vpcp_auth = []
        s_time = time.time()
        while time.time() - s_time < 300:
            res = self.VPCP_DescribeVpcpAuth(page=page, size=size)
            total = int(jsonpath(res, '$.res.total')[0])
            for data in jsonpath(res, '$.res.data')[0]:
                if data['status'] == 'wait':
                    vpcp_auth.append(data)
            if page * size >= total / size:
                break
            page += 1
        return vpcp_auth

    def VPCP_CreateVpcpAuth(self, instanceName, vpcId, toVpcId, toUserId=None, quantity=1, renewType="notrenew",
                            rentCount=1, rentUnit="month", azoneId=None, chargeType="postpaid",
                            bandwidth=0, specificationCode="vpcpeer.normal.local", instanceCode='vpcpeer.normal.local',
                            orderCategory='NEW', payType="CHARGING_HOURS", **kwargs):
        """
        创建跨域授权vpcp
        :param instanceName:
        :param vpcId:
        :param toVpcId:
        :param toUserId:
        :param quantity:
        :param renewType:
        :param rentCount:
        :param rentUnit:
        :param azoneId:
        :param chargeType: postpaid
        :param bandwidth:
        :param specificationCode:
        :param instanceCode:
        :param orderCategory:
        :param payType: CHARGING_HOURS
        :param kwargs:
        :return:{"res":null,"msg":"创建VPC对等体跨账户申请成功","code":"Network.Success"}
        """
        api = 'api/networks/vpcp'
        method = 'post'
        action = 'CreateVpcpAuth'
        if not toUserId:
            toUserId = self.user_id
        azoneId = self.azone_id if azoneId == None else azoneId
        data = {"azoneId": azoneId, "chargeType": chargeType,
                "commonProperties": {"vpcId": vpcId, "toVpcId": toVpcId,
                                     "toUserId": toUserId, "bandwidth": bandwidth},
                "componentProperty": {"specificationCode": specificationCode},
                "instanceCode": instanceCode, "instanceName": instanceName, "orderCategory": orderCategory,
                "payType": payType,
                "productDescription": "{\"name\":\"{" + instanceName + "\",\"conf\":{\"实例名称\":\"" +
                                      instanceName +
                                      "\",\"本端地域\":\"成都研发测试主AZ节点\",\"本端VPC\":\"" +
                                      "VPC测试组（172.16.0.0/16）\",\"对端地域\":\"成都研发测试主AZ节点\",\"对端VPC\":\"pc2wip（192.168.0.0/16）\"}}",
                "productProperties": [], "quantity": quantity, "renewType": renewType, "rentCount": rentCount,
                "rentUnit": rentUnit}
        res = self.send_request(api, method, data, Action=action, regionId=self.region_dict[self.target_region_name],
                                t=timeStap(), **kwargs)
        return res


def check_vpcp(self, instanceId):
    res = self.VPCP_DescribeVpcp(instanceId)
    assert check_res_code(res), '检查vpcp {} 失败'.format(instanceId)
    status = jsonpath(res, '$.res.data..status')
    assert status and status[0] == "RUNNING", '检查vpcp {}状态失败，当前为{}'.format(instanceId, status)
