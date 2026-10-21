"""模块1：数据清洗（PPT 1.2.3 数据流第 1 环，对应 Day4 课时 23~30 讲义）。

按 9 条规则把脏数据变成标准表（六列）：
    1. 字段抽取：10 列只读前 4 列（time / imsi / lac_id / cell_id）
    2. 去脏 imsi：删除含 #、*、空格、空白符的 imsi
    3. 去空：删除 lac_id / cell_id 缺失或空串的行
    4. 毫秒 UTC 时间戳转北京时间（+8h），统一成 YYYYMMDDHHMMSS 字符串
    5. 只保留目标日 20181003
    （教学抽样）按整用户抽样约 2 万行，SAMPLE_ROWS=0 时全量
    6. 拼 laci 左连接基站表补 lon/lat，删除未匹配行
    7. 按 imsi + time 排序
    8. 同一用户同一分钟去重（keep first）
    9. 删除当天点数 < 20 的稀疏用户

输入：data/raw/原始数据.csv（532,828 行，UTF-8，无表头）
      data/raw/基站经纬度数据.csv（无表头，真实列序 lon,lat,laci）
输出：result/cleaned_data.csv（固定 6 列：imsi,time,lac_id,cell_id,lon,lat）
讲义基准（默认抽样）：17,362 行 / 196 个用户

注意：
- 时间戳统一存成 YYYYMMDDHHMMSS 字符串（讲义课时25：方便 startswith 判日期、
  前 12 位做分钟去重键；需要时间运算时用 utils.parse_time 转回 datetime）
- imsi / lac_id / cell_id 必须按字符串读取，防止丢前导零
- 抽样单位是"整用户"而不是"行"（课时28），否则轨迹被抽碎、规则9 几乎删光
"""
import sys
import time
from pathlib import Path

# 把项目根目录加入模块搜索路径，保证不管从哪个目录运行都能 import project_code
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from project_code.config import (
    MIN_POINTS_PER_USER,
    RAW_FILES,
    RAW_TIMEZONE_OFFSET_HOURS,
    RESULT_FILES,
    SAMPLE_ROWS,
    TARGET_DATE,
)
from project_code.utils import load_csv, save_result


def _step(name: str, before: int, after: int) -> None:
    """打印每步行数变化（每步留痕，出问题立刻能定位）。"""
    diff = after - before
    print(f'{name}: {before} -> {after}（{"增加" if diff > 0 else "删除"} {abs(diff)} 行）')


def sample_by_user(df: pd.DataFrame) -> pd.DataFrame:
    """整用户抽样：以"用户"为单位抽样，选中就保留完整轨迹。

    规则：
    - 在当天点数 >= MIN_POINTS_PER_USER 的合格用户里随机打乱（random_state 固定可复现）
    - 逐个整用户纳入，累计点数达到 SAMPLE_ROWS 即停；装不下的跳过继续找
    """
    user_cnt = df.groupby('imsi').size()
    eligible = user_cnt[user_cnt >= MIN_POINTS_PER_USER]
    if SAMPLE_ROWS <= 0 or eligible.sum() <= SAMPLE_ROWS:
        print(f'整用户抽样: 跳过（SAMPLE_ROWS={SAMPLE_ROWS}，保留全量 {len(df)} 行）')
        return df
    shuffled = eligible.sample(frac=1.0, random_state=42)  # 打乱用户顺序，保证代表性
    kept, total = [], 0
    for imsi, cnt in shuffled.items():
        if total + cnt > SAMPLE_ROWS and kept:
            continue                 # 当前用户装不下就跳过，继续找更轻的
        kept.append(imsi)
        total += cnt
        if total >= SAMPLE_ROWS:
            break
    result = df[df['imsi'].isin(kept)]
    print(f'整用户抽样: 选中 {len(kept)} 个用户、{len(result)} 行')
    return result


