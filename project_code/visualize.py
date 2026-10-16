import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from project_code.utils import save_fig, setup_style  # noqa: E402
from project_code.utils import load_csv, save_result
from project_code.config import RAW_FILES, RESULT_FILES
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from utils import log

plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

def plt_pie(label_df: pd.DataFrame):
    print("生成图一:出行/驻留比饼图")
    fig,ax = plt.subplots(figsize=(8,8))

    stay = int((label_df['label']==0).sum())
    travel = int((label_df['label']==1).sum())
    pe=ax.pie([stay,travel],labels=['驻留','出行'],autopct="%1.1f%%",colors=["#2ca02c","#d62728"],startangle=90)
    ax.set_title('出行/驻留占比图',fontsize='12',fontweight='bold')
    plt.tight_layout()
    save_fig(fig, 'fig_stage3_pie.png')
    plt.close(fig)

def plt_plot(label_df: pd.DataFrame):
    print("24 小时出行/驻留折线")
    fig,ax1 = plt.subplots(figsize=(10,9))
    dt = pd.to_datetime(label_df['time'],format='%Y%m%d%H%M%S')
    tmp = pd.DataFrame({'hour':dt.dt.hour,'label':label_df['label']}).dropna()
    hours = list(range(24))
    stay = tmp[tmp.label==0].groupby('hour').size().reindex(hours,fill_value=0)
    travel = tmp[tmp.label==1].groupby('hour').size().reindex(hours,fill_value=0)
    ax1.plot(hours,stay,marker='o',color='#2ca02c',label='驻留点')
    ax1.set_xlabel('时间',fontsize='12')
    ax1.set_ylabel('驻留',fontsize='12',color='blue')
    ax1.set_xticks(hours)
    ax1.tick_params(axis='y',labelcolor='blue')

    ax2 = ax1.twinx()
    ax2.plot(hours,travel,marker='s',color='#d62728',label='出行点')
    ax2.set_ylabel('出行',fontsize='12',color='red')
    ax2.set_xticks(hours)
    ax2.tick_params(axis='y',labelcolor='red')

    line1,labels1 = ax1.get_legend_handles_labels()
    line2,labels2 = ax2.get_legend_handles_labels()
    ax1.legend(line1+line2,labels1+labels2,loc='upper right',fontsize='12')
    ax1.grid(True,axis='y',linestyle='-',alpha=0.5)

    plt.tight_layout()
    save_fig(fig, 'fig_hour_line.png')
    plt.close(fig)

def plt_bar3(purpose_df: pd.DataFrame):
    print(" 生成图3：出行目的柱状图")

    purpose_counts = purpose_df['final_purpose'].value_counts()
    purpose_order = ["居住", "购物", "旅游", "其他"]
    purpose_counts = purpose_counts.reindex([p for p in purpose_order if p in
                                             purpose_counts.index])
    purpose_colors = ["#1f77b4", "#ff7f0e", "#9467bd", "#7f7f7f"]
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(purpose_counts.index, purpose_counts.values, color=purpose_colors,
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
    print(" 生成图4：出行方式柱状图")
    mode_counts = mode_df["final_mode"].value_counts()
    mode_order = ["地铁", "公交", "小汽车", "其他"]
    mode_counts = mode_counts.reindex([m for m in mode_order if m in
                                       mode_counts.index])
    mode_colors = ["#d62728", "#1f77b4", "#ff7f0e", "#7f7f7f"]
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(mode_counts.index, mode_counts.values, color=mode_colors,
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
    print(" 生成图5：商圈热力图")
    heatmap_df["time_dt"] = pd.to_datetime(heatmap_df["time"])
    biz_total = heatmap_df.groupby("biz_name")
    ["count"].sum().sort_values(ascending=False)
    top10_biz = biz_total.head(10).index.tolist()
    heatmap_data = np.zeros((len(top10_biz), 24))
    for i, biz in enumerate(top10_biz):
        sub = heatmap_df[heatmap_df["biz_name"] == biz]
        for hour in range(24):
            heatmap_data[i, hour] = sub[sub["time_dt"].dt.hour == hour]["count"].sum()
    fig, ax = plt.subplots(figsize=(14, 6))
    im = ax.imshow(heatmap_data, aspect="auto", cmap="YlOrRd", interpolation="nearest")
    ax.set_xticks(range(24))
    ax.set_xticklabels(range(24), fontsize=10)
    ax.set_yticks(range(len(top10_biz)))
    ax.set_yticklabels(top10_biz, fontsize=10)
    ax.set_xlabel("小时", fontsize=12)
    ax.set_ylabel("商圈", fontsize=12)
    ax.set_title("Top10商圈每小时人次热力图", fontsize=14, fontweight="bold")
    plt.colorbar(im, ax=ax, label="总人次")
    plt.tight_layout()
    save_fig(fig, 'fig_heatmap.png')
    plt.close(fig)


def plt_3d_traj(df: pd.DataFrame):

    top_users =df.groupby("imsi").size().sort_values(ascending=False).head(5).index.tolist()
    fig = plt.figure(figsize=(14, 10))
    ax = fig.add_subplot(111, projection="3d")
    colors = ["#d62728", "#1f77b4", "#2ca02c", "#ff7f0e", "#9467bd"]
    for i, (user, color) in enumerate(zip(top_users, colors)):
        user_df = df[df["imsi"] == user].sort_values("time_dt")
        x = user_df["lon"].values
        y = user_df["lat"].values
        z = user_df["time_dt"].dt.hour.values + user_df["time_dt"].dt.minute.values /60
        ax.plot(x, y, z, color=color, linewidth=1.5, alpha=0.8, label=f"用户{i + 1}")

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
    """可视化主流程（骨架，6 张业务图 + Dashboard 待实现）。"""
    setup_style()
    print('[模块6] 结果可视化：待实现（6 张业务图 + Dashboard）')
    label_df = load_csv(RAW_FILES['stage3'], header=None)
    purpose_df = load_csv(RAW_FILES['purpose'], header=None)
    mode_df = load_csv(RAW_FILES['mode'], header=None)
    heat_df = load_csv(RAW_FILES['heatmap'], header=None)

    plot_tasks = [
        ("图1 出行/驻留占比饼图", plt_pie, label_df),
        ("图2 24 小时出行/驻留折线", plt_plot, label_df),
        ("图3 出行目的柱状图", plt_bar3, purpose_df),
        ("图4 出行方式柱状图", plt_bar4, mode_df),
        ("图5 商圈 ×24 小时热力矩阵", plt_heat, heat_df),
        ("图6 用户 3D 时空轨迹",plt_3d_traj, label_df),
    ]

    # 循环逐个执行绘图
    for name, fn, data in plot_tasks:
        try:
            print(f"开始生成：{name}")
            fn(data)  # 调用绘图函数，传入对应data
        except Exception as e:
            # 捕获异常，只打印警告日志，不会崩溃退出
            log(f"{name} 生成失败: {e}", level="WARN")


if __name__ == '__main__':
    visualize_all()
