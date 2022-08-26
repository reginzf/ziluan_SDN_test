# -*- coding: UTF-8 -*-
import time

from backend.MyClass.task import task, TaskSet
from source.monkey_patch import get_env_from_user, on_start
from source import VPC, ORDER, check, ECS
import requests

requests.packages.urllib3.disable_warnings()


class VPC_SUBNET_ECS(VPC, ECS, TaskSet):
    '''
    创建VPC,创建子网,创建ECS,删除ECS,删除子网,删除VPC
    '''
    authKey = "LBD"

    def __init__(self, user):
        pass
        VPC.__init__(self)
        TaskSet.__init__(self, user)
        # 从user中获取环境变量
        get_env_from_user(self)
        # 从environment中获取配置
        # self.init_cfg()

    def on_start(self):
        self.vpc_name = "VPC_SUBNET_ECS"
        self.subnet_name = "VPC_SUBNET_ECS"
        self.ecs_name = "VPC_SUBNET_ECS"
        self.sg_id="sg-fh5vt34dwqmk"
    def on_stop(self):
        pass

    @task
    def create_vpc(self):
        @check(10, "创建VPC失败", 5, self)
        def check_vpc(vpc_id):
            ret = self.VPC_describe(vpcId=vpc_id)
            res = ret["res"]
            assert len(res) == 1, "未查询到vpc"

        cidr = "10.0.0.0/8"
        subnet_cidr = "10.0.0.0/24"
        vpc_name = self.vpc_name
        subnet_name = self.subnet_name
        # 为避免脏数据,首先查找有没有VPC可用
        exist_vpc = self.VPC_get_vpcid_by_vpc_name(name=vpc_name)
        if len(exist_vpc):
            self.vpc_id = exist_vpc[0]["instanceId"]
        else:
            # 没有现成的就新建一个
            ret = self.VPC_create(name=vpc_name, cidr=cidr, subnet_name=subnet_name, subnet_cidrblock=subnet_cidr)
            if ret["code"] != "Network.Success":
                raise "VPC创建失败"
            res = ret["res"]
            self.vpc_id = res["vpcId"]
        check_vpc(self.vpc_id)

    @task
    def create_subnet(self):
        @check(10, "创建子网失败", 5, self)
        def check_subnet(vpc_id=self.vpc_id, subnet_id=None):
            ret = self.VPC_describe_subnet(vpc_id=vpc_id)
            subnets = ret["res"]
            found = False
            for subnet in subnets:
                sub_id = subnet["id"]
                if sub_id == subnet_id:
                    found = True
                    break
            assert found == True, "创建子网失败,VPC:%s" % vpc_id

        subnet_name = "new_test_subnet"
        subnet_cidr = "10.0.1.0/24"
        gw = "10.0.1.1"
        ret = self.VPC_create_subnet(vpc_instance=self.vpc_id, name=subnet_name, cidr=subnet_cidr, gatewayIp=gw)
        if ret["code"] != "Network.Success":
            raise "子网创建失败"
        self.subnet_id = ret["res"]["Id"]
        check_subnet(subnet_id=self.subnet_id)

    @task
    def create_ecs(self):
        self.ECS_RunEcs(vpc_id=self.vpc_id, subnet_id=self.subnet_id, name=self.ecs_name,sg_id=self.sg_id)
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
        assert create_success == True, "5分钟内ECS没有创建成功,请检查ECS状态"

    # 读取TOP图
    @task
    def get_top(self):
        self.logger.info("开始获取VPC拓扑")
        ret = self.VPC_DescribeVpcTopology(vpc_id=self.vpc_id)
        if ret["code"] != "Network.Success":
            raise "获取拓扑图失败"

    @task
    def del_ecs(self):
        self.logger.info("删除子网中所有的ECS")
        ret=self.VPC_describe_subnet(vpc_id=self.vpc_id)
        subnets=ret["res"]
        ecs_ids=[]
        for subnet in subnets:
            resources=subnet["bindResources"]
            if not resources:
                continue
            for item in resources:
                if str(item["reviceId"]).startswith("ecs-"):
                    ecs_ids.append(str(item["reviceId"]))
        self.logger.info("获取到ECS ID:%s\n执行关机操作" % ecs_ids)
        self.ECS_poweroff(ecs_ids=ecs_ids)
        s_time = time.time()
        self.logger.info("检查关机是否成功")
        while time.time() - s_time < (5 * 60):
            for ecs_id in ecs_ids:
                self.logger.info("开始检查ecs:%s状态" % ecs_id)
                ecs_state = self.ECS_DescribeEcs(instance_id=ecs_id)[0]["status"]
                if ecs_state == "DOWN":
                    self.logger.info("ecs:%s关机成功,执行删除操作" % ecs_id)
                    self.ECS_DeleteEcs(ecs_ids=ecs_id)
                    self.logger.info("ECS(%s)删除成功"%ecs_id)
                    ecs_ids.remove(ecs_id)
                else:
                    self.logger.info("ecs:%s 当前状态为%s,继续等待" % (ecs_id, ecs_state))
            if not len(ecs_ids):
                break
            self.my_sleep(5, "等待ECS关机")
        self.my_sleep(60, "等待ECS销毁")

    @task
    def del_subnet(self, vpc_id=None, subnet_id=None):
        self.logger.info("删除VPC中所有的子网")
        ret = self.VPC_describe_subnet(self.vpc_id)
        subnets = ret["res"]
        for subnet in subnets:
            subnet_id = subnet["id"]
            ret = self.VPC_delete_subnet(vpc_id=self.vpc_id, subnet_id=subnet_id)
            if ret["code"] != "Network.Success":
                raise "子网删除失败"
        self.my_sleep(5, "等待子网删除完成")

    @task
    def del_vpc(self):
        # 获取所有的子网然后删除
        ret = self.VPC_describe_subnet(vpc_id=self.vpc_id)
        subnets = ret["res"]
        for subnet in subnets:
            sub_id = subnet["id"]
            self.del_subnet(vpc_id=self.vpc_id, subnet_id=sub_id)

        ret = self.VPC_delete(instance_id=self.vpc_id)
        if ret["code"] != "Network.Success":
            raise "VPC删除失败,VPCID:%s" % self.vpc_id


if __name__ == '__main__':
    pass
