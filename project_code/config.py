"""全局配置：路径常量与分析参数集中管理。

所有模块从这里取路径，不要在各自文件里写死相对路径，
这样调整目录结构时只需要改这一个文件。
"""
from pathlib import Path

# 项目根目录（project_code 的上级）。用 __file__ 锚定，不依赖"从哪个目录运行"
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 数据目录（data/ 太大，不入库，见 .gitignore）
DATA_DIR = PROJECT_ROOT / 'data'
RAW_DIR = DATA_DIR / 'raw'              # 原始数据（7 个 CSV + 特征值解释.txt）
PROCESSED_DIR = DATA_DIR / 'processed'  # 清洗后的中间数据

# 结果目录
RESULT_DIR = PROJECT_ROOT / 'result'
FIGURES_DIR = RESULT_DIR / 'figures'    # 图表输出

# 原始数据文件名（data/raw/ 下，字段说明见 特征值解释.txt 和 Day01 课件）
RAW_FILES = {
    'signal': '原始数据.csv',          # 手机信令，约 53 万行，UTF-8，无表头，10 列
    'station': '基站经纬度数据.csv',    # 基站经纬度，关联键 laci = lac_id-cell_id 共49954行
    'biz': '商业区数据.csv',            # 商圈范围，实时热力用 104行
    'purpose': '出行目的静态数据.csv',  # GBK 编码 1273行
    'mode': '出行方式静态数据.csv',     # GBK 编码 986行
    'realtime': '实时流数据.csv',       # 实时流，滑窗统计用 256212行
    'hive': 'hive模块静态数据.csv',     # 原 Hive 模块参考数据，可不使用 225行
}

# 各模块输出到 result/ 的结果文件名（对应 PPT 1.2.3 的 6 大模块）
RESULT_FILES = {
    'cleaned': 'cleaned_data.csv',      # 模块1 数据清洗
    'stage3': 'stage3_label.csv',       # 模块2 出行驻留识别（阶段3 标签）
    'purpose': 'purpose_result.csv',    # 模块3 出行目的
    'mode': 'mode_result.csv',          # 模块4 出行方式
    'heatmap': 'heatmap_result.csv',    # 模块5 实时商圈热力
}

# 中间数据文件名（data/processed/ 下，模块2 各阶段接力用）
PROCESSED_FILES = {
    'trajectory': 'trajectory_points.csv',  # 模块2 阶段1 轨迹点表
}

# ---------- 数据清洗参数（对应 Day4 课时 23~30 讲义） ----------
TARGET_DATE = '20181003'             # 规则5：只保留目标日
MIN_POINTS_PER_USER = 20             # 规则9：当天点数不足的用户删除
SAMPLE_ROWS = 20000                  # 教学抽样：整用户抽样目标行数；0 = 全量（手写 k-means 慢，慎用）
RAW_TIMEZONE_OFFSET_HOURS = 8        # 规则4：毫秒 UTC 时间戳转北京时间的时差

# ---------- 阶段1 速度参数（对应 Day5 讲义：速度粗筛出行点） ----------
SPEED_THRESHOLD = 8                  # 低于该速度视为静止（km/h）
ABNORMAL_SPEED = 200                 # 高于该速度视为基站跳跃假高速，置空（不删行）
