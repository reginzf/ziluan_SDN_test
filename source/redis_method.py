# -*- coding: UTF-8 -*-
from copy import deepcopy
from random import randint
from time import sleep, time

import ipaddress
import redis
from jinja2 import Template

head_template = '''{
    "overlay_ports": [
        {{routes}}
    ]
}'''
route = '''{
            "bgp_as_number": "{{bgp_as_number}}",
            "l2vni": "{{l2vni}}",
            "l3vni": "{{l3vni}}",
            "nic_cvk_ip": "{{nic_cvk_ip}}",
            "nic_index": "{{nic_index}}",
            "nic_ip": "{{nic_ip}}",
            "nic_mac": "{{nic_mac}}",
            "nic_name": "{{nic_name}}",
            "online_type": "{{online_type}}",
            "rt": "{{rt}}",
            "subnet_gw_ip": "{{subnet_gw_ip}}",
            "subnet_gw_mac": "{{subnet_gw_mac}}",
            "subnet_mask": "{{subnet_mask}}"
        }'''


class Redis_client():
    def __init__(self, host, username, password, port=6379, db=1):
        # sentinel port: 26379
        self.client = redis.Redis(host=host, username=username, password=password, port=port, db=db)
        self.head_template = Template(source=head_template)
        self.route_template = Template(source=route)

    def get_all_routes(self, n, bgp_as_number, l2vni, l3vni, nic_cvk_ip, nic_index, nic_mac, nic_ip, nic_name,
                       subnet_gw_ip,
                       subnet_gw_mac,
                       subnet_mask, online_type=1, rt=10, res=[]):
        routes = self.gen_routes(n, bgp_as_number, l2vni, l3vni, nic_cvk_ip, nic_index, nic_mac, nic_ip, nic_name,
                                 subnet_gw_ip,
                                 subnet_gw_mac,
                                 subnet_mask, online_type, rt, res=res)
        return self.head_template.render(routes=routes)

    def gen_route(self, **kwargs):
        # 按jinja方式，从kwarg中以key:value渲染
        return self.route_template.render(**kwargs)

    def gen_routes(self, n, bgp_as_number, l2vni, l3vni, nic_cvk_ip, nic_index, nic_mac, nic_ip, nic_name, subnet_gw_ip,
                   subnet_gw_mac,
                   subnet_mask, online_type=1, rt=10, res=[]) -> str:
        # 先赋值，然后在res的基础上增加n条路由，res为当前已有的路由
        base_config = {
            'bgp_as_number': bgp_as_number,
            'l2vni': l2vni,
            'l3vni': l3vni,
            'nic_cvk_ip': nic_cvk_ip,
            'nic_index': nic_index,
            'nic_ip': nic_ip,
            'nic_mac': nic_mac,
            'nic_name': nic_name,
            'subnet_gw_ip': subnet_gw_ip,
            'subnet_gw_mac': subnet_gw_mac,
            'subnet_mask': subnet_mask,
            'online_type': online_type,
            'rt': rt
        }
        for i in range(1, n + 1):
            cfg = deepcopy(base_config)
            cfg['nic_index'] += i
            cfg['nic_ip'] = gen_ip_address(cfg['nic_ip'], i)
            cfg['nic_mac'] = gen_mac(cfg['nic_mac'], i)
            cfg['nic_name'] = "tap-24-NRG{}".format(i)
            res.append(self.gen_route(**cfg))
        return ','.join([str(ele) for ele in res])

    def alter_cvk_version(self, host_name, host, l3vni, value):
        field = 'CVK:{host_name}:{host}'.format(host_name=host_name, host=host)
        key = 'VPC:HOST:{l3vni}'.format(l3vni=l3vni)
        return self.client.hset(field, key, value)

    def alter_l3vni_version(self, host_name, host, l3vni, value, rt=10):
        field = 'VPC:CVK:{l3vni}'.format(l3vni=l3vni)
        key = 'CVK:ZONE_{rt}:{host_name}:{host}'.format(host=host, host_name=host_name, rt=rt)
        return self.client.hset(field, key, value)

    def update_version(self, host_name, host, l3vni, rt=10, value=''):
        # 更新指定cvk，指定l3vni的，要更新l3vni下所有cvk，请参考redis_sub.py
        if not value:
            value = '{request_id}:{time}'.format(request_id=func_instanceName(30), time=timeStap())
        self.alter_l3vni_version(host_name, host, l3vni, value, rt=rt)
        self.alter_cvk_version(host_name, host, l3vni, value)


def gen_ip_address(ip, n):
    return str(ipaddress.IPv4Address(ip) + n)


def gen_mac(mac: str, offset: int):
    # 将mac转化为int，+1之后再转化为str
    mac_address = "{:012X}".format(int(mac.replace(":", ""), 16) + offset)
    return ":".join([mac_address[i:i + 2] for i in range(0, len(mac_address), 2)])


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
    return int(time() * 1000)


if __name__ == '__main__':
    route_num = 1000
    # redis 登陆信息
    redis_host = '172.25.50.30'
    redis_user = 'moove'
    redis_password = 'unic-moove'
    # cvk信息
    cvk_host = '100.100.200.8'
    cvk_hostname = 'CD-AZ1-COMCVK-003'
    cvk_host_1 = '100.100.200.129'
    cvk_hostname_1 = 'CD-AZ1-COMCVK-001'
    # 路由信息
    l3vni = '60028'
    l2vni = '10024'
    bgp_as = '64513'
    nic_cvk_ip = cvk_host_1
    nic_index_start = 2000
    nic_ip_start = '192.168.0.200'
    nic_mac_start = 'fa:16:3e:4c:0b:ff'
    nic_name_start = 'nic_name'
    online_type = 1
    rt = 10
    subnet_gw_ip = '192.168.0.1'
    subnet_gw_mac = 'fa:16:3e:dc:02:d4'
    subnet_mask = 16
    # 构建非本地cvk的路由，直接hset，然后触发更新
    # 需要提前创建vpc，掩码配置为16，ecs，并获取l3vni、l2vni、网关的ip、mac，规划非本机cvk
    client = Redis_client(redis_host, redis_user, redis_password)

    # 创建1000条路由，然后hset到redis

    a = client.get_all_routes(route_num, bgp_as, l2vni, l3vni, nic_cvk_ip, nic_index_start, nic_mac_start, nic_ip_start,
                              nic_name_start, subnet_gw_ip, subnet_gw_mac, subnet_mask)
    # print(a)
    # 直接hset路由
    client.client.hset('VPC:HOST:{}'.format(l3vni), 'CVK:ZONE_10:{}:{}'.format(cvk_hostname_1, cvk_host_1), a)
    sleep(5)
    # 触发更新
    value = '{request_id}:{time}'.format(request_id=func_instanceName(30), time=timeStap())

    client.alter_l3vni_version(cvk_hostname_1, cvk_host_1, l3vni, value=value)  # 非本cvk更新
    sleep(1)
    client.update_version(cvk_hostname, cvk_host, l3vni, value=value)  # 本cvk更新
    client.client.close()
