# -*- coding: UTF-8 -*-
import jsonpath

from source.PRODUCT_module import PRODUCT
from source.locust_methods import timeStap, check_res_code


# 因为没有继承Agent类，所以部分方法是灰的
class EIP_product_cfg:
    component_code = "Bandwidth"
    specification_code = "eip.bgp.static"
    dict_instance_code = {'eip.bgp.static': "BGP(多线)", "eip.single.common": "单线",
                          'eip.single.internet.Instanse': "单线"}


class EIP(PRODUCT):
    def __init__(self):
        super(EIP, self).__init__()
        self.EIP_set_default_code()

    def EIP_set_default_code(self):
        """
        EIP产品的默认配置、属性
        :return:
        """
        self.dict_account_type = {'YEAR_MONTH': '包年包月', "CHARGING_HOURS": '按小时实时计费', "STREAM_HOUR_HOUR": '按流量付费',
                                  "DAY_TRIAL": "免费试用", 'DAY_MONTH': '按日月结'}
        self.resource_group_id = ''

    def EIP_create(self, eip_name, quantity=1, charge_type='prepaid', rent_count=1,
                   rent_unit="month", instanceCode='eip.bgp.static', projectId='',
                   eipInstanceCode="eip.bgp.static.instance", pay_type="YEAR_MONTH",
                   bandwidth=1, azoneId='', trial=False, **kwargs):
        """
        默认为单线、包年包月、1M
        :param name: str
        :param resource_group_id: 没填自动获取
        :param quantity:int 数量
        :param charge_type:['prepaid','postpaid']
        :param rent_count: 时长数 int
        :param rent_unit: 可售卖时长 ['month']
        :param instanceCode:['eip.bgp.static', 'eip.single','eip.bgp.dynamic','eip.bgp.static.instance']
        :param pay_type:["YEAR_MONTH", 'DAY_TRIAL', 'DAY_MONTH','CHARGING_HOURS','HOUR_MONTH_TIME','CHARGING_HOURS','STREAM_HOUR_HOUR']
        :param bandwidth:int
        :param kwargs:
        :return:{"res":{"orderId":"198371310903022649","resources":[{"EIP":"eip-bsji1ofyg6fg"}]},"msg":"操作成功","code":"Network.Success"}
        """
        api = 'api/networks/eip'
        action = 'AllocateEip'
        method = 'post'
        # 如果没有projectId,选一个
        if not projectId:
            res = self.getUserProjectList('BANDWIDTH_PUBLIC')
            resource_project_id = jsonpath.jsonpath(res, '$.res..resource_project_id')
            resource_project_name = jsonpath.jsonpath(res, '$.res..resource_project_name')
        try:
            index = resource_project_name.index('default')
            if index >= 0:
                projectId = resource_project_id[index]
        except ValueError:
            projectId = resource_project_id[0]
        except Exception as e:
            raise e
        self.resource_group_id = ''
        azoneId = self.azone_id if azoneId == '' else azoneId
        data = {"trial": trial, "projectId": projectId, "ipAddress": None,
                "azoneId": azoneId
            , "instanceName": eip_name,
                "quantity": quantity, "chargeType": charge_type, "rentCount": rent_count, "instanceCode": instanceCode,
                "bandwidth": bandwidth, "rentUnit": rent_unit,
                "productDescription": "{" + "\"name\":\"{name}\",\"billingMethod\":\"{billingMethod}\",".format(
                    name=eip_name,
                    billingMethod=pay_type) + "\"conf\":{" + "\"地域\":\"{region}\",\"线路选择\":\"{instance_code}\",\"带宽\":\"{bandwidth}Mbps\",\"计费模式\":\"{account_type}\"".format(
                    region=self.region[0], instance_code=self.dict_instance_code[instanceCode], bandwidth=bandwidth,
                    account_type=self.dict_account_type[pay_type]) + "}}",
                "payType": pay_type, "orderCategory": "NEW", "renewType": "manualrenew",
                "eipInstanceCode": eipInstanceCode}

        res = self.send_request(api, method, data, Action=action, regionId=self.region_dict[self.target_region_name],
                                t=timeStap(), **kwargs)
        return res

    def EIP_describe(self, instanceId='', eipName='', ipAddress='', page=1, size=10, **kwargs):
        """
        :param instanceId:
        :param eipName:
        :param ipAddress:
        :param kwargs:
        :return:{'res': {'page': 1, 'size': 10, 'total': 1, 'data': [{'instanceId': 'eip-bsji6pyst4yq', 'userId': '9d367b04-a5b9-4223-b69f-c961b568549f', 'regionId': 'H3C-HZ', 'status': 'RUNNING', 'instanceName': 'weyvipeip-2', 'instanceCode': 'eip.bgp.static', 'azoneId': 'H3C-HZ-AZ1', 'instanceOperationType': {'specificationClassCode': 'eip.bgp.static', 'componentCode': 'Bandwidth', 'rangeAttribute': 'bandwidth', 'bandwidth_unit': 'M', 'endSize': 500, 'start_bandwidth': 1, 'startSize': 1, 'step': 1, 'describe': '弹性公网IP-bgp(多线)*M', 'specificationCode': 'eip.bgp.static', 'step_unit': 'M', 'specificationName': 'bgp(多线)', 'end_bandwidth': 500}, 'instanceOperationInfo': {'operationStatus': 2, 'rentCount': 1, 'instanceName': 'weyvipeip-2', 'orderId': 198371706040009730, 'rentUnit': 'month', 'regionName': 'H3C-HZ', 'chargeType': 0, 'productGroupId': None, 'isThirdProduct': False, 'organizationId': '340db793-0d95-44ff-88b5-344ac7d3a920', 'payType': 'YEAR_MONTH', 'instanceReleaseTime': None, 'userParentId': None, 'releaseType': None, 'turnFormalTime': None, 'azId': 'H3C-HZ-AZ1', 'id': 'eip-bsji6pyst4yq', 'instanceLabel': 1, 'instanceRestartTime': None, 'productType': 'instance', 'isOld': 0, 'isPay': 1, 'instanceEndTime': 1628352000000, 'instanceParentId': 'ecs-bsji7ljamy8x', 'formalPayTime': 1625629303000, 'updateTime': 1625629310000, 'closeType': None, 'dueTime': '2021-08-08', 'instanceStartTime': 1625629303000, 'renewType': 1, 'userName': 'zlltest', 'userId': '9d367b04-a5b9-4223-b69f-c961b568549f', 'instanceCloseTime': None, 'instanceDescription': None, 'isPayClose': False, 'productCode': 'BANDWIDTH_PUBLIC', 'createTime': 1625629303000, 'regionId': 'H3C-HZ', 'isMspProduct': False, 'az': None, 'subUserId': None, 'projectId': None, 'trialDescription': None}, 'bandwidth': 100, 'ipAddress': '150.66.0.29', 'parentType': 'ECS', 'parentInstanceId': 'ecs-bsji7ljamy8x', 'parentInstanceName': None, 'cbwId': '', 'cbwInfo': None}]},
        'msg': '操作成功', 'code': 'Network.Success'}

        """
        for key, value in locals().items():
            if key == 'kwargs' or key == 'self':
                continue
            if value:
                kwargs[key] = value
        api = 'api/networks/eip'
        action = 'DescribeEip'
        method = 'get'
        data = {}
        res = self.send_request(api, method, data, Action=action, regionId=self.region_dict[self.target_region_name],
                                t=timeStap(), **kwargs)
        return res

    def EIP_describe_all(self) -> list:
        """获取所有EIP实例信息"""
        page, size = 1, 100
        res = self.EIP_describe(page=page, size=size)
        total = int(jsonpath.jsonpath(res, '$.res.total')[0])
        res_data = jsonpath.jsonpath(res, '$.res.data')[0]
        while total > len(res_data):
            page += 1
            res_data.extend(jsonpath.jsonpath(self.EIP_describe(page=page, size=size), '$.res.data')[0])
        return res_data

    def EIP_describe_available(self, **kwargs):
        '''
        :param kwargs:
        :return: res: [{"instanceId":"eip-bsjiz463ba2q","userId":"9d367b04-a5b9-4223-b69f-c961b568549f","regionId":"H3C-HZ","status":"RUNNING","instanceName":"emCyBzQiBuJeE","instanceCode":"eip.bgp.static","azoneId":"H3C-HZ-AZ1","instanceOperationType":None,"instanceOperationInfo":None,"bandwidth":43,"ipAddress":"150.66.0.177","parentType":"","parentInstanceId":"","parentInstanceName":None,"cbwId":"","cbwInfo":None}]
        msg: "操作成功"
        code: "Network.Success"
        '''
        api = 'api/networks/eip'
        action = 'DescribeAvailableEip'
        method = 'get'
        data = {}
        res = self.send_request(api, method, data, Action=action, regionId=self.region_dict[self.target_region_name],
                                azoneId=self.azone_id,
                                t=timeStap(), **kwargs)
        instance_ids = jsonpath.jsonpath(res, "$.res..instanceId")
        return instance_ids

    def EIP_release(self, eip_id, **kwargs):
        """
        :param eip_id: Unin[str,list]
        :param kwargs:
        :return: {"res":None,"msg":"操作成功","code":"Network.Success"}
        """

        eip_id = ','.join(eip_id) if type(eip_id) == list else eip_id
        api = 'api/networks/eip'
        method = 'delete'
        action = 'ReleaseEip'
        data = {}
        res = self.send_request(api, method, data, Action=action, regionId=self.region_dict[self.target_region_name],
                                instanceId=eip_id,
                                smsCode='', t=timeStap(), **kwargs)
        return res

    def EIP_modify(self, new_name, instance_id, **kwargs):
        """
        :param new_name:
        :param instance_id:
        :return: {"res":null,"msg":"操作成功","code":"Network.Success"}
        """
        api = 'api/networks/eip'
        action = 'ModifyEip'
        method = 'put'
        data = {}
        res = self.send_request(api, method, data, Action=action, regionId=self.region_dict[self.target_region_name],
                                insId=instance_id,
                                instanceName=new_name, t=timeStap(), **kwargs)
        return res

    def EIP_associate(self, eip_id, parent_id, port_id, parent_type='ECS', **kwargs):
        """
        :param eip_id:
        :param parent_type:['ECS','ENI','VIP']
        :param parent_id:
        :param port_id:
        :param kwargs:
        :return:{"res":null,"msg":"操作成功","code":"Network.Success"}
        """
        api = 'api/networks/eip'
        action = 'AssociateEip'
        method = 'put'
        data = {}
        res = self.send_request(api, method, data, Action=action, eipId=eip_id, parentId=parent_id,
                                parentType=parent_type, portId=port_id,
                                regionId=self.region_dict[self.target_region_name], **kwargs)
        return res

    def EIP_unassociate(self, eip_id, parent_id, **kwargs):
        """
        :param eip_id:
        :param parent_id:
        :param kwargs:
        :return:{"res":null,"msg":"操作成功","code":"Network.Success"}
        """
        api = 'api/networks/eip'
        action = 'UnassociateEip'
        method = 'put'
        data = {}
        res = self.send_request(api, method, data, Action=action, regionId=self.region_dict[self.target_region_name],
                                eipId=eip_id,
                                parentId=parent_id, t=timeStap(), **kwargs)
        return res

    def EIP_modify_eip_bandwidth(self, bandwidth, eip_name='', instance_id='', charge_type='postpaid',
                                 rent_unit="month", eipInstanceCode='eip.bgp.static.instance',
                                 instance_code='eip.bgp.static', pay_type='CHARGING_HOURS', order_category='UPGRADE',
                                 **kwargs, ) -> (str, str):
        """
        :param name: str
        :param charge_type:['prepaid','postpaid']
        :param order_category: ['UPGRADE', 'DOWNGRADE']
        :param rent_unit: 可售卖时长 ['month']
        :param pay_type:["YEAR_MONTH", 'DAY_TRIAL', 'DAY_MONTH','CHARGING_HOURS','HOUR_MONTH_TIME','CHARGING_HOURS','STREAM_HOUR_HOUR']
        :param bandwidth:int
        :param instance_id:
        :param instance_code:['eip.bgp.static']
        :param kwargs:
        :return:{"res":{"orderId":"198372925810719287","resources":[{"EIP":"eip-bsjjfxfzrend"}]},"msg":"操作成功","code":"Network.Success"}
        """
        api = 'api/networks/eip'
        method = 'post'
        action = 'ModifyEipBandwidth'
        data = {"chargeType": charge_type, "eipInstanceCode": eipInstanceCode,
                "instanceCode": instance_code, "bandwidth": bandwidth, "instanceId": instance_id,
                "payType": pay_type, "orderCategory": order_category,
                "productDescription": "{" + "\"name\":\"{name}\",\"billingMethod\":\"{billingMethod}\",".format(
                    name=eip_name,
                    billingMethod=pay_type) + "\"conf\":{" + "\"地域\":\"{region}\",\"线路选择\":\"{instance_code}\",\"带宽\":\"{bandwidth}Mbps\",\"计费模式\":\"{account_type}\"".format(
                    region=self.region[0], instance_code=self.dict_instance_code[instance_code], bandwidth=bandwidth,
                    account_type=self.dict_account_type[pay_type]) + "}}",
                "rentUnit": rent_unit}
        res = self.send_request(api, method, data, Action=action, regionId=self.region_dict[self.target_region_name],
                                t=timeStap(), **kwargs)
        return res


