# -*- coding: UTF-8 -*-
import json
import jsonpath
import logging

from source.locust_methods import timeStap, check_res_code
from source.PRODUCT_module import PRODUCT
from source.commons import PayType


class NAT(PRODUCT):
    component_code = "NetworkAddressTranslation"
    specification_code = "nat.normal"

    def NAT_get_available_vpc(self, azoneId=None, **kwargs) -> list:
        '''
        :return:
        '''
        api = 'api/networks/nat'
        action = 'DescribeAvailableVpcForNat'
        method = 'get'
        data = {}

        res = self.send_request(api, method, data, Action=action, regionId=self.region_dict[self.target_region_name],
                                azoneId=azoneId,
                                t=timeStap(), **kwargs)
        return res['res']

    def NAT_create(self, name, vpc_instance, vpc_name, description='', nat_instance_code='nat.normal',
                   payType='DAY_MONTH', quantity=1, renewType="manualrenew", rentCount=1, rentUnit='month',
                   eip_instanceCode='', orderCategory='NEW', region_name=None, trial=False, projectId='',
                   azoneId='', chargeType='postpaid', specificationCode="nat.normal", price=0, **kwargs):
        """
        :param name:
        :param vpc_instance:
        :param vpc_name:
        :param description:
        :param nat_instance_code:
        :param payType:
        :param quantity:
        :param renewType:
        :param rentCount:
        :param rentUnit:
        :param eip_instanceCode:
        :param orderCategory:
        :param region_name:
        :param trial:
        :param projectId:
        :param azoneId:
        :param chargeType:
        :param specificationCode:
        :param price:
        :param kwargs:
        :return:{"res":{"orderId":"198370761147189431","resources":[{"product":"NAT","instanceId":"nat-bsjiunvz1qoa"}]},"msg":"购买NAT网关下单成功","code":"Network.Success"
        """
        api = 'api/networks/nat'
        method = 'post'
        action = 'CreateNat'
        if not price:
            try:
                price = \
                    self.get_product_price(product_name='NAT', charge_type=chargeType, order_category=orderCategory,
                                           pay_type=payType,
                                           quantity=quantity, count=rentCount, unit=rentUnit)['totalPrice']
            except Exception as e:
                price = 0
                logging.info(msg=e.args)
        projectId = self.project_id_(projectId, 'NAT')
        azoneId = self.azone_id if azoneId == '' else azoneId
        region_name = self.region_name if region_name is None else region_name
        data = {
            "trial": trial,
            "projectId": projectId,
            "azoneId": azoneId,
            "chargeType": chargeType,
            "componentProperty": {
                "specificationCode": specificationCode
            },
            "eipInstanceCode": eip_instanceCode,
            "instanceCode": nat_instance_code,
            "instanceName": name,
            "orderCategory": orderCategory,
            "payType": payType,
            "productDescription": json.dumps({'totalPrice': price, 'vpc': f'{vpc_instance}/{vpc_name}', 'conf': {
                '地域': region_name, 'vpc': f'{vpc_instance}/{vpc_name}',
                '计费模式': f'{getattr(PayType, payType)}'}}),
            "productProperties": [
                {
                    "description": description,
                    "eipId": eip_instanceCode,
                    "vpcId": vpc_instance
                }
            ],
            "quantity": quantity,
            "renewType": renewType,
            "rentCount": rentCount,
            "rentUnit": rentUnit
        }
        res = self.send_request(api, method, data, Action=action, regionId=self.region_dict[self.target_region_name],
                                t=timeStap(), **kwargs)
        return res

    def NAT_delete(self, instance_id, **kwargs):
        '''
        :param instance:string
        :param kwargs:msCode=  ,regionId='H3C-HZ',page:1 zise:10
        :return: {"res":None,"msg":"删除NAT网关成功","code":"Network.Success"}
        '''
        api = 'api/networks/nat'
        action = 'DeleteNat'
        method = 'delete'
        data = {}
        res = self.send_request(api, method, data, Action=action, natIds=instance_id,
                                regionId=self.region_dict[self.target_region_name],
                                smsCode='', t=timeStap(), **kwargs)
        return res

    def NAT_describe(self, instanceId=None, instanceName=None, page=1, size=100, **kwargs):
        '''
        :param kwargs: instanceId,instanceName
        :return:
        '''
        ARGS = ['instanceId', 'instanceName']
        for arg in ARGS:
            temp = locals().get(arg, False)
            if temp:
                kwargs[arg] = temp
        api = 'api/networks/nat'
        method = 'get'
        action = 'DescribeNat'
        data = {}
        res = self.send_request(api, method, data, Action=action, regionId=self.region_dict[self.target_region_name],
                                t=timeStap(), page=page,
                                size=size, **kwargs)
        return res

    def NAT_describe_all(self, **kwargs) -> (list, list, list):
        page, size = 1, 100
        res = self.NAT_describe(page=page, size=size, **kwargs)
        total = int(jsonpath.jsonpath(res, '$.res.total')[0])
        pages = total // size if total % size == 0 else total // size + 1
        datas = jsonpath.jsonpath(res, '$.res.data')[0]
        nat_instances = []
        eip_lists = []
        vpc_list = []
        while page < pages:
            page += 1
            data = jsonpath.jsonpath(self.NAT_describe(page=page, size=size), '$.res.data')[0]
            if data:
                datas.extend(data)
        for ele in datas:
            nat_instances.append(ele['instanceId'])
            eip_lists.append(ele['eipList'])
            vpc_list.append(ele['vpcId'])
        return nat_instances, eip_lists, vpc_list

    def NAT_update_name(self, instance_id, name):
        '''

        :param instance_id:
        :param name:
        :return:{"res":None,"msg":"修改NAT网关名称成功","code":"Network.Success"}
        '''
        api = 'api/networks/nat'
        action = 'UpdateNat'
        method = 'put'
        data = {}
        res = self.send_request(api, method, data, Action=action, natId=instance_id, name=name, regionId=self.location,
                                t=timeStap())
        return res

    def NAT_bind_eips(self, instance_id, eips: list, **kwargs):
        '''
        :param instance_id: string
        :param eips: list
        :return:{"res":None,"msg":"NAT网关绑定弹性公网IP成功","code":"Network.Success"}
        '''
        api = 'api/networks/nat'
        method = 'put'
        action = 'BindEipToNat'
        body = eips
        res = self.send_request(api, method, body, Action=action, natId=instance_id,
                                regionId=self.region_dict[self.target_region_name],
                                t=timeStap(), **kwargs)
        return res

    def NAT_unbind_eips(self, nat_id, eips: list, **kwargs):
        """
        :param nat_id:
        :param eips:
        :param kwargs:
        :return: {"res":null,"msg":"NAT网关解绑弹性公网IP成功","code":"Network.Success"}
        """
        api = 'api/networks/nat'
        action = 'UnbindEipFromNat'
        method = 'put'
        data = eips
        res = self.send_request(api, method, data, Action=action, natId=nat_id,
                                regionId=self.region_dict[self.target_region_name], t=timeStap(),
                                **kwargs)
        return res

    def NAT_describe_bind_eip(self, nat_id, **kwargs):
        '''
        :param nat_id:
        :return:{"res":[{"instanceId":"eip-bsjiy1qg2je1","instanceName":"nrgNatTest-5","instanceCode":"eip.bgp.static","ipAddress":"150.66.0.136","bandwidth":"1"}],
        "msg":"查询NAT已绑定的弹性公网IP列表成功","code":"Network.Success"}
        '''
        api = 'api/networks/nat'
        action = 'DescribeBindEipForNat'
        method = 'get'
        data = {}
        res = self.send_request(api, method, data, Action=action, natId=nat_id,
                                regionId=self.region_dict[self.target_region_name], t=timeStap(),
                                **kwargs)
        return res

    def NAT_stop(self):
        pass

    def NAT_start(self):
        pass

    def SNAT_create(self, nat_id, subnet_ids: list, eip_id, vpc_id, **kwargs):
        '''
        :param nat_id:
        :param subnet_ids:
        :param eip_id:
        :param vpc_id:
        :param kwargs:
        :return:{"res":{"snatId":"snat-bsjiyd13pw3w","natId":"nat-bsjiyd13pwu0","vpcId":"vpc-bsjixihlwojd","userId":"9d367b04-a5b9-4223-b69f-c961b568549f","eipId":"eip-bsjiyd13pwgn","eipAddr":"150.66.0.122","status":"UNAVAILABLE","subnets":[{"subnetId":None,"cidr":"192.168.35.0/24"}]},
        "msg":"创建snat成功","code":"Network.Success"}
        '''
        api = 'api/networks/nat'
        action = 'CreateSnat'
        method = 'post'
        data = {"eipId": eip_id, "subnetIds": subnet_ids, "vpcId": vpc_id}
        res = self.send_request(api, method, data, Action=action, natId=nat_id,
                                regionId=self.region_dict[self.target_region_name], t=timeStap(),
                                **kwargs)
        return res

    def SNAT_delete(self, snat_id, **kwargs):
        '''
        :param snat_id:
        :param kwargs:
        :return: {"res":True,"msg":"删除snat成功","code":"Network.Success"}
        '''
        api = 'api/networks/nat'
        method = 'POST'
        action = 'DeleteSnat'
        data = {}
        res = self.send_request(api, method, data, Action=action, snatIds=snat_id,
                                regionId=self.region_dict[self.target_region_name],
                                t=timeStap(), **kwargs)
        return res

    def SNAT_update(self, snat_id, vpc_id, add_subnet_ids=[], remove_subnet_ids=[], **kwargs):
        '''
        :param snat_id:
        :param vpc_id:
        :param add_subnet_ids: list
        :param remove_subnet_ids: list
        :return:{"res":None,"msg":"修改snat成功","code":"Network.Success"}
        '''
        api = 'api/networks/nat'
        action = 'UpdateSnat'
        method = 'put'
        data = {"addSubnetIds": add_subnet_ids, "removeSubnetIds": remove_subnet_ids, "snatId": snat_id,
                "vpcId": vpc_id}
        res = self.send_request(api, method, data, Action=action, regionId=self.region_dict[self.target_region_name],
                                t=timeStap(), **kwargs)
        return res

    def SNAT_describe(self, natId, page=1, size=10, **kwargs) -> (list, list, list):
        """
        :param natId:
        :param page:
        :param size:
        :param kwargs:
        :return: {"res":{"page":1,"size":10,"total":2,"data":[{"snatId":"snat-ecb1vaxhto86","natId":"nat-ecb1vylu6lhq","vpcId":"vpc-erp6qlkzwf9m","userId":"e9e4ef62-47df-4349-bee8-a64254f146b4","eipId":"eip-erp6qlkzwf7w","eipAddr":"172.25.131.203","status":"RUNNING","subnets":[{"subnetId":"vsnet-erp6qlkzwf9n","cidr":"192.168.0.0/24"}]},{"snatId":"snat-ecb1vylu6llu","natId":"nat-ecb1vylu6lhq","vpcId":"vpc-erp6qlkzwf9m","userId":"e9e4ef62-47df-4349-bee8-a64254f146b4","eipId":"eip-erp6qdovf6d9","eipAddr":"172.25.129.49","status":"RUNNING","subnets":[{"subnetId":"vsnet-ecb1vylu6llt","cidr":"192.168.9.0/24"}]}]},"msg":"条件查询snat成功","code":"Network.Success"}
        """
        api = 'api/networks/nat'
        action = 'DescribeSnats'
        method = 'get'
        data = {}
        res = self.send_request(api, method, data, Action=action, page=page, size=size,
                                regionId=self.region_dict[self.target_region_name],
                                natId=natId, t=timeStap(),
                                **kwargs)
        return res

    def SNAT_query_condition(self):
        pass

    def SNAT_describe_available_subnet(self, nat_id, **kwargs):
        '''
        :param nat_id:
        :return:{"res":[{"subnetId":"005131048b5949099ea6a102525231d6","cidr":"192.168.200.0/24"}]
        'msg': "查询该snat可以添加的子网Id成功",'code': "Network.Success"}
        '''
        api = 'api/networks/nat'
        method = 'get'
        action = 'DescribeAvailableSubnetForSnat'
        data = {}
        res = self.send_request(api, method, data, Action=action, natId=nat_id,
                                regionId=self.region_dict[self.target_region_name],
                                azoneId=self.azone_id, t=timeStap(), **kwargs)
        return res

    def DNAT_create(self, nat_id, eip_id, eip_port, fix_port_id, fix_port_num, protpcal='tcp', **kwargs):
        '''
        :param eip_id:
        :param eip_port: int 公网端口
        :param fix_port_id: str device 网卡 id
        :param fix_port:int 私网端口
        :param protpcal: tcp|udp
        :return:{"res":{"userId":"9d367b04-a5b9-4223-b69f-c961b568549f","dnatId":"dnat-bsjiy1qg2f4u","natId":"nat-bsjiyd13pwu0","eipId":"eip-bsjiyd13pwgm","eipAddr":"150.66.0.120","eipPortNum":2,"fixedPortId":"eni-bsjixqdqcskf","ownerEcsId":"ecs-bsjixqdqcskd","fixedIpAddr":"192.168.144.2","fixedPortNum":2,"protocal":None,"status":"UNAVAILABLE"},"
        msg":"创建dnat成功","code":"Network.Success"}
        '''
        api = 'api/networks/nat'
        action = 'CreateDnat'
        method = 'post'
        data = {"eipId": eip_id, "eipPortNum": str(eip_port), "fixedPortNum": str(fix_port_num),
                "fixedPortId": fix_port_id,
                "protocal": protpcal}
        res = self.send_request(api, method, data, Action=action, natId=nat_id,
                                regionId=self.region_dict[self.target_region_name], t=timeStap(),
                                **kwargs)
        return res

    def DNAT_delete(self, dnat_ids, **kwargs):
        '''
        :param dnat_ids:
        :param kwargs:
        :return: {"res":True,"msg":"删除dnat成功","code":"Network.Success"}
        '''
        api = 'api/networks/nat'
        method = 'delete'
        action = 'DeleteDnat'
        data = {}
        res = self.send_request(api, method, data, Action=action, dnatIds=dnat_ids,
                                regionId=self.region_dict[self.target_region_name],
                                t=timeStap(), **kwargs)
        return res

    def DNAT_update(self, dnatId, eipPortNum, fixedPortNum, **kwargs):
        """
        :param dnatId:
        :param eipPortNum:
        :param fixedPortNum:
        :return:{"res":null,"msg":"修改dnat成功","code":"Network.Success"}
        """
        api = 'api/networks/nat'
        method = 'PUT'
        action = 'UpdateDnat'
        data = {"dnatId": dnatId, "eipPortNum": eipPortNum, "fixedPortNum": fixedPortNum}
        res = self.send_request(api, method, data, Action=action, regionId=self.region_dict[self.target_region_name],
                                t=timeStap(), **kwargs)
        return res

    def DNAT_describe(self, natId, page=1, size=10, **kwargs):
        """

        :param natId:
        :param page:
        :param size:
        :param kwargs:
        :return:res:
                    page: 1
                    size: 10
                    total: 1
                    data:{
                        userId: "1e629fd2-78d2-4c9a-a82b-612a25cccb75"
                        dnatId: "dnat-ecb1vaxhtloc"
                        natId: "nat-ecb1u21ddga6"
                        eipId: "eip-ecb1u21ddgjt"
                        eipAddr: "172.25.129.15"
                        eipPortNum: 123
                        fixedPortId: "eni-ecb1u21ddg9p"
                        ownerEcsId: "ecs-ecb1u21ddg9m"
                        fixedIpAddr: "192.168.0.32"
                        fixedPortNum: 31
                        protocal: "tcp"
                        status: "UNAVAILABLE"
                    msg: "条件查询dnat成功"
                    code: "Network.Success"
        """
        api = 'api/networks/nat'
        method = 'get'
        action = 'DescribeDnats'
        data = {}
        res = self.send_request(api, method, data, Action=action, natId=natId,
                                regionId=self.region_dict[self.target_region_name],
                                t=timeStap(), **kwargs)
        return res


