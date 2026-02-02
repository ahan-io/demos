import json
import sys
import urllib
from copy import deepcopy
from typing import Dict, List
from urllib.parse import urlencode

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt  # type: ignore

import pymysql
import seaborn as sns  # type: ignore
import numpy as np  # type: ignore
import pandas as pd  # type: ignore
import platform

import traceback


class NodeInfo(object):
    def __init__(self, node_ip: str = ""):
        self.node_ip = node_ip
        self.cpu_max_of_a_week = 0
        self.cpu_max_of_a_day = 0
        self.cpu_mean_of_a_week = 0
        self.cpu_mean_of_a_day = 0

        self.mem_max_of_a_week = 0  # 内存占用比率（总内存 - free）/ 总内存
        self.mem_max_of_a_day = 0
        self.mem_mean_of_a_week = 0
        self.mem_mean_of_a_day = 0

        self.cluster: str = ""
        self.node_pool: str = ""

        self.mem_total = 0

    def __str__(self):
        return "%r" % self.__dict__


class ClusterInfo(object):
    def __init__(self, name: str):
        self.name = name
        self.cpu_max_usage_week = 0
        self.mem_max_usage_week = 0


class NodePoolInfo(object):
    def __init__(self, name: str):
        self.name = name
        self.cpu_max_usage_week = 0
        self.mem_max_usage_week = 0
        self.cpu_mean_usage_week = 0
        self.mem_mean_usage_week = 0
        self.total_cpu = 0
        self.total_cpu_avail = 0
        self.total_mem = 0
        self.total_mem_avail = 0
        self.cpu_sell_rate = 0
        self.mem_sell_rate = 0
        self.node_list = []

    def __str__(self):
        return "Pool name:%s, total node:%d, totalcpu:%d, totalmem:%d, cpu max:%d%%, cpu mean:%f%%, cpu_sell_rate:%f%% mem max:%f%%, mem mean:%f%%, mem sell rate:%f%%" % (self.name,
        len(self.node_list), self.total_cpu, self.total_mem, self.cpu_max_usage_week, self.cpu_mean_usage_week, self.cpu_sell_rate, self.mem_max_usage_week, self.mem_mean_usage_week, self.mem_sell_rate)


def query_influxb_by_http(host: str, port: int, db: str, query: str) -> Dict:
    query_params = {"db": db, "q": query}
    request_url = "http://%s:%d/query?" % (host, port) + urlencode(query_params)
    print(request_url)

    req = urllib.request.Request(request_url)  # type: ignore
    res = urllib.request.urlopen(req)  # type: ignore

    resp = res.read().decode("utf-8")
    resp = json.loads(resp)
    print(type(resp))
    return resp


# 热力图
def draw_heatmap():
    a = np.random.uniform(0, 1, size=(10, 10))
    print(type(a))
    sns.heatmap(a, cmap="Reds")
    plt.show()
    plt.savefig("report/heatmap.svg", dpi=250)


def ShowGRAHeatMap(data: Dict[str, List], title: str = "", savefileto: str = ""):
    data2 = deepcopy(data)
    # 把 data2 的 value 转变为长度相等的数组
    max_len = 0
    for value in data2.values():
        max_len = max(max_len, len(value))
    mask = data
    for key, value in data2.items():
        ori_len = len(value)
        if ori_len < max_len:
            # 对于没达到 max_len 的数组，都填充0，补齐长度
            value.extend((max_len - ori_len) * [0])
            mask[key] = ori_len * [False]  # 对于原始的值，mask = False，都展示
            mask[key].extend((max_len - ori_len) * [True])  # 对于补齐的值，mask=True，都不展示
        else:
            mask[key] = ori_len * [False]  # 对于原始的值，mask = False，都展示

    df = pd.DataFrame(data2)
    mask = pd.DataFrame(mask)
    f, ax = plt.subplots(figsize=(15, 15))
    ax.set_title(title)

    with sns.axes_style("white"):
        sns.heatmap(
            df,
            cmap="YlGnBu",
            annot=True,
            mask=mask,
        )

    if savefileto:
        plt.savefig(savefileto, dpi=250)


