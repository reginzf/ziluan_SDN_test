# -*- coding: UTF-8 -*-
import os
import re
import time
from re import IGNORECASE
import xlrd
from xlrd import xldate_as_datetime
from xlrd.sheet import Sheet
import xlwt
from xlwt import Worksheet
from pyecharts.options import AxisOpts, LabelOpts
from pyecharts.charts import *
from collections import defaultdict

SORTED = {"问题单号": "id", "简述": "description", "当前处理人": "cur", "问题修改人": "problem_modifier", "提交日期": "submit_date",
          "提交人": "author", "严重程度": "level", "是否关闭": "closed", "特性": "feature", "子特性": "sub_feature",
          "子系统": "sub_system", "模块": "module", "标签": "tag"}
PATTERS = {
    "vpc": re.compile(r'(虚拟专有云)|(vpc[^pP])', flags=IGNORECASE),
    "sg": re.compile(r'(安全组)|(sg)', flags=IGNORECASE),
    "eip": re.compile(r'(弹性公网IP)|(EIP)', flags=IGNORECASE),
    "slb": re.compile(r'([^h]slb)|([^(高性能)(全局)]负载均衡)', flags=IGNORECASE),
    "nat": re.compile(r'(nat)', flags=IGNORECASE),
    "hvip": re.compile(r'(vip)|(高可用虚拟)', flags=IGNORECASE),
    "sharebandwidth": re.compile(r'(共享)', flags=IGNORECASE),
    "hslb": re.compile(r'(hslb)|(高性能负载均衡)', flags=IGNORECASE),
    "ipescVpn": re.compile(r'(ipsec)', flags=IGNORECASE),
    "vpcp": re.compile(r'(vpcp)|(对等连接)', flags=IGNORECASE),
    "sslVpn": re.compile(r'(ssl)', flags=IGNORECASE),
    "bfw": re.compile(r'(bfw)|(边界防火墙)', flags=IGNORECASE),
    "cfw": re.compile(r'(cfw)|(云防火墙)', flags=IGNORECASE),
    "ccn": re.compile(r'(ccn)|(云联网)', flags=IGNORECASE),
    "gdns": re.compile(r'(gdns)|(全局负载均衡)', flags=IGNORECASE),
    "csl": re.compile(r'(云专线)', flags=IGNORECASE),
    "dns": re.compile(r'([^g]dns)|(云解析)', flags=IGNORECASE),
    "ovsOvnAgent": re.compile(r'(ovs)|(ovn)|(agent)', flags=IGNORECASE),
    "danos": re.compile(r'(danos)', flags=IGNORECASE)
}


class Parse_xls:
    """
    处理xls文件，返回表头key_loc和所有bug的列表
    """

    def __init__(self, xls_filepath):
        try:
            self.book = xlrd.open_workbook_xls(xls_filepath)
        except Exception as e:
            self.book = xlrd.open_workbook(xls_filepath)
        self.sheet: Sheet = self.book.sheet_by_index(0)
        self.key_loc = dict()
        self.__bugs = list()
        self.get_key_loc()
        self.get_bugs()

    def get_key_loc(self):
        for i in range(self.sheet.ncols):
            val = self.sheet.cell(0, i).value
            self.key_loc[val] = i

    def get_bugs(self):
        for i in range(1, self.sheet.nrows):
            bug = list()
            for j in range(self.sheet.ncols):
                cell = self.sheet.cell(i, j)
                if cell.ctype == 2 and cell.value > 200000:
                    value = str(int(cell.value))
                elif cell.ctype == 3:
                    value = xldate_as_datetime(cell.value, 0).strftime("%Y-%m-%d")
                else:
                    value = cell.value
                bug.append(value)
            # 处理问题单号
            bug[0] = str(int(bug[0]))
            self.__bugs.append(bug)

    @property
    def bugs(self) -> list:
        return self.__bugs

    @property
    def key_location(self):
        return self.key_loc


