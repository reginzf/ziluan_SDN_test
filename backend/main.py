# -*- coding: UTF-8 -*-
from backend.MyClass.env import Environment
from backend.web import WEB_UI
from backend.MyClass.users import User
from backend.MyClass.thread_control import ThreadControl
from source import Agent_SDN_nolocust
from source.monkey_patch import on_start


class MyUser(User, Agent_SDN_nolocust):
    # 在这里登录
    def __init__(self, env):
        User.__init__(self, env)
        Agent_SDN_nolocust.__init__(self)

    pass


MyUser.on_start = on_start  # 登录信息放在了MyUser中，在task中调用get_env_from_user,可以将user中的信息放入task中，防止多次登录


class MyUser(User):
    pass


def main():
    env = Environment()
    user = MyUser(env)
    thread_control = ThreadControl(user)
    web = WEB_UI(thread_control)

    user.run()
    thread_control.run()
    web.start()


if __name__ == '__main__':
    main()
