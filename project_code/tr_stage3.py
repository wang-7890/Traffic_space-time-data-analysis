"""模块2 阶段3：出行 & 驻留识别 —— 业务判定（PPT 1.2.3 数据流第 2 环）。

本文件负责阶段3：在聚类结果上按业务规则（驻留时长、时段等）判定
每个簇是"驻留"还是"路过"，给每个用户打出出行/驻留标签。

输入：data/processed/ 下阶段2 的聚类结果
输出：result/stage3_label.csv（出行/驻留标签表）
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from project_code.config import RESULT_FILES  # noqa: E402
from project_code.utils import save_result  # noqa: E402


def main():
    """业务判定主流程（骨架，待实现）。"""
    print('[模块2-阶段3] 出行驻留识别-业务判定：待实现')
    # save_result(labels_df, RESULT_FILES['stage3'])


if __name__ == '__main__':
    main()
