# -*- coding: UTF-8 -*-


from backend.MyClass.task import TaskSet, task,TaskSet
from source.monkey_patch import get_env_from_user
from source import EIP, sendto_weixin


class Test_User(EIP, TaskSet):
    # 在init的时候初始化,在user中，user在实例化测试用例的时候传入的，所以只能在init中修改
    token: str
    """登录用token"""
    authKey = 'NRG'

    # def __init__(self, user):
    #     super(Test_User, self).__init__(user)
    def __init__(self, user):
        TaskSet.__init__(self, user)
        EIP.__init__(self)
        get_env_from_user(self)
        pass

    @task
    def test_param(self):
        # 直接检查支持的参数
        # print(sys.modules)
        # self.sendto_weixin('test')
        print('aaaaaaaaaa')