def demo2():
    # 构造一个 key 为“集群”，值为机器的 CPU 使用率的DataFrame，然后看看画出来什么样
    data = {
        "storage-cp.org": [0.2, 0.2, 0.3, 0.4],
        "storage-cp2.org": [0.9, 0.8, 0.19, 0.19, 0.89],
        "storage-cp3.org": [0.9, 0.8, 0.19, 0.19],
        "storage-cp4.org": [0.9, 0.8, 0.2],
        "storage-cp5.org": [0.1],
    }
    ShowGRAHeatMap(
        data, title="Cluster Node CPU Heatmap", savefileto="report/heatmap4.svg"
    )


def fetch_node_cpu_usage_mean(node_map: Dict[str, NodeInfo], host: str, port: int, db: str, region: str, time_s):
    """获取某个 region 下的节点的 CPU 平均利用率"""
    node_statics_list = fetch_node_statics(host=host, port=port, db=db, region=region, time_s=time_s,
                                           measurement="rule_cpu_usage_total", statics_method="mean")
    for x in node_statics_list:
        n = node_map.get(x.node_ip)
        if n:
            n.cpu_mean_of_a_week = x.value


class NodeStatics(object):
    def __init__(self, node_ip: str, value: int):
        self.node_ip = node_ip
        self.value = value


def fetch_node_statics(host: str, port: int, db: str, region: str, measurement: str, statics_method: str, time_s) -> \
List[NodeStatics]:
    """获取某个 region 下的节点的 CPU 最大利用率"""
    query = (
            'SELECT %s("value") FROM "%s" WHERE ("Region" =~ /^%s$/) AND time >= now() - %ds GROUP BY "Region", "k8s_node", "k8s_nodeip" fill(null)'
            % (statics_method, measurement, region, time_s)
    )

    print("query:=====")
    print(query)
    resp = query_influxb_by_http(host, port, db, query)
    # 解析 influxdb 的返回结果
    series = resp['results'][0]['series']
    node_statics_list = []
    for x in series:
        node_ip = x['tags']['k8s_nodeip']
        value = None
        if len(x['values']) == 1 and len(x['values'][0]) == 2:
            value = x['values'][0][1]
        else:
            print(node_ip, " values:", x)
            continue
        n = NodeStatics(node_ip, value)
        node_statics_list.append(n)

    return node_statics_list


def fetch_node_cpu_usage_max(node_map: Dict[str, NodeInfo], host: str, port: int, db: str, region: str, time_s):
    """获取某个 region 下的节点的 CPU 最大利用率"""

    node_statics_list = fetch_node_statics(host=host, port=port, db=db, region=region, time_s=time_s,
                                           measurement="rule_cpu_usage_total", statics_method="max")
    for x in node_statics_list:
        n = node_map.get(x.node_ip)
        if n:
            n.cpu_max_of_a_week = x.value


def fetch_node_mem_statics(node_map: Dict[str, NodeInfo], host: str, port: int, db: str, region: str, time_s):
    """获取某个 region 下的节点的 内存 最大利用率"""

    node_statics_list = fetch_node_statics(host=host, port=port, db=db, region=region, time_s=time_s,
                                           measurement="mem_total", statics_method="max")
    for x in node_statics_list:
        n = node_map.get(x.node_ip)
        if n:
            n.mem_total = x.value

    node_statics_list = fetch_node_statics(host=host, port=port, db=db, region=region, time_s=time_s,
                                           measurement="mem_available_percent", statics_method="min")
    for x in node_statics_list:
        n = node_map.get(x.node_ip)
        if n:
            n.mem_max_of_a_week = 100.0 - x.value

    node_statics_list = fetch_node_statics(host=host, port=port, db=db, region=region, time_s=time_s,
                                           measurement="mem_available_percent", statics_method="mean")
    for x in node_statics_list:
        n = node_map.get(x.node_ip)
        if n:
            n.mem_mean_of_a_week = 100.0 - x.value


