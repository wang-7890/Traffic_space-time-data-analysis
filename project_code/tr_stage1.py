"""模块2 阶段1：出行 & 驻留识别 —— 预处理。

本文件负责：把清洗后的标准表按用户、按时间排序，并计算每条记录的相邻点速度：
- 用 groupby(imsi).shift(1) 找"同一用户上一条记录"
- 计算相邻点时间差 time_diff（秒）与 Haversine 距离 dist_km（公里）
- 速度 speed = dist / time；异常速度（> ABNORMAL_SPEED，基站跳跃假高速）置空，不删行
- 速度粗筛出行点：speed > SPEED_THRESHOLD 记为 is_travel
- 只保存出行点（is_travel=True）为中间结果，供阶段2 聚类使用

输入：result/cleaned_data.csv（模块1 输出，固定 6 列：imsi,time,lac_id,cell_id,lon,lat）
输出：data/processed/stage1_dt.csv（出行点表：imsi,time,lac_id,cell_id,lon,lat,speed，阶段2 的输入）
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# 把项目根目录加入模块搜索路径，保证不管从哪个目录运行都能 import project_code
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from project_code.config import (  # noqa: E402
    ABNORMAL_SPEED,
    RESULT_DIR,
    RESULT_FILES,
    SPEED_THRESHOLD,
)
from project_code.utils import Harversine, parse_time, save_processed,_read_csv_any_encoding # noqa: E402

def main():
    """
    阶段一读入数据清洗模块输出的标准表cleaned_data.csv（imsi、time、lac_id、cell_id、lon、lat六列，共17362条记录）。首先按imsi，lon，lat
    统计每个位置的出现次数，过滤同一用户同一位置出现次数少于4次的低频漂移点；再按用户分组、按时间排序，用shift计算相邻记录的时间差
    time_diff（秒），用Haversine公式计算相邻点的球面距离dist_km（公里），速度speed＝dist_km/time_diff×3600（km/h）；对速度超过200km/h
    的基站跳跃假高速置空而不删行；最后速度大于8km/h的点标记is_travel=True，作为疑似出行点输出到data/processed/stage1_dt.csv。

    """
    print('[模块2-阶段1] 出行驻留识别-预处理：开始')

    # 读标准表（imsi / lac_id / cell_id 必须按字符串读，防止丢前导零）
    df = _read_csv_any_encoding(
        RESULT_DIR / RESULT_FILES['cleaned'],
        dtype={'imsi': str, 'lac_id': str, 'cell_id': str},
    )
    #去掉低频率点
    df['time_dt'] = parse_time(df['time'])
    loc_cnt = df.groupby(["imsi","lon","lat"]).size().reset_index(name='cnt')
    low_freq = loc_cnt[loc_cnt['cnt']<4][['imsi','lat','lon']]
    low_freq["_is_low"] = 1
    df = df.merge(low_freq,on=["lat","imsi","lon"],how="left")
    df = df[df["_is_low"].isna()].drop(columns="_is_low").reset_index(drop=True)

    prev_imsi = df["imsi"].shift(1)
    prev_lon = df["lon"].shift(1)
    prev_lat = df["lat"].shift(1)

    user_change = (df["imsi"]!=prev_imsi)
    loc_change = (df["lon"]!=prev_lon)|(df["lat"]!=prev_lat)
    seg_change = (user_change | loc_change).astype("int64")
    df["seg_id"] = seg_change.groupby(df['imsi']).cumsum()

    df["time_diff"] = df.groupby("imsi")["time_dt"].diff().dt.total_seconds()
    df["prev_lon"] = df.groupby('imsi')["lon"].shift(1)
    df["prev_lat"] = df.groupby("imsi")["lat"].shift(1)

    dist_km = Harversine(df["prev_lon"],df["prev_lat"],df["lon"],df["lat"],unit='km')
    df["speed"] = (dist_km*3600.0/df["time_diff"]).round(2)
    df.loc[(df["speed"]<0) | (df["speed"]>ABNORMAL_SPEED),"speed"] = np.nan
    df['is_travel'] = df["speed"]>SPEED_THRESHOLD

    travel = df[df["is_travel"]].copy()
    travel = travel[["imsi","time","lac_id","cell_id","lon","lat","speed"]]
    #保留出行点
    save_processed(travel,"stage1_dt.csv")
    return travel
if __name__ == '__main__':
    main()