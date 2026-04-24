"""
dashboard/app.py — HFT Order Book Simulator Dashboard

UI Aesthetic: NEON AURORA / CYBERPUNK
- Deep space purple background #0d0520
- Electric teal #00f5d4, hot pink #f72585, lime #b5e853
- Glassmorphism panels with gradient borders
- Futuristic monospace typography (Space Mono + Orbitron)
- Completely different from ALL previous projects
"""

import sys
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

st.set_page_config(page_title="Order Book Terminal",page_icon="⚡",
                   layout="wide",initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Orbitron:wght@400;700;900&display=swap');

:root{
    --bg:     #0d0520;
    --bg2:    #120830;
    --panel:  rgba(255,255,255,0.04);
    --teal:   #00f5d4;
    --pink:   #f72585;
    --lime:   #b5e853;
    --purple: #9b5de5;
    --amber:  #fee440;
    --white:  #f0eeff;
    --muted:  #6b5a8a;
    --border: rgba(0,245,212,0.25);
}

html,body,[data-testid="stAppViewContainer"],[data-testid="stApp"]{
    background:var(--bg)!important;
    font-family:'Space Mono',monospace!important;
    color:var(--white)!important;
}

[data-testid="stSidebar"],[data-testid="collapsedControl"],
button[kind="header"]{display:none!important;}
.main .block-container{max-width:100%!important;padding:0 20px 20px 20px!important;}

/* Glowing header */
.terminal-header{
    background:linear-gradient(135deg,#0d0520,#1a0a3a);
    border-bottom:1px solid var(--teal);
    padding:14px 20px;
    margin:0 -20px 20px -20px;
    display:flex; align-items:center; justify-content:space-between;
    box-shadow:0 0 30px rgba(0,245,212,0.15);
}
.th-brand{
    font-family:'Orbitron',monospace;font-size:1rem;font-weight:900;
    color:var(--teal);letter-spacing:.12em;text-shadow:0 0 20px rgba(0,245,212,0.8);
}
.th-status{
    font-size:10px;letter-spacing:.2em;color:var(--muted);
    text-transform:uppercase;display:flex;gap:20px;align-items:center;
}
.dot-live{width:7px;height:7px;background:var(--lime);border-radius:50%;
    display:inline-block;margin-right:5px;
    box-shadow:0 0 10px var(--lime);animation:blink 1.5s infinite;}
@keyframes blink{0%,100%{opacity:1;}50%{opacity:0.3;}}

/* Glassmorphism cards */
.glass-card{
    background:rgba(255,255,255,0.03);
    border:1px solid var(--border);
    border-radius:4px;
    padding:16px 18px; margin:4px 0;
    backdrop-filter:blur(10px);
    box-shadow:0 4px 24px rgba(0,0,0,0.3),inset 0 1px 0 rgba(255,255,255,0.05);
    position:relative; overflow:hidden;
}
.glass-card::before{
    content:'';position:absolute;top:0;left:0;right:0;height:2px;
    background:linear-gradient(90deg,var(--teal),var(--purple),var(--pink));
}
.glass-card.pink::before{background:linear-gradient(90deg,var(--pink),var(--amber));}
.glass-card.lime::before{background:linear-gradient(90deg,var(--lime),var(--teal));}
.glass-card.amber::before{background:linear-gradient(90deg,var(--amber),var(--pink));}
.glass-card.purple::before{background:linear-gradient(90deg,var(--purple),var(--teal));}

.gc-label{font-size:9px;letter-spacing:.25em;color:var(--muted);
    text-transform:uppercase;margin-bottom:6px;}
.gc-value{font-family:'Orbitron',monospace;font-size:1.4rem;
    color:var(--teal);font-weight:700;line-height:1.1;
    text-shadow:0 0 15px rgba(0,245,212,0.5);}
.gc-value.pink{color:var(--pink);text-shadow:0 0 15px rgba(247,37,133,0.5);}
.gc-value.lime{color:var(--lime);text-shadow:0 0 15px rgba(181,232,83,0.5);}
.gc-value.amber{color:var(--amber);text-shadow:0 0 15px rgba(254,228,64,0.5);}
.gc-sub{font-size:10px;color:var(--muted);margin-top:3px;}

h1{font-family:'Orbitron',monospace!important;font-size:1.4rem!important;
    font-weight:900!important;color:var(--teal)!important;
    letter-spacing:.08em!important;text-transform:uppercase!important;
    text-shadow:0 0 20px rgba(0,245,212,0.6)!important;
    border-left:3px solid var(--teal)!important;padding-left:14px!important;
    margin-bottom:16px!important;}
h2{font-family:'Orbitron',monospace!important;font-size:.8rem!important;
    color:var(--purple)!important;letter-spacing:.1em!important;
    text-transform:uppercase!important;}
h3{font-family:'Space Mono',monospace!important;font-size:.65rem!important;
    letter-spacing:.25em!important;text-transform:uppercase!important;
    color:var(--muted)!important;}

.stTabs [data-baseweb="tab"]{
    font-family:'Space Mono',monospace!important;font-size:10px!important;
    letter-spacing:.15em!important;text-transform:uppercase!important;
    color:var(--muted)!important;background:transparent!important;
    border-bottom:2px solid transparent!important;padding:10px 18px!important;}
.stTabs [aria-selected="true"]{color:var(--teal)!important;
    border-bottom:2px solid var(--teal)!important;
    text-shadow:0 0 10px rgba(0,245,212,0.5)!important;}
.stTabs [data-baseweb="tab-list"]{border-bottom:1px solid rgba(0,245,212,0.2)!important;
    background:transparent!important;}

.stButton>button{
    background:transparent!important;
    border:1px solid var(--teal)!important;
    color:var(--teal)!important;
    font-family:'Space Mono',monospace!important;
    letter-spacing:.1em!important;text-transform:uppercase!important;
    font-size:10px!important;padding:9px 22px!important;border-radius:2px!important;
    box-shadow:0 0 15px rgba(0,245,212,0.2)!important;
}
.stButton>button:hover{
    background:var(--teal)!important;color:var(--bg)!important;
    box-shadow:0 0 25px rgba(0,245,212,0.5)!important;}

div[data-testid="metric-container"]{
    background:rgba(255,255,255,0.03)!important;
    border:1px solid rgba(0,245,212,0.25)!important;
    border-top:2px solid var(--teal)!important;
    padding:13px!important;border-radius:4px!important;
    box-shadow:0 4px 20px rgba(0,0,0,0.3)!important;
}
div[data-testid="metric-container"] label{
    font-size:9px!important;letter-spacing:.2em!important;
    text-transform:uppercase!important;color:var(--muted)!important;
    font-family:'Space Mono',monospace!important;}
div[data-testid="metric-container"] [data-testid="stMetricValue"]{
    font-family:'Orbitron',monospace!important;
    font-size:1.3rem!important;color:var(--teal)!important;
    text-shadow:0 0 10px rgba(0,245,212,0.4)!important;}

[data-testid="stNumberInput"] input,
[data-testid="stSelectbox"]>div>div{
    background:rgba(255,255,255,0.04)!important;
    border:1px solid rgba(0,245,212,0.3)!important;
    border-radius:2px!important;color:var(--white)!important;
    font-family:'Space Mono',monospace!important;}

p,li{color:var(--white)!important;}
hr{border:none;border-top:1px solid rgba(0,245,212,0.2);margin:16px 0;}
</style>""", unsafe_allow_html=True)

# ── Colors ────────────────────────────────────────────────────────────────────
BG="#0d0520"; BG2="#120830"; TEAL="#00f5d4"; PINK="#f72585"
LIME="#b5e853"; PURPLE="#9b5de5"; AMBER="#fee440"; MUTED="#6b5a8a"; WHITE="#f0eeff"

PLOT = dict(
    paper_bgcolor=BG2, plot_bgcolor=BG2,
    font=dict(family="Space Mono", color=WHITE, size=10),
    xaxis=dict(gridcolor="rgba(0,245,212,0.08)",linecolor="rgba(0,245,212,0.2)",
               tickfont=dict(size=9,color=MUTED)),
    yaxis=dict(gridcolor="rgba(0,245,212,0.08)",linecolor="rgba(0,245,212,0.2)",
               tickfont=dict(size=9,color=MUTED)),
    legend=dict(bgcolor=BG,bordercolor="rgba(0,245,212,0.2)",
                borderwidth=1,font=dict(size=9)),
    margin=dict(l=50,r=20,t=40,b=40),
)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="terminal-header">
  <div>
    <div class="th-brand">⚡ ORDER BOOK TERMINAL</div>
    <div style="font-size:9px;color:#6b5a8a;letter-spacing:.15em;margin-top:3px">
      HFT SIMULATION ENGINE v1.0 — L2 ORDER BOOK
    </div>
  </div>
  <div class="th-status">
    <span><span class="dot-live"></span>LIVE SIM</span>
    <span>SYMBOL: AAPL</span>
    <span>ENGINE: PRICE-TIME PRIORITY</span>
  </div>
</div>""", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1,tab2,tab3,tab4,tab5 = st.tabs([
    "📊  Order Book",
    "📈  Market Simulation",
    "🤖  Market Making",
    "💥  Market Impact",
    "⚡  Latency",
])

from orderbook.engine  import OrderBook, Order, seed_order_book
from orderbook.simulator import simulate, SimConfig, MarketMaker
from orderbook.impact  import impact_curve, total_impact, ImpactParams

# ── TAB 1 — ORDER BOOK ────────────────────────────────────────────────────────
with tab1:
    st.title("Live Order Book")

    col_cfg, col_act = st.columns([2,1])
    with col_cfg:
        mid_p  = st.number_input("Mid Price ($)",10.0,1000.0,150.0,0.5)
        levels = st.slider("Depth Levels",3,20,10)
    with col_act:
        if st.button("🔄  Generate Book"):
            book = OrderBook("AAPL")
            book = seed_order_book(book, mid_p, levels=levels)
            st.session_state["book"] = book

    if "book" not in st.session_state:
        book = OrderBook("AAPL")
        book = seed_order_book(book, mid_p, levels=levels)
        st.session_state["book"] = book

    book = st.session_state["book"]
    summ = book.summary()
    depth = book.depth(levels)

    # KPI row
    k1,k2,k3,k4,k5,k6 = st.columns(6)
    k1.markdown(f'<div class="glass-card"><div class="gc-label">Best Bid</div>'
                f'<div class="gc-value lime">${summ["best_bid"] or "—"}</div></div>',
                unsafe_allow_html=True)
    k2.markdown(f'<div class="glass-card pink"><div class="gc-label">Best Ask</div>'
                f'<div class="gc-value pink">${summ["best_ask"] or "—"}</div></div>',
                unsafe_allow_html=True)
    k3.markdown(f'<div class="glass-card amber"><div class="gc-label">Spread</div>'
                f'<div class="gc-value amber">${summ["spread"] or "—"}</div></div>',
                unsafe_allow_html=True)
    k4.markdown(f'<div class="glass-card purple"><div class="gc-label">Mid Price</div>'
                f'<div class="gc-value">${summ["mid_price"] or "—"}</div></div>',
                unsafe_allow_html=True)
    k5.markdown(f'<div class="glass-card lime"><div class="gc-label">Imbalance</div>'
                f'<div class="gc-value lime">{summ["imbalance"]:.4f}</div></div>',
                unsafe_allow_html=True)
    k6.markdown(f'<div class="glass-card"><div class="gc-label">Total Trades</div>'
                f'<div class="gc-value">{summ["total_trades"]}</div></div>',
                unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col1,col2 = st.columns(2)

    with col1:
        st.subheader("Depth Chart")
        bids_p = [p for p,_ in depth["bids"]]
        bids_v = [v for _,v in depth["bids"]]
        asks_p = [p for p,_ in depth["asks"]]
        asks_v = [v for _,v in depth["asks"]]
        fig = go.Figure()
        fig.add_trace(go.Bar(x=bids_p,y=bids_v,name="Bids",
                              marker_color=LIME,opacity=0.8))
        fig.add_trace(go.Bar(x=asks_p,y=asks_v,name="Asks",
                              marker_color=PINK,opacity=0.8))
        if summ["mid_price"]:
            fig.add_vline(x=summ["mid_price"],line_color=TEAL,line_dash="dash",
                          annotation_text="Mid",annotation_font=dict(color=TEAL))
        fig.update_layout(**PLOT,height=320,barmode="overlay",
                          title=dict(text="DEPTH CHART — BIDS vs ASKS",
                                     font=dict(size=10,color=MUTED)),
                          xaxis_title="Price ($)",yaxis_title="Volume")
        st.plotly_chart(fig,use_container_width=True)

    with col2:
        st.subheader("Submit Order")
        o_side = st.selectbox("Side",["buy","sell"])
        o_type = st.selectbox("Type",["limit","market"])
        o_qty  = st.number_input("Quantity",1,10000,100)
        o_price= st.number_input("Price ($)",0.01,2000.0,mid_p,0.01)                  if o_type=="limit" else None
        if st.button("▶  Submit Order"):
            import uuid
            oid = str(uuid.uuid4())[:8]
            o   = Order(oid, o_side, o_price or 0, o_qty, o_type)
            trades = book.submit(o)
            st.success(f"Order {oid}: status={o.status} | filled={o.filled} | trades={len(trades)}")
            st.session_state["book"] = book
            st.rerun()

        # Ladder view
        st.subheader("Order Ladder")
        rows = []
        for p,v in reversed(depth["asks"][:5]):
            rows.append({"Price":f"${p:.2f}","Bid Vol":"","Ask Vol":f"{v:,}","Side":"ASK"})
        rows.append({"Price":f"${summ['mid_price']:.2f}" if summ['mid_price'] else "—",
                     "Bid Vol":"","Ask Vol":"","Side":"MID"})
        for p,v in depth["bids"][:5]:
            rows.append({"Price":f"${p:.2f}","Bid Vol":f"{v:,}","Ask Vol":"","Side":"BID"})
        df_ladder = pd.DataFrame(rows)
        st.dataframe(df_ladder,use_container_width=True,height=280)

# ── TAB 2 — SIMULATION ────────────────────────────────────────────────────────
with tab2:
    st.title("Market Simulation")

    col1,col2,col3 = st.columns(3)
    n_steps  = col1.slider("Steps",100,2000,500)
    mid_sim  = col2.number_input("Mid Price",10.0,1000.0,150.0)
    vol_sim  = col3.slider("Volatility",0.0005,0.01,0.002,0.0005,format="%.4f")

    if st.button("▶  Run Simulation"):
        with st.spinner("Simulating order flow..."):
            cfg    = SimConfig(n_steps=n_steps,mid_price=mid_sim,volatility=vol_sim)
            result = simulate(cfg)
            st.session_state["sim"] = result

    if "sim" in st.session_state:
        r = st.session_state["sim"]
        s = r["summary"]

        m1,m2,m3,m4 = st.columns(4)
        m1.metric("TOTAL TRADES",  f"{s['total_trades']:,}")
        m2.metric("TOTAL VOLUME",  f"{s['total_volume']:,}")
        m3.metric("AVG SPREAD",
                  f"${np.mean([x for x in r['spreads'] if x>0]):.4f}"
                  if r["spreads"] else "N/A")
        m4.metric("VWAP",  f"${s['vwap']}" if s["vwap"] else "N/A")

        col1,col2 = st.columns(2)
        with col1:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                y=r["mids"], mode="lines", name="Mid Price",
                line=dict(color=TEAL,width=1.5),
                fill="tozeroy",fillcolor="rgba(0,245,212,0.05)"
            ))
            fig.update_layout(**PLOT,height=300,
                              title=dict(text="MID PRICE EVOLUTION",
                                         font=dict(size=10,color=MUTED)),
                              yaxis_title="Price ($)")
            st.plotly_chart(fig,use_container_width=True)

        with col2:
            fig2 = make_subplots(rows=2,cols=1,shared_xaxes=True,row_heights=[0.6,0.4])
            spreads_clean = [s for s in r["spreads"] if s>0]
            fig2.add_trace(go.Scatter(y=r["spreads"],mode="lines",name="Spread",
                                       line=dict(color=AMBER,width=1)),row=1,col=1)
            fig2.add_trace(go.Scatter(y=r["imbalances"],mode="lines",name="Imbalance",
                                       line=dict(color=PINK,width=1),
                                       fill="tozeroy",
                                       fillcolor="rgba(247,37,133,0.1)"),row=2,col=1)
            fig2.update_layout(**PLOT,height=300,
                               title=dict(text="SPREAD & IMBALANCE",
                                          font=dict(size=10,color=MUTED)))
            st.plotly_chart(fig2,use_container_width=True)

        if not r["trades_df"].empty:
            st.subheader("Trade Tape")
            st.dataframe(r["trades_df"].tail(20),use_container_width=True,height=220)
    else:
        st.info("Configure parameters above and click **▶ Run Simulation**")

# ── TAB 3 — MARKET MAKING ────────────────────────────────────────────────────
with tab3:
    st.title("Market Making Strategy")

    col1,col2,col3 = st.columns(3)
    mm_spread = col1.slider("Target Spread ($)",0.01,0.20,0.04,0.01)
    mm_qty    = col2.number_input("Quote Size",10,1000,50)
    mm_steps  = col3.slider("Simulation Steps",100,2000,500)

    if st.button("▶  Run Market Maker"):
        with st.spinner("Running market making strategy..."):
            cfg = SimConfig(n_steps=mm_steps)
            mm  = MarketMaker(spread_target=mm_spread, qty=mm_qty)
            res = mm.run(cfg)
            st.session_state["mm"] = res

    if "mm" in st.session_state:
        r = st.session_state["mm"]
        m1,m2,m3,m4 = st.columns(4)
        m1.metric("FINAL P&L",    f"${r['final_pnl']:,.2f}")
        m2.metric("TOTAL FILLS",  f"{r['total_fills']:,}")
        m3.metric("SHARPE RATIO", f"{r['sharpe']:.3f}")
        m4.metric("FINAL INV",    f"{r['inventory'][-1]:,}")

        col1,col2 = st.columns(2)
        with col1:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                y=r["pnl_curve"], mode="lines", name="P&L",
                line=dict(color=LIME,width=2),
                fill="tozeroy",fillcolor="rgba(181,232,83,0.06)"
            ))
            fig.add_hline(y=0,line_color=PINK,line_dash="dash",line_width=1)
            fig.update_layout(**PLOT,height=300,
                              title=dict(text="MARKET MAKER P&L CURVE",
                                         font=dict(size=10,color=MUTED)),
                              yaxis_title="P&L ($)")
            st.plotly_chart(fig,use_container_width=True)

        with col2:
            fig2 = go.Figure()
            colors = [LIME if v>=0 else PINK for v in r["inventory"]]
            fig2.add_trace(go.Scatter(
                y=r["inventory"], mode="lines", name="Inventory",
                line=dict(color=PURPLE,width=1.5),
                fill="tozeroy",fillcolor="rgba(155,93,229,0.08)"
            ))
            fig2.add_hline(y=0,line_color=TEAL,line_dash="dash",line_width=1)
            fig2.update_layout(**PLOT,height=300,
                               title=dict(text="INVENTORY POSITION",
                                          font=dict(size=10,color=MUTED)),
                               yaxis_title="Net Position (shares)")
            st.plotly_chart(fig2,use_container_width=True)
    else:
        st.info("Configure parameters above and click **▶ Run Market Maker**")

