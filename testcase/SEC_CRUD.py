# -*- coding: UTF-8 -*-
import time

from backend.MyClass.task import task, TaskSet
from source.monkey_patch import get_env_from_user, on_start
from source import VPC, SEC, ECS
import requests

requests.packages.urllib3.disable_warnings()


class SEC_CRUD(VPC, ECS, SEC, TaskSet):
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
        self.vpc_name = "SEC_CRUD"
        self.subnet_name = "SEC_CRUD"
        self.ecs_name = "SEC_CRUD"
        self.sg_id="sg-fh5vt34dwqmk"

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
        else:
            self.logger.info("有现成的子网")
            subnet = subnets[0]
            self.subnet_id = subnet["id"]

    @task
    def create_ecs(self):
        self.logger.info("查看是否有ecs,没有就新建")
        ret = self.VPC_describe_subnet(vpc_id=self.vpc_id)
        # 取第一个子网
        subnet = ret["res"][0]
        subnet_resource = subnet["bindResources"]
        subnet_has_ecs = False
        if subnet_resource and len(subnet_resource) > 0:
            self.logger.info("子网中有资源,检查是否是ecs")
            for resource in subnet_resource:
                id = resource["reviceId"]
                # 需要检查长度,超长的为SLB/CCN等的ECS也会在这里展示
                if str(id).startswith("ecs-") and len(id) == len("ecs-e9ocxuzdov70"):
                    self.logger.info("子网中有ecs,id为:%s" % id)
                    self.ecs_id = id
                    ecs_info = self.ECS_DescribeEcs(instanceId=self.ecs_id)[0]
                    self.eni_id = ecs_info["eniId"]
                    subnet_has_ecs = True
        if subnet_has_ecs == False:
            self.logger.info("子网中没有ECS,创建一个ECS")
            self.ECS_RunEcs(vpc_id=self.vpc_id, subnet_id=self.subnet_id, name=self.ecs_name,sg_id=self.sg_id)
            self.my_sleep(10, "等待订单生效")
            self.logger.info("检查ecs是否创建成功")
            ecs_ids = self.ECS_get_ecsid_by_ecs_name(name=self.ecs_name)
            assert len(ecs_ids) != 0, "ecs创建失败"
            ecs_id = ecs_ids[0]
            s_time = time.time()
            create_success = False
            while time.time() - s_time < (5 * 60):
                ecs = self.ECS_DescribeEcs(instance_id=ecs_id)
                assert len(ecs) != 0, "获取ecs状态失败"
                print(ecs)
                ecs_state = ecs[0]["status"]
                if ecs_state == "RUNNING":
                    self.logger.info("ecs:%s创建成功" % ecs_id)
                    self.ecs_id = ecs_id
                    self.eni_id = ecs[0]["eniId"]
                    break
                self.my_sleep(5, "等待ECS创建成功", 1)
            assert create_success == True, "5分钟内ECS没有创建成功,请检查ECS状态"

    @task
    def create_sg(self):
        self.logger.info("创建一个安全组")
        self.sg_id = self.SEC_CreateSecurityGroup()
        self.my_sleep(5, "等待安全组创建成功")
        self.logger.info("检查安全组是否创建成功:%s" % self.sg_id)
        sgs = self.SEC_DescribeSecurityGroup(id=self.sg_id)
        assert len(sgs) == 1, "通过id查询安全组数量不为1,sgs:%s" % sgs
        self.logger.info("新建安全组成功")

    @task
    def modify_sg(self):
        new_name = "new_sg_name"
        new_desc = "new_sg_desc"
        self.logger.info("修改安全组:%s的名称为:%s,描述为:%s" % (self.sg_id, new_name, new_desc))
        self.SEC_UpdateSecurityGroup(id=self.sg_id, new_name=new_name, new_desc=new_desc)
        self.logger.info("检查安全组修改成功")
        sgs = self.SEC_DescribeSecurityGroup(id=self.sg_id)
        assert len(sgs) == 1, "通过id查询安全组数量不为1,sgs:%s" % sgs
        sg = sgs[0]
        assert sg["instanceName"] == new_name, "修改安全组名称失败"
        assert sg["description"] == new_desc, "修改安全组描述失败"
        self.logger.info("修改安全组成功,当前名称:%s,描述:%s" % (new_name, new_desc))

    @task
    def bind_sg_to_ecs(self):
        self.logger.info("将安全组:%s绑定到ecs" % self.sg_id)
        self.logger.info("查找可用的ecs")
        ecses = self.SEC_AvbForSg(sg_id=self.sg_id, name=self.ecs_name)
        assert len(ecses) != 0, "ecs查找失败"

        self.logger.info("获取到ECSID:%s,eni:%s,SG:%s" % (self.ecs_id, self.eni_id, self.sg_id))
        self.SEC_BindSecurityGroupBatch(sg_id=self.sg_id, ecs_id=self.ecs_id, eni_id=self.eni_id)
        self.logger.info("验证安全组(%s)绑定ECS(%s)成功" % (self.sg_id, self.ecs_id))
        ecses = self.SEC_DescribeEcsBySgId(sg_id=self.sg_id, ecs_id=self.ecs_id)
        assert len(ecses) == 1, "绑定ECS失败,当前绑定的ecs:%s" % self.ecs_id
        self.logger.info("安全组(%s)绑定ECS(%s)成功" % (self.sg_id, self.ecs_id))

    @task
    def add_sg_rules(self):
        self.logger.info("为安全组(%s)添加一条入方向全放通规则" % self.sg_id)
        self.rule_id = self.SEC_CreateSecurityGroupRule(sg_id=self.sg_id)
        self.logger.info("规则创建成功,规则ID:%s" % self.rule_id)

    @task
    def modify_sg_rules(self):
        new_priority = 99
        self.logger.info("修改ACL RULES")
        self.SEC_UpdateSecurityGroupRule(sg_id=self.sg_id, rule_id=self.rule_id, priority=new_priority)
        self.logger.info("验证ACL规则修改成功")
        rules = self.SEC_DescribeSecurityGroupRuleList(sg_id=self.sg_id)
        assert len(rules) != 0, "获取安全组规则失败"
        rule = rules[0]
        assert rule["priority"] == new_priority
        self.logger.info("修改ACL规则成功")

    @task
    def del_sg_rules(self):
        self.logger.info("删除安全组规则:%s" % self.rule_id)
        self.SEC_DeleteSecurityGroupRule(sg_id=self.sg_id, sg_rule_id=self.rule_id)
        self.logger.info("验证ACL规则删除成功")
        rules = self.SEC_DescribeSecurityGroupRuleList(sg_id=self.sg_id)
        assert len(rules) == 0, "安全组删除失败"
        self.logger.info("安全组规则:%s删除成功" % self.rule_id)

    @task
    def unbind_sg_to_ecs(self):
        self.logger.info("将安全组:%s从ECS解绑" % self.sg_id)
        self.SEC_UnbindSecurityGroupBatch(sg_id=self.sg_id, ecs_id=self.ecs_id, eni_id=self.eni_id)
        # self.logger.info("验证安全组(%s)解绑ECS(%s)成功" % (self.sg_id, self.ecs_id))
        # self.my_sleep(30,"等待安全组解绑ECS")
        # ecses = self.SEC_DescribeEcsBySgId(sg_id=self.sg_id, ecs_id=self.ecs_id)
        # assert len(ecses) == 0, "解绑ECS失败,当前绑定的ecs:%s" % ecs_id
        self.logger.info("安全组(%s)解绑ECS(%s)成功" % (self.sg_id, self.ecs_id))

    @task
    def del_sg(self):
        self.logger.info("删除安全组:%s" % self.sg_id)
        self.SEC_DeleteSecurityGroup(sg_id=self.sg_id)
        self.logger.info("验证删除安全组成功")
        self.my_sleep(3, "等待安全组删除成功")
        sgs = self.SEC_DescribeSecurityGroup(id=self.sg_id)
        assert len(sgs) == 0, "安全组%s删除失败" % self.sg_id
        self.logger.info("安全组:%s删除成功" % self.sg_id)
