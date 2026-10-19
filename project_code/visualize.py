"""模块6：结果可视化（PPT 1.2.3 数据流第 6 环，课时56 六张业务图）。

一次读四张结果表，生成六张图，每张图回答一个问题：

| 图 | 文件 | 回答的问题 |
| --- | --- | --- |
| 1 出行/驻留占比饼图 | fig_stage3_pie.png | 一天里移动点和停留点占比 |
| 2 24 小时出行/驻留双折线 | fig_hour_line.png | 出行/驻留随时间如何变化 |
| 3 出行目的柱状图 | fig_purpose_bar.png | 停留都在干什么 |
| 4 出行方式柱状图 | fig_mode_bar.png | 出行都怎么去 |
| 5 商圈×24h 热力矩阵 | fig_heatmap.png | 哪里、什么时间最拥挤 |
| 6 Top5 用户 3D 时空轨迹 | fig_3d_traj.png | 个体一天的时空轨迹长什么样 |

输入：result/ 下的各模块结果表（均带表头）——
stage3_label.csv（模块2）、purpose_result.csv（模块3）、mode_result.csv（模块4）、
heatmap_result.csv（模块5）。未产出的表打印警告并跳过对应图；单张图失败只警告，
不影响其他图（课时56 第七节）。
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from loguru import logger

# 把项目根目录加入模块搜索路径，保证不管从哪个目录运行都能 import project_code
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from project_code.config import RESULT_DIR, RESULT_FILES  # noqa: E402
from project_code.utils import (  # noqa: E402
    _read_csv_any_encoding,
    save_fig,
    setup_style,
)

# 图3/图4 的固定类别顺序（课时56：缺的类别补 0，柱子不错位，颜色与类别绑定）
PURPOSE_ORDER = ["居住", "购物", "旅游", "其他"]
PURPOSE_COLORS = ["#1f77b4", "#ff7f0e", "#9467bd", "#7f7f7f"]  # 居住蓝/购物橙/旅游紫/其他灰
MODE_ORDER = ["地铁", "公交", "小汽车", "其他"]
MODE_COLORS = ["#d62728", "#1f77b4", "#ff7f0e", "#7f7f7f"]      # 地铁红/公交蓝/小汽车橙/其他灰


def plt_pie(label_df: pd.DataFrame):
    """图1：出行/驻留占比饼图。"""
    print("生成图1：出行/驻留占比饼图")
    fig, ax = plt.subplots(figsize=(8, 8))

    stay = int((label_df['label'] == 0).sum())
    travel = int((label_df['label'] == 1).sum())
    ax.pie([stay, travel], labels=['驻留', '出行'], autopct="%1.1f%%",
           colors=["#2ca02c", "#d62728"], startangle=90)
    ax.set_title('出行/驻留占比图', fontsize='12', fontweight='bold')
    plt.tight_layout()
    save_fig(fig, 'fig_stage3_pie.png')
    plt.close(fig)


def plt_plot(label_df: pd.DataFrame):
    """图2：24 小时出行/驻留双折线（课时42 的合理性检查画成图）。"""
    print("生成图2：24 小时出行/驻留折线")
    fig, ax1 = plt.subplots(figsize=(10, 9))
    dt = pd.to_datetime(label_df['time'], format='%Y%m%d%H%M%S')
    tmp = pd.DataFrame({'hour': dt.dt.hour, 'label': label_df['label']}).dropna()
    hours = list(range(24))
    # reindex 补 0：没有点的小时也显示为 0，曲线连续（课时56）
    stay = tmp[tmp.label == 0].groupby('hour').size().reindex(hours, fill_value=0)
    travel = tmp[tmp.label == 1].groupby('hour').size().reindex(hours, fill_value=0)
    ax1.plot(hours, stay, marker='o', color='#2ca02c', label='驻留点')
    ax1.set_xlabel('时间', fontsize='12')
    ax1.set_ylabel('驻留', fontsize='12', color='blue')
    ax1.set_xticks(hours)
    ax1.tick_params(axis='y', labelcolor='blue')

    ax2 = ax1.twinx()
    ax2.plot(hours, travel, marker='s', color='#d62728', label='出行点')
    ax2.set_ylabel('出行', fontsize='12', color='red')
    ax2.set_xticks(hours)
    ax2.tick_params(axis='y', labelcolor='red')

    line1, labels1 = ax1.get_legend_handles_labels()
    line2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(line1 + line2, labels1 + labels2, loc='upper right', fontsize='12')
    ax1.grid(True, axis='y', linestyle='-', alpha=0.5)

    plt.tight_layout()
    save_fig(fig, 'fig_hour_line.png')
    plt.close(fig)


def plt_bar3(purpose_df: pd.DataFrame):
    """图3：出行目的柱状图（固定顺序 + reindex 补 0，柱子不错位）。"""
    print("生成图3：出行目的柱状图")

    purpose_counts = purpose_df['final_purpose'].value_counts().reindex(
        PURPOSE_ORDER, fill_value=0)
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(purpose_counts.index, purpose_counts.values, color=PURPOSE_COLORS,
                  edgecolor="black", linewidth=1.2)
    ax.set_ylabel("驻留段数", fontsize=12)
    ax.set_title("出行目的分布", fontsize=14, fontweight="bold")
    for bar, val in zip(bars, purpose_counts.values):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 5,
                f"{val}\n({val / len(purpose_df) * 100:.1f}%)",
                ha="center", va="bottom", fontsize=11, fontweight="bold")
    ax.set_ylim(0, purpose_counts.max() * 1.2)
    ax.grid(axis="y", alpha=0.3, linestyle="--")
    plt.tight_layout()
    save_fig(fig, 'fig_purpose_bar.png')
    plt.close(fig)


def plt_bar4(mode_df: pd.DataFrame):
    """图4：出行方式柱状图（固定顺序 + reindex 补 0）。"""
    print("生成图4：出行方式柱状图")
    mode_counts = mode_df["final_mode"].value_counts().reindex(
        MODE_ORDER, fill_value=0)
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(mode_counts.index, mode_counts.values, color=MODE_COLORS,
                  edgecolor="black", linewidth=1.2)
    ax.set_ylabel("出行段数", fontsize=12)
    ax.set_title("出行方式分布", fontsize=14, fontweight="bold")
    for bar, val in zip(bars, mode_counts.values):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 1,
                f"{val}\n({val / len(mode_df) * 100:.1f}%)",
                ha="center", va="bottom", fontsize=11, fontweight="bold")
    ax.set_ylim(0, mode_counts.max() * 1.2)
    ax.grid(axis="y", alpha=0.3, linestyle="--")
    plt.tight_layout()
    save_fig(fig, 'fig_mode_bar.png')
    plt.close(fig)


def plt_heat(heatmap_df: pd.DataFrame):
    """图5：Top10 商圈 ×24 小时热力矩阵（课时56 第五节：groupby+unstack 成透视表）。"""
    print("生成图5：商圈热力图")
    # heatmap_result.csv 里 hour 列已由模块5算好；只有老格式（time 列）才需要换算
    if "hour" not in heatmap_df.columns:
        t = pd.to_datetime(heatmap_df["time"])
        heatmap_df = heatmap_df.assign(hour=t.dt.hour)
    heatmap_df = heatmap_df.dropna(subset=["hour"])
    pivot = heatmap_df.groupby(["biz_name", "hour"])["count"].max().unstack(fill_value=0)
    pivot = pivot.reindex(columns=range(24), fill_value=0)
    top = pivot.max(axis=1).sort_values(ascending=False).head(10)
    M = pivot.loc[top.index]

    fig, ax = plt.subplots(figsize=(14, 6))
    im = ax.imshow(M.values, aspect="auto", cmap="YlOrRd", interpolation="nearest")
    ax.set_xticks(range(24))
    ax.set_xticklabels(range(24), fontsize=10)
    ax.set_yticks(range(len(M)))
    ax.set_yticklabels(M.index, fontsize=10)
    ax.set_xlabel("小时", fontsize=12)
    ax.set_ylabel("商圈", fontsize=12)
    ax.set_title("Top10商圈每小时人次热力图", fontsize=14, fontweight="bold")
    fig.colorbar(im, ax=ax, label="10分钟窗口人流峰值")
    plt.tight_layout()
    save_fig(fig, 'fig_heatmap.png')
    plt.close(fig)


def plt_3d_traj(label_df: pd.DataFrame):
    """图6：Top5 用户 3D 时空轨迹（x/y=空间，z=时间，课时56 第六节）。"""
    print("生成图6：用户 3D 时空轨迹")
    label_df = label_df.copy()
    label_df['time_dt'] = pd.to_datetime(label_df['time'], format='%Y%m%d%H%M%S')
    top_users = label_df['imsi'].value_counts().head(5).index.tolist()
    fig = plt.figure(figsize=(14, 10))
    ax = fig.add_subplot(111, projection="3d")
    colors = ["#d62728", "#1f77b4", "#2ca02c", "#ff7f0e", "#9467bd"]
    for i, (user, color) in enumerate(zip(top_users, colors)):
        g = label_df[label_df.imsi == user].sort_values("time_dt")
        z = g["time_dt"].dt.hour + g["time_dt"].dt.minute / 60.0  # z轴=时间（小时）
        ax.plot(g["lon"], g["lat"], z, marker="o", markersize=3, color=color,
                linewidth=1.5, alpha=0.8, label=f"用户{str(user)[-4:]}")

    ax.set_xlabel("经度", fontsize=12, labelpad=10)
    ax.set_ylabel("纬度", fontsize=12, labelpad=10)
    ax.set_zlabel("时间（小时）", fontsize=12, labelpad=10)
    ax.set_title("Top5用户3D移动轨迹", fontsize=14, fontweight="bold")
    ax.legend(loc="upper left", fontsize=10)
    ax.view_init(elev=25, azim=50)
    plt.tight_layout()
    save_fig(fig, 'fig_3d_traj.png')
    plt.close(fig)


def visualize_all():
    """可视化主流程（课时56）：一次读四张结果表，生成六张图。"""
    setup_style()
    print('[模块6] 结果可视化：开始')

    def load_result(name):
        """读 result/ 下带表头的结果表；文件不存在时警告并返回 None（对应图跳过）。"""
        path = RESULT_DIR / RESULT_FILES[name]
        if not path.exists():
            print(f'警告: 未找到 {path}，对应图跳过（先运行对应模块）')
            return None
        return _read_csv_any_encoding(path, dtype={'imsi': str})

    label_df = load_result('stage3')    # 模块2（已完成）
    purpose_df = load_result('purpose')  # 模块3（未产出则跳过图3）
    mode_df = load_result('mode')        # 模块4（未产出则跳过图4）
    heat_df = load_result('heatmap')     # 模块5（未产出则跳过图5）

    plot_tasks = [
        ("图1 出行/驻留占比饼图", plt_pie, label_df),
        ("图2 24 小时出行/驻留折线", plt_plot, label_df),
        ("图3 出行目的柱状图", plt_bar3, purpose_df),
        ("图4 出行方式柱状图", plt_bar4, mode_df),
        ("图5 商圈 ×24 小时热力矩阵", plt_heat, heat_df),
        ("图6 用户 3D 时空轨迹", plt_3d_traj, label_df),
    ]

    # 循环逐个执行绘图；单张图失败只警告、不会崩溃退出（课时56 第七节）
    for name, fn, data in plot_tasks:
        if data is None:
            continue
        try:
            print(f"开始生成：{name}")
            fn(data)
        except Exception as e:
            logger.warning(f"{name} 生成失败: {e}")
    print('[模块6] 结果可视化：完成')


if __name__ == '__main__':
    visualize_all()
