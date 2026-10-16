"""模块2 阶段2：出行 & 驻留识别 —— 聚类（PPT 1.2.3 数据流第 2 环）。

本文件负责阶段2：对阶段1 得到的轨迹点做聚类，找出每个用户的驻留候选点。
按课程要求手写 k-means（不用 sklearn），距离用 Haversine 公式（不用 geopandas）。

输入：data/processed/ 下阶段1 的中间结果
输出：data/processed/ 下的中间结果（聚类簇心、簇标签）
"""
import sys
from pathlib import Path
import numpy as np
from project_code.config import PROCESSED_DIR
from project_code.utils import _read_csv_any_encoding

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def main():
    """聚类主流程（骨架，手写 k-means 待实现）。"""
    print('[模块2-阶段2] 出行驻留识别-聚类：待实现（手写 k-means）')
    def kmeans(X,k,max_iter=100,tol=1e-6):
        n=len(X)
        if k>=n:
            return np.arange(n,dtype=int),X.copy()
        centers = X[np.random.choice(n,k,replace=False)].copy(),
        labels = np.zeros(n,dtype=int) #每个样本的簇号，后续持续更新每个样本距离哪个质心最近
        for _ in range(max_iter):
            #返回一个样本点数 * k的矩阵，代表距离每一个中心点的距离
            dist = np.sqrt(((X[:,None,:] - centers[None,:,:])**2).sum(axis=2))
            new_labels = dist.argmin(axis=1)#找到每一个样本所对应的簇
            new_centers = centers.copy()
            for c in range(k):#循环每一个簇编号
                mask = new_labels == c #mask记录样本是否属于当次循环的簇
                if mask.any():#只要mask里任有一个为True就进行计算
                    new_centers[c] = X[mask].mean(axis=0)#
            shift = np.sqrt(((new_centers-centers)**2).sum())
            labels,centers = new_labels,new_centers
            if shift<tol:
                break
        return labels,centers



if __name__ == '__main__':
    main()
