"""模块5：实时商圈热力（PPT 1.2.3 数据流第 4 环）。

任务：滑窗统计各商圈过去 10 分钟人次。
输入：data/raw/实时流数据.csv（256,212 行，UTF-8，无表头）
      data/raw/商业区数据.csv（104 行，字段：经度、纬度、商圈名，
      如太原街商圈、中街商圈、沈阳站商圈、棋盘山风景区、世博园）
输出：result/heatmap_result.csv
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from project_code.config import RAW_FILES, RESULT_FILES  # noqa: E402
from project_code.utils import load_csv, save_result  # noqa: E402

# 滑窗大小（分钟）：统计"过去 10 分钟"的人次
WINDOW_MINUTES = 10


def main():
    """实时热力主流程（骨架，滑窗统计待实现）。"""
    print(f'[模块5] 实时商圈热力：待实现（{WINDOW_MINUTES} 分钟滑窗）')
    # stream = load_csv(RAW_FILES['realtime'], header=None)
    # biz = load_csv(RAW_FILES['biz'], header=None)
    # save_result(heat_df, RESULT_FILES['heatmap'])


if __name__ == '__main__':
    main()
