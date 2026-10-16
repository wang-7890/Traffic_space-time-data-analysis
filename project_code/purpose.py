"""模块3：出行目的识别（PPT 1.2.3 数据流第 3 环）。

任务：在模块2 的驻留标签基础上，切出"驻留段"，结合时间特征与 POI 空间证据，
判定每段目的 —— 居住 / 购物 / 旅游 / 其他（课时43~46）。

流程（课时43 第四节）：
stage3_label → 切驻留段（label=1 打断）→ 段聚合（起止时间/点数/中心/时长/起止小时）
→ POI 最近邻匹配（段中心 → 1km 内最近的小区/商场/景点）→ decide_purpose
（居住=时长+夜间 → 空间证据=购物/旅游 → 时间兜底=先窄后宽）→ purpose_result.csv

输入：result/stage3_label.csv（模块2 阶段3 标签，7 列：
      imsi,time,lac_id,cell_id,lon,lat,label；0=驻留 1=出行）
      data/raw/出行目的静态数据.csv（GBK，1273 行，无表头，真实列序：
      lon,lat,poi_type,poi_name；poi_type 分布：居住900/购物293/旅游80）
输出：result/purpose_result.csv（每驻留段一行，15 列，课时46 第三节）：
      imsi,seg_id,start_time,end_time,points,center_lon,center_lat,
      duration_hours,start_hour,end_hour,final_purpose,
      nearest_poi_name,nearest_poi_type,nearest_dist_m,match_success
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from project_code.config import (  # noqa: E402
    LIVING_DURATION_THRESHOLD,
    PURPOSE_MATCH_THRESHOLD,
    RAW_FILES,
    RESULT_DIR,
    RESULT_FILES,
    SHOPPING_END_HOUR,
    SHOPPING_START_HOUR,
    TOUR_END_HOUR,
    TOUR_START_HOUR,
)
from project_code.utils import (  # noqa: E402
    Harversine,
    _read_csv_any_encoding,
    load_csv,
    parse_time,
    save_result,
)


def is_night(hour):
    """夜间判定：0-6 点或 20-23 点（课时44，居住判据用端点时刻）。"""
    return (0 <= hour <= 6) or (20 <= hour <= 23)


def main():
    """出行目的识别主流程（待实现，课时43~46）。

    步骤：
    1) 读 stage3_label.csv，label=1 打断切驻留段（课时43：变化标记+cumsum，
       注意与阶段1 切段不同——只有出行点才打断，小范围驻留点算同一段）；
    2) 段聚合：start/end_time、points、center_lon/lat、duration_hours、
       start/end_hour（课时44：groupby+agg 命名聚合）；
    3) POI 最近邻匹配：段中心 × 全部 POI 广播 Haversine（米），
       取 argmin 得最近 POI 与距离，< PURPOSE_MATCH_THRESHOLD(1000m) 才算匹配成功（课时46）；
    4) decide_purpose（课时45）：居住（时长>4h 且端点在夜间）→
       空间证据（匹配到购物/旅游 POI 直接采用）→ 时间兜底（先窄后宽：9-17 旅游、9-21 购物），
       注意"购物窗覆盖旅游窗"陷阱：窄条件必须先判；
    5) 整理 15 列输出，save_result(RESULT_FILES['purpose'])。
    """
    print('[模块3] 出行目的识别：待实现')
    # 接力的数据契约（都已就绪，实现课时43~46 时直接使用）：
    # stage3 = _read_csv_any_encoding(RESULT_DIR / RESULT_FILES['stage3'], dtype={'imsi': str})
    # poi = load_csv(RAW_FILES['purpose'], header=None,
    #                names=['lon', 'lat', 'poi_type', 'poi_name'])   # GBK 由 utils 兜底
    # poi 的 lon/lat 需 pd.to_numeric 清洗（课时46 第一节）


if __name__ == '__main__':
    main()