def draw_barh(x: List[str], y: List, title: str, output_file: str, order: bool = True, text_map: Dict[str, str] = None,
              horizontal_line=None, vertical_line=None):
    # 根据列表的长度，设置图的高度
    figsize_height = len(x) * 0.25
    plt.figure(figsize=(15, figsize_height))
    # 根据 y 值排序
    if order:
        x, y = zip(*sorted(zip(x, y), key=lambda x: x[1]))
    # 把 y 轴的 label 旋转一下，避免文字太长放不下
    plt.yticks(rotation=30)
    plt.barh(range(len(x)), y, tick_label=x)
    # 打text
    if text_map:
        for a, c in zip(range(len(x)), y):
            plt.text(c + 1, a, text_map[a], color="gray", ha="left", va="center", fontsize=10)
    else:
        for a, c in zip(range(len(x)), y):
            plt.text(c + 1, a, "%.0f" % c, color="gray", ha="left", va="center", fontsize=10)

    if vertical_line:
        plt.axvline(x=vertical_line, c="c", linestyle='--', label=str(vertical_line))
    plt.title(title)
    plt.savefig(output_file)


def draw_barh_multi_group(labels: List[str], x: List[List], x_labels: List[str], title: str, output_file: str,
                          order: bool = True, text_map: Dict[str, str] = None, horizontal_line=None,
                          vertical_line=None):
    # 每个柱子的宽度
    width = 0.25
    # 组内的柱子的个数
    num_in_group = len(x)

    # 根据列表的长度，设置图的高度
    figsize_height = len(labels) * width * len(x)
    plt.figure(figsize=(15, figsize_height))
    # 根据 y 值排序
    # if order:
    #     x, y = zip(*sorted(zip(x, y), key=lambda x:x[1]))
    # 把 y 轴的 label 旋转一下，避免文字太长放不下

    # 每组的 y 轴的间隔
    y_witdh = (num_in_group + 1) * width

    y = np.arange(0, len(labels) * y_witdh, y_witdh)

    plt.yticks(y, rotation=30, labels=labels)
    i = 0
    for k in range(len(x)):
        x_ = x[k]
        x_label = x_labels[k]
        plt.barh(y + i * width, x_, width, label=x_label)
        plt.legend()
        for a, c in zip(y + i * width, x_):
            plt.text(c + 1, a, "%.0f" % c, color="gray", ha="left", va="center", fontsize=10)
        i = i + 1

    #
    # plt.barh(y - width / 2, x[0], width)
    # plt.barh(y + width / 2, x[1], width)

    # 打text
    # if text_map:
    #     for a, c in zip(range(len(labels)), x):
    #         plt.text(c + 1, a, text_map[a], color="gray", ha="left", va="center", fontsize=10)
    # else:
    #     for a, c in zip(range(len(labels)), x):
    #         plt.text(c + 1, a, "%.0f" % c, color="gray", ha="left", va="center", fontsize=10)

    # if vertical_line:
    #     plt.axvline(x=vertical_line, c="c", linestyle='--', label=str(vertical_line))
    plt.title(title)
    plt.savefig(output_file)


def draw_bar2(x, y, title, output_file):
    """
    画条形图，y 轴上，除了打上数字之外，把比例也打上
    :param x:
    :param y:
    :param title:
    :param output_file:
    :return:
    """
    plt.rcParams["font.sans-serif"] = ["Songti SC", "WenQuanYi Zen Hei"]
    params = {
        'figure.figsize': '10, 4'
    }
    plt.rcParams.update(params)
    if platform.system().lower() == "windows":
        plt.rcParams["font.sans-serif"] = ["SimHei"]
    if platform.system().lower() == "linux":
        plt.rcParams["font.sans-serif"] = ["SimHei"]
    plt.rcParams["axes.unicode_minus"] = False
    plt.cla()
    plt.style.use('ggplot')
    plt.bar(x, y)
    total = sum(y)
    for a, c in zip(x, y):
        text = "%.0f(%.0f %%)" % (c, c * 100.0 / total)
        plt.text(a, c + 0.05, text, ha="center", va="bottom", fontsize=7)
    plt.title(title)
    plt.savefig(output_file, dpi=100)


