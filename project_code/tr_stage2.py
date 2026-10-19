"""模块2 阶段2：出行 & 驻留识别 —— 聚类（PPT 1.2.3 数据流第 2 环）。

本文件负责阶段2：对阶段1 得到的轨迹点做聚类，找出每个用户的驻留候选点。
按课程要求手写 k-means（不用 sklearn）。距离用平面欧氏近似——课时41 的分工：
"聚类用平面近似、判阈值用真实距离"，阶段3 的阈值判定才用 Haversine 真实距离。

每个用户独立聚类，k 的选取按课时37「轮廓系数与邓恩指数选 K」：
让 k 从 K_MIN 到 K_MAX 都试一遍，用"轮廓系数 + 0.1 × 邓恩指数"打分，
分最高的 k 入选（轮廓系数为主、邓恩指数小权重辅助，两者量级不同用 0.1 平衡）。

输入：data/processed/stage1_dt.csv（阶段1 输出，出行点：imsi,time,lac_id,cell_id,lon,lat,speed）
输出（data/processed/，阶段3 接力用）：
- stage2_cluster.csv  在出行点基础上加两列（课时38）：
    cluster（簇编号，每用户内从 0 开始，配合 imsi 使用不会混淆）
    is_single_cluster（是否单点簇：簇里只有 1 个点记 1，阶段3 直接判出行）
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# 把项目根目录加入模块搜索路径，保证不管从哪个目录运行都能 import project_code
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from project_code.config import PROCESSED_DIR  # noqa: E402
from project_code.utils import (  # noqa: E402
    _read_csv_any_encoding,
    save_processed,
)

# 阶段间中间结果文件名（文件名写死，与阶段1 的 stage1_dt.csv 同款做法）
STAGE1_INPUT_FILE = 'stage1_dt.csv'        # 阶段1 输出（出行点）
STAGE2_OUT_FILE = 'stage2_cluster.csv'     # 阶段2 输出（课时38：出行点 + cluster + is_single_cluster）

# 课时37：候选 k 的范围
K_MIN = 2
K_MAX = 10


def pairwise_euclidean(X):
    """点到点欧氏距离矩阵（课时37：pairwise_euclidean）。广播一次算好，各 k 复用。

    X[:, None, :] 是 (n,1,2)，X[None, :, :] 是 (1,n,2)，相减平方求和 axis=2 得 (n,n)。
    对角线是点到自己的距离，恒为 0。
    """
    return np.sqrt(((X[:, None, :] - X[None, :, :]) ** 2).sum(axis=2))


def kmeans(X, k, max_iter=100, tol=1e-6):
    """手写 k-means（课时36，NumPy 实现，不用 sklearn），平面欧氏距离。

    参数:
        X: (n,2) 数组，列为 (lon, lat)
        k: 簇数
        max_iter: 最大迭代次数
        tol: 簇心位移收敛容差

    返回 (labels, centers)：labels 为每点簇号，centers 为簇心 (k,2)。
    初始化用 np.random.choice 全局随机源，main() 里先 np.random.seed(42) 固定，结果可复现。
    """
    n = len(X)
    if k >= n:                       # 簇数不少于点数：每个点自成一簇
        return np.arange(n, dtype=int), X.copy()
    # 1) 随机选 k 个样本作为初始中心（不重复抽样）
    centers = X[np.random.choice(n, k, replace=False)].copy()
    labels = np.zeros(n, dtype=int)

    for _ in range(max_iter):
        # 2) 分配步：每个点到所有中心的距离，取最近的簇
        dist = np.sqrt(((X[:, None, :] - centers[None, :, :]) ** 2).sum(axis=2))
        new_labels = dist.argmin(axis=1)

        # 3) 更新步：每簇成员均值为新中心；空簇保留旧中心（避免 NaN）
        new_centers = centers.copy()
        for c in range(k):
            mask = new_labels == c
            if mask.any():
                new_centers[c] = X[mask].mean(axis=0)

        # 中心位移，小于 tol 认为收敛
        shift = np.sqrt(((new_centers - centers) ** 2).sum())
        labels, centers = new_labels, new_centers
        if shift < tol:
            break
    return labels, centers


def silhouette_score(D, labels):
    """轮廓系数（课时37，手写）：所有点平均 s(i)，范围 -1~1，越接近 1 越好。

    对每个点 i：
    - a(i)：点 i 到同簇其他点的平均距离（越小越紧）；
    - b(i)：点 i 到"最近的另一个簇"所有点的平均距离（越大越分开）；
    - s(i) = (b - a) / max(a, b)。
    """
    #找到所有的簇号
    uniq = np.unique(labels)
    #单簇没法算
    if len(uniq) <= 1:
        return 0.0
    #创建vals数组，代表每个样本点的轮廓系数，越大越好
    n = len(labels)
    vals = np.zeros(n)
    #遍历每一个点，找到除了自己之外的与i同簇的点计算平均距离，命名为a
    for i in range(n):
        same = (labels == labels[i]); same[i] = False
        a = D[i, same].mean() if same.any() else 0.0  # 单点簇 a 按 0 处理
        #b=到最近别的簇的平均距离
        b = np.inf
        for c in uniq:
            if c == labels[i]:
                continue
            other = (labels == c)
            if other.any():
                b = min(b, D[i, other].mean())
        denom = max(a, b)
        vals[i] = (b - a) / denom if denom > 0 else 0.0
    return float(vals.mean())


def dunn_index(D, labels):
    """邓恩指数（课时37，手写）：簇间最小距离 / 簇内最大直径，越大越好。

    分子越大（簇间隔得开）、分母越小（簇内越紧），值越大越好。
    np.ix_ 用于取"行集合×列集合"的子矩阵。
    """
    uniq = np.unique(labels)
    max_intra = 0.0
    for c in uniq:  # 各簇最大直径
        idx = np.where(labels == c)[0]
        if len(idx) > 1:
            max_intra = max(max_intra, D[np.ix_(idx, idx)].max())
    min_inter = np.inf
    for i in range(len(uniq)):
        for j in range(i + 1, len(uniq)):  # 簇间最小距离
            a = np.where(labels == uniq[i])[0]
            b = np.where(labels == uniq[j])[0]
            min_inter = min(min_inter, D[np.ix_(a, b)].min())
    if max_intra <= 0:
        return 0.0
    return float(min_inter / max_intra)


def choose_best_k(X):
    """课时37 选 k：k 从 K_MIN 到 K_MAX 都试一遍，选打分最高的 k。

    打分：score = 轮廓系数 + 0.1 × 邓恩指数（轮廓系数为主、邓恩指数小权重辅助）。
    距离矩阵 D 只算一次，各 k 复用，省时间；n < K_MIN 的点太少，直接单簇。
    返回 (best_labels, best_k)。
    """
    n = len(X)
    if n < K_MIN:  # 点太少，直接单簇
        return np.zeros(n, dtype=int), 1
    D = pairwise_euclidean(X)  # 距离矩阵只算一次，各 K 复用
    k_max = min(K_MAX, n)
    best_score, best_k, best_labels = -np.inf, 1, np.zeros(n, dtype=int)
    for k in range(K_MIN, k_max + 1):
        labels, _ = kmeans(X, k)
        if len(np.unique(labels)) < 2:
            score = -np.inf  # 退化成单簇不给高分
        else:
            score = silhouette_score(D, labels) + 0.1 * dunn_index(D, labels)
        if score > best_score:  # 严格大于：分数打平取更小的 k
            best_score, best_k, best_labels = score, k, labels
    return best_labels, best_k


def main(seed=42):
    """阶段2 主流程：读阶段1 中间结果 → 每用户聚类（课时37 自动选 k）→ 写 stage2_cluster.csv。

    seed 默认 42，保证选 k 结果可复现（main.py 以 module.main() 无参调用）。
    """
    print('[模块2-阶段2] 出行驻留识别-聚类：开始')

    path = PROCESSED_DIR / STAGE1_INPUT_FILE
    if not path.exists():
        print(f'[模块2-阶段2] 未找到阶段1 中间结果: {path}')
        print('    请先运行: python project_code/tr_stage1.py')
        raise FileNotFoundError(
            f'未找到阶段1 中间结果: {path}，请先运行 python project_code/tr_stage1.py'
        )

    # imsi 按字符串读，防止丢前导零/精度（阶段1 同款约定）
    df = _read_csv_any_encoding(path, dtype={'imsi': str})
    if df.empty:
        raise FileNotFoundError(
            f'阶段1 中间结果为空: {path}，请重新运行 python project_code/tr_stage1.py'
        )

    # 聚类前固定随机种子（课时38），所有随机初始化确定，每次跑出同样的簇
    np.random.seed(seed)

    # 逐用户聚类：聚类只在同一个用户的点之间进行（课时38），
    # 所以 groupby("imsi") 后逐人调用选 K + K-Means
    out_parts, chosen_ks = [], []
    for imsi, g in df.groupby('imsi', sort=False):  # sort=False 保持文件顺序，输出可复现
        X = g[['lon', 'lat']].to_numpy(dtype=float)
        labels, best_k = choose_best_k(X)
        chosen_ks.append(best_k)

        g = g.copy()
        g['cluster'] = labels             # 簇编号（每用户内从 0 开始）
        # 单点簇标记：簇里只有 1 个点记 1（阶段3 直接判出行）
        size_map = pd.Series(labels).value_counts()
        g['is_single_cluster'] = g['cluster'].map(
            lambda c: 1 if size_map.get(c, 0) == 1 else 0)
        out_parts.append(g)

    result = pd.concat(out_parts, ignore_index=True)
    result['cluster'] = result['cluster'].astype(int)
    out_path = save_processed(result, STAGE2_OUT_FILE)

    n_clusters = int(result.groupby(['imsi', 'cluster']).ngroups)  # 实际形成的簇数（空簇不算）
    n_single = int((result['is_single_cluster'] == 1).sum())  # 单点簇数
    ks = np.array(chosen_ks)
    print(f'读入阶段1出行点: {len(result)} 行, {len(chosen_ks)} 个用户')
    print(f'共形成 {n_clusters} 个簇（其中单点簇 {n_single} 个），')
    print(f'最优K分布: 最小 {ks.min()} / 最大 {ks.max()} / 平均 {ks.mean():.1f}')
    print(f'保存: {out_path}')
    return {
        'input_rows': len(result),
        'users': len(chosen_ks),
        'n_clusters': n_clusters,
        'n_single_clusters': n_single,
        'out_path': out_path,
    }


if __name__ == '__main__':
    main()
