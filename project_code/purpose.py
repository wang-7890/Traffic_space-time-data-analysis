"""模块3：出行目的识别（PPT 1.2.3 数据流第 3 环）。

任务：判定每次驻留的目的 —— 居住 / 购物 / 旅游 等。
输入：result/stage3_label.csv（模块2 的标签结果）
      data/raw/出行目的静态数据.csv（1,273 行，GBK 编码，无表头，
      字段：经度、纬度、目的、目的地，如 "123.457628,41.722539,居住,北站广场"）
输出：result/purpose_result.csv
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from project_code.config import RAW_FILES, RESULT_FILES  # noqa: E402
from project_code.utils import load_csv, save_result  # noqa: E402


def haversine(lon1, lat1, lon2, lat2, unit="km"):
    """Haversine球面距离计算"""
    R = 6371.0
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    c = 2 * np.arcsin(np.sqrt(a))
    dist = R * c
    return dist * 1000 if unit == "m" else dist

def judge_purpose_by_time(start_hour, end_hour, duration_hours):
    """
    时间规则判定出行目的
    优先级：居住 > 购物 > 旅游 > 其他
    """
    is_night_start = (0 <= start_hour < 6) or (20 <= start_hour <= 23)
    is_night_end = (0 <= end_hour < 6) or (20 <= end_hour <= 23)
    if duration_hours > 4 and (is_night_start or is_night_end):
        return "居住"
    if start_hour >= 9 and end_hour <= 21:
        return "购物"
    if start_hour >= 9 and end_hour <= 17:
        return "旅游"
    return 'order'


def main():
    """出行目的识别主流程（骨架，待实现）。"""
    print('[模块3] 出行目的识别：待实现')
    # df = load_csv(RAW_FILES['purpose'], header=None)  # GBK 编码 utils 会自动兜底
    # save_result(result_df, RESULT_FILES['purpose'])
    # 1.读取阶段3输出结果
    df_stage3 = pd.read_csv(
        RESULT_FILES["stage3"],
        dtype={"imsi": str, "time": str, "lac_id": str, "cell_id": str}
    )
    df_stage3 = df_stage3.sort_values(["imsi", "time"]).reset_index(drop=True)

    # 2.驻留段识别
    df_stage3["is_stay"] = df_stage3["label"] == 0
    df_stage3["user_change"] = df_stage3["imsi"] != df_stage3["imsi"].shift(1)
    df_stage3["stay_change"] = df_stage3["is_stay"] != df_stage3["is_stay"].shift(1)
    df_stage3["seg_change"] = df_stage3["user_change"] | df_stage3["stay_change"]
    df_stage3["seg_id"] = df_stage3.groupby("imsi")["seg_change"].cumsum()

    stay_df = df_stage3[df_stage3["is_stay"]].copy()
    segments = stay_df.groupby(["imsi", "seg_id"]).agg(
        start_time=("time", "min"),
        end_time=("time", "max"),
        points=("time", "count"),
        center_lon=("lon", "mean"),
        center_lat=("lat", "mean"),
    ).reset_index()

    #开始时间，结束时间，驻留时间
    segments["start_dt"] = pd.to_datetime(segments["start_time"], format="%Y%m%d%H%M%S", errors="coerce")
    segments["end_dt"] = pd.to_datetime(segments["end_time"], format="%Y%m%d%H%M%S", errors="coerce")
    segments["duration_hours"] = (segments["end_dt"] - segments["start_dt"]).dt.total_seconds() / 3600
    segments["start_hour"] = segments["start_dt"].dt.hour
    segments["end_hour"] = segments["end_dt"].dt.hour

    # 3.时间规则判定目的
    segments["purpose_by_time"] = segments.apply(
        lambda r: judge_purpose_by_time(r["start_hour"], r["end_hour"], r["duration_hours"]),
        axis=1
    )
    print("\n时间规则判定结果分布：")
    print(segments["purpose_by_time"].value_counts().to_string())

    # 4.读取POI静态数据，完整字段探查打印
    print("\n==== 读取出行目的POI静态数据 ====")

    poi_df = load_csv(RAW_FILES["purpose"], header=None)

    print(f"POI原始行数：{len(poi_df)}")
    print(f"POI原始列索引：{list(poi_df.columns)}")
    print("POI原始前5行：")
    print(poi_df.head().to_string(index=False))

    poi_df.columns = ["poi_type", "poi_name", "lon", "lat"]
    print(f"\n重命名后列名：{list(poi_df.columns)}")

    print("\nPOI字段数据类型：")
    print(poi_df.dtypes)

    print("\nPOI缺失值统计：")
    print(poi_df.isnull().sum().to_string())

    poi_df["lon"] = pd.to_numeric(poi_df["lon"], errors="coerce")
    poi_df["lat"] = pd.to_numeric(poi_df["lat"], errors="coerce")

    before_clean = len(poi_df)
    poi_df = poi_df.dropna(subset=["lon", "lat"]).drop_duplicates()
    after_clean = len(poi_df)
    print(f"\nPOI清洗：{before_clean} → {after_clean}，删除{before_clean - after_clean}行")

    print("\nPOI目的类型分布（清洗后）：")
    print(poi_df["poi_type"].value_counts().to_string())

    # 5.POI空间匹配，阈值1000米
    MATCH_THRESHOLD = 1000
    segments["nearest_poi_name"] = None
    segments["nearest_poi_type"] = None
    segments["nearest_dist_m"] = np.nan
    segments["match_success"] = False

    poi_lons = poi_df["lon"].values
    poi_lats = poi_df["lat"].values

    for idx, seg in segments.iterrows():
        dists = haversine(seg["center_lon"], seg["center_lat"], poi_lons, poi_lats, unit="m")
        min_idx = np.argmin(dists)
        min_dist = dists[min_idx]
        if min_dist < MATCH_THRESHOLD:
            poi_item = poi_df.iloc[min_idx]
            segments.at[idx, "nearest_poi_name"] = poi_item["poi_name"]
            segments.at[idx, "nearest_poi_type"] = poi_item["poi_type"]
            segments.at[idx, "nearest_dist_m"] = min_dist
            segments.at[idx, "match_success"] = True

    match_cnt = segments["match_success"].sum()
    print(f"\n空间匹配完成：匹配成功 {match_cnt} / {len(segments)}，匹配率 {match_cnt / len(segments) * 100:.1f}%")

    segments["final_purpose"] = segments["purpose_by_time"]
    print("\n最终出行目的分布：")
    print(segments["final_purpose"].value_counts().to_string())

    # 保存结果，使用config的purpose键
    save_result(segments, RESULT_FILES["purpose"])
    print(f"\n出行目的识别全部完成，输出结果。")

if __name__ == '__main__':
    main()





