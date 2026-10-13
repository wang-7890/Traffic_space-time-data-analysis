"""模块3：出行目的识别（PPT 1.2.3 数据流第 3 环）。

任务：判定每次驻留的目的 —— 居住 / 购物 / 旅游 等。
输入：result/stage3_label.csv（模块2 的标签结果）
      data/raw/出行目的静态数据.csv（1,273 行，GBK 编码，无表头，
      字段：经度、纬度、目的、目的地，如 "123.457628,41.722539,居住,北站广场"）
输出：result/purpose_result.csv
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from project_code.config import RAW_FILES, RESULT_FILES  # noqa: E402
from project_code.utils import load_csv, save_result  # noqa: E402


def main():
    """出行目的识别主流程（骨架，待实现）。"""
    print('[模块3] 出行目的识别：待实现')
    # df = load_csv(RAW_FILES['purpose'], header=None)  # GBK 编码 utils 会自动兜底
    # save_result(result_df, RESULT_FILES['purpose'])


if __name__ == '__main__':
    main()