def check_dnat(nat, dnatId, self):
    # 检查nat下是否有dnat
    res = self.DNAT_describe(nat)
    dnat = jsonpath.jsonpath(res, '$.res.data..dnatId')
    assert dnat and dnatId in dnat, '未创建nat {} dnat {}'.format(nat, dnatId)
    status = jsonpath.jsonpath(res, '$.res.data..status')
    flag = True

    for _dnat, _status in zip(dnat, status):
        if _dnat == dnatId:
            flag = False
            assert _status == 'RUNNING', "dnat {} 状态为 {}".format(_dnat, _status)
            break
    if flag:
        raise KeyError('未在nat {} 找到 dnat {}'.format(nat, dnatId))


def check_snat(nat, snat, self):
    # 检查nat下是否有snat
    res = self.SNAT_describe(nat)
    code = jsonpath.jsonpath(res, '$.code')
    assert code and code[0] == "Network.Success", '查询snat失败'
    data = jsonpath.jsonpath(res, '$.res.data')[0]
    for ele in data:
        if ele['snatId'] == snat:
            assert ele['status'] == 'RUNNING', '检查snat {} 状态失败'.format(snat)
            break
    assert False, 'nat {} 下不存在snat {}'.format(nat, snat)


def check_nat(nat, self):
    # 检查是否存在nat，状态为running
    res = self.NAT_describe(nat)
    assert check_res_code(res), '查询nat {}状态失败'.format(nat)
    try:
        temp = jsonpath.jsonpath(res, '$.res.data..status')[0]
    except TypeError:
        raise AssertionError('未查询到nat {}'.format(nat))
    assert temp == 'RUNNING', '检查nat {}状态失败{}'.format(nat, temp)