class Bug:
    """按表头处理bug，一个bug创建1个实例，为bug分类"""

    def __init__(self, __bug: list, key_loc: dict):
        self.bug = __bug
        self.key_loc = key_loc
        self.id = None
        self.description = None
        self.cur = None
        self.problem_modifier = None
        self.submit_date = None
        self.author = None
        self.level = None
        self.closed = None
        self.feature = None
        self.sub_feature = None
        self.sub_system = None
        self.tag = None
        self.module = list()

        for k, v in self.key_loc.items():
            try:
                key = SORTED[k]
            except KeyError:
                continue
            self.__setattr__(key, __bug[v])

        self.parse_module()

    def parse_module(self):
        if self.module and type(self.module) != list:
            pass
        else:
            for k, v in PATTERS.items():
                self.res = re.search(v, self.description)
                if self.res:
                    self.module.append(k)
            if not self.module:
                self.module.append('其他')

    def context(self):
        # 输出bug正文，list
        res = [self.__getattribute__(name) for name in SORTED.values()]
        res.extend(self.module)
        return res


class Result:
    """
    统计bug信息
    """
    _fatal = []
    _serious = []
    _normal = []
    _notice = []
    module_data = defaultdict(lambda: list())
    level_data = {"致命": 0, "严重": 0, "一般": 0, "提示": 0}
    author_data = defaultdict(lambda: list())
    author_level_data = defaultdict(lambda: defaultdict(lambda: list()))
    date_data = defaultdict(lambda: list())
    tag_data = defaultdict(lambda: list())

    def parase_bug(self, bug: Bug):
        if bug.level == "严重":
            self.serious.append(bug)
        elif bug.level == "一般":
            self.normal.append(bug)
        elif bug.level == "提示":
            self.notice.append(bug)
        elif bug.level == "致命":
            self.fatal.append(bug)
        # 处理level
        self.level_data[bug.level] += 1
        # 处理module
        self.__module_data(bug)
        # 处理提单人
        self.__author_data(bug)
        # 处理提单时间
        self.__date_data(bug)
        # 处理tag
        self.__tag_data(bug)

    @property
    def all_bugs(self) -> list:
        return self.fatal + self.serious + self.normal + self.notice

    @property
    def fatal(self):
        return self._fatal

    @property
    def serious(self):
        return self._serious

    @property
    def normal(self):
        return self._normal

    @property
    def notice(self):
        return self._notice

    def bug_level_data(self) -> dict:
        return {"致命": len(self.fatal), "严重": len(self.serious), "普通": len(self.normal), "提示": len(self.notice)}

    def __module_data(self, bug: Bug):
        if type(bug.module) == list and len(bug.module) > 1:
            # 去重
            score = dict()  # 分数最高的为模块名
            temp = bug.feature + bug.sub_feature + bug.sub_system
            for module in bug.module:
                res = re.findall(PATTERS[module], temp)
                if res:
                    score[module] = len(res)
            if score:  # 分数存在
                _ = sorted(score.items(), key=lambda kv: (kv[0], kv[1]))
                if len(_) > 1:  # 剩余分数长度>1，选最大的
                    if _[0][1] > _[1][1]:
                        bug.module = [_[0][0]]
                    else:
                        print("无法区分模块:", bug.context())
                elif len(_) == 1:
                    bug.module = [_[0][0]]
            else:
                print("无法区分模块:", bug.context())

            for m in bug.module:
                self.module_data[m].append(bug)
        elif type(bug.module) == list:
            self.module_data[bug.module[0]].append(bug)
        else:
            self.module_data[bug.module].append(bug)

    def __author_data(self, bug: Bug):
        self.author_data[bug.author].append(bug)
        self.author_level_data[bug.author][bug.level].append(bug)

    def __date_data(self, bug: Bug):
        self.date_data[bug.submit_date].append(bug)

    def __tag_data(self, bug: Bug):
        if bug.tag:
            for ele in str(bug.tag).split(' '):
                if ele:
                    self.tag_data[ele].append(bug)


