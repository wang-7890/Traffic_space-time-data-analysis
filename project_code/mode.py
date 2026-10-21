"""模块4：出行方式识别

任务：判定每次出行采用的方式 —— 地铁 / 公交 / 小汽车 等。
输入：result/stage3_label.csv（模块2 的标签结果）
      data/raw/出行方式静态数据.csv（968 行，GBK 编码，无表头）
输出：result/mode_result.csv
"""
import sys
from pathlib import Path

import sys
from pathlib import Path
import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from project_code.config import RAW_DIR,RAW_FILES, RESULT_FILES ,RESULT_DIR # noqa: E402
from project_code.utils import load_csv, save_result,_read_csv_any_encoding  # noqa: E402

# 判定参数（课时45/46 阈值）：
MATCH_THRESHOLD = 500       # 站点匹配阈值：出行点到地铁/公交站 500 米内算"命中"
SUBWAY_MIN_POINTS = 2       # 一段出行里命中 ≥2 个地铁站 → 判地铁
BUS_MIN_POINTS = 3          # 命中 ≥3 个公交站 → 判公交（公交站更密、易误命中，阈值比地铁高）
SPEED_OTHER = 12            # 平均速度 < 12 km/h → "其他"（步行等慢速出行）
SPEED_BUS = 20              # 平均速度 12~20 → 公交档；> 20 → 地铁或小汽车档

def haversine(lon1, lat1, lon2, lat2, unit="m"):
    R = 6371.0
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    c = 2 * np.arcsin(np.sqrt(a))
    dist_m = R * c * 1000
    return dist_m if unit == "m" else dist_m / 1000

def judge_mode_by_speed(avg_speed):
    """按平均速度粗判方式（结果存 mode_speed 列，仅作参考）：
    <12 其他（步行等）/ 12~20 公交档 / >20 地铁或小汽车档。
    地铁和小汽车速度接近，单靠速度分不开，要靠后面站点匹配区分。"""
    if avg_speed < SPEED_OTHER:
        return "其他"
    elif avg_speed <= SPEED_BUS:
        return "公交"
    else:
        return "地铁或小汽车"

def final_mode_judge(subway_cnt, bus_cnt, avg_speed):
    """最终方式判定（站点匹配优先，速度兜底）：
    1) 命中 ≥2 个地铁站 → 地铁（地铁站间距大、误命中少，最可信）
    2) 命中 ≥3 个公交站 → 公交
    3) 都没命中但速度快 >20 → 小汽车（不靠站、速度快的机动出行）
    4) 其余 → 其他"""
    if subway_cnt >= SUBWAY_MIN_POINTS:
        return "地铁"
    elif bus_cnt >= BUS_MIN_POINTS:
        return "公交"
    elif avg_speed > SPEED_BUS:
        return "小汽车"
    else:
        return "其他"


