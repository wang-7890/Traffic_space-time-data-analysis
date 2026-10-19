# 交通时空大数据分析系统

基于 **Python + NumPy + Pandas + Matplotlib** 的交通时空大数据分析课程项目。
手机信令数据记录"谁 + 何时 + 在哪（基站）"，是人的移动轨迹的代理数据。
项目按 PPT 1.2.3 的数据流拆成 **6 大模块**：每个模块产出一张结果表接力给下游，
最终输出 6 张业务图 + Streamlit 大屏。

## 当前进度与关键数字（2026-10-19 更新）

6大模块全部跑通

| 模块 | 状态 | 关键数字 |
| --- | --- | --- |
| ① 数据清洗 | ✅ 完成 | 17,362 行 / 196 用户（讲义基准，默认抽样 20,000 行） |
| ② 出行驻留识别 | ✅ 完成 | 阶段1 过滤后 11,184 行、出行点 806、速度中位 17.1 km/h；阶段2 275 簇（单点 152）、平均 k=2.4；阶段3 出行 699（4.0%）/ 驻留 16,663（96.0%） |
| ③ 出行目的识别 | ✅ 完成 | 740 驻留段，POI 匹配率 92.3%；居住 531 / 购物 155 / 旅游 34 / 其他 20 |
| ④ 出行方式识别 | ✅ 完成 | 97 出行段；小汽车 37 / 其他 29 / 公交 28 / 地铁 3 |
| ⑤ 实时商圈热力 | ✅ 完成 | 10 分钟滑窗，按"分钟 × 商圈"输出人次 |
| ⑥ 结果可视化 | ✅ 完成 | 6 张业务图全部生成 |
| Dashboard 大屏 | ✅ 可运行 | Streamlit（需单独安装，见「环境配置」） |

## 数据流：6 大模块（PPT 1.2.3）

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

技术约定：**不用 sklearn**（k-means 手写）、**不用 geopandas**（经纬度距离用 Haversine 公式）。

## 项目结构

```
data-analysis-project/
├── data/                        # 数据目录（不入库，太大）
│   ├── raw/                     # 原始数据（7 个 CSV + 特征值解释.txt）
│   └── processed/               # 模块2 中间结果（stage1_dt.csv、stage2_cluster.csv）
├── project_code/                # 代码目录（6 大模块）
│   ├── config.py                # 全局配置：路径、阈值、参数（改参数只改这里）
│   ├── utils.py                 # 公共工具：读 CSV 编码兜底、Haversine、存结果、中文字体
│   ├── check_data.py            # 数据完整性检查（跑之前先执行）
│   ├── data_clean.py            # ① 数据清洗（9 条规则）
│   ├── tr_stage1.py             # ②-1 阶段1 预处理（速度粗筛出行点）
│   ├── tr_stage2.py             # ②-2 阶段2 聚类（手写 k-means，轮廓系数+邓恩指数选 k）
│   ├── tr_stage3.py             # ②-3 阶段3 业务判定（出行/驻留标签）
│   ├── purpose.py               # ③ 出行目的（时间规则 + POI 匹配，POI 优先）
│   ├── mode.py                  # ④ 出行方式（速度 + 地铁/公交 POI 匹配）
│   ├── heatmap.py               # ⑤ 实时商圈热力（10 分钟滑窗）
│   ├── visualize.py             # ⑥ 结果可视化（6 张业务图）
│   ├── Dashboard.py             # Streamlit 大屏（需额外装 streamlit）
│   └── main.py                  # 主入口（一键串联各模块）
├── result/                      # 结果目录（*.csv 不入库，figures/*.png 入库）
│   ├── cleaned_data.csv         # ① 清洗结果（6 列标准表）
│   ├── stage3_label.csv         # ② 出行/驻留标签（0=驻留，1=出行）
│   ├── purpose_result.csv       # ③ 目的结果（每驻留段一行）
│   ├── mode_result.csv          # ④ 方式结果（每出行段一行）
│   ├── heatmap_result.csv       # ⑤ 热力结果（minute, biz_name, count, hour）
│   └── figures/                 # ⑥ 6 张业务图（png）
├── notebooks/                   # Jupyter 笔记本（数据探查）
├── pyproject.toml               # 依赖清单与 uv 配置（以它为准）
├── uv.lock                      # uv 锁文件
├── requirements.txt             # pip 依赖清单
├── .python-version              # 固定 Python 3.14
└── README.md                    # 项目说明
```

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
   │       ├── 基站经纬度数据.csv     # 49,954 行，关联键 laci = lac_id-cell_id
   │       ├── 商业区数据.csv         # 104 行，实时热力用
   │       ├── 出行目的静态数据.csv   # 1,273 行，GBK 编码（经度,纬度,目的,目的地）
   │       ├── 出行方式静态数据.csv   # 968 行，GBK 编码，5 列
   │       ├── 实时流数据.csv         # 256,212 行，滑窗统计用
   │       ├── hive模块静态数据.csv   # 225 行，参考用，可不使用
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