# ── TAB 4 — MARKET IMPACT ────────────────────────────────────────────────────
with tab4:
    st.title("Market Impact Model")
    st.markdown("*Kyle (1985) permanent impact + temporary bid-ask cost*")

    col1,col2,col3 = st.columns(3)
    adv    = col1.number_input("ADV (shares)", 100000, 50000000, 1000000, 100000)
    sigma  = col2.slider("Daily Volatility",0.005,0.10,0.02,0.005,format="%.3f")
    qty    = col3.number_input("Order Size", 100, 1000000, 10000, 1000)

    params = ImpactParams(sigma=sigma,adv=adv)
    impact = total_impact(qty, params)
    curve  = impact_curve(adv, sigma)

    m1,m2,m3,m4 = st.columns(4)
    m1.metric("PERM IMPACT",  f"${impact['permanent_impact']:.5f}")
    m2.metric("TEMP IMPACT",  f"${impact['temporary_impact']:.5f}")
    m3.metric("TOTAL COST",   f"${impact['total_cost']:,.2f}")
    m4.metric("COST (BPS)",   f"{impact['cost_bps']:.2f}")

    col1,col2 = st.columns(2)
    with col1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=curve["quantities"],y=curve["perm_impacts"],
                                  name="Permanent",line=dict(color=PINK,width=2)))
        fig.add_trace(go.Scatter(x=curve["quantities"],y=curve["temp_impacts"],
                                  name="Temporary",line=dict(color=AMBER,width=2)))
        fig.add_vline(x=qty,line_color=TEAL,line_dash="dash",
                      annotation_text=f"Order: {qty:,}",
                      annotation_font=dict(color=TEAL,size=9))
        fig.update_layout(**PLOT,height=320,
                          title=dict(text="IMPACT CURVE vs ORDER SIZE",
                                     font=dict(size=10,color=MUTED)),
                          xaxis_title="Order Size (shares)",
                          yaxis_title="Impact ($)",
                          xaxis_type="log")
        st.plotly_chart(fig,use_container_width=True)

    with col2:
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=curve["quantities"],y=curve["cost_bps"],
                                   name="Cost (bps)",
                                   line=dict(color=PURPLE,width=2),
                                   fill="tozeroy",fillcolor="rgba(155,93,229,0.08)"))
        fig2.add_vline(x=qty,line_color=TEAL,line_dash="dash")
        fig2.update_layout(**PLOT,height=320,
                           title=dict(text="TRANSACTION COST IN BASIS POINTS",
                                      font=dict(size=10,color=MUTED)),
                           xaxis_title="Order Size (shares)",
                           yaxis_title="Cost (bps)",xaxis_type="log")
        st.plotly_chart(fig2,use_container_width=True)