def draw_cpu_mean_week_bar_char(node_list: List[NodeInfo]):
    """画节点一周以来的 CPU 平均利用率条形图
    节点太多了，全部画出来，画不下，按阶梯来绘图
    """
    total = len(node_list)
    node_cpu_mean_list = [x.cpu_mean_of_a_week for x in node_list if x.cpu_mean_of_a_week != 0]
    count_less_than10 = 0
    count_less_than20 = 0
    count_less_than30 = 0
    count_less_than40 = 0
    count_less_than50 = 0
    count_large_than50 = 0
    for y in node_cpu_mean_list:
        if y < 10:
            count_less_than10 += 1
        elif y < 20:
            count_less_than20 += 1
        elif y < 30:
            count_less_than30 += 1
        elif y < 40:
            count_less_than40 += 1
        elif y < 50:
            count_less_than50 += 1
        else:
            count_large_than50 += 1
    x = ["< 10",
         "10~20",
         "20~30",
         "30~40",
         "40~50",
         ">50"
         ]
    y = [
        count_less_than10,
        count_less_than20,
        count_less_than30,
        count_less_than40,
        count_less_than50,
        count_large_than50
    ]
    draw_bar2(x, y, "cpu mean distribution of a week", "cpu_mean_week.svg")


def draw_mem_max_week_bar_char(node_list: List[NodeInfo]):
    """画节点一周以来的 内存 最大利用率条形图
    节点太多了，全部画出来，画不下，按阶梯来绘图
    """
    total = len(node_list)
    node_mem_max_list = [x.mem_max_of_a_week for x in node_list if x.mem_max_of_a_week != 0]
    count_less_than10 = 0
    count_less_than20 = 0
    count_less_than30 = 0
    count_less_than40 = 0
    count_less_than50 = 0
    count_large_than50 = 0
    for y in node_mem_max_list:
        if y < 10:
            count_less_than10 += 1
        elif y < 20:
            count_less_than20 += 1
        elif y < 30:
            count_less_than30 += 1
        elif y < 40:
            count_less_than40 += 1
        elif y < 50:
            count_less_than50 += 1
        else:
            count_large_than50 += 1
    x = ["< 10",
         "10~20",
         "20~30",
         "30~40",
         "40~50",
         ">50"
         ]
    y = [
        count_less_than10,
        count_less_than20,
        count_less_than30,
        count_less_than40,
        count_less_than50,
        count_large_than50
    ]
    draw_bar2(x, y, "mem max distribution of a week", "mem_max_week.svg")


def draw_cluster_cpu_max_week_bar_char(cluster_list: List[ClusterInfo]):
    """画节点一周以来的 内存 最大利用率条形图
    节点太多了，全部画出来，画不下，按阶梯来绘图
    """

    x = [c.name for c in cluster_list]
    y = [c.cpu_max_usage_week for c in cluster_list]
    draw_barh(x, y, "cluster_cpu_max_week", "cluster_cpu_max_week.svg")


def draw_cluster_mem_max_week_bar_char(cluster_list: List[ClusterInfo]):
    x = [c.name for c in cluster_list]
    y = [c.mem_max_usage_week for c in cluster_list]
    draw_barh(x, y, "cluster_mem_max_week", "cluster_mem_max_week.svg")