class Charts:
    """
    各种视图
    """

    def __init__(self, result: Result):
        self.result = result

    def level_chart(self):
        data = self.result.level_data
        pie = Pie().add('问题单level统计', [[k, v] for k, v in data.items()])
        pie.render('level_chart.html')

    def author_chart(self):
        data = self.result.author_data
        data_level = self.result.author_level_data
        authors = list(data.keys())
        authors.sort()
        bar = Bar().add_xaxis([a.split(' ')[0] for a in authors])

        for level in ['致命', '严重', '一般', '提示']:
            y_data = []
            for author in data.keys():
                y_data.append(len(data_level[author][level]))
                bar.add_yaxis(level, y_data, stack='x')
        bar.set_global_opts(xaxis_opts=AxisOpts(axislabel_opts=LabelOpts(rotate=30)))
        bar.render("author_chart.html")

    def submit_date_chart(self):
        data = self.result.date_data
        x_data = sorted(data.keys())
        y_data = [len(data[k]) for k in x_data]
        line = Line().add_xaxis(x_data).add_yaxis('', y_data)
        line.set_global_opts(xaxis_opts=AxisOpts(axislabel_opts=LabelOpts(rotate=30)))
        line.render('submit_date_chart.html')

    def tag_chart(self):
        data = self.result.tag_data
        sorted_data = sorted(data.items(), key=lambda kv: (len(kv[1]), len(kv[0])))
        x_data = [ele[0] for ele in sorted_data]
        y_data = [len(ele[1]) for ele in sorted_data]
        # print('tag_data', x_data, y_data)
        bar = Bar().add_xaxis(x_data).add_yaxis('', y_data)
        bar.set_global_opts(xaxis_opts=AxisOpts(axislabel_opts=LabelOpts(rotate=90)))
        bar.render('tag_chart.html')

    def module_chart(self):
        sorted_data = sorted(self.result.module_data.items(), key=lambda kv: (len(kv[1]), len(kv[0])))

        x_data = [ele[0] for ele in sorted_data]
        y_data = [len(ele[1]) for ele in sorted_data]

        bar = Bar().add_xaxis(x_data).add_yaxis('', y_data)
        bar.set_global_opts(xaxis_opts=AxisOpts(axislabel_opts=LabelOpts(rotate=90)))
        bar.render('module_chart.html')


class Write_xls:
    def __init__(self, xls_filepath, result: Result):
        self.book = xlwt.Workbook(encoding='utf-8')
        self.sheet: Worksheet = self.book.add_sheet('问题单')
        self.bugs = [_.context() for _ in result.all_bugs]
        self.loc_row = 0
        self.loc_col = 0
        self.write_head(list(SORTED.keys()))
        self.write_xls(self.bugs)
        self.book.save(xls_filepath)

    def write_xls(self, bugs: list):
        for i in range(len(bugs)):
            for j in range(len(bugs[i])):
                try:
                    self.sheet.write(i + 1, j, bugs[i][j])
                except IndexError:
                    pass

    def write_head(self, key_loc: list):
        n = len(key_loc)
        for i in range(n):
            self.sheet.write(0, i, key_loc[i])
        self.sheet.write(0, n, '模块')
        self.sheet.write(0, n + 1, '标签')


class ModifiedResult:
    def __init__(self, result_xls_path):
        self.p = Parse_xls(result_xls_path)
        self._result = Result()
        for b in self.p.bugs:
            self._result.parase_bug(Bug(b, self.p.key_loc))

        self.chart = Charts(self._result)
        self.draw_charts()

    @property
    def result(self):
        return self._result.all_bugs

    def draw_charts(self):
        self.chart.level_chart()
        self.chart.author_chart()
        self.chart.submit_date_chart()
        self.chart.tag_chart()
        self.chart.module_chart()


if __name__ == '__main__':
    pa = Parse_xls('aaa.xls')
    result = Result()
    for bug in pa.bugs:
        b = Bug(bug, pa.key_loc)
        result.parase_bug(b)
    xls_w = Write_xls('result.xls', result)
    os.system('result.xls')
    input('请处理无法区分的模块，编辑问题单标签，任意键继续\n')

    ModifiedResult('result.xls')
