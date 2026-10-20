"""模块2 阶段2：出行 & 驻留识别 —— 聚类（PPT 1.2.3 数据流第 2 环）。

本文件负责阶段2：对阶段1 得到的轨迹点做聚类，找出每个用户的驻留候选点。
按课程要求手写 k-means（不用 sklearn）。距离用平面欧氏近似——课时41 的分工：
"聚类用平面近似、判阈值用真实距离"，阶段3 的阈值判定才用 Haversine 真实距离。

每个用户独立聚类，k 的选取按轮廓系数与邓恩指数选 K：
让 k 从 K_MIN 到 K_MAX 都试一遍，用"轮廓系数 + 0.1 × 邓恩指数"打分，
分最高的 k 入选（轮廓系数为主、邓恩指数小权重辅助，两者量级不同用 0.1 平衡）。

输入：data/processed/stage1_dt.csv（阶段1 输出，出行点：imsi,time,lac_id,cell_id,lon,lat,speed）
输出（data/processed/，阶段3 ）：
- stage2_cluster.csv  在出行点基础上加两列：
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
    """点到点欧氏距离矩阵（pairwise_euclidean）。广播一次算好，各 k 复用。

    输入：X 是 (n,2) 数组——n 个点，每个点 (lon, lat) 两个坐标。
    输出：D 是 (n,n) 矩阵——D[i, j] = 点 i 到点 j 的欧氏距离。
    后面轮廓系数、邓恩指数都要反复查"点 i 到点 j 的距离"，所以一次算好整张表，
    每个候选 k 复用，避免重复计算。

    X[:, None, :] 是 (n,1,2)，X[None, :, :] 是 (1,n,2)，相减平方求和 axis=2 得 (n,n)。
    对角线是点到自己的距离，恒为 0。
    """
    # 广播的形状变化（重点，课时11）：
    #   X[:, None, :]  -> (n, 1, 2)：n 个点竖着摆，第 2 维留 1 个位置等着广播
    #   X[None, :, :]  -> (1, n, 2)：同样的 n 个点横着摆
    # 相减时 numpy 自动把 1 扩成对方的大小 -> (n, n, 2)
    # 第 [i, j] 格 = 点 i 的坐标 - 点 j 的坐标（两个数的差）
    return np.sqrt(((X[:, None, :] - X[None, :, :]) ** 2).sum(axis=2))
    #      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^  平方后沿 axis=2（坐标那一维）求和
    #      得到每对点的"坐标差平方和"；再开根号就是欧氏距离公式
    #      sqrt((x1-x2)^2 + (y1-y2)^2)。结果 (n,n)，对角线上自己到自己恒为 0


def kmeans(X, k, max_iter=100, tol=1e-6):
    """手写 k-means（NumPy 实现，不用 sklearn），平面欧氏距离。

    参数:
        X: (n,2) 数组，列为 (lon, lat)
        k: 簇数
        max_iter: 最大迭代次数
        tol: 簇心位移收敛容差

    返回 (labels, centers)：labels 为每点簇号，centers 为簇心 (k,2)。
    初始化用 np.random.choice 全局随机源，main() 里先 np.random.seed(42) 固定，结果可复现。
    """
    n = len(X)                                # 一共有多少个点
    if k >= n:                                # 簇数不少于点数：不用聚了
        return np.arange(n, dtype=int), X.copy()  # 每个点自成一簇：标签 0,1,2...，簇心就是点本身
    # 1) 随机选 k 个样本作为初始中心（不重复抽样）
    centers = X[np.random.choice(n, k, replace=False)].copy()  # 随机取 k 个点当初始簇心,返回一个k*2的数组
    #        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    #        np.random.choice(n, k, replace=False)：从 0..n-1 里"不重复"地抽 k 个下标
    #        X[下标] 取出这 k 个点；得到 (k,2) 的初始簇心表
    labels = np.zeros(n, dtype=int)  # 一维数组，下标=样本号，值=该样本所在的簇，先全记 0

    for _ in range(max_iter):                 # 最多迭代 max_iter 轮，防止不收敛时死循环
        # 2) 分配步：每个点到所有簇心的距离，取最近的簇
        dist = np.sqrt(((X[:, None, :] - centers[None, :, :]) ** 2).sum(axis=2))
        #      X 变 (n,1,2)、centers 变 (1,k,2)，广播相减得 (n,k,2) 再按坐标求和开根号
        #      X n行1列，centers 1行k列，每个单元格包含一个位置坐标（x，y）
        #      结果 dist 是 (n,k) 数组：dist[i, c] = 点 i 到簇心 c 的距离
        new_labels = dist.argmin(axis=1)      # 每行取最小值的列号 -> 点 i 最近的簇编号

        # 3) 更新步：每簇成员均值为新中心；空簇保留旧中心（避免 NaN）
        new_centers = centers.copy()          # 先复制旧簇心，下面逐簇覆盖
        for c in range(k):                    # 遍历每一个簇
            mask = new_labels == c            # 布尔数组：哪些样本属于簇 c（匹配相同簇的样本）
            if mask.any():                    # 该簇至少有一个成员才更新
                new_centers[c] = X[mask].mean(axis=0)  # 求该簇所有样本的均值，作为新簇心
                # 空簇（mask 全 False）不更新，沿用旧簇心——否则对空数组求均值会产生 NaN

        # 4) 收敛判断：所有簇心一共移动了多少，小于 tol 认为收敛
        shift = np.sqrt(((new_centers - centers) ** 2).sum())  # 新旧簇心差值的总长度
        labels, centers = new_labels, new_centers              # 更新：用新结果替换旧结果
        if shift < tol:                       # 簇心几乎不动了，提前结束迭代
            break
    return labels, centers


def silhouette_score(D, labels):
    """轮廓系数：所有点平均 s(i)，范围 -1~1，越接近 1 越好。

    对每个点 i：
    - a(i)：点 i 到同簇其他点的平均距离（越小越紧）；
    - b(i)：点 i 到"最近的另一个簇"所有点的平均距离（越大越分开）；
    - s(i) = (b - a) / max(a, b)。
    """
    uniq = np.unique(labels)                  # 找到所有的簇号，比如 [0, 1, 2]
    if len(uniq) <= 1:                        # 只有一个簇（或没有）没法算"簇间"，直接返回 0
        return 0.0
    n = len(labels)                           # 点的总数
    vals = np.zeros(n)                        # 创建 vals 数组，存每个点的轮廓系数（越大越好）
    # 遍历每一个点，计算它的 s(i)
    for i in range(n):
        same = (labels == labels[i]); same[i] = False
        #       布尔数组：哪些点和 i 同簇；再把 i 自己排除掉——
        #       自己到自己的距离是 0，混进去会把平均值拉低
        a = D[i, same].mean() if same.any() else 0.0  # 单点簇没有"其他同簇点"，a 按 0 处理
        #       a = 点 i 到"同簇其他点"的平均距离（越小说明簇内越紧）
        b = np.inf                            # b = 点 i 到"最近的另一个簇"的平均距离，先设无穷大
        for c in uniq:                        # 遍历所有簇，找最近的"别的"簇
            if c == labels[i]:                # 跳过自己所在的簇
                continue
            other = (labels == c)             # 布尔数组：簇 c 的成员
            if other.any():                   # 簇 c 有成员才参与比较
                b = min(b, D[i, other].mean())  # 与各"别的簇"平均距离取最小 -> b
        denom = max(a, b)                     # 公式里的分母 max(a, b)
        vals[i] = (b - a) / denom if denom > 0 else 0.0
        #   ^^^^^^^^^^^^^^^^ 公式计算轮廓指数 s(i) = (b - a) / max(a, b)
        #   b 远大于 a -> 接近 1（好）；a、b 差不多 -> 接近 0；a 大于 b -> 负数（差）
        #   denom == 0（该点与所有点完全重合）时公式无意义，记 0 兜底
    return float(vals.mean())                 # 所有点取平均 = 这次聚类的轮廓系数


def dunn_index(D, labels):
    """邓恩指数：簇间最小距离 / 簇内最大直径，越大越好。

    分子越大（簇间隔得开）、分母越小（簇内越紧），值越大越好。
    np.ix_ 用于取"行集合×列集合"的子矩阵。
    """
    uniq = np.unique(labels)                  # 所有簇号
    # ---------- 分母：各簇的最大直径 ----------
    max_intra = 0.0                           # 所有簇直径里的最大值，先记 0
    for c in uniq:  # 各簇最大直径
        idx = np.where(labels == c)[0]        # 簇 c 的成员下标
        if len(idx) > 1:                      # 单点簇直径是 0，跳过不算
            max_intra = max(max_intra, D[np.ix_(idx, idx)].max())
            #   D[np.ix_(idx, idx)] 取"簇 c 成员 × 簇 c 成员"的子矩阵，
            #   最大值就是簇内最远两点之间的距离（直径）
    # ---------- 分子：不同簇之间的最小距离 ----------
    min_inter = np.inf                        # 所有簇对里最近的距离，先记无穷大
    for i in range(len(uniq)):
        for j in range(i + 1, len(uniq)):     # 两两配对，且 (i, j) 不重复组合
            a = np.where(labels == uniq[i])[0]  # 簇 i 的成员下标
            b = np.where(labels == uniq[j])[0]  # 簇 j 的成员下标
            min_inter = min(min_inter, D[np.ix_(a, b)].min())
            #   D[np.ix_(a, b)] 是"簇 i 成员 × 簇 j 成员"的子矩阵，
            #   最小值就是这两个簇之间最近的两点距离
    if max_intra <= 0:                        # 所有簇直径都是 0（全是重合点），比值无意义
        return 0.0
    return float(min_inter / max_intra)       # 间隔大、直径小 -> 邓恩指数大 -> 聚类好


def choose_best_k(X):
    """选 k：k 从 K_MIN 到 K_MAX 都试一遍，选打分最高的 k。

    打分：score = 轮廓系数 + 0.1 × 邓恩指数（轮廓系数为主、邓恩指数小权重辅助）。
    距离矩阵 D 只算一次，各 k 复用，省时间；n < K_MIN 的点太少，直接单簇。
    返回 (best_labels, best_k)。
    """
    n = len(X)                                # 这个用户的点数
    if n < K_MIN:                             # 点太少（不足 K_MIN=2 个），不值得聚
        return np.zeros(n, dtype=int), 1      # 全部归到 0 号簇，k=1
    D = pairwise_euclidean(X)                 # 距离矩阵只算一次，后面每个候选 k 都复用
    k_max = min(K_MAX, n)                     # 候选 k 的上限：最多 10，也不超过点数
    best_score, best_k, best_labels = -np.inf, 1, np.zeros(n, dtype=int)
    #   当前最好分数 / 对应的 k / 对应的标签；分数从 -inf 起，
    #   保证任何一个"合法"候选都能超过它，选出真正的最大值
    for k in range(K_MIN, k_max + 1):         # k = 2, 3, ..., k_max 逐个试
        labels, _ = kmeans(X, k)              # 用这个 k 跑一次 k-means（只关心标签）
        if len(np.unique(labels)) < 2:        # 实际只聚出 1 个簇（退化）
            score = -np.inf                   # 给最低分，等于放弃这个 k
        else:
            score = silhouette_score(D, labels) + 0.1 * dunn_index(D, labels)
            #       轮廓系数为主（范围 -1~1），邓恩指数量级偏大、乘 0.1 当小权重辅助
        if score > best_score:                # 严格大于才换 -> 分数打平时保留更小的 k
            best_score, best_k, best_labels = score, k, labels
    return best_labels, best_k                # 返回最优 k 对应的标签和 k


def main(seed=42):
    """
    阶段2：把疑似出行点按用户分组，每个用户互相独立；用手写 K-Means 聚类，k 从 2 到 10 逐个试，以「轮廓系数 + 0.1×邓恩指数」打分选出最优 k。簇号
    在用户内从 0开始，所以不同用户之间簇号可能相同，要配合 imsi 使用。输出带 cluster 和 is_single_cluster 两列的表给阶段3。

    Q&A：
    Q：为什么要对阶段1粗筛出的出行点再进行筛选？
    A：手机信号在两三个基站之间来回切换时，位置记录会来回跳，人站着条，相邻点的距离很大，算出来的速度也大

    Q：为什么要聚类
    A：① 把一天的散点切成"停留候选区"
    一个用户一天的疑似出行点散在各地：家附近一团、公司附近一团、商场附近一团，中间是路上的点。聚类把这些空间上挨得近的点自动归组——tr_stage2.py 的
    docstring
    说得直接："找出每个用户的驻留候选点"。每个簇就是一个候选的停留区，阶段3 再逐个验真。

    ② 产出"簇心"——阶段3 规则的参照系
    阶段3 判定写的是"首/中/尾三点到簇中心距离 < 1km"。这个簇心只有聚类能给出（簇内点坐标均值）。没有聚类，这条规则连计算对象都没有。

    ③ 把不可靠的单点信号转成可靠的群体形状
    单点速度会被基站抖动骗（假高速），但一组点的空间分布形态骗不了人：
    - 聚成一团（都在簇心 1km 内、跨度 <2h）→ 人没走远 → 驻留
    - 散成一条线 → 人真在移动 → 出行

    """
    print('[模块2-阶段2] 出行驻留识别-聚类：开始')  # 运行提示

    path = PROCESSED_DIR / STAGE1_INPUT_FILE   # 拼接输入文件完整路径：data/processed/stage1_dt.csv
    if not path.exists():                      # 阶段1 还没跑过：文件不存在
        print(f'[模块2-阶段2] 未找到阶段1 中间结果: {path}')
        print('    请先运行: python project_code/tr_stage1.py')
        raise FileNotFoundError(               # 给出可操作的提示后直接报错退出（fail-fast），
            f'未找到阶段1 中间结果: {path}，请先运行 python project_code/tr_stage1.py'
        )                                      # 不让流水线在后面的环节才莫名其妙地挂掉

    # imsi 按字符串读，防止丢前导零/精度（阶段1 同款约定）
    df = _read_csv_any_encoding(path, dtype={'imsi': str})
    #   读阶段1 输出；dtype 指定 imsi 为字符串（15 位手机号按数字读会丢精度），
    #   编码 UTF-8 / GBK 由工具函数自动兜底
    if df.empty:                               # 文件存在但是空表（异常情况）
        raise FileNotFoundError(               # 提示重新跑阶段1
            f'阶段1 中间结果为空: {path}，请重新运行 python project_code/tr_stage1.py'
        )

    # 聚类前固定随机种子（课时38），所有随机初始化确定，每次跑出同样的簇
    np.random.seed(seed)

    # 逐用户聚类：聚类只在同一个用户的点之间进行（课时38），
    # 所以 groupby("imsi") 后逐人调用选 K + K-Means
    out_parts, chosen_ks = [], []              # 收集每个用户的结果片段 / 每个用户选出的 k
    for imsi, g in df.groupby('imsi', sort=False):  # 按 imsi 分组，逐个用户处理
        #                sort=False 保持文件里的原始顺序，输出字节级可复现
        X = g[['lon', 'lat']].to_numpy(dtype=float)  # 取出该用户的坐标，转成 (n,2) 数组
        labels, best_k = choose_best_k(X)      # 自动选 k 并聚类，返回每点簇号和选中的 k
        chosen_ks.append(best_k)              # 记下这个用户的 k，最后统计最优 K 分布用

        g = g.copy()                           # 复制一份再改，避免改到分组产生的视图
        g['cluster'] = labels                  # 簇编号（每用户内从 0 开始，配合 imsi 使用不会混淆）
        # 单点簇标记：簇里只有 1 个点记 1（阶段3 直接判出行）
        size_map = pd.Series(labels).value_counts()  # 数每个簇有几个点：簇号 -> 点数
        g['is_single_cluster'] = g['cluster'].map(   # 每个点去查"自己所在的簇有几个点"
            lambda c: 1 if size_map.get(c, 0) == 1 else 0)  # 只有自己 1 个点 -> 记 1
        out_parts.append(g)                    # 收起来，最后统一拼表

    result = pd.concat(out_parts, ignore_index=True)  # 所有用户的结果拼回一张大表（行号重置）
    result['cluster'] = result['cluster'].astype(int)  # 簇号统一转整数（去掉浮点形式）
    out_path = save_processed(result, STAGE2_OUT_FILE)  # 保存到 data/processed/stage2_cluster.csv

    n_clusters = int(result.groupby(['imsi', 'cluster']).ngroups)  # 实际形成的簇数（空簇不算）
    n_single = int((result['is_single_cluster'] == 1).sum())       # 单点簇的个数
    ks = np.array(chosen_ks)                   # 所有用户的 k 拼成数组，方便统计最小/最大/平均
    print(f'读入阶段1出行点: {len(result)} 行, {len(chosen_ks)} 个用户')
    print(f'共形成 {n_clusters} 个簇（其中单点簇 {n_single} 个），')
    print(f'最优K分布: 最小 {ks.min()} / 最大 {ks.max()} / 平均 {ks.mean():.1f}')
    print(f'保存: {out_path}')
    return {                                   # 把关键统计返回给调用方（如 main.py），方便串联
        'input_rows': len(result),
        'users': len(chosen_ks),
        'n_clusters': n_clusters,
        'n_single_clusters': n_single,
        'out_path': out_path,
    }


if __name__ == '__main__':
    main()
