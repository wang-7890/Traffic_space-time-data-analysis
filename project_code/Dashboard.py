# dashboard.py
import streamlit as st
from pathlib import Path
import sys
# 把项目根目录加入路径，复用配置/工具函数（可选，KPI统计用）
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from project_code.config import RESULT_FILES,RESULT_DIR
from project_code.utils import _read_csv_any_encoding

# ========= 页面基础配置 =========
st.set_page_config(page_title="用户时空出行驻留分析看板", layout="wide")
st.title("用户时空出行驻留分析 Dashboard")

# 图片目录：save_fig输出的目录，和你utils里save_fig保持一致
FIG_DIR = Path(__file__).resolve().parent.parent / "result" / "figures"

# ========= 顶部KPI指标栏 =========
st.subheader("📊 全局指标概览")
label_df = _read_csv_any_encoding(RESULT_DIR/RESULT_FILES['stage3'], dtype={'imsi': str})
total = len(label_df)
stay_cnt = (label_df["label"] == 0).sum()
travel_cnt = (label_df["label"] == 1).sum()
stay_ratio = stay_cnt / total
travel_ratio = travel_cnt / total

col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
with col_kpi1:
    st.metric("总轨迹样本", f"{total:,}")
with col_kpi2:
    st.metric("驻留样本数量", f"{stay_cnt:,}", f"{stay_ratio:.1%}")
with col_kpi3:
    st.metric("出行样本数量", f"{travel_cnt:,}", f"{travel_ratio:.1%}")
with col_kpi4:
    st.metric("驻留/出行比例", f"{stay_ratio / travel_ratio:.2f}")

st.divider()

# ========= 2行3列图表布局 =========
# 第一行
row1_col1, row1_col2, row1_col3 = st.columns(3)
with row1_col1:
    st.subheader("图1 出行/驻留占比饼图")
    st.image(str(FIG_DIR / "fig_stage3_pie.png"))

with row1_col2:
    st.subheader("图2 24小时出行/驻留折线")
    st.image(str(FIG_DIR / "fig_hour_line.png"))

with row1_col3:
    st.subheader("图3 出行目的柱状图")
    st.image(str(FIG_DIR / "fig_purpose_bar.png"))

# 第二行
row2_col1, row2_col2, row2_col3 = st.columns(3)
with row2_col1:
    st.subheader("图4 出行方式柱状图")
    st.image(str(FIG_DIR / "fig_mode_bar.png"))

with row2_col2:
    st.subheader("图5 Top10商圈 ×24h热力矩阵")
    st.image(str(FIG_DIR / "fig_heatmap.png"))

with row2_col3:
    st.subheader("图6 Top5用户3D时空轨迹")
    st.image(str(FIG_DIR / "fig_3d_traj.png"))

st.divider()
st.markdown("""
> 项目说明：
> - label=0：驻留；label=1：出行
> - 热力图展示Top10热门商圈24小时人次分布
> - 3D轨迹：经度(X)、纬度(Y)、时间(Z)，展示个体用户时空移动特征
""")
