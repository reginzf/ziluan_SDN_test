import time

from source.locust_methods import Agent_SDN_nolocust, timeStap


class HSLB(Agent_SDN_nolocust):
    def HSLB_DescribeDpvs(self, id=None, name=None, ipv4=None, ipv6=None):
        """
        高性能SLB
        """
        api = 'api/networks/hslb'
        method = 'GET'
        params = {"Action": "DescribeDpvs", "regionId": self.region[0], "t": timeStap(), "size": 10}
        if id is not None:
            params["instanceId"] = id
        if name is not None:
            params["instanceName"] = name
        if ipv4 is not None:
            params["address"] = ipv4
        if ipv6 is not None:
            params["ipv6Address"] = ipv6
        page = 1
        hslb = []
        s_time = time.time()
        while time.time() - s_time < (5 * 60):
            params["page"] = page
            ret = self.send_request(api=api, method=method, **params)
            if ret["code"] != "Network.Success":
                raise "启动SLB失败"
            hslb.extend(ret["res"]["data"])
            total = int(ret["res"]["total"])
            if len(hslb) >= total:
                break
            page += 1
        return hslb

    def HSLB_DescribeDpvsListener(self, hslb_id):
        '''
        拉取监听器列表
        '''
        api = 'api/networks/hslb'
        method = 'GET'
        params = {"Action": "DescribeDpvsListener", "regionId": self.region[0], "t": timeStap(), "size": 10,
                  "loadbalancerId": hslb_id}
        page = 1
        listeners = []
        s_time = time.time()
        while time.time() - s_time < (5 * 60):
            params["page"] = 1
            ret = self.send_request(api=api, method=method, **params)
            if ret["code"] != "Network.Success":
                raise "获取监听器失败:%s" % hslb_id
            listeners.extend(ret["res"]["data"])
            total = int(ret["res"]["total"])
            if len(listeners) >= total:
                break
            page += 1
        return listeners

    def HSLB_DescribeDpvsServerGroup(self, hslb_id):
        '''
        拉取监听器列表
        '''
        api = 'api/networks/hslb'
        method = 'GET'
        params = {"Action": "DescribeDpvsServerGroup", "regionId": self.region[0], "t": timeStap(), "size": 10,
                  "loadbalancerId": hslb_id}
        page = 1
        server_groups = []
        s_time = time.time()
        while time.time() - s_time < (5 * 60):
            params["page"] = 1
            ret = self.send_request(api=api, method=method, **params)
            if ret["code"] != "Network.Success":
                raise "获取服务器组失败:%s" % hslb_id
            server_groups.extend(ret["res"]["data"])
            total = int(ret["res"]["total"])
            if len(server_groups) >= total:
                break
            page += 1
        return server_groups

    def HSLB_BatchOperateDpvsServerPort(self, hslb_id, server_group_id, servers):
        '''
        为HSLB服务器组增删服务器,服务器组信息:
        [
                {
                    "portId": "eni-e9ocx2vh5cq0",
                    "serverId": "ecs-e9ocx2vh5cqy",
                    "serverIpv4Ip": "172.16.0.15",
                    "serverIpv6Ip": "",
                    "serverPort": 29531,
                    "weight": 1,
                    "serverGroupId": "c58544bdc7b14084a6bf9a004f091ba7",
                    "actionStatus": 0,
                    "loadbalancerId": "hslb-fj2ixi092tu9",
                    "subnetId": "vsnet-e9ocxuzdo532",
                    "serverStatus": "RUNNING",
                    "etherType": "ipv4"
                }
            ]
        '''
        api = 'api/networks/hslb'
        method = 'POST'
        params = {"Action": "BatchOperateDpvsServerPort", "regionId": self.region[0], "t": timeStap()}
        data = {
            "loadbalancerId": hslb_id,
            "serverGroupId": server_group_id,
            "servers": servers
        }
        ret = self.send_request(api=api, method=method, data=data, **params)
        if ret["code"] != "Network.Success":
            raise "获取ACL失败"
        return ret

    def HSLB_DescribeDpvsAcl(self, name=None):
        '''
        拉取监听器列表
        '''
        api = 'api/networks/hslb'
        method = 'GET'
        params = {"Action": "DescribeDpvsAcl", "regionId": self.region[0], "t": timeStap(), "size": 10}
        if name is not None:
            params["name"] = name
        page = 1
        acls = []
        s_time = time.time()
        while time.time() - s_time < (5 * 60):
            params["page"] = 1
            ret = self.send_request(api=api, method=method, **params)
            if ret["code"] != "Network.Success":
                raise "获取ACL失败"
            acls.extend(ret["res"]["data"])
            total = int(ret["res"]["total"])
            if len(acls) >= total:
                break
            page += 1
        return acls

    def HSLB_DescribeDpvsAclRule(self, acl_id):
        '''
        拉取监听器列表
        '''
        api = 'api/networks/hslb'
        method = 'GET'
        params = {"Action": "DescribeDpvsAclRule", "regionId": self.region[0], "t": timeStap(), "size": 10,
                  "aclPolicyId": acl_id}
        page = 1
        acl_rules = []
        s_time = time.time()
        while time.time() - s_time < (5 * 60):
            params["page"] = 1
            ret = self.send_request(api=api, method=method, **params)
            if ret["code"] != "Network.Success":
                raise "获取ACL失败"
            acl_rules.extend(ret["res"]["data"])
            total = int(ret["res"]["total"])
            if len(acl_rules) >= total:
                break
            page += 1
        return acl_rules

    def HSLB_CreateDpvs(self, vpc_id, subnet_id, ip_address="", project_id=None, name="hslb_auto_name"):
        '''
        新建高性能SLB
        '''
        api = 'api/networks/hslb'
        method = 'POST'
        params = {"Action": "CreateDpvs", "regionId": self.region[0], "t": timeStap()}
        if project_id is None:
            project_id = self.HSLB_get_available_project_id()
        data = {"azoneId": self.azone_id, "chargeType": "postpaid",
                "componentProperty": {"specificationCode": "slb.highperformance.small"},
                "instanceCode": "hpslbInstance",
                "instanceName": name, "orderCategory": "NEW", "payType": "DAY_MONTH",
                "productDescription": "",
                "productProperties": [
                    {"address": ip_address, "subnetId": subnet_id, "vpcId": vpc_id}],
                "projectId": project_id,
                "quantity": 1, "renewType": "notrenew", "rentCount": 1, "rentUnit": "month"}
        ret = self.send_request(api=api, method=method, data=data, **params)
        if ret["code"] != "Network.Success":
            raise "新建高性能SLB失败"
        order_id = ret["res"]["orderId"]
        slb_id = ret["res"]["resources"][0]["instanceId"]
        self.SLB_approve_order(order_id=order_id)
        return slb_id

    def SLB_approve_order(self, order_id):
        api = "/api/transaction-core/uco/v1/transaction/approveOrder"
        method = "GET"
        params = {"t": str(int(time.time() * 1000)), "orderId": order_id}
        data = {}
        self.send_request(api=api, method=method, data=data, **params)

    def HSLB_get_available_project_id(self):
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

    def HSLB_CreateDpvsWizard(self, hslb_id, lister_name="auto_default_name", protoco="TCP", protocolPort="8080",
                              server_group="", health_check_open=True, hc_name="hc_default_name", hc_check_type="TCP",
                              servers=[]):
        '''
        创建SLB监听器,server_group如下:
        {
                "id": "5f88819094554b999276646447c4874a",
                "name": "tcp8888",
                "description": "",
                "algorithm": "ROUND_ROBIN",
                "sessionType": "",
                "cookieName": "",
                "loadbalancerId": "hslb-e9ocxuzdos7i",
                "serverGroupId": "5f88819094554b999276646447c4874a"
            }
        '''
        api = 'api/networks/hslb'
        method = 'POST'
        params = {"Action": "CreateDpvsWizard", "regionId": self.region[0], "t": timeStap()}
        data = {
            "listener": {
                "name": lister_name,
                "protocol": protoco,
                "protocolPort": protocolPort,
                "redirect": False,
                "sni": False,
                "connectionLimit": "",
                "description": "",
                "loadbalancerId": hslb_id
            },
            "serverGroup": server_group,
            "healthMonitor": {
                "open": health_check_open,
                "name": hc_name,
                "checkType": hc_check_type,
                "httpMethod": "",
                "matchingUrl": "",
                "expectResponseCode": [],
                "checkInterval": 5,
                "timeout": 3,
                "maxRetries": 3,
                "loadbalancerId": hslb_id
            },
            "servers": servers
        }
        ret = self.send_request(api=api, method=method, data=data, **params)
        if ret["code"] != "Network.Success":
            raise "创建监听器失败"
        return ret

    def HSLB_DescribeVmListForDpvsServerGroup(self, hslb_id):
        '''
        高性能SLB获取可用的虚机列表
        '''
        api = 'api/networks/hslb'
        method = 'GET'
        params = {"Action": "DescribeVmListForDpvsServerGroup", "regionId": self.region[0], "t": timeStap(),
                  "azoneId": self.azone_id, "loadbalancerId": hslb_id}
        ret = self.send_request(api=api, method=method, **params)
        ecses = ret["res"]
        return ecses

    def HSLB_CreateDpvsServerGroup(self, hslb_id, server_group_name="auto_defalut_name", desc="auto desc",
                                   algorithm="ROUND_ROBIN", servers=[]):
        '''
        创建高性能SLB监听器,servers实例如下
        [
                {
                    "etherType": "ipv4",
                    "serverPort": "54100",
                    "weight": 1,
                    "serverId": "ecs-e9ocx2vh5cqy",
                    "serverName": "test",
                    "portId": "eni-e9ocx2vh5cq0",
                    "serverIpv4Ip": "172.16.0.15",
                    "eipAddr": "172.25.136.194",
                    "serverIpv6Ip": "",
                    "subnetId": "vsnet-e9ocxuzdo532",
                    "cbwId": None
                }
            ]
        '''
        api = 'api/networks/hslb'
        method = 'POST'
        if not isinstance(servers, list):
            servers = [servers]
        params = {"Action": "CreateDpvsServerGroup", "regionId": self.region[0], "t": timeStap()}
        data = {
            "name": server_group_name,
            "description": desc,
            "algorithm": algorithm,
            "sessionType": "",
            "cookieName": "",
            "loadbalancerId": hslb_id,
            "servers": servers
        }
        ret = self.send_request(api=api, method=method, data=data, **params)
        if ret["code"] != "Network.Success":
            raise "创建服务器组失败"
        return ret

    def HSLB_StopDpvsListener(self, listener_ids, hslb_id):
        '''
        关闭SLB监听器
        '''
        api = 'api/networks/hslb'
        method = 'POST'
        params = {"Action": "StopDpvsListener", "regionId": self.region[0], "t": timeStap()}
        if not isinstance(listener_ids, list):
            listener_ids = [listener_ids]
        data = {
            "listenerIds": listener_ids,
            "loadbalancerId": hslb_id
        }
        ret = self.send_request(api=api, method=method, data=data, **params)
        if ret["code"] != "Network.Success":
            raise "停止监听器失败"
        return ret

    def HSLB_StartDpvsListener(self, listener_ids, hslb_id):
        '''
        开启SLB监听器
        '''
        api = 'api/networks/hslb'
        method = 'POST'
        params = {"Action": "StartDpvsListener", "regionId": self.region[0], "t": timeStap()}
        if not isinstance(listener_ids, list):
            listener_ids = [listener_ids]
        data = {
            "listenerIds": listener_ids,
            "loadbalancerId": hslb_id
        }
        ret = self.send_request(api=api, method=method, data=data, **params)
        if ret["code"] != "Network.Success":
            raise "开启监听器失败"
        return ret

    def HSLB_StopDpvs(self, hslb_ids):
        '''
        停止高性能SLB
        '''
        api = 'api/networks/hslb'
        method = 'POST'
        params = {"Action": "StopDpvs", "regionId": self.region[0], "t": timeStap()}
        if not isinstance(hslb_ids, list):
            hslb_ids = [hslb_ids]
        data = hslb_ids
        ret = self.send_request(api=api, method=method, data=data, **params)
        if ret["code"] != "Network.Success":
            raise "停止高性能SLB失败"
        return ret

    def HSLB_StartDpvs(self, hslb_ids):
        '''
        开启高性能SLB
        '''
        api = 'api/networks/hslb'
        method = 'POST'
        params = {"Action": "StartDpvs", "regionId": self.region[0], "t": timeStap()}
        if not isinstance(hslb_ids, list):
            hslb_ids = [hslb_ids]
        data = hslb_ids
        ret = self.send_request(api=api, method=method, data=data, **params)
        if ret["code"] != "Network.Success":
            raise "开启高性能SLB失败"
        return ret

    def HSLB_DeleteDpvsListener(self, listener_ids, hslb_id):
        '''
        删除监听器
        '''
        api = 'api/networks/hslb'
        method = 'POST'
        params = {"Action": "DeleteDpvsListener", "regionId": self.region[0], "t": timeStap()}
        if not isinstance(listener_ids, list):
            listener_ids = [listener_ids]
        data = {
            "listenerIds": listener_ids,
            "loadbalancerId": hslb_id
        }
        ret = self.send_request(api=api, method=method, data=data, **params)
        if ret["code"] != "Network.Success":
            raise "删除监听器失败"
        return ret

    def HSLB_DeleteDpvsServerGroup(self, hslb_id, server_group_ids):
        '''
        删除高性能SLB服务器组
        '''
        api = 'api/networks/hslb'
        method = 'POST'
        params = {"Action": "DeleteDpvsServerGroup", "regionId": self.region[0], "t": timeStap()}
        if not isinstance(server_group_ids, list):
            server_group_ids = [server_group_ids]
        data = {
            "loadbalancerId": hslb_id,
            "serverGroupIds": server_group_ids
        }
        ret = self.send_request(api=api, method=method, data=data, **params)
        if ret["code"] != "Network.Success":
            raise "删除服务器组失败"
        return ret

    def HSLB_DeleteDpvs(self, ids):
        '''
        删除高性能SLB
        '''
        api = 'api/networks/hslb'
        method = 'POST'
        params = {"Action": "DeleteDpvs", "regionId": self.region[0], "t": timeStap(), "smsCode": ""}
        if not isinstance(ids, list):
            ids = [ids]
        data = ids
        ret = self.send_request(api=api, method=method, data=data, **params)
        if ret["code"] != "Network.Success":
            raise "删除服务器组失败"
        return ret

    def HSLB_CreateDpvsAcl(self, name, rules=[]):
        '''
        创建高性能SLB访问控制列表,rule格式如下
        [
                {
                    "ipSegment": "123.1.1.1",
                    "etherType": "IPV4",
                    "description": ""
                }
            ]
        '''
        api = 'api/networks/hslb'
        method = 'POST'
        params = {"Action": "CreateDpvsAcl", "regionId": self.region[0], "t": timeStap()}
        if not isinstance(rules, list):
            rules = [rules]
        data = {
            "rules": rules,
            "name": name
        }
        ret = self.send_request(api=api, method=method, data=data, **params)
        if ret["code"] != "Network.Success":
            raise "新建规则失败"
        return ret

    def HSLB_CreateDpvsAclRule(self, acl_id, rules):
        '''
        创建ACL规则,rules参数如下:
        [
                {
                    "ipSegment": "1.1.1.1",
                    "etherType": "IPV4",
                    "description": ""
                }
            ]
        '''
        if not isinstance(rules, list):
            rules = [rules]
        api = 'api/networks/hslb'
        method = 'POST'
        params = {"Action": "CreateDpvsAclRule", "regionId": self.region[0], "t": timeStap()}
        data = {
            "aclPolicyId": acl_id,
            "aclRuleList": rules
        }
        ret = self.send_request(api=api, method=method, data=data, **params)
        if ret["code"] != "Network.Success":
            raise "新建ACL规则失败"
        return ret

    def HSLB_ModifyDpvsAclRule(self, acl_rule_id, new_desc):
        '''
        修改ACL规则描述
        '''
        api = 'api/networks/hslb'
        method = 'PUT'
        params = {"Action": "ModifyDpvsAclRule", "regionId": self.region[0], "t": timeStap()}
        data = {
            "description": new_desc,
            "id": acl_rule_id
        }
        ret = self.send_request(api=api, method=method, data=data, **params)
        if ret["code"] != "Network.Success":
            raise "修改ACL规则描述失败"
        return ret

    def HSLB_DeleteDpvsAclRule(self, acl_id, acl_rule_id):
        '''
        删除ACL规则
        '''
        if not isinstance(acl_rule_id, list):
            acl_rule_id = [acl_rule_id]
        api = 'api/networks/hslb'
        method = 'POST'
        params = {"Action": "DeleteDpvsAclRule", "regionId": self.region[0], "t": timeStap()}
        data = {
            "aclPolicyId": acl_id,
            "ids": acl_rule_id
        }
        ret = self.send_request(api=api, method=method, data=data, **params)
        if ret["code"] != "Network.Success":
            raise "删除ACL规则失败"
        return ret

    def HSLB_BindAclFromDpvsListener(self, acl_id, hslb_id, listener_id):
        '''
        绑定ACL到监听器
        '''
        api = 'api/networks/hslb'
        method = 'POST'
        params = {"Action": "BindAclFromDpvsListener", "regionId": self.region[0], "t": timeStap()}
        data = {
            "aclPolicyId": acl_id,
            "listenerId": listener_id,
            "loadbalancerId": hslb_id
        }
        ret = self.send_request(api=api, method=method, data=data, **params)
        if ret["code"] != "Network.Success":
            raise "安全组(%s)绑定SLB(%s)监听器(%s)失败" % (acl_id, hslb_id, listener_id)
        return ret

    def HSLB_UnbindAclFromDpvsListener(self, acl_id, hslb_id, listener_id):
        '''
        绑定ACL到监听器
        '''
        api = 'api/networks/hslb'
        method = 'PUT'
        params = {"Action": "UnbindAclFromDpvsListener", "regionId": self.region[0], "t": timeStap()}
        data = {
            "aclPolicyId": acl_id,
            "listenerId": listener_id,
            "loadbalancerId": hslb_id
        }
        ret = self.send_request(api=api, method=method, data=data, **params)
        if ret["code"] != "Network.Success":
            raise "安全组(%s)绑定SLB(%s)监听器(%s)失败" % (acl_id, hslb_id, listener_id)
        return ret

    def HSLB_DeleteDpvsAcl(self, acl_id):
        '''
        删除ACL
        '''
        api = 'api/networks/hslb'
        method = 'POST'
        params = {"Action": "DeleteDpvsAcl", "regionId": self.region[0], "t": timeStap(), "aclPolicyId": acl_id}
        ret = self.send_request(api=api, method=method, **params)
        if ret["code"] != "Network.Success":
            raise "安全组(%s)删除失败" % (acl_id)
        return ret
