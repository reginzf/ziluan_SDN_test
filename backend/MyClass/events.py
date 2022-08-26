import logging
import traceback


class EventHook:
    """
    使用方式：
        my_event = EventHook()
        def on_my_event(a, b, **kw):
            print("Event was fired with arguments: %s, %s" % (a, b))
        my_event.add_listener(on_my_event)
        my_event.fire(a="foo", b="bar")
    """

    def __init__(self):
        self._handlers = []

    def add_listener(self, handler):
        self._handlers.append(handler)
        return handler

    def remove_listener(self, handler):
        self._handlers.remove(handler)

    def fire(self, *, reverse=False, **kwargs):
        if reverse:
            handlers = reversed(self._handlers)
        else:
            handlers = self._handlers
        for handler in handlers:
            try:
                handler(**kwargs)
            except Exception:
                logging.error("Uncaught exception in event handler: \n%s", traceback.format_exc())


class Events:
    init: EventHook
    """
    在环境初始化的时候执行，传入environment,可以用这个向环境中注入参数
    environment:Environment
    """
    web_init: EventHook
    """
    在web初始化配置的时候执行
    可以在这里对flask进行配置self.app = Flask(__name__)，注册路由啥的
    传入app
    """
    user_init: EventHook
    """
    在user初始化的时候执行，传入user
    user:User
    """
    testcase_start: EventHook
    """
    在测试用例开始的时候运行，传入测试用例的实例  
    task_instance: 测试用例实例 TaskSet
    """
    thread_control_init: EventHook
    """
    在thread_control的时候执行，传入thread_control，可以在这里直接控制任务
    thread_control:ThreadControl
    """
    task_init: EventHook
    """
    在指定任务初始化的时候执行？为啥不用on_start?
    """
    add_class: EventHook
    """
    在将测试用例class添加到user中之后调用
    可以在这里直接将配置写入测试用例class中
    """

    def __init__(self):
        for name, value in vars(type(self)).items():
            if value == EventHook:
                setattr(self, name, value())

        for name, value in self.__annotations__.items():
            if value == EventHook:
                setattr(self, name, value())


events = Events()
