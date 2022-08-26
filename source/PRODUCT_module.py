# -*- coding: UTF-8 -*-
import jsonpath

from source.locust_methods import Agent_SDN_nolocust, timeStap


class PRODUCT(Agent_SDN_nolocust):
    acount_type = {'YEAR_MONTH': '包年包月', "CHARGING_HOURS": '按小时实时计费', "STREAM_HOUR_HOUR": '按流量付费',
                   "DAY_TRIAL": "免费试用", 'DAY_MONTH': '按日月结'}

    def get_product_price(self, product_name, charge_type='prepaid', order_category='NEW', pay_type="YEAR_MONTH",
                          quantity=1, count=1, instance_id='', product_code='BANDWIDTH_PUBLIC',
                          component_code='Bandwidth', bandwidth=1,
                          unit="month", **kwargs) -> dict:
        '''
        :param product_name:
        :param charge_type:
        :param pay_type:
        :param quantity:
        :param count:
        :param unit:
        :param kwargs:
        :return:{'auth': True, 'code': 'Success', 'message': 'Successful!', 'success': True, 'data': {'totalPrice': 600.0, 'tradePrice': 600.0, 'promotionPrice': 0.0, 'refundPrice': None, 'items': [{'productCode': 'NAT', 'regionId': 'H3C-HZ', 'originalPrice': '600.0', 'costAfterDiscount': '600.0', 'promotionPrice': '0.0', 'promotionDetails': []}], 'promotionDetails': None}}
        '''
        api = 'api/moove/cps/order/price'
        method = 'post'
        data = {"chargeType": charge_type, "orderCategory": order_category}
        if order_category == 'NEW':
            data['products'] = [{"components": [
                {"componentCode": self.component_code,
                 "componentProperty": {"specificationCode": self.specification_code}}],
                "payType": pay_type,
                "productCode": product_name, "quantity": quantity,
                "regionId": self.region[0], "rentCount": count,
                "rentUnit": unit}]
        if order_category == "UPGRADE":
            data["uporDownInstance"] = {"productCode": product_code, "instanceId": instance_id, "components": [
                {"componentCode": component_code,
                 "componentProperty": {"specificationCode": self.specification_code, "bandwidth": bandwidth}}],
                                        "payType": pay_type,
                                        "rentUnit": unit}
            data["promotionIds"] = []
            data["userId"] = self.user_id
        res = self.send_request(api, method, data, **kwargs)
        return {'totalPrice': res['data']['tradePrice'], 'promotionPrice': res['data']['promotionPrice'],
                'refundPrice': res['data']['refundPrice']}

    def getUserProjectList(self, productCode, **kwargs):
        """
        :param productCode:['BANDWIDTH_PUBLIC']
        :param kwargs:
        :return:    status: true
                    code: 0
                    res: [{resource_project_id: "1523498079754387456", resource_project_name: "default", enabled: 1}]
                    auth: true
                    msg: null
        """
        api = 'api/moove/cps/projects'
        method = 'get'
        action = 'getUserProjectList'
        data = {}
        res = self.send_request(api, method, data, Action=action, productCode=productCode,
                                regionId=self.region_dict[self.target_region_name],
                                t=timeStap(), **kwargs)
        return res

    def project_id_(self, projectId=None, productCode='', name='default'):
        res = self.getUserProjectList(productCode)
        resource_project_id = jsonpath.jsonpath(res, '$.res..resource_project_id')
        resource_project_name = jsonpath.jsonpath(res, '$.res..resource_project_name')
        try:
            index = resource_project_name.index(name)
            if index >= 0:
                projectId = resource_project_id[index]
        except ValueError:
            projectId = resource_project_id[0]
        except Exception as e:
            raise e
        return projectId
