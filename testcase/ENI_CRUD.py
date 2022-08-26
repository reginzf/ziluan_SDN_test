# -*- coding: UTF-8 -*-
import time

from backend.MyClass.task import task, TaskSet
from source.monkey_patch import get_env_from_user, on_start
from source import VPC, check, ECS, ENI, SEC
import requests

requests.packages.urllib3.disable_warnings()


class ENI_CRUD(VPC, ECS, ENI, SEC, TaskSet):
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
        self.vpc_name = "ENI_CRUD"
        self.subnet_name = "ENI_CRUD"
        self.ecs_name = "ENI_CRUD"
        # 固定安全组
        self.sg_id = "sg-fh5vt34dwqmk"

    def on_stop(self):
        pass

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
        self.logger.info("查找是否有现成的子网,没有则新建,共需要2个子网")
        ret = self.VPC_describe_subnet(vpc_id=self.vpc_id)
        subnets = ret["res"]
        print("当前已有子网个数:%s" % len(subnets))
        # 存在的子网ID
        exist_subnet_id = []
        if len(subnets) < 2:
            exist_subnet_count = len(subnets)
            # 获取已经存在的子网的CIDR
            exist_subnet_cidr = []
            for i in range(exist_subnet_count):
                subnet = subnets[exist_subnet_count - 1]
                exist_subnet_cidr.append(subnet["cidr"])
                exist_subnet_id.append(subnet["id"])
            print("已有的cidr:%s" % exist_subnet_cidr)
            # 需要至少2个子网,创建缺少的子网
            for i in range(2 - exist_subnet_count):
                subnet_name = self.subnet_name + str(i)
                # 查找一个没有使用的CIDR
                for net in range(254):
                    subnet_cidr = "10.0.%s.0/24" % net
                    # 查看子网CIDR是否存在
                    if subnet_cidr not in exist_subnet_cidr:
                        exist_subnet_cidr.append(subnet_cidr)
                        subnet_gw = "10.0.%s.1" % net
                        self.logger.info("找到一个未使用的cidr:%s" % subnet_cidr)
                        break
                # 创建子网
                ret = self.VPC_create_subnet(vpc_instance=self.vpc_id, name=subnet_name, cidr=subnet_cidr,
                                             gatewayIp=subnet_gw)
                if ret["code"] != "Network.Success":
                    raise "子网创建失败"
                new_subnet_id = ret["res"]["Id"]
                exist_subnet_id.append(new_subnet_id)
                self.logger.info("新建子网成功,子网ID:%s" % new_subnet_id)
        else:
            for subnet in subnets:
                exist_subnet_id.append(subnet["id"])
            self.logger.info("有现成的子网,子网ID:%s" % exist_subnet_id)
        # 由于ENI与SUBNET要在不同的子网,因此这里要区分开子网后续使用
        self.ecs_subnet = exist_subnet_id[0]
        self.eni_subnet = exist_subnet_id[1]

    @task
    def create_ecs(self):
        self.logger.info("查看ecs子网(%s)是否存在ECS,没有则创建" % self.ecs_subnet)
        subnets = self.VPC_describe_subnet(vpc_id=self.vpc_id)["res"]
        for subnet in subnets:
            if subnet["id"] == self.ecs_subnet:
                resources = subnet["bindResources"]
                break
        # 查看是否有ECS
        found = False
        if resources is not None:
            for resource in resources:
                resource_id = resource["reviceId"]
                if str(resource_id).startswith("ecs") and len(resource_id) == len("ecs-fj1xbwyrzu16"):
                    found = True
                    self.ecs_id = resource_id
                    break
        if not found:
            self.logger.info("在子网中没有找到ECS,新建一台ECS")
            self.ECS_RunEcs(vpc_id=self.vpc_id, subnet_id=self.ecs_subnet, name=self.ecs_name, sg_id=self.sg_id)
            self.my_sleep(10, "等待订单生效")
            self.logger.info("检查ecs是否创建成功")
            ecs_ids = self.ECS_get_ecsid_by_ecs_name(name=self.ecs_name)
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
                if not len(ecs_ids):
                    create_success = True
                    break
                self.my_sleep(5, "等待ECS创建成功", 1)
            assert create_success == True, "5分钟内ECS没有创建成功,请检查ECS状态"
            self.ecs_id = ecs_ids[0]
            self.logger.info("ECS创建成功,ecsid:%s" % self.ecs_id)
        else:
            self.logger.info("在ECS子网中找到一台ECS:%s" % self.ecs_id)

    @task
    def create_eni(self):
        self.logger.info("在ENI子网(%s)中创建一个弹性网卡" % self.eni_subnet)
        eni_name = "auto_eni_name"
        sg_id = self.sg_id
        ret = self.ENI_create(eni_name=eni_name, vpc_id=self.vpc_id, sg_id=sg_id, subnet_id=self.eni_subnet)
        self.eni_id = ret["instanceId"]
        self.logger.info("创建ENI成功:%s" % self.eni_id)

    @task
    def bind_eni_to_ecs(self):
        self.logger.info("将ENI(%s)绑定到ECS(%s)" % (self.eni_id, self.ecs_id))
        ret = self.ENI_BindECS(eni_id=self.eni_id, ecs_id=self.ecs_id)
        if ret["status"] != True:
            raise "ENI(%s)绑定ECS(%s)失败,status:%s" % (self.eni_id, self.ecs_id, str(ret["status"]))
        self.logger.info("ENI(%s)绑定ECS(%s)成功" % (self.eni_id, self.ecs_id))
        # 等待状态变为运行中
        s_time = time.time()
        eni_running = False
        while time.time() - s_time < (5 * 60):
            eni = self.ENI_DescribeEni(eni_id=self.eni_id)[0]
            eni_state = eni["status"]
            if eni_state == "RUNNING":
                eni_running = True
                break
            self.my_sleep(10, "等待ENI解绑成功")
        assert eni_running == True, "5分钟内ENI(%s)仍然不为running状态,当前:%s" % (self.eni_id, eni_state)

    @task
    def unbind_eni_to_ecs(self):
        self.logger.info("将ENI(%s)从ECS(%s)解绑" % (self.eni_id, self.ecs_id))
        ret = self.ENI_UnbindEcs(eni_id=self.eni_id)
        if ret["status"] != True:
            raise "ENI(%s)解绑ECS(%s)失败,status:%s" % (self.eni_id, self.ecs_id, str(ret["status"]))
        self.logger.info("ENI(%s)解绑ECS(%s)成功" % (self.eni_id, self.ecs_id))
        # 等待状态变为运行中
        s_time = time.time()
        eni_running = False
        while time.time() - s_time < (5 * 60):
            eni = self.ENI_DescribeEni(eni_id=self.eni_id)[0]
            eni_state = eni["status"]
            if eni_state == "RUNNING":
                eni_running = True
                break
            self.my_sleep(10, "等待ENI解绑成功")
        assert eni_running == True, "5分钟内ENI(%s)仍然不为running状态,当前:%s" % (self.eni_id, eni_state)

    @task
    def del_eni(self):
        self.logger.info("删除ENI:%s" % self.eni_id)
        ret = self.ENI_Delete(eni_id=self.eni_id)
        if ret["status"] != True:
            raise "ENI(%s)删除失败,status:%s" % (self.eni_id, str(ret["status"]))
        self.logger.info("ENI(%s)删除成功" % (self.eni_id))
