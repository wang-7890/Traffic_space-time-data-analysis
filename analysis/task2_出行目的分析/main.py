"""task2 出行目的分析（成员 B）

数据: datas/出行目的静态数据.csv（GBK 编码，无表头，列含义见数据说明）
目标: 分析出行目的的构成、不同地点的出行目的差异等。
"""
import sys
from pathlib import Path

# 把项目根目录加入模块搜索路径，保证不管从哪个目录运行都能 import src
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import matplotlib.pyplot as plt

from src.data_loader import load_csv
from src.plotting import setup_style, save_fig

setup_style()


def main():
    # 该文件无表头，读取时加 header=None，列名按数据说明自行补充
    df = load_csv('出行目的静态数据.csv', header=None)
    print(df.shape)
    print(df.head())

    # TODO: 在这里开始你的分析
    # fig, ax = plt.subplots()
    # df[...].value_counts().plot(kind='pie', ax=ax)
    # save_fig(fig, 'task2_xxx.png')


if __name__ == '__main__':
    main()