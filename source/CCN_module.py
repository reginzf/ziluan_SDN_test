# -*- coding: UTF-8 -*-
from typing import Union

from jsonpath import jsonpath

from source.locust_methods import Agent_SDN_nolocust, timeStap, check_res_code


class CCN(Agent_SDN_nolocust):
    def CCN_set_default_code(self):
        self.instanceCode_normal = "ccn.standard.normal"

    def CCN_Create(self, instanceName, azoneId=None, quantity=1, chargeType='postpaid', description='',
                   instanceCode='ccn.standard.normal', orderCategory='NEW', payType='DAY_MONTH',
                   renewType='notrenew', rentCount=1, rentUnit='month', **kwargs):
        """
        创建CCN实例
        :param instanceName:
        :param azoneId:
        :param quantity:
        :param chargeType:
        :param description:
        :param instanceCode:
        :param orderCategory:
        :param orderCategory:
        :param payType:
        :param renewType:
        :param rentCount:
        :param rentUnit:
        :return:{
  "res": {
    "orderId": "693881756562104647",
    "resources": [
      {
        "product": "CCN",
        "instanceId": "ccn-fj2it8nfbdui"
      }
    ]
  },
  "msg": "购买CCN下单成功",
  "code": "Network.Success"
}
        """
        if not azoneId:
            azoneId = self.azone_id
        api = 'api/networks/ccn'
        action = 'CreateCcn'
        method = 'post'
        data = {"azoneId": azoneId, "chargeType": chargeType, "commonProperties": {"description": description},
                "componentProperties": {}, "instanceCode": instanceCode, "instanceName": instanceName,
                "orderCategory": orderCategory, "payType": payType, "quantity": quantity, "renewType": renewType,
                "rentCount": rentCount,
                "rentUnit": rentUnit}
        res = self.send_request(api, method, data, Action=action, regionId=self.region_dict[self.target_region_name],
                                t=timeStap(), **kwargs)
        return res

    def CCN_DescribeCcn(self, instanceId=None, instanceName=None, page=1, size=10, **kwargs):
        """
        查询CCN列表
        :param InstanceId:
        :param InstanceName:
        :param page:
        :param size:
        :param kwargs:
        :return:
            res:
            data: [{
                    instanceId: "ccn-e44v57il98hc"
                    instanceName: "test"
                    instanceCode: "ccn.standard.normal"
                    payType: "DAY_MONTH"
                    description: ""
                    deleteType: "0"
                    userId: "6757cd7f-ccd1-4b79-a9ff-c2d4634bb6fa"
                    azoneId: "hz-base-az1"
                    regionId: "hz-base-region"
                    status: "RUNNING"
                    createTime: "2022-04-22T09:32:42.000+0800"
                    updateTime: "2022-04-22T09:32:42.000+0800"
                    }]
            msg: "查询CCN列表成功"
            code: "Network.Success"
        """
        ARGS = ['size', 'page', 'instanceId', 'instanceName']
        for arg in ARGS:
            temp = locals().get(arg, None)
            if temp:
                kwargs[arg] = temp
        api = 'api/networks/ccn'
        action = 'DescribeCcn'
        method = 'get'
        data = {}
        res = self.send_request(api, method, data, Action=action, regionId=self.region_dict[self.target_region_name],
                                t=timeStap(), **kwargs)
        # status = jsonpath(res, '$.res.data..status')[0]
        return res

    def CCN_CreateCcnVpc(self, ccn_id, vpcId, accountType=1, toUserId=None, **kwargs):
        """
        CCN绑定VPC
        :param ccn_id:
        :param vpcId:
        :param accountType:1 同账户 2 异账户
        :param toUserId:
        :param kwargs:
        :return: {"res":null,"msg":"CCN下创建网络实例成功","code":"Network.Success"}
        """
        api = 'api/networks/ccn'
        action = 'CreateCcnVpc'
        method = 'post'
        data = {"instanceId": ccn_id, "vpcId": vpcId, "accountType": accountType, "toUserId": toUserId}
        res = self.send_request(api, method, data, Action=action, regionId=self.region_dict[self.target_region_name],
                                t=timeStap(), **kwargs)
        return res

    def CCN_DeleteCcn(self, ccn_id: Union[str, list], **kwargs):
        """
        删除ccn实例
        :param ccn_id:
        :param kwargs:
        :return: {"res":null,"msg":"删除CCN成功","code":"Network.Success"}
        """
        api = 'api/networks/ccn'
        action = 'DeleteCcn'
        method = 'DELETE'
        data = ccn_id if type(ccn_id) == list else [ccn_id]
        res = self.send_request(api, method, data, Action=action, regionId=self.region_dict[self.target_region_name],
                                smsCode='', t=timeStap(),
                                **kwargs)
        return res

    def CCN_DeleteCcnVpc(self, ccn_id, vpcId, **kwargs):
        """
        删除CCN下绑定的VPC
        :param ccn_id:
        :param vpcId:
        :param kwargs:
        :return: {"res":null,"msg":"批量删除网络实例成功","code":"Network.Success"}
        """
        api = 'api/networks/ccn'
        action = 'DeleteCcnVpc'
        method = 'delete'
        data = [vpcId]
        res = self.send_request(api, method, data, Action=action, regionId=self.region_dict[self.target_region_name],
                                ccnId=ccn_id, t=timeStap(),
                                **kwargs)
        return res

    def CCN_DescribeCcnVpc(self, instanceId='', page=1, size=10, **kwargs):
        """
        查询CCN详细信息
        :param instanceId: ccn_id
        :param instanceName: ccn_name
        :param page:
        :param size:
        :param kwargs:
        :return:{code: "Network.Success"
            msg: "分页查询CCN下网络实例列表成功"
            res: {
                data: [
                    {instanceId: "ccn-e9ocxm288jsm", regionId: "cd-unicloud-region", azoneId: "cd-unicloud-region-az1",…}
                    accountType: "1"
                    authFlag: "1"
                    azoneId: "cd-unicloud-region-az1"
                    cidr: "192.168.1.0/24"
                    createTime: "2022-05-10T17:53:01.000+0800"
                    instanceId: "ccn-e9ocxm288jsm"
                    instanceType: "VPC"
                    regionId: "cd-unicloud-region"
                    status: "0"
                    toUserId: "911aa6e2-8ffe-4555-b148-2ac147f3c4de"
                    updateTime: "2022-05-10T17:53:01.000+0800"
                    userId: "911aa6e2-8ffe-4555-b148-2ac147f3c4de"
                    vpcId: "vpc-e9ocxe64r7fp"
                    vpcName: "ccn01"
                    vpcStatus: "RUNNING"
                }]
                page: 1
                size: 10
                total: 1
        """
        api = 'api/networks/ccn'
        action = 'DescribeCcnVpc'
        method = 'get'
        data = {}
        res = self.send_request(api, method, data, Action=action, regionId=self.region_dict[self.target_region_name],
                                t=timeStap(), page=page,
                                size=size, instanceId=instanceId, **kwargs)
        # $.res.data..instanceId  $.res.data..vpcStatus
        return res

    def check_ccn_vpc_status(self, ccn, vpcs: list):
        """
        检查ccn下vpc状态
        :param ccn:
        :param vpcs:
        :return:
        """
        res = self.CCN_DescribeCcnVpc(ccn)
        assert check_res_code(res), '查询ccn {}失败'.format(ccn)
        vpcs_ = jsonpath(res, '$.res.data..vpcId')  # ccn下所有vpc
        status = jsonpath(res, '$.res.data..vpcStatus')
        temp = {}
        for key, value in zip(vpcs_, status):
            temp[key] = value
        for vpc in vpcs:  # 检查目标vpc状态
            vpc_status = temp.get(vpc, None)
            if vpc_status:
                assert vpc_status == 'RUNNING', 'CCN {}中{}状态为{}'.format(ccn, vpc, vpc_status)
            else:
                assert vpc_status, 'CCN {} 下不存在{}'.format(ccn, vpc)

    def check_vpc_deleted(self, ccn, vpcs: list):
        """
        检查ccn下vpc是否被删除
        :param ccn:
        :param vpcs:
        :return:
        """
        res = self.CCN_DescribeCcnVpc(ccn)
        assert check_res_code(res)
        vpcs_ = jsonpath(res, '$.res.data..vpcId')
        for vpc in vpcs:
            assert vpc not in vpcs_, 'CCN {}下{}未删除'.format(ccn, vpc)

    def check_ccn_status(self, ccn):
        """
        检查ccn状态是否为RUNNING
        :param ccn:
        :return:
        """
        res = self.CCN_DescribeCcn(instanceId=ccn)
        assert check_res_code(res), '查询ccn{}失败'.format(ccn)
        status = jsonpath(res, '$.res.data..status')
        assert status and status[0] == 'RUNNING', '检查CCN {}状态失败'.format(ccn)
