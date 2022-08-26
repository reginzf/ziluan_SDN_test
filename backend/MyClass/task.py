from typing import Callable, List, Union, TypeVar, Type, overload
from typing_extensions import final
from backend.MyClass.myclass import MyDict, TaskSetMeta
import random, logging, time
from backend.log_hander import logger

TaskT = TypeVar("TaskT", bound=Union[Callable[..., None], Type["TaskSet"]])


@overload
def task(weight: TaskT) -> TaskT:
    ...


@overload
def task(weight: int) -> Callable[[TaskT], TaskT]:
    ...


def task(weight: Union[TaskT, int] = 1) -> Union[TaskT, Callable[[TaskT], TaskT]]:
    def decorator_func(func):
        if func.__name__ in ["on_stop", "on_start"]:
            logging.warning(
                "You have tagged your on_stop/start function with @task. This will make the method get called both as a task AND on stop/start."
            )  # this is usually not what the user intended
        if func.__name__ == "run":
            raise Exception(
                "User.run() is a method used internally by Locust, and you must not override it or register it as a task"
            )
        func.locust_task_weight = weight
        return func

    if callable(weight):
        func = weight
        weight = 1
        return decorator_func(func)
    else:
        return decorator_func


def tag(*tags: str) -> Callable[[TaskT], TaskT]:
    def decorator_func(decorated):
        if hasattr(decorated, "tasks"):
            decorated.tasks = list(map(tag(*tags), decorated.tasks))
        else:
            if "locust_tag_set" not in decorated.__dict__:
                decorated.locust_tag_set = set()
            decorated.locust_tag_set |= set(tags)
        return decorated

    if len(tags) == 0 or callable(tags[0]):
        raise ValueError("No tag name was supplied")

    return decorator_func


def get_tasks_from_base_classes(bases, class_dict):
    new_tasks = []
    res = MyDict()
    for base in bases:
        if hasattr(base, "tasks") and base.tasks:
            new_tasks += base.tasks

    if "tasks" in class_dict and class_dict["tasks"] is not None:
        tasks = class_dict["tasks"]
        if isinstance(tasks, dict):
            tasks = tasks.items()

        for task in tasks:
            if isinstance(task, tuple):
                task, count = task
                for _ in range(count):
                    new_tasks.append(task)
            else:
                new_tasks.append(task)

    for item in class_dict.values():
        if "locust_task_weight" in dir(item):
            for i in range(item.locust_task_weight):
                new_tasks.append(item)
    for task in new_tasks:
        res[task.__name__] = task

    return res


class TaskSet_(metaclass=TaskSetMeta):
    tasks = MyDict()
    _user: "User"
    _parent: "User"
    ran_times = 0
    interval = None
    run_times = None
    stream_flag = False
    logger: "logging.Logger"
    stream_cfg = {}
    _starttime = '-/-'
    _stoptime = '-/-'

    def __init__(self, parent: "User") -> None:
        self._task_queue: List[Callable] = []
        if isinstance(parent, TaskSet):
            self._user = parent.user
        else:
            self._user = parent
        self._parent = parent
        # if this class doesn't have a min_wait, max_wait or wait_function defined, copy it from Locust

    @property
    def user(self) -> "User":
        """:py:class:`User <locust.User>` instance that this TaskSet was created by"""
        return self._user

    @property
    def parent(self):
        """Parent TaskSet instance of this TaskSet (or :py:class:`User <locust.User>` if this is not a nested TaskSet)"""
        return self._parent

    def on_start(self):
        pass

    def on_stop(self):
        pass

    def start_stream(self, serverIp, serverPort, clientIp, streamType: Union['tcp', 'udp'], speed: int, action='start',
                     vip=None, vport=None):

        params = {"serverIp": serverIp, "serverPort": serverPort, "clientIp": clientIp, "streamType": streamType,
                  "speed": speed, 'action': action}
        if vip:
            params['vip'] = vip
            params['vport'] = vport
        return {"msgType": "config", "configType": "stream", "authKey": "LBD", "params": params}

    def wait(self):
        if self.interval:
            time.sleep(self.interval)

    def schedule_task(self, task_callable, first=False):
        """
        Add a task to the User's task execution queue.

        :param task_callable: User task to schedule.
        :param first: Optional keyword argument. If True, the task will be put first in the queue.
        """
        if first:
            self._task_queue.insert(0, task_callable)
        else:
            self._task_queue.append(task_callable)

    def get_next_task(self):
        if not self.tasks:
            raise Exception(
                f"No tasks defined on {self.__class__.__name__}. use the @task decorator or set the tasks property of the TaskSet"
            )
        return random.choice(self.tasks)

    @final
    def run(self):
        try:
            self.on_start()
            # 没有tasks，raise异常
            if not self.tasks:
                self.logger.error('未发现task装饰的函数！')
                raise Exception('未发现task装饰的函数！')
            # 然后再跑
            for name in self.tasks.keys():
                self.execute_task(self.tasks[name])
            self.on_stop()
            self.wait()
        except Exception as e:
            self.on_stop()
            raise e

    def execute_task(self, task):
        # check if the function is a method bound to the current locust, and if so, don't pass self as first argument
        if hasattr(task, "__self__") and task.__self__ == self:
            # task is a bound method on self
            task()
        elif hasattr(task, "tasks") and issubclass(task, TaskSet):
            # task is another (nested) TaskSet class
            task(self).run()
        else:
            # task is a function
            task(self)

    def init_cfg(self):
        if not self.user.environment.testcase_cfg.get(self.__class__.__name__, None):
            try:
                self.user.environment.get_testcase_cfg(self.__class__.__name__)
            except Exception:
                self.user.testcase_cfg[self.__class__.__name__] = {}
                self.user.logger.info('读取{}配置失败,尝试直接从测试用例中读取'.format(self.__class__.__name__))
        for key, value in self.user.testcase_cfg[self.__class__.__name__].items():
            self.__setattr__(key, value)


class TaskSet(TaskSet_):
    def sendto_weixin(self, msg, authKey=None):
        """
        将信息发送到liubo的框架上，必须传入self
        :param msg:
        :param authKey:
        :param self:
        :return:
        """
        if not self:
            raise ValueError('请将测试用例实例self传入self中')
        if not authKey:
            name = self.__class__.__name__
            try:
                temp = self.user.get_task_by_name(name)
                if hasattr(temp, 'authKey') and temp.authKey:
                    authKey = temp.authKey
                if not authKey:
                    authKey = self.user.environment.testcase_cfg[name].get('authKey', '')
            except Exception as e:
                logger.warning(msg="未在{}.json中发现authKey配置，使用全局配置".format(name) + str(e))
            self.user.note_liubo(name + ':' + msg, authKey)
