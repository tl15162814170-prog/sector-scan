import streamlit as st
import akshare as ak
import pandas as pd
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

st.set_page_config(
    page_title="阿盘·收盘扫盘同款",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📊 收盘扫盘 · 板块资金流向")
st.caption("同款逻辑：偷偷建仓 / 明牌启动 / 失血 | 手机浏览器可用 | 数据来源：东方财富")

# ==================== 侧边栏参数 ====================
st.sidebar.header("🔧 参数设置")

black_inflow = st.sidebar.number_input("黑马：主力净流入 ≥（亿）", 3.0, 100.0, 8.0, 1.0)
black_pct_max = st.sidebar.number_input("黑马：板块涨幅 ≤（%）", 0.1, 5.0, 1.0, 0.1)
start_inflow = st.sidebar.number_input("冒头：主力净流入 ≥（亿）", 2.0, 50.0, 5.0, 1.0)
start_pct_min = st.sidebar.number_input("冒头：板块涨幅 ≥（%）", 0.5, 10.0, 1.5, 0.1)
bleed_outflow = st.sidebar.number_input("失血：主力净流出 ≤（亿）", -200.0, -5.0, -20.0, 5.0)

st.sidebar.markdown("---")
st.sidebar.info("建议收盘后使用（15:00后数据更准确）")

# ==================== 主程序 ====================
if st.button("🚀 开始扫盘", type="primary", use_container_width=True):
    with st.spinner("正在获取今日板块资金流向数据..."):
        try:
            df = ak.stock_sector_fund_flow_rank_em(indicator="今日")
            
            # 统一列名
            df = df.rename(columns={
                "名称": "板块",
                "今日主力净流入-净额": "主力净流入",
                "今日涨跌幅": "板块涨跌",
                "今日主力净流入-净占比": "净占比"
            })
            
            df["主力净流入_亿"] = pd.to_numeric(df["主力净流入"], errors="coerce") / 1e8
            df["板块涨跌"] = pd.to_numeric(df["板块涨跌"], errors="coerce")
            df = df.dropna(subset=["主力净流入_亿", "板块涨跌"])
            
            # ========== 三类分类 ==========
            # 1. 黑马：钱进来了，价没抬（偷偷建仓）
            black = df[
                (df["主力净流入_亿"] >= black_inflow) & 
                (df["板块涨跌"] <= black_pct_max) &
                (df["板块涨跌"] > -2)
            ].sort_values("主力净流入_亿", ascending=False)
            
            # 2. 冒头：钱到位，已经动了（明牌启动）
            start = df[
                (df["主力净流入_亿"] >= start_inflow) & 
                (df["板块涨跌"] >= start_pct_min)
            ].sort_values("板块涨跌", ascending=False)
            
            # 3. 失血：大钱在跑
            bleed = df[
                (df["主力净流入_亿"] <= bleed_outflow)
            ].sort_values("主力净流入_亿").head(12)
            
            st.success(f"✅ 扫描完成 · {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            
            # ========== 黑马 ==========
            st.subheader("🐴 黑马 | 钱进来了，价没抬（偷偷建仓）")
            if not black.empty:
                show_black = black[["板块", "主力净流入_亿", "板块涨跌"]].copy()
                show_black.columns = ["板块", "主力净流入(亿)", "板块涨跌%"]
                show_black["主力净流入(亿)"] = show_black["主力净流入(亿)"].round(2)
                show_black["板块涨跌%"] = show_black["板块涨跌%"].round(2)
                st.dataframe(show_black, use_container_width=True, hide_index=True)
                
                top = show_black.iloc[0]
                st.info(f"**{top['板块']}** 净流入 **{top['主力净流入(亿)']} 亿**，板块只涨了 **{top['板块涨跌%']}%** —— 钱进来了价没动，是低位埋单的形态。")
            else:
                st.write("今日无明显黑马板块")
            
            st.markdown("---")
            
            # ========== 冒头 ==========
            st.subheader("🚀 冒头 | 钱到位，已经动了（明牌启动）")
            if not start.empty:
                show_start = start[["板块", "主力净流入_亿", "板块涨跌"]].copy()
                show_start.columns = ["板块", "主力净流入(亿)", "板块涨跌%"]
                show_start["主力净流入(亿)"] = show_start["主力净流入(亿)"].round(2)
                show_start["板块涨跌%"] = show_start["板块涨跌%"].round(2)
                st.dataframe(show_start, use_container_width=True, hide_index=True)
            else:
                st.write("今日无明显启动板块")
            
            st.markdown("---")
            
            # ========== 失血 ==========
            st.subheader("❌ 失血 | 大钱在跑，位置还在高位")
            if not bleed.empty:
                show_bleed = bleed[["板块", "主力净流入_亿", "板块涨跌"]].copy()
                show_bleed.columns = ["板块", "主力净流入(亿)", "板块涨跌%"]
                show_bleed["主力净流入(亿)"] = show_bleed["主力净流入(亿)"].round(2)
                show_bleed["板块涨跌%"] = show_bleed["板块涨跌%"].round(2)
                st.dataframe(show_bleed, use_container_width=True, hide_index=True)
            else:
                st.write("今日无明显失血板块")
            
            # ========== 一句话总结 ==========
            st.markdown("---")
            st.subheader("📌 一句话总结")
            if not black.empty and not bleed.empty:
                st.success(f"**钱从高位科技往低位周期搬**：重点观察【{black.iloc[0]['板块']}】的持续吸筹，警惕【{bleed.iloc[0]['板块']}】的继续失血。")
            elif not black.empty:
                st.success(f"今日重点观察【**{black.iloc[0]['板块']}**】——主力在低位偷偷建仓。")
            elif not start.empty:
                st.success(f"今日最强启动板块是【**{start.iloc[0]['板块']}**】。")
            else:
                st.info("今日资金流向较为分散，建议继续观察。")
            
            # ========== 下载全部数据 ==========
            st.markdown("---")
            all_data = df[["板块", "主力净流入_亿", "板块涨跌"]].copy()
            all_data.columns = ["板块", "主力净流入(亿)", "板块涨跌%"]
            all_data = all_data.sort_values("主力净流入(亿)", ascending=False)
            all_data["主力净流入(亿)"] = all_data["主力净流入(亿)"].round(2)
            all_data["板块涨跌%"] = all_data["板块涨跌%"].round(2)
            
            csv = all_data.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                label="📥 下载今日全部板块资金流向CSV",
                data=csv,
                file_name=f"板块资金流向_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
                
        except Exception as e:
            st.error(f"获取数据失败：{str(e)}")
            st.info("可能原因：网络问题或akshare接口暂时限流，请稍后重试。")

# 使用说明
with st.expander("📖 使用说明"):
    st.markdown("""
    **三类信号解释**：
    
    - **黑马（偷偷建仓）**：主力净流入很大，但板块涨幅很小 → 钱进来了价没抬，低位埋单形态
    - **冒头（明牌启动）**：主力净流入较大 + 板块明显上涨 → 钱到位，已经动了
    - **失血**：主力大幅净流出 + 板块下跌 → 大钱在跑，位置还高
    
    **建议**：
    1. 每天收盘后（15:00后）运行一次
    2. 重点跟踪「黑马」板块后续是否持续吸筹
    3. 「失血」板块短期谨慎追高
    """)

st.markdown("---")
st.caption("仅供学习研究，不构成投资建议。数据来源：东方财富 via akshare")
