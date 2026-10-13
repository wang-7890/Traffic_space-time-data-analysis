"""数据完整性检查脚本。

用法（在项目根目录运行）:
    python project_code/check_data.py
"""
import sys
from pathlib import Path

REQUIRED = [
    '原始数据.csv',
    '出行方式静态数据.csv',
    '出行目的静态数据.csv',
    '商业区数据.csv',
    '基站经纬度数据.csv',
    '实时流数据.csv',
    'hive模块静态数据.csv',
]

DATA_DIR = Path(__file__).resolve().parent.parent / 'data' / 'raw'


def main() -> int:
    missing = [f for f in REQUIRED if not (DATA_DIR / f).exists()]
    if missing:
        print('[缺少数据] 以下文件不存在，请按 README「数据准备」章节把数据放到 data/raw/ 文件夹：')
        for f in missing:
            print('  -', f)
        return 1
    print('[OK] 数据完整，可以开始分析')
    return 0


if __name__ == '__main__':
    sys.exit(main())