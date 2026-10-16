"""模块2 阶段3：出行 & 驻留识别 —— 业务判定（PPT 1.2.3 数据流第 2 环）。

本文件负责阶段3：在聚类结果上按业务规则（驻留时长、时段等）判定
每个簇是"驻留"还是"路过"，给每个用户打出出行/驻留标签。

输入：data/processed/ 下阶段2 的聚类结果
输出：result/stage3_label.csv（出行/驻留标签表）
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from project_code.config import (  # noqa: E402
    CLUSTER_DIST_THRESHOLD,
    PROCESSED_DIR,
    PROCESSED_FILES,
    RESULT_DIR,
    RESULT_FILES,
    TIME_SPAN_THRESHOLD,
)
from project_code.utils import (  # noqa: E402
    Harversine,
    _read_csv_any_encoding,
    parse_time,
    save_result,
)


def main():
    """业务判定主流程（课时40~41）：单点簇直接判出行；
    多点簇"首/中/尾三点到簇中心距离都 <1km 且首末跨度 <2h"判驻留，否则判出行。"""
    print('[模块2-阶段3] 出行驻留识别-业务判定：开始')
    cluster = _read_csv_any_encoding(PROCESSED_DIR/PROCESSED_FILES['stage2_cluster'],dtype={'imsi':str})
    cleaned = _read_csv_any_encoding(RESULT_DIR/RESULT_FILES['cleaned'],dtype={'imsi':str,"lac_id":str,'cell_id':str})
    df = cleaned.merge(
        cluster[['imsi','time','cluster','is_single_cluster']],
        on=['imsi','time'],how='left'
    )
    assert len(df) == len(cleaned)  # 课时40：左连接后行数必须不变（防 cluster 表 (imsi,time) 重复）
    df['cluster'] = df['cluster'].fillna(-1).astype(int)
    df['is_single_cluster'] = df['is_single_cluster'].fillna(0).astype(int)
    df['time_dt'] = parse_time(df['time'])
    df = df.sort_values(['imsi','time']).reset_index(drop=True)
    df["label"] = 0

    clustered = df[df['cluster']>=0]
    n_single_travel = 0
    n_multi_travel = 0
    n_multi_stay = 0
    for (imsi,cid),g in clustered.groupby(['imsi','cluster'],sort=False):
        idx=g.index
        if int(g['is_single_cluster'].iloc[0]) == 1 or len(g) == 1:
            df.loc[idx,"label"] = 1
            n_single_travel +=1
            continue
        center_lon = g["lon"].mean()
        center_lat = g['lat'].mean()
        first,mid,last = g.iloc[0],g.iloc[len(g) // 2],g.iloc[-1]

        d_first=Harversine(center_lon,center_lat,first['lon'],first['lat'],unit='m')
        d_mid=Harversine(center_lon,center_lat,mid['lon'],mid['lat'],unit='m')
        d_last=Harversine(center_lon,center_lat,last['lon'],last['lat'],unit='m')

        time_span_h = (last['time_dt'] - first["time_dt"]).total_seconds()/3600.0

        is_stay = (d_first<CLUSTER_DIST_THRESHOLD and d_mid<CLUSTER_DIST_THRESHOLD
                   and d_last<CLUSTER_DIST_THRESHOLD and time_span_h < TIME_SPAN_THRESHOLD)
        if is_stay:
            n_multi_stay +=1
        else:
            df.loc[idx,'label'] = 1
            n_multi_travel +=1
    out = df[['imsi','time','lac_id','cell_id','lon','lat','label']]
    save_result(out, RESULT_FILES['stage3'])

    n_travel = int((df['label'] == 1).sum())
    n_stay = int((df['label'] == 0).sum())
    total = len(df)
    print(f'单点簇判出行 {n_single_travel}；多点簇判出行 {n_multi_travel}；多点簇判驻留 {n_multi_stay}')
    print(f'最终：出行 {n_travel}（{n_travel / total * 100:.1f}%），驻留 {n_stay}（{n_stay / total * 100:.1f}%）')
if __name__ == '__main__':
    main()
