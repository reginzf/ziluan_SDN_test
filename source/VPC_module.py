# -*- coding: UTF-8 -*-
import ipaddress
import threading
import time

from source.locust_methods import Agent_SDN_nolocust, timeStap


class VPC(Agent_SDN_nolocust):
    def VPC_create(self, name, cidr='192.0.0.0/16', subnet_name='', subnet_cidrblock='192.0.0.0/24', gateway_ip=None,
                   **kwargs):
        '''
        :param name:
        :param cidr:
        :param subnet_name:
        :param subnet_cidrblock:
        :param gateway_ip:
        :return:{'res': {'subnetId': [''], 'vpcId': 'vpc-bsjivjghu09a'}, 'msg': '创建指令已下发', 'code': 'Network.Success'}
        '''
        if not gateway_ip:
            gateway_ip = ipaddress.IPv4Address(subnet_cidrblock.split('/')[0]) + 1
        if not subnet_name:
            subnet_name = name
        if cidr != '192.0.0.0/16' and subnet_cidrblock == '192.0.0.0/24':
            subnet_cidrblock = "{}/{}".format(ipaddress.IPv4Address(cidr.split('/')[0]), 24)
        api = 'api/networks/vpc'
        action = 'CreateVpc'
        method = 'post'

        data = {"azoneId": self.azone_id, "openIpV6": "", "vpcName": "{}".format(name),
                "vpcCidrBlock": "{}".format(cidr),
                "subnetName": "{}".format(subnet_name), "subnetCidrBlock": "{}".format(subnet_cidrblock),
                "instanceCode": "vpc.standard",
                "gatewayIp": "{}".format(gateway_ip), "privateDnsServers": []}
        res = self.send_request(api, method, data, Action=action, regionId=self.region_dict[self.target_region_name],
                                t=timeStap(), **kwargs)
        return res

    def VPC_create_subnet(self, vpc_instance, name, cidr='192.168.0.0/24', gatewayIp='192.168.0.1',
                          private_dns_servers=[], azoneId='', open_ip_v6=False, **kwargs):
        '''
        :param vpc_instance:
        :param name:
        :param cidr:
        :param gatewayIp:
        :param privateDnsServers:
        :param kwargs:
        :return: {"res":{"Name":"a2","Id":"cd6529d323ca4aec855ff45216ede58b","Cidr":"192.168.1.0/24","GatewayIp":"192.168.1.1","IPv6Cidr":"","IPv6GatewayIp":"","AvailableZone":"","IpAssignedCount":0,"IpTotalCount":250,"VpcId":"vpc-bsjixihlwojd","AllocationPool":{"End":"192.168.1.251","Start":"192.168.1.2"},"PrivateDnsServers":[],"BindResources":None,"EnableIPv6":False,"CrossZone":True},
        "msg":"操作成功","code":"Network.Success"}
        '''
        api = 'api/networks/vpc'
        method = 'post'
        action = 'CreateSubnet'
        azoneId = self.azone_id if azoneId == '' else azoneId
        if gatewayIp == '192.168.0.1' and cidr != '192.168.0.0/24':
            gatewayIp = (ipaddress.IPv4Address(cidr.split('/')[0]) + 1).__str__()
        data = {"azoneId": azoneId, "name": name, "cidr": cidr,
                "gatewayIp": gatewayIp, "privateDnsServers": private_dns_servers}
        res = self.send_request(api, method, data, Action=action, regionId=self.region_dict[self.target_region_name],
                                vpcId=vpc_instance,
                                openIpV6=open_ip_v6, t=timeStap(), **kwargs)
        return res

    def VPC_describe(self, vpcId=None, name='', page=1, size=100, **kwargs):
        '''
        :param kwargs:vpcId: str , name:str
        :return:{"res":[{"userId":"9d367b04-a5b9-4223-b69f-c961b568549f","cidr":"192.168.0.0/16","instanceId":"vpc-bsjis4m4wi3r","instanceName":"nrgMVVKEXLFAJ","instanceCode":"vpc.standard","status":"RUNNING","regionId":"H3C-HZ","subnets":[{"name":"nrgtest0103","id":"5d0db0f8c3a2406e84b7bb1def425fbd","cidr":"192.168.0.0/24","azoneId":"","gatewayIp":"192.168.0.1","ipV6Cidr":"","ipV6GatewayIp":"","allocationPool":{"end":"192.168.0.251","start":"192.168.0.2"},"privateDnsServers":[],"bindResources":[],"ipAssignedCount":0,"ipTotalCount":250,"hasIpV6":False,"isCrossZone":True}],"createTime":"2021-06-23T10:37:14.000+0800"}],"msg":"操作成功","code":"Network.Success"}
        '''
        ARGS = ['vpcId', 'name']
        for arg in ARGS:
            temp = locals().get(arg, None)
            if temp:
                kwargs[arg] = temp
        api = 'api/networks/vpc'
        method = 'get'
        action = 'DescribeVpc'
        data = {}
        res = self.send_request(api, method, data, Action=action, regionId=self.region_dict[self.target_region_name],
                                t=timeStap(), **kwargs)
        return res

    def VPC_describe_subnet(self, vpc_id, **kwargs):
        '''
        :param vpc_id: str
        :param kwargs:
        :return:{"res":[{"name":"nrgtest0103","id":"d258963da53d477db622b4f2d90cd832","cidr":"192.168.0.0/24","azoneId":"","gatewayIp":"192.168.0.1","ipV6Cidr":"","ipV6GatewayIp":"","allocationPool":{"end":"192.168.0.251","start":"192.168.0.2"},"privateDnsServers":[],"bindResources":[],"ipAssignedCount":0,"ipTotalCount":250,"hasIpV6":False,"isCrossZone":True}],"msg":"操作成功","code":"Network.Success"}
        '''
        api = 'api/networks/vpc'
        action = 'DescribeSubnet'
        method = 'get'
        data = {}
        res = self.send_request(api, method, data, Action=action, vpcId=vpc_id,
                                regionId=self.region_dict[self.target_region_name], t=timeStap(),
                                **kwargs)
        return res

    def VPC_delete_subnet(self, vpc_id, subnet_id, **kwargs):
        '''
        :param vpc_id:
        :param subnet_id:
        :param kwargs:
        :return:{"res":None,"msg":"操作成功","code":"Network.Success"}
        '''
        api = 'api/networks/vpc'
        method = 'delete'
        data = {}
        action = 'DeleteSubnet'
        res = self.send_request(api, method, data, Action=action, regionId=self.region_dict[self.target_region_name],
                                vpcId=vpc_id,
                                subnetId=subnet_id, t=timeStap(), **kwargs)
        return res

    def VPC_delete(self, instance_id, **kwargs):
        '''
        :param instance_id:
        :param kwargs:
        :return:{"res":None,"msg":"操作成功","code":"Network.Success"}
        '''
        api = 'api/networks/vpc'
        action = 'DeleteVpc'
        method = 'delete'
        data = {}
        res = self.send_request(api, method, data, Action=action, regionId=self.region_dict[self.target_region_name],
                                instanceId=instance_id,
                                t=timeStap(), smsCode='', **kwargs)
        return res

    def VPC_delete_vpc_can_delete(self, interval=100, **kwargs):
        '''
        :kwargs: name:str ,vpc_id:str
        :param interval: 多少个vpc 起一个删除进程
        :return: None
        '''
        vpcs = self.VPC_describe(**kwargs)['res']
        print(vpcs)
        temp = -1
        for i in range(len(vpcs)):
            if vpcs[i]['instanceName'] == 'nrg33':
                temp = i
        if temp != -1:
            vpcs.pop(temp)
        vpc_nums = len(vpcs)
        start, end = 0, min(interval, vpc_nums)
        thread_nums = vpc_nums // interval + 1
        threads = []

        def delete_thread(start, end):
            for i in range(start, end):
                subnets = self.VPC_describe_subnet(vpcs[i]['instanceId'])
                if subnets['res']:
                    for subnet in subnets['res']:
                        subnet_id = subnet['id']
                        try:
                            self.VPC_delete_subnet(vpcs[i]['instanceId'], subnet_id)
                        except:
                            pass
                try:
                    self.VPC_delete(vpcs[i]['instanceId'])
                except:
                    pass

        for i in range(thread_nums):
            threads.append(threading.Thread(target=delete_thread, args=(start, end,)))
            start += interval
            end += interval
            if start > vpc_nums: break
            if end > vpc_nums:
                end = vpc_nums - 1

        for t in threads:
            t.start()
            t.join()

    def VPC_get_vpcid_by_vpc_name(self, name=None):
        '''
        根据VPC名字查找VPCid
        '''
        api = 'api/networks/vpc'
        method = 'GET'
        params = {"Action": "DescribeVpcPage", "regionId": self.region[0], "t": str(int(time.time() * 1000)),
                  "size": 10}
        if name is not None:
            params["name"] = name
        page = 1
        vpces = []
        s_time = time.time()
        while time.time() - s_time < (5 * 60):
            params["page"] = page
            ret = self.send_request(api, method, **params)
            vpc_list = ret["res"]["data"]
            vpces.extend(vpc_list)
            total = int(ret["res"]["total"])
            if len(vpces) >= total:
                break
            page += 1
        return vpces

    def VPC_DescribeVpcTopology(self, vpc_id=None):
        '''
        获取VPC拓扑
        '''
        api = 'api/networks/vpc'
        method = "GET"
        params = {"Action": "DescribeVpcTopology", "vpcId": vpc_id, "regionId": self.region[0], "t": timeStap()}

        return self.send_request(api=api, method=method, **params)
