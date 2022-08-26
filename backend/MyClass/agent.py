# -*- coding: UTF-8 -*-

import json
import requests


class Agent:
    host: str = None  # 监控主机地址
    port: str = None

    def __init__(self, environment):
        try:
            self.cfg = environment.agent_data
        except KeyError:
            raise KeyError('未获取到Agent配置')
        self.ower = self.cfg['authKey']
        # 格式见template\stream_cfg_template.json
        self.config_stream_header = {"msgType": "config", "configType": "", "authKey": self.ower}
        self.query_stream_header = {"msgType": "query"}
        self.report_header = {"msgType": "report", "msg": {"owner": self.ower, "msg": None}}

    def flush_env(self):
        self.host = self.cfg['host']
        self.port = self.cfg['port']

    def send_message(self, message: dict = None):
        self.flush_env()
        dst_host = "http://%s:%s" % (self.host, self.port)
        headers = {"Content-Type": "application/json"}
        try:
            print('send to liubo')
            reponse = requests.post(url=dst_host, headers=headers, data=json.dumps(message), timeout=8)
            c = reponse.content
            c = c.decode("utf-8")
            return json.loads(c)
        except Exception as e:
            print(str(e))
            return_dict = {'code': '70000', 'message': 'no response'}
            return return_dict