def draw_node_pool_bar_char(node_pool_list: List[NodePoolInfo]):
    x = [np.name for np in node_pool_list]
    y = [np.cpu_max_usage_week for np in node_pool_list]
    print(x)
    print(y)
    # 构建节点池的展示信息
    np_text_map = {}
    for np in node_pool_list:
        np_text_map[np.name] = str(np)

    draw_barh(x, y, "node_pool_cpu_max_week", "node_pool_cpu_max_week.svg")

    y = [np.mem_max_usage_week for np in node_pool_list]
    draw_barh(x, y, "node_pool_mem_max_week", "node_pool_mem_max_week.svg")

    y = [np.mem_mean_usage_week for np in node_pool_list]
    draw_barh(x, y, "node_pool_mem_mean_week", "node_pool_mem_mean_week.svg")

    y = [np.cpu_mean_usage_week for np in node_pool_list]
    draw_barh(x, y, "node_pool_cpu_mean_week", "node_pool_cpu_mean_week.svg")


def get_node_list_from_db(mysql_host: str, mysql_user: str, mysql_password: str) -> List[NodeInfo]:
    """从数据库里获取节点的列表，并填充好节点的静态信息，包括 节点池、IP、所属集群等等

    :param mysql_host:
    :param mysql_user:
    :param mysql_password:
    :return:
    """

    db = pymysql.connect(host=mysql_host,
                         user=mysql_user,
                         password=mysql_password,
                         database='inframgmt')

    # 使用 cursor() 方法创建一个游标对象 cursor
    cursor = db.cursor()

    sql = "select id, ip, node_type, kube_cluster, pool_name, mem, model from node_infos"
    node_list = []
    try:
        # 使用 execute()  方法执行 SQL 查询
        cursor.execute(sql)
        # 获取所有记录列表
        results = cursor.fetchall()
        i = 1
        for row in results:
            id, ip, node_type, kube_cluster, pool_name, mem, model = row[0], row[1], row[2], row[3], row[4], row[5], \
                                                                     row[6]
            node = NodeInfo(node_ip=ip)
            node.cluster = kube_cluster
            node.node_pool = pool_name
            node_list.append(node)
            # print(id, ip, node_type, kube_cluster, pool_name, mem, model)
    except:
        traceback.print_exc()
    # 关闭数据库连接
    db.close()
    return node_list


def fetch_node_pool_cpu_mem_sell(host: str, port: int, node_pool_map: Dict[str, NodePoolInfo]):
    query_params = {"Action": "ListNodePools", "Version": "2018-01-01"}
    request_url = "http://%s:%d/action/?" % (host, port) + urlencode(query_params)
    print(request_url)
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        'Host': '2020.11.10',
        'X-Date': '10.11x',
        'Authorization': 'dfsdfsfsfsdfds',
        'Async': 'false',
        'X-Top-User-Id': '0',
        'X-Top-Account-Id': '0',
        'X-Top-Service': 'InfraMgmt',
        'X-Top-Region': 'cn-north-1',
    }

    req = urllib.request.Request(request_url, headers=headers,
                                 method="POST")  # type: ignore
    res = urllib.request.urlopen(req)  # type: ignore
    resp = res.read().decode("utf-8")
    resp = json.loads(resp)

    node_pool_list = resp["Result"]["Pool"]
    for np in node_pool_list:
        node_pool = node_pool_map.get(np["Name"])
        if not node_pool:
            continue
        node_pool.total_cpu = np["CpuCapacity"]
        node_pool.total_cpu_avail = np["CpuAvailable"]
        node_pool.cpu_sell_rate = (np['CpuCapacity'] - np["CpuAvailable"]) * 100.0 / np["CpuCapacity"]

        node_pool.total_mem = np["MemCapacity"]
        node_pool.total_mem_avail = np["MemAvailable"]
        node_pool.mem_sell_rate = (np['MemCapacity'] - np["MemAvailable"]) * 100.0 / np["MemCapacity"]


