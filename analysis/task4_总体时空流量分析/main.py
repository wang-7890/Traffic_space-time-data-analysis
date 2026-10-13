"""task4 总体时空流量分析（成员 D）

数据: datas/原始数据.csv、datas/实时流数据.csv、datas/hive模块静态数据.csv（UTF-8 编码，无表头）
目标: 总体流量随时间的变化趋势、空间热点等。
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
    # 原始数据.csv 第一列是毫秒时间戳；实时流数据.csv 第一列是时间字符串
    # 原始数据可能很大，先用 nrows 试读，摸清结构后再全量读
    raw = load_csv('原始数据.csv', header=None, nrows=10000)
    realtime = load_csv('实时流数据.csv', header=None, nrows=10000)
    print(raw.shape, realtime.shape)
    print(raw.head())

    # TODO: 在这里开始你的分析
    # 提示: 时间戳转时间可用 src.preprocess.to_datetime(df, 0, unit='ms')
    # fig, ax = plt.subplots()
    # save_fig(fig, 'task4_xxx.png')


if __name__ == '__main__':
    main()