import re, os

import gevent

SOURCE_FOLDER = '../source'
abs_source = os.path.abspath(os.path.join(os.path.abspath('.'), SOURCE_FOLDER))
files = os.listdir(SOURCE_FOLDER)
contexts = []


def context_get_func(context):
    patter = re.compile(r'(\s+def \w+\(self.*?)\Wdef \w+\(self', re.DOTALL)
    res = re.findall(patter, context)
    return res


for f in files[4:5]:
    path = os.path.join(abs_source, f)

    f = open(path, 'r', encoding='utf-8')
    context = f.read()
    context_get_func(context)


class Class_struct:
    def __init__(self, context):
        self.context = context
        self.res = {}

    def func_name(self) -> list:
        pass

    def func_context(self, func_name):
        pass

    def struct(self):
        for func_name in self.func_name():
            self.res[func_name] = self.func_context(func_name)
        return self.res
from gevent.server import StreamServer
from gevent import socket
g = gevent.spawn()