def draw_node_pool_statics(node_pool_list: List[NodePoolInfo]):
    lables = [np.name for np in node_pool_list]
    y_cpu = [np.cpu_sell_rate for np in node_pool_list]
    y_cpu_mean = [np.cpu_mean_usage_week for np in node_pool_list]
    y_cpu_max = [np.cpu_max_usage_week for np in node_pool_list]
    y_mem = [np.mem_sell_rate for np in node_pool_list]
    y_mem_mean = [np.mem_mean_usage_week for np in node_pool_list]
    y_mem_max = [np.mem_max_usage_week for np in node_pool_list]

    total_cpu_avail = sum([np.total_cpu_avail for np in node_pool_list])
    total_cpu_capacity = sum([np.total_cpu for np in node_pool_list])
    total_mem_avail = sum([np.total_mem_avail for np in node_pool_list])
    total_mem_capacity = sum([np.total_mem for np in node_pool_list])

    total_cpu_sell_rate = (total_cpu_capacity - total_cpu_avail) * 100 / total_cpu_capacity
    total_mem_sell_rate = (total_mem_capacity - total_mem_avail) * 100 / total_mem_capacity

    # 构建节点池的展示信息
    # np_text_map = {}
    # for np in node_pool_list:
    #     np_text_map[np.name] = str(np)

    draw_barh(lables, y_cpu, "node_pool_cpu_sell_rate", "node_pool_cpu_sell_rate.svg",
              vertical_line=total_cpu_sell_rate)
    draw_barh(lables, y_mem, "node_pool_mem_sell_rate", "node_pool_mem_sell_rate.svg",
              vertical_line=total_mem_sell_rate)

    draw_barh_multi_group(lables, [y_cpu, y_cpu_mean, y_cpu_max, y_mem, y_mem_mean, y_mem_max],
                          ["cpu_sell_rate", "cpu_mean", "cpu_max", "mem_sell_rate", "mem_mean", "mem_max"],
                          "node_pool_statics", "node_pool_statics.svg")


def get_node_sell_info(host, port):
    """获取节点资源售卖的情况"""

    query_params = {"Action": "GetNodePool", "Version": "2018-01-01"}
    request_url = "http://%s:%d/action/?" % (host, port) + urlencode(query_params)
    print(request_url)
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        'Host': '2020.11.10',
        'X-Date': '10.11x',
        'Authorization': 'dfsdfsfsfsdfds',
        'Async': 'false',
        'X-Top-User-Id': '0',
        'X-Top-Account-Id': '0',
        'X-Top-Service': 'InfraMgmt',
        'X-Top-Region': 'cn-north-1',
    }

    data = {"PoolName": "control-panel-default"}
    req = urllib.request.Request(request_url, data=json.dumps(data).encode("utf-8"), headers=headers,
                                 method="POST")  # type: ignore
    res = urllib.request.urlopen(req)  # type: ignore

    resp = res.read().decode("utf-8")
    resp = json.loads(resp)

    print(resp)
    return resp


