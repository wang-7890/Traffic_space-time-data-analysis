"""通用数据清洗函数。

大家遇到共用的清洗逻辑（去重、去缺失值、类型转换）优先加到这里，
避免每个任务各自写一份。
"""
import pandas as pd


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