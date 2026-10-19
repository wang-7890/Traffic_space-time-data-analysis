"""通用工具函数：读数据、存结果、绘图配置。

对应 PPT 4.2.4 里的 utils.py。所有模块共用，避免每个任务各写一份：
- 读 CSV：data/raw/ 里编码不统一（部分 UTF-8、部分 GBK），在这里兜底解决一次
- 存结果：CSV 统一写 result/，图片统一写 result/figures/
- 绘图：解决 matplotlib 默认不显示中文的问题

后续课时还会往这里加算法工具（haversine 距离等）。
"""
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import logging
import time

from project_code.config import FIGURES_DIR, PROCESSED_DIR, RAW_DIR, RESULT_DIR


def _read_csv_any_encoding(path: Path, **kwargs) -> pd.DataFrame:
    """先按 UTF-8 读取，失败再按 GBK 读取。

    GBK 是 Windows 下中文 CSV 的常见编码（出行目的/出行方式静态数据就是），
    不能写死一种编码。
    """
    try:
        return pd.read_csv(path, encoding='utf-8', **kwargs)
    except UnicodeDecodeError:
        return pd.read_csv(path, encoding='gbk', **kwargs)


def load_csv(filename: str, **kwargs) -> pd.DataFrame:
    """读取 data/raw/ 下的 CSV 文件，用于加载原数据

    参数:
        filename: 文件名，建议用 config.RAW_FILES 里的常量，如 RAW_FILES['signal']
        **kwargs: 原样传给 pd.read_csv。data/raw/ 下的 CSV 都没有表头行，
                  请加 header=None，并参考数据说明自行定义列名。

    文件缺失时会抛出带解决提示的 FileNotFoundError。
    """
    path = RAW_DIR / filename
    if not path.exists():
        raise FileNotFoundError(
            f'找不到数据文件: {path}\n'
            '请按 README「数据准备」章节，把数据放到项目 data/raw/ 文件夹。'
        )
    return _read_csv_any_encoding(path, **kwargs)


def save_result(df: pd.DataFrame, name: str) -> Path:
    """把结果 DataFrame 写到 result/ 目录，自动建目录。

    参数:
        name: 文件名，建议用 config.RESULT_FILES 里的常量
    """
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    path = RESULT_DIR / name
    # utf-8-sig：带 BOM，Excel 直接打开中文不乱码
    df.to_csv(path, index=False, encoding='utf-8-sig')
    print(f'结果已保存: {path}')
    return path


def setup_style() -> None:
    """设置全局绘图风格（中文字体）。每个脚本画图前调用一次。"""
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']  # 中文字体
    plt.rcParams['axes.unicode_minus'] = False  # 正常显示负号
    plt.rcParams['figure.dpi'] = 120


def save_fig(fig, name: str) -> Path:
    """
    把图保存到 result/figures/ 目录，自动创建目录。
    :param fig: Figure 画布对象
    :param name:文件名，取config.RESULT_FILES里的常量
    :return: 保存文件的完整Path路径对象
    """
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    path = FIGURES_DIR / name
    fig.savefig(path, bbox_inches='tight')
    print(f'图片已保存: {path}')
    return path


def save_processed(df: pd.DataFrame, name: str) -> Path:
    """把中间结果写到 data/processed/ 目录，自动建目录（各阶段接力用）。

    参数:
        name: 文件名，建议用 config.PROCESSED_FILES 里的常量
    """
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    path = PROCESSED_DIR / name
    df.to_csv(path, index=False, encoding='utf-8-sig')
    print(f'中间结果已保存: {path}')
    return path


def parse_time(s):
    """把清洗后的 YYYYMMDDHHMMSS 时间字符串转回 datetime（讲义课时25 的 parse_time）。"""
    return pd.to_datetime(s, format='%Y%m%d%H%M%S')


def Harversine(lon1,lat1,lon2,lat2,unit="km"):
    R=6371.0
    lon1,lat1,lon2,lat2 =map(np.radians,[lon1,lat1,lon2,lat2])
    dlat = lat2-lat1
    dlon = lon2-lon1
    a = (np.sin(dlat/2.0))**2 + np.cos(lat1)*np.cos(lat2)*(np.sin(dlon/2.0))**2
    c = 2.0*np.arcsin(np.sqrt(a))
    dist = R * c
    return dist *1000.0 if unit == 'm' else dist


# 初始化日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# 自定义log函数
def log(msg, level="INFO"):
    if level.upper() == "WARN":
        logging.warning(msg)
    elif level.upper() == "INFO":
        logging.info(msg)
    elif level.upper() == "ERROR":
        logging.error(msg)


class Timer:
    """计时上下文管理器（课时57：main 一键集成时统计每模块耗时）。"""
    def __init__(self, name: str = ""):
        self.name = name

    def __enter__(self):
        self._start = time.time()
        return self

    def __exit__(self, *exc):
        print(f'[耗时] {self.name}: {time.time() - self._start:.1f} 秒')
