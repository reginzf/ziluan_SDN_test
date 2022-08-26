# -*- coding: UTF-8 -*-
import os

import json5

from backend.MyClass.agent import Agent
from backend.MyClass.events import events
from backend.log_hander import logger

TESTCASE_DIR = '../testcase_config'


class Environment:

    def __init__(self):
        self.data = self.get_config()
        self._agent_data = None
        self._agent_streams = {}  # 保存流状态 {'taskId':stream_cfg}
        # 和刘波 Agent的通讯实例
        self._agent()

        # 环境配置
        self._ziluan_cfg = {}
        self._web_ui_cfg = {}
        # 测试用例配置，{classname: {attr: value}}
        self._testcase_cfg = {}
        events.init.fire(environment=self)  # 注册钩子

    def get_config(self):
        data = None
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                data = json5.load(f, encoding='utf-8')
        except FileNotFoundError as e:
            logger.warning('从当前目录:{}获取config.json失败,尝试从上一层目录获取...error:{}'.format(os.getcwd(), str(e)))
            try:
                with open('../' + 'config.json', 'r', encoding='utf-8') as f:
                    data = json5.load(f, encoding='utf-8')
            except FileNotFoundError as e:
                logger.error('从上层目录获取config.json失败，请检查配置...error:{}'.format(str(e)))
        return data

    # web_ui相关：
    @property
    def web_ui_cfg(self):
        try:
            web_ui = self.data['web_ui']
            self._web_ui_cfg['host'] = web_ui['host']
            self._web_ui_cfg['port'] = web_ui['port']
            self._web_ui_cfg['local_interface_address'] = web_ui['local_interface_address']
            return self._web_ui_cfg
        except KeyError as e:
            logger.error('web ui配置错误{}'.format(str(e)))
            return None

    @property
    def ziluan_cfg(self):
        try:
            self._ziluan_cfg = self.data['ziluan']
            return self._ziluan_cfg
        except KeyError as e:
            logger.error('紫鸾环境配置错误{}'.format(str(e)))
            return None

    # agent相关：
    def _agent(self):
        self.agent = Agent(self)

    @property
    def agent_data(self):
        self._agent_data = self.data['agent'] if not self._agent_data else self._agent_data
        return self._agent_data

    @property
    def streams(self):
        return self._agent_streams

    # 测试用例配置相关
    def get_testcase_cfg(self, classname):
        filename = os.path.join(TESTCASE_DIR, classname + '.json')
        with open(filename, 'r', encoding='utf-8') as f:
            data = json5.load(f, encoding='utf-8')
            self._testcase_cfg[classname] = data
        return self.testcase_cfg[classname]

    @property
    def testcase_cfg(self):
        return self._testcase_cfg