def analyze_node_pool(node_pool_list:List[NodePoolInfo]) -> None:
    max_cpu_over_sell_rate = 20 # 2000%
    max_cpu_mean_use_rate = 50.0 # 节点池CPU平均利用率不要超过50%
    max_mem_sell_rate = 95.0 # 内存售卖率不要超过95%
    max_cpu_sell_rate_when_not_over_sell = 90 # 不超分的时候，CPU 的售卖率不要超过90%

    total_save_core = 0
    for np in node_pool_list:
        if np.mem_sell_rate == 0 or np.cpu_mean_usage_week == 0:
            print("nodepool {} not used.".format(np.name))
            continue

        # 计算推荐的超分
        ## 如果内存不超分的情况
        over_sell_rate = min(max_mem_sell_rate / np.mem_sell_rate, max_cpu_mean_use_rate / np.cpu_mean_usage_week, max_cpu_over_sell_rate)
        ## 如果不考虑内存，那么超分比应该是多少
        over_sell_rate2 = min(max_cpu_mean_use_rate / np.cpu_mean_usage_week,
                             max_cpu_over_sell_rate)
        print("nodepool:{}, sell rate should be {} or {} (if no mem limit)".format(str(np), over_sell_rate, over_sell_rate2))


        # 计算如果不超分，onvke 后可以节省的 CPU
        # 在不超分的情况下，把内存用到上限max_mem_sell_rate，此时需要的 CPU 售卖率为：
        x = max_mem_sell_rate / np.mem_sell_rate * np.cpu_sell_rate
        if x >= max_cpu_sell_rate_when_not_over_sell:
            print("如果不超分，nodepool {} CPU 不会有浪费，内存足以让 CPU 卖到上限{},{},{}".format(np.name, x, np.mem_sell_rate, np.cpu_sell_rate))
        else:
            # 实际需要的 core 数 * max_cpu_sell_rate_when_not_over_sell = 当前的 core 数 * x
            save_cpu_core =  (1 - x / max_cpu_sell_rate_when_not_over_sell) * np.total_cpu
            print("如果不超分，nodepool {} CPU 浪费 {} core".format(np.name, save_cpu_core))

        # 在超分的情况下，把内存用到上限，此时需要的 CPU 售卖率为:
        # y代表超分后实际需要的 core 是当前节点池 core 的百分之几
        # y * max_cpu_mean_use_rate / 100 = x * (cpu 利用率/cpu 售卖率)
        y = x * np.cpu_mean_usage_week / np.cpu_sell_rate / max_cpu_mean_use_rate * 100

        if y >= 100:
            print("如果超分，nodepool {} CPU 不会有浪费，内存足以让 CPU 卖到上限{},{}".format(np.name, y, np.cpu_mean_usage_week))
        else:
            # 实际需要的 core 数 * max_cpu_sell_rate_when_not_over_sell = 当前的 core 数 * x
            save_cpu_core = (100 - y) / 100 * np.total_cpu
            print("如果超分，nodepool {} CPU 浪费 {} core y:{}".format(np.name, save_cpu_core, y))
            total_save_core += save_cpu_core

        # 计算如果超分，onvke 后可以节省的 cpu
        # 计算在推荐的超分的条件下，合适的CPU、内存比应该是什么样的？
        new_mem_G = (np.mem_sell_rate * over_sell_rate2 / 100.0) * np.total_mem / 1024
        print("nodepool {} cpu:mem should be 1:{}".format(np.name, new_mem_G / np.total_cpu) )

    print("total save core:{}".format(total_save_core))

