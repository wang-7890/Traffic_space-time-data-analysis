import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from project_code.config import RAW_FILES, RESULT_FILES  # noqa: E402
from project_code.utils import load_csv, save_result,Harversine  # noqa: E402

import pandas as pd
import numpy as np
from haversine import haversine

# 滑窗大小（分钟）：统计"过去 10 分钟"的人次
def heatmap_analysis():
    """实时热力主流程（骨架，滑窗统计待实现）。"""
    WINDOW_MINUTES = 10
    TARGET_DATE = 20181003
    BATCH_SIZE = 10000
    HEATMAP_MATCH_THRESHOLD = 1000  # 单位：米

    print(f'[模块5] 实时商圈热力：滑窗大小 {WINDOW_MINUTES} 分钟')
    #读取实时流数据
    stream = load_csv(RAW_FILES['realtime'], header=None, names=['time','imsi','lon','lat'], dtype=str)

    before = len(stream)
    stream = stream.copy()
    stream['lon'] = pd.to_numeric(stream['lon'], errors='coerce')
    stream['lat'] = pd.to_numeric(stream['lat'], errors='coerce')
    stream = stream.dropna(subset=['lon', 'lat'])
    stream = stream[stream['time'].astype(str).str.startswith(str(TARGET_DATE))]
    stream['time_dt'] = pd.to_datetime(stream['time'], format="%Y%m%d%H%M%S", errors='coerce')
    stream = stream.dropna(subset=['time_dt']).reset_index(drop=True)
    print(before ,"->",len(stream))

    #读取商圈数据
    biz = load_csv(RAW_FILES['biz'], header=None, names=['lon','lat','biz_name'], dtype=str)
    before = len(biz)
    biz = biz.copy()
    biz['lon'] = pd.to_numeric(biz['lon'], errors='coerce')
    biz['lat'] = pd.to_numeric(biz['lat'], errors='coerce')
    biz = biz.dropna(subset=['lon', 'lat']).reset_index(drop=True)
    print(before ,"->",len(biz))

    #分批广播距离匹配
    n=len(stream)
    p_lon = stream['lon'].to_numpy()
    p_lat = stream['lat'].to_numpy()
    biz_lon = biz['lon'].to_numpy()
    biz_lat = biz['lat'].to_numpy()
    matched = np.full(n , -1, dtype=int)

    for s in range(0, n, BATCH_SIZE):
        e = min(s + BATCH_SIZE, n)
        # unit='m'：距离单位米！
        d = Harversine(p_lon[s:e,None], p_lat[s:e,None], biz_lon[None,:], biz_lat[None,:], unit='m')
        nn  = d.argmin(axis=1)
        nd = d[np.arange(e-s), nn]
        hit = nd < HEATMAP_MATCH_THRESHOLD
        matched[s + np.where(hit)[0]] = nn[hit]

    # ========== 回填商圈名称到stream ==========
    stream['biz_idx'] = matched
    stream['biz_name'] = None
    valid_mask = stream['biz_idx'] != -1
    stream.loc[valid_mask, 'biz_name'] = biz.loc[stream.loc[valid_mask, 'biz_idx'], 'biz_name'].values

    # 计算当日分钟序号：0~1439
    stream['min_of_day'] = stream['time_dt'].dt.hour * 60 + stream['time_dt'].dt.minute

    # 分组：按当日分钟、商圈名称统计点数
    panel = stream.groupby(['min_of_day','biz_name']).size().unstack(fill_value=0)
    full_minutes = np.arange(0,1440)
    panel = panel.reindex(full_minutes , fill_value=0)

    # 10分钟滚动求和滑窗
    roll = panel.rolling(WINDOW_MINUTES, min_periods=1).sum()
    result = roll.stack().reset_index()
    result.columns = ['minute','biz_name','count']
    # 把 minute（全天0~1439分钟）转回小时，方便后面可视化
    result['hour'] = result['minute'] // 60
    result = result[result['count']>0]

    #导出结果，供给模块6可视化plt_heat绘图
    save_result(result, RESULT_FILES['heatmap'])

if __name__ == '__main__':
    heatmap_analysis()
