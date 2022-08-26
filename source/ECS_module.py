# -*- coding: UTF-8 -*-
import time

from jsonpath import jsonpath

from source.locust_methods import Agent_SDN_nolocust, timeStap, check_res_code


class ECS(Agent_SDN_nolocust):
    def ECS_avb_for_eip(self, **kwargs):
        '''
        查询未绑定eip的ecs
        :return:{"status":true,"code":0,"auth":true,"res":[{"id":"ecs-b16j3eg85u3r","name":"zcvm300","ip":"172.1.1.27","ipv6Addr":"","eniId":"eni-b16j3eg85u3t","eniName":"gFnECcnLGubgW","vpcId":"vpc-bsji6h2odp0i","vpcName":"zcvpc001","subnetId":"cc36a7e869a6482fbd4711fc3efa5a16"}],
        "msg":null}
        '''
        api = 'api/iam/ecs/instances'
        action = 'AvbForEip'
        method = 'get'
        data = {}
        res = self.send_request(api, method, data, Action=action, regionId=self.region_dict[self.target_region_name],
                                azoneId=self.azone_id,
                                t=timeStap(), **kwargs)
        return res

    def ECS_eni_avb_for_eip(self, **kwargs):
        '''
        查询未绑定eip的eni
        :param kwargs:
        :return: {"status":true,"code":0,"auth":true,"res":[{"id":39,"regionId":"H3C-HZ","azoneId":"H3C-HZ-AZ1","userId":"9d367b04-a5b9-4223-b69f-c961b568549f","accountId":null,"instanceId":"eni-bsjisgyrju92","instanceName":"xAjzt1a8azXeA","instanceCode":"ENI.elasticity","vmId":null,"ipv4Addr":"192.168.128.4","macAddr":"fa:16:3e:2a:04:8b","subnetId":"0d884a5a7cc7468a890c0effcd476634","status":"RUNNING","type":"secondary","description":null,"createTime":1624260813000,"updateTime":null,"name":"xAjzt1a8azXeA"}],
        "msg":null}
        '''
        api = 'api/iam/ecs/networkInterfaces/avbForEip'
        method = 'get'
        data = {}
        res = self.send_request(api, method, data, regionId=self.region_dict[self.target_region_name],
                                azoneId=self.azone_id, t=timeStap(),
                                **kwargs)
        # instance_id = res['res'][0]['instanceId']
        return res

    def ECS_create_eni(self, eni_name, vpcId, subnetId, sgId, azoneId='', releaseType=1, ipAddress='', **kwargs):
        """
        创建弹性网卡
        :param eni_name:
        :param vpcId:
        :param subnetId:
        :param azoneId:
        :param sgId:
        :param releaseType:
        :param ipAddress:
        :param kwargs:
        :return:$.[auth,code,msg,status,res.[instanceId,instanceName,ipv4Addr,macAddr,status]]
        """
        api = 'api/iam/ecs/networkInterfaces'
        method = 'post'
        azoneId = self.azone_id if azoneId == '' else azoneId
        data = {"regionId": self.region[0], "name": eni_name, "vpcId": vpcId,
                "subnetId": subnetId, "azoneId": azoneId, "sgId": sgId,
                "releaseType": releaseType, "ipAddress": ipAddress}
        res = self.send_request(api, method, data, **kwargs)
        return res

    def ECS_AvbByVpcAndSubnetIds(self, vpc_id, **kwargs):
        """
        获取vpc下所有ecs、eni信息
        :param vpc_id:
        :return:{"status":true,"code":"0","auth":true,"res":[{"instanceId":"ecs-ecb1u21ddha4","instanceName":"lntest2","eniId":"eni-ecb1u21ddha6"},
        """
        api = 'api/iam/ecs/instances'
        action = 'AvbByVpcAndSubnetIds'
        method = 'get'
        data = {}
        res = self.send_request(api, method, data, Action=action, regionId=self.region_dict[self.target_region_name],
                                vpcId=vpc_id,
                                t=timeStap(), azoneId=self.azone_id, **kwargs)

        ecs = jsonpath(res, '$.res..instanceId')
        ecs_name = jsonpath(res, '$.res..instanceName')
        eni = jsonpath(res, '$.res..eniId')
        return zip(ecs, ecs_name, eni)

    def ECS_networkInterfaces(self, instanceId=None, instanceName=None, ipv4Addr='', ipv6Addr='', page=1, size=10,
                              *args, **kwargs):
        """
        # 查询eni信息
        instanceId,instanceName,ipv4Addr,ipv6Addr
        :param page:
        :param size:
        :param args:
        :param kwargs:
        :return:
        """

        ARGS = ['instanceId', 'instanceName', 'ipv4Addr', 'ipv6Addr']
        for arg in ARGS:
            temp = locals().get(arg, None)
            if temp:
                kwargs[arg] = temp
        api = 'api/iam/ecs/networkInterfaces'
        method = 'get'
        data = {}
        return self.send_request(api=api, method=method, data=data, regionId=self.region_dict[self.target_region_name],
                                 **kwargs)

    def ECS_ipAddress(self, eniId, ip, releaseType=1, **kwargs):
        """
        :param eniId:
        :param ip:
        :param releaseType: 1 勾选随实例释放
        :return:{"status":true,"code":"0","auth":true,"res":null,"msg":null}
        """
        api = 'api/iam/ecs/networkInterfaces/ipAddress'
        method = 'POST'
        data = {"eniId": eniId, "ip": ip, "releaseType": releaseType}
        return self.send_request(api, method, data, **kwargs)

    def ECS_RunEcs(self, vpc_id=None, subnet_id=None, sg_id=None, name="test", hostname="test",
                   password="admin123", project_id=None):
        '''
        创建包月ECS
        '''
        if isinstance(self.region, list):
            region = self.region[0]
        else:
            region = self.region
        # self.region = "cd-unicloud-region"
        # self.azone_id = "cd-unicloud-region-az1"

        if project_id is None:
            project_id = self.ECS_get_available_project_id()
        if sg_id is None:
            from source import SEC
            ret = SEC.get_securitygroups(self)
            assert len(ret) > 0, "没有安全组"
            sg_id = ret[0]["instanceId"]
        print("get sg is :", sg_id)
        api = "/api/iam/ecs/instances"
        params = {"Action": "RunEcs"}
        method = "POST"
        data = {
            "productDescription": "",
            "payType": "DAY_MONTH",
            "chargeType": "postpaid",
            "regionId": region,
            "azoneId": self.azone_id,
            "productRentCount": 1,
            "productRentUnit": "month",
            "userId": "",
            "accountId": "",
            "instanceCode": "c1.medium.2",
            "sysDisk": {
                "instanceCode": "ebs.ones_hybrid.hdd",
                "diskSize": 40
            },
            "imageType": "linux",
            "imageId": "CentOS_7_9_64bit_Minimal_std",
            "imageCode": "CentOS_7_9_64bit_Minimal_std",
            "imageParentCode": "ecs.image.public",
            "dataDisks": [],
            "vpcId": vpc_id,
            "eip": None,
            "securityGroup": {
                "rules": [],
                "securityGroupId": sg_id
            },
            "authType": "2",
            "password": password,
            "keypair": "",
            "instanceName": name,
            "hostName": hostname,
            "description": "",
            "affinityId": "",
            "projectId": project_id,
            "amount": 1,
            "initialShell": "",
            "trial": False,
            "networkInterfaces": [
                {
                    "subnetId": subnet_id,
                    "type": "master",
                    "releaseType": 1,
                    "ipv4Addr": "",
                    "startIP": ""
                }
            ],
            "tagIds": []
        }
        ret = self.send_request(api=api, method=method, data=data, **params)
        print(ret)
        order_id = ret["res"]["orderId"]
        self.ECS_approve_order(order_id=order_id)
        return order_id

    def ECS_approve_order(self, order_id):
        api = "/api/transaction-core/uco/v1/transaction/approveOrder"
        method = "GET"
        params = {"t": str(int(time.time() * 1000)), "orderId": order_id}
        data = {}
        self.send_request(api=api, method=method, data=data, **params)

    def ECS_get_available_project_id(self):
        api = "/api/moove/cps/projects"
        method = "GET"
        params = {"Action": "getUserProjectList", "regionId": self.region[0], "productCode": "VPC",
                  "t": str(int(time.time() * 1000))}
        data = {}
        ret = self.send_request(api=api, method=method, data=data, **params)
        project_list = ret["res"]
        for project in project_list:
            return project["resource_project_id"]
        return None

    def ECS_get_ecsid_by_ecs_name(self, name=None):
        api = "/api/iam/ecs/instances"
        method = "GET"
        params = {"Action": "DescribeEcs", "regionId": self.region[0], "instanceName": name}
        ret = self.send_request(api=api, method=method, **params)
        ecses = ret["res"]["list"]
        ecs_ids = []
        for ecs in ecses:
            ecs_id = ecs["instanceId"]
            ecs_ids.append(ecs_id)
        return ecs_ids

    def ECS_poweroff(self, ecs_ids):
        '''
        ECS关机
        '''
        if not isinstance(ecs_ids, list):
            ecs_ids = [ecs_ids]
        api = "/api/iam/ecs/instances"
        params = {"Action": "OperateEcsStatus", "operation": "stop"}
        data = {"instanceIds": ecs_ids}
        return self.send_request(api, "PUT", data, **params)

    def ECS_DeleteEcs(self, ecs_ids):
        '''
        删除ECS
        '''
        api = "/api/iam/ecs/instances"
        method = "DELETE"
        params = {"Action": "DeleteEcs"}
        if not isinstance(ecs_ids, list):
            ecs_ids = [ecs_ids]
        data = {"instanceIds": ecs_ids, "withEip": False, "withPostDisk": False, "verificationCode": ""}
        return self.send_request(api=api, method=method, data=data, **params)

    def ECS_DescribeEcs(self, instanceId='', instanceName='', privateAddr='', tagKey='', status='',
                        instanceSystem='', size=10, page=1, **kwargs):
        """
        :param instanceId:
        :param instanceName:
        :param privateAddr: 私网地址
        :param tagKey: 标签
        :param status: 运行状态 running...
        :param instanceSystem: 操作系统（镜像名称）
        :param kwargs:其他放入kwargs
        :return:"status": true,
  "code": "0",
  "auth": true,
  "res": {
        "page": 1,
        "size": 10,
        "totalCount": 1,
        "totalPages": 1,
        "list": [
          {
            "instanceId": "ecs-fj2itky1yq8s",
            "instanceName": "nrg-CCN_2_2-1",
            "sysDiskSize": 40,
            "sysDiskCode": "ebs.ones_hybrid.hdd",
            "sysDiskId": "sys-fj2itky1yq8t",
            "status": "RUNNING",
            "imageId": "img-fh5t2y4r5dfz",
            "imageType": "linux",
            "imageCode": "image.private.image.init",
            "imageParentCode": "ecs.image.private",
            "instanceSystem": "CentOS_7_9_64bit_Minimal_std",
            "productConf": null,
            "createTime": 1653381015000,
            "description": "",
            "ip": "172.16.2.3",
            "ipv6Addr": "",
            "eipId": null,
            "eipAddr": null,
            "eipSize": null,
            "eipName": null,
            "eipCode": null,
            "instanceCode": "c1.medium.2",
            "instanceCodeName": "计算型1核2GB",
            "payType": "DAY_MONTH",
            "startTime": 1653381055000,
            "endTime": null,
            "bindDiskCount": 0,
            "maxDisk": 15,
            "eniId": "eni-fj2itky1yq8u",
            "vpcId": "vpc-fj2itky1yq5q",
            "vpcCidr": "172.16.2.0/24",
            "subnetId": "vsnet-fj2itky1yq5r",
            "subnetCidr": "172.16.2.0/24",
            "regionId": "cd-unicloud-region",
            "regionName": "成都基地",
            "azoneId": "cd-unicloud-region-az1",
            "azoneName": "成都基地可用区1",
            "instanceLabel": 1,
            "gpuCount": 0,
            "gpuType": null,
            "secondaryEni": null,
            "iscsiDiskCount": 0,
            "maxIscsi": 1,
            "instanceCloseTime": null,
            "instanceReleaseTime": null,
            "affinityId": null,
            "tags": null,
            "kmsId": null,
            "instanceCpu": 1,
            "instanceMemory": 2
          }
        ]
      },
      "msg": null
    }
        """
        api = "/api/iam/ecs/instances"
        method = "GET"
        action = 'DescribeEcs'

        ecses = []
        ARGS = ["instanceId", "instanceName", "privateAddr", "tagKey", "status",
                "instanceSystem", "page", "size"]
        for arg in ARGS:
            temp = locals().get(arg, False)
            if temp:
                kwargs[arg] = temp
        s_time = time.time()
        while time.time() - s_time < 300:
            ret = self.send_request(api=api, method=method, Action=action,
                                    regionId=self.region_dict[self.target_region_name], **kwargs)
            ecses.extend(ret["res"]["list"])
            total_page = int(ret["res"]["totalPages"])
            if page >= total_page:
                break
            page += 1
            kwargs['page'] = page
        return ecses

    def ECS_AvbForVip(self, havip_id, subnet_id):
        '''
        过滤HAVIP可绑定的ECS
        '''
        api = "/api/iam/ecs/instances"
        method = "GET"
        ecses = []
        params = {"Action": "AvbForVip", "t": timeStap(), "regionId": self.region[0], "azoneId": self.azone_id,
                  "vipId": havip_id, "subnetId": subnet_id}
        ret = self.send_request(api=api, method=method, **params)
        ecses.extend(ret["res"])
        return ecses

    def ECS_DescribeEcs_nrg(self, instanceId='', instanceName='', privateAddr='', tagKey='', status='',
                            instanceSystem='', size=10, page=1, **kwargs):
        """
        :param instanceId:
        :param instanceName:
        :param privateAddr: 私网地址
        :param tagKey: 标签
        :param status: 运行状态 running...
        :param instanceSystem: 操作系统（镜像名称）
        :param kwargs:其他放入kwargs
        :return:"status": true,
  "code": "0",
  "auth": true,
  "res": {
        "page": 1,
        "size": 10,
        "totalCount": 1,
        "totalPages": 1,
        "list": [
          {
            "instanceId": "ecs-fj2itky1yq8s",
            "instanceName": "nrg-CCN_2_2-1",
            "sysDiskSize": 40,
            "sysDiskCode": "ebs.ones_hybrid.hdd",
            "sysDiskId": "sys-fj2itky1yq8t",
            "status": "RUNNING",
            "imageId": "img-fh5t2y4r5dfz",
            "imageType": "linux",
            "imageCode": "image.private.image.init",
            "imageParentCode": "ecs.image.private",
            "instanceSystem": "CentOS_7_9_64bit_Minimal_std",
            "productConf": null,
            "createTime": 1653381015000,
            "description": "",
            "ip": "172.16.2.3",
            "ipv6Addr": "",
            "eipId": null,
            "eipAddr": null,
            "eipSize": null,
            "eipName": null,
            "eipCode": null,
            "instanceCode": "c1.medium.2",
            "instanceCodeName": "计算型1核2GB",
            "payType": "DAY_MONTH",
            "startTime": 1653381055000,
            "endTime": null,
            "bindDiskCount": 0,
            "maxDisk": 15,
            "eniId": "eni-fj2itky1yq8u",
            "vpcId": "vpc-fj2itky1yq5q",
            "vpcCidr": "172.16.2.0/24",
            "subnetId": "vsnet-fj2itky1yq5r",
            "subnetCidr": "172.16.2.0/24",
            "regionId": "cd-unicloud-region",
            "regionName": "成都基地",
            "azoneId": "cd-unicloud-region-az1",
            "azoneName": "成都基地可用区1",
            "instanceLabel": 1,
            "gpuCount": 0,
            "gpuType": null,
            "secondaryEni": null,
            "iscsiDiskCount": 0,
            "maxIscsi": 1,
            "instanceCloseTime": null,
            "instanceReleaseTime": null,
            "affinityId": null,
            "tags": null,
            "kmsId": null,
            "instanceCpu": 1,
            "instanceMemory": 2
          }
        ]
      },
      "msg": null
    }
        """
        api = "/api/iam/ecs/instances"
        method = "GET"
        action = 'DescribeEcs'

        ARGS = ["instanceId", "instanceName", "privateAddr", "tagKey", "status",
                "instanceSystem", "page", "size"]
        for arg in ARGS:
            temp = locals().get(arg, False)
            if temp:
                kwargs[arg] = temp
        ret = self.send_request(api=api, method=method, Action=action,
                                regionId=self.region_dict[self.target_region_name], **kwargs)
        return ret

    def ECS_DescribeEcs_all(self, **kwargs) -> list:
        """
        返回所有符合条件的ecs
        :param kwargs:
        :return:
        """
        ecses = []

        page = 1
        s_time = time.time()
        while time.time() - s_time < 300:
            ret = self.ECS_DescribeEcs_nrg(page=page, **kwargs)
            ecses.extend(ret["res"]["list"])
            total_page = int(ret["res"]["totalPages"])
            if page >= total_page:
                break
            page += 1
        return ecses

    def ECS_Stream_nrg(self, ecses: list, taskId='', taskname='', serverPort='5000', streamType='udp', speed='500',
                       vport='5000', sleep_time=0):
        """
        传入2个绑定eip的ecs，然后相互打流
        返回成功或任务重复则继续，否则抛出异常
        :param ecses: [ecs_id]
        :param taskId:  注册名称，会分别注册 taskId + '1',taskId + '2'
        :param taskname: __class__.__name__  回调过来名称
        :param serverPort: 5000,5001
        :param streamType: udp
        :param speed: 500
        :param vport: 默认和serverPort一致
        :return:{stream_cfg1['taskId']: stream_cfg1, stream_cfg2['taskId']: stream_cfg2}
        """
        ecs_interface = {}
        for ecs in ecses:
            res = self.ECS_DescribeEcs_nrg(instanceId=ecs)
            assert check_res_code(res), '查询ecs接口返回失败'
            try:
                private_ip = jsonpath(res, '$.res.list..ip')[0]
                public_ip = jsonpath(res, '$.res.list..eipAddr')[0]
                ecs_interface[ecs] = [private_ip, public_ip]
            except TypeError as e:
                raise e('查询{}地址错误\n{}'.format(ecs, str(e)))

        interface_1 = ecs_interface[ecses[0]]
        interface_2 = ecs_interface[ecses[1]]

        stream_cfg1 = {"serverIp": interface_1[1],
                       "serverPort": serverPort,
                       "clientIp": interface_2[1],
                       "streamType": streamType,
                       "speed": speed,
                       "action": "start",
                       "vip": interface_1[0],
                       "vport": vport,
                       "taskId": taskId + '1',
                       "callback": "http://" + self.user.environment.web_ui_cfg[
                           'local_interface_address'] + "/stop_taskset/{}".format(taskname)}

        stream_cfg2 = {"serverIp": interface_2[1],
                       "serverPort": str(int(serverPort) + 1),
                       "clientIp": interface_1[1],
                       "streamType": streamType,
                       "speed": speed,
                       "action": "start",
                       "vip": interface_2[0],
                       "vport": str(int(vport) + 1),
                       "taskId": taskId + '2',
                       "callback": "http://" + self.user.environment.web_ui_cfg[
                           'local_interface_address'] + "/stop_taskset/{}".format(taskname)}

        res = self.user.start_stream(taskId + '1', stream_cfg1)
        assert res['code'] == '10202' or res['code'] == '200', '下发流量配置失败，配置：\n{}\n返回：{}'.format(stream_cfg1, res)
        self.logger.info(msg='流{} 下发成功,msg:{}'.format(stream_cfg1['taskId'], res['message']))

        res = self.user.start_stream(taskId + '2', stream_cfg2)
        assert res['code'] == '10202' or res['code'] == '200', '下发流量配置失败，配置：\n{}\n返回：{}'.format(stream_cfg2, res)
        self.logger.info(msg='流{} 下发成功,msg:{}'.format(stream_cfg2['taskId'], res['message']))
        if sleep_time:
            time.sleep(sleep_time)
            self.user.stop_stream(stream_cfg1['taskId'], stream_cfg1)
            self.user.stop_stream(stream_cfg2['taskId'], stream_cfg2)
        return {stream_cfg1['taskId']: stream_cfg1, stream_cfg2['taskId']: stream_cfg2}


if __name__ == "__main__":
    pass
    import logging, os

    logging.basicConfig(level=logging.DEBUG,
                        filename='logs\\{}.log'.format(os.path.basename(__file__).split('.py')[0]),
                        filemode='w',
                        format='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s')
    ECS.logger = logging.getLogger()
    ecs = ECS()
    order_id = ecs.ECS_create_order(vpc_id="vpc-e9ocxuzdo531", subnet_id="vsnet-e9ocxuzdo532",
                                    sg_id="sg-e9ocxuzdov7f")
    ret = ecs.ECS_approve_order(order_id=order_id)
    print(ret)
