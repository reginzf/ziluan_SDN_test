import time

from source.locust_methods import Agent_SDN_nolocust


class ENI(Agent_SDN_nolocust):
    def ENI_create(self, eni_name="auto_eni_name", vpc_id=None, sg_id=None, subnet_id=None, ip_address=""):
        '''
        返回eni信息,{
          "id": 16144,
          "regionId": "cd-unicloud-region",
          "azoneId": "cd-unicloud-region-az1",
          "userId": "e9e4ef62-47df-4349-bee8-a64254f146b4",
          "accountId": null,
          "instanceId": "eni-fj10vx2y38j0",
          "instanceName": "n0qZN2TtC2iMr",
          "instanceCode": "ENI.elasticity",
          "vmId": null,
          "ipv4Addr": "10.0.0.45",
          "ipv6Addr": null,
          "macAddr": "fa:16:3e:ad:03:58",
          "subnetId": "vsnet-fj2it8nfbe10",
          "status": "RUNNING",
          "type": "secondary",
          "description": null,
          "createTime": 1653533130041,
          "updateTime": null
        }
        '''
        api = 'api/iam/ecs/networkInterfaces'
        method = 'POST'
        data = {
            "regionId": self.region[0],
            "name": eni_name,
            "vpcId": vpc_id,
            "subnetId": subnet_id,
            "azoneId": self.azone_id,
            "sgId": sg_id,
            "releaseType": 1,
            "ipAddress": ip_address
        }
        ret = self.send_request(api=api, method=method, data=data)
        if ret["code"] != "0":
            raise "新建ENI失败"
        eni = ret["res"]
        return eni

    def ENI_DescribeEni(self, name=None, eni_id=None, ipv4_addr=None, ipv6_addr=None):
        '''
        返回列表[{eni1},{eni2}],里边为ENI信息,ENI信息见create
        '''
        api = 'api/iam/ecs/networkInterfaces'
        method = 'GET'
        params = {"regionId": self.region[0], "size": 10}
        if name is not None:
            params["name"] = name
        if eni_id is not None:
            params["instanceId"] = eni_id
        if ipv4_addr is not None:
            params["ip"] = ipv4_addr
        if ipv6_addr is not None:
            params["ipV6"] = ipv6_addr
        page = 1
        enies = []
        s_time = time.time()
        while time.time() - s_time < (5 * 60):
            params["page"] = page
            ret = self.send_request(api=api, method=method, **params)
            if ret["code"] != "0":
                raise "新建ENI失败"
            enies.extend(ret["res"]["list"])
            total = int(ret["res"]["totalCount"])
            if len(enies) >= total:
                break
            page += 1
        return enies

    def ENI_modify_name(self, eni_id, new_name):
        '''
        修改ENI名称,返回ENI信息,ENI信息格式如下:
        {
          "id": 16144,
          "regionId": "cd-unicloud-region",
          "azoneId": "cd-unicloud-region-az1",
          "userId": "e9e4ef62-47df-4349-bee8-a64254f146b4",
          "accountId": null,
          "instanceId": "eni-fj10vx2y38j0",
          "instanceName": "test",
          "instanceCode": "ENI.elasticity",
          "vmId": null,
          "ipv4Addr": "10.0.0.45",
          "ipv6Addr": "",
          "macAddr": "fa:16:3e:ad:03:58",
          "subnetId": "vsnet-fj2it8nfbe10",
          "status": "RUNNING",
          "type": "secondary",
          "description": null,
          "createTime": 1653533130000,
          "updateTime": 1653535041181
        }
        '''
        api = 'api/iam/ecs/networkInterfaces/%s/name' % eni_id
        method = 'PUT'
        params = {"name": new_name}
        ret = self.send_request(api=api, method=method, **params)
        if ret["code"] != "0":
            raise "修改ENI名字失败"
        return ret["res"]

    def ENI_check_ip_exist(self, eni_id, ip_need_check):
        '''
        检查IP地址是否可用
        '''
        api = 'api/iam/ecs/networkInterfaces/checkIp'
        method = 'GET'
        params = {"eniId": eni_id, "ip": ip_need_check}
        ret = self.send_request(api=api, method=method, **params)
        if ret["code"] != "0":
            raise "IP地址检查失败"
        return ret

    def ENI_modify_ip_addr(self, eni_id, new_ip_addr):
        '''
        修改ENI IP地址
        '''
        api = 'api/iam/ecs/networkInterfaces/ipAddress'
        method = "POST"
        data = {
            "eniId": eni_id,
            "ip": new_ip_addr,
            "releaseType": 1
        }
        ret = self.send_request(api=api, method=method, data=data)
        if ret["code"] != "0":
            raise "修改IP地址失败"
        return ret

    def ENI_AvbForEni(self, eni_id, ecs_name=None, ecs_id=None):
        '''
        获取ENI能绑定的ECS列表
        '''
        api = 'api/iam/ecs/instances'
        method = "POST"
        params = {"Action": "AvbForEni", "eniId": eni_id, "regionId": self.region[0], "size": 10}
        if ecs_id is not None:
            params["instanceId"] = ecs_id
        if ecs_name is not None:
            params["name"] = ecs_name
        page = 1
        s_time = time.time()
        ecses = []
        while time.time() - s_time < (5 * 60):
            params["page"] = page
            ret = self.send_request(api=api, method=method, **params)
            if ret["code"] != "0":
                raise "获取ENI可绑定的ECS失败"
            ecses.extend(ret["res"]["list"])
            total = int(ret["res"]["totalCount"])
            if len(ecses) >= total:
                break
            page += 1
        return ecses

    def ENI_BindECS(self, eni_id, ecs_id):
        '''
        ENI绑定ECS
        '''
        api = 'api/iam/ecs/networkInterfaces/attach'
        method = "POST"
        data = {
            "eniId": eni_id,
            "vmId": ecs_id
        }
        ret = self.send_request(api=api, method=method, data=data)
        if ret["code"] != "0":
            raise "ENI绑定ECS失败"
        return ret

    def ENI_UnbindEcs(self, eni_id):
        '''
        ENI解绑ECS
        '''
        api = 'api/iam/ecs/networkInterfaces/detach'
        method = "POST"
        data = {
            "eniId": eni_id,
        }
        ret = self.send_request(api=api, method=method, data=data)
        if ret["code"] != "0":
            raise "ENI解绑ECS失败"
        return ret

    def ENI_Delete(self, eni_id):
        '''
        删除ENI
        '''
        api = "api/iam/ecs/networkInterfaces/%s" % eni_id
        method = "DELETE"
        ret = self.send_request(api=api, method=method)
        if ret["code"] != "0":
            raise "ENI删除失败"
        return ret

    def ENI_BindSg(self, eni_id, sg_id):
        '''
        ENI绑定安全组
        '''
        api = "api/networks/securitygroup"
        method = "PUT"
        params = {"Action": "BindSecurityGroup", "regionId": self.region[0], "instanceId": eni_id,
                  "instanceType": "ENI", "portId": eni_id}
        if not isinstance(sg_id, list):
            sg_id = [sg_id]
        data = sg_id
        ret = self.send_request(api=api, method=method, data=data, **params)
        if ret["code"] != "Network.Success":
            raise "ENI绑定SG失败"
        return ret

    def ENI_UnbindSg(self, eni_id, sg_id):
        '''
        ENI解绑安全组
        '''
        api = "api/networks/securitygroup"
        method = "PUT"
        params = {"Action": "UnbindSecurityGroup", "regionId": self.region[0], "instanceId": eni_id,
                  "instanceType": "ENI", "portId": eni_id}
        if not isinstance(sg_id, list):
            sg_id = [sg_id]
        data = sg_id
        ret = self.send_request(api=api, method=method, data=data, **params)
        if ret["code"] != "Network.Success":
            raise "ENI绑定SG失败"
        return ret
