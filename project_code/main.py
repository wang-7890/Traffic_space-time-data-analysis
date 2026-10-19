"""主入口：一键跑通全流程（课时57：顺序执行 + 单模块容错 + 结果核对）。

按 PPT 1.2.3 数据流顺序串联 8 个模块；单模块失败打印完整 traceback 但继续后续，
跑完自动核对 7 张结果 CSV + 6 张图的产出情况。

用法（在项目根目录运行）：
    python project_code/main.py
"""
import os
import sys
import traceback
from pathlib import Path

# 把项目根目录加入模块搜索路径，保证不管从哪个目录运行都能 import project_code
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from project_code import (  # noqa: E402
    data_clean,
    heatmap,
    mode,
    purpose,
    tr_stage1,
    tr_stage2,
    tr_stage3,
    visualize,
)
from project_code.config import (  # noqa: E402
    FIGURES_DIR,
    PROCESSED_DIR,
    RESULT_DIR,
    RESULT_FILES,
)
from project_code.utils import Timer, log  # noqa: E402

# 8 个模块：名称 + 入口函数，按数据流顺序（课时57 第二节）
MODULES = [
    ("① 数据清洗", data_clean.main),
    ("②-1 阶段1 速度粗筛", tr_stage1.main),
    ("②-2 阶段2 KMeans聚类", tr_stage2.main),
    ("②-3 阶段3 规则精判", tr_stage3.main),
    ("③ 出行目的识别", purpose.main),
    ("④ 出行方式识别", mode.main),
    ("⑤ 实时热力分析", heatmap.heatmap_analysis),
    ("⑥ 可视化", visualize.visualize_all),
]

# 结果核对清单：7 CSV + 6 PNG（课时57 第四节）
RESULT_CSVS = [
    ("① 清洗数据", RESULT_DIR / RESULT_FILES['cleaned']),
    ("②-1 阶段1出行点", PROCESSED_DIR / 'stage1_dt.csv'),
    ("②-2 阶段2聚类", PROCESSED_DIR / 'stage2_cluster.csv'),
    ("②-3 阶段3标签", RESULT_DIR / RESULT_FILES['stage3']),
    ("③ 目的结果", RESULT_DIR / RESULT_FILES['purpose']),
    ("④ 方式结果", RESULT_DIR / RESULT_FILES['mode']),
    ("⑤ 热力结果", RESULT_DIR / RESULT_FILES['heatmap']),
]
RESULT_FIGS = [
    ("图1 出行/驻留占比饼图", "fig_stage3_pie.png"),
    ("图2 24小时出行/驻留折线", "fig_hour_line.png"),
    ("图3 出行目的柱状图", "fig_purpose_bar.png"),
    ("图4 出行方式柱状图", "fig_mode_bar.png"),
    ("图5 商圈×24h热力矩阵", "fig_heatmap.png"),
    ("图6 Top5用户3D时空轨迹", "fig_3d_traj.png"),
]


def run_modules():
    """顺序执行 + 单模块容错：一个模块报错只记录、继续后续。"""
    for name, fn in MODULES:
        print(f'===== {name} =====')
        try:
            with Timer(name):
                fn()
        except Exception as e:
            log(f'模块【{name}】执行失败: {e}', level='ERROR')
            traceback.print_exc()
            log('继续执行后续模块……', level='WARN')


def check_results():
    """结果核对：7 CSV + 6 PNG 是否存在、大小多少。"""
    print('\n===== 结果核对 =====')
    all_ok = True
    for name, path in RESULT_CSVS:
        ok = os.path.isfile(path)
        size = f'{os.path.getsize(path) / 1024:.1f} KB' if ok else '-'
        all_ok &= ok
        print(f"[{'OK' if ok else '缺失'}] {name}: {os.path.basename(path)} ({size})")
    for name, fname in RESULT_FIGS:
        ok = os.path.isfile(FIGURES_DIR / fname)
        all_ok &= ok
        print(f"[{'OK' if ok else '缺失'}] {name}: {fname}")
    return all_ok


def main():
    with Timer('全流程'):
        run_modules()
    if check_results():
        print('\n===== 全部完成，7 CSV + 6 PNG 齐全 =====')
    else:
        print('\n===== 全流程结束（存在缺失产物，见上方核对清单） =====')


if __name__ == '__main__':
    main()