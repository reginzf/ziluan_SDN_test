# -*- coding: UTF-8 -*-

import ipaddress
import logging
import os
import random
import types
from ipaddress import IPv4Address
from random import randint

import jsonpath
import urllib3
from requests import session

from source import VPC, EIP, ORDER, ECS, NAT, VPCP, CFW, CCN, BFW, func_instanceName, DNS
from source.monkey_patch import send_request

urllib3.disable_warnings()


class T_VPC(EIP, ORDER, ECS, NAT, VPCP, CFW, CCN, BFW, VPC, DNS):
    def on_start(self):
        # 打猴子补丁
        self.session = session()
        self.temp_ = self.send_request
        self.send_request = types.MethodType(send_request, self)

        # self.setup(web_user="aa66378185f7afa4", web_password="ab6d2d968af9a9a5a7bfba", sql_host='172.25.50.25',
        #            sql_user='moove', sql_password='unic-moove', sql_port='3306', username='testcase')
        self.setup(web_user="b071238183e5a8", web_password="bf67299c88a7eef2", sql_host='172.40.150.50',
                   sql_user='moove', sql_password='unic-moove', sql_port='3306', username='nrgtest')

        # 卸载补丁
        self.send_request = self.temp_
        # 默认发一个request后等待0.2s
        # self.request_wait_time = 0.2

    def create_vpc(self):
        start = IPv4Address('10.0.0.0')
        mask = '20'
        sub_mask = '24'
        mask_range = 16 * 256
        for i in range(0, 15):
            n = i + 1
            cidr = start + i * mask_range
            # name = self.get_name(n, str(cidr), mask)
            name = f'CCN_3_1-{i}'
            sub_name = self.get_sub_name(n, n, str(cidr), 24)
            res = self.VPC_create(name=name, cidr=str(cidr) + '/' + mask, subnet_name=sub_name,
                                  subnet_cidrblock=str(cidr) + '/' + sub_mask)
            print(res)

    def get_name(self, n, cidr: str, mask):
        template = 'nrg-EIP_3_1-{n}-{cidr}-{mask}'
        cidr = cidr.replace('.', '_')
        return template.format(n=n, cidr=cidr, mask=mask)

    def get_sub_name(self, n, sub_n, cidr, mask):
        template = 'T-{n}-{sub_n}-{cidr}-{mask}'
        cidr = cidr.replace('.', '_')
        return template.format(n=n, sub_n=1, cidr=cidr, mask=mask)

    def create_eip(self):
        self.EIP_set_default_code()
        for i in range(1):
            n = i + 1
            name = self.get_eip_name(n, randint(1, 20))
            res = self.EIP_create(name, charge_type='postpaid', pay_type='DAY_MONTH', rent_count=randint(1, 12),
                                  bandwidth=randint(1, 20), azoneId=None)
            order_id = jsonpath.jsonpath(res, '$.res.orderId')[0]
            res = self.approve_order(order_id)
            print(res)

    def get_eip_name(self, n, bandwidth):
        template = 'EIP_{}_{}'
        return template.format(n, bandwidth)

    def create_eni(self):
        self.ECS_create_eni('AAA', 'vpc-e9ocxe64sh5d', 'vsnet-e9ocxe64sh5e', 'sg-e9ocxm288sjj', azoneId=None)

    def query_db(self):
        sql_conn_uni_network_basic = self.c_sql.connect_db('uni_network_basic').cursor()
        sql_conn_uni_compute = self.c_sql.connect_db('uni_network_basic').cursor()
        sql_conn_uni_network_basic.execute(
            '''SELECT ecs_id FROM tbl_base_ecs_resource a WHERE instance_id='ccn-fj1xbwyrzwgt';''')
        ecs = [ele['ecs_id'] for ele in sql_conn_uni_network_basic.fetchall()]
        for e in ecs:
            sql_conn_uni_compute.execute(
                '''SELECT is_deleted FROM uni_compute.tbl_domain WHERE domain_uuid='{}' '''.format(e))
            res = sql_conn_uni_compute.fetchall()

            assert res and res[0]['is_deleted'] == '1', ''

    def create_stream(self):
        self.ECS_Stream_nrg(['ecs-fj1xbwyrzwq9', 'ecs-fj1xbwyrzwrf'], 'aaa', 'bbb')

    def bind_vpc2ccn(self):
        self.CCN_CreateCcnVpc('ccn-fo4lvcqy3den', 'vpc-fj10sno4cyq9')

    def get_scps(self):
        data = {'name': 'CFW_2_1-23-axFk',
                'description': 'attEuwPpXkAQEJEBEc', 'srcIpAddress': '228.157.19.126/25',
                'destIpAddress': '225.33.98.174/24', 'protocol': 2, 'srcVmPortStart': None, 'srcVmPortEnd': None,
                'destVmPortStart': None, 'destVmPortEnd': None, 'strategy': 2, 'direction': 1}

        return self.CFW_ModifyCfwScp('cfw-fj10y0kpe9tb', 'scp-fo4lv0fcfv1o', **data)


def gen_ipv4_target():
    return [str(ipaddress.IPv4Address(random.randint(0, 4294967295))) for _ in range(random.randint(1, 50))]


def gen_ipv6_target():
    return [str(ipaddress.IPv6Address(random.randint(0, 340282366920938463463374607431768211455))) for _ in
            range(random.randint(1, 50))]


def gen_cname_target():
    return func_instanceName(random.randint(5, 10)) + '.' + func_instanceName(random.randint(5, 10))


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        filename='logs\\{}.log'.format(os.path.basename(__file__).split('.py')[0]),
                        filemode='w',
                        format='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s')
    T_VPC.logger = logging.getLogger()
    aaa = T_VPC()
    aaa.on_start()

    # def create_dns():
    #     for i in range(20):
    #         res = aaa.DNS_CreateLDns(func_instanceName(10) + '.com')
    #         ldns = jsonpath.jsonpath(res, '$.res.instanceId')[0]
    #         print(ldns)
    #         for j in range(200):
    #             try:
    #                 res = aaa.DNS_CreateLDnsResolve_nrg(ldnsId=ldns)
    #                 print(res)
    #                 time.sleep(0.3)
    #             except Exception as e:
    #                 raise e
    #
    #
    # threads = []
    # for i in range(5):
    #     t = threading.Thread(target=create_dns, args=())
    #     threads.append(t)
    # for t in threads:
    #     t.start()
    # time.sleep(300)
    # exit(1)
    # aaa.VPC_delete_vpc_can_delete()
    for i in range(10):
        aaa.CFW_CreateCfwScp_random('cfw-f98br0ojcyvl', network_strict=True)
