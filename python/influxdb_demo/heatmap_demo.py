import sys
from copy import deepcopy
from typing import Dict, List

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd


def demo1():
    # 构造一个 key 为“集群”，值为机器的 CPU 使用率的DataFrame，然后看看画出来什么样
    data = {"name": [0.2, 0.2, 0.3, 0.4],
            'age': [0.9, 0.8, 0.19, 0.19]}

    df = pd.DataFrame(data)
    f, ax = plt.subplots(figsize=(15, 15))
    ax.set_title('Cluster Node CPU Heatmap')
    # 设置展示一半，如果不需要注释掉mask即可
    # mask = np.zeros_like(df)
    # mask[np.triu_indices_from(mask)] = True  # np.triu_indices 上三角矩阵

    with sns.axes_style("white"):
        sns.heatmap(df,
                    cmap="YlGnBu",
                    annot=True,
                    )
    # plt.show()
    plt.savefig("report/heatmap.svg", dpi=250)

def ShowGRAHeatMap(data:Dict[str, List], title:str = "", savefileto: str = ""):
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
            mask[key] = ori_len * [False] # 对于原始的值，mask = False，都展示
            mask[key].extend((max_len - ori_len) * [True]) # 对于补齐的值，mask=True，都不展示
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
    ShowGRAHeatMap(data, title="Cluster Node CPU Heatmap", savefileto="report/heatmap4.svg")


def main():
    demo1()
    demo2()
    return 0


if __name__ == "__main__":
    sys.exit(main())
