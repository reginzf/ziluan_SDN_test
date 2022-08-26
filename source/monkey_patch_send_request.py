# -*- coding: UTF-8 -*-
import time
import json
from backend.log_hander import logger
def send_request(self, api, method, data, **kwargs) -> dict:
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
            self.session.cookies.update(kwargs['cookies'])
            kwargs.pop('cookies')
        except:
            pass
        url = "{url}?{params}".format(url=url, params='&'.join(
            ["{key}={value}".format(key=key, value=value) for key, value in kwargs.items()]))
    try:
        logger.info(
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
        info = '请求失败:code:{},url:{},method:{},data{}'.format(response.status_code, url, method, data)
        logger.info(info)
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
    logger.info(msg=response.text)
    return res
