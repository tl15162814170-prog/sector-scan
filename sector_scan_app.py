import streamlit as st
import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import warnings
warnings.filterwarnings("ignore")

st.set_page_config(
    page_title="选股魔方",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 自定义样式，让界面更接近截图风格
st.markdown("""
<style>
    .main-header {
        font-size: 28px;
        font-weight: bold;
        color: #1f1f1f;
        margin-bottom: 5px;
    }
    .sub-header {
        font-size: 14px;
        color: #888;
        margin-bottom: 20px;
    }
    .card {
        background: linear-gradient(135deg, #fff5f5 0%, #fff 100%);
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    .stButton>button {
        border-radius: 12px;
        height: 48px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">选股魔方</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">专业投研 · 聚焦价值 · 策略优良</div>', unsafe_allow_html=True)

# ==================== 工具函数 ====================
def safe_get_sector(max_retry=3):
    for i in range(max_retry):
        try:
            df = ak.stock_sector_fund_flow_rank(indicator="今日", sector_type="行业资金流")
            if df is not None and not df.empty:
                return df
        except:
            time.sleep(1.5)
    return None

def get_stock_list():
    try:
        df = ak.stock_zh_a_spot_em()
        df = df[df["代码"].str.match(r"^(00|30|60|68)")]
        df = df[~df["名称"].str.contains("ST|st|\*ST|退", na=False)]
        return df
    except:
        return None

# ==================== 页面分区 ====================
tab1, tab2, tab3, tab4 = st.tabs(["📊 板块资金扫盘", "🌙 尾盘量化选股", "☀️ 早盘量化选股", "⭐ 特色指标"])

# ========== 1. 板块资金扫盘 ==========
with tab1:
    st.subheader("板块资金流向扫盘")
    col1, col2, col3 = st.columns(3)
    with col1:
        black_inflow = st.number_input("黑马净流入≥(亿)", 5.0, 50.0, 8.0, 1.0, key="b1")
    with col2:
        black_pct = st.number_input("黑马涨幅≤(%)", 0.5, 3.0, 1.0, 0.1, key="b2")
    with col3:
        start_inflow = st.number_input("冒头净流入≥(亿)", 3.0, 30.0, 5.0, 1.0, key="b3")

    if st.button("🚀 开始扫盘", key="scan1", use_container_width=True):
        with st.spinner("正在扫描全市场板块资金..."):
            df = safe_get_sector()
            if df is None:
                st.error("获取数据失败，东方财富接口繁忙，请稍后再试或改用本地运行")
            else:
                # 列名兼容处理
                name_col = [c for c in df.columns if "名称" in c][0]
                pct_col = [c for c in df.columns if "涨跌幅" in c][0]
                net_col = [c for c in df.columns if "主力净流入-净额" in c or ("主力净流入" in c and "净额" in c)][0]

                df["板块"] = df[name_col]
                df["涨跌幅"] = pd.to_numeric(df[pct_col], errors="coerce")
                df["净流入亿"] = pd.to_numeric(df[net_col], errors="coerce") / 1e8
                df = df.dropna(subset=["涨跌幅", "净流入亿"])

                # 黑马
                black = df[(df["净流入亿"] >= black_inflow) & (df["涨跌幅"] <= black_pct) & (df["涨跌幅"] > -1.5)]
                black = black.sort_values("净流入亿", ascending=False)

                # 冒头
                start = df[(df["净流入亿"] >= start_inflow) & (df["涨跌幅"] >= 1.5)]
                start = start.sort_values("涨跌幅", ascending=False)

                # 失血
                bleed = df[df["净流入亿"] <= -15].sort_values("净流入亿").head(10)

                st.success(f"扫描完成 {datetime.now().strftime('%H:%M:%S')}")

                st.markdown("### 🐴 黑马 | 钱进来了，价没抬")
                if not black.empty:
                    st.dataframe(black[["板块", "净流入亿", "涨跌幅"]].round(2), use_container_width=True, hide_index=True)
                else:
                    st.info("今日无明显黑马")

                st.markdown("### 🚀 冒头 | 钱到位，已经动了")
                if not start.empty:
                    st.dataframe(start[["板块", "净流入亿", "涨跌幅"]].round(2), use_container_width=True, hide_index=True)
                else:
                    st.info("今日无明显启动板块")

                st.markdown("### ❌ 失血 | 大钱在跑")
                if not bleed.empty:
                    st.dataframe(bleed[["板块", "净流入亿", "涨跌幅"]].round(2), use_container_width=True, hide_index=True)

# ========== 2. 尾盘量化选股 ==========
with tab2:
    st.subheader("尾盘量化选股 · 横盘放量启动")
    st.caption("逻辑：长期横盘 + 突然放量 + 收阳")

    c1, c2, c3 = st.columns(3)
    with c1:
        sideways_days = st.slider("横盘天数", 15, 45, 25, key="t1")
    with c2:
        amp_th = st.slider("最大振幅%", 10, 25, 15, key="t2") / 100
    with c3:
        vol_ratio = st.slider("放量倍数", 1.5, 3.0, 1.8, 0.1, key="t3")

    max_num = st.slider("扫描数量（越大越慢）", 100, 800, 300, 50, key="t4")

    if st.button("🌙 开始尾盘选股", key="scan2", use_container_width=True):
        with st.spinner(f"正在扫描约{max_num}只股票，请耐心等待..."):
            stock_df = get_stock_list()
            if stock_df is None:
                st.error("获取股票列表失败")
            else:
                stock_df = stock_df.head(max_num)
                results = []
                progress = st.progress(0)
                status = st.empty()

                for i, row in stock_df.iterrows():
                    code = row["代码"]
                    name = row["名称"]
                    status.text(f"扫描中 {i+1}/{len(stock_df)}  {code} {name}")
                    try:
                        end = datetime.now().strftime("%Y%m%d")
                        start = (datetime.now() - timedelta(days=90)).strftime("%Y%m%d")
                        hist = ak.stock_zh_a_hist(symbol=code, period="daily", start_date=start, end_date=end, adjust="qfq")
                        if hist is None or len(hist) < sideways_days + 25:
                            continue
                        hist = hist.rename(columns={"日期":"date","开盘":"open","收盘":"close","最高":"high","最低":"low","成交量":"volume","成交额":"amount","涨跌幅":"pct"})
                        hist = hist.sort_values("date").reset_index(drop=True)

                        recent = hist.iloc[-(sideways_days+1):-1]
                        today = hist.iloc[-1]

                        amp = (recent["high"].max() - recent["low"].min()) / recent["low"].min()
                        if amp > amp_th:
                            continue
                        vol_ma = hist["volume"].iloc[-(21):-1].mean()
                        if vol_ma <= 0 or today["volume"] / vol_ma < vol_ratio:
                            continue
                        if today["close"] < today["open"] and today["pct"] <= 0:
                            continue
                        if today["amount"] < 5e7:
                            continue

                        results.append({
                            "代码": code,
                            "名称": name,
                            "现价": round(today["close"], 2),
                            "涨幅%": round(today["pct"], 2),
                            "放量倍数": round(today["volume"]/vol_ma, 2),
                            "振幅%": round(amp*100, 2)
                        })
                    except:
                        pass
                    progress.progress((i+1)/len(stock_df))
                    time.sleep(0.08)

                progress.empty()
                status.empty()

                if results:
                    res_df = pd.DataFrame(results).sort_values("放量倍数", ascending=False)
                    st.success(f"找到 {len(res_df)} 只符合条件的股票")
                    st.dataframe(res_df, use_container_width=True, hide_index=True)
                    csv = res_df.to_csv(index=False).encode("utf-8-sig")
                    st.download_button("下载结果CSV", csv, f"尾盘选股_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")
                else:
                    st.warning("未找到符合条件的股票，可适当放宽参数")

# ========== 3. 早盘量化选股 ==========
with tab3:
    st.subheader("早盘量化选股 · 高开放量")
    st.caption("逻辑：高开 + 放量 + 强势")

    if st.button("☀️ 开始早盘选股", key="scan3", use_container_width=True):
        with st.spinner("正在获取实时行情..."):
            df = get_stock_list()
            if df is None:
                st.error("获取数据失败")
            else:
                df["涨跌幅"] = pd.to_numeric(df["涨跌幅"], errors="coerce")
                df["成交额"] = pd.to_numeric(df["成交额"], errors="coerce")
                # 简单强势过滤
                strong = df[
                    (df["涨跌幅"] >= 3) &
                    (df["涨跌幅"] < 9.9) &
                    (df["成交额"] >= 1e8)
                ].sort_values("涨跌幅", ascending=False).head(30)

                st.success(f"找到 {len(strong)} 只早盘强势股")
                show = strong[["代码", "名称", "最新价", "涨跌幅", "成交额"]].copy()
                show["成交额"] = (show["成交额"]/1e8).round(2)
                show.columns = ["代码", "名称", "最新价", "涨跌幅%", "成交额(亿)"]
                st.dataframe(show, use_container_width=True, hide_index=True)

# ========== 4. 特色指标 ==========
with tab4:
    st.subheader("特色指标（简化版）")
    st.info("以下为简化演示逻辑，实际可继续扩展")

    st.markdown("""
    **十全十美（示意）**  
    - 均线多头排列  
    - 成交量温和放大  
    - 股价站上关键均线  
    - 所属板块有资金流入  

    **趋势王（示意）**  
    - 股价创阶段新高  
    - 量价齐升  
    - 回踩不破关键支撑  
    """)

    st.warning("完整特色指标需要更多历史数据和回测支持，后续可继续迭代。")

st.markdown("---")
st.caption("仅供学习研究，不构成投资建议 | 数据来源：东方财富 via akshare")
