# -*- coding: UTF-8 -*-
import ipaddress
import random
from collections import defaultdict


class ChargeType:
    postpaid = 'postpaid'
    prepaid = 'prepaid'


class RentUnit:
    month = 'month'


class PayType:
    YEAR_MONTH = 'YEAR_MONTH'  # 包年包月
    DAY_TRIAL = 'DAY_TRIAL'  # 免费试用
    DAY_MONTH = 'DAY_MONTH'  # 按日月结
    CHARGING_HOURS = 'CHARGING_HOURS'  # 按小时实时计费
    HOUR_MONTH_TIME = 'HOUR_MONTH_TIME'  # 按小时月结
    STREAM_HOUR_HOUR = 'STREAM_HOUR_HOUR'  # 按流量付费

    @classmethod
    def all(cls):
        return [cls.YEAR_MONTH, cls.DAY_MONTH, cls.DAY_TRIAL, cls.CHARGING_HOURS, cls.HOUR_MONTH_TIME,
                cls.STREAM_HOUR_HOUR]


def CVK_get_ecs_taps(host, username, password):
    """
    查询CVK，返回ecs和tap列表
    :param host:
    :param username:
    :param password:
    :return:{'ecs':['tap-1','tap-2']}
    """
    import paramiko
    import re
    ecs_patter = re.compile(r'(ecs-.+?)\b')
    tap_patter = re.compile(r'<.*?dev=\'(tap.*?)\'.*')
    ecs_taps = defaultdict(lambda: [])
    with paramiko.SSHClient() as ssh:
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, username=username, password=password)
        _, out, _ = ssh.exec_command('virsh list --all')
        ecs = [re.search(ecs_patter, res).group(0) for res in out.readlines()[1:] if re.search(ecs_patter, res)]

        for e in ecs:
            _, out, err = ssh.exec_command('''virsh dumpxml {} | grep "target dev='tap-1"'''.format(e))
            for line in out.readlines():
                temp = re.search(tap_patter, line)
                if temp:
                    ecs_taps[e].append(temp.group(1))
    return ecs_taps


ip_types = {'ipv4': lambda: str(ipaddress.IPv4Address(random.randint(0, 4294967295))),
            'ipv6': lambda: str(ipaddress.IPv6Address(random.randint(0, 340282366920938463463374607431768211455)))}
