# -*- coding: UTF-8 -*-
import json
import os
import random
import time
from functools import wraps
from random import randint

import json5
import jsonpath
from requests import session

from backend.log_hander import logger
from source.exceptions import HttpCodeException
from source.sql_methods import SQL

global config_data
config_data = None


class Base(object):
    # 共有的方法、登陆、sql啥的放这里
    def send_request(self, api, method, data, **kwargs):
        pass

    def setup(self, web_user, web_password, sql_host, sql_user, sql_password, sql_port=3306, username=''):
        self.login(web_user, web_password)
        if type(sql_port) != int:
            try:
                sql_port = int(sql_port)
            except:
                raise TypeError('sql_port类型错误！')

        self.sql(sql_host, sql_user, sql_password, port=sql_port)
        self.get_region()
        self.get_azone_id()
        self.user_id = self.get_user_id(name=username)

    def sql(self, host, user, password, port=None):
        self.c_sql = SQL(host, user, password, port)

    def login(self, username, password, **kwargs):
        api = 'api/user/pco/user/v1/login'
        method = 'post'
        data = {"userName": username, "password": password, "userDomainType": "ordinary"}
        self.username = username
        self.password = password

        res = self.send_request(api, method, data, t=timeStap(), **kwargs)
        # res = send_request(self, api, method, data, t=timeStap(), **kwargs)
        try:
            self.token = res['res']['token']
            logger.info(msg='登陆成功,token:{}'.format(self.token))
        except Exception as e:
            logger.info(msg="获取token失败:response:{}".format(res))
            raise e
        # 获取其他参数,有就有，没有拉到后面也用不到
        try:
            res = res['res']
            self.user_id = res['userId']
            self.cmpUserId = res['cmpUserId']
        except:
            pass

    def get_region(self):
        api = 'api/user/pco/user/v1/users/region'
        method = 'get'
        data = {}
        res = self.send_request(api, method, data, t=timeStap())
        self.region = jsonpath.jsonpath(res, '$.res..id')
        self.region_name = jsonpath.jsonpath(res, '$.res..regionName')
        self.region_dict = {}
        self.region_dict.update(zip(self.region_name, self.region))

    def get_azone_id(self):
        db = 'resource_core'
        table = 'azone'
        cows = ['azone_id']
        res = self.c_sql.query(db, table, cows, region_id=self.region[0])
        try:
            self.azone_id = res[0]['azone_id']
            logger.info(msg='获取azone_id成功,azone_id:' + self.azone_id)
        except Exception as e:
            logger.info(msg='获取azone 失败')
            raise e

    def get_user_id(self, name):
        db = 'tenant-core'
        table = 'user'
        cows = 'id'
        res = self.c_sql.query(db, table, cows, name=name)
        try:
            user_id = res[0]['id']
            logger.info(msg='获取user_id成功,user_id:' + self.user_id)
        except Exception as e:
            logger.info(msg="获取user_id失败")
            raise e
        return user_id

    # def get_region_id(self, **kwargs): // 废弃 2022-05-11 宁瑞庚
    #     """
    #     status: true
    #     auth: true
    #     code: "0"
    #     res: [{organ_id: "c68f5f72-5550-4bec-aeff-f24d723805b7", organ_name: "默认组织",…},…]
    #     0: {organ_id: "c68f5f72-5550-4bec-aeff-f24d723805b7", organ_name: "默认组织",…}
    #     organ_id: "c68f5f72-5550-4bec-aeff-f24d723805b7"
    #     organ_name: "默认组织"
    #     project_id: "53879d9f-9b8f-4e75-a3fd-330854dac1dc"
    #     project_name: "默认项目"
    #     post_id: "2"
    #     post_name: null
    #     regions: [{id: "cd-test-region", cloudName: "cd-test-region", regionName: "cd-test-region",…}]
    #     msg: null
    #     """
    #     api = 'api/tenant/v1/basic/user/organ/region'
    #     method = 'post'
    #     data = {}
    #     res = self.send_request(api, method, data, **kwargs)
    #     organ_ids = jsonpath.jsonpath(res, '$.res..organ_id')
    #     project_ids = jsonpath.jsonpath(res, '$.res..project_id')
    #     return organ_ids, project_ids

    # def get_parent_rgList(self, **kwargs) -> list:   // 废弃 2022-05-09 宁瑞庚
    #     '''
    #     :param kwargs:
    #     :return:{'code': '0', 'msg': '操作成功', 'res': [{'id': 'rg-bsjisgyrju5v', 'name': '默认资源组', 'identity': 'default', 'isDeleted': 0, 'resourceNum': 2406, 'iamUserNum': None}],
    #     'auth': True, 'status': True}
    #     '''
    #     api = 'api/iam/ucp'
    #     method = 'get'
    #     data = {}
    #     action = 'getParentRgList'
    #     temp = self.send_request(api, method, data, Action=action, regionId=self.region_dict[self.target_region_name], t=timeStap(), **kwargs)
    #     try:
    #         res = temp['res']
    #     except KeyError as e:
    #         self.logger.info(msg='获取资源组失败:{}'.format(temp))
    #         raise e
    #         return res


