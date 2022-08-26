# -*- coding: UTF-8 -*-
import time

from backend.MyClass.task import task, TaskSet
from source.monkey_patch import get_env_from_user, on_start
from source import VPC, check, ECS, HAVIP, EIP, SLB
import requests

requests.packages.urllib3.disable_warnings()


class SLB_CRUD(VPC, ECS, SLB, TaskSet):
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
        self.vpc_name = "lb_auto_public"
        self.subnet_name = "lb_auto_public"
        self.ecs_name = "lb_auto_public"
        self.slb_id = None

    def on_stop(self):
        if self.slb_id:
            self.SLB_DeleteSlb(slb_id=self.slb_id)

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
        self.lb_server_ecs_name = "lb_server"
        self.lb_client_ecs_name = "lb_client"
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
    def create_slb_instance(self):
        self.slb_name = "lb_auto_test"
        self.logger.info("创建一个SLB实例,名为:%s" % self.slb_name)
        self.slb_id = self.SLB_CreateSlb(vpc_id=self.vpc_id, subnet_id=self.subnet_id, name=self.slb_name)
        self.my_sleep(5,"等待交付单")
        self.logger.info("检查SLB是否创建成功")
        slb_create_success = False
        s_time = time.time()
        while time.time() - s_time < (15 * 60):
            slb = self.SLB_DescribeSlb(id=self.slb_id)
            if not len(slb):
                raise "SLB创建失败,slb id:%s"%self.slb_id
            else:
                slb=slb[0]
            slb_status = slb["status"]
            if slb_status == "RUNNING":
                self.logger.info("SLB状态为RUNNING,SLB创建成功")
                slb_create_success = True
                break
            self.my_sleep(10, "当前SLB状态为:%s不是RUNNING,继续等待SLB创建成功" % slb_status)
        assert slb_create_success == True, "SLB5分钟内仍然不为RUNNING状态"

    @task
    def modify_slb(self):
        new_slb_name = "new_slb_name"
        self.logger.info("开始测试修改SLB名称,修改SLB名称为%s" % new_slb_name)
        self.SLB_ModifySlb(slb_id=self.slb_id, new_slb_name=new_slb_name)
        self.my_sleep(5, "等待SLB名称修改生效")
        slb = self.SLB_DescribeSlb(id=self.slb_id)[0]
        slb_name = slb["instanceName"]
        assert slb_name == new_slb_name, "修改SLB名称失败"
        self.logger.info("修改SLB名称成功")

    @task
    def create_listener(self):
        self.logger.info("为SLB:%s创建监听器" % self.slb_id)
        self.SLB_WIZARD(slb_id=self.slb_id)
        self.my_sleep(10, "等待监听器创建成功")
        listeners = self.SLB_DescribeListener(slb_id=self.slb_id)
        assert len(listeners) != 0, "创建SLB监听器失败"
        listener = listeners[0]
        self.listener_id = listener["id"]
        self.logger.info("监听器创建成功,监听器id:%s" % self.listener_id)

    @task
    def stop_listener(self):
        self.logger.info("开始测试停止监听器")
        self.SLB_StopListener(slb_id=self.slb_id, listener_ids=self.listener_id)
        self.my_sleep(5, "等待监听器停止")
        listeners = self.SLB_DescribeListener(slb_id=self.slb_id)
        assert len(listeners) != 0, "监听器过滤失败"
        listener = listeners[0]
        listener_status = int(listener["status"])
        assert listener_status == 2, "监听器停止失败"
        self.logger.info("监听器停止成功")

    @task
    def start_listener(self):
        self.logger.info("开启停止的监听器:%s" % self.listener_id)
        self.SLB_StartListener(slb_id=self.slb_id, listener_ids=self.listener_id)
        self.my_sleep(5, "等待监听器启动")
        listeners = self.SLB_DescribeListener(slb_id=self.slb_id)
        assert len(listeners) != 0, "监听器过滤失败"
        listener = listeners[0]
        listener_status = int(listener["status"])
        assert listener_status == 0, "监听器停止失败"
        self.logger.info("监听器停止成功")

    @task
    def create_acl(self):
        acl_name = "lb_autoacl"
        self.logger.info("新建一个ACL:%s" % acl_name)
        self.SLB_CreateAcl(acl_name=acl_name, rules=[])
        self.my_sleep(5, "等待ACL新建成功")
        acls = self.SLB_DescribeAcl(name=acl_name)
        assert len(acls) != 0, "ACL新建失败"
        acl = acls[0]
        self.acl_id = acl["id"]
        self.logger.info("ACL新建成功")

    @task
    def modify_acl(self):
        new_acl_name = "new_acl_name_auto"
        self.logger.info("将ACL的名称修改为:%s" % new_acl_name)
        self.SLB_ModifyAcl(acl_id=self.acl_id, new_acl_name=new_acl_name)
        self.my_sleep(3, "等待ACL新名称生效")
        ret = self.SLB_DescribeAcl(name=new_acl_name)
        assert len(ret) != 0, "修改ACL名称失败"
        self.logger.info("修改ACL名称成功")

    @task
    def create_acl_rules(self):
        self.logger.info("为ACL增加规则")
        self.SLB_CreateAclRule(acl_id=self.acl_id, ip="1.1.1.1/32", desc="test_auto")
        self.my_sleep(3, "等待ACL规则创建成功")
        acl_rules = self.SLB_DescribeAclRule(acl_id=self.acl_id)
        assert len(acl_rules) != 0, "ACL规则创建失败"
        acl_rule = acl_rules[0]
        self.acl_rule_id = acl_rule["id"]
        self.logger.info("创建ACL规则成功")

    @task
    def modify_acl_rules(self):
        new_acl_rule_desc = "new acl rule desc"
        self.logger.info("修改ACL规则描述为:%s" % new_acl_rule_desc)
        self.SLB_ModifyAclRule(rule_id=self.acl_rule_id, new_desc=new_acl_rule_desc)
        self.my_sleep(3, "等待ACL规则描述修改成功")
        acl_rules = self.SLB_DescribeAclRule(acl_id=self.acl_id)
        acl_rule = acl_rules[0]
        acl_desc = acl_rule["description"]
        assert acl_desc == new_acl_rule_desc, "修改ACL规则描述失败"
        self.logger.info("修改ACL规则描述成功")

    @task
    def bind_acl_to_listener(self):
        self.logger.info("将ACL:%s绑定到监听器:%s" % (self.acl_id, self.listener_id))
        self.SLB_BindAclToListener(acl_id=self.acl_id, listener_id=self.listener_id)
        self.logger.info("查看监听器与ACL是否绑定成功")
        self.my_sleep(3, "等待监听器绑定ACL")
        listeners = self.SLB_DescribeListener(slb_id=self.slb_id)
        found = False
        for listener in listeners:
            if listener["id"] == self.listener_id and listener["aclPolicy"]["id"] == self.acl_id:
                found = True
                break
        assert found == True, "监听器:%s绑定ACL:%s失败" % (self.listener_id, self.acl_id)
        self.logger.info("监听器:%s绑定ACL:%s成功" % (self.listener_id, self.acl_id))

    @task
    def modify_server_group(self):
        self.logger.info("查找一个服务器组")
        server_groups = self.SLB_DescribeServerGroup(slb_id=self.slb_id)
        assert len(server_groups) != 0, "服务器组查找失败"
        server_group = server_groups[0]
        server_group_id = server_group["id"]
        self.logger.info("修改服务器组信息,增加一台RS")
        ecses = self.SLB_DescribeAvailableEcsForSlb(slb_id=self.slb_id)
        assert len(ecses) != 0, "SLB没有可用的ECS"
        ecs = ecses[0]
        ecs_id = ecs["instanceId"]
        ecs_ip = ecs["ip"]
        eni_id = ecs["eniId"]
        ecs_port = 9999
        server = {
            "portId": eni_id,
            "serverId": ecs_id,
            "serverIp": ecs_ip,
            "serverPort": ecs_port,
            "weight": 1,
            "serverGroupId": server_group_id,
            "actionStatus": 0,
            "loadbalancerId": self.slb_id
        }
        self.SLB_OperateServer(server)
        self.logger.info("检查RS是否增加成功")
        server_groups = self.SLB_DescribeServerGroup(slb_id=self.slb_id, server_group_id=server_group_id)
        assert len(server_groups) == 1, "获取服务器组失败"
        server_group = server_groups[0]
        rses = server_group["lbServerDtoList"]
        found = False
        for rs in rses:
            rs_id = rs["serverId"]
            if rs_id == ecs_id:
                found = True
                break
        assert found == True, "绑定RS到服务器组失败"

    @task
    def unbind_acl_to_listener(self):
        self.logger.info("开始解绑监听器与服务器组")
        self.SLB_UnbindAclFromListener(acl_id=self.acl_id, listener_id=self.listener_id)
        self.logger.info("查看监听器解绑ACL是否成功")
        self.my_sleep(3, "等待监听器ACL解绑")
        listeners = self.SLB_DescribeListener(slb_id=self.slb_id)
        found = False
        for listener in listeners:
            if listener["id"] == self.listener_id and (listener["aclPolicy"] is not None):
               raise "监听器:%s解绑ACL:%s失败" % (self.listener_id, self.acl_id)
        self.logger.info("监听器:%s解绑ACL:%s成功" % (self.listener_id, self.acl_id))

    @task
    def del_acl_rules(self):
        self.logger.info("开始删除ACL规格")
        self.SLB_DeleteAclRule(acl_id=self.acl_id, rule_id=self.acl_rule_id)
        self.my_sleep(3, "等待ACL规则删除成功")
        rules = self.SLB_DescribeAclRule(acl_id=self.acl_id)
        found = False
        for rule in rules:
            if rule["id"] == self.acl_rule_id:
                found = True
                break
        assert found == False, "ACL规则%s删除失败" % self.acl_rule_id
        self.logger.info("ACL规则删除成功")

    @task
    def del_acl(self):
        self.logger.info("删除ACL规则")
        self.SLB_DeleteAcl(acl_id=self.acl_id)
        self.logger.info("查看ACL是否删除成功")
        self.my_sleep(3, "等待ACL删除完成")
        acls = self.SLB_DescribeAcl()
        found = False
        for acl in acls:
            if acl["id"] == self.acl_id:
                found = True
                break
        assert found == False, "ACL删除失败"
        self.logger.info("ACL删除成功")

    @task
    def del_listener(self):
        self.logger.info("删除监听器:%s" % self.listener_id)
        self.SLB_DeleteListener(slb_id=self.slb_id, listener_ids=self.listener_id)
        self.logger.info("检查监听器是否删除成功")
        self.my_sleep(3, "等待监听器删除")
        found = False
        listeners = self.SLB_DescribeListener(slb_id=self.slb_id)
        for listener in listeners:
            if listener["id"] == self.listener_id:
                found = True
                break
        assert found == False, "删除监听器失败"
        self.logger.info("删除监听器成功")

    @task
    def stop_slb(self):
        self.logger.info("停止SLB")
        self.SLB_StopSlb(slb_id=self.slb_id)
        self.my_sleep(5, "等待SLB:%s停止" % self.slb_id)
        self.logger.info("检查SLB:%s是否停止成功" % self.slb_id)
        slbs = self.SLB_DescribeSlb(id=self.slb_id)
        slb = slbs[0]
        slb_state = slb["status"]
        assert slb_state == "STOPPED", "停止SLB失败"
        self.logger.info("SLB停止成功")

    @task
    def start_slb(self):
        self.logger.info("开启SLB:%s" % self.slb_id)
        self.SLB_StartSlb(slb_id=self.slb_id)
        self.my_sleep(5, "等待SLB:%s启动" % self.slb_id)
        self.logger.info("检查SLB:%s是否启动成功" % self.slb_id)
        slbs = self.SLB_DescribeSlb(id=self.slb_id)
        slb = slbs[0]
        slb_state = slb["status"]
        assert slb_state == "RUNNING", "启动SLB失败"
        self.logger.info("SLB启动成功")

    @task
    def del_slb(self):
        self.logger.info("开始删除SLB")
        self.SLB_DeleteSlb(slb_id=self.slb_id)
        self.my_sleep(5, "等待SLB删除")
        slb = self.SLB_DescribeSlb(id=self.slb_id)
        assert len(slb) == 0, "SLB:%s删除失败" % self.slb_id
        self.logger.info("SLB:%s删除成功")
