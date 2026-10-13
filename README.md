# 交通时空大数据分析系统

基于 **Python + NumPy + Pandas + Matplotlib** 的交通时空大数据分析项目（课程 14 天版）。
手机信令数据 = 谁 + 何时 + 在哪（基站），是人的移动轨迹代理数据。


## 项目结构
### 所有人写之前先看这个项目结构，先把每一个模块的功能看清楚
```
data-analysis-project/
├── data/                    # 数据目录（不入库，太大）
│   ├── raw/                 # 原始数据
│   └── processed/           # 清洗后的中间数据
├── project_code/            # 代码目录（6 大模块）
│   ├── config.py            # 配置文件（路径、阈值、参数）
│   ├── utils.py             # 工具函数（读 CSV、存结果、中文字体等）
│   ├── check_data.py        # 数据完整性检查
│   ├── data_clean.py        # ① 数据清洗模块（9 条规则）
│   ├── tr_stage1.py         # ② 出行驻留识别 - 阶段1 预处理
│   ├── tr_stage2.py         # ② 出行驻留识别 - 阶段2 聚类（手写 k-means）
│   ├── tr_stage3.py         # ② 出行驻留识别 - 阶段3 业务判定
│   ├── purpose.py           # ③ 出行目的识别
│   ├── mode.py              # ④ 出行方式识别
│   ├── heatmap.py           # ⑤ 实时商圈热力
│   ├── visualize.py         # ⑥ 可视化（6 张业务图 + Dashboard）
│   └── main.py              # 主入口（一键跑通全流程）
├── result/                  # 结果目录
│   ├── cleaned_data.csv     # ① 清洗结果
│   ├── stage3_label.csv     # ② 标签结果
│   ├── purpose_result.csv   # ③ 目的结果
│   ├── mode_result.csv      # ④ 方式结果
│   ├── heatmap_result.csv   # ⑤ 热力结果
│   └── figures/             # ⑥ 图表输出
├── notebooks/               # Jupyter 笔记本（数据探查、算法调试）
├── requirements.txt         # 依赖清单
└── README.md                # 项目说明
```

## 业务目标：6 大模块（PPT 1.2.3）

```
原始信令数据
    │
    ▼
┌─────────────┐
│ ① 数据清洗    │  9 条规则，把脏数据变成标准表
└──────┬──────┘
       ▼
┌─────────────┐
│ ② 出行&驻留识别 │  三阶段：预处理 → 聚类 → 业务判定
└──────┬──────┘
       ├──────────────┐
       ▼              ▼
┌──────────┐   ┌──────────┐
│ ③ 出行目的  │   │ ④ 出行方式  │
│ 居住/购物/旅游│   │ 地铁/公交/小汽车│
└──────────┘   └──────────┘
       │
       ▼
┌─────────────┐
│ ⑤ 实时商圈热力  │  滑窗统计各商圈过去 10 分钟人次
└──────┬──────┘
       ▼
┌─────────────┐
│ ⑥ 结果可视化   │  6 张业务图 + Dashboard 大屏
└─────────────┘
```

技术约定：**不用 sklearn**（k-means 手写）、**不用 geopandas**（经纬度直接用 Haversine 公式）。

## ⚠️ 数据准备

原始数据**不上传 Git**（太大，`data/` 已在 `.gitignore` 中忽略），克隆代码后需要手动获取：

1. 从群里下载数据包
2. 解压后，把里面所有 `.csv` 文件放到 **`data/raw/`** 文件夹中
3. 放置后目录结构**必须**是：

   ```
   data-analysis-project/
   ├── data/
   │   └── raw/
   │       ├── 原始数据.csv          # 约 53 万行，UTF-8，无表头，10 列
   │       ├── 基站经纬度数据.csv     # 关联键 laci = lac_id-cell_id
   │       ├── 商业区数据.csv         # 104 行，实时热力用
   │       ├── 出行目的静态数据.csv   # 1,273 行，GBK 编码
   │       ├── 出行方式静态数据.csv   # 968 行，GBK 编码
   │       ├── 实时流数据.csv         # 256,212 行，滑窗统计用
   │       ├── hive模块静态数据.csv   # 参考用，可不使用
   │       └── 特征值解释.txt
   ├── README.md
   └── ...
   ```

4. 常见错误自查：

   - ❌ 数据还留在 `下载/` 文件夹，没有挪进项目里
   - ❌ 解压时多套了一层文件夹：`data/raw/数据包/原始数据.csv`（要的是 `data/raw/原始数据.csv`）
   - ❌ 文件名被改：群文件重复下载会变成 `原始数据 (1).csv`，请改回原名

5. 验证：在项目根目录运行 `python project_code/check_data.py`，输出 `[OK] 数据完整` 即成功

> 读数据时注意：`lac_id`、`cell_id`、`imsi` 必须按**字符串**读取（`dtype=str`），否则 pandas 推断成数值会丢精度/前导零，和基站表拼 `laci` 时对不上，匹配率变 0。出行目的/出行方式静态数据是 **GBK 编码**，`project_code/utils.py` 的 `load_csv` 会自动兜底。

## 环境配置

1. Python 3.10+
2. 安装依赖：

   ```bash
   pip install -r requirements.txt
   ```
   ```bash
   #如果你使用的是uv包管理器，输入
   uv sync
   ```



## 运行方式

在**项目根目录**下运行（导入用绝对导入 `from project_code.xxx import ...`）：

```bash
python project_code/check_data.py   # 1. 检查数据是否齐备
python project_code/main.py         # 2. 一键跑通 6 大模块全流程
```

也可以单独运行某个模块：`python project_code/data_clean.py`（各模块脚本自带路径引导，任意目录下运行均可）。

## 开发约定

- 数据/代码/结果分离：数据放 `data/`，代码放 `project_code/`，结果放 `result/`
- 路径、阈值等参数集中在 `project_code/config.py`，不要写死在模块里
- 公共函数（读 CSV、编码兜底、存结果、matplotlib 中文字体）统一写在 `project_code/utils.py`
