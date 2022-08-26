# -*- coding: UTF-8 -*-
from typing import List

from source.locust_methods import Agent_SDN_nolocust, timeStap, jsonpath


class ORDER(Agent_SDN_nolocust):
    def get_order_product(self, order_id, **kwargs):
        '''

        :param order_id:
        :param kwargs:
        :return: {"status": True, "auth": True, "code": "0", "res": {"id": "198371706040015715", "orderNo": "P41809119219844",
                                                            "userId": "9d367b04-a5b9-4223-b69f-c961b568549f",
                                                            "userName": "zlltest", "orderCategory": "NEW",
                                                            "orderStatus": "UNPAID",
                                                            "productCategory": "BANDWIDTH_PUBLIC",
                                                            "productCode": "BANDWIDTH_PUBLIC", "productName": "弹性公网IP",
                                                            "chargeType": "prepaid", "payType": "YEAR_MONTH",
                                                            "payTypeName": "包年包月", "productRegionId": "H3C-HZ",
                                                            "productRegionName": "H3C-HZ", "totalPrice": 23.0000,
                                                            "promotionAmount": 0.0000, "finalPrice": 23.0000,
                                                            "payTime": None, "createTime": 1625647131000,
                                                            "updateTime": 1625647131000, "dueTime": 1625733531000,
                                                            "cancelType": None, "agentPaid": False,
                                                            "refundReason": None, "orderLabel": "FORMAL",
                                                            "mooveOrder": True, "offlinePayChannel": False,
                                                            "trialEndTime": None, "businessName": "曾璐璐",
                                                            "businessMobile": "11111111111", "items": [
                {"productCode": "BANDWIDTH_PUBLIC", "productName": "弹性公网IP", "chargeType": "prepaid",
                 "payType": "YEAR_MONTH", "payTypeName": "包年包月", "quantity": 1,
                 "productDescription": "{\"name\":\"NetFPxLMdOivA\",\"billingMethod\":\"YEAR_MONTH\",\"conf\":{\"地域\":\"H3C-HZ\",\"线路选择\":\"BGP(多线)\",\"带宽\":\"1Mbps\",\"计费模式\":\"包年包月\"}}",
                 "productRentCount": 1, "productRentUnit": "month", "rentUnit": "month", "rentCount": 1,
                 "productStartTime": 1625647131000, "productEndTime": 1628352000000, "originalPrice": 23.0000,
                 "finalPrice": 23.0000, "promotionPrice": 0.0000, "regionId": "H3C-HZ", "regionName": "H3C-HZ",
                 "azId": "H3C-HZ-AZ1"}]}, "msg": None}
        '''
        api = 'api/transaction-core/uco/v1/transaction/getOrderAndProduct'
        method = 'get'
        data = {}
        res = self.send_request(api, method, data, orderId=order_id, t=timeStap(), **kwargs)
        # finalPrice = res['res']['finalPrice']
        return res

    def get_order(self, page=1, size=100, productCategory='', orderCategory='', orderStatus='', orderNo='', startTime=0,
                  endTime=0, **kwargs) -> (List, List, int):
        """
        :param page: int
        :param size: int
        :param productCategory: str
        :param orderCategory: str
        :param orderStatus: str
        :param orderNo: int
        :param startTime: int
        :param endTime: int
        :param kwargs: {'status': True, 'auth': True, 'code': '0', 'res':{'page': 1, 'size': 100, 'totalCount': 102, 'totalPages': None, 'list':
        [{'id': '198371328082870348', 'userId': '9d367b04-a5b9-4223-b69f-c961b568549f', 'orderNo': 'P41413982231366', 'userName': 'zlltest', 'orderStatus': 'UNPAID', 'orderCategory': 'NEW', 'payType': 'YEAR_MONTH', 'payTypeName': '包年包月', 'isOffine': None, 'productCategory': 'BANDWIDTH_PUBLIC', 'itemCount': None, 'isInvoice': None, 'payTime': None, 'totalPrice': 23.0, 'couponAmount': 0.0, 'promotionAmount': 0.0, 'promotionRule': None, 'finalPrice': 23.0, 'paidAmount': None, 'productRegionId': 'H3C-HZ', 'productRegionName': 'H3C-HZ', 'cancelType': None, 'createTime': 1625299264000, 'updateTime': 1625299264000, 'refundOrderId': None, 'refundReason': None, 'instanceId': None, 'note': None, 'chargeType': 'prepaid', 'orderLabel': 'FORMAL', 'deliverStatus': None, 'deliverTime': None}],
        'msg': None}
        :return:
        """
        for key, value in locals().items():
            if key == 'kwargs' or key == 'self':
                continue
            if value:
                kwargs[key] = value
        api = 'api/transaction-core/uco/v1/transaction'
        method = 'get'
        data = {}
        action = 'GetOrderList'

        res = self.send_request(api, method, data, Action=action, t=timeStap(), **kwargs)
        order_ids = jsonpath.jsonpath(res, "$.res.list..id")
        order_nos = jsonpath.jsonpath(res, "$.res.list..orderNo")
        total_page = int(jsonpath.jsonpath(res, "$.res.totalPages")[0])
        return order_ids, order_nos, total_page

    def get_all_orders(self, page=1, size=100, productCategory='', orderCategory='', orderStatus='', orderNo='',
                       startTime=0,
                       endTime=0, **kwargs) -> (List, List):
        for key, value in locals().items():
            if key == 'kwargs' or key == 'self':
                continue
            if value:
                kwargs[key] = value
        order_ids, order_nos, total_page = self.get_order(**{str(key): value for key, value in kwargs.items()})
        if total_page >= 2:
            for i in range(2, total_page + 1):
                kwargs["page"] = i
                ids, nos, n_p = self.get_order(**{str(key): value for key, value in kwargs.items()})
                order_ids.extend(ids)
                order_nos.extend(nos)
        self.logger.info(msg=order_ids)
        return order_ids, order_nos

    def pay_order(self, order_id, pay_amount, pay_channel='WALLET', **kwargs):
        '''
        :param order_id:
        :param pay_channel:
        :param pay_amount:
        :param kwargs:
        :return:{"status":True,"auth":True,"code":"0","res":{"tradeNo":"198370589348498969","orderId":"198370606528376045","orderNo":"P40640888123189","thirdPartyPaymentChannel":None,"status":"SUCCESS","thirdPayUrl":None},"msg":None}
        '''
        api = 'api/payment-gateway/uco/paymentgateway/web/payGw'
        action = 'payOrder'
        method = 'post'
        data = {"channelDetailList": [{"addition": "", "payAmount": pay_amount, "payChannel": pay_channel}],
                "orderId": order_id, "remark": "{\"token\":\"%s\"}" % self.token}
        res = self.send_request(api, method, data, Action=action, t=timeStap(), **kwargs)
        return res

    def approve_order(self, order_id, **kwargs):
        """
        提交审批
        :param order_id:
        :param kwargs:
        :return:
        """
        api = 'api/transaction-core/uco/v1/transaction/approveOrder'
        method = 'get'
        data = {}
        res = self.send_request(api, method, data, orderId=order_id, t=timeStap(), **kwargs)
        return res

    def cancel_order(self, orderId, **kwargs):
        """
        :return:{"status":true,"auth":true,"code":"0","res":{"withdraw":true},"msg":null}
        """
        api = 'api/transaction/transaction'
        method = 'patch'
        data = {}
        res = self.send_request(api, method, data, Action='CancelOrder', orderId=orderId, t=timeStap(), **kwargs)
        return res
