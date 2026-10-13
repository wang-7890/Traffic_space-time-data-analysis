# Traffic space-time data analysis

基于 pandas、matplotlib、numpy 的交通时空数据分析项目（4 人协作）。

## ⚠️ 数据准备

原始数据**不上传 GitHub**，克隆代码后需要手动获取：

1. 从群文件下载数据包
2. 解压后，把里面所有 `.csv` 文件放到**项目根目录下、名为 `datas` 的文件夹**中（没有就新建一个，必须建在根目录，不是任何子目录里）
3. 放置后目录结构**必须**是：

   ```
   Traffic_space-time-data-analysis/
   ├── datas/
   │   ├── 原始数据.csv
   │   ├── 出行方式静态数据.csv
   │   ├── 出行目的静态数据.csv
   │   ├── 商业区数据.csv
   │   ├── 基站经纬度数据.csv
   │   ├── 实时流数据.csv
   │   └── hive模块静态数据.csv
   ├── README.md
   └── ...
   ```

4. 常见错误自查：

   - ❌ 数据还留在 `下载/` 文件夹，没有挪进项目里
   - ❌ 解压时多套了一层文件夹：`datas/数据包/datas/原始数据.csv`（要的是 `datas/原始数据.csv`）
   - ❌ 文件名被改：群文件重复下载会变成 `原始数据 (1).csv`，请改回原名

5. 验证：在项目根目录运行 `python src/check_data.py`，输出 `[OK] 数据完整` 即成功

> 为什么数据不进 git？CSV 太大（GitHub 单文件上限 100MB），且数据不需要版本管理。`datas/` 已在 `.gitignore` 中忽略——PyCharm 里该文件夹显示**黄色**是正常现象，不是错误。

## 环境配置

1. Python 3.10+
2. 安装依赖：

   ```bash
   pip install -r requirements.txt
   ```

## 项目结构（约定）

```
Traffic_space-time-data-analysis/
├── datas/              # 原始数据（不入库，见上方说明）
├── src/                # 公共代码：数据读取、清洗、绘图配置
├── analysis/           # 按分析主题分工，每人一个模块
│   ├── ...
│   └── ...
├── output/             # 生成的图表、结果
└── README.md
```

- 公共函数（读 CSV、处理中文编码、matplotlib 中文字体等）统一写在 `src/`，所有人 import
- 每人只在自己 `analysis/taskN_xxx/` 目录下写代码，避免冲突
- 图表统一输出到 `output/`

## 协作分工

| 成员 | 负责模块 | 主要数据 |
| ---- | -------- | -------- |
| 成员 A | 出行方式分析 | 出行方式静态数据.csv |
| 成员 B | 出行目的分析 | 出行目的静态数据.csv |
| 成员 C | 商业区/基站空间分析 | 商业区数据.csv、基站经纬度数据.csv |
| 成员 D | 总体时空流量分析 | 原始数据.csv、实时流数据.csv、hive模块静态数据.csv |