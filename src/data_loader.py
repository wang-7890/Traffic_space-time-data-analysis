"""统一的数据读取模块。

所有分析脚本都通过这里读取数据，不要各自直接 pd.read_csv，
这样编码、路径问题只需要在这里解决一次。

注意：datas/ 下大部分 CSV 没有表头行，读取时请加 header=None，
并参考数据说明自行定义列名。
"""
from pathlib import Path

import pandas as pd

# 项目根目录（datas 的上级）。用 __file__ 锚定，不依赖"从哪个目录运行"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / 'datas'


def _read_csv_any_encoding(path: Path, **kwargs) -> pd.DataFrame:
    """先按 UTF-8 读取，失败再按 GBK 读取。

    datas/ 里的文件编码不统一（部分 utf-8、部分 gbk），
    gbk 是 Windows 下中文 CSV 的常见编码，不能写死一种。
    """
    try:
        return pd.read_csv(path, encoding='utf-8', **kwargs)
    except UnicodeDecodeError:
        return pd.read_csv(path, encoding='gbk', **kwargs)


def load_csv(filename: str, **kwargs) -> pd.DataFrame:
    """读取 datas/ 下的 CSV 文件。

    参数:
        filename: 文件名，如 '原始数据.csv'
        **kwargs: 原样传给 pd.read_csv，如 header=None、nrows=1000

    文件缺失时会抛出带解决提示的 FileNotFoundError。
    """
    path = DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(
            f'找不到数据文件: {path}\n'
            '请按 README「数据准备」章节，把数据放到项目根目录的 datas/ 文件夹。'
        )
    return _read_csv_any_encoding(path, **kwargs)


def load_all() -> dict[str, pd.DataFrame]:
    """一次读取 datas/ 下全部 CSV，返回 {文件名: DataFrame}。

    原始数据.csv 可能很大，建议先用 load_csv(..., nrows=1000) 试读。
    """
    return {p.name: _read_csv_any_encoding(p) for p in sorted(DATA_DIR.glob('*.csv'))}
