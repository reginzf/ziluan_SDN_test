# -*- coding: UTF-8 -*-


import ipaddress
import json
import logging
import os
import random
import time
import types
from random import randint

import jsonpath
import urllib3
from locust import SequentialTaskSet, task, HttpUser, between

from source import VPC, EIP, ORDER, ECS, NAT, VPCP, CFW, CCN, BFW, func_instanceName, DNS
from source.exceptions import HttpCodeException
from source.monkey_patch import send_request

a = ['ipv4', 'ipv6']
ip_types = {'ipv4': lambda: str(ipaddress.IPv4Address(random.randint(0, 4294967295))),
            'ipv6': lambda: str(ipaddress.IPv6Address(random.randint(0, 340282366920938463463374607431768211455)))}

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logging.basicConfig(level=logging.DEBUG,
                    filename='logs\\{}.log'.format(os.path.basename(__file__).split('.py')[0]),
                    filemode='w',
                    format='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s')
LOCUST_REQUEST_PARAMS = {'name': None, 'catch_response': False, 'params': {}, 'files': '', 'auth': None,
                         'timeout': None, 'allow_redirects': True, 'proxies': '', 'stream': False,
                         'cert': None}

from threading import Lock

matrix = Lock()
global location
location = 0


def send_request_(self, api, method, data={}, **kwargs) -> dict:
    if self.request_wait_time:
        time.sleep(self.request_wait_time)
    method = method.upper()
    if self.token:
        self.headers['x-auth-token'] = self.token
    if self.region:
        self.headers['x-auth-cloud-Id'] = self.region[0]
    if method == 'POST' and data:
        self.headers['Content-Length'] = str(len(str(data)))
    url = '{protocol}://{host}:12011/{api}'.format(protocol=self.protocol, host=self.host, api=api)

    if kwargs:
        try:
            for key in LOCUST_REQUEST_PARAMS:
                if kwargs.get(key, None) and kwargs.get(key) != LOCUST_REQUEST_PARAMS[key]:
                    LOCUST_REQUEST_PARAMS[key] = kwargs[key]
                    kwargs.pop(key)


        except Exception as e:
            raise e
        url = "{url}?{params}".format(url=url, params='&'.join(
            ["{key}={value}".format(key=key, value=value) for key, value in kwargs.items()]))
    try:
        self.logger.info(
            msg='url:{}\ndata:{}\nheader:{}\ncookies:{}'.format(url, data, self.headers, self.session.cookies))

    except AttributeError:
        pass
    except Exception as e:
        raise e
    response = self.session.request(method, url, data=json.dumps(data), headers=self.headers,
                                    verify=False, cookies=self.session.cookies, **LOCUST_REQUEST_PARAMS)
    # 处理Set-cookie
    try:
        set_cookies = response.headers.get('Set-Cookie', None)
        if set_cookies:
            self.session.cookies.update(set_cookies)
    except:
        pass

    if response.status_code != 200:
        info = '请求失败:code:{},url:{},method:{},data{},response:{}'.format(response.status_code, url, method, data,
                                                                         response.content)
        self.logger.info(info)
        raise HttpCodeException(info, response.status_code)
    res = json.loads(response.content.decode("utf-8"))
    self.logger.info(msg=response.text)
    if self.re_auth:  # token 超期后自动认证
        try:
            msg = res['msg']
            if msg == 'token无效':
                self.logger.info(msg='当前token无效，尝试重新登录后重发')
                self.token = ''
                self.headers.pop('x-auth-token')
                self.headers.pop('Cookie')
                self.login(self.username, self.password)
                res = self.send_request(api, method, data, **kwargs)
        except:
            pass

    return res


class T_VPC(SequentialTaskSet, EIP, ORDER, ECS, NAT, VPCP, CFW, CCN, BFW, VPC, DNS):
    def on_start(self):
        # 打猴子补丁
        super(EIP, self).__init__()
        self.logger = logging.getLogger()
        self.temp_ = self.send_request
        self.send_request = types.MethodType(send_request, self)

        # self.setup(web_user="aa66378185f7afa4", web_password="ab6d2d968af9a9a5a7bfba", sql_host='172.25.50.25',
        #            sql_user='moove', sql_password='unic-moove', sql_port='3306', username='testcase')
        self.setup(web_user="b071238183e5a8", web_password="bf67299c88a7eef2", sql_host='172.25.50.25',
                   sql_user='moove', sql_password='unic-moove', sql_port='3306', username='nrgtest')

        # 卸载补丁
        self.send_request = self.temp_
        self.session = self.client
        # 默认发一个request后等待0.2s
        # self.request_wait_time = 0.2
        self.projectId = self.project_id_(productCode='DNS')
        self.request_wait_time = 0
        self.ptrs = self.get_all_ptr()

    # @task
    def create_ptr(self):
        ip_type = random.choice(a)
        ipAddress = ip_types[ip_type]()
        self.DNS_CreateLDnsPtr(ipAddress=ipAddress, ipType=ip_type,
                               cname=func_instanceName(random.randint(5, 10)) + '.' + func_instanceName(
                                   random.randint(5, 10)), description=func_instanceName(randint(1, 64)),
                               ttl=randint(300, 2147483647), projectId=self.projectId, name='create_ptr')

    # @task
    def delete_ptr(self):
        global location
        matrix.acquire()
        start = location
        if location < len(self.ptrs):
            if start + 100 < len(self.ptrs):
                end = start + 100
                location += 100
            else:
                end = len(self.ptrs)
                location = len(self.ptrs)
        else:
            return
        matrix.release()

        self.DNS_DeleteLDnsPtr(self.ptrs[start:end], name='delete_ptr')

    def get_all_ptr(self):
        total = jsonpath.jsonpath(self.DNS_GetLDnsPtrPage(), '$.res.total')[0]
        page = 1
        size = 100
        ptrs = []
        while page * size <= total:
            ptrs.extend(jsonpath.jsonpath(self.DNS_GetLDnsPtrPage(page=page, size=size, name='get_ptr'),
                                          '$.res.data..instanceId'))
            page += 1
        return ptrs

    @task
    def create_cfw_policy(self):
        for i in range(10):
            self.CFW_CreateCfwScp_random('cfw-f9aaas6idxla', network_strict=True, name='createCfwScp')



T_VPC.send_request = send_request_


class TEST_PLACE(HttpUser):
    tasks = [T_VPC]
    wait_time = between(0.001, 0.002)


def gen_ipv4_target():
    return [str(ipaddress.IPv4Address(random.randint(0, 4294967295))) for _ in range(random.randint(1, 50))]


def gen_ipv6_target():
    return [str(ipaddress.IPv6Address(random.randint(0, 340282366920938463463374607431768211455))) for _ in
            range(random.randint(1, 50))]


def gen_cname_target():
    return func_instanceName(random.randint(5, 10)) + '.' + func_instanceName(random.randint(5, 10))


if __name__ == '__main__':
    os.system('locust -f aaa1.py --web-host=127.0.0.1 ')
