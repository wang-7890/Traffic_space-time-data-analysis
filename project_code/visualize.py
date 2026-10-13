"""模块6：结果可视化（PPT 1.2.3 数据流最后一环）。

任务：产出 6 张业务图 + Dashboard 大屏。
输入：result/ 下各模块的结果 CSV（cleaned_data / stage3_label /
      purpose_result / mode_result / heatmap_result）
输出：result/figures/ 下的 6 张业务图 + Dashboard

画图前记得先调用 setup_style()，否则中文显示为方框。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from project_code.utils import save_fig, setup_style  # noqa: E402


def main():
    """可视化主流程（骨架，6 张业务图 + Dashboard 待实现）。"""
    setup_style()
    print('[模块6] 结果可视化：待实现（6 张业务图 + Dashboard）')
    # fig, ax = plt.subplots()
    # save_fig(fig, 'fig_purpose_bar.png')


if __name__ == '__main__':
    main()
