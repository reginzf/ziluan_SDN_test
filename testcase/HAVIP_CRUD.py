# -*- coding: UTF-8 -*-
import time

from backend.MyClass.task import task, TaskSet
from source.monkey_patch import get_env_from_user, on_start
from source import VPC, check, ECS, HAVIP,EIP
import requests

requests.packages.urllib3.disable_warnings()


class HAVIP_CRUD(HAVIP, VPC, ECS,EIP, TaskSet):
    '''
    创建VPC,创建子网,创建ECS,删除ECS,删除子网,删除VPC
    '''
    authKey = "LBD"

    def __init__(self, user):
        pass
        HAVIP.__init__(self)
        TaskSet.__init__(self, user)
        # 从user中获取环境变量
        get_env_from_user(self)
        # 从environment中获取配置
        # self.init_cfg()

    def on_start(self):
        self.vpc_name = "HAVIP_CRUD"
        self.subnet_name = "HAVIP_CRUD"
        self.ecs_name = "HAVIP_CRUD"
        self.eip_id="eip-fo4l3wjsnvyu"

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
                    subnet_has_ecs = True
        if subnet_has_ecs == False:
            self.logger.info("子网中没有ECS,创建一个ECS")
            self.ECS_RunEcs(vpc_id=self.vpc_id, subnet_id=self.subnet_id, name=self.ecs_name,sg_id="sg-fh5vt34dwqmk")
            self.my_sleep(10, "等待订单生效")
            self.logger.info("检查ecs是否创建成功")
            ecs_ids = self.ECS_get_ecsid_by_ecs_name(name=self.ecs_name)
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
                self.my_sleep(10, "等待ECS创建成功")
            assert create_success == True, "10分钟内ECS没有创建成功,请检查ECS状态"

    @task
    def create_havip(self):
        ret = self.HAVIP_CreateVip(vpc_id=self.vpc_id, subnet_id=self.subnet_id)
        if ret["code"] != "Network.Success":
            raise "创建HAVIP失败"
        self.havip_id = ret["res"]["vipId"]

    @task
    def havip_bind_ecs(self):
        self.logger.info("绑定/解绑 ECS与HAVIP")
        # 获取可以绑定的ECS接口列表,上面创建了一个ECS,所以最少有一个
        self.logger.info("获取可以绑定的ECS列表")
        ret = self.ECS_AvbForVip(havip_id=self.havip_id, subnet_id=self.subnet_id)
        ret = ret[0]
        ecs_id = ret["instanceId"]
        eni_id = ret["eniId"]
        self.logger.info("获取到ECS:%s,ENI:%s,开始绑定到HAVIP:%s"%(ecs_id,eni_id,self.havip_id))

        ret = self.HAVIP_BindEcsToVip(ecs_id=ecs_id, havip_id=self.havip_id, eni_id=eni_id)
        if ret["code"] != "Network.Success":
            raise "绑定vip和ECS失败,VIP:%s,ECS:%s" % (self.havip_id, ecs_id)
        self.my_sleep(5, "等待HAVIP绑定ECS")

        self.logger.info("开始解绑ECS与HAVIP")
        ret=self.HAVIP_UnbindEcsFromVip(havip_id=self.havip_id,ecs_id=ecs_id,eni_id=eni_id)
        if ret["code"] != "Network.Success":
            raise "解绑vip和ECS失败,VIP:%s,ECS:%s" % (self.havip_id, ecs_id)

    @task
    def havip_bind_eip(self):
        self.logger.info("开始测试HAVIP绑定/解绑EIP")

        eip_id=self.eip_id

        self.logger.info("获取到弹性公网IP:%s"%eip_id)

        self.logger.info("开始绑定HAVIP:%s和EIP:%s"%(self.havip_id,eip_id))
        ret=self.HAVIP_AssociateEip(eip_id=eip_id,havip_id=self.havip_id)
        if ret["code"]!="Network.Success":
            raise "绑定HAVIP与EIP失败"
        self.logger.info("绑定HAVIP:%s与EIP:%s成功" % (self.havip_id, eip_id))
        self.my_sleep(5,"等待HAVIP绑定EIP")

        self.logger.info("开始解绑HAVIP与EIP")
        ret = self.HAVIP_UnassociateEip(eip_id=eip_id, havip_id=self.havip_id)
        if ret["code"] != "Network.Success":
            raise "解绑HAVIP与EIP失败"
        self.logger.info("解绑HAVIP:%s与EIP:%s成功"%(self.havip_id,eip_id))

    @task
    def del_havip(self):
        self.logger.info("开始删除HAVIP:%s"%self.havip_id)
        ret=self.HAVIP_DeleteVip(havip_id=self.havip_id)
        if ret["code"] != "Network.Success":
            raise "删除HAVIP失败:%s"%self.havip_id
        self.logger.info("删除HAVIP:%s成功"%self.havip_id)