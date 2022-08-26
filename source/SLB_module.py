import time

from source.locust_methods import Agent_SDN_nolocust, timeStap


class SLB(Agent_SDN_nolocust):
    def SLB_CreateSlb(self, vpc_id, subnet_id, name="test", ip_address="", eip_id=""):
        """
        return:
        """
        api = 'api/networks/slb'
        method = 'POST'
        params = {"Action": "CreateSlb", "regionId": self.region[0], "t": timeStap()}
        data = {"azoneId": self.azone_id, "chargeType": "postpaid",
                "componentProperty": {"specificationCode": "slb.s1.small"}, "instanceCode": "SLB",
                "instanceName": name, "orderCategory": "NEW", "payType": "DAY_MONTH",
                "productDescription": "",
                "productProperties": [
                    {"address": ip_address, "eipId": eip_id, "subnetId": subnet_id, "vpcId": vpc_id}],
                "quantity": 1, "renewType": "notrenew", "rentCount": 1, "rentUnit": "month", "trial": False}
        ret = self.send_request(api=api, method=method, data=data, **params)
        if ret["code"] != "Network.Success":
            raise "新建SLB失败"
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

    def SLB_DescribeSlb(self, name=None, id=None):
        '''
        根据条件过滤SLB
        '''
        api = 'api/networks/slb'
        method = 'GET'
        params = {"Action": "DescribeSlb", "regionId": self.region[0], "t": timeStap(), "size": 10}
        page = 1
        if name is not None:
            params["instanceName"] = name
        if id is not None:
            params["instanceId"] = id
        slbs = []
        s_time = time.time()
        # 为了避免死循环
        while time.time() - s_time < (5 * 60):
            params["page"] = page
            ret = self.send_request(api=api, method=method, **params)
            if ret["code"] != "Network.Success":
                raise "查询SLB失败"
            slbs.extend(ret["res"]["data"])
            page += 1
            total = int(ret["res"]["total"])
            if len(slbs) >= total:
                break
        return slbs

    def SLB_ModifySlb(self, slb_id, new_slb_name):
        '''
        修改SLB名称
        '''
        api = 'api/networks/slb'
        method = 'PUT'
        params = {"Action": "ModifySlb", "regionId": self.region[0], "t": timeStap(), "lbId": slb_id,
                  "name": new_slb_name}
        ret = self.send_request(api=api, method=method, **params)
        if ret["code"] != "Network.Success":
            raise "修改SLB名称失败"
        return ret

    def SLB_StopSlb(self, slb_id=None):
        '''
        停止SLB,slb_id可以是一个SLB ID的列表
        '''
        if not isinstance(slb_id, list):
            slb_id = [slb_id]
        api = 'api/networks/slb'
        method = 'PUT'
        params = {"Action": "StopSlb", "regionId": self.region[0], "t": timeStap()}
        data = {"lbIdList": slb_id}
        ret = self.send_request(api=api, method=method, data=data, **params)
        if ret["code"] != "Network.Success":
            raise "停止SLB失败"
        return ret

    def SLB_StartSlb(self, slb_id=None):
        '''
        停止SLB,slb_id可以是一个SLB ID的列表
        '''
        if not isinstance(slb_id, list):
            slb_id = [slb_id]
        api = 'api/networks/slb'
        method = 'PUT'
        params = {"Action": "StartSlb", "regionId": self.region[0], "t": timeStap()}
        data = {"lbIdList": slb_id}
        ret = self.send_request(api=api, method=method, data=data, **params)
        if ret["code"] != "Network.Success":
            raise "启动SLB失败"
        return ret

    def SLB_DeleteSlb(self, slb_id=None):
        '''
        停止SLB,slb_id可以是一个SLB ID的列表
        '''
        if not isinstance(slb_id, list):
            slb_id = [slb_id]
        api = 'api/networks/slb'
        method = 'PUT'
        params = {"Action": "DeleteSlb", "regionId": self.region[0], "t": timeStap()}
        data = {"ids": slb_id}
        ret = self.send_request(api=api, method=method, data=data, **params)
        if ret["code"] != "Network.Success":
            raise "启动SLB失败"
        return ret

    def SLB_WIZARD(self, slb_id, listener_name="test", protocol="TCP", port="80", redirect=False, sni=False,
                   connect_limit="", listener_desc="", server_group_id="", server_group_name="auto_server_group",
                   server_group_desc="", server_group_algorithm="ROUND_ROBIN", server_group_session_type="",
                   server_group_cookieName="", server_group_list=[], health_check=True,
                   health_check_name="auto_health_name", health_type="TCP", health_check_http_method="",
                   health_check_match_url="", health_check_expect_rsp_code="", health_check_interval=5,
                   health_check_timeout=3, health_check_max_retry=3):
        '''
        新建监听器,至少需要传入SLBID,其余都有默认值
        '''
        api = 'api/networks/slb'
        method = 'PUT'
        params = {"Action": "WIZARD", "regionId": self.region[0], "t": timeStap()}
        if not isinstance(health_check_expect_rsp_code, list):
            health_check_expect_rsp_code = [health_check_expect_rsp_code]
        data = {
            "listener": {
                "name": listener_name,
                "protocol": protocol,
                "protocolPort": port,
                "redirect": redirect,
                "sni": sni,
                "connectionLimit": connect_limit,
                "description": listener_desc,
                "loadbalancerId": slb_id
            },
            "serverGroup": {
                "id": server_group_id,
                "name": server_group_name,
                "description": server_group_desc,
                "algorithm": server_group_algorithm,
                "sessionType": server_group_session_type,
                "cookieName": server_group_cookieName,
                "loadbalancerId": slb_id
            },
            "servers": server_group_list,
            "healthMonitor": {
                "open": health_check,
                "name": health_check_name,
                "checkType": health_type,
                "httpMethod": health_check_http_method,
                "matchingUrl": health_check_match_url,
                "expectResponseCode": health_check_expect_rsp_code,
                "checkInterval": health_check_interval,
                "timeout": health_check_timeout,
                "maxRetries": health_check_max_retry,
                "loadbalancerId": slb_id
            }
        }
        ret = self.send_request(api=api, method=method, data=data, **params)
        if ret["code"] != "Network.Success":
            raise "创建监听器失败"
        return ret

    def SLB_DescribeListener(self, slb_id):
        '''
        拉取监听器列表,返回列表
        '''
        api = 'api/networks/slb'
        method = 'GET'
        params = {"Action": "DescribeListener", "regionId": self.region[0], "t": timeStap(), "loadbalancerId": slb_id,
                  "size": 10}
        page = 1
        listeners = []
        s_time = time.time()
        while time.time() - s_time < (5 * 60):
            params["page"] = page
            ret = self.send_request(api=api, method=method, **params)
            if ret["code"] != "Network.Success":
                raise "启动SLB失败"
            listeners.extend(ret["res"]["data"])
            total = int(ret["res"]["total"])
            if len(listeners) >= total:
                break
            page += 1

        return listeners

    def SLB_StopListener(self, slb_id, listener_ids):
        '''
        停止监听器
        '''
        api = 'api/networks/slb'
        method = 'PUT'
        params = {"Action": "StopListener", "regionId": self.region[0], "t": timeStap()}
        if not isinstance(listener_ids, list):
            listener_ids = [listener_ids]

        data = {"listenerIds": listener_ids, "loadbalancerId": slb_id}
        ret = self.send_request(api=api, method=method, data=data, **params)
        if ret["code"] != "Network.Success":
            raise "停止监听器失败"
        return ret

    def SLB_StartListener(self, slb_id, listener_ids):
        '''
        启动监听器
        '''
        api = 'api/networks/slb'
        method = 'PUT'
        params = {"Action": "StartListener", "regionId": self.region[0], "t": timeStap()}
        if not isinstance(listener_ids, list):
            listener_ids = [listener_ids]

        data = {"listenerIds": listener_ids, "loadbalancerId": slb_id}
        ret = self.send_request(api=api, method=method, data=data, **params)
        if ret["code"] != "Network.Success":
            raise "启动监听器失败"
        return ret

    def SLB_DeleteListener(self, slb_id, listener_ids):
        '''
        启动监听器
        '''
        api = 'api/networks/slb'
        method = 'PUT'
        params = {"Action": "DeleteListener", "regionId": self.region[0], "t": timeStap()}
        if not isinstance(listener_ids, list):
            listener_ids = [listener_ids]

        data = {"listenerIds": listener_ids, "loadbalancerId": slb_id}
        ret = self.send_request(api=api, method=method, data=data, **params)
        if ret["code"] != "Network.Success":
            raise "删除监听器失败"
        return ret

    def SLB_ModifyListener(self, listener_id, new_name="autoNewName", connect_limit="", new_desc="auto new_desc"):
        '''
        修改监听器参数
        '''
        api = 'api/networks/slb'
        method = 'PUT'
        params = {"Action": "DeleteListener", "regionId": self.region[0], "t": timeStap()}
        data = {"name": new_name, "connectionLimit": connect_limit, "new_desc": "123", "id": listener_id}
        ret = self.send_request(api=api, method=method, data=data, **params)
        if ret["code"] != "Network.Success":
            raise "修改监听器失败"
        return ret

    def SLB_DescribeServerGroup(self, slb_id, server_group_id=None):
        '''
        获取SLB服务器组列表
        '''
        api = 'api/networks/slb'
        method = 'GET'
        params = {"Action": "DescribeServerGroup", "regionId": self.region[0], "t": timeStap(),
                  "loadbalancerId": slb_id, "size": 10}
        if server_group_id is not None:
            params["serverGroupIds"] = server_group_id
        page = 1
        server_groups = []
        s_time = time.time()
        while time.time() - s_time < (5 * 60):
            params["page"] = page
            ret = self.send_request(api=api, method=method, **params)
            server_groups.extend(ret["res"]["data"])
            total = int(ret["res"]["total"])
            if len(server_groups) >= total:
                break
            page += 1

        return server_groups

    def SLB_DescribeAvailableEcsForSlb(self, slb_id):
        '''
        检查SLB可用的ECS
        '''
        api = 'api/networks/slb'
        method = 'GET'
        params = {"Action": "DescribeAvailableEcsForSlb", "regionId": self.region[0], "t": timeStap(),
                  "azoneId": self.azone_id, "loadbalancerId": slb_id}
        ret = self.send_request(api=api, method=method, **params)
        ecses = ret["res"]
        return ecses

    def SLB_OperateServer(self, servers):
        '''
        给服务器组增加RS
          "servers": [
            {
              "portId": "eni-e9ocx2vh5cq0",
              "serverId": "ecs-e9ocx2vh5cqy",
              "serverIp": "172.16.0.15",
              "serverPort": 34512,
              "weight": 1,
              "serverGroupId": "5fbbe54c30874a1ea8e675413b722dec",
              "actionStatus": 0,
              "loadbalancerId": "slb-e9ocxuzdop8z"
            }
          ]
        '''
        if not isinstance(servers, list):
            servers = [servers]
        api = 'api/networks/slb'
        method = 'PUT'
        params = {"Action": "OperateServer", "regionId": self.region[0], "t": timeStap()}
        data = {
            "servers": servers
        }
        ret = self.send_request(api=api, method=method, data=data, **params)
        if ret["code"] != "Network.Success":
            raise "服务器组添加服务器失败"
        return ret

    def SLB_CreateServerGroup(self, server_group_name, server_group_desc="", algorithm="ROUND_ROBIN", session_type="",
                              cookie_name="", slb_id="", servers=[]):
        '''
        创建服务器组
        '''
        api = 'api/networks/slb'
        method = 'POST'
        params = {"Action": "CreateServerGroup", "regionId": self.region[0], "t": timeStap()}
        data = {
            "name": server_group_name,
            "description": server_group_desc,
            "algorithm": algorithm,
            "sessionType": session_type,
            "cookieName": cookie_name,
            "loadbalanceId": "",
            "loadbalancerId": slb_id,
            "servers": servers
        }
        ret = self.send_request(api=api, method=method, data=data, **params)
        server_group_id = ret["res"]["ids"][0]
        return server_group_id

    def SLB_DeleteServerGroup(self, slb_id, server_group_id):
        '''
        删除服务器组
        '''
        api = 'api/networks/slb'
        method = 'POST'
        params = {"Action": "DeleteServerGroup", "regionId": self.region[0], "t": timeStap()}
        data = {
            "loadbalancerId": slb_id,
            "serverGroupIds": [server_group_id]
        }
        ret = self.send_request(api=api, method=method, data=data, **params)
        if ret["code"] != "Network.Success":
            raise "删除服务器组失败"
        return ret

    def SLB_DescribeSlbMonitor(self, slb_id, start_time, end_time=timeStap(), direction="in"):
        '''
        拉取监控信息
        '''
        if direction == "in":
            direction = "bandwidthIn"
            title = "流入带宽"
        elif direction == "out":
            direction = "bandwidthOut"
            title = "流出带宽"
        api = 'api/networks/slb'
        method = 'POST'
        params = {"Action": "DescribeSlbMonitor", "regionId": self.region[0], "t": timeStap(), "category": direction,
                  "title": title, "chartsTitle": "带宽（单位：Mbps）", "startTime": start_time, "endTime": end_time,
                  "instance": slb_id}
        ret = self.send_request(api=api, method=method, **params)
        if ret["code"] != "Network.Success":
            raise "拉取监控信息失败"
        return ret

    def SLB_CreateAcl(self, acl_name="auto_default", rules=None):
        '''
        创建访问控制列表[{"ipSegment": "10.0.0.1/32","description": "" }]
        '''
        if rules is None:
            rules = []
        api = 'api/networks/slb'
        method = 'POST'
        params = {"Action": "CreateAcl", "regionId": self.region[0], "t": timeStap()}
        data = {
            "rules": rules,
            "name": acl_name,
            "etherType": "IPv4"
        }
        ret = self.send_request(api=api, method=method, data=data, **params)
        if ret["code"] != "Network.Success":
            raise "新建ACL失败"
        return ret

    def SLB_DescribeAcl(self, name=None):
        '''
        拉取访问控制列表
        '''
        api = 'api/networks/slb'
        method = 'GET'
        params = {"Action": "DescribeAcl", "regionId": self.region[0], "t": timeStap(), "size": 10}
        if name is not None:
            params["name"] = name
        page = 1
        acls = []
        s_time = time.time()
        while time.time() - s_time < (5 * 60):
            params["page"] = page
            ret = self.send_request(api=api, method=method, **params)
            if ret["code"] != "Network.Success":
                raise "新建ACL失败"
            acls.extend(ret["res"]["data"])
            total = int(ret["res"]["total"])
            if len(acls) >= total:
                break
            page += 1
        return acls

    def SLB_ModifyAcl(self, acl_id, new_acl_name):
        '''
        修改访问控制列表
        '''
        api = 'api/networks/slb'
        method = 'PUT'
        params = {"Action": "ModifyAcl", "regionId": self.region[0], "t": timeStap(), "aclId": acl_id,
                  "name": new_acl_name}

        ret = self.send_request(api=api, method=method, **params)
        if ret["code"] != "Network.Success":
            raise "修改ACL名称失败"
        return ret

    def SLB_DeleteAcl(self, acl_id):
        '''
        删除访问控制列表
        '''
        api = 'api/networks/slb'
        method = 'DELETE'
        params = {"Action": "DeleteAcl", "regionId": self.region[0], "t": timeStap(), "aclId": acl_id}

        ret = self.send_request(api=api, method=method, **params)
        if ret["code"] != "Network.Success":
            raise "删除ACL失败"
        return ret

    def SLB_DescribeAclRule(self, acl_id):
        '''
        拉取ACL规则列表
        '''
        api = 'api/networks/slb'
        method = 'GET'
        params = {"Action": "DescribeAclRule", "regionId": self.region[0], "t": timeStap(), "aclId": acl_id}

        ret = self.send_request(api=api, method=method, **params)
        if ret["code"] != "Network.Success":
            raise "删除ACL失败"
        aclrules = ret["res"]["data"]
        return aclrules

    def SLB_CreateAclRule(self, acl_id, ip, desc):
        '''
        创建ACL规则
        '''
        api = 'api/networks/slb'
        method = 'POST'
        params = {"Action": "CreateAclRule", "regionId": self.region[0], "t": timeStap()}
        data = {
            "rules": [
                {
                    "ipSegment": ip,
                    "description": desc,
                    "aclPolicyId": acl_id
                }
            ]
        }

        ret = self.send_request(api=api, method=method, data=data, **params)
        if ret["code"] != "Network.Success":
            raise "创建ACL规则"
        return ret

    def SLB_ModifyAclRule(self, rule_id, new_desc):
        '''
        修改访问控制列表规则,目前只能改描述
        '''
        api = 'api/networks/slb'
        method = 'PUT'
        params = {"Action": "ModifyAclRule", "regionId": self.region[0], "t": timeStap()}
        data = {
            "description": new_desc,
            "id": rule_id
        }
        ret = self.send_request(api=api, method=method, data=data, **params)
        if ret["code"] != "Network.Success":
            raise "修改ACL规则失败"
        return ret

    def SLB_DeleteAclRule(self, acl_id, rule_id):
        '''
        删除访问控制列表规则
        '''
        api = 'api/networks/slb'
        method = 'PUT'
        params = {"Action": "DeleteAclRule", "regionId": self.region[0], "t": timeStap(), "aclId": acl_id}
        data = [rule_id]

        ret = self.send_request(api=api, method=method, data=data, **params)
        if ret["code"] != "Network.Success":
            raise "删除ACL失败"
        return ret

    def SLB_BindAclToListener(self, acl_id, listener_id):
        '''
        绑定SLB监听器和访问控制列表
        '''
        api = 'api/networks/slb'
        method = 'PUT'
        params = {"Action": "BindAclToListener", "regionId": self.region[0], "t": timeStap(), "aclId": acl_id,
                  "listenerId": listener_id}

        ret = self.send_request(api=api, method=method, **params)
        if ret["code"] != "Network.Success":
            raise "绑定ACL到监听器失败"
        return ret

    def SLB_UnbindAclFromListener(self, acl_id, listener_id):
        '''
        解绑SLB监听器和访问控制列表
        '''
        api = 'api/networks/slb'
        method = 'PUT'
        params = {"Action": "UnbindAclFromListener", "regionId": self.region[0], "t": timeStap(), "aclId": acl_id,
                  "listenerId": listener_id}

        ret = self.send_request(api=api, method=method, **params)
        if ret["code"] != "Network.Success":
            raise "绑定ACL到监听器失败"
        return ret
