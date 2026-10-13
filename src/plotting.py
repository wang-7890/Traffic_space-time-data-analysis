"""统一绘图配置。

解决两件事:
1. matplotlib 默认不显示中文（图上全是方框）-> 配置中文字体
2. 图表统一保存到 output/ 目录，方便最后汇总
"""
from pathlib import Path

import matplotlib.pyplot as plt

# 输出目录（项目根目录下的 output/），用 __file__ 锚定，不依赖运行目录
OUTPUT_DIR = Path(__file__).resolve().parent.parent / 'output'


def setup_style() -> None:
    """设置全局绘图风格。每个脚本画图前调用一次。"""
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']  # 中文字体
    plt.rcParams['axes.unicode_minus'] = False  # 正常显示负号
    plt.rcParams['figure.dpi'] = 120


def save_fig(fig, name: str) -> Path:
    """把图保存到 output/ 目录，自动创建目录。"""
    OUTPUT_DIR.mkdir(exist_ok=True)
    path = OUTPUT_DIR / name
    fig.savefig(path, bbox_inches='tight')
    print(f'图片已保存: {path}')
    return path