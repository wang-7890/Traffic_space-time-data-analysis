"""模块1：数据清洗（PPT 1.2.3 数据流第 1 环）。

任务：按 9 条规则把脏数据变成标准表。
输入：data/raw/原始数据.csv（约 53 万行，UTF-8，无表头，10 列，
      关键字段 timestamp / imsi / lac_id / cell_id）
输出：result/cleaned_data.csv（清洗后的标准表）

注意：
- lac_id、cell_id、imsi 必须按字符串读取，否则 pandas 推断成数值会丢前导零，
  后面和基站表拼 laci（lac_id-cell_id）时对不上、匹配率变 0。
- 9 条规则的具体实现后续课时逐步补充。

下方保留了几个通用清洗函数（去重、缺失值、类型转换），各模块可复用。
"""
import sys
from pathlib import Path

# 把项目根目录加入模块搜索路径，保证不管从哪个目录运行都能 import project_code
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from project_code.config import RAW_FILES, RESULT_FILES
from project_code.utils import load_csv, save_result


# ---------- 通用清洗函数（各模块可复用） ----------

def drop_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """去除完全重复的行。"""
    return df.drop_duplicates()


def drop_missing(df: pd.DataFrame, threshold: float = 0.5) -> pd.DataFrame:
    """删除缺失值过多的列。

    参数:
        threshold: 缺失比例超过该值的列被删除（0.5 表示缺一半就删）
    """
    return df.dropna(axis=1, thresh=int((1 - threshold) * len(df)))


def to_numeric(df: pd.DataFrame, column, errors: str = 'coerce') -> pd.DataFrame:
    """把某列转成数值，无法转换的值变为 NaN。"""
    df = df.copy()
    df[column] = pd.to_numeric(df[column], errors=errors)
    return df


def to_datetime(df: pd.DataFrame, column, unit=None) -> pd.DataFrame:
    """把某列转成时间类型。

    原始数据.csv 的第一列是毫秒时间戳，可这样用:
        to_datetime(df, 0, unit='ms')
    """
    df = df.copy()
    df[column] = pd.to_datetime(df[column], unit=unit)
    return df


def quick_info(df: pd.DataFrame) -> None:
    """打印 DataFrame 的快速概览：形状、缺失值、列类型。"""
    print(f'形状: {df.shape}')
    print('各列缺失值数量:')
    print(df.isna().sum())
    print('各列类型:')
    print(df.dtypes)

#-----------清洗参数------------
SIGNAL_COLS = ['timestamp','imsi','lac_id','cell_id','phone','timestamp1','tmp0','tmp1','nid','npid']
STATION_COLS = ['longitude','latitude','laci']
TARGET_DATE = '20181003'
MIN_RECORDS = 20


# ---------- 清洗主流程 ----------

def main():
    """清洗主流程（骨架，9 条规则待实现）。"""
    print('[模块1] 数据清洗：开始')

    #规则1 字段抽取： 无表头，按字符串读入并手动命名（防止丢前导零）
    df = load_csv(RAW_FILES['signal'],header=None,dtype=str,names=SIGNAL_COLS)
    print(f"规则1 字段抽取后: {len(df)}行")
    df = drop_duplicates(df)   #去完全重复行

    #规则2 去脏imsi：只保留15~20位纯数字
    imsi = df['imsi'].astype(str).str.strip()
    df = df[imsi.str.match(r'^\d{15,20}$')].copy()
    print(f"规则2 去脏 imsi后: {len(df)}行")

    #规则3 去空间残缺： imsi/lac_id/cell_id 为空或占位符'000'的行删除
    for col in ['imsi','lac_id','cell_id']:
        df[col] = df[col].astype(str).str.strip()
    df = df[(df['imsi'] != '') & (df['lac_id'] != '') & (df['cell_id'] != '')]  #剔除空字符串
    df = df[~df[['imsi','lac_id','cell_id']].isin(['000','nan','None']).any(axis=1)]
    print(f"规则3 去残缺后：{len(df)} 行")

    #规则4 毫秒时间戳转换 ：13位毫秒时间戳
    df['timestamp'] = pd.to_datetime(
        pd.to_numeric(df['timestamp'], errors='coerce'),
        errors='coerce',
        unit='ms'
    ).dt.strftime('%Y%m%d%H%M%S')
    print(f"规则4 毫秒时间戳转换后：{len(df)} 行")

    #规则5 目标日期过滤：只保留2018-10-03
    df = df[df["timestamp"].str.startswith(TARGET_DATE)]
    print(f"规则5 日期过滤后：{len(df)} 行")

    #规则6 基站表左关联补全经纬度：拼接laci = lac_id-cell_id
    df['laci'] = df['lac_id'].str.strip() + '-' + df['cell_id'].str.strip()   #拼接laci
    stations = load_csv(RAW_FILES['station'],header=None,dtype=str,names=STATION_COLS)   #读入基站表
    stations = stations[['laci','longitude','latitude']].drop_duplicates(subset = 'laci')  #按laci去重
    df = df.merge(stations,on='laci',how='left')   #左连接，补经纬度
    df = to_numeric(df,'longitude',errors='coerce')
    df = to_numeric(df,'latitude',errors='coerce')    #经纬度从字符串转成数字
    print(f"规则6 关联后：{len(df)}行，未匹配经纬度 {df['longitude'].isna().sum()} 行")

    #规则7 排序：先按用户，再按时间
    df = df.sort_values(['imsi','timestamp']).reset_index(drop=True)

    #规则8 分钟去重：同一imsi 同一分钟只能留一条。抑制基站乒乓切换
    df['_minute'] = df['timestamp'].str[:12]
    df = df.drop_duplicates(subset=['imsi', '_minute'], keep='first')
    df = df.drop(columns='_minute').reset_index(drop=True)
    print(f'规则8 分钟去重后：{len(df)} 行')

    #规则9 低频用户过滤：单imsi记录数 < 20条的用户删除
    counts = df['imsi'].value_counts()
    df = df[df['imsi'].isin(counts[counts >= MIN_RECORDS].index)]
    print(f'规则9 低频用户过滤后：{len(df)} 行')

    save_result(df, RESULT_FILES['cleaned'])
    print('[模块1] 数据清洗：完成')

    # 示例：先小样本试读，确认列结构
    # df = load_csv(RAW_FILES['signal'], header=None, nrows=1000, dtype=str)
    # quick_info(df)
    # save_result(df, RESULT_FILES['cleaned'])


if __name__ == '__main__':
    main()