class Agent_SDN_nolocust(Base):
    # 不期望请求被locust统计到使用这个类
    request_wait_time = 0
    token = ''
    region = []
    headers = {}

    def __init__(self, *args, **kwargs):
        data = self.get_config()
        self.cfg = data['ziluan']
        self.host = self.cfg['ip_addr']
        self.protocol = self.cfg['protocol']
        self.target_region_name = self.cfg.get('target_region_name', None)
        self.token = ''
        self.url = self.cfg['protocol'] + "://" + self.cfg['ip_addr'] + ":" + self.cfg['port']
        self.headers = {'Host': '{}:12011'.format(self.host), 'Connection': 'keep-alive',
                        'Accept': 'application/json, text/plain, */*',
                        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.66 Safari/537.36 Edg/103.0.1264.44',
                        'Content-Type': 'application/json;charset=UTF-8',
                        'Sec-Fetch-Site': 'same-origin',
                        'Sec-Fetch-Mode': 'cors',
                        'Origin': '{}://{}:12011'.format(self.protocol, self.host),
                        'Referer': '{}://{}:12011/console'.format(self.protocol, self.host),
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
                        'x-auth-cloud-id': 'hz-base-region',
                        'x-request-ip': ''}
        self.cookies = {}
        self.session = session()
        self.region = []
        self.dict_account_mode = {"YEAR_MONTH": '包年包月', 'DAY_TRIAL': '免费试用', 'DAY_MONTH': '按日月结'}
        self.location = ''
        self.request_wait_time = 0
        self.component_code = ''
        self.specification_code = ''
        self.user_id = ''
        self.re_auth = True

    def get_config(self):
        global config_data
        if config_data is None:
            try:
                with open('config.json', 'r', encoding='utf-8') as f:
                    config_data = json5.load(f, encoding='utf-8')
            except FileNotFoundError as e:
                logger.warning('从当前目录:{}获取config.json失败,尝试从上一层目录获取...error:{}'.format(os.getcwd(), str(e)))
                try:
                    with open('../' + 'config.json', 'r', encoding='utf-8') as f:
                        config_data = json5.load(f, encoding='utf-8')
                except FileNotFoundError as e:
                    logger.error('从上层目录获取config.json失败，请检查配置...error:{}'.format(str(e)))
        return config_data

    def get_env(self):
        with open('config.json', 'r') as f:
            data = json.load(f)
        if data:
            self.cfg = data['ziluan']

    def send_request(self, api, method, data={}, **kwargs) -> dict:
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
            self.logger.info(
                msg='url:{}\ndata:{}\nheader:{}\ncookies:{}'.format(url, data, self.headers, self.session.cookies))

        except AttributeError:
            pass
        except Exception as e:
            raise e
        response = self.session.request(method, url, data=json.dumps(data), headers=self.headers,
                                        verify=False, cookies=self.session.cookies)
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

    def setup(self, web_user, web_password, sql_host, sql_user, sql_password, sql_port=3306, username=''):
        self.login(web_user, web_password)
        if type(sql_port) != int:
            try:
                sql_port = int(sql_port)
            except:
                raise TypeError('sql_port类型错误！')

        self.sql(sql_host, sql_user, sql_password, port=sql_port)

        self.get_region()
        self.get_azone_id()
        self.user_id = self.get_user_id(name=username)

    def my_sleep(self, sleep_time=60, msg=None, interval=1):
        '''
        sleep,每隔interval时间打印一个提醒
        '''
        s_time = time.time()
        interval = int(interval)
        sleep_time = int(sleep_time)
        if msg:
            print(msg)
        while time.time() - s_time < (sleep_time):
            print("sleeping ..,total:%s,now:%s" % (sleep_time, int(time.time() - s_time)), end="")
            time.sleep(interval)
            print("\r", end="", flush=True)