def check_eip_bind(self, eip, parent_id=None):
    # 检查单个eip的绑定状态，如果带了parent_id，状态为running+parentType检查通过为pass,不带，状态为running+parentType为None pass
    res = self.EIP_describe(eip)
    assert check_res_code(res), self.logger.info('查询eip {}状态失败'.format(eip))

    eip_info = jsonpath.jsonpath(res, '$.res.data')[0]
    if parent_id:
        parentType = parent_id.split('-')[0].upper()

        assert eip_info and eip_info[0]['parentType'] == parentType and eip_info[0][
            'parentInstanceId'] == parent_id and eip_info[0]['status'] == 'RUNNING', self.logger.info(
            '检查eip:{}绑定状态失败'.format(eip))
    else:
        assert eip_info and not eip_info[0]['parentType'] and not eip_info[0][
            'parentInstanceId'] and eip_info[0]['status'] == 'RUNNING', self.logger.info(
            '检查eip:{}解绑状态失败'.format(eip))


def check_eip_bandwidth(eip, bandwidth, self):
    res = self.EIP_describe(eip)
    _bandwidth = jsonpath.jsonpath(res, '$.res.data..bandwidth')
    assert _bandwidth and _bandwidth[0] == bandwidth, self.logger.info(
        'eip {}检查失败bandwidth期望{} 实际{}'.format(eip, bandwidth, _bandwidth))


def check_eip_status(eip, self):
    res = self.EIP_describe(instanceId=eip)
    status = jsonpath.jsonpath(res, '$.res.data..status')
    assert status and status[0] == 'RUNNING', 'eip:{}检查状态失败 status:{}'.format(eip, status)


def check_eip_unbind(self, eip):
    res_eip = self.EIP_describe(eip)
    assert check_res_code(res_eip), self.logger.info('查询eip {}状态失败'.format(eip))
    # 检查eip绑定状态
    eip_info = jsonpath.jsonpath(res_eip, '$.res.data')[0]
    assert eip_info and eip_info[0]['status'] == 'RUNNING' and not eip_info[0]['parentType'], self.logger.info(
        '检查eip:{}绑定状态失败'.format(eip))