def main():
    host = "volc-ops-influxdb-boe.byted.org"
    port = 80
    db = "cloud_storage"
    query = "show measurements"
    # query_influxb_by_http(host, port, db, query)

    # draw_heatmap()
    # demo2()

    # LF BOE 环境
    lf_boe = {
        "host": "volc-ops-influxdb-boe-lfwg.byted.org",
        "port": 80,
        "db": "cloud_storage",
    }

    # LF 线上环境
    lf = {
        "host": "volc-ops-influxdb.byted.org",
        "port": 80,
        "db": "cloud_storage",
        "region": "cn-beijing",
        # 只读数据库，用于获取节点的信息
        "mysqlhost": '10.8.110.2',
        "user": 'dts',
        "password": 'ADK123adk!',
        "database": 'inframgmt',

        # 基础设施服务访问入口
        "open_api_host": "10.250.27.25",
        "open_api_port": 32773,
    }

    test_env = lf

    # 从数据库获取初步的节点列表
    node_list = get_node_list_from_db(test_env["mysqlhost"], test_env["user"], test_env["password"])
    # 构建以 IP 为 key 的 map
    node_map = {}
    for n in node_list:
        node_map[n.node_ip] = n
    # 获取过去7天的节点的 CPU 平均利用率情况
    fetch_node_cpu_usage_mean(node_map, test_env["host"], test_env["port"], test_env["db"],
                              test_env["region"], 24 * 3600 * 7)

    # 获取过去7天的节点的 CPU 的最大利用率情况
    fetch_node_cpu_usage_max(node_map, test_env["host"], test_env["port"], test_env["db"],
                             test_env["region"], 24 * 3600 * 7)

    for n in node_list:
        print(n.__dict__)
    # 获取过去7天的节点的内存使用情况
    fetch_node_mem_statics(node_map, test_env["host"], test_env["port"], test_env["db"],
                           test_env["region"], 24 * 3600 * 7)
    # print("total node number:", len(node_list))
    # print("cpu mean usage < 10% number:", len([x for x in node_list if x.cpu_mean_of_a_week < 10]))
    # print("cpu mean usage < 10% number:", len([x for x in node_list if x.cpu_mean_of_a_week < 5]))

    # 创建集群对象
    cluster_map: Dict[str, ClusterInfo] = {}
    cluster_list = []
    for n in node_list:
        cluster_name = n.cluster
        if cluster_name not in cluster_map:
            cluster = ClusterInfo(cluster_name)
            cluster_list.append(cluster)
            cluster_map[cluster_name] = cluster

    # 创建节点池对象
    node_pool_map: Dict[str, NodePoolInfo] = {}
    node_pool_list = []
    for n in node_list:
        node_pool_name = n.node_pool
        if node_pool_name not in node_pool_map:
            np = NodePoolInfo(node_pool_name)
            node_pool_list.append(np)
            node_pool_map[node_pool_name] = np
            np.node_list.append(n)
        else:
            np = node_pool_map[node_pool_name]
            np.node_list.append(n)
    # 按集群统计 CPU 最大利用率 和 内存最大利用率
    for n in node_list:
        cluster = cluster_map[n.cluster]
        cluster.cpu_max_usage_week = max(n.cpu_max_of_a_week, cluster.cpu_max_usage_week)
        cluster.mem_max_usage_week = max(n.mem_max_of_a_week, cluster.mem_max_usage_week)

    # 按节点池统计 CPU 最大利用率 和 内存最大利用率
    for n in node_list:
        np = node_pool_map[n.node_pool]
        np.cpu_max_usage_week = max(n.cpu_max_of_a_week, np.cpu_max_usage_week)
        np.mem_max_usage_week = max(n.mem_max_of_a_week, np.mem_max_usage_week)

    # 按节点池统计 CPU 平均利用率和内存平均利用率
    for np in node_pool_list:
        np.cpu_mean_usage_week = sum([n.cpu_mean_of_a_week for n in np.node_list]) / len(np.node_list)
        np.mem_mean_usage_week = sum([n.mem_mean_of_a_week for n in np.node_list]) / len(np.node_list)

    # 获取节点池的 CPU、内存售卖情况
    fetch_node_pool_cpu_mem_sell(test_env["open_api_host"], test_env["open_api_port"], node_pool_map)

    draw_cpu_mean_week_bar_char(node_list)
    draw_mem_max_week_bar_char(node_list)
    draw_cluster_cpu_max_week_bar_char(cluster_list)
    draw_cluster_mem_max_week_bar_char(cluster_list)
    draw_node_pool_bar_char(node_pool_list)
    draw_node_pool_statics(node_pool_list)

    for np in node_pool_list:
        print(np)
        if "vedb-azb-pagestore" == np.name:
            for n in np.node_list:
                print(n)

    # 实际型产品的节点池
    instance_node_pool_name_list = ["influxdb",
                               "graph",
                               "config",
                               "mysql",
                               "redis",
                               "hbase",
                               "rds",
                                "mongodb",
                                    "rocketmq",
                                    "kafka",
                                    "rabbitmq",
                                    "vedb",
                               ]
    control_node_pool_suffix = "panel-default"
    def is_instance_node_pool(node_pool_name:str) -> bool:
        node_pool_name = node_pool_name.lower()
        if node_pool_name.endswith(control_node_pool_suffix):
            return False
        for x in instance_node_pool_name_list:
            if x in node_pool_name:
                return True
        return False

    instance_node_pool_list = [np for np in node_pool_list if is_instance_node_pool(np.name)] # 过滤出实例型产品的节点池
    # 分析节点池的合适的超卖率
    analyze_node_pool(instance_node_pool_list)

    return 0


if __name__ == "__main__":
    sys.exit(main())
