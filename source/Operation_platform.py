# -*- coding: UTF-8 -*-
import json
import logging
import time

from requests import session

from source.locust_methods import timeStap


class Operation(object):
    def __init__(self, host):
        self.host = host
        self.token = None
        self.request_wait_time = None
        self.session = session()
        self.re_auth = False
        self.logger = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36',
            'Origin': 'http://{host}:12008'.format(host=self.host),
            'Referer': 'http://{host}:12008'.format(host=self.host),
            'Cookie': 'loginState=true',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Content-Type': 'application/json;charset=UTF-8',
            'Content-Length': 0,
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        }

    def login(self, username, password, **kwargs):
        api = 'api/admin/v1/user/login'
        method = 'post'
        data = {"email": username, "password": password, "ip": "223.93.141.226",
                "city": "CHINA"}
        res = self.send_request(api, method, data, **kwargs)
        res = res['res']
        try:
            self.token = res['token']
            self.username = username
            self.password = password

            self.logger.info('登录成功，token：{}'.format(self.token))

        except Exception:
            self.logger.info('登录失败')
            return

    def send_request(self, api, method, data, **kwargs) -> dict:
        if not self.logger: self.logger = logging
        if self.request_wait_time:
            time.sleep(self.request_wait_time)
        method = method.upper()
        if self.token:
            self.headers['x-auth-token'] = self.token
            self.headers['Cookie'] = 'loginState=true'

        if method == 'POST' and data:
            self.headers['Content-Length'] = str(len(str(data)))
        url = 'http://{host}:12008/{api}'.format(host=self.host, api=api)

        if kwargs:
            try:
                self.session.cookies.update(kwargs['cookies'])
                kwargs.pop('cookies')
            except:
                pass
            url = "{url}?{params}".format(url=url, params='&'.join(
                ["{key}={value}".format(key=key, value=value) for key, value in kwargs.items()]))
        try:
            self.logger.info(
                msg='url:{}\ndata:{}\nheader:{}\ncookies:{}'.format(url, data, self.headers, self.session.cookies))
            response = self.session.request(method, url, data=json.dumps(data), headers=self.headers,
                                            verify=False, cookies=self.session.cookies)
        except AttributeError as e:
            raise e
        # 处理Set-cookie
        try:
            set_cookies = response.headers['Set-Cookie']
            self.session.cookies.update(set_cookies)

        except:
            pass

        if response.status_code != 200:
            info = '请求失败:code:{},url:{},method:{},data{},response:{}'.format(response.status_code, url, method, data,
                                                                             response.content)
            self.logger.info(info)
            raise Exception(info)
        res = json.loads(response.content.decode("utf-8"))
        if self.re_auth:  # token 超期后自动认证
            try:
                msg = res['msg']
                if msg == 'token无效':
                    self.login(self.username, self.password)
                    res = self.send_request(api, method, data, **kwargs)
            except:
                pass
        self.logger.info(msg=response.text)
        return res

    def Operation_destroy(self, instanceIds: list, **kwargs):
        """
        :param instanceIds:需要释放的实例
        :return:{"status":true,"auth":true,"code":"0","res":"管理员释放实例操作成功!","msg":null}
        """
        api = 'api/instance-core/uco/v1/instance/getway/destroyOperationByAdminNew'
        method = 'post'
        data = {"instanceIds": instanceIds}
        res = self.send_request(api, method, data, **kwargs)
        return res

    def Operation_restart(self, instanceIds: list, chargeType=0, instanceEndTime=30, **kwargs):
        """
        :param instanceIds:
        :param chargeType:
        :param instanceEndTime: 默认增加30天
        :return:{"status":true,"auth":true,"code":"0","res":[],"msg":null}
        """
        api = 'api/instance-core/uco/v1/instance/getway/restartByAdminNew'
        method = 'post'
        instanceEndTime = timeStap() + instanceEndTime * 86400000
        data = {"instanceIds": instanceIds, "chargeType": chargeType, "instanceEndTime": instanceEndTime}
        res = self.send_request(api, method, data, **kwargs)
        return res
