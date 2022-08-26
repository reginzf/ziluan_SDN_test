from source.locust_methods import Agent_SDN_nolocust, timeStap


class VM(Agent_SDN_nolocust):
    def VM_bind_eip(self):
        pass

    def get_vm_list(self, **kwargs):
        """
        可搜索的key:status instanceName eipAddr tags
        """
        api = 'api/iam/ecs/instances'
        method = 'get'
        data = {}
        action = "DescribeEcs"
        res = []
        page = 1
        while True:
            try:
                temp = self.send_request(api, method, data, Action=action, t=timeStap(), size=100,
                                         page=page, **kwargs)

                res.append(temp["res"]["list"])
                # logging.info(msg='page{}的vm为:'.format(page))
                page += 1
            except Exception:
                break
        return res

    def _vm_bind_eip(self, vm, eip):
        api = 'api/networks/eip'
        method = 'put'
        action = 'AssociateEip'
        data = {}
        res = self.send_request(api, method, data, action=action, regionId=eip['regionId'], eipId=eip['instanceId'],
                                parentType='ECS', parentId=vm['instanceId'], portId=vm["eniId"])

        return res

    def _vm_unbind_eip(self, vm, eip):
        api = 'api/networks/eip'
        method = 'put'
        action = 'UnassociateEip'
        data = {}
        res = self.send_request(api, method, data, action=action, regionId=eip['regionId'], eipId=eip['instanceId'],
                                parentId=vm['instanceId'], portId=vm["eniId"])
        return res
