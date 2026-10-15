import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from project_code.config import RAW_FILES, RESULT_FILES  # noqa: E402
from project_code.utils import load_csv, save_result  # noqa: E402

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from haversine import haversine

# 滑窗大小（分钟）：统计"过去 10 分钟"的人次
WINDOW_MINUTES = 10
TARGET_DATE = 20181003
BATCH_SIZE = 10000
HEATMAP_MATCH_THRESHOLD = 1000

def main():
    """实时热力主流程（骨架，滑窗统计待实现）。"""
    print(f'[模块5] 实时商圈热力：待实现（{WINDOW_MINUTES} 分钟滑窗）')
    #读取实时流数据
    stream = load_csv(RAW_FILES['realtime'], header=None,names=['time','imsi','lon','lat'],dtype=str)

    before = len(stream)
    stream = stream.copy()
    stream['lon'] = pd.to_numeric(stream['lon'], errors='coerce')
    stream['lat'] = pd.to_numeric(stream['lat'], errors='coerce')
    stream = stream.dropna(subset=['lon', 'lat'])
    stream = stream[stream['time'].astype(str).str.startswith(TARGET_DATE)]
    stream['time_dt'] = pd.to_datetime(stream['time'], format="%Y%m%d%H%M%S", errors='coerce')
    stream = stream.dropna(subset=['time_dt']).reset_index(drop=True)
    print(before ,"->",len(stream))
    #读取商圈数据
    biz = load_csv(RAW_FILES['biz'], header=None,names=['lon','lat','biz_name'],dtype=str)

    before = len(biz)
    biz = biz.copy()
    biz['lon'] = pd.to_numeric(biz['lon'], errors='coerce')
    biz['lat'] = pd.to_numeric(biz['lat'], errors='coerce')
    biz = biz.dropna(subset=['lon', 'lat']).reset_index(drop=True)
    print(before ,"->",len(biz))

    #分批广播匹配
    n=len(stream)
    p_lon = stream['lon'].to_numpy()
    p_lat = stream['lat'].to_numpy()
    biz_lon = biz['lon'].to_numpy()
    biz_lat = biz['lat'].to_numpy()
    matched = np.full(n , -1, dtype=int)

    for s in range(0, n, BATCH_SIZE):
        e = min(s + BATCH_SIZE, n)
        d = haversine(p_lon[s:e,None],p_lat[s:e,None],biz_lon[None,:],biz_lat[None,:])
        nn  = d.argmin(axis=1)
        nd = d[np.arange(e-s),nn]
        hit = nd < HEATMAP_MATCH_THRESHOLD
        matched[s + np.where(hit)[0]] = nn[hit]

    full_minutes = np.arange(0,1440)
    stream['minute'] = stream['time_dt'].dt.floor('1min')
    panel = stream.groupby(['minute','biz_name']).size().unstack(fill_value=0)
    panel = panel.reindex(full_minutes , fill_value=0)
    roll = panel.rolling(HEATMAP_MATCH_THRESHOLD,min_periods=1).sum()
    result = roll.stack().reset_index()
    result.columns = ['time','biz_name','count']
    result = result[result['count']>0]

    #导出结果
    save_result(result, RESULT_FILES['heatmap'])


if __name__ == '__main__':
    main()
