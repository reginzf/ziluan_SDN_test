# -*- coding: UTF-8 -*-
"""
传入url，data，输出api，api需要手动调试
"""

API_TEMPLATE = '''
def {{ module_name }}_{{ action }}(self,{{ api_args }},{{ api_kwargs }},**kwargs):
    """
    {{ res }}
    """
    api = '{{ api }}'
    method = '{{ method }}'
    Action = '{{ action }}'
	{{ to_edit }}
    data = {{ data }}    
    res = self.send_request(api, method, data,{{ send_kwargs }}, **kwargs)
    return res
'''

from collections import defaultdict
from urllib.parse import urlparse, parse_qs

from jinja2 import Template

TO_EDIT = {'regionId': 'self.region[0] if regionId == None else regionId'}
SEND_KWARGS = {'Action': 'action', 'regionId': 'regionId', 't': 'timeStap()'}
SORT_ARI_ARGS = ['regionId', 't']


class Api_Generater(object):
    def __init__(self, module_name, method, url, data, args_with_data=None, to_edit=None, res=None):
        """
        :param module_name: 模块名称
        :param method: GET POST DELETE
        :param url: 直接拷贝url
        :param data: 发送的载荷，dict
        :param args_with_data: 带默认值的参数 dict
        :param to_edit: 需要编辑的参数，输入{'func_A': 'python代码'} 将输出func_A = python代码
        :param res: 接口的返回
        """
        self.to_edit = None
        self.args_with_data = None
        self.payload_data = {}
        self.res = None
        self.method = None
        self.data = None
        self.url = None
        self.module_name = None
        self.tmp = Template(API_TEMPLATE)
        self.api_args = list()
        self.api_kwarg = defaultdict(lambda: None)  # 含值的kwargs默认为None
        self.send_kwargs = dict()

        self.init_data(module_name, method, url, data, args_with_data, to_edit, res)
        self.do_parse()

    def init_data(self, module_name, method, url, data, args_with_data, to_edit, res):
        self.module_name = module_name
        self.url: str = url
        self.data: dict = data
        self.method = method.upper()
        self.res = res
        self.args_with_data = args_with_data
        self.to_edit = to_edit if to_edit else dict()

    def do_parse(self):
        self.parse_url()
        self.payload_data = self.parse_data()
        self.parse_data_kwargs(self.args_with_data)
        self.parse_to_edit()
        self.sort_api_args()

    def parse_url(self):
        # 解析url，返回api_apth、param，将param中参数加入arp_args中
        u = urlparse(self.url)
        self.api_path = u.path
        _data = dict()
        [_data.update({a: b[0]}) for a, b in parse_qs(u.query).items()]
        if _data.get('t', None):  # 在后面处理t
            self.flag_t = True
        self.url_query: dict = _data
        keys = list(self.url_query.keys())

        [keys.remove(ele) for ele in {'t', 'Action'}]
        self.api_args.extend(keys)

    def parse_data(self):
        # 解析载荷，将参数全部加入self.api_args中，将参数key重构成data
        api_args = list()

        def _parse_data(data: dict, api_args):
            if type(data) == dict:
                res = {}
                for key, value in data.items():
                    api_args.append(key)

                    if type(value) == list or type(value) == dict:
                        res[key] = _parse_data(value, api_args)
                    else:
                        res[key] = value
                    _parse_data(value, api_args)
            elif type(data) == list:
                res = []
                for ele in data:
                    if type(ele) == dict or type(ele) == list:
                        res.append(_parse_data(ele, api_args))
            else:
                return {}
            return res

        ret = _parse_data(self.data, api_args)
        self.api_args.extend(set(api_args))

        _ = ','.join(['\'{}\':{}'.format(key, value) for key, value in ret.items()])
        return '{' + _ + '}'

    def parse_data_kwargs(self, args_with_data: dict):
        # 将需要默认参数的参数重构成kwargs
        if args_with_data:
            for key, value in args_with_data.items():
                try:
                    self.api_args.remove(key)
                    self.api_kwarg[key] = value
                except ValueError:  # remove报错直接pass
                    pass

    def parse_to_edit(self):
        # 1、默认的公用参数直接格式化到to_edit中
        # 2、支持以 dict 方式传入，例：{fun_A:'stat_to_exec'}

        self.args_union = list()

        self.args_union.extend(self.api_args)
        self.args_union.extend(self.api_kwarg.keys())

        for key, value in TO_EDIT.items():
            if key in self.args_union:
                self.to_edit[key] = value
        res = ''
        for key, value in self.to_edit.items():
            res = res + '{} = {}\n\t'.format(key, value)
        self.to_edit = res

    def parse_send_kwargs(self):
        temp = dict()
        for key, value in SEND_KWARGS.items():
            if key in self.args_union:
                temp[key] = value
        if self.flag_t:
            temp['t'] = SEND_KWARGS['t']
        if self.Action:
            temp['Action'] = SEND_KWARGS['Action']
        return ','.join(['{}={}'.format(key, value) for key, value in temp.items()])

    def parse_res(self):
        ret = ''.join([':param {}:\n\t'.format(ele) for ele in self.args_union])
        return '{ret}:return: {res}'.format(ret=ret, res=self.res)

    @property
    def Action(self):
        return self.url_query.get('Action', None)

    @property
    def regionId(self):
        if self.url_query.get('regionId', None):
            return 'self.region[0] if regionId == None else regionId'

    @property
    def t(self):
        if self.url_query.get('t', None):
            return 'timeStap()'

    def sort_api_args(self):
        for ele in SORT_ARI_ARGS:
            try:
                self.api_args.remove(ele)
                self.api_args.append(ele)
            except:
                pass

    def generate_api(self):
        result = {
            'module_name': self.module_name,
            'action': self.Action,
            'api_args': ','.join(self.api_args),
            'api_kwargs': ','.join(['{}={}'.format(a, b) for a, b in self.api_kwarg.items()]),
            'res': self.parse_res(),
            'api': self.api_path[1:],
            'method': self.method,
            'to_edit': self.to_edit,  # 下午写
            'data': self.payload_data,
            'send_kwargs': self.parse_send_kwargs()
        }
        return self.tmp.render(**result)


if __name__ == '__main__':
    data = {"instanceId": "instanceId", "ldnsId": "ldnsId", "instanceName": "instanceName", "type": "type",
            "ttl": "ttl", "desc": "desc", "addValues": "addValues", "rmvValues": "rmvValues"}
    A = Api_Generater('DNS', 'get', 'http://172.25.0.1:12001/api/get/dns?Action=aaa&t=1234123&regionId=cd', data,
                      {'ldnsId': None, 'ttl': 123}, {"instanceName": 'fffffkkk'}, {'a': 'b'})

    print(A.generate_api())
