# -*- coding: UTF-8 -*-
import json
import time
import types

from requests import session

from backend.MyClass.users import User
from source.monkey_patch_send_request import send_request

__all__ = ['on_start', 'get_env_from_user']




def on_start(self):
    # 打猴子补丁,使用时应该在 + 其他模块中
    self = self
    self.session = session()

    self.temp_ = self.send_request
    self.send_request = types.MethodType(send_request, self)
    # 如果是User的subclass使用env获取环境基本参数,后续需要在用例中调用get_env_from_user(self)，将信息复制到用例中
    if issubclass(self.__class__, User):
        self.ziluan_cfg = self.environment.ziluan_cfg

        self.setup(web_user=self.ziluan_cfg['web_user'], web_password=self.ziluan_cfg['web_password'],
                   sql_host=self.ziluan_cfg['sql_host'],
                   sql_user=self.ziluan_cfg['sql_user'], sql_password=self.ziluan_cfg['sql_password'],
                   sql_port=self.ziluan_cfg['sql_port'], username=self.ziluan_cfg['username'])

    else:
        # 先尝试获取cfg
        try:
            cfg = self.__getattribute__('cfg')
            self.setup(web_user=cfg['web_user'], web_password=cfg['web_password'],
                       sql_host=cfg['sql_host'],
                       sql_user=cfg['sql_user'], sql_password=cfg['sql_password'],
                       sql_port=cfg['sql_port'], username=cfg['username'])
        except Exception:
            self.setup(web_user="ad7725978af399afe0", web_password="ab6d2d968af9a9a5a7bfba", sql_host='172.25.50.25',
                       sql_user='moove', sql_password='unic-moove', sql_port='3306', username='stableEnv')

    # 卸载补丁
    self.send_request = self.temp_
    # 默认发一个request后等待0.15s
    self.request_wait_time = 0.15


def get_env_from_user(self):
    # 如果在user中调用on_start，需要在测试点中获取这些环境参数
    self.token = self.user.token
    self.region = self.user.region
    self.region_dict = self.user.region_dict
    self.request_wait_time = self.user.request_wait_time
    self.user_id = self.user.user_id
    self.username = self.user.username
    self.password = self.user.password
    self.azone_id = self.user.azone_id
    self.c_sql = self.user.c_sql
