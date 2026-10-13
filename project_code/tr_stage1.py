"""模块2 阶段1：出行 & 驻留识别 —— 预处理（PPT 1.2.3 数据流第 2 环）。

出行 & 驻留识别整体分三阶段：预处理 → 聚类 → 业务判定。
本文件负责阶段1：把清洗后的标准表整理成按用户、按时间排序的轨迹点序列，
并关联基站经纬度（laci = lac_id + '-' + cell_id），为聚类做准备。

输入：result/cleaned_data.csv（模块1 的输出）
      data/raw/基站经纬度数据.csv（空间补全用）
输出：data/processed/ 下的中间结果（轨迹点表）
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from project_code.config import RAW_FILES  # noqa: E402
from project_code.utils import load_csv  # noqa: E402


def main():
    """预处理主流程（骨架，待实现）。"""
    print('[模块2-阶段1] 出行驻留识别-预处理：待实现')
    # station = load_csv(RAW_FILES['station'], header=None, names=['longitude', 'latitude', 'laci'])


if __name__ == '__main__':
    main()
