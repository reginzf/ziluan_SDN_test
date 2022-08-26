# -*- coding: UTF-8 -*-
import time

import gevent

from backend.MyClass.users import events
from backend.MyClass.myclass import MyDict
from threading import Thread
from backend.log_hander import logger


class ThreadControl:
    def __init__(self, user):
        self.user = user
        self.env = self.user.environment
        # 注册钩子
        events.thread_control_init.fire(thread_control=self)
        self.agent = self.env.agent
        self.running_task = self.user._running_task
        self.abnormal_task = self.user.abnormal_task
        self.abnormal_task_ = self.user.abnormal_task_
        self.stopped_task = self.user.stopped_task

        self.stop_by_adm = MyDict()
        self.renew_task = MyDict()
        self.stop_by_adm_msg = MyDict()

    def run(self):
        gevent.spawn(self.thread_control)
        # t.join()
        # t = Thread(target=self.thread_control, args=())
        # t.start()
        # t.join()

    def thread_control(self):
        while True:
            # 刷新所有task状态
            self.flush_task()
            # 处理异常任务
            if self.abnormal_task:
                # 删除任务配置
                self.note_abnormal_task()
                for name, task in self.abnormal_task.items():
                    # 将异常写入对应log,删除配置
                    try:
                        self.user.loggers[name].getlog().error(msg=task.exc_traceback)
                        del self.env.testcase_cfg[name]
                    except KeyError:
                        pass
                    except Exception:
                        pass
                    # 如果有流量则停止流量
                    if self.env.streams.get(name, False):
                        self.stop_stream(name)
                        self.user.loggers.pop(name, None)
            # 尝试将renew_task重新跑
            # print('renew_task',self.renew_task)
            for taskname_, task in self.renew_task.items():
                try:
                    # 只有running_task需要主动改，其他靠flush
                    self.run_new_taskset(taskname_)
                    # yield {'type': 'rerun', 'task': task['taskname'], 'code': 'success'}
                except Exception as e:
                    # yield {'type': 'rerun', 'task': task['taskname'], 'code': 'failed', 'msg': e.__context__}
                    raise e
            time.sleep(20)

    def get_stop_task(self):
        # 获取停止的task,同时修改runningtask
        stoped_task = MyDict()
        for taskname, task in self.running_task.items():
            if task.dead:
                stoped_task[taskname] = task
        return stoped_task

    def get_abnormal_task(self):
        # 获取异常的task
        abnormal_task = MyDict()
        for taskname, task in self.stopped_task.items():
            if not task.successful():
                abnormal_task[taskname] = task
                # 如果不在abnormal_task_ (历史记录中),则加入历史记录
                if not self.abnormal_task_[taskname]:
                    self.abnormal_task_[taskname] = task
        return abnormal_task

    def note_abnormal_task(self):
        self.user.note_abnormal_task(list(self.abnormal_task.keys()))

    def get_renew_task(self):
        # print('self.user.stop_by_adm', self.stop_by_adm)
        rerun_task = MyDict()
        # 这里需要复制下，不知道为啥用deepcopy会报错...
        for taskname, task in self.stopped_task.items():
            rerun_task[taskname] = task
        # 排除异常的任务
        for taskname, task in self.abnormal_task.items():
            rerun_task.pop(taskname)
        # 排除手工指定停止的任务
        for taskname, task in self.stop_by_adm.items():
            if rerun_task[taskname]:
                rerun_task.pop(taskname)

        return rerun_task

    def stop_taskset(self, taskname):
        # 传入名称，找对应的在运行的实例，如果有则通过抛出异常停止
        taskset = self.user.get_task_by_name(taskname)

        if not taskset:
            return {'type': 'stop', 'taskname': taskname, 'code': 'failed',
                    'msg': 'can not find {} in registed tasks'.format(taskname)}
        # 写入停止时间
        taskset._stoptime = time.strftime('%Y/%m/%d %H:%M:%S')
        # 检查是否在running_task中存在，
        if self.running_task[taskname]:
            task = self.running_task[taskname]
            # 存在的话停止流量、删除logger等
            try:
                # task.stop()  # 强行停止
                self.stop_stream(taskname)  # 传给刘波，停止流量
                self.user.loggers.pop(taskname)  # 移除logger
                try:
                    del self.env.testcase_cfg[taskname]  # 如果有流量配置则删除
                except:
                    pass
                self.stop_by_adm[taskname] = taskset

                return {'type': 'stop', 'taskname': taskname, 'code': 'success'}
            except SystemExit:
                return {'type': 'stop', 'taskname': taskname, 'code': 'success'}
            except Exception as e:
                logger.error(msg=str(e))
                return {'type': 'stop', 'taskname': taskname, 'code': 'failed', 'msg': str(e)}
        # 完成后加入stop_by_adm 中

        return {'type': 'stop', 'taskname': taskname, 'code': 'failed',
                'msg': 'can not find {} in running tasks'.format(taskname)}

    def stop_all_taskset(self):
        res = []
        tasks = self.user._tasks
        for name, task in tasks.items():
            temp = self.stop_taskset(name)
            if temp['code'] != 'success':
                res.append({'taskname': name, 'traceback': temp['msg']})
        logger.info('停止所有任务')
        return {'type': 'stop_all_taskset', 'code': 'success' if not res else 'failed', 'msg': res}

    def run_new_taskset(self, classname, interval=None, run_times=None, loglevel='info', from_web=False):
        # 先从user.tasks中获取对应的taskset
        # 默认情况下interval 和run_times都是None，非None的时候认为是外部传入
        taskset = self.user.get_task_by_name(classname)
        stream_res = None
        if taskset:
            # 处理外部传入
            if from_web:
                # 先处理时间
                taskset._starttime = time.strftime('%Y/%m/%d %H:%M:%S')
                if interval or run_times:
                    taskset.interval = interval
                    taskset.run_times = run_times
                    taskset.ran_times = 0
            # 处理默认情况
            else:
                # 如果没有次数则直接跑，不进行判断
                if not taskset.run_times:
                    pass
                # 如果已经跑的次数大于等于run_times,则停止
                elif taskset.run_times and taskset.ran_times >= taskset.run_times:
                    # 在stop_taskset 会将任务加入stop_by_adm中
                    self.stop_taskset(classname)
                    # 走到这里直接终止
                    return {'type': 'new', 'taskname': classname, 'code': 'success',
                            'msg': 'just start new task'}
        # 开始跑任务，在user.run_new_taskset 中将ran_times+=1，其他不变
        if taskset and self.user.run_new_taskset(classname):
            # 处理流量：
            if hasattr(taskset, 'stream_cfg') and getattr(taskset, 'stream_cfg'):
                # 首次开始
                if self.env.streams[classname] == None:
                    cfg = taskset.stream_cfg
                    stream_res = self.start_stream(classname, cfg)
                # 非首次开始，之前失败的不重新跑
                elif self.env.streams[classname]['res']['message'] != 'success':
                    pass
                # 非首次开始，成功的不动
                else:
                    pass
            try:
                self.stop_by_adm.pop(classname)
                res = {'type': 'new', 'taskname': classname, 'code': 'success',
                       'msg': 'remove task {} from adm stopped tasks'.format(classname)}
            except KeyError:
                res = {'type': 'new', 'taskname': classname, 'code': 'success',
                       'msg': 'just start new task'}

        else:
            # 没找到直接返回
            return {'type': 'new', 'taskname': classname,
                    'msg': 'can not find {} in registered tasks'.format(classname),
                    'code': 'failed'}
        if stream_res:
            res["stream_res"] = stream_res
        return res

    def start_stream(self, classname, cfg):
        msg = {"msgType": "config", "configType": "stream", "authKey": "NRG",
               "params": cfg}
        res = self.agent.send_message(msg)
        self.env.streams[classname] = {'params': cfg, 'res': res}
        return res

    def stop_stream(self, classname):
        temp = self.env.streams.get(classname, False)
        if temp:
            cfg = temp['params']
            cfg['action'] = 'stop'
            msg = {"msgType": "config", "configType": "stream", "authKey": "NRG",
                   "params": cfg}
            res = self.agent.send_message(msg)

    def start_all_tasks(self):
        self.stop_by_adm.clear()
        self.stop_by_adm_msg.clear()
        return self.user.start_all_tasks()

    def show_stream_status(self, tasks: list):
        res = []
        if tasks:
            for task in tasks:
                temp = self.env.streams.get(task)
                if temp:
                    res.append({'task': task, 'cfg': temp['cfg'], 'status': temp['res']})
        else:
            for task in self.env.streams.keys():
                temp = self.env.streams[task]
                res.append({'task': task, 'stream_cfg': temp['cfg'], 'stream_status': temp['res']})
        return res

    def flush_task(self):
        self.stopped_task = self.get_stop_task()
        for taskname, task in self.stopped_task.items():
            self.running_task.pop(taskname)
        self.abnormal_task = self.get_abnormal_task()
        self.user.abnormal_task = self.abnormal_task
        self.renew_task = self.get_renew_task()
        logger.info('running_task:{}\nstopped_task:{}\nabnormal_task:{}\nrenew_task:{}'.format(self.running_task,
                                                                                               self.stopped_task,
                                                                                               self.abnormal_task,
                                                                                               self.renew_task))