def main():
    """
    先拆分每个人的独立出行片段，算出每段出行的平均速度；再看这段轨迹里面有多少个点靠近地铁站 / 公交站；优先用站点匹配判定，速度作为兜底，
    最终识别出行方式
    """
    print('[模块4] 出行方式识别')
    df_stage3 = _read_csv_any_encoding(RESULT_DIR/RESULT_FILES["stage3"])
    df_stage3 = df_stage3.sort_values(["imsi", "time"]).reset_index(drop=True)
    print(f"读取stage3数据：{len(df_stage3)}行")

    # 2.生成出行段seg_id，label==1为出行
    #与驻留目的分析一致，对所有用户进行切片
    df_stage3["is_travel"] = df_stage3["label"] == 1
    df_stage3["user_shift"] = df_stage3["imsi"] != df_stage3["imsi"].shift(1)
    df_stage3["travel_shift"] = df_stage3["is_travel"] != df_stage3["is_travel"].shift(1)
    df_stage3["seg_change"] = df_stage3["user_shift"] | df_stage3["travel_shift"]
    # 根据imsi分组，每组seg_id从1开始，遇到seg_change为True则+1
    df_stage3["seg_id"] = df_stage3.groupby("imsi")["seg_change"].cumsum()
    #只找出行的人
    travel_all = df_stage3[df_stage3["is_travel"]].copy()

    # 聚合每个出行段
    seg_df = travel_all.groupby(["imsi", "seg_id"]).agg(
        start_time=("time", "min"),
        end_time=("time", "max"),
        point_count=("time", "count"),
        lon_start=("lon", "first"),
        lat_start=("lat", "first"),
        lon_end=("lon", "last"),
        lat_end=("lat", "last"),
    ).reset_index()

    # 过滤至少2个点的出行段
    seg_df = seg_df[seg_df["point_count"] >= 2].copy()
    print(f"有效出行段数量：{len(seg_df)}")
    # 3.逐段计算平均速度：相邻轨迹点 距离/时间差 = 点间速度，段内取均值
    speed_list = []
    for _, seg in seg_df.iterrows():
        #按照用户和segid计算每一个出行段的相关数据
        one_seg = travel_all[(travel_all["imsi"] == seg["imsi"]) & (travel_all["seg_id"] == seg["seg_id"])].copy()
        one_seg = one_seg.sort_values("time").reset_index(drop=True)
        one_seg["dt"] = pd.to_datetime(one_seg["time"], format="%Y%m%d%H%M%S", errors="coerce")
        one_seg["dt_diff"] = one_seg["dt"].diff().dt.total_seconds()          # 相邻点时间差（秒）
        one_seg["lon_prev"] = one_seg["lon"].shift(1)                          # 上一个点的坐标
        one_seg["lat_prev"] = one_seg["lat"].shift(1)
        one_seg["dist_m"] = haversine(one_seg["lon_prev"], one_seg["lat_prev"], one_seg["lon"], one_seg["lat"])
        one_seg["speed_kmh"] = one_seg["dist_m"] / 1000 * 3600 / one_seg["dt_diff"]  # 米/秒 × 3.6 = km/h
        #获得有效表，剔除速度不正常的记录
        valid = one_seg[(one_seg["speed_kmh"] > 0) & (one_seg["speed_kmh"] < 200)]   # 剔 0（同点）和假高速
        sp_mean = valid["speed_kmh"].mean() if len(valid) > 0 else np.nan
        speed_list.append(sp_mean)

    seg_df["avg_speed"] = speed_list
    seg_df = seg_df[seg_df["avg_speed"].notna()].copy()
    #根据速度初步判定，后续根据规则详细判定
    seg_df["mode_speed"] = seg_df["avg_speed"].apply(judge_mode_by_speed)

    # 4.读取出行方式静态数据，拼接RAW_DIR完整路径！
    mode_file = RAW_DIR / RAW_FILES["mode"]
    print(f"读取站点文件：{mode_file} , exists={mode_file.exists()}")
    station_df = load_csv(mode_file, header=None)
    station_df.columns = ["lon", "lat",'mode_type','station_name','line_name']  # 文件字段：经度,纬度,方式类型,站点名,线路名

    # 清洗站点
    station_df["lon"] = pd.to_numeric(station_df["lon"], errors="coerce")
    station_df["lat"] = pd.to_numeric(station_df["lat"], errors="coerce")
    station_df = station_df.dropna(subset=["lon", "lat"]).drop_duplicates()

    subway_sta = station_df[station_df["mode_type"].str.contains("地铁", na=False)].copy()
    bus_sta = station_df[station_df["mode_type"].str.contains("公交", na=False)].copy()

    sub_lon_arr = subway_sta["lon"].values
    sub_lat_arr = subway_sta["lat"].values
    bus_lon_arr = bus_sta["lon"].values
    bus_lat_arr = bus_sta["lat"].values

    # 5.每个出行段匹配站点，统计命中点数
    subway_hit = []
    bus_hit = []
    final_mode_list = []

    for _, seg in seg_df.iterrows():
        one_seg = travel_all[(travel_all["imsi"] == seg["imsi"]) & (travel_all["seg_id"] == seg["seg_id"])].copy()
        sub_cnt = 0
        bu_cnt = 0
        # 逐个轨迹点判断是否"压过"地铁站/公交站：500 米内算命中一次
        for _, p in one_seg.iterrows():
            d_sub = haversine(p["lon"], p["lat"], sub_lon_arr, sub_lat_arr)   # 该点到所有地铁站的距离
            if np.any(d_sub < MATCH_THRESHOLD):
                sub_cnt += 1
            d_bus = haversine(p["lon"], p["lat"], bus_lon_arr, bus_lat_arr)   # 该点到所有公交站的距离
            if np.any(d_bus < MATCH_THRESHOLD):
                bu_cnt += 1
        subway_hit.append(sub_cnt)
        bus_hit.append(bu_cnt)
        fm = final_mode_judge(sub_cnt, bu_cnt, seg["avg_speed"])
        final_mode_list.append(fm)

    seg_df["subway_hit_count"] = subway_hit
    seg_df["bus_hit_count"] = bus_hit
    seg_df["final_mode"] = final_mode_list

    print("\n====出行方式统计====")
    print(seg_df["final_mode"].value_counts().to_string())

    # 6.输出结果，调用项目工具 save_result
    out_cols = [
        "imsi", "seg_id", "start_time", "end_time", "point_count",
        "lon_start", "lat_start", "lon_end", "lat_end",
        "avg_speed", "mode_speed", "subway_hit_count", "bus_hit_count", "final_mode"
    ]
    result_df = seg_df[out_cols].copy()
    save_result(result_df, RESULT_FILES["mode"])
    print(f"模块4完成，输出mode_result.csv，共{len(result_df)}条出行段")


if __name__ == '__main__':
    main()
