from source.locust_methods import Agent_SDN_nolocust, timeStap


class HAVIP(Agent_SDN_nolocust):
    def HAVIP_DescribeVip(self):
        """
        拉取HAVIP列表,返回列表
        """
        api = 'api/networks/vip'
        method = 'GET'
        params = {"Action": "DescribeVip", "regionId": self.region[0], "t": timeStap(), "size": 10}
        page = 1
        havip_list = []
        while True:
            params["page"] = page
            res = self.send_request(api, method, **params)
            havips = res["res"]["data"]
            havip_list.extend(havips)
            total_count = res["res"]["total"]
            page += 1
            if len(havip_list) >= total_count:
                break
        return havip_list

    def HAVIP_ModifyVip(self, vip_id, new_name):
        """
        修改HAVIP名称
        """
        api = 'api/networks/vip'
        method = 'PUT'
        params = {"Action": "DescribeVip", "vipId": vip_id, "name": new_name, "regionId": self.region[0],
                  "t": timeStap()}
        return self.send_request(api, method, **params)

    def HAVIP_AssociateEip(self, eip_id, havip_id):
        '''
        HAVIP绑定EIP
        '''
        api = 'api/networks/vip'
        method = 'PUT'
        params = {"Action": "AssociateEip", "regionId": self.region[0], "eipId": eip_id, "parentId": havip_id,
                  "portId": havip_id, "parentType": "VIP", "t": timeStap()}
        return self.send_request(api, method, **params)

    def HAVIP_UnassociateEip(self, eip_id, havip_id):
        '''
        HAVIP解绑EIP
        '''
        api = 'api/networks/vip'
        method = 'PUT'
        params = {"Action": "UnassociateEip", "regionId": self.region[0], "eipId": eip_id, "parentId": havip_id,
                  "t": timeStap()}
        return self.send_request(api, method, **params)

    def HAVIP_CreateVip(self, vpc_id, subnet_id, name="test"):
        '''
        创建HAVIP
        '''
        api = 'api/networks/vip'
        method = 'POST'
        params = {"Action": "CreateVip", "regionId": self.region[0], "t": timeStap()}
        data = {"azoneId": self.azone_id, "instanceName": name, "subnetId": subnet_id, "vpcId": vpc_id}
        return self.send_request(api=api, method=method, data=data, **params)

    def HAVIP_BindEcsToVip(self, havip_id, ecs_id, eni_id):
        '''
        绑定HAVIP到ECS
        '''
        api = 'api/networks/vip'
        method = 'PUT'
        params = {"Action": "BindEcsToVip", "regionId": self.region[0], "t": timeStap(), "vipId": havip_id}
        data = [{"ecsId": ecs_id, "portId": eni_id}]
        return self.send_request(api=api, method=method, data=data, **params)

    def HAVIP_UnbindEcsFromVip(self, havip_id, ecs_id, eni_id):
        '''
        解绑HAVIP和ECS
        '''
        api = 'api/networks/vip'
        method = 'PUT'
        params = {"Action": "UnbindEcsFromVip", "regionId": self.region[0], "t": timeStap(), "vipId": havip_id}
        data = [{"ecsId": ecs_id, "portId": eni_id}]
        return self.send_request(api=api, method=method, data=data, **params)

    def HAVIP_DeleteVip(self, havip_id):
        '''
        删除HAVIP
        '''
        api = 'api/networks/vip'
        method = 'DELETE'
        params = {"Action": "DeleteVip", "regionId": self.region[0], "t": timeStap(), "vipId": havip_id}
        return self.send_request(api=api, method=method, **params)
