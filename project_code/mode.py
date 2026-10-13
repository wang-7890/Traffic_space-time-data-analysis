"""模块4：出行方式识别（PPT 1.2.3 数据流第 3 环）。

任务：判定每次出行采用的方式 —— 地铁 / 公交 / 小汽车 等。
输入：result/stage3_label.csv（模块2 的标签结果）
      data/raw/出行方式静态数据.csv（968 行，GBK 编码，无表头）
输出：result/mode_result.csv
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from project_code.config import RAW_FILES, RESULT_FILES  # noqa: E402
from project_code.utils import load_csv, save_result  # noqa: E402


def main():
    """出行方式识别主流程（骨架，待实现）。"""
    print('[模块4] 出行方式识别：待实现')
    # df = load_csv(RAW_FILES['mode'], header=None)
    # save_result(result_df, RESULT_FILES['mode'])


if __name__ == '__main__':
    main()
