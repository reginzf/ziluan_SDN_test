from source.locust_methods import Agent_SDN_nolocust, timeStap
from source.ORDER_module import ORDER
import time


class GSLB(Agent_SDN_nolocust):
    def GSLB_CreateGslb(self, name="myautotest", desc="auto test desc", cname=None):
        api = 'api/networks/gslb'
        method = "POST"
        if cname is None:
            raise "cname不能为None"
        data = {
            "chargeType": "postpaid",
            "componentProperty": {
                "specificationCode": "gslb.common.normal"
            },
            "instanceCode": "gslbInstance",
            "orderCategory": "NEW",
            "payType": "DAY_MONTH",
            "instanceName": name,
            "productProperties": [
                {
                    "desc": desc,
                    "globalTtl": 10,
                    "realmName": cname
                }
            ],
            "quantity": 1,
            "renewType": "notrenew",
            "rentCount": 1,
            "rentUnit": "month"
        }
        # print("开始发送请求")
        params = {"Action": "CreateGslbOrder", "regionId": self.region[0], "t": timeStap()}
        ret = self.send_request(api=api, method=method, data=data, **params)
        if ret["code"] != "Network.Success":
            return False
        # print("请求成功:", ret)
        order_id = ret["res"]["orderId"]
        ORDER.approve_order(self, order_id=order_id)
        gslb_id = ret["res"]["resources"][0]["instanceId"]
        return gslb_id

    def GSLB_DeleteGslb(self, gslb_id=None):
        '''
        删除GSLB实例
        :gslb_id 为列表或者字符串
        '''
        if gslb_id is None:
            raise "gslb id为None"
        if not isinstance(gslb_id, list):
            gslb_id = [gslb_id]

        params = {"Action": "DeleteGslb", "regionId": self.region[0], "t": timeStap()}
        data = gslb_id
        api = 'api/networks/gslb'
        method = "POST"
        ret = self.send_request(api=api, method=method, data=data, **params)
        if ret["code"] != "Network.Success":
            return False
        # print("gslb %s 删除成功" % gslb_id)
        return True

    def GSLB_CreateGslbPolicys(self, gslb_id=None, policy_name="autoname", pool_id=None, lvs="All",
                               desc="auto description"):
        '''
        创建gslb策略
        lvs:支持All和Weight,返回所有地址和按权重返回
        '''
        data = {
            "gslbId": gslb_id,
            "instanceName": policy_name,
            "resolveRoute": "Global",
            "addrPoolId": pool_id,
            "lvsStr": lvs,
            "note": desc
        }
        params = {"Action": "CreateGslbPolicys", "regionId": self.region[0], "t": timeStap()}
        api = 'api/networks/gslb'
        method = "POST"
        ret = self.send_request(api=api, method=method, data=data, **params)
        if ret["code"] != "Network.Success":
            return False
        print("创建GSLB:%s策略成功" % gslb_id)
        return True

    def GSLB_DeleteGslbPolicys(self, gslb_id=None, policy_id=None):
        '''
        删除GSLB策略
        '''
        if not isinstance(policy_id, list):
            policy_id = [policy_id]
        data = {
            "gslbId": gslb_id,
            "instanceIds": policy_id
        }
        params = {"Action": "DeleteGslbPolicys", "regionId": self.region[0], "t": timeStap()}
        api = 'api/networks/gslb'
        method = "DELETE"
        ret = self.send_request(api=api, method=method, data=data, **params)
        if ret["code"] != "Network.Success":
            return False
        print("删除GSLB:%s策略:%s成功" % (gslb_id, policy_id))
        return True

    def GSLB_GetGslbPolicysPage(self, gslb_id=None):
        '''
        获取GSLB的策略详情
        return:
        [{
      "instanceId": "gsty-f33ny8b1qet7",
      "instanceName": "test",
      "resolveRoute": "Global",
      "resolveRouteName": "全局",
      "lvsStr": "Weight",
      "lvsStrName": "按权重返回地址",
      "note": "",
      "gslbId": "gslb-f33ny0fw94pl",
      "addrPoolId": "pool-fahbasby0kr8",
      "addrPoolName": "永远在线",
      "status": "RUNNING"
    }]
        '''
        page = 1
        params = {"Action": "GetGslbPolicysPage", "regionId": self.region[0], "t": timeStap(), "gslbId": gslb_id,
                  "size": 10}
        api = 'api/networks/gslb'
        method = "GET"
        policys = []
        s_time = time.time()
        while time.time() - s_time < (5 * 60):
            params["page"] = page
            ret = self.send_request(api=api, method=method, **params)
            if ret["code"] != "Network.Success":
                raise "获取GSLB策略失败"
            policys.extend(ret["res"]["data"])
            page += 1
            total = int(ret["res"]["total"])
            if len(policys) >= total:
                break
        return policys

    def GSLB_GetGslbPage(self, count=0):
        '''
        获取GSLB实例列表
        return:
        [{
      "instanceId": "gslb-f33ny0fw94pl",
      "instanceName": "mytest",
      "instanceCode": "gslb.common.normal",
      "userId": "e9e4ef62-47df-4349-bee8-a64254f146b4",
      "regionId": "hz-base-region",
      "regionName": "杭州基地",
      "azoneId": null,
      "realmName": "11.testgslb.com",
      "globalTtl": 10,
      "projectId": "rg092429885444",
      "desc": "test",
      "status": "RUNNING",
      "createTime": "2022-07-13T17:03:54.000+08:00",
      "updateTime": "2022-07-13T17:03:54.000+08:00",
      "deleteTime": null,
      "strCount": 1,
      "instanceOperationInfo": {
        "operationStatus": 2,
        "orderId": 767120964822576900,
        "rentUnit": null,
        "chargeType": 1,
        "productGroupId": null,
        "isThirdProduct": false,
        "payType": "DAY_MONTH",
        "userParentId": "e9e4ef62-47df-4349-bee8-a64254f146b4",
        "azId": "",
        "id": "gslb-f33ny0fw94pl",
        "formalPayTime": 1657703035000,
        "renewType": null,
        "dueTime": null,
        "instanceCloseTime": null,
        "isPayClose": false,
        "az": null,
        "projectName": "default",
        "projectId": "rg092429885444",
        "chargeFlag": 1,
        "note": null,
        "rentCount": null,
        "instanceName": "mytest",
        "regionName": "杭州基地",
        "creatorName": "ZGgmdd",
        "instanceReleaseTime": null,
        "turnFormalTime": null,
        "releaseType": null,
        "instanceLabel": 1,
        "instanceRestartTime": null,
        "productType": "instance",
        "isOld": 0,
        "userParentName": "ZGgmdd",
        "creator": "e9e4ef62-47df-4349-bee8-a64254f146b4",
        "isPay": 1,
        "instanceEndTime": null,
        "instanceParentId": null,
        "updateTime": 1657703034000,
        "originalProjectId": "rg092429885444",
        "userName": "ZGgmdd",
        "instanceStartTime": 1657703035000,
        "closeType": null,
        "userId": "e9e4ef62-47df-4349-bee8-a64254f146b4",
        "instanceDescription": null,
        "productCode": "GSLB",
        "createTime": 1657703035000,
        "regionId": "hz-base-region",
        "isMspProduct": false,
        "subUserId": "e9e4ef62-47df-4349-bee8-a64254f146b4",
        "trialDescription": null
      },
      "instanceOperationType": {
        "specificationClassCode": "gslb.common",
        "componentCode": "gslbInstance",
        "startSize": null,
        "componentName": "全局负载均衡",
        "describe": "通用普通型全局负载均衡",
        "specificationCode": "gslb.common.normal",
        "specificationName": "普通型",
        "endSize": null,
        "componentProperty": {
          "specificationCode": "gslb.common.normal"
        }
      }
    }]
        '''
        params = {"Action": "GetGslbPage", "regionId": self.region[0], "t": timeStap(), "size": 100}
        api = 'api/networks/gslb'
        method = "GET"
        gslbs = []
        page = 1
        s_time = time.time()
        while time.time() - s_time < (5 * 60):
            params["page"] = page
            print(params)
            ret = self.send_request(api=api, method=method, **params)
            if ret["code"] != "Network.Success":
                raise "获取GSLB策略失败"
            gslbs.extend(ret["res"]["data"])
            page += 1
            total = int(ret["res"]["total"])
            if count != 0 and total > 1000:
                total = count
            print(len(gslbs), total)
            if len(gslbs) >= total:
                break
        return gslbs

    def GSLB_CreateAddressPools(self, pool_name="autoname", desc="auto description", hc_type="PING", hc_overtime=3,
                                hc_port=80):
        '''
        创建GSLB 地址池
        healthy check支持PING/TCP/HTTP
        '''
        data = {
            "instanceName": pool_name,
            "desc": desc,
            "hcStatus": 0,
            "hcType": hc_type,
            "hcOvertime": hc_overtime,
            "hcPort": hc_port,
            "hcMethod": None,
            "hcHost": None,
            "hcPath": None,
            "hcStatusCode": None,
            "hcResp": None
        }
        params = {"Action": "CreateAddressPools", "regionId": self.region[0], "t": timeStap()}
        api = 'api/networks/gslb'
        method = "POST"
        ret = self.send_request(api=api, method=method, data=data, **params)
        if ret["code"] != "Network.Success":
            return False
        print("GSLB地址池创建成功")
        return True

    def GSLB_GetAddressesPage(self, pool_id=None):
        '''
        获取地址池中的地址
        :return:
        [{
      "instanceId": "addr-fpmhhgkrtis9",
      "ipAddress": "2.2.2.2",
      "weight": 1,
      "checkType": "Forever_Offline",
      "note": "",
      "addrPoolId": "pool-fpmhhgkrtiru",
      "status": "RUNNING",
      "createTime": "2022-07-14T11:17:14.000+08:00",
      "updateTime": "2022-07-14T11:17:32.000+08:00"
    }]
        '''
        params = {"Action": "GetAddressesPage", "regionId": self.region[0], "t": timeStap(), "size": 10,
                  "addrPoolId": pool_id}
        api = 'api/networks/gslb'
        method = "GET"
        addresses = []
        page = 1
        s_time = time.time()
        while time.time() - s_time < (5 * 60):
            params["page"] = page
            ret = self.send_request(api=api, method=method, **params)
            if ret["code"] != "Network.Success":
                raise "获取GSLB策略失败"
            addresses.extend(ret["res"]["data"])
            page += 1
            total = int(ret["res"]["total"])
            if len(addresses) >= total:
                break
        return addresses

    def GSLB_GetAddressPoolsPage(self):
        '''
        获取GSLB地址池列表
        return:
        [{
      "instanceId": "pool-fpmhhgkrtiru",
      "instanceName": "tet",
      "userId": "e9e4ef62-47df-4349-bee8-a64254f146b4",
      "regionId": "hz-base-region",
      "azoneId": null,
      "desc": "",
      "status": "RUNNING",
      "hcStatus": 1,
      "hcType": null,
      "hcPort": null,
      "hcMethod": null,
      "hcHost": null,
      "hcPath": null,
      "hcStatusCode": null,
      "hcResp": null,
      "hcOvertime": null,
      "addrCount": 1,
      "createTime": "2022-07-14T10:58:55.000+08:00",
      "updateTime": "2022-07-14T10:58:55.000+08:00"
    }]
        '''
        params = {"Action": "GetAddressPoolsPage", "regionId": self.region[0], "t": timeStap(), "size": 10}
        api = 'api/networks/gslb'
        method = "GET"
        pools = []
        page = 1
        s_time = time.time()
        while time.time() - s_time < (5 * 60):
            params["page"] = page
            ret = self.send_request(api=api, method=method, **params)
            if ret["code"] != "Network.Success":
                raise "获取GSLB策略失败"
            pools.extend(ret["res"]["data"])
            page += 1
            total = int(ret["res"]["total"])
            if len(pools) >= total:
                break
        return pools

    def GSLB_CreateAddresses(self, pool_id=None, check_type="Intelligent_Return", ip="1.1.1.1", weight="1",
                             desc="auto description"):
        '''
        给GSLB地址池增加IP地址
        check_type:
        Intelligent_Return:只能返回
        Forever_Online:永远在线
        Forever_Offline:永远离线
        '''
        data = {
            "addrPoolId": pool_id,
            "checkType": check_type,
            "ipAddress": ip,
            "weight": weight,
            "note": desc
        }
        params = {"Action": "CreateAddresses", "regionId": self.region[0], "t": timeStap()}
        api = 'api/networks/gslb'
        method = "POST"
        ret = self.send_request(api=api, method=method, data=data, **params)
        if ret["code"] != "Network.Success":
            return False
        print("创建地址成功")
        return True

    def GSLB_ModifyAddresses(self, pool_id, check_type, addr_id, ip, weight, desc):
        '''
        修改GSLB地址池地址相关信息
        '''
        data = {
            "addrPoolId": pool_id,
            "instanceId": addr_id,
            "checkType": check_type,
            "ipAddress": ip,
            "weight": weight,
            "note": desc
        }
        params = {"Action": "ModifyAddresses", "regionId": self.region[0], "t": timeStap()}
        api = 'api/networks/gslb'
        method = "PUT"
        ret = self.send_request(api=api, method=method, data=data, **params)
        if ret["code"] != "Network.Success":
            return False
        print("修改地址成功")
        return True

    def GSLB_DeleteAddresses(self, pool_id, addr_id):
        '''
        删除GSLB地址池中的地址
        '''
        if not isinstance(addr_id, list):
            addr_id = [addr_id]
        data = {
            "addrPoolId": pool_id,
            "instanceIds": addr_id
        }
        params = {"Action": "DeleteAddresses", "regionId": self.region[0], "t": timeStap()}
        api = 'api/networks/gslb'
        method = "DELETE"
        ret = self.send_request(api=api, method=method, data=data, **params)
        if ret["code"] != "Network.Success":
            return False
        print("删除地址成功")
        return True

    def GSLB_DeleteAddressPools(self, pool_id=None):
        '''
        删除GSLB地址池
        '''
        if not isinstance(pool_id, list):
            pool_id = [pool_id]
        data = {"instanceIds": pool_id}
        params = {"Action": "DeleteAddressPools", "regionId": self.region[0], "t": timeStap()}
        api = 'api/networks/gslb'
        method = "DELETE"
        ret = self.send_request(api=api, method=method, data=data, **params)
        if ret["code"] != "Network.Success":
            return False
        print("删除地址池成功")
        return True
