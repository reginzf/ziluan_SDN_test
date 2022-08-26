import time

from source.locust_methods import Agent_SDN_nolocust, timeStap, func_instanceName


class SEC(Agent_SDN_nolocust):
    def delete_securitygroup(self):
        for group in self.get_securitygroups():
            self._delete_securitygroup(group)

    def _delete_securitygroup(self, group):
        api = 'api/networks/securitygroup'
        method = 'delete'
        data = {}
        action = 'DeleteSecurityGroup'
        res = self.send_request(api, method, data, action=action, reginId=group["reginId"], sgId=group["instanceId"],
                                t=timeStap())
        return res

    def get_securitygroups(self, **kwargs):
        '''可选项:
        name: [string]
        description: [string]
        '''
        api = 'api/networks/securitygroup'
        method = 'GET'
        param = {"Action": "DescribeSecurityGroup", "regionId": self.region[0], "t": timeStap(), "size": 10}
        page = 1
        res = []
        s_time = time.time()
        while time.time() - s_time < (5 * 60):
            param["page"] = page
            temp = self.send_request(api, method, **param)
            total = int(temp["res"]["total"])
            temp = temp["res"]["data"]
            res.extend(temp)
            page += 1
            if len(res) >= total:
                break
        return res

    def create_get_securitygroup(self, **kwargs):
        api = 'api/networks/securitygroup'
        method = 'post'
        data = {"description": "", "instanceCode": "SecurityGroup.normal", "name": func_instanceName(15), "rules": [
            {"direction": "egress", "etherType": "IPv4", "isDeny": 0, "portRangeMin": None, "portRangeMax": None,
             "priority": 100, "protocol": "", "remoteIpPrefix": "0.0.0.0/0"}]}
        action = 'CreateSecurityGroup'
        res = self.send_request(api, method, data, Action=action, regionId="CD-Test", t=timeStap())
        return res

    def SEC_CreateSecurityGroup(self, project_id=None, name="test_auto", desc="auto_test", rules=[]):
        '''
        创建安全组,rule规则示例如下
        {
            "direction": "egress",
            "etherType": "IPv4",
            "isDeny": 0,
            "portRangeMin": None,
            "portRangeMax": None,
            "priority": 100,
            "protocol": "",
            "remoteIpPrefix": "0.0.0.0/0"
        }
        '''
        api = 'api/networks/securitygroup'
        method = 'POST'
        params = {"Action": "CreateSecurityGroup", "regionId": self.region[0], "t": timeStap()}
        if project_id is None:
            project_id = self.SEC_get_available_project_id()
        data = {
            "projectId": project_id,
            "description": desc,
            "instanceCode": "SecurityGroup.normal",
            "name": name,
            "rules": [

            ]
        }
        ret = self.send_request(api=api, method=method, data=data, **params)
        if ret["code"] != "Network.Success":
            raise "安全组创建失败"
        sg_id = ret["res"]["sgId"]
        return sg_id

    def SEC_get_available_project_id(self):
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

    def SEC_DescribeSecurityGroup(self, id=None, name=None):
        '''
        拉取安全组列表,过滤安全组
        '''
        api = 'api/networks/securitygroup'
        method = "GET"
        params = {"Action": "DescribeSecurityGroup", "regionId": self.region[0], "t": timeStap(), "size": 10}
        page = 1
        if name is not None:
            params["name"] = name
        if id is not None:
            params["sgId"] = id
        s_time = time.time()
        sgs = []
        while time.time() - s_time < (5 * 60):
            params["page"] = page
            ret = self.send_request(api=api, method=method, **params)
            if ret["code"] != "Network.Success":
                raise "获取安全组列表失败"
            sgs.extend(ret["res"]["data"])
            total = int(ret["res"]["total"])
            if len(sgs) >= total:
                break
            page += 1
        return sgs

    def SEC_UpdateSecurityGroup(self, id, new_name, new_desc):
        '''
        修改安全组名称
        '''
        api = 'api/networks/securitygroup'
        method = "PUT"
        params = {"Action": "UpdateSecurityGroup", "regionId": self.region[0], "t": timeStap()}
        data = {
            "sgId": id,
            "name": new_name,
            "description": new_desc
        }
        ret = self.send_request(api=api, method=method, data=data, **params)
        if ret["code"] != "Network.Success":
            raise "安全组创建失败"
        return ret

    def SEC_CreateSecurityGroupRule(self, sg_id):
        '''
        增加安全组规则
        '''
        api = 'api/networks/securitygroup'
        method = "POST"
        params = {"Action": "CreateSecurityGroupRule", "regionId": self.region[0], "t": timeStap(), "sgId": sg_id}
        data = [
            {
                "direction": "ingress",
                "etherType": "ipv4",
                "remoteIpPrefix": "0.0.0.0/0",
                "securityGroupId": sg_id,
                "priority": "100",
                "isDeny": "0"
            }
        ]
        ret = self.send_request(api=api, method=method, data=data, **params)
        if ret["code"] != "Network.Success":
            raise "安全组规则创建失败"
        rule_id = ret["res"]["ID"]
        return rule_id

    def SEC_DescribeSecurityGroupRuleList(self, sg_id, direction="ingress"):
        '''
        获取安全组规则
        direction:ingress/egress
        '''
        api = 'api/networks/securitygroup'
        method = "GET"
        params = {"Action": "DescribeSecurityGroupRuleList", "regionId": self.region[0], "t": timeStap(), "sgId": sg_id,
                  "direction": direction, "size": 10}
        page = 1
        rules = []
        s_time = time.time()
        while time.time() - s_time < (5 * 60):
            params["page"] = page
            ret = self.send_request(api=api, method=method, **params)
            if ret["code"] != "Network.Success":
                raise "安全组规则获取失败"
            rules.extend(ret["res"]["sgRules"])
            total = int(ret["res"]["totalCount"])
            if len(rules) >= total:
                break
            page += 1
        return rules

    def SEC_UpdateSecurityGroupRule(self, sg_id, rule_id, priority):
        '''
        修改安全组规则优先级
        '''
        api = 'api/networks/securitygroup'
        method = "PUT"
        params = {"Action": "UpdateSecurityGroupRule", "regionId": self.region[0], "t": timeStap()}
        if not isinstance(priority, str):
            priority = str(priority)
        data = {
            "id": rule_id,
            "direction": "ingress",
            "remoteIpPrefix": "0.0.0.0/0",
            "etherType": "ipv4",
            "priority": priority,
            "isDeny": "0",
            "securityGroupId": sg_id
        }
        ret = self.send_request(api=api, method=method, data=data, **params)
        if ret["code"] != "Network.Success":
            raise "安全组规则修改失败"
        return ret

    def SEC_DeleteSecurityGroupRule(self, sg_id, sg_rule_id):
        '''
        删除安全组规则
        '''
        api = 'api/networks/securitygroup'
        method = "PUT"
        params = {"Action": "DeleteSecurityGroupRule", "regionId": self.region[0], "t": timeStap(), "sgId": sg_id}
        if not isinstance(sg_rule_id, list):
            sg_rule_id = [sg_rule_id]
        data = sg_rule_id
        ret = self.send_request(api=api, method=method, data=data, **params)
        if ret["code"] != "Network.Success":
            raise "安全组规则删除失败"
        return ret

    def SEC_DeleteSecurityGroup(self, sg_id):
        '''
        删除安全组
        '''
        api = 'api/networks/securitygroup'
        method = "DELETE"
        params = {"Action": "DeleteSecurityGroup", "regionId": self.region[0], "t": timeStap(), "sgId": sg_id}
        ret = self.send_request(api=api, method=method, **params)
        if ret["code"] != "Network.Success":
            raise "安全组删除失败"
        return ret

    def SEC_BindSecurityGroupBatch(self, sg_id, ecs_id, eni_id):
        '''
        将安全组绑定到ECS
        '''
        api = 'api/networks/securitygroup'
        method = "PUT"
        params = {"Action": "BindSecurityGroupBatch", "regionId": self.region[0], "t": timeStap(), "sgId": sg_id,
                  "instanceType": "ECS"}
        data = [
            {
                "instanceId": ecs_id,
                "portId": eni_id
            }
        ]
        ret = self.send_request(api=api, method=method, data=data, **params)
        if ret["code"] != "Network.Success":
            raise "安全组规则修改失败"
        return ret

    def SEC_AvbForSg(self, sg_id, name=None):
        '''
        获取sg可绑定的ECS列表
        '''
        api = 'api/iam/ecs/instances'
        method = "GET"
        params = {"Action": "AvbForSg", "regionId": self.region[0], "t": timeStap(), "sgId": sg_id, "size": 10}
        if name is not None:
            params["name"] = name
        page = 1
        ecses = []
        s_time = time.time()
        while time.time() - s_time < (5 * 60):
            params["page"] = page
            ret = self.send_request(api=api, method=method, **params)
            if ret["code"] != "0":
                raise "获取可用的ECS失败失败"
            ecses.extend(ret["res"]["list"])
            total = int(ret["res"]["totalCount"])
            if len(ecses) >= total:
                break
            page += 1
        return ecses

    def SEC_DescribeEcsBySgId(self, sg_id, ecs_id=None):
        '''
        查看安全组绑定到额ecs
        '''
        api = 'api/iam/ecs/instances'
        method = "GET"
        params = {"Action": "DescribeEcsBySgId", "regionId": self.region[0], "t": timeStap(), "sgId": sg_id, "size": 10}
        if ecs_id is not None:
            params["instanceId"] = ecs_id
        page = 1
        ecses = []
        s_time = time.time()
        while time.time() - s_time < (5 * 60):
            params["page"] = page
            ret = self.send_request(api=api, method=method, **params)
            if ret["code"] != "0":
                raise "安全组删除失败"
            ecses.extend(ret["res"]["list"])
            total = int(ret["res"]["totalCount"])
            if len(ecses) >= total:
                break
            page += 1
        return ecses

    def SEC_UnbindSecurityGroupBatch(self, sg_id, ecs_id, eni_id):
        '''
        安全组解绑ECS
        '''
        api = 'api/networks/securitygroup'
        method = "PUT"
        params = {"Action": "UnbindSecurityGroupBatch", "regionId": self.region[0], "t": timeStap(), "sgId": sg_id,
                  "instanceType": "ECS"}
        data = [
            {
                "instanceId": ecs_id,
                "portId": eni_id
            }
        ]
        ret = self.send_request(api=api, method=method, data=data, **params)
        if ret["code"] != "Network.Success":
            raise "安全组规则修改失败"
        return ret
