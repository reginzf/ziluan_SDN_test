# -*- coding: UTF-8 -*-
import importlib
import os
import sys
import time
import traceback
from copy import deepcopy

import gevent
from gevent import GreenletExit
from typing_extensions import final

from backend.MyClass.events import events
from backend.MyClass.myclass import MyDict, UserMeta
from backend.MyClass.task import TaskSet
from backend.log_hander import MyLog, logger


class User(metaclass=UserMeta):
    tasks = MyDict()
    loggers = MyDict()
    abstract = True

    def __init__(self, environment):
        # super().__init__()
        self.environment = environment
        print(environment.data)
        events.user_init.fire(user=self)
        self.logger = logger
        self.agent = self.environment.agent
        self.testcase_cfg = self.environment.testcase_cfg
        print(self.testcase_cfg)
        self._taskset_instance = MyDict()
        self.running_task = MyDict()
        self.abnormal_task = MyDict()
        self.abnormal_task_ = MyDict()
        self.stopped_task = MyDict()
        self.task_num = len(self.tasks)

    def get_taskset_instance(self, name, taskset):
        if self._taskset_instance[name]:
            return self._taskset_instance[name]
        else:
            temp = taskset(self)
            self._taskset_instance[name] = temp
            return temp

    @property
    def _tasks(self):
        return self.tasks

    @property
    def _running_task(self):
        return self.running_task

    def on_start(self):
        """
        Called when a User starts running.
        """
        pass

    def on_stop(self):
        """
        Called when a User stops running (is killed)
        """
        pass

    @final
    def run(self):
        try:
            # run the TaskSet on_start method, if it has one
            self.on_start()
            for name, taskset in self.tasks.items():
                # 每个taskset 创建一个进程，并发执行
                # task_instance = taskset(self)
                task_instance = self.get_taskset_instance(name, taskset)
                events.testcase_start.fire(task_instance=task_instance)
                # 加入running_task，后续会被thread_control拉起来
                t = gen_thread(task_instance)  # 打了monkeypatch后spwan后直接开始运行
                self.running_task.update(t)
        except (GreenletExit):
            # run the on_stop method, if it has one
            self.logger.warning('停止User')
            self.on_stop()
        # 监控已经在跑的taskset，如果正常退出则继续跑，如果异常，则退出并打印告警
        except Exception as e:
            # 如果on_start，进程错误啥的，打log，不影响主进程
            self.logger.error("%s\n%s", e, traceback.format_exc())
        finally:
            self.on_stop()

    def remove_task_from_running_task(self, taskset: TaskSet):
        # 如果有在跑的，则杀死对应任务，并从running_task中移除
        temp = None
        if self.running_task[taskset.__name__]:
            temp = taskset.__name__
            # self.running_task[temp].stop()  # 强行停止
            self.running_task.pop(temp)
        return temp

    # 下面是给接口用的函数
    def get_task_by_name(self, taskname):

        res = None
        if self.tasks[taskname]:
            res = self.tasks[taskname]
        return res

    def run_new_taskset(self, taskname):
        taskset = self.get_task_by_name(taskname)
        if taskset:
            # 如果有在跑的，则停止对应任务，重新跑。跑的次数清0
            if self.remove_task_from_running_task(taskset):
                taskset.ran_times = 0
            # 准备开始跑，ran_times + 1
            taskset.ran_times += 1
            task_instance = self.get_taskset_instance(taskname, taskset)  # 已优化为单例
            events.testcase_start.fire(task_instance=task_instance)
            # 获取logger
            temp = self.loggers.get(taskname, None)
            if not temp:
                temp = MyLog(taskname)
                self.loggers[taskname] = temp
            else:
                temp.reset_log()

            task_instance.logger = temp.getlog()
            t = gen_thread(task_instance)
            self.running_task.update(t)
            # t['task'].join()
            # 加入running_task
            # self.running_task[t['taskname']] = t['task']
            return True
        else:
            return False

    # 注册taskset
    def registe_testcase_class(self, filename: str, classname: str):
        res = {'type': 'regist', 'taskname': classname, 'code': 'success'}
        # 先查重
        if self.tasks[classname]:
            # 查到有重复的，返回已注册
            res['code'], res['msg'] = 'failed', 'class {} has been registed!'.format(classname)
        else:
            # 不存在重复的，执行注册操作
            try:
                import_file = importlib.import_module('testcase.{filename}'.format(filename=filename.split('.')[0]))
                importlib.reload(import_file)  # 如果之前引入了，这里再reload下
                import_class = getattr(import_file, classname)

                self.tasks[classname] = import_class
                events.add_class.fire(import_class=import_class)
            except Exception:
                res['code'], res['msg'] = 'failed', traceback.format_exc()
        return res

    def show_running_task(self):
        res = []
        for name, taskset in self.running_task.items():
            # res.append(name)
            task_class = self.get_task_by_name(name)
            res.append({'name': name, 'interval': task_class.interval, 'runtimes': task_class.run_times,
                        'rantimes': task_class.ran_times})
            # task = taskset._target

        #     res.append({'name': name, 'interval': taskset.interval, 'runtimes': taskset.run_times,
        #                 'rantimes': taskset.ran_times})
        self.logger.info('当前正在运行的测试用例:{}'.format(self.running_task.keys()))
        return {'type': 'show_running_task', 'msg': res, 'code': 'success'}

    def show_abnormal_task(self):
        tasknames = list(self.abnormal_task_.keys())
        return {'type': 'show_abnormal_task', 'msg': tasknames, 'code': 'success'}

    def remove_abnormal_task(self, taskname):
        if self.abnormal_task_[taskname]:
            self.abnormal_task_.pop(taskname)
            return {'type': 'remove_abnormal_task', 'msg': taskname, 'code': 'success'}
        return {'type': 'remove_abnormal_task', 'msg': 'can not find abnormal task:{}'.format(taskname),
                'code': 'failed'}

    def show_registed_taskset(self):
        tasknames = list(self.tasks.keys())
        return {'type': 'show_registed_taskset', 'msg': tasknames, 'code': 'success'}

    def remove_taskcase_class(self, filename, classname):
        try:
            # 先查有没有对应的taskset
            taskset = self.get_task_by_name(classname)
            if taskset:
                # 移除引入
                self.tasks.pop(classname)
                # 获取import_path
                path = import_path(filename, classname)

                sys.modules.pop(path)
                self.logger.warning('移除class {} 成功'.format(classname))
                return {'type': 'remove_taskcase_class', 'taskname': classname, 'code': 'success'}
        except Exception as e:
            return {'type': 'remove_taskcase_class', 'taskname': classname, 'code': 'failed',
                    'msg': str(e)}

    def reload_all(self):
        # 加载所有在testcase下的文件，并找出testcase
        # renew_tasks = MyDict()
        self.tasks.clear()
        self._taskset_instance.clear()
        testcase_path = os.path.join(os.path.abspath(os.path.curdir), '../testcase')
        for filename in os.listdir(testcase_path):

            if filename.endswith('py'):
                filename = filename.split('.py')[0]
                try:
                    # 移除引入,默认filename和classname是一样的
                    self.remove_taskcase_class(filename, filename)

                    import_file = importlib.import_module(
                        'testcase.{filename}'.format(filename=filename))
                    importlib.reload(import_file)
                    for f in dir(import_file):
                        temp = getattr(import_file, f) if f != 'TaskSet' else None
                        if temp:
                            try:
                                if issubclass(temp, TaskSet):
                                    importlib.reload(import_file)
                                    # renew_tasks[f] = temp
                                    self.tasks[f] = temp
                                    # 注册到events里
                                    events.add_class.fire(import_class=temp)
                            except TypeError as e:
                                # 忽略不是class类型的参数
                                # raise e
                                pass
                except ImportError as e:
                    # 忽略ImportError
                    pass
                except Exception as e:
                    return {'type': 'reload_all', 'code': 'failed', 'msg': str(e)}
        # self.tasks = renew_tasks
        self.logger.info('重新加载所有class：{}'.format(self.tasks.keys()))
        return {'type': 'reload_all', 'code': 'success', 'msg': list(self.tasks.keys())}

    def start_all_tasks(self):
        res = []
        for name, taskset in self.tasks.items():
            if self.run_new_taskset(name):
                pass
            else:
                res.append(name)
        return {'type': 'start_all_tasks', 'code': 'success' if not res else 'failed', 'msg': res}

    # 通知接口写下边~
    def note_abnormal_task(self, tasks: list):
        # 发送给刘波
        for task in tasks:
            # 获取authKey，从class中读取，不行从配置文件中读取，最后使用默认值
            authKey = ''
            try:
                temp = self.get_task_by_name(task)
                # 将stoptime写入类：
                temp._stoptime = time.strftime('%Y/%m/%d %H:%M:%S')
                if hasattr(temp, 'authKey') and temp.authKey:
                    authKey = temp.authKey
                if not authKey:
                    authKey = self.environment.testcase_cfg[task].get('authKey', '')
            except Exception as e:
                logger.warning(msg="未在{}.json中发现authKey配置，使用全局配置".format(task) + str(e))
            self.note_liubo('任务{}异常，请检查状态'.format(task), authKey)

    def start_env_stream(self, cfg, task_name):
        if cfg:
            cfg['callback'] = cfg['callback'].format(self.environment.web_ui_cfg['local_interface_address'], task_name)
            self.start_stream(task_name, cfg)

    def start_stream(self, classname, cfg):
        """
        开始打流
        :param classname:
        :param cfg:
        :return:
        """
        # 检查是否携带taskId:
        if not cfg['taskId']:
            cfg['taskId'] = classname
        if not cfg['callback']:
            cfg['callback'] = 'http://{}:{}/stop_taskset/EIP_2_1'.format(
                self.environment.agent_data['host'], self.environment.agent_data['port'])

        msg = deepcopy(self.agent.config_stream_header)
        msg['params'] = cfg
        msg['configType'] = 'stream'
        res = self.agent.send_message(msg)
        # 将命令行和结果保存到streams中
        self.environment.streams[classname] = {'params': cfg, 'res': res}
        return res

    def stop_stream(self, classname, cfg=None):
        """
        停止流量
        :param classname:
        :param cfg:
        :return:
        """
        msg = deepcopy(self.agent.config_stream_header)
        # 有cfg直接按cfg发：
        if cfg:
            msg['params'] = cfg
        else:
            # 没有cfg检查本地有没配置
            temp = self.environment.streams[classname]
            if temp:
                cfg = temp['params']
                msg = deepcopy(self.agent.config_stream_header)
                msg['params'] = cfg
            else:
                # 本地没配置直接返回
                return
        # 动作一定是stop
        cfg['action'] = 'stop'
        res = self.agent.send_message(msg)
        self.environment.streams[classname] = {'params': cfg, 'res': res}
        return res

    def stream_status(self, classname):
        """
        获取流状态
        :param classname:
        :return: res
        """
        msg = deepcopy(self.agent.query_stream_header)
        msg['params'] = {'taskId': classname}
        res = self.agent.send_message(msg)
        # 处理状态
        return res

    def note_liubo(self, _msg, authKey):
        msg = deepcopy(self.agent.report_header)
        if authKey:
            msg['msg']['owner'] = authKey
        msg['msg']['msg'] = _msg
        res = self.agent.send_message(msg)
        return res


def gen_thread(taskset_instance):
    # return {
    #     'taskname': taskset_instance.__class__.__name__,
    #     'task': ThreadClass(target=taskset_instance.run, args=())
    # }
    return {taskset_instance.__class__.__name__: gevent.spawn(taskset_instance.run)}


def import_path(filename, classname):
    return 'testcase.{filename}'.format(filename=filename.split('.')[0])
