from source.locust_methods import Agent_SDN_nolocust, timeStap


class VIP(Agent_SDN_nolocust):
    def VIP_describe_for_eip(self, **kwargs):
        """
        :param kwargs:
        :return:{"res":{["vip-b16lh1ls8wa2","instanceName":"yz-hip","vpcId":"vpc-bsjisgyrju6s","ipAddress":"172.16.1.36","ipProtocol":null,"regionId":"H3C-HZ","azoneId":"H3C-HZ-AZ1","userId":"9d367b04-a5b9-4223-b69f-c961b568549f","subnetId":"3bba7d1cb2c54e71a322346a7daa160d","createTime":"2021-07-12T17:14:00.000+0800","eip":null,
        ,"msg":"查询可绑定EIP的虚IP成功","code":"Network.Success"}
        """
        api = 'api/networks/vip'
        action = 'DescribeVipForEip'
        method = 'get'
        data = {}
        res = self.send_request(api, method, data, Action=action, azoneId=self.azone_id,
                                regionId=self.region_dict[self.target_region_name],
                                t=timeStap(), **kwargs)
        # res['res'][0]['instanceId']
        return res
