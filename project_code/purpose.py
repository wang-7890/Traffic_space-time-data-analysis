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

from project_code.config import RAW_FILES, RESULT_FILES,RESULT_DIR # noqa: E402
# load_csv 在第4步读 GBK 的 POI 静态数据（自动编码兜底），删了会在运行时 NameError
from project_code.utils import load_csv,save_result,Harversine,_read_csv_any_encoding# noqa: E402


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
    时间规则判定出行目的（粗判，最终目的还要看 POI 匹配结果）
    判定顺序：
      1) 居住：时长 > 4h 且开始/结束时段在夜间
      2) 旅游：9-17 点（窄窗）
      3) 购物：9-21 点（宽窗）
      4) 其他：都不满足时兜底
    注意顺序：旅游窗(9-17) 是购物窗(9-21) 的子集，必须先判窄窗再判宽窗，
    否则 9-17 的段会先被购物吞掉，旅游永远判不到。
    """
    # 夜间时段：0-6 点（凌晨）或 20-23 点（晚上）
    is_night_start = (0 <= start_hour < 6) or (20 <= start_hour <= 23)
    is_night_end = (0 <= end_hour < 6) or (20 <= end_hour <= 23)
    if duration_hours > 4 and (is_night_start or is_night_end):
        return "居住"
    # 先判窄窗（旅游 9-17）再判宽窗（购物 9-21），否则窄窗会被宽窗吞掉
    if start_hour >= 9 and end_hour <= 17:
        return "旅游"
    if start_hour >= 9 and end_hour <= 21:
        return "购物"
    return '其他'  # 兜底：不在任何时间窗内的段归"其他"


def main():
    """出行目的识别主流程：驻留段识别 → 时间规则粗判 → POI 匹配精判 → 融合输出。"""
    print('[模块3] 出行目的识别：待实现')
    # df = load_csv(RAW_FILES['purpose'], header=None)  # GBK 编码 utils 会自动兜底
    # save_result(result_df, RESULT_FILES['purpose'])
    # 1.读取阶段3输出结果
    df_stage3 =_read_csv_any_encoding(
        RESULT_DIR/RESULT_FILES["stage3"],
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

    # 按文件实际字段顺序命名列：经度,纬度,目的,目的地（docstring 第 5-6 行的示例行就是）
    # 曾写错成 [poi_type, poi_name, lon, lat]：中文列被 to_numeric 转成 NaN 后
    # dropna 会把 1273 行全删光、POI 匹配直接失败，所以列序不能想当然
    poi_df.columns = ["lon", "lat", "poi_type", "poi_name"]
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
        dists = Harversine(seg["center_lon"], seg["center_lat"], poi_lons, poi_lats, unit="m")
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

    # 最终目的融合：POI 优先 + 时间规则兜底
    # 第一步先用时间规则结果打底，第二步把"匹配成功"的段用最近 POI 的类型覆盖。
    # POI 是真实目的标注（居住/购物/旅游），比时间窗推断更权威；
    # 没匹配上的段保留时间规则结果（"其他"只可能出现在这里）
    segments["final_purpose"] = segments["purpose_by_time"]
    matched = segments["match_success"]
    segments.loc[matched, "final_purpose"] = segments.loc[matched, "nearest_poi_type"]
    print("\n最终出行目的分布：")
    print(segments["final_purpose"].value_counts().to_string())

    # 保存结果，使用config的purpose键
    save_result(segments, RESULT_FILES["purpose"])
    print(f"\n出行目的识别全部完成，输出结果。")

if __name__ == '__main__':
    main()





