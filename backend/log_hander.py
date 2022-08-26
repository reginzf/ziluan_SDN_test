# -*- coding: UTF-8 -*-
import logging, os
from logging.handlers import RotatingFileHandler

class LogLevelException(Exception):
    def __init__(self, level):
        self.level = level

    def __str__(self):
        return "LogLevelException must in ['CRITICAL','FATAL','ERROR','WARNING','WARN','INFO','DEBUG','NOTSET'] not {}".format(
            self.level)
LOG_LEVEL = {'CRITICAL': 50,
             'FATAL': 50,
             'ERROR': 40,
             'WARNING': 30,
             'WARN': 30,
             'INFO': 20,
             'DEBUG': 10,
             'NOTSET': 0}


class MyLog(object):
    formatter = logging.Formatter(
        '[%(asctime)s] %(filename)s->%(funcName)s line:%(lineno)d [%(levelname)s]%(message)s')
    """
    单个日志最多10M，3个backuo
    """

    def __init__(self, classname, level='INFO'):
        # 按classname创建一个logger
        self.logger = logging.getLogger(classname)
        log_level = LOG_LEVEL.get(level)
        if not log_level and log_level != 0:
            raise LogLevelException(level)

        self.logger.setLevel(log_level)
        # 创建一个handler，用于写入日志文件
        self.log_name = os.path.join('logs', classname + '.log')
        if not os.path.exists('logs'):
            os.mkdir('logs')
        self.logger.addHandler(self.set_fh())
        self.logger.addHandler(self.set_ch())

    def getlog(self):
        return self.logger

    def set_fh(self):
        fh = RotatingFileHandler(self.log_name, 'w', maxBytes=10485760, backupCount=2, encoding='utf-8')
        fh.setLevel(logging.INFO)
        fh.setFormatter(self.formatter)
        self.fh = fh
        return fh

    def set_ch(self):
        ch = logging.StreamHandler()
        ch.setLevel(logging.WARNING)
        ch.setFormatter(self.formatter)
        self.ch = ch
        return ch

    def clear_log(self):
        self.fh.close()
        self.logger.removeHandler(self.fh)

    def reset_log(self):
        self.clear_log()
        self.logger.addHandler(self.set_fh())


log = MyLog('main')
logger = log.getlog()
