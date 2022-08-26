# -*- coding: UTF-8 -*-
import json
import os
import time
from copy import deepcopy

import gevent
from flask import Flask, request, flash, redirect, send_from_directory
from flask_cors import CORS
from gevent import pywsgi
from werkzeug.utils import secure_filename

from backend.MyClass.events import events
from backend.MyClass.gen_api import Api_Generater
from backend.MyClass.thread_control import ThreadControl

UPLOAD_FOLDER = '../testcase'
UPLOAD_FOLDER_CONFIG = '../testcase_config'
ALLOWED_EXTENSIONS = {'py', 'json'}
LOG_FOLDER = 'logs'
SOURCE_FOLDER = '../source'

API_KEYS = {'data': '载荷', 'args_with_data': '带默认值的参数', 'to_edit': '带方法的参数', 'res': '接口返回'}


class WEB_UI:
    def __init__(self, thread_control: ThreadControl):
        self.thread_control = thread_control
        self.user = self.thread_control.user
        self.environment = self.user.environment

        app = Flask(__name__)

        # cors = CORS(app, resources={r"/api/*": {"origins": "*"}}) # 所有资源都是动态返回,直接CORS(APP)
        CORS(app)

        app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
        app.config['UPLOAD_FOLDER_CONFIG'] = UPLOAD_FOLDER_CONFIG
        app.config['SESSION_TYPE'] = 'filesystem'  # flask 以wsgi方式跑，部分配置未初始化，需手动置顶
        app.secret_key = 'super secret key'

        self.app = app
        web_ui_cfg = self.environment.web_ui_cfg
        self.host = web_ui_cfg['host']
        self.port = web_ui_cfg['port']

        events.web_init.fire(app=self.app)

        @app.route('/run_new_taskset/<string:taskname>', methods=['POST', 'GET'])
        def run_new_taskset(taskname):
            interval, run_times = None, None
            res = {'type': 'run_new_taskset', 'code': 'failed', 'msg': 'invalid data'}
            # 手动操作，先尝试清除stream的信息
            self.environment.streams.pop(taskname, None)
            if request.method == 'POST':
                try:
                    data = json.loads(request.data)
                    interval = int(data['interval'])
                    run_times = int(data['runtimes'])
                except ValueError:
                    return res
            try:
                remove_taskcase_class(taskname, taskname)
                registe_testcast_class(taskname, taskname)
            except Exception as e:
                res['msg'] = 'remove or registe error,please operate manually, error:{}'.format(str(e))
                return res
            res = self.thread_control.run_new_taskset(taskname, interval, run_times, from_web=True)
            # 清除错误信息
            if res['code'] == 'success':
                self.thread_control.stop_by_adm_msg.pop(taskname, None)
            return res

        @app.route('/stop_taskset/<string:taskname>', methods=['POST', 'GET'])
        def stop_taskset(taskname):
            if request.method == 'POST':
                data = json.loads(request.data)
                # 处理刘波来的数据

                # {"type":"error","user":"liubo","msg":"xxx"}
                user = data.get('owner', None)
                temp = self.user.get_task_by_name(taskname)
                if user and temp:
                    self.user.note_abnormal_task([taskname])
                    self.thread_control.stop_by_adm_msg[taskname] = data

                    # 处理手动调接口来的数据，直接return
                else:
                    return {'type': 'stop_taskset', 'code': 'failed', 'msg': 'invalid data'}
            return self.thread_control.stop_taskset(taskname)

        @app.route('/stop_all_taskset', methods=['POST', 'GET'])
        def stop_all_taskset():
            return self.thread_control.stop_all_taskset()

        @app.route('/registe_testcast_class/<string:filename>/<string:classname>', methods=['POST', 'GET'])
        def registe_testcast_class(filename, classname):
            return self.user.registe_testcase_class(filename, classname)

        @app.route('/remove_taskcase_class/<string:filename>/<string:classname>')
        def remove_taskcase_class(filename, classname):
            return self.user.remove_taskcase_class(filename, classname)

        @app.route('/show_running_task', methods=['GET'])
        def show_running_task():
            return self.user.show_running_task()

        @app.route('/show_abnormal_task', methods=['GET'])
        def show_abnormal_task():
            return self.user.show_abnormal_task()

        @app.route('/show_registed_taskset', methods=['POST', 'GET'])
        def show_registed_taskset():
            return self.user.show_registed_taskset()

        @app.route('/remove_abnormal_task/<string:taskname>', methods=['POST', 'GET'])
        def remove_abnormal_task(taskname):
            return self.user.remove_abnormal_task(taskname)

        @app.route('/reload_all', methods=['POST', 'GET'])
        def reload_all():
            return self.user.reload_all()

        @app.route('/start_all_tasks', methods=['POST', 'GET'])
        def start_all_tasks():
            return self.thread_control.start_all_tasks()

        @app.route('/show_adm_stopped_tasks', methods=['GET'])
        def show_adm_stopped_tasks():
            names = []
            for name, task in self.thread_control.stop_by_adm.items():
                temp = self.thread_control.stop_by_adm_msg[name]
                if temp:
                    names.append({'taskname': name, "msg": temp})
                else:
                    names.append(name)
            return {'type': 'show_adm_stopped_tasks', 'tasks': names}

        @app.route('/show_stream_status', methods=['GET'])
        def show_stream_status():
            data = []
            names = []
            try:
                data = json.loads(request.data)
            except:
                pass
            if data:
                try:
                    names = data['tasks']
                except ValueError:
                    return {'type': 'show_stream_status', 'code': 'error', 'msg': 'invalid data'}
            return {'type': 'show_stream_status', 'code': 'success',
                    'msg': self.thread_control.show_stream_status(names)}

        @app.route('/upload', methods=['GET', 'POST'])
        def upload():
            if request.method == 'POST':
                if 'file' not in request.files:
                    flash('No file part')
                    return redirect(request.url)
                file = request.files['file']
                if not file.filename:
                    flash('No selected file')
                    return redirect(request.url)
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    return '''
            <!doctype html>
            <title>上传测试用例</title>
            <h1>上传成功</h1>
            <h1>上传测试用例</h1>
            <form method=post enctype=multipart/form-data>
              <input type=file name=file>
              <input type=submit value=Upload>
            </form>
            '''
            return '''
            <!doctype html>
            <title>上传测试用例</title>
            <h1>上传测试用例</h1>
            <form method=post enctype=multipart/form-data>
              <input type=file name=file>
              <input type=submit value=Upload>
            </form>
            '''

        @app.route('/upload_config', methods=['GET', 'POST'])
        def upload_config():
            # 上传测试点配置文件
            if request.method == 'POST':
                if 'file' not in request.files:
                    flash('No file part')
                    return redirect(request.url)
                file = request.files['file']
                if not file.filename:
                    flash('No selected file')
                    return redirect(request.url)
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER_CONFIG'], filename))
                    return '''
             <!doctype html>
             <title>上传配置文件</title>
             <h1>上传成功</h1>
             <h1>上传配置文件</h1>
             <form method=post enctype=multipart/form-data>
               <input type=file name=file>
               <input type=submit value=Upload>
             </form>
             '''
            return '''
             <!doctype html>
             <title>上传配置文件</title>
             <h1>上传配置文件</h1>
             <form method=post enctype=multipart/form-data>
               <input type=file name=file>
               <input type=submit value=Upload>
             </form>
             '''

        @app.route('/delete_file_config', methods=['GET', 'POST'])
        def delete_file_config():
            # 删除配置文件
            if request.method == 'POST':
                data = json.loads(request.data)
                filename = data.get('file', None)
                if filename:
                    try:
                        os.remove(os.path.join(UPLOAD_FOLDER_CONFIG, filename))
                    except FileNotFoundError as e:
                        msg = os.listdir(UPLOAD_FOLDER_CONFIG)
                        return {'type': 'delete_file_config', 'msg': msg, 'code': 'error', 'error_msg': str(e)}
                    msg = os.listdir(UPLOAD_FOLDER_CONFIG)
                    return {'type': 'delete_file_config', 'msg': msg, 'code': 'success'}
            msg = os.listdir(UPLOAD_FOLDER_CONFIG)
            return {'type': 'get_files_config', 'msg': msg, 'code': 'success'}

        @app.route('/delete_file', methods=['GET', 'POST'])
        def delete_file():
            if request.method == 'POST':
                data = json.loads(request.data)
                filename = data.get('file', None)
                if filename:
                    try:
                        os.remove(os.path.join(UPLOAD_FOLDER, filename))
                    except FileNotFoundError as e:
                        msg = os.listdir(UPLOAD_FOLDER)
                        return {'type': 'delete_file', 'msg': msg, 'code': 'error', 'error_msg': str(e)}
                    msg = os.listdir(UPLOAD_FOLDER)
                    return {'type': 'delete_file', 'msg': msg, 'code': 'success'}
            msg = os.listdir(UPLOAD_FOLDER)
            return {'type': 'get_files', 'msg': msg, 'code': 'success'}

        @app.route('/show_class', methods=['GET'])
        def show_class():
            # 获取指定文件夹下的所有文件
            file_data = []
            data_template = {
                'name': '',
                'size': 0,
                'last_modify': '',
                'description': '',
                'status': '未加载'
            }
            for file in os.listdir(UPLOAD_FOLDER):
                if file.endswith('.py'):
                    temp = deepcopy(data_template)
                    data = os.stat(os.path.join(UPLOAD_FOLDER, file))
                    temp['name'] = file
                    temp['size'] = data.st_size
                    temp['last_modify'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data.st_mtime))
                    temp['description'] = ''
                    if self.user.tasks.get(file.split('.py')[0], False):
                        temp['status'] = '已加载'
                    file_data.append(temp)
            return {'type': 'show_class_config', 'msg': file_data, 'code': 'success'}

        @app.route('/show_class_config', methods=['GET'])
        def show_class_config():
            # 获取指定文件夹下的所有文件
            file_data = []
            data_template = {
                'name': '',
                'size': '',
                'last_modify': '',
                'testcase_name': ''
            }
            for file in os.listdir(UPLOAD_FOLDER_CONFIG):
                if file.endswith('.json'):
                    temp = deepcopy(data_template)
                    data = os.stat(os.path.join(UPLOAD_FOLDER_CONFIG, file))
                    temp['name'] = file
                    temp['size'] = str(data.st_size) + 'Byte'
                    temp['last_modify'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data.st_mtime))
                    temp['testcase_name'] = file.split('.json')[0]

                    file_data.append(temp)
            return {'type': 'show_class_config', 'msg': file_data, 'code': 'success'}

        @app.route('/show_task_status', methods=['GET'])
        def show_task_status():
            data_template = {
                'name': '',
                'status': '',
                'starttime': '',
                'stoptime': '',
                'interval': '',
                'runtimes': '',
                'rantimes': '',
                'description': ''
            }
            msg = []
            running_task = list(self.user.running_task.keys())
            abnormal_task_ = list(self.user.abnormal_task_.keys())
            stop_by_adm = list(self.thread_control.stop_by_adm.keys())
            # 处理用户停止,用户停止需要等待原测试用例退出，避免资源残留,状态为停止中，用户停止
            stopping = []
            for name in stop_by_adm:
                if self.user.running_task.get(name, False):
                    stopping.append(name)
                    running_task.remove(name)
            for name in stopping:
                stop_by_adm.remove(name)
            msg.extend(_show_task_status(self, stopping, '停止中', data_template))
            msg.extend(_show_task_status(self, stop_by_adm, '用户停止', data_template))
            msg.extend(_show_task_status(self, running_task, '运行中', data_template))
            msg.extend(_show_task_status(self, abnormal_task_, '异常', data_template))
            return {'type': 'show_task_status', 'msg': msg, 'code': 'success'}

        @app.route('/get_log/<string:filename>', methods=['GET'])
        def get_log(filename):
            filepath = os.path.join(LOG_FOLDER, filename)
            if not os.path.exists(filepath):
                return {'type': 'get_log', 'code': 'failed', 'msg': '文件{}不存在'.format(filepath)}
            return send_from_directory(LOG_FOLDER, filename)

        @app.route('/get_source_modules', methods=['GET'])
        def get_source_modules():
            # 将source下的文件返回
            files = os.listdir(SOURCE_FOLDER)
            # 获取class下的方法,读取def xxx(self,x)

        @app.route('/gen_api', methods=['POST'])
        def get_api():
            data = json.loads(request.data)
            dict_keys = ['data', 'args_with_data', 'to_edit', 'res']
            for key in dict_keys:
                if data[key] and type(data[key]) != dict:
                    try:
                        data[key] = json.loads(data[key])
                    except Exception:
                        return {'code': 'failed', 'msg': '{}参数需要为字典'.format(API_KEYS[key])}
            api_generater = Api_Generater(**data)
            ret = api_generater.generate_api()
            del api_generater
            return {'code': 'success', 'context': ret}

    def start(self):
        print(self.app.url_map)
        self.greenlet = gevent.spawn(self.start_server)
        self.greenlet.join()

    def start_server(self):
        self.server = pywsgi.WSGIServer((self.host, self.port), self.app, log=None)
        self.server.serve_forever()


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _show_task_status(self, tasks: list, flag, template):
    res = []
    if tasks:
        for taskname in tasks:
            t = deepcopy(template)
            task_class = self.user.get_task_by_name(taskname)
            if task_class:
                t['name'] = taskname
                t['status'] = flag
                t['interval'] = task_class.interval
                t['runtimes'] = task_class.run_times
                t['rantimes'] = task_class.ran_times
                t['description'] = None
                t['starttime'] = task_class._starttime
                t['stoptime'] = task_class._stoptime
                res.append(t)
    return res
