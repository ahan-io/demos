from typing import Dict, List

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt  # type: ignore
import platform
import numpy as np


def draw_bar(x, y, title, output_file):
    plt.rcParams["font.sans-serif"] = ["Songti SC","WenQuanYi Zen Hei"]
    params = {
        'figure.figsize': '4, 4'
    }
    plt.rcParams.update(params)
    if platform.system().lower() == "windows":
        plt.rcParams["font.sans-serif"] = ["SimHei"]
    if platform.system().lower() == "linux":
        plt.rcParams["font.sans-serif"] = ["SimHei"]
    plt.rcParams["axes.unicode_minus"] = False
    plt.cla()
    plt.bar(x, y)
    for a, c in zip(x, y):
        plt.text(a, c + 0.05, "%.0f" % c, ha="center", va="bottom", fontsize=7)
    plt.title(title)
    plt.savefig(output_file, dpi=250)

def draw_barh(x, y, title, output_file):
    """画横向的 bar
    有时候标签字符数太多了，画成横向的更好展示。
    """
    plt.figure(dpi=250, figsize=(20, 4))
    plt.barh(x, y)
    for a, c in zip(x, y):
        plt.text(c + 0.1, a, "%.0f" % c, ha="center", va="bottom", fontsize=10)
    plt.title(title)
    plt.savefig(output_file)

def draw_barh2(x, y, title, output_file,order:bool=True, text_map:Dict[str, str]=None):
    # 根据列表的长度，设置图的高度
    figsize_height = len(x) * 1
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
    plt.title(title)
    plt.savefig(output_file)

def draw_barh_multi_group(labels: List[str], x: List[List], x_labels: List[str], title: str, output_file: str):
    # 每个柱子的宽度
    width = 0.25
    # 组内的柱子的个数
    num_in_group = len(x)

    # 根据列表的长度，设置图的高度
    figsize_height = len(labels) * width * len(x)
    # 避免高度太小
    figsize_height = max(figsize_height, 10)
    plt.figure(figsize=(15, figsize_height))

    # 每组的 y 轴的间隔
    y_witdh = (num_in_group + 1) * width
    y = np.arange(0, len(labels) * y_witdh, y_witdh)
    # 把 y 轴的 label 旋转一下，避免文字太长放不下
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

    plt.title(title)
    plt.savefig(output_file)


x = ['label1', 'lable2']
y = [10, 20]
draw_bar(x, y, "test", "sample_bar.svg")

x = ['this is a very very very long label1', 'lable2']
y2 = [15, 5]
draw_barh(x, y2, "test", "sample_barh.svg")

draw_barh2(x, y, "test2", "sample_barh2.svg", True)

draw_barh_multi_group(x, [y, y2], ["y", "y2"], "test3", "sample_barh3.svg")