def func_instanceName(n, spec=False):
    res = ''
    i = 0
    while i < n:
        temp = chr(randint(65, 122))
        if not spec and not temp.isalpha():
            continue
        res += temp
        i += 1
    return res


def timeStap():
    return int(time.time() * 1000)


def find_kwargs(key, kwargs, default=None):
    if key in kwargs.keys:
        temp = kwargs[key]
        kwargs.pop(key)
        return temp
    return default


def check(n=1, msg=None, interval=5, self=None):
    # 装饰器，跑了n次还是错误的话，返回异常和msg,检查失败后默认等待5s
    def check_decorator(func):
        @wraps(func)
        def wrapped_function(*args, **kwargs):
            # 执行测试点，检查assert
            for i in range(n):
                try:
                    func(*args, **kwargs)
                except AssertionError as e:
                    # 检查失败，先尝试写个log
                    if self:
                        self.logger.info(
                            msg='run:{i},{func_name} check failed, error:{e}'.format(i=i, func_name=func.__name__,
                                                                                     e=str(e)))
                    # 最后检查没过，抛出错误
                    if i == n - 1:
                        # 先检查全局变量，这个msg可以随时修改
                        temp = globals().get('msg', None)
                        raise AssertionError(temp) if temp else AssertionError(msg)
                    # 继续跑
                    time.sleep(interval)
                    continue
                except Exception as e:
                    # 其他错误直接抛出
                    raise e
                # 检查成功，直接退出
                if self:
                    self.logger.info(msg='{func_name} check success'.format(func_name=func.__name__))
                break
            return None

        return wrapped_function

    return check_decorator


def modify_msg(**local_kwargs):
    # 装饰器，修改全局变量...感觉没啥用
    def args_decorator(func, **decorator_kwargs):
        @wraps(func)
        def wrapped_function(*args, **kwargs):
            temp = {}
            for key, value in globals().items():
                temp[key] = value
            for key, value in local_kwargs.items():
                globals()[key] = value
            func(*args, **kwargs)
            # 完成后改回去
            for key, value in local_kwargs.items():
                globals()[key] = temp[key]

        return wrapped_function(**decorator_kwargs)

    return args_decorator


def check_res_code(res):
    # 检查返回code
    code = jsonpath.jsonpath(res, '$.code')
    return code and (code[0] == 'Network.Success' or code[0] == '0')


def randomIP():
    # 生成随机ip地址
    a = random.sample(list(range(1, 256)) * 4, 4)
    b = map(str, a)
    return '.'.join(b)


def sendto_weixin(msg, authKey='', self=None):
    """
    将信息发送到liubo的框架上，必须传入self
    :param msg:
    :param authKey:
    :param self:
    :return:
    """
    if not self:
        raise ValueError('请将测试用例实例self传入self中')
    if not authKey:
        name = self.__class__.__name__
        try:
            temp = self.user.get_task_by_name(name)
            if hasattr(temp, 'authKey') and temp.authKey:
                authKey = temp.authKey
            if not authKey:
                authKey = self.user.environment.testcase_cfg[name].get('authKey', '')
        except Exception as e:
            logger.warning(msg="未在{}.json中发现authKey配置，使用全局配置".format(name) + str(e))
        self.user.note_liubo(name + ':' + msg, authKey)


if __name__ == '__main__':
    msg = ''


    @modify_msg(msg='bbb')
    @check(n=5, msg=msg)
    def aaa():
        raise Exception


    aaa()
