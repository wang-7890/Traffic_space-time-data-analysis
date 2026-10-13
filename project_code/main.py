"""主入口：一键跑通全流程（PPT 1.2.3 的 6 大模块）。

数据流：
    原始信令数据
        → ① 数据清洗（9 条规则）
        → ② 出行 & 驻留识别（阶段1 预处理 → 阶段2 聚类 → 阶段3 业务判定）
        → ③ 出行目的识别  /  ④ 出行方式识别
        → ⑤ 实时商圈热力（10 分钟滑窗）
        → ⑥ 结果可视化（6 张业务图 + Dashboard）

用法（在项目根目录运行）：
    python project_code/main.py
"""
import sys
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

# 按 PPT 1.2.3 的数据流顺序排列
PIPELINE = [
    ('① 数据清洗', data_clean),
    ('② 出行驻留识别 · 阶段1 预处理', tr_stage1),
    ('② 出行驻留识别 · 阶段2 聚类', tr_stage2),
    ('② 出行驻留识别 · 阶段3 业务判定', tr_stage3),
    ('③ 出行目的识别', purpose),
    ('④ 出行方式识别', mode),
    ('⑤ 实时商圈热力', heatmap),
    ('⑥ 结果可视化', visualize),
]


def main():
    for name, module in PIPELINE:
        print(f'===== {name} =====')
        module.main()
    print('===== 全流程结束 =====')


if __name__ == '__main__':
    main()
