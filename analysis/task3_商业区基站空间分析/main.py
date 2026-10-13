"""task3 商业区/基站空间分析（成员 C）

数据: datas/商业区数据.csv、datas/基站经纬度数据.csv（UTF-8 编码，无表头）
目标: 商业区的空间分布、基站密度与商业区的关系等。
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
    # 两个文件都无表头：前两列是经纬度（商业区数据第三列是商圈名）
    commercial = load_csv('商业区数据.csv', header=None)
    stations = load_csv('基站经纬度数据.csv', header=None)
    print(commercial.shape, stations.shape)

    # TODO: 在这里开始你的分析
    # 例如: 散点图把商业区和基站画在同一张经纬度图上
    # fig, ax = plt.subplots()
    # ax.scatter(stations[0], stations[1], s=1)
    # save_fig(fig, 'task3_xxx.png')


if __name__ == '__main__':
    main()