# ── TAB 5 — LATENCY ──────────────────────────────────────────────────────────
with tab5:
    st.title("Latency Benchmarking")

    n_bench = st.slider("Orders to Benchmark", 100, 5000, 1000)
    if st.button("▶  Run Latency Benchmark"):
        with st.spinner("Benchmarking..."):
            import time, uuid
            book_b = OrderBook("BENCH")
            book_b = seed_order_book(book_b, 150.0, levels=10)
            np.random.seed(42)
            for i in range(n_bench):
                side  = np.random.choice(["buy","sell"])
                otype = "market" if np.random.random()<0.15 else "limit"
                qty   = max(1,int(np.random.exponential(100)))
                price = round(150.0+np.random.normal(0,0.5),2) if otype=="limit" else 0
                o = Order(str(uuid.uuid4())[:8],side,price,qty,otype)
                book_b.submit(o)
            st.session_state["bench"] = book_b

    if "bench" in st.session_state:
        book_b = st.session_state["bench"]
        lat    = book_b.latency_stats()
        lats   = np.array(book_b.latencies)

        m1,m2,m3,m4,m5,m6 = st.columns(6)
        m1.metric("MEAN (µs)",   f"{lat.get('mean_us','N/A')}")
        m2.metric("MEDIAN (µs)", f"{lat.get('median_us','N/A')}")
        m3.metric("P95 (µs)",    f"{lat.get('p95_us','N/A')}")
        m4.metric("P99 (µs)",    f"{lat.get('p99_us','N/A')}")
        m5.metric("MIN (µs)",    f"{lat.get('min_us','N/A')}")
        m6.metric("MAX (µs)",    f"{lat.get('max_us','N/A')}")

        col1,col2 = st.columns(2)
        with col1:
            fig = go.Figure()
            fig.add_trace(go.Histogram(x=lats,nbinsx=60,
                                        marker_color=TEAL,opacity=0.8,name="Latency"))
            for pct,color,label in [(95,AMBER,"P95"),(99,PINK,"P99")]:
                v = np.percentile(lats,pct)
                fig.add_vline(x=v,line_color=color,line_dash="dash",
                              annotation_text=label,annotation_font=dict(color=color,size=9))
            fig.update_layout(**PLOT,height=320,showlegend=False,
                              title=dict(text="LATENCY DISTRIBUTION (µs)",
                                         font=dict(size=10,color=MUTED)),
                              xaxis_title="Latency (µs)",yaxis_title="Count")
            st.plotly_chart(fig,use_container_width=True)

        with col2:
            pctiles = [50,75,90,95,99,99.9]
            vals    = [np.percentile(lats,p) for p in pctiles]
            fig2 = go.Figure(go.Bar(
                x=[f"P{p}" for p in pctiles], y=vals,
                marker_color=[TEAL,TEAL,AMBER,AMBER,PINK,PINK],
                text=[f"{v:.3f}" for v in vals],textposition="outside",
                textfont=dict(size=9,color=WHITE)
            ))
            fig2.update_layout(**PLOT,height=320,
                               title=dict(text="LATENCY PERCENTILES (µs)",
                                          font=dict(size=10,color=MUTED)),
                               yaxis_title="Latency (µs)")
            st.plotly_chart(fig2,use_container_width=True)

        st.subheader("Cumulative Latency Distribution")
        sorted_lats = np.sort(lats)
        cdf         = np.arange(len(sorted_lats))/len(sorted_lats)*100
        fig3 = go.Figure(go.Scatter(
            x=sorted_lats, y=cdf, mode="lines",
            line=dict(color=LIME,width=2),
            fill="tozeroy",fillcolor="rgba(181,232,83,0.05)"
        ))
        fig3.update_layout(**PLOT,height=280,
                           title=dict(text="CUMULATIVE DISTRIBUTION",
                                      font=dict(size=10,color=MUTED)),
                           xaxis_title="Latency (µs)",yaxis_title="Percentile (%)")
        st.plotly_chart(fig3,use_container_width=True)
    else:
        st.info("Click **▶ Run Latency Benchmark** to measure order processing speed")