1. Python **3.13+**（仓库 `.python-version` 固定为 3.14）
2. 安装依赖（依赖清单以 `pyproject.toml` 为准：pandas / numpy / matplotlib / loguru / haversine）：

   ```bash
   # 推荐：uv 包管理器
   uv sync
   ```

   ```bash
   # 或者：pip
   pip install -r requirements.txt
   ```

3. Dashboard 大屏另需 Streamlit（不随项目依赖安装）：

   ```bash
   pip install streamlit
   ```

## 运行方式

在**项目根目录**下运行（各脚本自带路径引导，从任意目录运行均可）。

### 1. 逐模块运行（推荐）

模块之间有接力关系，按顺序执行（注释标注了每步吃哪张表）：

```bash
python project_code/check_data.py   # 0. 检查数据是否齐备

python project_code/data_clean.py   # ① 数据清洗 → result/cleaned_data.csv
python project_code/tr_stage1.py    # ②-1 预处理 → data/processed/stage1_dt.csv
python project_code/tr_stage2.py    # ②-2 聚类 → data/processed/stage2_cluster.csv
python project_code/tr_stage3.py    # ②-3 业务判定 → result/stage3_label.csv

python project_code/purpose.py      # ③ 出行目的（吃 stage3_label.csv + POI 静态数据）
python project_code/mode.py         # ④ 出行方式（吃 stage3_label.csv + 方式静态数据）
python project_code/heatmap.py      # ⑤ 实时热力（吃实时流 + 商业区数据）
python project_code/visualize.py    # ⑥ 可视化（吃 4 张结果表 → 6 张图）
```

### 2. 一键跑通 main.py（课时57）

```bash
python project_code/main.py         # 按数据流顺序串联 8 个模块
```

> main.py 按课时57 实现：每个模块单独计时；单模块失败只打印 traceback、**继续后续模块**；
> 跑完自动核对 7 张结果 CSV + 6 张图的产出情况（缺失的会标 `[缺失]`）。

### 3. Dashboard 大屏

```bash
streamlit run project_code/Dashboard.py   # 需先安装 streamlit、先生成 6 张图
```

## 结果表接力契约

| 结果表 | 产出模块 | 关键列 | 喂给 |
| --- | --- | --- | --- |
| `result/cleaned_data.csv` | ① | imsi, time, lac_id, cell_id, lon, lat | ②-1 |
| `data/processed/stage1_dt.csv` | ②-1 | 出行点，另含 speed | ②-2 |
| `data/processed/stage2_cluster.csv` | ②-2 | 另含 cluster, is_single_cluster | ②-3 |
| `result/stage3_label.csv` | ②-3 | 另含 label（0=驻留，1=出行） | ③ ④ ⑥ |
| `result/purpose_result.csv` | ③ | 每驻留段一行，final_purpose | ⑥ |
| `result/mode_result.csv` | ④ | 每出行段一行，final_mode | ⑥ |
| `result/heatmap_result.csv` | ⑤ | minute, biz_name, count, hour | ⑥ |

模块 6 生成的 6 张业务图（`result/figures/`）：

| 图 | 文件 | 回答的问题 |
| --- | --- | --- |
| 1 出行/驻留占比饼图 | fig_stage3_pie.png | 一天里移动点和停留点占比 |
| 2 24 小时出行/驻留双折线 | fig_hour_line.png | 出行/驻留随时间如何变化 |
| 3 出行目的柱状图 | fig_purpose_bar.png | 停留都在干什么 |
| 4 出行方式柱状图 | fig_mode_bar.png | 出行都怎么去 |
| 5 商圈×24h 热力矩阵 | fig_heatmap.png | 哪里、什么时间最拥挤 |
| 6 Top5 用户 3D 时空轨迹 | fig_3d_traj.png | 个体一天的时空轨迹长什么样 |

## 开发约定

- 数据/代码/结果分离：数据放 `data/`，代码放 `project_code/`，结果放 `result/`
- 路径、阈值等参数集中在 `project_code/config.py`，不要写死在模块里
- 公共函数（读 CSV、编码兜底、Haversine、存结果、matplotlib 中文字体）统一写在 `project_code/utils.py`
- 时间统一为 `YYYYMMDDHHMMSS` 字符串（无时区，毫秒时间戳已按 +8h 转北京时间）
- ID 类字段（imsi / lac_id / cell_id）一律按字符串读写，防丢前导零
- 结果 CSV 统一用 `utf-8-sig` 写出（Excel 直接打开中文不乱码）
- 各阶段结果表之间按上表契约接力，改动列名需同步改上下游