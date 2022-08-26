# -*- coding: UTF-8 -*-
import time

from backend.MyClass.task import task, TaskSet
from source.monkey_patch import get_env_from_user, on_start
from source import VPC, check, ECS, HSLB
import requests

requests.packages.urllib3.disable_warnings()


class HSLB_CRUD(VPC, ECS, HSLB, TaskSet):
    '''
    SLB的增删改查
    '''
    authKey = "LBD"

    def __init__(self, user):
        pass
        VPC.__init__(self)
        TaskSet.__init__(self, user)
        # 从user中获取环境变量
        get_env_from_user(self)

    def on_start(self):
        self.vpc_name = "HSLB_CRUD"
        self.subnet_name = "HSLB_CRUD"
        self.ecs_name = "HSLB_CRUD"
        self.slb_id = None

    def on_stop(self):
        pass

    @task
    def create_vpc(self):
        cidr = "10.0.0.0/8"
        subnet_cidr = "10.0.0.0/24"
        vpc_name = self.vpc_name
        subnet_name = self.subnet_name
        # 为避免脏数据,首先查找有没有VPC可用
        self.logger.info("查找是否有名为%s的VPC,没有则创建" % vpc_name)
        exist_vpc = self.VPC_get_vpcid_by_vpc_name(name=vpc_name)
        if len(exist_vpc):
            self.vpc_id = exist_vpc[0]["instanceId"]
            self.vpc_cidr = exist_vpc[0]["cidr"]
            self.logger.info("找到已存在的测试VPC,vpcid:%s" % self.vpc_id)
        else:
            # 没有现成的就新建一个
            self.logger.info("没有找到现有的VPC,新建VPC")
            ret = self.VPC_create(name=vpc_name, cidr=cidr, subnet_name=subnet_name, subnet_cidrblock=subnet_cidr)
            if ret["code"] != "Network.Success":
                raise "VPC创建失败"
            res = ret["res"]
            self.vpc_id = res["vpcId"]
            vpc = self.VPC_get_vpcid_by_vpc_name(name=vpc_name)[0]
            self.vpc_cidr = vpc["cidr"]

    @task
    def create_subnet(self):
        self.logger.info("查找是否有现成的子网,没有则新建")
        ret = self.VPC_describe_subnet(vpc_id=self.vpc_id)
        subnets = ret["res"]
        if len(subnets) == 0:
            self.logger.info("没有找到现成的子网,新建子网")
            subnet_name = self.subnet_name
            subnet_cidr = self.vpc_cidr
            last_point_index = str(self.vpc_cidr).rindex(".") + 1
            x_index = str(self.vpc_cidr).index("/")
            # 取出10.0.0.x/24中的x
            last_int = str(self.vpc_cidr)[last_point_index:x_index]
            # 取出10.0.0.x/24中的10.0.0.
            prefix = str(self.vpc_cidr)[:last_point_index]
            # 网络地址位加1变为网关地址
            last_int = int(last_int) + 1
            # 前缀加网关最后一位组成网关地址
            gw = str(prefix) + str(last_int)
            ret = self.VPC_create_subnet(vpc_instance=self.vpc_id, name=subnet_name, cidr=subnet_cidr, gatewayIp=gw)
            if ret["code"] != "Network.Success":
                raise "子网创建失败"
            self.subnet_id = ret["res"]["Id"]
            self.logger.info("新建子网成功,子网ID:%s" % self.subnet_id)
        else:
            subnet = subnets[0]
            self.subnet_id = subnet["id"]
            self.logger.info("有现成的子网,子网ID:%s" % self.subnet_id)

    @task
    def create_ecs(self):
        self.lb_server_ecs_name = "hslb_server"
        self.lb_client_ecs_name = "hslb_client"
        self.logger.info("查找2台ecs,名称分别为:%s,%s,没有则新建" % (self.lb_server_ecs_name, self.lb_client_ecs_name))
        ret = self.VPC_describe_subnet(vpc_id=self.vpc_id)
        # 取第一个子网
        subnet = ret["res"][0]
        # 过滤ecs
        ecs = self.ECS_get_ecsid_by_ecs_name(name=self.lb_server_ecs_name)
        self.lb_server_ecs_id = None
        if ecs:
            self.lb_server_ecs_id = ecs[0]
        else:
            self.logger.info("没有现成的ECS,创建一个名为:%s的ECS" % self.lb_server_ecs_name)
            self.ECS_RunEcs(vpc_id=self.vpc_id, subnet_id=self.subnet_id, name=self.lb_server_ecs_name)
            self.my_sleep(10, "等待订单生效")
            self.logger.info("检查ecs是否创建成功")
            ecs_ids = self.ECS_get_ecsid_by_ecs_name(name=self.lb_server_ecs_name)
            assert len(ecs_ids) != 0, "ecs创建失败"
            s_time = time.time()
            create_success = False
            while time.time() - s_time < (10 * 60):
                for ecs_id in ecs_ids:
                    ecs = self.ECS_DescribeEcs(instance_id=ecs_id)
                    assert len(ecs) != 0, "获取ecs状态失败"
                    print(ecs)
                    ecs_state = ecs[0]["status"]
                    if ecs_state == "RUNNING":
                        self.logger.info("ecs:%s创建成功" % ecs_id)
                        ecs_ids.remove(ecs_id)
                if not len(ecs_ids):
                    create_success = True
                    break
                self.my_sleep(10, "等待ECS创建成功", 1)
            assert create_success == True, "5分钟内ECS没有创建成功,请检查ECS状态"
        self.lb_server_ecs_id = self.ECS_get_ecsid_by_ecs_name(name=self.lb_server_ecs_name)[0]

        ecs = self.ECS_get_ecsid_by_ecs_name(name=self.lb_client_ecs_name)
        self.lb_client_ecs_id = None
        if ecs:
            self.lb_client_ecs_id = ecs[0]
        else:
            self.logger.info("没有现成的ECS,创建一个名为:%s的ECS" % self.lb_client_ecs_name)
            self.ECS_RunEcs(vpc_id=self.vpc_id, subnet_id=self.subnet_id, name=self.lb_client_ecs_name)
            self.my_sleep(10, "等待订单生效")
            self.logger.info("检查ecs是否创建成功")
            ecs_ids = self.ECS_get_ecsid_by_ecs_name(name=self.lb_client_ecs_name)
            assert len(ecs_ids) != 0, "ecs创建失败"
            s_time = time.time()
            create_success = False
            while time.time() - s_time < (5 * 60):
                for ecs_id in ecs_ids:
                    ecs = self.ECS_DescribeEcs(instance_id=ecs_id)
                    assert len(ecs) != 0, "获取ecs状态失败"
                    print(ecs)
                    ecs_state = ecs[0]["status"]
                    if ecs_state == "RUNNING":
                        self.logger.info("ecs:%s创建成功" % ecs_id)
                        ecs_ids.remove(ecs_id)
                if not len(ecs_ids):
                    create_success = True
                    break
                self.my_sleep(5, "等待ECS创建成功", 1)
            assert create_success == True, "5分钟内ECS没有创建成功,请检查ECS状态"
            self.lb_client_ecs_id = self.ECS_get_ecsid_by_ecs_name(name=self.lb_client_ecs_name)[0]

    @task
    def create_hslb_instance(self):
        self.slb_name = "hlb_auto_test"
        self.logger.info("创建一个SLB实例,名为:%s" % self.slb_name)
        self.slb_id = self.HSLB_CreateDpvs(vpc_id=self.vpc_id, subnet_id=self.subnet_id, name=self.slb_name)
        self.my_sleep(5, "等待交付单")
        self.logger.info("检查HSLB是否创建成功")
        slb_create_success = False
        s_time = time.time()
        while time.time() - s_time < (15 * 60):
            slb = self.HSLB_DescribeDpvs(id=self.slb_id)
            if not len(slb):
                raise "SLB创建失败,slb id:%s" % self.slb_id
            else:
                slb = slb[0]
            slb_status = slb["status"]
            if slb_status == "RUNNING":
                self.logger.info("SLB状态为RUNNING,SLB创建成功")
                slb_create_success = True
                break
            self.my_sleep(10, "当前SLB状态为:%s不是RUNNING,继续等待SLB创建成功" % slb_status)
        assert slb_create_success == True, "HSLB10分钟内仍然不为RUNNING状态"

    @task
    def create_new_server_group(self):
        self.logger.info("创建一个服务器组")
        self.HSLB_CreateDpvsServerGroup(hslb_id=self.slb_id, server_group_name="hslb_auto")
        self.my_sleep(5, "等待服务器组创建成功")
        sgs = self.HSLB_DescribeDpvsServerGroup(hslb_id=self.slb_id)
        self.server_group_id = None
        for sg in sgs:
            if sg["name"] == "hslb_auto":
                self.server_group_id = sg["serverGroupId"]
                break
        assert self.server_group_id != None, "获取服务器组ID失败"
        self.logger.info("创建服务器组成功,服务器组ID:%s" % self.server_group_id)

    @task
    def create_hslb_listener(self):
        self.logger.info("为HSLB:%s创建监听器" % self.slb_id)
        server_group = {
            "id": self.server_group_id,
            "name": "hslb_auto",
            "description": "",
            "algorithm": "ROUND_ROBIN",
            "sessionType": "",
            "cookieName": "",
            "loadbalancerId": self.slb_id,
            "serverGroupId": self.server_group_id
        }
        self.HSLB_CreateDpvsWizard(hslb_id=self.slb_id, server_group=server_group)
        self.my_sleep(10, "等待监听器创建成功")
        listeners = self.HSLB_DescribeDpvsListener(hslb_id=self.slb_id)
        assert len(listeners) != 0, "创建SLB监听器失败"
        listener = listeners[0]
        self.listener_id = listener["listenerId"]
        self.logger.info("监听器创建成功,监听器id:%s" % self.listener_id)

    @task
    def modify_server_group(self):
        self.logger.info("为服务器组增加服务器")
        self.logger.info("获取可用的虚机列表")
        ecses = self.HSLB_DescribeVmListForDpvsServerGroup(hslb_id=self.slb_id)
        if len(ecses) == 0:
            raise "没有可用的虚机"
        ecs = ecses[0]

        servers = [
            {
                "portId": ecs["eniId"],
                "serverId": ecs["instanceId"],
                "serverIpv4Ip": ecs["ip"],
                "serverIpv6Ip": "",
                "serverPort": 29531,
                "weight": 1,
                "serverGroupId": self.server_group_id,
                "actionStatus": 0,
                "loadbalancerId": self.slb_id,
                "subnetId": ecs["subnetId"],
                "serverStatus": "RUNNING",
                "etherType": "ipv4"
            }
        ]
        self.HSLB_BatchOperateDpvsServerPort(hslb_id=self.slb_id, server_group_id=self.server_group_id, servers=servers)
        self.my_sleep(5, "等待服务器组绑定完成")
        self.logger.info("查询服务器组绑定成功")
        sgs = self.HSLB_DescribeDpvsServerGroup(hslb_id=self.slb_id)
        found = False
        for sg in sgs:
            if sg["serverGroupId"] == self.server_group_id:
                self.logger.info("找到对应的服务器组,查看服务器是否存在")
                sg_servers = sg["servers"]
                for ser in sg_servers:
                    if ser["serverId"] == ecs["instanceId"]:
                        found = True
                        break
        assert found == True, "查找服务器失败,请检查是否添加成功"
        self.logger.info("服务器组添加服务器成功,ecs:%s" % ecs["instanceId"])

    @task
    def create_acl(self):
        acl_name = "hslb_auto"
        self.logger.info("创建一个高性能SLB的ACL")
        self.HSLB_CreateDpvsAcl(name=acl_name,rules=[])
        acls = self.HSLB_DescribeDpvsAcl(name=acl_name)
        assert len(acls) != 0, "ACL新建失败,请检查是否存在名为%s的ACL" % acl_name
        acl = acls[0]
        self.acl_id = acl["instanceId"]
        self.logger.info("新建ACL成功,ACL_ID:%s" % self.acl_id)

    @task
    def add_acl_rules(self):
        self.logger.info("增加ACL规则")
        rules = {
            "ipSegment": "1.1.1.1",
            "etherType": "IPV4",
            "description": ""
        }
        self.HSLB_CreateDpvsAclRule(acl_id=self.acl_id, rules=rules)
        self.logger.info("检查规则是否新建成功")
        ret_rules = self.HSLB_DescribeDpvsAclRule(acl_id=self.acl_id)
        found = False
        for rule in ret_rules:
            if rule["ipSegment"] == "1.1.1.1":
                found = True
                self.acl_rule_id = rule["instanceId"]
                break
        assert found == True, "没有找到新建的ACL规则"
        self.logger.info("新建ACL规则成功,RULE_ID:%s" % self.acl_rule_id)

    @task
    def modify_acl_rules(self):
        new_desc = "hello world"
        self.logger.info("修改ACL规则描述为:%s" % new_desc)
        self.HSLB_ModifyDpvsAclRule(acl_rule_id=self.acl_rule_id, new_desc=new_desc)
        self.logger.info("检查描述是否修改成功")
        ret_rules = self.HSLB_DescribeDpvsAclRule(acl_id=self.acl_id)
        found = False
        for rule in ret_rules:
            if rule["instanceId"] == self.acl_rule_id and rule["description"] == new_desc:
                found = True
                break
        assert found == True, "ACL规则描述修改失败"
        self.logger.info("ACL规则描述修改成功,RULE_ID:%s" % self.acl_rule_id)

    # @task
    def bind_acl_to_listener(self):
        self.logger.info("绑定ACL(%s)到监听器(%s)" % (self.acl_id, self.listener_id))
        self.HSLB_BindAclFromDpvsListener(acl_id=self.acl_id, hslb_id=self.slb_id, listener_id=self.listener_id)
        self.logger.info("ACL绑定监听器成功")

    # @task
    def unbind_acl_to_rule(self):
        self.logger.info("解绑ACL(%s)到监听器(%s)" % (self.acl_id, self.listener_id))
        self.HSLB_UnbindAclFromDpvsListener(acl_id=self.acl_id, hslb_id=self.slb_id, listener_id=self.listener_id)
        self.logger.info("ACL解绑监听器成功")

    @task
    def del_acl_rule(self):
        self.logger.info("删除ACL(%s)规则(%s)" % (self.acl_id, self.acl_rule_id))
        self.HSLB_DeleteDpvsAclRule(acl_id=self.acl_id, acl_rule_id=self.acl_rule_id)
        self.logger.info("ACL规则(%s)删除成功" % self.acl_rule_id)

    @task
    def del_acl(self):
        self.logger.info("删除ACL(%s)" % (self.acl_id))
        self.HSLB_DeleteDpvsAcl(acl_id=self.acl_id)
        self.logger.info("ACL删除成功")

    @task
    def stop_listener(self):
        self.logger.info("停止监听器(%s)" % (self.listener_id))
        self.HSLB_StopDpvsListener(listener_ids=self.listener_id, hslb_id=self.slb_id)
        self.logger.info("监听器(%s)停止成功" % (self.listener_id))
        self.logger.info("检查监听器是否停止成功")
        s_time = time.time()
        stopped = False
        while time.time() - s_time < (5 * 60):
            listeners = self.HSLB_DescribeDpvsListener(hslb_id=self.slb_id)
            if not len(listeners):
                raise "获取监听器失败"
            listener = listeners[0]
            if listener["status"] == 2:
                stopped = True
                break
            else:
                self.my_sleep(5, "等待SLB监听器开启")
        assert stopped == True, "停止监听器(%s)失败" % self.listener_id
        self.logger.info("停止监听器(%s)成功" % self.listener_id)

    @task
    def start_listener(self):
        self.logger.info("开启监听器(%s)" % (self.listener_id))
        self.HSLB_StartDpvsListener(listener_ids=self.listener_id, hslb_id=self.slb_id)
        self.logger.info("监听器(%s)开启成功" % (self.listener_id))
        self.logger.info("检查监听器是否停止成功")
        s_time = time.time()
        stopped = True
        while time.time() - s_time < (5 * 60):
            listeners = self.HSLB_DescribeDpvsListener(hslb_id=self.slb_id)
            if not len(listeners):
                raise "获取监听器失败"
            listener=listeners[0]
            if listener["status"] == 0:
                stopped=False
                break
            else:
                self.my_sleep(5, "等待SLB监听器开启")
        assert stopped == False, "开启监听器(%s)失败" % self.listener_id
        self.logger.info("开启监听器(%s)成功" % self.listener_id)

    @task
    def del_listener(self):
        self.logger.info("删除监听器%s" % self.listener_id)
        self.HSLB_DeleteDpvsListener(listener_ids=self.listener_id, hslb_id=self.slb_id)
        self.logger.info("删除监听器%s成功" % self.listener_id)

    @task
    def delete_server_group(self):
        self.logger.info("删除新建的服务器组:%s" % self.server_group_id)
        self.HSLB_DeleteDpvsServerGroup(hslb_id=self.slb_id, server_group_ids=self.server_group_id)
        self.my_sleep(5, "等待服务器组删除成功")
        self.logger.info("检查服务器组是否删除成功")
        sgs = self.HSLB_DescribeDpvsServerGroup(hslb_id=self.slb_id)
        found = False
        for sg in sgs:
            if sg["serverGroupId"] == self.server_group_id:
                found = True
                break
        assert found == False, "服务器组删除失败"
        self.logger.info("服务器组删除成功")

    @task
    def stop_hslb(self):
        self.logger.info("停止SLB(%s)" % (self.slb_id))
        self.HSLB_StopDpvs(hslb_ids=self.slb_id)
        self.logger.info("停止SLB(%s)成功" % (self.slb_id))
        self.logger.info("检查HSLB是否停止成功")
        s_time = time.time()
        stopped = True
        while time.time() - s_time < (5 * 60):
            slbs = self.HSLB_DescribeDpvs(id=self.slb_id)
            if len(slbs):
                slb = slbs[0]
            else:
                raise "获取SLB(%s)失败" % self.slb_id
            if slb["status"] == "STOPPED":
                stopped = True
                break
            self.my_sleep(5, "等待SLB关闭")
        assert stopped == True, "停止HSLB(%s)失败" % self.slb_id
        self.logger.info("停止HSLB(%s)成功" % self.slb_id)

    @task
    def start_hslb(self):
        self.logger.info("开启SLB(%s)" % (self.slb_id))
        self.HSLB_StartDpvs(hslb_ids=self.slb_id)
        self.logger.info("开启SLB(%s)成功" % (self.slb_id))
        self.logger.info("检查HSLB是否开启成功")
        s_time = time.time()
        stopped = True
        while time.time() - s_time < (5 * 60):
            slbs = self.HSLB_DescribeDpvs(id=self.slb_id)
            if len(slbs):
                slb = slbs[0]
            else:
                raise "获取SLB(%s)失败" % self.slb_id
            if slb["status"] == "RUNNING":
                stopped = False
                break
            self.my_sleep(5, "等待SLB关闭")
        assert stopped == False, "开启HSLB(%s)失败" % self.slb_id
        self.logger.info("开启HSLB(%s)成功" % self.slb_id)

    @task
    def del_hslb(self):
        self.logger.info("开始删除SLB")
        self.HSLB_DeleteDpvs(ids=self.slb_id)
        self.my_sleep(5, "等待SLB删除")
        slb = self.HSLB_DescribeDpvs(id=self.slb_id)
        assert len(slb) == 0, "SLB:%s删除失败" % self.slb_id
        self.logger.info("SLB:%s删除成功"%self.slb_id)
