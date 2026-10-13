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


# ---------- 清洗主流程 ----------

def main():
    """清洗主流程（骨架，9 条规则待实现）。"""
    print('[模块1] 数据清洗：待实现（9 条规则）')
    # 示例：先小样本试读，确认列结构
    # df = load_csv(RAW_FILES['signal'], header=None, nrows=1000, dtype=str)
    # quick_info(df)
    # save_result(df, RESULT_FILES['cleaned'])


if __name__ == '__main__':
    main()
