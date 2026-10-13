"""模块2 阶段2：出行 & 驻留识别 —— 聚类（PPT 1.2.3 数据流第 2 环）。

本文件负责阶段2：对阶段1 得到的轨迹点做聚类，找出每个用户的驻留候选点。
按课程要求手写 k-means（不用 sklearn），距离用 Haversine 公式（不用 geopandas）。

输入：data/processed/ 下阶段1 的中间结果
输出：data/processed/ 下的中间结果（聚类簇心、簇标签）
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def main():
    """聚类主流程（骨架，手写 k-means 待实现）。"""
    print('[模块2-阶段2] 出行驻留识别-聚类：待实现（手写 k-means）')


if __name__ == '__main__':
    main()