def main():
    """清洗主流程（9 条规则）。"""
    t0 = time.perf_counter()
    print('[模块1] 数据清洗：开始')

    # 规则1 字段抽取：只读前 4 列，按字符串读入并手动命名（防止丢前导零）
    df = load_csv(
        RAW_FILES['signal'],
        header=None,
        usecols=[0, 1, 2, 3],
        names=['time', 'imsi', 'lac_id', 'cell_id'],
        dtype=str,
    )
    print(f'规则1 字段抽取: {len(df)} 行')

    # 规则2 去脏 imsi：删除含 #、*、空格、空白符的行
    n = len(df)
    df = df[~df['imsi'].str.contains(r'[#* ^\s]', na=False, regex=True)]
    _step('规则2 去脏imsi', n, len(df))

    # 规则3 去空：lac_id / cell_id 缺失或空串的行删除（没有基站编号无法定位）
    n = len(df)
    df = df.dropna(subset=['lac_id', 'cell_id'])
    df = df[(df['lac_id'].str.strip() != '') & (df['cell_id'].str.strip() != '')]
    _step('规则3 去空lac/cell', n, len(df))

    # 规则4 毫秒 UTC 时间戳转北京时间（13 位毫秒：>= 10^12）
    num = pd.to_numeric(df['time'], errors='coerce')
    if num.notna().all() and (num.abs() >= 10**12).all():
        dt = (pd.to_datetime(num.astype('int64'), unit='ms', utc=True)
              + pd.Timedelta(hours=RAW_TIMEZONE_OFFSET_HOURS))
        df['time'] = dt.dt.tz_convert(None).dt.strftime('%Y%m%d%H%M%S')
    else:
        df['time'] = pd.to_datetime(df['time'], errors='coerce').dt.strftime('%Y%m%d%H%M%S')
    print(f'规则4 时间转换（UTC+{RAW_TIMEZONE_OFFSET_HOURS}h）示例: {df["time"].iloc[0]}')

    # 规则5 目标日过滤：只保留 2018-10-03
    n = len(df)
    df = df[df['time'].str.startswith(TARGET_DATE)]
    _step(f'规则5 目标日 {TARGET_DATE}', n, len(df))

    # 教学抽样（非 9 条规则）：按整用户抽样，控制手写 k-means 的耗时
    df = sample_by_user(df)

    # 规则6 基站表左关联补经纬度：拼 laci = lac_id-cell_id，删除未匹配行
    station = load_csv(RAW_FILES['station'], header=None, names=['lon', 'lat', 'laci'], dtype=str)
    station['lon'] = pd.to_numeric(station['lon'], errors='coerce')
    station['lat'] = pd.to_numeric(station['lat'], errors='coerce')
    station = station.dropna(subset=['lon', 'lat', 'laci']).drop_duplicates('laci')
    df['laci'] = df['lac_id'].astype(str) + '-' + df['cell_id'].astype(str)
    n = len(df)
    df = df.merge(station[['laci', 'lon', 'lat']], on='laci', how='left')
    df = df.dropna(subset=['lon', 'lat'])   # 没有坐标的点无法做空间分析，直接删
    _step('规则6 基站关联', n, len(df))

    # 规则7 排序：先按用户，再按时间（阶段1 shift(1) 找"上一条"的前提）
    df = df.sort_values(['imsi', 'time']).reset_index(drop=True)
    print('规则7 排序: 按 imsi + time 排序完成')

    # 规则8 分钟去重：同一 imsi 同一分钟只留第一条（抑制重复记录 / 除零）
    n = len(df)
    df['_minute'] = df['time'].str[:12]   # 201810031230，精确到分钟
    df = df.drop_duplicates(subset=['imsi', '_minute'], keep='first')
    df = df.drop(columns='_minute').reset_index(drop=True)
    _step('规则8 分钟去重', n, len(df))

    # 规则9 稀疏用户过滤：当天点数 < 20 的用户轨迹不可靠，整用户删除
    n = len(df)
    counts = df.groupby('imsi').size()
    df = df[df['imsi'].isin(counts[counts >= MIN_POINTS_PER_USER].index)].reset_index(drop=True)
    _step('规则9 稀疏用户过滤', n, len(df))

    # 输出固定 6 列标准表（列顺序固定，下游模块依赖它）
    df = df[['imsi', 'time', 'lac_id', 'cell_id', 'lon', 'lat']]
    save_result(df, RESULT_FILES['cleaned'])
    print(f'[模块1] 数据清洗：完成（{len(df)} 行 / {df["imsi"].nunique()} 用户，'
          f'耗时 {time.perf_counter() - t0:.2f} 秒）')
    return df


if __name__ == '__main__':
    main()