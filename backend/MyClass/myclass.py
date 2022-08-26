# -*- coding: UTF-8 -*-
from source import Agent_SDN_nolocust
import ctypes, sys, traceback
import threading
from threading import Thread


class MyDict(dict):
    def __missing__(self, key):
        return None


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


class TaskSetMeta(type):
    """
    Meta class for the main User class. It's used to allow User classes to specify task execution
    ratio using an {task:int} dict, or a [(task0,int), ..., (taskN,int)] list.
    """

    def __new__(mcs, classname, bases, class_dict):
        # 处理tasks
        class_dict["tasks"] = get_tasks_from_base_classes(bases, class_dict)
        # 处理class
        try:
            if reload_class():
                temp = importlib.import_module('source')
                importlib.reload(temp)
        except:
            pass
        # for base in bases:
        #     print(base.__name__)
        #     if rd.get(base.__name__, False):
        #         print('rd.get(base.__name__',rd.get(base.__name__).EIP_flag)
        #         new_bases.append(rd[base.__name__])
        #     else:
        #         new_bases.append(base)
        # new_bases = tuple(new_bases)
        return type.__new__(mcs, classname, bases, class_dict)


class UserMeta(type):
    def __new__(mcs, classname, bases, class_dict):
        # gather any tasks that is declared on the class (or it's bases)
        tasks = get_tasks_from_base_classes(bases, class_dict)
        class_dict['tasks'] = tasks
        if not class_dict.get("abstract"):
            # Not a base class
            class_dict["abstract"] = False
        return type.__new__(mcs, classname, bases, class_dict)


class MyThread(Thread):
    def __init__(self, *args, **kwargs):
        super(MyThread, self).__init__(*args, **kwargs)
        self.exitcode = 0
        self.exception = None
        self.exc_traceback = ''
        self.exit_adm = False

    def run(self) -> None:
        try:
            if self._target:
                self._target(*self._args, **self._kwargs)
        # except SystemExit:
        #     self.exitcode = 2
        #     self.exit_adm = True
        except Exception as e:
            self.exitcode = 1
            self.exception = e
            self.exc_traceback = ''.join(traceback.format_exception(*sys.exc_info()))
        finally:
            del self._target, self._args, self._kwargs

    def get_id(self):
        if hasattr(self, '_thread_id'):
            return self._thread_id
        for id, thread in threading._active.items():
            if thread is self:
                return id

    def raise_exception(self):
        thread_id = self.get_id()
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id,
                                                         ctypes.py_object(SystemExit))
        if res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)


import os, importlib

SOURCE_PATH = os.path.join(os.path.abspath(os.path.curdir), '../source')
SOURCE_CHANGE = {}  # 记录修改时间


def changed_files():
    files = []
    for file in os.listdir(SOURCE_PATH):
        files.append(os.path.join(SOURCE_PATH, file))

    res = []
    for file in files:
        data = os.stat(file)
        if data.st_mtime != SOURCE_CHANGE.get(file, False):
            SOURCE_CHANGE[file] = data.st_mtime
            res.append(file)
    return res


def reload_class():
    c_files = changed_files()  # 获取变化的文件
    reloads = {}  # 获取变化的类
    for file in c_files:
        file = os.path.abspath(file).split('\\')[-1].split('.py')[0]
        if file.endswith('module'):
            try:
                import_file = importlib.import_module('source.{}'.format(file))
                importlib.reload(import_file)
                for name in dir(import_file):
                    try:
                        if name != 'Agent_SDN_nolocust' and issubclass(getattr(import_file, name), Agent_SDN_nolocust):
                            exec('{}=getattr(import_file,name)'.format(name))  # 获取更新的类
                            reloads[name] = getattr(import_file, name)
                    except:
                        pass
            except:
                pass
    return reloads
