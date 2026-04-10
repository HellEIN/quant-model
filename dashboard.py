import streamlit as st
import sqlite3
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from pathlib import Path

# ══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG — must be first Streamlit call
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="BVC Market Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════════════
# GLOBAL CSS — dark mode, Sora + JetBrains Mono
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ─── Base ─────────────────────────────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; }
html, body, [class*="css"] {
    font-family: 'Sora', sans-serif !important;
    background-color: #0B0F1A !important;
    color: #CDD9E5 !important;
}
.stApp { background-color: #0B0F1A !important; }

/* hide default Streamlit chrome — keep sidebar toggle visible */
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }
/* Do NOT hide 'header' — it contains the sidebar toggle button.
   Instead hide only its inner content. */
[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stHeader"] > * { visibility: hidden; }
[data-testid="stHeader"] [data-testid="stSidebarCollapsedControl"],
[data-testid="stHeader"] button[kind="header"] {
    visibility: visible !important;
}
.stDeployButton { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }
/* Sidebar collapse/expand toggle always visible */
[data-testid="stSidebarCollapsedControl"] { visibility: visible !important; }
button[data-testid="baseButton-header"] { visibility: visible !important; }

/* ─── Sidebar ──────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background-color: #0D1117 !important;
    border-right: 1px solid #21262D !important;
    min-width: 220px !important;
}
[data-testid="stSidebar"] > div {
    padding-top: 0 !important;
}
/* make sure all text in sidebar is visible */
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] div,
[data-testid="stSidebar"] label {
    color: #CDD9E5 !important;
}
[data-testid="stSidebar"] .stRadio label {
    display: flex !important;
    align-items: center !important;
    padding: 10px 16px !important;
    border-radius: 6px !important;
    font-size: 0.84rem !important;
    color: #8B949E !important;
    cursor: pointer;
    transition: background 0.12s, color 0.12s;
    font-family: 'Sora', sans-serif !important;
    background: transparent !important;
    border: none !important;
}
[data-testid="stSidebar"] .stRadio label:hover {
    background: #161B22 !important;
    color: #E6EDF3 !important;
}
[data-testid="stSidebar"] .stRadio > div { gap: 2px !important; }

/* date inputs in sidebar */
[data-testid="stSidebar"] .stDateInput input,
[data-testid="stSidebar"] .stDateInput label {
    color: #CDD9E5 !important;
    background: #161B22 !important;
    border-color: #30363D !important;
    font-size: 0.8rem !important;
}

/* ─── Main content ─────────────────────────────────────────────────── */
.main .block-container {
    padding: 1.8rem 2.2rem 3rem 2.2rem;
    max-width: 1440px;
    background-color: #0B0F1A;
}

/* ─── Metric cards ─────────────────────────────────────────────────── */
[data-testid="metric-container"] {
    background: #0D1117 !important;
    border: 1px solid #21262D !important;
    border-radius: 10px !important;
    padding: 1rem 1.25rem !important;
    transition: border-color 0.2s;
}
[data-testid="metric-container"]:hover {
    border-color: #388BFD !important;
}
[data-testid="metric-container"] > label,
[data-testid="metric-container"] label {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.62rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.14em !important;
    color: #57A6FF !important;
    font-weight: 400 !important;
}
[data-testid="stMetricValue"] {
    font-size: 1.55rem !important;
    font-weight: 600 !important;
    color: #E6EDF3 !important;
    letter-spacing: -0.02em !important;
}
[data-testid="stMetricDelta"] {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.7rem !important;
}
[data-testid="stMetricDelta"] svg { display: none; }

/* ─── Section divider label ────────────────────────────────────────── */
.sec {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.6rem;
    text-transform: uppercase;
    letter-spacing: 0.18em;
    color: #57A6FF;
    margin: 1.6rem 0 0.6rem 0;
    display: flex;
    align-items: center;
    gap: 10px;
}
.sec::after { content: ''; flex: 1; height: 1px; background: #21262D; }

/* ─── Page headers ─────────────────────────────────────────────────── */
.ptitle {
    font-size: 1.5rem; font-weight: 700;
    color: #E6EDF3; letter-spacing: -0.03em; margin-bottom: 2px;
}
.psub {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.6rem; color: #57A6FF;
    margin-bottom: 1.3rem; letter-spacing: 0.12em;
}

/* ─── Sidebar logo ─────────────────────────────────────────────────── */
.sb-head {
    padding: 1.3rem 1.2rem 1rem 1.2rem;
    border-bottom: 1px solid #21262D;
    margin-bottom: 0.5rem;
}
.sb-logo {
    font-size: 1.05rem; font-weight: 700;
    color: #E6EDF3; letter-spacing: -0.01em;
}
.sb-logo em { font-style: normal; color: #3FB950; }
.sb-tag {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.58rem; color: #30363D;
    letter-spacing: 0.12em; text-transform: uppercase; margin-top: 3px;
}
.sb-sep {
    margin: 0.8rem 1.2rem;
    border: none; border-top: 1px solid #21262D;
}
.sb-sect-label {
    padding: 0 1.2rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.56rem; text-transform: uppercase;
    letter-spacing: 0.15em; color: #388BFD;
    margin-bottom: 0.4rem;
}
.sb-info {
    padding: 0 1.2rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.58rem; color: #30363D; line-height: 2;
}

/* ─── Ticker pill ──────────────────────────────────────────────────── */
.tpill {
    display: inline-block; background: #161B22;
    color: #57A6FF; font-family: 'JetBrains Mono', monospace;
    font-size: 0.76rem; font-weight: 500;
    padding: 0.18rem 0.6rem; border-radius: 4px;
    letter-spacing: 0.08em; margin-right: 0.6rem;
    border: 1px solid #30363D;
}

/* ─── Help / info box ──────────────────────────────────────────────── */
.hbox {
    background: #0D1117;
    border: 1px solid #21262D;
    border-left: 3px solid #388BFD;
    border-radius: 6px;
    padding: 1rem 1.1rem;
    margin: 0.3rem 0 0.8rem 0;
    font-size: 0.79rem;
    color: #8B949E;
    line-height: 1.72;
}
.hbox h4 {
    font-size: 0.78rem; font-weight: 600;
    color: #E6EDF3; margin: 0.8rem 0 0.2rem 0;
    letter-spacing: 0.02em;
}
.hbox h4:first-child { margin-top: 0; }
.hbox strong { color: #CDD9E5; font-weight: 500; }
.hbox code {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.74rem; color: #79C0FF;
    background: #161B22; padding: 1px 5px; border-radius: 3px;
}
.hbox ul { margin: 0.4rem 0 0.4rem 1rem; padding: 0; }
.hbox li { margin-bottom: 0.3rem; }
.hbox .formula {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.76rem; color: #E3B341;
    background: #161B22; padding: 0.4rem 0.7rem;
    border-radius: 4px; margin: 0.5rem 0;
    display: block;
}
.hbox .good { color: #3FB950; font-weight: 500; }
.hbox .bad  { color: #F85149; font-weight: 500; }
.hbox .note {
    margin-top: 0.6rem; padding-top: 0.6rem;
    border-top: 1px solid #21262D;
    font-size: 0.72rem; color: #57A6FF; font-style: italic;
}

/* ─── Active stock mini-card ───────────────────────────────────────── */
.mcard {
    background: #0D1117; border: 1px solid #21262D;
    border-radius: 8px; padding: 0.7rem 0.85rem;
    margin-bottom: 0.5rem; transition: border-color 0.15s;
}
.mcard:hover { border-color: #388BFD; }

/* ─── Stats row ────────────────────────────────────────────────────── */
.stat-row {
    display: flex; justify-content: space-between; align-items: center;
    padding: 7px 0; border-bottom: 1px solid #21262D;
}
.stat-key {
    font-family: 'JetBrains Mono', monospace; font-size: 0.67rem;
    color: #8B949E; text-transform: uppercase; letter-spacing: 0.08em;
}
.stat-val {
    font-family: 'JetBrains Mono', monospace; font-size: 0.82rem;
    color: #E6EDF3; font-weight: 500;
}

/* ─── Scrollbar ────────────────────────────────────────────────────── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: #0B0F1A; }
::-webkit-scrollbar-thumb { background: #21262D; border-radius: 10px; }

/* ─── Widget overrides (main area) ─────────────────────────────────── */
.stSelectbox > div > div,
.stMultiSelect > div > div {
    background: #0D1117 !important;
    border-color: #30363D !important;
    color: #E6EDF3 !important;
}
.stSelectbox label, .stMultiSelect label, .stSlider label {
    color: #57A6FF !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.62rem !important;
    text-transform: uppercase; letter-spacing: 0.12em;
}
/* expander */
[data-testid="stExpander"] {
    background: #0D1117 !important;
    border: 1px solid #21262D !important;
    border-radius: 6px !important;
}
[data-testid="stExpander"] summary {
    color: #57A6FF !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.72rem !important;
}
hr { border-color: #21262D !important; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# COLOUR PALETTE & CHART DEFAULTS
# ══════════════════════════════════════════════════════════════════════════════
BG     = "#0D1117"
PAPER  = "#0D1117"
GRID   = "#161B22"
TICK   = "#30363D"
TXT_H  = "#E6EDF3"   # high-emphasis text
TXT_M  = "#8B949E"   # mid / muted
BLUE   = "#388BFD"   # primary accent
GREEN  = "#3FB950"   # positive / up
RED    = "#F85149"   # negative / down
GOLD   = "#E3B341"   # amber
PURPLE = "#BC8CFF"
CYAN   = "#56D3DD"
ORANGE = "#FFA657"
PALETTE = [BLUE, GREEN, GOLD, CYAN, PURPLE, ORANGE, RED]

HOVER = dict(
    bgcolor="#161B22",
    font=dict(family="JetBrains Mono, monospace", size=11, color="#E6EDF3"),
    bordercolor=BLUE,
)
_AX = dict(
    gridcolor=GRID, linecolor=TICK, tickcolor=TICK, zeroline=False,
    tickfont=dict(family="JetBrains Mono, monospace", size=10, color=TXT_M),
)


def cly(title="", h=300, **kw):
    """Build a dark Plotly layout dict, safely merging xaxis / yaxis overrides."""
    xd = {**_AX}
    yd = {**_AX, "linecolor": "rgba(0,0,0,0)"}
    if "xaxis" in kw: xd.update(kw.pop("xaxis"))
    if "yaxis" in kw: yd.update(kw.pop("yaxis"))
    cfg = dict(
        paper_bgcolor=PAPER, plot_bgcolor=BG,
        font=dict(family="Sora, sans-serif", color=TXT_M, size=11),
        margin=dict(l=10, r=10, t=38 if title else 16, b=10),
        height=h, xaxis=xd, yaxis=yd,
        hoverlabel=HOVER, **kw,
    )
    if title:
        cfg["title"] = dict(
            text=title, x=0, xanchor="left",
            font=dict(size=12, color=TXT_H, family="Sora"),
            pad=dict(l=0, b=10),
        )
    return cfg


def leg():
    return dict(
        orientation="h", x=0, y=1.07,
        font=dict(family="JetBrains Mono, monospace", size=10, color=TXT_M),
        bgcolor="rgba(0,0,0,0)",
    )


# ══════════════════════════════════════════════════════════════════════════════
# DATA
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data(show_spinner=False)
def load_data(path: str) -> pd.DataFrame:
    conn = sqlite3.connect(path)
    df = pd.read_sql("SELECT * FROM companies", conn)
    conn.close()
    df["date"] = pd.to_datetime(df["date"], format="%d/%m/%Y")
    for c in ["haut_du_jour","bas_du_jour","volume_des_echanges",
              "nombre_de_titres_echanges","nombre_de_transactions","ouverture"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df.sort_values("date").reset_index(drop=True)


DB = None
for candidate in ["companies_SQL.db", Path(__file__).parent / "companies_SQL.db"]:
    if Path(candidate).exists():
        DB = str(candidate)
        break

if DB is None:
    st.error("⚠️  `companies_SQL.db` not found — place it next to this script.")
    st.stop()

df  = load_data(DB)
TKN = df[["ticker","instrument"]].drop_duplicates().set_index("ticker")["instrument"].to_dict()
ALL = sorted(df["ticker"].unique())


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def fmt(v, d=1):
    if v is None or (isinstance(v, float) and np.isnan(v)): return "—"
    if abs(v) >= 1e9: return f"{v/1e9:.{d}f} Bn"
    if abs(v) >= 1e6: return f"{v/1e6:.{d}f} M"
    if abs(v) >= 1e3: return f"{v/1e3:.{d}f} K"
    return f"{v:.0f}"


def chg(new, old):
    if not old or old == 0 or pd.isna(old): return None
    p = (new - old) / old * 100
    return f"{'+' if p>=0 else ''}{p:.2f}%"


def sec(label: str):
    st.markdown(f'<div class="sec">{label}</div>', unsafe_allow_html=True)


def hbox(html: str):
    st.markdown(f'<div class="hbox">{html}</div>', unsafe_allow_html=True)


def stat_row(key, val):
    st.markdown(
        f'<div class="stat-row">'
        f'<span class="stat-key">{key}</span>'
        f'<span class="stat-val">{val}</span>'
        f'</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(
        '<div class="sb-head">'
        '<div class="sb-logo">BVC<em> ▪ </em>Markets</div>'
        '<div class="sb-tag">Casablanca Stock Exchange</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Navigation — plain st.radio so Streamlit renders actual clickable buttons
    st.markdown("**Navigate**")
    page = st.radio(
        "Page",
        options=["Market Overview", "Stock Analysis", "Comparison", "Rankings", "Portfolio Builder", "ARIMA Forecast"],
        label_visibility="collapsed",
    )

    st.markdown('<hr class="sb-sep">', unsafe_allow_html=True)
    st.markdown('<div class="sb-sect-label">Time Period</div>', unsafe_allow_html=True)

    min_d   = df["date"].min().date()
    max_d   = df["date"].max().date()
    d_start = st.date_input("From", value=pd.Timestamp("2025-01-01").date(),
                             min_value=min_d, max_value=max_d)
    d_end   = st.date_input("To",   value=max_d, min_value=min_d, max_value=max_d)

    st.markdown('<hr class="sb-sep">', unsafe_allow_html=True)
    st.markdown(
        f'<div class="sb-info">'
        f'{len(df):,} records<br>'
        f'{len(ALL)} listed securities<br>'
        f'{df["date"].min().strftime("%b %Y")} → {df["date"].max().strftime("%b %Y")}'
        f'</div>',
        unsafe_allow_html=True,
    )

# ── Apply period filter ──────────────────────────────────────────────────────
mask = (df["date"].dt.date >= d_start) & (df["date"].dt.date <= d_end)
dff  = df[mask].copy()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE ① — MARKET OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
if page == "Market Overview":

    latest_dt = dff["date"].max()
    prev_dt   = dff[dff["date"] < latest_dt]["date"].max()
    td        = dff[dff["date"] == latest_dt]
    pd_       = dff[dff["date"] == prev_dt]

    total_cap = td["capitalisation"].sum()
    prev_cap  = pd_["capitalisation"].sum()
    total_vol = td["volume_des_echanges"].sum()
    prev_vol  = pd_["volume_des_echanges"].sum()
    n_active  = int(td["dernier_cours"].notna().sum())
    total_tx  = td["nombre_de_transactions"].sum()
    prev_tx   = pd_["nombre_de_transactions"].sum()

    # header row
    hc, dc = st.columns([3, 1])
    with hc:
        st.markdown('<div class="ptitle">Market Overview</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="psub">DATA AS OF {latest_dt.strftime("%B %d, %Y").upper()}'
            f'  ·  CASABLANCA STOCK EXCHANGE</div>', unsafe_allow_html=True)
    with dc:
        s = dff.groupby("date")["capitalisation"].sum()
        if len(s) >= 2:
            p = (s.iloc[-1] - s.iloc[0]) / s.iloc[0] * 100
            c = GREEN if p >= 0 else RED
            st.markdown(
                f"<div style='text-align:right;padding-top:.5rem;'>"
                f"<div style='font-family:JetBrains Mono;font-size:.58rem;"
                f"color:{BLUE};text-transform:uppercase;letter-spacing:.12em;'>Period Return</div>"
                f"<div style='font-size:1.75rem;font-weight:700;color:{c};"
                f"letter-spacing:-.025em;line-height:1.1;'>{'+' if p>=0 else ''}{p:.2f}%</div>"
                f"</div>", unsafe_allow_html=True)

    # ── KPI row ──────────────────────────────────────────────────────────────
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Market Capitalisation", fmt(total_cap), chg(total_cap, prev_cap))
    k2.metric("Trading Volume",        fmt(total_vol), chg(total_vol, prev_vol))
    k3.metric("Active Securities",     f"{n_active} / {len(ALL)}")
    k4.metric("Transactions",
              f"{int(total_tx):,}" if total_tx > 0 else "—",
              chg(total_tx, prev_tx))

    with st.expander("📖  Understanding the KPIs — formulas, interpretation & benchmarks"):
        hbox("""
<h4>📦 Market Capitalisation</h4>
<span class="formula">Market Cap = Σ ( share_price × shares_outstanding )  for all securities</span>
In this dataset it is stored directly in the <code>capitalisation</code> column.
The <strong>total</strong> shown here is the sum across every listed security on the latest trading day.
<ul>
  <li>The delta compares today's total vs. the <em>immediately preceding</em> trading session — not a calendar day.</li>
  <li><strong class="good">Rising cap</strong> = aggregate wealth on the exchange is growing (price increases or new listings).</li>
  <li><strong class="bad">Falling cap</strong> = price declines outweigh any new listings or capital increases.</li>
  <li>BVC total cap typically ranges 650–800 Bn MAD — values far outside that range deserve scrutiny.</li>
</ul>

<h4>💧 Trading Volume</h4>
<span class="formula">Volume (MAD) = Σ volume_des_echanges  for all securities on the latest session</span>
This is the <em>monetary value</em> of shares traded, not the share count.
<ul>
  <li>Higher volume = more market participation = tighter bid-ask spreads = easier execution.</li>
  <li>A spike in volume without a corresponding price move may indicate institutional repositioning.</li>
  <li>Volume significantly <em>below</em> average for several consecutive days can signal reduced market confidence.</li>
</ul>

<h4>✅ Active Securities</h4>
Count of tickers that recorded a non-null <code>dernier_cours</code> (last price) on the latest date,
out of all tickers in the database.
<ul>
  <li>A high ratio (e.g. 70/80) means most securities had at least one trade — normal for a healthy session.</li>
  <li>A low ratio (e.g. 30/80) may indicate a half-day session, public holiday, or broad illiquidity.</li>
</ul>

<h4>🔁 Transactions</h4>
<span class="formula">Transactions = Σ nombre_de_transactions = total number of individual matched orders</span>
Different from volume: two small orders = 2 transactions even if total value is tiny.
<ul>
  <li>High transaction count with low volume = many small retail trades.</li>
  <li>Low transaction count with high volume = fewer but larger institutional block trades.</li>
</ul>
""")

    # ── Market evolution chart ────────────────────────────────────────────────
    sec("Market Evolution — Capitalisation & Volume")
    with st.expander("📖  How to read this chart"):
        hbox("""
<h4>🔵 Blue area (left axis) — Market Capitalisation in Billions MAD</h4>
This line tracks the <em>aggregate market value</em> of all listed companies each day.
<ul>
  <li>A <strong class="good">steadily rising</strong> cap line signals a bull market — investors are pricing companies higher.</li>
  <li>A <strong class="bad">sharp drop</strong> over a few days usually indicates a macro shock (rate hike, geopolitical event) or a major sell-off in the heaviest-weight stocks (ATW, IAM, BCP typically dominate).</li>
  <li>Flat periods reflect low activity — common during Ramadan or summer months on the BVC.</li>
</ul>

<h4>🟠 Orange bars (right axis) — Daily Trading Volume in Millions MAD</h4>
Each bar is the total MAD value of all trades executed on that day.
<ul>
  <li><strong>Volume confirms price moves.</strong> A cap increase backed by high volume is more reliable than one on thin volume.</li>
  <li><strong>Divergence warning:</strong> if cap keeps rising but volume keeps shrinking, the rally may be losing steam.</li>
  <li>Volume spikes mid-week often coincide with earnings releases or index rebalancing.</li>
  <li>Friday sessions on the BVC tend to close early — expect structurally lower Friday bars.</li>
</ul>

<h4>🕵️ What to look for</h4>
<ul>
  <li>Sustained cap growth + rising volume = healthy bull trend.</li>
  <li>Cap drop + volume spike = panic selling / capitulation (can be a buying opportunity).</li>
  <li>Cap drop + low volume = drift lower, no conviction — watch for reversal signals.</li>
</ul>
""")

    daily = dff.groupby("date").agg(
        cap=("capitalisation","sum"),
        vol=("volume_des_echanges","sum"),
    ).reset_index()

    fig_m = make_subplots(specs=[[{"secondary_y": True}]])
    fig_m.add_trace(go.Scatter(
        x=daily["date"], y=daily["cap"]/1e9,
        name="Market Cap (Bn MAD)", mode="lines",
        line=dict(color=BLUE, width=2),
        fill="tozeroy", fillcolor="rgba(56,139,253,0.09)",
        hovertemplate="<b>%{x|%b %d %Y}</b><br>Cap: %{y:.2f} Bn MAD<extra></extra>",
    ), secondary_y=False)
    fig_m.add_trace(go.Bar(
        x=daily["date"], y=daily["vol"]/1e6,
        name="Volume (M MAD)",
        marker_color=ORANGE, marker_opacity=0.5, marker_line_width=0,
        hovertemplate="Vol: %{y:.1f} M MAD<extra></extra>",
    ), secondary_y=True)
    fig_m.update_layout(
        paper_bgcolor=PAPER, plot_bgcolor=BG, height=320, hovermode="x unified",
        margin=dict(l=10,r=10,t=16,b=10), hoverlabel=HOVER, legend=leg(),
    )
    fig_m.update_yaxes(tickformat=".1f", ticksuffix=" Bn", **_AX, secondary_y=False)
    fig_m.update_yaxes(tickformat=".0f", ticksuffix=" M", showgrid=False,
                       linecolor="rgba(0,0,0,0)", zeroline=False,
                       tickfont=dict(family="JetBrains Mono",size=10,color=TXT_M),
                       secondary_y=True)
    fig_m.update_xaxes(**_AX)
    st.plotly_chart(fig_m, width="stretch")

    # ── Heatmap + pie ─────────────────────────────────────────────────────────
    ch, cp = st.columns([3, 1])

    with ch:
        sec("Monthly Capitalisation Heatmap — Top 15 Securities")
        with st.expander("📖  How to read this chart"):
            hbox("""
<h4>What each cell shows</h4>
Each cell is the <strong>average daily capitalisation</strong> of one security (column) during
one calendar month (row), expressed in Billions MAD.
<span class="formula">Cell value = mean( capitalisation ) over all trading days in that month</span>

<h4>Colour scale</h4>
<ul>
  <li><strong style="color:#0E2A45">Dark navy (near black)</strong> = low or zero capitalisation for that month — the company may not have been listed yet, or had no trades.</li>
  <li><strong style="color:#388BFD">Bright blue</strong> = highest capitalisation — the company was at its market peak during that period.</li>
</ul>

<h4>How to use it</h4>
<ul>
  <li>Scan <em>columns</em> (a single stock over time): a column that transitions from dark to bright = the company grew significantly. A sudden drop to dark = sell-off or de-listing.</li>
  <li>Scan <em>rows</em> (a single month across stocks): which stocks dominated that month? Useful for spotting market rotation between sectors.</li>
  <li>A column that is uniformly bright = a dominant, stable large-cap (typically ATW, IAM, BCP on BVC).</li>
</ul>

<div class="note">Only the top 15 securities by average cap are shown to keep the chart readable.</div>
""")
        top15 = dff.groupby("ticker")["capitalisation"].mean().nlargest(15).index.tolist()
        hdf   = dff[dff["ticker"].isin(top15)].copy()
        hdf["month"] = hdf["date"].dt.to_period("M").astype(str)
        pivot = (hdf.groupby(["month","ticker"])["capitalisation"]
                    .mean().unstack(fill_value=np.nan) / 1e9)
        pivot = pivot[[t for t in top15 if t in pivot.columns]]
        fig_h = go.Figure(go.Heatmap(
            z=pivot.values, x=list(pivot.columns), y=pivot.index.tolist(),
            colorscale=[[0,"#0B0F1A"],[0.3,"#0E2A45"],[0.65,"#1B5E8A"],[1,BLUE]],
            hovertemplate="<b>%{x}</b> · %{y}<br>Avg Cap: %{z:.2f} Bn MAD<extra></extra>",
            colorbar=dict(ticksuffix=" Bn", thickness=10, len=0.8, x=1.01,
                          outlinewidth=0,
                          tickfont=dict(family="JetBrains Mono",size=9,color=TXT_M)),
        ))
        fig_h.update_layout(**cly(h=310,
            xaxis=dict(tickangle=-30, tickfont=dict(size=9)),
            yaxis=dict(tickfont=dict(size=9), autorange="reversed")))
        st.plotly_chart(fig_h, width="stretch")

    with cp:
        sec("Trading Activity")
        with st.expander("📖  How to read"):
            hbox("""
<h4>What it measures</h4>
For each security, we compute its <em>activity rate</em>:
<span class="formula">activity_rate = trading_days_with_volume > 0 ÷ total_days_in_period</span>
Then securities are grouped into 4 buckets.

<h4>Buckets</h4>
<ul>
  <li><strong class="good">> 75%</strong> — Liquid, actively traded. You can enter/exit positions easily.</li>
  <li><strong>50–75%</strong> — Moderately active. Occasional gaps between trades.</li>
  <li><strong>25–50%</strong> — Thinly traded. Wider spreads, harder to execute large orders.</li>
  <li><strong class="bad">< 25%</strong> — Illiquid. May trade only a few days per month. High transaction cost risk.</li>
</ul>

<div class="note">For a market order on an illiquid stock, the execution price can be far from the quoted price — always check individual volume before trading.</div>
""")
        act  = dff.groupby("ticker")["volume_des_echanges"].apply(lambda s: (s>0).mean())
        bins = pd.cut(act, bins=[0,0.25,0.5,0.75,1.001],
                      labels=["< 25%","25–50%","50–75%","> 75%"])
        bc   = bins.value_counts().sort_index()
        fig_pie = go.Figure(go.Pie(
            labels=bc.index.tolist(), values=bc.values, hole=0.60,
            marker=dict(colors=["#21262D","#2D3A4A",BLUE,GREEN],
                        line=dict(color="#0B0F1A",width=2)),
            textfont=dict(family="JetBrains Mono",size=10,color=TXT_H),
            hovertemplate="<b>%{label}</b><br>%{value} securities (%{percent})<extra></extra>",
        ))
        fig_pie.update_layout(**cly(h=310, showlegend=True,
            legend=dict(font=dict(family="JetBrains Mono",size=9,color=TXT_M),
                        orientation="v",x=0.5,xanchor="center",y=-0.18,
                        bgcolor="rgba(0,0,0,0)"),
            annotations=[dict(text=f"<b>{len(ALL)}</b>",x=0.5,y=0.5,
                               showarrow=False,
                               font=dict(family="Sora",size=22,color=TXT_H))]))
        st.plotly_chart(fig_pie, width="stretch")

    # ── Most active today ─────────────────────────────────────────────────────
    sec(f"Most Active Securities — {latest_dt.strftime('%B %d, %Y')}")
    with st.expander("📖  What 'most active' means & how to interpret"):
        hbox("""
<h4>Ranking criterion</h4>
Securities are ranked by <code>volume_des_echanges</code> (MAD value traded) on the <em>latest available session</em>.
This is more meaningful than share count because it reflects actual money flowing in/out.

<h4>Price change shown</h4>
<span class="formula">Day change = ( last_price − previous_close ) ÷ previous_close × 100</span>
"Previous close" = the closing price of the immediately preceding <em>trading</em> session (skips weekends and holidays).

<h4>Reading each card</h4>
<ul>
  <li><strong>Ticker</strong> — the exchange symbol.</li>
  <li><strong>Price</strong> — last traded price in MAD.</li>
  <li><strong class="good">Green %</strong> — stock closed higher than yesterday's close.</li>
  <li><strong class="bad">Red %</strong> — stock closed lower.</li>
  <li><strong>Vol</strong> — total MAD value traded in that session.</li>
</ul>

<h4>Why this matters</h4>
High-volume stocks often drive overall index moves. If ATW (Attijariwafa) and IAM (Maroc Telecom)
both appear here with strong gains, expect the overall market cap line to trend up.
""")
    top_t = (td.dropna(subset=["volume_des_echanges"])
               .sort_values("volume_des_echanges", ascending=False)
               .head(10))
    if len(top_t) > 0:
        cols = st.columns(5)
        for i, (_, row) in enumerate(top_t.iterrows()):
            col = cols[i % 5]
            pr  = pd_[pd_["ticker"] == row["ticker"]]
            pc  = pr["dernier_cours"].values[0] if len(pr) > 0 else None
            if pc and pc > 0 and row["dernier_cours"] > 0:
                dc_  = (row["dernier_cours"] - pc) / pc * 100
                cs   = f"{'+' if dc_>=0 else ''}{dc_:.2f}%"
                cc   = GREEN if dc_ >= 0 else RED
            else:
                cs, cc = "—", TXT_M
            col.markdown(
                f"<div class='mcard'>"
                f"<div style='font-family:JetBrains Mono;font-size:.62rem;"
                f"color:{BLUE};letter-spacing:.1em;'>{row['ticker']}</div>"
                f"<div style='font-weight:600;font-size:1.05rem;letter-spacing:-.02em;"
                f"color:{TXT_H};margin:3px 0;'>{row['dernier_cours']:,.0f}"
                f"<span style='font-size:.58rem;font-weight:400;color:{TXT_M};'> MAD</span></div>"
                f"<div style='font-family:JetBrains Mono;font-size:.72rem;"
                f"color:{cc};font-weight:500;'>{cs}</div>"
                f"<div style='font-family:JetBrains Mono;font-size:.6rem;"
                f"color:{TICK};margin-top:5px;'>{fmt(row['volume_des_echanges'])} MAD</div>"
                f"</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE ② — STOCK ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════

    # ── Volume anomaly detector ───────────────────────────────────────────────
    sec("Volume Anomaly Detector")
    with st.expander("📖  What is a volume anomaly and why does it matter?"):
        hbox("""
<h4>Definition</h4>
A <strong>volume anomaly</strong> occurs when a security's daily trading volume is significantly
higher than its own recent average — a statistical outlier in that stock's own history.
<span class="formula">Z-score = ( V_today − μ_20d ) ÷ σ_20d</span>
where μ_20d = 20-day mean volume, σ_20d = 20-day standard deviation of volume.
A Z-score above <strong>2.0</strong> means today's volume is more than 2 standard deviations
above the stock's recent norm — statistically unusual (top ~2.3% of days).

<h4>Why traders watch this</h4>
<ul>
  <li><strong>Earnings releases</strong> — companies reporting results almost always spike in volume.</li>
  <li><strong>M&A rumours / takeover bids</strong> — unusual volume in a small-cap before an announcement is a classic signal.</li>
  <li><strong>Index rebalancing</strong> — passive funds must buy/sell in bulk when constituents change.</li>
  <li><strong>Insider activity</strong> (indirect signal) — not conclusive, but persistent anomalies in illiquid stocks warrant scrutiny.</li>
</ul>

<h4>How to use this table</h4>
<ul>
  <li>Z-score 2–3: Notable. Worth investigating.</li>
  <li>Z-score > 3: Very unusual. High probability of a material event.</li>
  <li>Cross-check with the price change: volume spike + large price move = confirmed event. Volume spike + flat price = potential accumulation before a move.</li>
</ul>

<div class="note">This uses the 20 most recent sessions to compute the baseline. For thinly traded stocks the baseline itself may be unreliable — treat Z-scores for illiquid names with caution.</div>
""")

    # compute rolling 20-day mean and std for each ticker, find today's anomalies
    anomaly_rows = []
    for tkr, g in dff.groupby("ticker"):
        g = g.sort_values("date")
        g = g[g["volume_des_echanges"] > 0]
        if len(g) < 22:
            continue
        g = g.copy()
        g["vol_mean20"] = g["volume_des_echanges"].shift(1).rolling(20).mean()
        g["vol_std20"]  = g["volume_des_echanges"].shift(1).rolling(20).std()
        last = g.iloc[-1]
        if pd.isna(last["vol_mean20"]) or last["vol_std20"] == 0:
            continue
        z = (last["volume_des_echanges"] - last["vol_mean20"]) / last["vol_std20"]
        if z > 1.8:
            # price change
            if len(g) >= 2:
                prev_c = g.iloc[-2]["dernier_cours"]
                curr_c = last["dernier_cours"]
                pchg   = (curr_c - prev_c) / prev_c * 100 if prev_c and prev_c > 0 else np.nan
            else:
                pchg = np.nan
            anomaly_rows.append(dict(
                Ticker=tkr,
                Name=TKN.get(tkr, tkr)[:25],
                Date=last["date"].strftime("%d %b %Y"),
                Volume=fmt(last["volume_des_echanges"]),
                Mean20=fmt(last["vol_mean20"]),
                ZScore=round(z, 2),
                PriceChg=pchg,
            ))

    if anomaly_rows:
        adf = pd.DataFrame(anomaly_rows).sort_values("ZScore", ascending=False).head(15)
        # render as styled HTML table
        rows_html = ""
        for _, r in adf.iterrows():
            pc_str  = f"{r['PriceChg']:+.2f}%" if not np.isnan(r["PriceChg"]) else "—"
            pc_col  = GREEN if (not np.isnan(r["PriceChg"]) and r["PriceChg"] >= 0) else RED
            z_col   = GOLD if r["ZScore"] < 3 else "#FF6B6B"
            rows_html += (
                f"<tr>"
                f"<td style='font-family:JetBrains Mono;font-size:.75rem;color:{BLUE};'>{r['Ticker']}</td>"
                f"<td style='font-size:.75rem;color:{TXT_M};'>{r['Name']}</td>"
                f"<td style='font-family:JetBrains Mono;font-size:.75rem;color:{TXT_M};'>{r['Date']}</td>"
                f"<td style='font-family:JetBrains Mono;font-size:.75rem;color:{TXT_H};'>{r['Volume']}</td>"
                f"<td style='font-family:JetBrains Mono;font-size:.75rem;color:{TXT_M};'>{r['Mean20']}</td>"
                f"<td style='font-family:JetBrains Mono;font-size:.78rem;color:{z_col};font-weight:600;'>{r['ZScore']}</td>"
                f"<td style='font-family:JetBrains Mono;font-size:.75rem;color:{pc_col};'>{pc_str}</td>"
                f"</tr>"
            )
        st.markdown(
            f"<table style='width:100%;border-collapse:collapse;background:#0D1117;"
            f"border:1px solid #21262D;border-radius:8px;overflow:hidden;'>"
            f"<thead><tr style='background:#161B22;'>"
            f"{''.join(f'<th style="font-family:JetBrains Mono;font-size:.6rem;text-transform:uppercase;letter-spacing:.1em;color:{BLUE};padding:8px 12px;text-align:left;">{h}</th>' for h in ['Ticker','Name','Date','Volume','20d Avg','Z-Score','Price Chg'])}"
            f"</tr></thead><tbody>"
            f"{''.join(f"<tr style='border-top:1px solid #21262D;padding:4px 0;'>{rows_html[rows_html.index(f'<tr>', rows_html.index(f'<tr>')+1) if False else 0:]}")  if False else rows_html}"
            f"</tbody></table>",
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"<div class='hbox'>No significant volume anomalies detected in the selected period "
            f"(threshold: Z-score &gt; 1.8).</div>",
            unsafe_allow_html=True
        )

    # ── Cap tier breakdown ────────────────────────────────────────────────────
    sec("Market Cap Tier Breakdown")
    with st.expander("📖  What are cap tiers and how are they defined?"):
        hbox("""
<h4>Cap tier definitions (BVC-adapted)</h4>
Unlike global markets where large-cap starts at $10 Bn USD, BVC operates on a smaller scale.
These thresholds are calibrated to the Moroccan market:
<ul>
  <li><strong style="color:#388BFD">Large-cap  (&gt; 10 Bn MAD)</strong>: Systemically important. ATW, IAM, BCP etc. Dominate the index. Highest analyst coverage. Most liquid.</li>
  <li><strong style="color:#3FB950">Mid-cap  (2–10 Bn MAD)</strong>: Growing companies with moderate liquidity. Often the sweet spot for active investors.</li>
  <li><strong style="color:#E3B341">Small-cap  (500 M – 2 Bn MAD)</strong>: Higher growth potential, lower liquidity, wider bid-ask spreads.</li>
  <li><strong style="color:#FFA657">Micro-cap  (&lt; 500 M MAD)</strong>: Speculative. Very illiquid. A single institutional order can move the price significantly.</li>
</ul>

<h4>How to use the chart</h4>
<ul>
  <li>The <strong>donut</strong> shows the number of companies in each tier — useful for understanding market structure.</li>
  <li>The <strong>bar chart</strong> shows total capitalisation per tier — shows where the money actually is.</li>
  <li>A market where 4 large-caps hold 60% of total cap is more concentrated (and therefore more volatile at the index level) than one where cap is spread across many mid-caps.</li>
</ul>
""")

    latest_caps = dff[dff["date"]==dff["date"].max()].groupby("ticker")["capitalisation"].last().dropna()
    def cap_tier(v):
        if v >= 10e9: return "Large-cap >10 Bn"
        if v >= 2e9:  return "Mid-cap 2-10 Bn"
        if v >= 500e6:return "Small-cap 0.5-2 Bn"
        return "Micro-cap <0.5 Bn"
    tier_colors = {"Large-cap >10 Bn": BLUE, "Mid-cap 2-10 Bn": GREEN, "Small-cap 0.5-2 Bn": GOLD, "Micro-cap <0.5 Bn": ORANGE}
    tiers = latest_caps.apply(cap_tier)
    tier_count = tiers.value_counts()
    tier_cap   = latest_caps.groupby(tiers).sum() / 1e9
    order = ["Large-cap >10 Bn", "Mid-cap 2-10 Bn", "Small-cap 0.5-2 Bn", "Micro-cap <0.5 Bn"]
    tier_count = tier_count.reindex([t for t in order if t in tier_count.index])
    tier_cap   = tier_cap.reindex([t for t in order if t in tier_cap.index])

    ct1, ct2 = st.columns(2)
    with ct1:
        fig_tc = go.Figure(go.Pie(
            labels=[t.replace("\n"," ") for t in tier_count.index],
            values=tier_count.values, hole=0.55,
            marker=dict(colors=[tier_colors[t] for t in tier_count.index],
                        line=dict(color="#0B0F1A", width=2)),
            textfont=dict(family="JetBrains Mono", size=10, color=TXT_H),
            hovertemplate="<b>%{label}</b><br>%{value} companies (%{percent})<extra></extra>",
        ))
        fig_tc.update_layout(**cly(h=280, showlegend=True,
            legend=dict(font=dict(family="JetBrains Mono", size=9, color=TXT_M),
                        bgcolor="rgba(0,0,0,0)"),
            title="Companies per tier",
            annotations=[dict(text=f"<b>{len(latest_caps)}</b>", x=0.5, y=0.5,
                               showarrow=False,
                               font=dict(family="Sora", size=20, color=TXT_H))]))
        st.plotly_chart(fig_tc, width="stretch")

    with ct2:
        fig_tb = go.Figure(go.Bar(
            x=[t.replace("\n"," ") for t in tier_cap.index],
            y=tier_cap.values,
            marker_color=[tier_colors[t] for t in tier_cap.index],
            marker_line_width=0, marker_opacity=0.85,
            text=[f"{v:.1f} Bn" for v in tier_cap.values],
            textfont=dict(family="JetBrains Mono", size=10, color=TXT_H),
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>%{y:.1f} Bn MAD<extra></extra>",
        ))
        fig_tb.update_layout(**cly(h=280, title="Total cap per tier (Bn MAD)",
            yaxis=dict(tickformat=".0f", ticksuffix=" Bn"),
            xaxis=dict(tickfont=dict(size=10))))
        st.plotly_chart(fig_tb, width="stretch")


elif page == "Stock Analysis":

    c1, c2, c3 = st.columns([2, 2, 1])
    with c1:
        ticker = st.selectbox("Security", ALL,
            format_func=lambda t: f"{t}  —  {TKN.get(t,t)}",
            index=ALL.index("ATW") if "ATW" in ALL else 0)
    with c2:
        ctype = st.selectbox("Chart type", ["Candlestick","Line","Area"])
    with c3:
        # Full database history for this ticker — ignore sidebar date filter
        _full_ticker = df[df["ticker"]==ticker].sort_values("date")
        _max_years = max(1, int(
            (_full_ticker["date"].max() - _full_ticker["date"].min()).days / 365.25
        ) + 1)
        chart_years = st.number_input(
            "Years of history",
            min_value=0.25,
            max_value=float(_max_years),
            value=min(float(_max_years), 2.0),
            step=0.25,
            format="%.2f",
            help="How many years of price history to display. "
                 "0.25 = 3 months, 1 = one year, etc. "
                 "Uses the full database — not limited by the sidebar date filter.",
        )

    # Slice full ticker history to the requested window
    _all_ticker = df[df["ticker"]==ticker].sort_values("date").dropna(subset=["dernier_cours"])
    if len(_all_ticker) == 0:
        st.warning("No price data found for this security.")
        st.stop()
    _cutoff = _all_ticker["date"].max() - pd.DateOffset(years=int(chart_years),
              days=int((chart_years % 1) * 365.25))
    tdf  = _all_ticker[_all_ticker["date"] >= _cutoff].copy()
    name = TKN.get(ticker, ticker)

    if tdf.empty:
        st.warning("No data available for the selected years window.")
        st.stop()

    valid   = tdf["dernier_cours"].dropna()
    lv      = valid.iloc[-1]
    fv      = valid.iloc[0]
    perf    = (lv - fv) / fv * 100 if fv else 0
    pc      = GREEN if perf >= 0 else RED
    ret     = valid.pct_change().dropna() * 100
    vol_ann = ret.std() * np.sqrt(252) if len(ret) > 5 else None
    mu_ann  = ret.mean() * 252          if len(ret) > 5 else None
    sharpe  = mu_ann / vol_ann          if vol_ann and vol_ann > 0 else None

    # header
    st.markdown(
        f"<div style='display:flex;align-items:baseline;gap:12px;margin-bottom:5px;'>"
        f"<span class='tpill'>{ticker}</span>"
        f"<span style='font-size:1.35rem;font-weight:700;letter-spacing:-.025em;"
        f"color:{TXT_H};'>{name}</span></div>"
        f"<div style='display:flex;align-items:baseline;gap:14px;margin-bottom:1.3rem;'>"
        f"<span style='font-size:2.1rem;font-weight:700;letter-spacing:-.03em;"
        f"color:{TXT_H};'>{lv:,.2f} "
        f"<span style='font-size:.8rem;font-weight:400;color:{TXT_M};'>MAD</span></span>"
        f"<span style='font-family:JetBrains Mono;font-size:.9rem;color:{pc};"
        f"font-weight:500;'>{'+' if perf>=0 else ''}{perf:.2f}%</span>"
        f"<span style='font-family:JetBrains Mono;font-size:.65rem;color:{TXT_M};'>"
        f"return over {chart_years:.2g}y window</span></div>",
        unsafe_allow_html=True)

    k1,k2,k3,k4,k5 = st.columns(5)
    k1.metric(f"High ({chart_years:.2g}y)",  f"{valid.max():,.2f}")
    k2.metric(f"Low ({chart_years:.2g}y)",   f"{valid.min():,.2f}")
    k3.metric("Mean Price",     f"{valid.mean():,.2f}")
    k4.metric("Annualised Vol", f"{vol_ann:.1f}%" if vol_ann else "—")
    k5.metric("Sharpe Ratio",   f"{sharpe:.2f}"   if sharpe  else "—")

    with st.expander("📖  All KPIs explained — formulas & how to interpret"):
        hbox("""
<h4>📈 Period Return  (shown in the header)</h4>
<span class="formula">Return = ( P_last − P_first ) ÷ P_first × 100</span>
This is a simple price return, not total return (dividends are not included in this dataset).
<ul>
  <li>Measures how much the stock has gained or lost <em>since the first trading day in your selected period</em>.</li>
  <li>Changing the sidebar date range will change this number — always note the period when comparing stocks.</li>
</ul>

<h4>📊 Period High / Low</h4>
Highest and lowest <code>dernier_cours</code> (last price) recorded during the selected period.
These are <em>not necessarily</em> the 52-week high/low unless your date range covers exactly 52 weeks.
<ul>
  <li>If the current price is near the <strong class="good">Period High</strong>, the stock is in a strong uptrend — but may face resistance at that level.</li>
  <li>If near the <strong class="bad">Period Low</strong>, the stock may be oversold — but could also be in a downtrend with no floor yet.</li>
</ul>

<h4>📉 Annualised Volatility  (σ)</h4>
<span class="formula">σ_annual = σ_daily × √252</span>
where <code>σ_daily</code> = standard deviation of daily log-returns, and 252 = trading days per year.
<ul>
  <li><strong>Low (&lt; 10%)</strong>: stable, bond-like behaviour. Common for utilities on the BVC.</li>
  <li><strong>Medium (10–25%)</strong>: typical equity range. Most BVC blue-chips fall here.</li>
  <li><strong class="bad">High (&gt; 25%)</strong>: highly uncertain price path. Higher potential reward but also higher drawdown risk.</li>
  <li>Volatility is <em>symmetric</em> — it captures both upside and downside swings.</li>
</ul>

<h4>⚖️ Sharpe Ratio</h4>
<span class="formula">Sharpe = μ_annual ÷ σ_annual  (risk-free rate = 0 for simplicity)</span>
Measures <em>return per unit of risk</em>.
<ul>
  <li><strong class="good">> 1.0</strong>: excellent risk-adjusted return — every 1% of risk earned more than 1% of return.</li>
  <li><strong>0 – 1.0</strong>: positive but modest. Acceptable for a single stock holding.</li>
  <li><strong class="bad">< 0</strong>: the stock returned less than the risk-free rate (or lost money). Holding cash would have been better.</li>
  <li>Note: a short period with a volatile bull run can produce a misleadingly high Sharpe. Always check the full history.</li>
</ul>
""")

    # ── Price chart ───────────────────────────────────────────────────────────
    sec("Price Chart")
    with st.expander("📖  How to read every element of this chart"):
        hbox("""
<h4>Candlestick mode (OHLC)</h4>
Each candle represents <strong>one trading session</strong>:
<ul>
  <li><strong>Body</strong> — the rectangle between Open and Close price.</li>
  <li><strong>Upper wick</strong> — extends to the session High. A long upper wick means buyers pushed the price up but sellers drove it back down by close — bearish sign.</li>
  <li><strong>Lower wick</strong> — extends to the session Low. A long lower wick means sellers pushed price down but buyers recovered it — bullish sign.</li>
  <li><span style="color:#3FB950">■</span> <strong class="good">Green candle</strong>: Close > Open. Buyers dominated the session.</li>
  <li><span style="color:#F85149">■</span> <strong class="bad">Red candle</strong>: Close &lt; Open. Sellers dominated the session.</li>
</ul>

<h4>🟠 MM20 — 20-day Simple Moving Average (short-term trend)</h4>
<span class="formula">MM20_t = average( Close_{t}, Close_{t-1}, …, Close_{t-19} )</span>
<ul>
  <li>Acts as <strong>dynamic support</strong> in an uptrend — price often bounces off MM20 before continuing higher.</li>
  <li>If price breaks below MM20 with conviction, it signals a potential trend reversal.</li>
  <li>Useful for short-term swing traders (days to weeks).</li>
</ul>

<h4>🟡 MM50 — 50-day Simple Moving Average (medium-term trend)</h4>
<span class="formula">MM50_t = average( Close_{t}, …, Close_{t-49} )</span>
<ul>
  <li>Slower and smoother than MM20. Price below MM50 = medium-term downtrend.</li>
  <li><strong>Golden Cross</strong>: MM20 crosses <em>above</em> MM50 → classic bullish signal, often precedes sustained uptrends.</li>
  <li><strong>Death Cross</strong>: MM20 crosses <em>below</em> MM50 → classic bearish signal.</li>
</ul>

<h4>Volume panel (bottom)</h4>
<ul>
  <li><span style="color:#3FB950">■</span> Green bars = up-day (Close ≥ Open). <span style="color:#F85149">■</span> Red bars = down-day.</li>
  <li><strong>High volume on a green candle</strong> = strong buying conviction. Confirms the uptrend.</li>
  <li><strong>High volume on a red candle</strong> = strong selling pressure or panic. Watch for follow-through.</li>
  <li><strong>Low volume on any candle</strong> = low conviction — move may not sustain.</li>
</ul>

<div class="note">BVC is a relatively low-volume market. A "high volume" day here may look small vs. European exchanges — always compare to the stock's own historical average, not absolute numbers.</div>
""")

    candle   = tdf.dropna(subset=["ouverture","dernier_cours","haut_du_jour","bas_du_jour"])
    has_ohlc = len(candle) > 5

    fig_p = make_subplots(rows=2, cols=1, shared_xaxes=True,
                          row_heights=[0.72,0.28], vertical_spacing=0.02)

    if ctype == "Candlestick" and has_ohlc:
        fig_p.add_trace(go.Candlestick(
            x=candle["date"],
            open=candle["ouverture"], high=candle["haut_du_jour"],
            low=candle["bas_du_jour"], close=candle["dernier_cours"],
            increasing=dict(line=dict(color=GREEN,width=1),
                            fillcolor="rgba(63,185,80,0.85)"),
            decreasing=dict(line=dict(color=RED,  width=1),
                            fillcolor="rgba(248,81,73,0.85)"),
            whiskerwidth=0.3, name="OHLC",
            hovertext=candle.apply(lambda r:
                f"O:{r['ouverture']:,.2f}  H:{r['haut_du_jour']:,.2f}<br>"
                f"L:{r['bas_du_jour']:,.2f}  C:{r['dernier_cours']:,.2f}", axis=1),
            hoverinfo="text+x",
        ), row=1, col=1)
    elif ctype == "Area":
        fig_p.add_trace(go.Scatter(
            x=tdf["date"], y=tdf["dernier_cours"], mode="lines",
            line=dict(color=BLUE,width=2),
            fill="tozeroy", fillcolor="rgba(56,139,253,0.09)",
            name="Close",
            hovertemplate="%{x|%b %d %Y}<br>%{y:,.2f} MAD<extra></extra>",
        ), row=1, col=1)
    else:
        fig_p.add_trace(go.Scatter(
            x=tdf["date"], y=tdf["dernier_cours"], mode="lines",
            line=dict(color=BLUE,width=2), name="Close",
            hovertemplate="%{x|%b %d %Y}<br>%{y:,.2f} MAD<extra></extra>",
        ), row=1, col=1)

    src = candle if (ctype=="Candlestick" and has_ohlc) else tdf
    for w, c, d, lbl in [(20,ORANGE,"dot","MM20"),(50,GOLD,"dash","MM50")]:
        if len(src) >= w:
            ma = src["dernier_cours"].rolling(w).mean()
            fig_p.add_trace(go.Scatter(
                x=src["date"], y=ma, mode="lines", name=lbl,
                line=dict(color=c,width=1.5,dash=d),
                hovertemplate=f"{lbl}: %{{y:,.2f}}<extra></extra>",
            ), row=1, col=1)

    vc = []
    for _, r in src.iterrows():
        o = r["ouverture"] if not pd.isna(r["ouverture"]) else r["dernier_cours"]
        vc.append("rgba(63,185,80,0.55)" if r["dernier_cours"]>=o
                  else "rgba(248,81,73,0.55)")
    fig_p.add_trace(go.Bar(
        x=src["date"], y=src["volume_des_echanges"],
        marker_color=vc, marker_line_width=0, name="Volume",
        hovertemplate="Vol: %{y:,.0f} MAD<extra></extra>",
    ), row=2, col=1)

    ax = {**_AX}
    fig_p.update_layout(
        paper_bgcolor=PAPER, plot_bgcolor=BG,
        height=500, hovermode="x unified",
        xaxis_rangeslider_visible=False,
        legend=leg(), hoverlabel=HOVER,
        margin=dict(l=10,r=10,t=30,b=10),
        xaxis=dict(**ax), yaxis=dict(**ax,tickformat=",.0f"),
        xaxis2=dict(**ax), yaxis2=dict(**ax,tickformat=",.0f"),
    )
    st.plotly_chart(fig_p, width="stretch")

    # ── Returns + stats ───────────────────────────────────────────────────────
    cd, cs_ = st.columns([3,2])
    with cd:
        sec("Daily Returns Distribution")
        with st.expander("📖  How to read this histogram"):
            hbox("""
<h4>What each bar means</h4>
<span class="formula">Daily return r_t = ( P_t − P_{t−1} ) ÷ P_{t−1} × 100</span>
Each bar counts how many days the stock earned a return in that specific percentage range.
For example, a tall bar at "+0.5%" means many days the stock gained between 0.5% and ~0.75%.

<h4>Key visual elements</h4>
<ul>
  <li><strong>Centre of mass</strong> — where most bars cluster. If this is to the right of zero, the stock drifts up over time.</li>
  <li><strong>🟠 Orange dashed line (μ)</strong> — the mean daily return. Even a small positive mean (e.g. +0.05%) compounds to significant gains annually.</li>
  <li><strong>Width of distribution</strong> — narrow = low volatility (stable stock). Wide = high volatility (big swings).</li>
  <li><strong>Tails</strong> — bars far left (large negative days) and far right (large positive days). Fat tails = higher crash and spike risk than a normal distribution would predict.</li>
</ul>

<h4>Skewness at a glance</h4>
<ul>
  <li>Distribution <strong class="good">leaning right</strong> = more frequent positive days, positive skew — historically favourable.</li>
  <li>Distribution <strong class="bad">leaning left</strong> = occasional large losses outweigh frequent small gains, negative skew — common for momentum stocks.</li>
</ul>
""")
        if len(ret) > 5:
            fig_r = go.Figure()
            fig_r.add_trace(go.Histogram(
                x=ret, nbinsx=40,
                marker_color=BLUE, marker_opacity=0.8, marker_line_width=0,
                hovertemplate="%{x:.2f}%: %{y} days<extra></extra>",
            ))
            fig_r.add_vline(x=0, line_color=TICK, line_width=1.5)
            fig_r.add_vline(x=ret.mean(), line_dash="dash", line_color=ORANGE,
                            line_width=1.5,
                            annotation_text=f" μ={ret.mean():.3f}%",
                            annotation_font=dict(family="JetBrains Mono",size=9,color=ORANGE))
            fig_r.update_layout(**cly(h=240,xaxis=dict(ticksuffix="%")))
            st.plotly_chart(fig_r, width="stretch")

    with cs_:
        sec("Return Statistics")
        with st.expander("📖  Statistical glossary"):
            hbox("""
<h4>Std Dev (σ)</h4>
Average deviation of daily returns from the mean.
Higher σ = more variable daily moves = more uncertainty.

<h4>Skewness</h4>
<ul>
  <li><strong class="good">Positive</strong>: rare large gains, frequent small losses — lottery-like upside.</li>
  <li><strong class="bad">Negative</strong>: rare large losses, frequent small gains — crash risk hidden in the left tail. Most equities have slightly negative skew.</li>
</ul>

<h4>Kurtosis (excess)</h4>
Measures <em>fat-tailedness</em> vs. a normal distribution (kurtosis = 0).
<ul>
  <li><strong class="bad">Positive (leptokurtic)</strong>: more extreme days than a normal distribution predicts. A reading of +3 means crashes and spikes happen ~3× more often than expected.</li>
  <li>Negative: flatter distribution, fewer extreme days.</li>
</ul>
""")
        for k, v in [
            ("Min Return",  f"{ret.min():.3f}%"),
            ("Max Return",  f"{ret.max():.3f}%"),
            ("Mean",        f"{ret.mean():.3f}%"),
            ("Median",      f"{ret.median():.3f}%"),
            ("Std Dev",     f"{ret.std():.3f}%"),
            ("Skewness",    f"{ret.skew():.3f}"),
            ("Kurtosis",    f"{ret.kurtosis():.3f}"),
        ]:
            stat_row(k, v)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE ③ — COMPARISON
# ══════════════════════════════════════════════════════════════════════════════

    # ── Bollinger Bands ───────────────────────────────────────────────────────
    sec("Bollinger Bands — Volatility Envelope")
    with st.expander("📖  What are Bollinger Bands and how do you trade them?"):
        hbox("""
<h4>Construction</h4>
Three lines plotted around the closing price:
<span class="formula">Middle Band  = MM20 (20-day Simple Moving Average)</span>
<span class="formula">Upper Band   = MM20 + 2 × σ_20d</span>
<span class="formula">Lower Band   = MM20 − 2 × σ_20d</span>
where σ_20d is the 20-day rolling standard deviation of closing prices.
By definition, roughly <strong>95% of price action</strong> falls inside the bands under normal conditions.

<h4>Band Width = Volatility gauge</h4>
<ul>
  <li><strong>Wide bands</strong>: high recent volatility — the market is uncertain about the stock's fair value.</li>
  <li><strong>Narrow bands (squeeze)</strong>: low recent volatility — energy is coiling. A squeeze often precedes a large directional move (up or down). The direction is not predicted by the squeeze itself.</li>
</ul>

<h4>Price vs. band signals</h4>
<ul>
  <li><strong>Price touches Upper Band</strong>: the stock is statistically "expensive" relative to its recent range. Often a short-term overbought signal — but in a strong uptrend, price can "walk the band" for weeks.</li>
  <li><strong>Price touches Lower Band</strong>: statistically "cheap" relative to recent range. Potential oversold condition — but in a downtrend, it can keep hugging the lower band.</li>
  <li><strong>W-bottom pattern</strong>: price touches lower band, bounces, pulls back but doesn't break the band again → bullish reversal signal.</li>
  <li><strong>M-top pattern</strong>: price touches upper band, pulls back, re-tests but fails to break through → bearish reversal signal.</li>
</ul>

<div class="note">Bollinger Bands are a relative measure — they adapt to each stock's own volatility. A band touch means something different for a stock with 5% daily swings vs one with 0.5% daily swings.</div>
""")
    if len(tdf) >= 21:
        bb = tdf[["date","dernier_cours"]].copy().dropna()
        bb["mm20"]  = bb["dernier_cours"].rolling(20).mean()
        bb["std20"] = bb["dernier_cours"].rolling(20).std()
        bb["upper"] = bb["mm20"] + 2 * bb["std20"]
        bb["lower"] = bb["mm20"] - 2 * bb["std20"]
        bb["bw"]    = (bb["upper"] - bb["lower"]) / bb["mm20"] * 100  # bandwidth %

        fig_bb = make_subplots(rows=2, cols=1, shared_xaxes=True,
                               row_heights=[0.70, 0.30], vertical_spacing=0.03)
        # Shaded band
        fig_bb.add_trace(go.Scatter(
            x=pd.concat([bb["date"], bb["date"][::-1]]),
            y=pd.concat([bb["upper"], bb["lower"][::-1]]),
            fill="toself", fillcolor="rgba(56,139,253,0.07)",
            line=dict(width=0), showlegend=False, hoverinfo="skip",
        ), row=1, col=1)
        fig_bb.add_trace(go.Scatter(x=bb["date"], y=bb["upper"], mode="lines", name="Upper Band",
            line=dict(color=BLUE, width=1, dash="dot"),
            hovertemplate="Upper: %{y:,.2f}<extra></extra>"), row=1, col=1)
        fig_bb.add_trace(go.Scatter(x=bb["date"], y=bb["mm20"], mode="lines", name="MM20",
            line=dict(color=ORANGE, width=1.5),
            hovertemplate="MM20: %{y:,.2f}<extra></extra>"), row=1, col=1)
        fig_bb.add_trace(go.Scatter(x=bb["date"], y=bb["lower"], mode="lines", name="Lower Band",
            line=dict(color=RED, width=1, dash="dot"),
            hovertemplate="Lower: %{y:,.2f}<extra></extra>"), row=1, col=1)
        fig_bb.add_trace(go.Scatter(x=bb["date"], y=bb["dernier_cours"], mode="lines", name="Close",
            line=dict(color=TXT_H, width=1.8),
            hovertemplate="%{x|%b %d %Y}<br>Close: %{y:,.2f}<extra></extra>"), row=1, col=1)
        # Bandwidth
        fig_bb.add_trace(go.Scatter(x=bb["date"], y=bb["bw"], mode="lines", name="Band Width %",
            line=dict(color=CYAN, width=1.5), fill="tozeroy",
            fillcolor="rgba(86,211,221,0.08)",
            hovertemplate="BW: %{y:.2f}%<extra></extra>"), row=2, col=1)

        ax = {**_AX}
        fig_bb.update_layout(
            paper_bgcolor=PAPER, plot_bgcolor=BG, height=440,
            hovermode="x unified", legend=leg(), hoverlabel=HOVER,
            margin=dict(l=10,r=10,t=20,b=10),
            xaxis=dict(**ax), yaxis=dict(**ax, tickformat=",.0f"),
            xaxis2=dict(**ax), yaxis2=dict(**ax, tickformat=".1f", ticksuffix="%"),
        )
        st.plotly_chart(fig_bb, width="stretch")
    else:
        st.info("Need at least 21 sessions to compute Bollinger Bands.")

    # ── RSI ───────────────────────────────────────────────────────────────────
    sec("RSI — Relative Strength Index (14-day)")
    with st.expander("📖  What is the RSI and how do you interpret it?"):
        hbox("""
<h4>Formula</h4>
<span class="formula">RSI = 100 − [ 100 ÷ ( 1 + RS ) ]</span>
where <code>RS = Average Gain over 14 days ÷ Average Loss over 14 days</code>
(Wilder smoothing used for the rolling average).
The RSI always stays between <strong>0 and 100</strong>.

<h4>The three zones</h4>
<ul>
  <li><strong class="bad">RSI &gt; 70 — Overbought zone</strong>: The stock has risen strongly relative to recent history. Not a sell signal on its own — in a strong uptrend, RSI can stay above 70 for weeks. Look for a <em>failure swing</em>: RSI peaks above 70, drops below 70, rallies again but fails to reach 70 → bearish divergence signal.</li>
  <li><strong>RSI 30–70 — Neutral zone</strong>: Normal trading range. 50 acts as a midline — RSI crossing above 50 confirms bullish momentum; below 50 confirms bearish momentum.</li>
  <li><strong class="good">RSI &lt; 30 — Oversold zone</strong>: The stock has fallen hard. Can signal a buying opportunity, but in a strong downtrend, RSI can stay below 30. Look for a bullish failure swing or a positive divergence (price makes new low, RSI does not).</li>
</ul>

<h4>RSI Divergence — the most powerful signal</h4>
<ul>
  <li><strong>Bullish divergence</strong>: Price makes a lower low, but RSI makes a higher low → downward momentum is weakening. Potential reversal up.</li>
  <li><strong>Bearish divergence</strong>: Price makes a higher high, but RSI makes a lower high → upward momentum is weakening. Potential reversal down.</li>
</ul>

<div class="note">RSI works best in range-bound markets. In strong trending markets, overbought/oversold readings alone are poor trade signals — always combine with price action and volume.</div>
""")
    if len(tdf) >= 16:
        rsi_src = tdf[["date","dernier_cours"]].dropna().copy()
        delta_r = rsi_src["dernier_cours"].diff()
        gain = delta_r.clip(lower=0)
        loss = (-delta_r).clip(lower=0)
        avg_gain = gain.ewm(com=13, adjust=False).mean()
        avg_loss = loss.ewm(com=13, adjust=False).mean()
        rs  = avg_gain / avg_loss.replace(0, np.nan)
        rsi_src["rsi"] = 100 - (100 / (1 + rs))

        fig_rsi = go.Figure()
        # coloured fill zones
        fig_rsi.add_hrect(y0=70, y1=100, fillcolor="rgba(248,81,73,0.06)",
                          line_width=0, annotation_text="Overbought",
                          annotation_position="top right",
                          annotation_font=dict(size=9, color=RED,
                                               family="JetBrains Mono"))
        fig_rsi.add_hrect(y0=0, y1=30, fillcolor="rgba(63,185,80,0.06)",
                          line_width=0, annotation_text="Oversold",
                          annotation_position="bottom right",
                          annotation_font=dict(size=9, color=GREEN,
                                               family="JetBrains Mono"))
        fig_rsi.add_hline(y=70, line_color=RED,   line_width=1, line_dash="dot")
        fig_rsi.add_hline(y=50, line_color=TICK,  line_width=1, line_dash="dot")
        fig_rsi.add_hline(y=30, line_color=GREEN, line_width=1, line_dash="dot")

        # colour RSI line dynamically
        rsi_vals = rsi_src["rsi"].fillna(50)
        fig_rsi.add_trace(go.Scatter(
            x=rsi_src["date"], y=rsi_vals,
            mode="lines", name="RSI(14)",
            line=dict(color=PURPLE, width=2),
            hovertemplate="%{x|%b %d %Y}<br>RSI: %{y:.1f}<extra></extra>",
        ))
        fig_rsi.update_layout(**cly(h=280,
            yaxis=dict(range=[0,100], tickvals=[0,30,50,70,100]),
            hovermode="x unified", legend=leg()))
        st.plotly_chart(fig_rsi, width="stretch")

    # ── Drawdown ──────────────────────────────────────────────────────────────
    sec("Drawdown Analysis")
    with st.expander("📖  What is drawdown and why is it critical for risk management?"):
        hbox("""
<h4>Definition</h4>
Drawdown measures how far the price has fallen from its most recent <strong>peak</strong>:
<span class="formula">Drawdown_t = ( P_t − Peak_t ) ÷ Peak_t × 100</span>
where <code>Peak_t = max( P_0, P_1, …, P_t )</code> — the highest price reached up to day t.
Drawdown is always ≤ 0. A drawdown of −20% means the stock is 20% below its last all-time high.

<h4>Maximum Drawdown (MDD)</h4>
<span class="formula">MDD = min( Drawdown_t )  over the entire period</span>
This is the single worst peak-to-trough decline experienced.
It answers: <em>"If you had bought at the worst possible moment, how much would you have lost?"</em>
<ul>
  <li><strong class="good">MDD &gt; −10%</strong>: Low drawdown. Very stable price path.</li>
  <li><strong>MDD −10% to −30%</strong>: Normal equity range. Requires psychological resilience to hold through.</li>
  <li><strong class="bad">MDD &lt; −30%</strong>: Severe drawdown. Either a major market crisis or company-specific trouble.</li>
</ul>

<h4>Recovery time</h4>
A drawdown is not just about the magnitude — it is also about how long it takes to recover.
A −20% drawdown that recovers in 2 months is very different from one that takes 3 years.
Watch for drawdowns that flatten at a low level (no recovery) — this may signal permanent capital impairment.

<h4>Reading the chart</h4>
<ul>
  <li>The area is filled red when the stock is underwater relative to its recent peak.</li>
  <li>When the line returns to 0%, the stock has made a new all-time high for the period.</li>
  <li>Prolonged periods far below 0% are periods of sustained pain for buy-and-hold investors.</li>
</ul>
""")
    if len(valid) >= 5:
        dd_prices = valid.reset_index(drop=True)
        rolling_max = dd_prices.cummax()
        dd = (dd_prices - rolling_max) / rolling_max * 100
        dd_dates = tdf.dropna(subset=["dernier_cours"])["date"].reset_index(drop=True)
        mdd = dd.min()
        mdd_idx = dd.idxmin()

        fig_dd = go.Figure()
        fig_dd.add_trace(go.Scatter(
            x=dd_dates, y=dd,
            mode="lines", name="Drawdown",
            line=dict(color=RED, width=1.5),
            fill="tozeroy", fillcolor="rgba(248,81,73,0.12)",
            hovertemplate="%{x|%b %d %Y}<br>DD: %{y:.2f}%<extra></extra>",
        ))
        # Mark max drawdown point
        if mdd_idx < len(dd_dates):
            fig_dd.add_trace(go.Scatter(
                x=[dd_dates.iloc[mdd_idx]], y=[mdd],
                mode="markers+text",
                text=[f" MDD: {mdd:.1f}%"],
                textposition="bottom right",
                textfont=dict(family="JetBrains Mono", size=9, color=RED),
                marker=dict(size=8, color=RED, symbol="circle"),
                name="Max Drawdown", showlegend=False,
                hovertemplate=f"Max Drawdown: {mdd:.2f}%<extra></extra>",
            ))
        fig_dd.add_hline(y=0, line_color=TICK, line_width=1)
        fig_dd.update_layout(**cly(h=260,
            yaxis=dict(ticksuffix="%"),
            hovermode="x unified"))
        st.plotly_chart(fig_dd, width="stretch")

        # MDD summary strip
        st.markdown(
            f"<div style='display:flex;gap:2rem;padding:.8rem 1rem;"
            f"background:#0D1117;border:1px solid #21262D;border-radius:8px;"
            f"margin-top:.5rem;'>"
            f"<div><div style='font-family:JetBrains Mono;font-size:.58rem;"
            f"color:{BLUE};text-transform:uppercase;letter-spacing:.1em;'>Max Drawdown</div>"
            f"<div style='font-size:1.3rem;font-weight:700;color:{RED};"
            f"letter-spacing:-.02em;'>{mdd:.2f}%</div></div>"
            f"<div><div style='font-family:JetBrains Mono;font-size:.58rem;"
            f"color:{BLUE};text-transform:uppercase;letter-spacing:.1em;'>Drawdown Date</div>"
            f"<div style='font-family:JetBrains Mono;font-size:1rem;font-weight:600;"
            f"color:{TXT_H};'>{dd_dates.iloc[mdd_idx].strftime('%d %b %Y') if mdd_idx < len(dd_dates) else '—'}</div></div>"
            f"<div><div style='font-family:JetBrains Mono;font-size:.58rem;"
            f"color:{BLUE};text-transform:uppercase;letter-spacing:.1em;'>Current DD</div>"
            f"<div style='font-family:JetBrains Mono;font-size:1rem;font-weight:600;"
            f"color:{RED if dd.iloc[-1] < -1 else GREEN};'>{dd.iloc[-1]:.2f}%</div></div>"
            f"<div><div style='font-family:JetBrains Mono;font-size:.58rem;"
            f"color:{BLUE};text-transform:uppercase;letter-spacing:.1em;'>Sessions analysed</div>"
            f"<div style='font-family:JetBrains Mono;font-size:1rem;font-weight:600;"
            f"color:{TXT_H};'>{len(dd)}</div></div>"
            f"</div>",
            unsafe_allow_html=True
        )


elif page == "Comparison":

    st.markdown('<div class="ptitle">Securities Comparison</div>', unsafe_allow_html=True)
    st.markdown('<div class="psub">RELATIVE PERFORMANCE · CORRELATION · RISK-RETURN</div>',
                unsafe_allow_html=True)

    defaults = [t for t in ["ATW","BCP","CIH","BOA"] if t in ALL][:4]

    # ── Controls row ─────────────────────────────────────────────────────────
    cmp_c1, cmp_c2 = st.columns([4, 1])
    with cmp_c1:
        selected = st.multiselect(
            "Select securities to compare (select any number)",
            ALL,
            format_func=lambda t: f"{t}  —  {TKN.get(t,t)}",
            default=defaults or ALL[:3],
        )
    with cmp_c2:
        # Compute max available years across selected tickers (or all tickers as fallback)
        _ref_tickers = selected if selected else ALL
        _cmp_full = df[df["ticker"].isin(_ref_tickers)].sort_values("date")
        _cmp_max_years = max(1, int(
            (_cmp_full["date"].max() - _cmp_full["date"].min()).days / 365.25
        ) + 1) if len(_cmp_full) > 0 else 3
        cmp_years = st.number_input(
            "Years of history",
            min_value=0.25,
            max_value=float(_cmp_max_years),
            value=min(float(_cmp_max_years), 2.0),
            step=0.25,
            format="%.2f",
            help="How many years back to display for all selected securities. "
                 "Uses the full database — not limited by the sidebar date filter.",
        )

    if len(selected) < 2:
        st.info("Select at least 2 securities.")
        st.stop()

    # Pull from full df (ignore sidebar filter), slice to the years window
    _cmp_cutoff = df["date"].max() - pd.DateOffset(
        years=int(cmp_years), days=int((cmp_years % 1) * 365.25)
    )
    cdf = (df[df["ticker"].isin(selected) & (df["date"] >= _cmp_cutoff)]
             .sort_values("date")
             .copy())

    # ── Normalised performance ────────────────────────────────────────────────
    sec(f"Normalised Performance — Indexed to 100  ({cmp_years:.2g}y window)")
    with st.expander("📖  How to read this chart"):
        hbox("""
<h4>What normalisation does</h4>
Every security's price is re-scaled so its first value in the period equals <strong>100</strong>:
<span class="formula">Indexed_t = ( P_t ÷ P_first ) × 100</span>
This removes the distortion of different price levels (a stock at 4,000 MAD vs one at 40 MAD).
Now you compare <em>percentage returns</em> directly.

<h4>Reading the chart</h4>
<ul>
  <li>A line at <strong>120</strong> means +20% since the start of the period.</li>
  <li>A line at <strong>85</strong> means −15% since the start.</li>
  <li>The <strong>dashed grey line at 100</strong> is the "break-even" reference — above it = profit, below = loss.</li>
  <li>Lines that <em>diverge</em> over time tell a clearer story than prices that may barely change in absolute terms.</li>
</ul>

<h4>Pitfalls</h4>
<ul>
  <li>Start date matters enormously — the same stock can look like a winner or a loser depending on when you start the period.</li>
  <li>This is price return only. If one stock paid a large dividend during the period, it will appear to underperform even if total return (price + dividend) was higher.</li>
</ul>
""")
    fig_n = go.Figure()
    for i, t in enumerate(selected):
        td = cdf[cdf["ticker"]==t].sort_values("date")
        v  = td["dernier_cours"].dropna()
        if len(v) < 2: continue
        fig_n.add_trace(go.Scatter(
            x=td["date"], y=v/v.iloc[0]*100,
            mode="lines", name=t,
            line=dict(color=PALETTE[i%len(PALETTE)], width=max(0.8, 2 - len(selected)*0.05)),
            hovertemplate=f"<b>{t}</b>  %{{y:.1f}}<extra></extra>",
        ))
    fig_n.add_hline(y=100, line_dash="dot", line_color=TICK, line_width=1.5)
    fig_n.update_layout(**cly(h=340, hovermode="x unified", legend=leg()))
    st.plotly_chart(fig_n, width="stretch")

    cc_, cv_ = st.columns([1,2])

    with cc_:
        sec(f"Return Correlation Matrix  ({cmp_years:.2g}y window)")
        with st.expander("📖  How to read"):
            hbox("""
<h4>What is Pearson correlation r?</h4>
<span class="formula">r(A,B) ranges from −1 to +1</span>
<ul>
  <li><strong class="good">r = +1</strong>: A and B move in perfect lockstep — no diversification benefit.</li>
  <li><strong>r = 0</strong>: completely independent moves — maximum diversification benefit.</li>
  <li><strong class="bad">r = −1</strong>: perfect inverse — when A rises, B falls (rare for equities in the same market).</li>
</ul>

<h4>Colour scale</h4>
<ul>
  <li><span style="color:#388BFD">■ Blue</span> = high positive correlation (stocks move together).</li>
  <li><span style="color:#161B22">■ Dark</span> = near zero (independent).</li>
  <li><span style="color:#F85149">■ Red</span> = negative correlation.</li>
</ul>

<h4>Portfolio insight</h4>
For a two-stock portfolio, combining stocks with r &lt; 0.5 significantly reduces portfolio volatility
without sacrificing expected return. Within BVC, bank stocks tend to be highly correlated with each other
(r > 0.7) — adding a non-bank reduces risk more effectively.

<div class="note">Only the lower triangle is shown to avoid redundancy — the matrix is symmetric.</div>
""")
        pivot = (cdf.pivot_table(index="date",columns="ticker",values="dernier_cours")
                    .pct_change().dropna())
        if pivot.shape[0]>5 and pivot.shape[1]>1:
            corr = pivot.corr()
            mask = np.tril(np.ones_like(corr.values,dtype=bool))
            zm   = np.where(mask, corr.values, np.nan)
            fig_c = go.Figure(go.Heatmap(
                z=zm, x=corr.columns.tolist(), y=corr.index.tolist(),
                colorscale=[[0,RED],[0.5,"#161B22"],[1,BLUE]],
                zmin=-1, zmax=1,
                text=np.where(mask,corr.round(2).values.astype(str),""),
                texttemplate="%{text}",
                textfont=dict(family="JetBrains Mono", size=max(7, 11 - len(selected)), color=TXT_H),
                hovertemplate="<b>%{x} × %{y}</b><br>r = %{z:.3f}<extra></extra>",
                showscale=False,
            ))
            _corr_h = max(280, min(60 * len(selected), 600))
            fig_c.update_layout(**cly(h=_corr_h,
                xaxis=dict(tickangle=-20,side="bottom"),
                yaxis=dict(autorange="reversed")))
            st.plotly_chart(fig_c, width="stretch")

    with cv_:
        sec(f"Monthly Volume Comparison  ({cmp_years:.2g}y window)")
        with st.expander("📖  How to read"):
            hbox("""
<h4>What it shows</h4>
Total MAD value traded (<code>volume_des_echanges</code>) summed per calendar month for each stock.

<h4>Why volume matters for comparison</h4>
<ul>
  <li>A stock with consistently high monthly volume is <strong>liquid</strong> — large orders can be executed without moving the price much.</li>
  <li>An illiquid stock may show great returns in a chart, but in practice you might not be able to buy or sell a meaningful position without slippage.</li>
  <li><strong>Volume divergence</strong>: if two stocks track each other in price but one has 10× the volume, the high-volume one is the safer trade.</li>
</ul>

<h4>Reading the grouped bars</h4>
Each colour = one security. Bars within the same month group are side-by-side.
A month where one bar dominates = that stock attracted unusual attention that month
(earnings release, rumour, index inclusion).
""")
        cdf["month"] = cdf["date"].dt.to_period("M").astype(str)
        vm = cdf.groupby(["month","ticker"])["volume_des_echanges"].sum().reset_index()
        fig_v = go.Figure()
        for i, t in enumerate(selected):
            td_ = vm[vm["ticker"]==t]
            fig_v.add_trace(go.Bar(
                x=td_["month"], y=td_["volume_des_echanges"]/1e6,
                name=t, marker_color=PALETTE[i%len(PALETTE)],
                marker_line_width=0, marker_opacity=0.85,
                hovertemplate=f"<b>{t}</b>  %{{y:.2f}} M MAD<extra></extra>",
            ))
        fig_v.update_layout(**cly(h=300, barmode="group",
            yaxis=dict(tickformat=".1f",ticksuffix=" M"), legend=leg()))
        st.plotly_chart(fig_v, width="stretch")

    sec(f"Risk vs. Return — Annualised  ({cmp_years:.2g}y window)")
    with st.expander("📖  How to read the Risk-Return scatter"):
        hbox("""
<h4>Axes</h4>
<ul>
  <li><strong>X-axis (Risk)</strong>: annualised volatility = <code>σ_daily × √252</code>. Further right = more volatile = more uncertain future price path.</li>
  <li><strong>Y-axis (Return)</strong>: annualised mean return = <code>μ_daily × 252</code>. Higher = better average annual performance over the selected period.</li>
</ul>

<h4>The four quadrants</h4>
<ul>
  <li><strong class="good">Top-left</strong>: High return, Low risk — the "ideal" quadrant. Rare for individual stocks.</li>
  <li><strong>Top-right</strong>: High return, High risk — speculative. Big upside but also big drawdown potential.</li>
  <li><strong>Bottom-left</strong>: Low return, Low risk — conservative. Suitable for capital preservation.</li>
  <li><strong class="bad">Bottom-right</strong>: Low return, High risk — worst quadrant. You are not being compensated for the risk taken.</li>
</ul>

<h4>The dashed line at y=0</h4>
Separates positive from negative annualised returns. Stocks below this line lost money on average over the selected period.

<h4>Capital Market Line (CML) intuition</h4>
A "rational" portfolio should sit as high and as far left as possible.
If you can draw a steep upward-sloping line from the origin to a cluster of stocks,
those stocks have a better Sharpe Ratio than stocks below that line.
""")
    rr = []
    for t in selected:
        td_ = cdf[cdf["ticker"]==t].sort_values("date")
        r_  = td_["dernier_cours"].pct_change().dropna()*100
        if len(r_)<5: continue
        rr.append(dict(ticker=t, ret=r_.mean()*252, risk=r_.std()*np.sqrt(252)))
    if rr:
        rr_df = pd.DataFrame(rr)
        fig_rr = go.Figure()
        for i, row in rr_df.iterrows():
            fig_rr.add_trace(go.Scatter(
                x=[row["risk"]], y=[row["ret"]],
                mode="markers+text", text=[row["ticker"]],
                textposition="top center",
                textfont=dict(family="JetBrains Mono",size=10,
                              color=PALETTE[i%len(PALETTE)]),
                marker=dict(size=14, color=PALETTE[i%len(PALETTE)],
                            line=dict(color="#0B0F1A",width=2)),
                name=row["ticker"],
                hovertemplate=(f"<b>{row['ticker']}</b><br>"
                               f"Return: {row['ret']:.1f}%<br>"
                               f"Risk: {row['risk']:.1f}%<extra></extra>"),
            ))
        fig_rr.add_hline(y=0, line_dash="dot", line_color=TICK)
        fig_rr.update_layout(**cly(h=320, showlegend=False,
            xaxis=dict(title="Annualised Risk (%)",ticksuffix="%"),
            yaxis=dict(title="Annualised Return (%)",ticksuffix="%")))
        st.plotly_chart(fig_rr, width="stretch")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE ④ — RANKINGS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Rankings":

    st.markdown('<div class="ptitle">Rankings & Leaderboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="psub">CAPITALISATIONS · VOLUMES · PERIOD PERFORMANCE</div>',
                unsafe_allow_html=True)

    _max_n = len(dff["ticker"].unique())
    n = st.slider("Number of securities to display", 5, _max_n, min(15, _max_n))
    ldf = dff[dff["date"] == dff["date"].max()]

    c1_, c2_ = st.columns(2)

    with c1_:
        sec("Top Market Capitalisations")
        with st.expander("📖  About this ranking"):
            hbox("""
<h4>How it is calculated</h4>
<span class="formula">Market Cap = share_price × total_shares_outstanding</span>
Taken from the <code>capitalisation</code> column on the most recent trading session in your period.

<h4>Why it matters</h4>
<ul>
  <li>Market cap determines a stock's <strong>weight in the index</strong>. On the BVC, the top 5 stocks by cap often represent 50%+ of the index — a move in ATW or IAM moves the whole market.</li>
  <li>Larger cap = more analyst coverage, more institutional ownership, generally more liquidity.</li>
  <li><strong>Mega-cap (&gt;20 Bn MAD)</strong>: systemically important, market-moving.</li>
  <li><strong>Mid-cap (2–20 Bn MAD)</strong>: growing companies, less liquidity.</li>
  <li><strong>Small-cap (&lt;2 Bn MAD)</strong>: high growth potential but also high risk and low liquidity.</li>
</ul>
""")
        tc = (ldf.groupby("ticker")["capitalisation"].last()
                       .dropna().nlargest(n).reset_index())
        fig_c = go.Figure(go.Bar(
            x=tc["capitalisation"]/1e9, y=tc["ticker"], orientation="h",
            marker=dict(color=tc["capitalisation"],
                        colorscale=[[0,"#0E2A45"],[1,BLUE]],
                        showscale=False, line=dict(width=0)),
            text=[f"{v:.1f} Bn" for v in tc["capitalisation"]/1e9],
            textfont=dict(family="JetBrains Mono",size=9,color=TXT_M),
            textposition="outside", cliponaxis=False,
            hovertemplate="<b>%{y}</b><br>%{x:.1f} Bn MAD<extra></extra>",
        ))
        _ch = max(320, min(26 * n, 1200))
        fig_c.update_layout(**cly(h=_ch,
            xaxis=dict(tickformat=".0f",ticksuffix=" Bn",showgrid=False),
            yaxis=dict(autorange="reversed",
                       tickfont=dict(family="JetBrains Mono",size=10))))
        st.plotly_chart(fig_c, width="stretch")

    with c2_:
        sec("Top Trading Volumes (Period Total)")
        with st.expander("📖  About this ranking"):
            hbox("""
<h4>What is measured</h4>
Cumulative <code>volume_des_echanges</code> (MAD) summed over the entire selected period.
This reflects <strong>total liquidity</strong> — how much money flowed through each stock.

<h4>Volume ≠ Cap rank</h4>
A stock can be high-cap but low-volume (thinly traded float) or low-cap but high-volume
(high retail interest, or a recent IPO with speculative trading).
Compare both rankings to find mismatches:
<ul>
  <li>High cap + High volume = core liquid holding, suitable for large positions.</li>
  <li>High cap + Low volume = illiquid blue-chip, difficult to trade in size.</li>
  <li>Low cap + High volume = possible speculative bubble or corporate event (M&A, dividend announcement).</li>
</ul>
""")
        tv = dff.groupby("ticker")["volume_des_echanges"].sum()\
                  .nlargest(n).reset_index()
        fig_v = go.Figure(go.Bar(
            x=tv["volume_des_echanges"]/1e6, y=tv["ticker"], orientation="h",
            marker=dict(color=tv["volume_des_echanges"],
                        colorscale=[[0,"#1A2A1A"],[1,GREEN]],
                        showscale=False, line=dict(width=0)),
            text=[f"{v:.0f} M" for v in tv["volume_des_echanges"]/1e6],
            textfont=dict(family="JetBrains Mono",size=9,color=TXT_M),
            textposition="outside", cliponaxis=False,
            hovertemplate="<b>%{y}</b><br>%{x:.0f} M MAD<extra></extra>",
        ))
        _vh = max(320, min(26 * n, 1200))
        fig_v.update_layout(**cly(h=_vh,
            xaxis=dict(tickformat=".0f",ticksuffix=" M",showgrid=False),
            yaxis=dict(autorange="reversed",
                       tickfont=dict(family="JetBrains Mono",size=10))))
        st.plotly_chart(fig_v, width="stretch")

    sec("Period Performance — Top Gainers & Losers")
    with st.expander("📖  How performance is calculated & how to read the chart"):
        hbox("""
<h4>Formula</h4>
<span class="formula">Return (%) = ( P_last − P_first ) ÷ P_first × 100</span>
where <code>P_first</code> = earliest closing price and <code>P_last</code> = most recent closing price
in the selected period.

<h4>What the chart shows</h4>
The top N gainers (green, extending right) and top N losers (red, extending left) are plotted
on the same axis with a vertical zero line in the centre.
<ul>
  <li><strong>Bar length</strong> = magnitude of return. A bar reaching +50% means the stock doubled in half the selected period.</li>
  <li><strong>Colour opacity</strong> scales with magnitude — the biggest movers are the most saturated.</li>
</ul>

<h4>Limitations</h4>
<ul>
  <li>Simple price return ignores dividends.</li>
  <li>A stock showing +200% may have had very low volume — a single large trade can distort the price artificially on an illiquid market.</li>
  <li>Always cross-check extreme movers with the volume ranking to confirm the move was backed by real trading activity.</li>
</ul>
""")
    perfs = []
    for t, g in dff.groupby("ticker"):
        v = g.sort_values("date")["dernier_cours"].dropna()
        if len(v)>=2:
            perfs.append(dict(ticker=t,
                              perf=(v.iloc[-1]-v.iloc[0])/v.iloc[0]*100,
                              vol=g["volume_des_echanges"].sum()))
    pf   = pd.DataFrame(perfs).sort_values("perf",ascending=False)
    both = (pd.concat([pf.head(n),pf.tail(n)])
              .drop_duplicates("ticker")
              .sort_values("perf",ascending=False))

    fig_pf = go.Figure(go.Bar(
        x=both["perf"], y=both["ticker"], orientation="h",
        marker=dict(
            color=[f"rgba(63,185,80,{min(.9,.3+abs(v)/80)})" if v>=0
                   else f"rgba(248,81,73,{min(.9,.3+abs(v)/80)})"
                   for v in both["perf"]],
            line=dict(width=0)),
        text=[f"{v:+.1f}%" for v in both["perf"]],
        textfont=dict(family="JetBrains Mono",size=9,
                      color=[GREEN if v>=0 else RED for v in both["perf"]]),
        textposition="outside", cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>%{x:.2f}%<extra></extra>",
    ))
    fig_pf.add_vline(x=0, line_color=TICK, line_width=1.5)
    _pf_h = max(400, min(28 * len(both), 1400))
    fig_pf.update_layout(**cly(h=_pf_h,
        xaxis=dict(ticksuffix="%",zeroline=False),
        yaxis=dict(autorange="reversed",
                   tickfont=dict(family="JetBrains Mono",size=10))))
    st.plotly_chart(fig_pf, width="stretch")

    sec("Market Map — Cap × Return × Volume")
    with st.expander("📖  How to read the bubble chart"):
        hbox("""
<h4>Three dimensions in one view</h4>
<ul>
  <li><strong>X-axis (log scale)</strong> — Total volume over the period in M MAD. Log scale is used because volume spans several orders of magnitude. Moving right = more liquid.</li>
  <li><strong>Y-axis</strong> — Price performance (%) over the selected period. Above zero = gains, below = losses.</li>
  <li><strong>Bubble size</strong> — Market capitalisation on the last day. Larger bubble = larger company. The biggest bubbles are the most index-influential.</li>
  <li><strong>Colour</strong> — Also encodes performance: <span class="good">green = positive</span>, <span class="bad">red = negative</span>. The colour bar on the right is the scale.</li>
</ul>

<h4>Most interesting regions</h4>
<ul>
  <li><strong class="good">Top-right</strong>: Large, liquid stocks with strong returns — the "sweet spot" for institutional investors.</li>
  <li><strong>Top-left</strong>: Small illiquid stocks with strong returns — potential value plays but hard to trade in size.</li>
  <li><strong class="bad">Bottom-right</strong>: Large, liquid stocks with poor returns — the market's biggest drags, but easier to short (if permitted).</li>
  <li><strong>Bottom-left</strong>: Small illiquid losers — avoid unless you have a very specific thesis.</li>
</ul>

<div class="note">The X-axis uses a logarithmic scale. Equal visual distances represent proportional changes in volume, not absolute — a stock at x=100 has 10× the volume of one at x=10, not 90 more units.</div>
""")
    bubble = pf.merge(ldf[["ticker","capitalisation"]].dropna(),
                      on="ticker",how="left").dropna(subset=["capitalisation"])
    bubble["size"] = (bubble["capitalisation"]/bubble["capitalisation"].max()*50).clip(lower=5)

    fig_b = go.Figure(go.Scatter(
        x=bubble["vol"]/1e6, y=bubble["perf"],
        mode="markers+text", text=bubble["ticker"],
        textposition="top center",
        textfont=dict(family="JetBrains Mono",size=8,color=TXT_M),
        marker=dict(
            size=bubble["size"],
            color=bubble["perf"],
            colorscale=[[0,RED],[0.5,"#161B22"],[1,GREEN]],
            cmin=-30, cmax=30, showscale=True,
            colorbar=dict(
                title=dict(text="Return %",
                           font=dict(family="JetBrains Mono",size=9,color=TXT_M)),
                tickfont=dict(family="JetBrains Mono",size=9,color=TXT_M),
                ticksuffix="%", thickness=8, len=0.7, outlinewidth=0),
            line=dict(color="#0B0F1A",width=1),
        ),
        hovertemplate="<b>%{text}</b><br>Volume: %{x:.1f} M MAD<br>Return: %{y:.2f}%<extra></extra>",
    ))
    fig_b.add_hline(y=0, line_dash="dot", line_color=TICK, line_width=1.5)
    fig_b.update_layout(**cly(h=450,
        xaxis=dict(title="Total Volume (M MAD)",type="log",ticksuffix=" M"),
        yaxis=dict(title="Performance (%)",ticksuffix="%")))
    st.plotly_chart(fig_b, width="stretch")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE ⑤ — PORTFOLIO BUILDER
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Portfolio Builder":

    st.markdown('<div class="ptitle">Portfolio Builder</div>', unsafe_allow_html=True)
    st.markdown('<div class="psub">WEIGHT YOUR HOLDINGS · SIMULATE RETURNS · ANALYSE RISK</div>',
                unsafe_allow_html=True)

    with st.expander("📖  How this tool works — full methodology"):
        hbox("""
<h4>What this page does</h4>
You pick a set of securities and assign each a portfolio weight (%).
The tool then simulates the <strong>weighted portfolio return</strong> over the selected period,
computes risk metrics, and compares the portfolio against each individual holding.

<h4>Portfolio return calculation</h4>
<span class="formula">R_portfolio_t = Σ ( w_i × r_i_t )  for all securities i</span>
where <code>w_i</code> = weight of security i (must sum to 100%), and
<code>r_i_t</code> = daily return of security i on day t.
This is a <strong>daily rebalanced</strong> portfolio — weights are assumed constant each day.
In practice, real portfolios drift and are only periodically rebalanced.

<h4>Risk metrics shown</h4>
<ul>
  <li><strong>Annualised Return</strong>: <code>μ_daily × 252</code></li>
  <li><strong>Annualised Volatility</strong>: <code>σ_daily × √252</code></li>
  <li><strong>Sharpe Ratio</strong>: <code>μ_annual ÷ σ_annual</code> (risk-free = 0)</li>
  <li><strong>Max Drawdown</strong>: worst peak-to-trough decline of the cumulative portfolio value</li>
  <li><strong>Calmar Ratio</strong>: <code>Annualised Return ÷ |Max Drawdown|</code> — measures return per unit of drawdown risk. Higher is better. A ratio &gt; 1 means the annual return exceeded the worst drawdown.</li>
</ul>

<h4>Diversification effect</h4>
Because securities are not perfectly correlated (r &lt; 1), a portfolio's volatility is
<em>less than</em> the weighted average of individual volatilities:
<span class="formula">σ_portfolio ≤ Σ ( w_i × σ_i )</span>
The difference between the weighted-average vol and portfolio vol is the
<strong>diversification benefit</strong> — shown explicitly in this tool.

<div class="note">This is a simplified back-test. It does not account for transaction costs, bid-ask spreads, taxes, dividends, or position size constraints. Past performance does not guarantee future results.</div>
""")

    # ── Security & weight selection ───────────────────────────────────────────
    sec("Step 1 — Select Securities")
    port_tickers = st.multiselect(
        "Add securities to your portfolio",
        ALL,
        format_func=lambda t: f"{t}  —  {TKN.get(t,t)}",
        default=[t for t in ["ATW","BCP","IAM","CIH"] if t in ALL][:4],
        max_selections=10,
    )

    if len(port_tickers) < 2:
        st.info("Add at least 2 securities to build a portfolio.")
        st.stop()

    sec("Step 2 — Set Weights (%)")
    st.markdown(
        '<div class="hbox">Adjust the sliders so weights sum to <strong>100%</strong>. '
        'The tool will warn you if they do not.</div>',
        unsafe_allow_html=True
    )

    default_w = round(100 / len(port_tickers), 1)
    weights = {}
    w_cols  = st.columns(min(len(port_tickers), 5))
    for i, t in enumerate(port_tickers):
        col = w_cols[i % len(w_cols)]
        weights[t] = col.slider(
            f"{t}", 0.0, 100.0, default_w, 0.5,
            key=f"w_{t}",
        )

    total_w = sum(weights.values())
    if abs(total_w - 100) > 0.5:
        st.warning(f"⚠️  Weights sum to **{total_w:.1f}%** — please adjust to reach exactly 100%.")
    else:
        st.success(f"✅  Weights sum to {total_w:.1f}%")

    # ── Build portfolio returns ───────────────────────────────────────────────
    sec("Step 3 — Portfolio Performance")

    price_pivot = (dff[dff["ticker"].isin(port_tickers)]
                     .pivot_table(index="date", columns="ticker", values="dernier_cours")
                     .sort_index()
                     .dropna(how="all"))

    # forward-fill minor gaps, then drop remaining NaN rows
    price_pivot = price_pivot.ffill().dropna()

    if len(price_pivot) < 5:
        st.warning("Not enough overlapping data for the selected securities and period.")
        st.stop()

    daily_ret = price_pivot.pct_change().dropna()
    w_arr     = np.array([weights[t] / 100 for t in daily_ret.columns])
    port_ret  = daily_ret.values @ w_arr  # shape (n_days,)

    # cumulative wealth index
    cum_port  = (1 + port_ret).cumprod()
    cum_dates = daily_ret.index

    # individual cumulative returns (normalised to 1)
    cum_indiv = (1 + daily_ret).cumprod()

    # ── Cumulative return chart ───────────────────────────────────────────────
    with st.expander("📖  How to read the cumulative return chart"):
        hbox("""
<h4>Wealth index (base = 1.0)</h4>
Starting from 1.0 (= 100% of invested capital), the chart shows how 1 MAD invested
at the start of the period would have grown (or shrunk) over time.
<span class="formula">Wealth_t = Π ( 1 + r_τ )  for τ = 1 to t</span>
A value of 1.25 means a 25% cumulative gain. A value of 0.80 means a 20% loss.

<h4>Portfolio line vs. individual lines</h4>
The <strong>white portfolio line</strong> is the blended result of your weights.
Individual security lines show what a 100% concentration in each would have delivered.
<ul>
  <li>If the portfolio line is <em>above</em> all individual lines at some point, weighting helped — you would have done better than any single holding.</li>
  <li>If the portfolio hugs one dominant holding, that security is driving all the results — consider whether that concentration is intentional.</li>
</ul>
""")

    fig_pw = go.Figure()
    for i, t in enumerate(daily_ret.columns):
        fig_pw.add_trace(go.Scatter(
            x=cum_dates, y=cum_indiv[t],
            mode="lines", name=f"{t} ({weights[t]:.0f}%)",
            line=dict(color=PALETTE[i % len(PALETTE)], width=1.4, dash="dot"),
            opacity=0.6,
            hovertemplate=f"<b>{t}</b>  %{{y:.3f}}<extra></extra>",
        ))
    fig_pw.add_trace(go.Scatter(
        x=cum_dates, y=cum_port,
        mode="lines", name="Portfolio",
        line=dict(color=TXT_H, width=2.5),
        hovertemplate="<b>Portfolio</b>  %{y:.3f}<extra></extra>",
    ))
    fig_pw.add_hline(y=1, line_dash="dot", line_color=TICK, line_width=1.2)
    fig_pw.update_layout(**cly(h=360, hovermode="x unified", legend=leg()))
    st.plotly_chart(fig_pw, width="stretch")

    # ── Portfolio metrics ─────────────────────────────────────────────────────
    sec("Risk & Return Metrics")

    port_mu  = port_ret.mean() * 252
    port_sig = port_ret.std()  * np.sqrt(252)
    port_sr  = port_mu / port_sig if port_sig > 0 else np.nan

    # portfolio drawdown
    cum_arr  = cum_port
    roll_max = np.maximum.accumulate(cum_arr)
    dd_arr   = (cum_arr - roll_max) / roll_max * 100
    port_mdd = dd_arr.min()
    calmar   = port_mu / abs(port_mdd) * 100 if port_mdd != 0 else np.nan

    # weighted-avg vol (no diversification)
    indiv_sigs = {t: daily_ret[t].std() * np.sqrt(252) * 100 for t in daily_ret.columns}
    w_avg_vol  = sum(weights[t]/100 * indiv_sigs[t] for t in daily_ret.columns)
    div_benefit = w_avg_vol - port_sig * 100

    km1,km2,km3,km4,km5 = st.columns(5)
    km1.metric("Annualised Return",    f"{port_mu*100:.2f}%")
    km2.metric("Annualised Volatility",f"{port_sig*100:.2f}%")
    km3.metric("Sharpe Ratio",         f"{port_sr:.3f}")
    km4.metric("Max Drawdown",         f"{port_mdd:.2f}%")
    km5.metric("Calmar Ratio",         f"{calmar:.3f}" if not np.isnan(calmar) else "—")

    st.markdown(
        f"<div style='margin-top:.6rem;padding:.75rem 1rem;"
        f"background:#0D1117;border:1px solid #21262D;border-radius:8px;"
        f"font-family:JetBrains Mono;font-size:.76rem;color:{TXT_M};'>"
        f"Diversification benefit: weighted-avg vol <b style=color:{GOLD}>{w_avg_vol:.2f}%</b>"
        f" → portfolio vol <b style=color:{GREEN}>{port_sig*100:.2f}%</b>"
        f" — you saved <b style=color:{CYAN}>{div_benefit:.2f}%</b> of annualised volatility "
        f"through diversification.</div>",
        unsafe_allow_html=True
    )

    # ── Per-security contribution ─────────────────────────────────────────────
    sec("Return & Risk Contribution per Security")
    with st.expander("📖  What is return and risk contribution?"):
        hbox("""
<h4>Return contribution</h4>
<span class="formula">Return contribution_i = w_i × annualised_return_i</span>
Shows how many percentage points each holding contributed to the total portfolio return.
A 30%-weight stock with 20% return contributes 6% to the portfolio return.

<h4>Risk contribution (marginal)</h4>
This is more nuanced than return contribution. A stock can have a high weight and high individual
volatility but low <em>portfolio</em> risk contribution if it is uncorrelated with the rest of the portfolio.
<span class="formula">Risk contribution_i ≈ w_i × Cov(r_i, r_portfolio) ÷ σ_portfolio</span>
A security that moves independently from others is a better diversifier, even at a high weight.
""")
    contrib_data = []
    for t in daily_ret.columns:
        ind_ret = daily_ret[t].mean() * 252 * 100
        ind_vol = daily_ret[t].std()  * np.sqrt(252) * 100
        ind_sr  = (daily_ret[t].mean()*252) / (daily_ret[t].std()*np.sqrt(252)) if daily_ret[t].std()>0 else 0
        cov_with_port = np.cov(daily_ret[t].values, port_ret)[0,1]
        risk_contrib  = (weights[t]/100) * cov_with_port / (port_ret.std()**2) * 100
        contrib_data.append(dict(
            Ticker=t, Weight=f"{weights[t]:.1f}%",
            Return=f"{ind_ret:.2f}%",
            RetContrib=f"{weights[t]/100*ind_ret:.2f}%",
            Volatility=f"{ind_vol:.2f}%",
            RiskContrib=f"{risk_contrib:.2f}%",
            Sharpe=f"{ind_sr:.3f}",
        ))

    cdf2 = pd.DataFrame(contrib_data)
    rows_h = ""
    for _, r in cdf2.iterrows():
        ret_c = GREEN if float(r["Return"].replace("%","")) >= 0 else RED
        rows_h += (
            f"<tr style='border-top:1px solid #21262D;'>"
            f"<td style='font-family:JetBrains Mono;font-size:.75rem;color:{BLUE};padding:8px 12px;'>{r['Ticker']}</td>"
            f"<td style='font-family:JetBrains Mono;font-size:.75rem;color:{TXT_M};padding:8px 12px;'>{r['Weight']}</td>"
            f"<td style='font-family:JetBrains Mono;font-size:.75rem;color:{ret_c};padding:8px 12px;'>{r['Return']}</td>"
            f"<td style='font-family:JetBrains Mono;font-size:.75rem;color:{CYAN};padding:8px 12px;'>{r['RetContrib']}</td>"
            f"<td style='font-family:JetBrains Mono;font-size:.75rem;color:{GOLD};padding:8px 12px;'>{r['Volatility']}</td>"
            f"<td style='font-family:JetBrains Mono;font-size:.75rem;color:{ORANGE};padding:8px 12px;'>{r['RiskContrib']}</td>"
            f"<td style='font-family:JetBrains Mono;font-size:.75rem;color:{PURPLE};padding:8px 12px;'>{r['Sharpe']}</td>"
            f"</tr>"
        )
    st.markdown(
        f"<table style='width:100%;border-collapse:collapse;background:#0D1117;"
        f"border:1px solid #21262D;border-radius:8px;overflow:hidden;'>"
        f"<thead><tr style='background:#161B22;'>"
        f"{''.join(f"<th style='font-family:JetBrains Mono;font-size:.6rem;text-transform:uppercase;letter-spacing:.1em;color:{BLUE};padding:8px 12px;text-align:left;'>{h}</th>" for h in ['Ticker','Weight','Indiv. Return','Return Contrib','Indiv. Vol','Risk Contrib','Sharpe'])}"
        f"</tr></thead><tbody>{rows_h}</tbody></table>",
        unsafe_allow_html=True
    )

    # ── Portfolio drawdown ────────────────────────────────────────────────────
    sec("Portfolio Drawdown")
    fig_pdd = go.Figure()
    fig_pdd.add_trace(go.Scatter(
        x=cum_dates, y=dd_arr,
        mode="lines", name="Portfolio Drawdown",
        line=dict(color=RED, width=1.5),
        fill="tozeroy", fillcolor="rgba(248,81,73,0.12)",
        hovertemplate="%{x|%b %d %Y}<br>DD: %{y:.2f}%<extra></extra>",
    ))
    fig_pdd.add_hline(y=0, line_color=TICK, line_width=1)
    fig_pdd.update_layout(**cly(h=240,
        yaxis=dict(ticksuffix="%"), hovermode="x unified"))
    st.plotly_chart(fig_pdd, width="stretch")

    # ── Weight allocation donut ───────────────────────────────────────────────
    sec("Portfolio Allocation")
    wa_col, wr_col = st.columns(2)
    with wa_col:
        fig_wa = go.Figure(go.Pie(
            labels=list(weights.keys()),
            values=list(weights.values()),
            hole=0.55,
            marker=dict(colors=PALETTE[:len(weights)],
                        line=dict(color="#0B0F1A", width=2)),
            textfont=dict(family="JetBrains Mono", size=10, color=TXT_H),
            hovertemplate="<b>%{label}</b><br>%{value:.1f}%<extra></extra>",
        ))
        fig_wa.update_layout(**cly(h=280, title="Weight allocation",
            showlegend=True,
            legend=dict(font=dict(family="JetBrains Mono",size=9,color=TXT_M),
                        bgcolor="rgba(0,0,0,0)")))
        st.plotly_chart(fig_wa, width="stretch")

    with wr_col:
        # return contribution waterfall
        ret_contribs = [float(r["RetContrib"].replace("%","")) for _, r in cdf2.iterrows()]
        ret_tickers  = cdf2["Ticker"].tolist()
        ret_colors   = [GREEN if v >= 0 else RED for v in ret_contribs]
        fig_wf = go.Figure(go.Bar(
            x=ret_tickers, y=ret_contribs,
            marker_color=ret_colors, marker_opacity=0.85, marker_line_width=0,
            text=[f"{v:+.2f}%" for v in ret_contribs],
            textfont=dict(family="JetBrains Mono", size=9, color=TXT_H),
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>Return contrib: %{y:.2f}%<extra></extra>",
        ))
        fig_wf.add_hline(y=0, line_color=TICK, line_width=1)
        fig_wf.update_layout(**cly(h=280, title="Return contribution per security",
            yaxis=dict(ticksuffix="%"), xaxis=dict(tickfont=dict(size=11))))
        st.plotly_chart(fig_wf, width="stretch")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE ⑥ — ARIMA FORECAST
# ══════════════════════════════════════════════════════════════════════════════
elif page == "ARIMA Forecast":

    # lazy imports — only loaded when this page is visited
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.stattools import adfuller, acf, pacf
    from statsmodels.stats.diagnostic import acorr_ljungbox
    import warnings
    warnings.filterwarnings("ignore")

    st.markdown('<div class="ptitle">ARIMA Price Forecast</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="psub">'
        'AUTO-REGRESSIVE INTEGRATED MOVING AVERAGE  ·  STATISTICAL PRICE FORECASTING'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── What is ARIMA — master explainer ─────────────────────────────────────
    with st.expander("📖  What is ARIMA? — Complete guide before you start"):
        hbox("""
<h4>The big picture</h4>
ARIMA stands for <strong>Auto-Regressive Integrated Moving Average</strong>.
It is a classical statistical model that predicts future values of a time series
using only that series' own past values — no external variables needed.
It is the workhorse of financial forecasting and econometrics, developed by
Box and Jenkins in 1970 and still widely used today.

<h4>The three components — ARIMA(p, d, q)</h4>

<ul>
<li>
  <strong>AR(p) — Auto-Regression</strong><br>
  The current value is a linear combination of its own past <code>p</code> values plus an error term.
  <span class="formula">X_t = c + φ₁X_{t-1} + φ₂X_{t-2} + … + φₚX_{t-p} + ε_t</span>
  Intuition: "Today's price is influenced by the last p days of prices."
  A high AR coefficient φ means strong momentum — yesterday's move predicts today's.
</li>

<li>
  <strong>I(d) — Integration (differencing)</strong><br>
  Stock prices are almost always <em>non-stationary</em> — they trend up or down over time,
  which violates the assumptions of AR and MA models.
  Differencing removes the trend by replacing the series with its changes:
  <span class="formula">ΔX_t = X_t − X_{t-1}  (first difference, d=1)</span>
  <span class="formula">Δ²X_t = ΔX_t − ΔX_{t-1}  (second difference, d=2)</span>
  Most financial price series become stationary after <strong>d=1</strong> differencing
  (i.e., working with returns rather than levels).
</li>

<li>
  <strong>MA(q) — Moving Average</strong><br>
  The current value depends on the past <code>q</code> forecast errors (residuals), not past values.
  <span class="formula">X_t = c + ε_t + θ₁ε_{t-1} + θ₂ε_{t-2} + … + θ_qε_{t-q}</span>
  Intuition: "Today's price is influenced by recent surprise shocks."
  A large negative θ₁ means the model quickly corrects for yesterday's over/under-prediction.
</li>
</ul>

<h4>Combined ARIMA(p,d,q) equation</h4>
After differencing d times, the model fits:
<span class="formula">ΔᵈX_t = c + Σ φᵢ·ΔᵈX_{t-i} + Σ θⱼ·ε_{t-j} + ε_t</span>

<h4>How the order (p,d,q) is chosen — auto_arima</h4>
This dashboard uses <strong>auto_arima</strong> (from the pmdarima library), which:
<ul>
  <li>Tests for stationarity using the <strong>ADF test</strong> (Augmented Dickey-Fuller) to determine d.</li>
  <li>Tries different combinations of p and q (up to the maximum you set).</li>
  <li>Selects the combination with the lowest <strong>AIC</strong> (Akaike Information Criterion):
  <code>AIC = 2k − 2·ln(L)</code> where k = number of parameters, L = likelihood.
  Lower AIC = better model fit penalised for complexity.</li>
</ul>

<h4>Confidence intervals</h4>
The shaded forecast cone represents <strong>95% prediction intervals</strong>:
<span class="formula">Forecast ± 1.96 × forecast_std_error</span>
The cone widens over time because uncertainty compounds — each step forward builds on the previous uncertainty.
A very wide cone after just a few periods signals high volatility and low predictability.

<h4>Important limitations ⚠️</h4>
<ul>
  <li>ARIMA captures <em>linear</em> patterns only. It cannot model jumps, regime changes, or news events.</li>
  <li>It assumes the future resembles the past. In volatile or structural-break periods, forecasts degrade quickly.</li>
  <li>For highly illiquid BVC stocks with many zero-volume days, the model may produce unreliable results.</li>
  <li>This is a statistical exercise, <strong>not financial advice</strong>. Never use ARIMA forecasts alone as a trading signal.</li>
</ul>
""")

    # ── Controls ──────────────────────────────────────────────────────────────
    st.markdown('<div class="sec">Model Configuration</div>', unsafe_allow_html=True)

    cfg1, cfg2, cfg3 = st.columns(3)
    with cfg1:
        arima_ticker = st.selectbox(
            "Security to forecast",
            ALL,
            format_func=lambda t: f"{t}  —  {TKN.get(t, t)}",
            index=ALL.index("ATW") if "ATW" in ALL else 0,
            key="arima_ticker",
        )
    with cfg2:
        forecast_horizon = st.slider(
            "Forecast horizon (trading days)", 5, 60, 20,
            help="How many future trading sessions to forecast. "
                 "Accuracy degrades rapidly beyond 10–15 days for most stocks.",
        )
    with cfg3:
        max_p = st.slider("Max AR order (p)", 1, 5, 3,
                          help="Maximum auto-regression lag to consider. Higher = more complex model.")
        max_q = st.slider("Max MA order (q)", 1, 5, 3,
                          help="Maximum moving-average lag to consider.")

    use_log = st.checkbox(
        "Model log-prices (recommended)",
        value=True,
        help="Taking log(price) before fitting makes the series more homoscedastic "
             "(constant variance) and ensures forecast prices are always positive. "
             "Forecasts are then exponentiated back to MAD.",
    )

    # ── Data prep ─────────────────────────────────────────────────────────────
    tdf_ar = dff[dff["ticker"] == arima_ticker].sort_values("date").dropna(
        subset=["dernier_cours"]
    )

    if len(tdf_ar) < 30:
        st.warning(
            f"Only {len(tdf_ar)} sessions available for {arima_ticker} in the selected period. "
            "Need at least 30 — expand the date range in the sidebar."
        )
        st.stop()

    prices     = tdf_ar["dernier_cours"].values.astype(float)
    dates      = tdf_ar["date"].values
    series     = np.log(prices) if use_log else prices
    series_lbl = "Log-Price" if use_log else "Price (MAD)"

    # ── Stationarity test ─────────────────────────────────────────────────────
    sec("Step 1 — Stationarity Analysis (ADF Test)")
    with st.expander("📖  What is the ADF test and why does stationarity matter?"):
        hbox("""
<h4>Stationarity — the fundamental requirement</h4>
A time series is <strong>stationary</strong> when its statistical properties
(mean, variance, autocorrelation) do not change over time.
ARIMA requires stationarity <em>after differencing</em> — that is why we choose d.

<h4>Why raw prices are non-stationary</h4>
A stock at 100 MAD that trends to 200 MAD has a different mean in the first half
vs. the second half. Its variance also grows with the level (higher prices → bigger swings in MAD).
This violates stationarity.

<h4>The Augmented Dickey-Fuller (ADF) test</h4>
Tests the null hypothesis: <em>"The series has a unit root"</em> (= is non-stationary).
<span class="formula">H₀: series is non-stationary (has unit root)</span>
<span class="formula">H₁: series is stationary (no unit root)</span>
<ul>
  <li><strong class="bad">p-value > 0.05</strong>: Fail to reject H₀ → series is non-stationary → needs differencing.</li>
  <li><strong class="good">p-value ≤ 0.05</strong>: Reject H₀ → series is stationary → ready to model.</li>
</ul>

<h4>The ADF test statistic</h4>
More negative = stronger evidence against unit root.
Critical values: −3.43 (1%), −2.86 (5%), −2.57 (10%).
A statistic below the 5% critical value confirms stationarity.
""")

    adf_orig  = adfuller(series, autolag="AIC")
    diff1     = np.diff(series)
    adf_diff1 = adfuller(diff1, autolag="AIC")

    ad1, ad2 = st.columns(2)
    with ad1:
        p_orig = adf_orig[1]
        col    = GREEN if p_orig <= 0.05 else RED
        st.markdown(
            f"<div style='background:#0D1117;border:1px solid #21262D;"
            f"border-left:3px solid {col};border-radius:6px;padding:.9rem 1.1rem;'>"
            f"<div style='font-family:JetBrains Mono;font-size:.6rem;color:{BLUE};"
            f"text-transform:uppercase;letter-spacing:.12em;margin-bottom:.4rem;'>"
            f"ADF on original {series_lbl}</div>"
            f"<div style='display:flex;gap:2rem;flex-wrap:wrap;'>"
            f"<div><div style='font-family:JetBrains Mono;font-size:.58rem;color:{TXT_M};'>Test Statistic</div>"
            f"<div style='font-family:JetBrains Mono;font-size:1rem;font-weight:600;color:{TXT_H};'>{adf_orig[0]:.4f}</div></div>"
            f"<div><div style='font-family:JetBrains Mono;font-size:.58rem;color:{TXT_M};'>p-value</div>"
            f"<div style='font-family:JetBrains Mono;font-size:1rem;font-weight:600;color:{col};'>{p_orig:.4f}</div></div>"
            f"<div><div style='font-family:JetBrains Mono;font-size:.58rem;color:{TXT_M};'>Result</div>"
            f"<div style='font-family:JetBrains Mono;font-size:.88rem;font-weight:600;color:{col};'>"
            f"{'✅ Stationary' if p_orig <= 0.05 else '❌ Non-stationary'}</div></div>"
            f"</div></div>",
            unsafe_allow_html=True,
        )

    with ad2:
        p_diff = adf_diff1[1]
        col2   = GREEN if p_diff <= 0.05 else RED
        st.markdown(
            f"<div style='background:#0D1117;border:1px solid #21262D;"
            f"border-left:3px solid {col2};border-radius:6px;padding:.9rem 1.1rem;'>"
            f"<div style='font-family:JetBrains Mono;font-size:.6rem;color:{BLUE};"
            f"text-transform:uppercase;letter-spacing:.12em;margin-bottom:.4rem;'>"
            f"ADF on 1st difference of {series_lbl}</div>"
            f"<div style='display:flex;gap:2rem;flex-wrap:wrap;'>"
            f"<div><div style='font-family:JetBrains Mono;font-size:.58rem;color:{TXT_M};'>Test Statistic</div>"
            f"<div style='font-family:JetBrains Mono;font-size:1rem;font-weight:600;color:{TXT_H};'>{adf_diff1[0]:.4f}</div></div>"
            f"<div><div style='font-family:JetBrains Mono;font-size:.58rem;color:{TXT_M};'>p-value</div>"
            f"<div style='font-family:JetBrains Mono;font-size:1rem;font-weight:600;color:{col2};'>{p_diff:.4f}</div></div>"
            f"<div><div style='font-family:JetBrains Mono;font-size:.58rem;color:{TXT_M};'>Result</div>"
            f"<div style='font-family:JetBrains Mono;font-size:.88rem;font-weight:600;color:{col2};'>"
            f"{'✅ Stationary' if p_diff <= 0.05 else '❌ Non-stationary'}</div></div>"
            f"</div></div>",
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

    # ── ACF / PACF ────────────────────────────────────────────────────────────
    sec("Step 2 — ACF & PACF (Choosing p and q manually)")
    with st.expander("📖  How to read ACF and PACF plots to choose p and q"):
        hbox("""
<h4>ACF — Autocorrelation Function</h4>
The ACF at lag k measures the correlation between the series and its own k-lag-shifted version:
<span class="formula">ACF(k) = Corr( X_t, X_{t-k} )</span>
Values range −1 to +1. The blue dashed lines are the <strong>95% confidence bounds</strong>:
<span class="formula">±1.96 / √n</span>
Bars extending beyond the bounds are <strong>statistically significant</strong> at the 5% level.

<h4>PACF — Partial Autocorrelation Function</h4>
PACF(k) measures the correlation at lag k after removing the effect of all shorter lags.
It isolates the <em>direct</em> relationship at exactly k lags.

<h4>The Box-Jenkins identification rules</h4>
Apply these rules to the <em>differenced</em> (stationary) series:
<ul>
  <li><strong>AR(p) signature</strong>: PACF cuts off sharply after lag p, ACF decays gradually → choose that p.</li>
  <li><strong>MA(q) signature</strong>: ACF cuts off sharply after lag q, PACF decays gradually → choose that q.</li>
  <li><strong>ARMA(p,q)</strong>: both ACF and PACF decay gradually → both p and q are needed.</li>
  <li>A single large spike at lag 1 in the ACF of the differenced series (and nothing beyond) suggests MA(1) — i.e., ARIMA(0,1,1).</li>
</ul>

<h4>In practice</h4>
For stock prices: d=1 is almost always correct (prices are a random walk).
After first-differencing, most stocks show very little significant autocorrelation —
which is consistent with the <em>Efficient Market Hypothesis</em> (prices already incorporate all available information).
If ACF/PACF show no significant lags, ARIMA(0,1,0) is a random walk — the best model is "tomorrow = today + noise."
""")

    nlags = min(30, len(diff1) // 2 - 1)
    acf_vals,  acf_ci  = acf(diff1,  nlags=nlags, alpha=0.05)
    pacf_vals, pacf_ci = pacf(diff1, nlags=nlags, alpha=0.05, method="ywm")
    lag_x = list(range(len(acf_vals)))
    conf  = 1.96 / np.sqrt(len(diff1))

    fig_acf = make_subplots(rows=1, cols=2,
                            subplot_titles=["ACF — 1st-differenced series",
                                            "PACF — 1st-differenced series"])
    for col_i, (vals, title) in enumerate([(acf_vals, "ACF"), (pacf_vals, "PACF")], start=1):
        bar_colors = [GREEN if abs(v) > conf else TXT_M for v in vals]
        fig_acf.add_trace(go.Bar(
            x=lag_x, y=vals,
            marker_color=bar_colors, marker_line_width=0,
            name=title, showlegend=False,
            hovertemplate=f"Lag %{{x}}<br>{title}: %{{y:.3f}}<extra></extra>",
        ), row=1, col=col_i)
        # confidence bands
        for sign in [1, -1]:
            fig_acf.add_hline(y=sign * conf, line_dash="dash",
                              line_color=BLUE, line_width=1,
                              row=1, col=col_i)
        fig_acf.add_hline(y=0, line_color=TICK, line_width=1,
                          row=1, col=col_i)

    fig_acf.update_layout(
        paper_bgcolor=PAPER, plot_bgcolor=BG, height=320,
        margin=dict(l=10, r=10, t=40, b=10),
        hoverlabel=HOVER,
        font=dict(family="JetBrains Mono, monospace", size=10, color=TXT_M),
    )
    for i in [1, 2]:
        fig_acf.update_xaxes(**_AX, title_text="Lag", row=1, col=i)
        fig_acf.update_yaxes(**{**_AX, "linecolor": "rgba(0,0,0,0)"},
                             title_text="Correlation", row=1, col=i)
    st.plotly_chart(fig_acf, width="stretch")

    # ── Auto-fit ARIMA ────────────────────────────────────────────────────────
    sec("Step 3 — Automatic Model Selection (auto_arima)")
    with st.expander("📖  How auto_arima selects the best model"):
        hbox("""
<h4>Search strategy</h4>
auto_arima uses a <strong>stepwise search</strong> (Hyndman-Khandakar algorithm):
<ol>
  <li>Start from ARIMA(2,d,2) and ARIMA(0,d,0).</li>
  <li>Evaluate neighbour models by varying p and q ±1.</li>
  <li>Keep the neighbour with the lowest AIC.</li>
  <li>Repeat until no neighbour improves AIC.</li>
</ol>
This is much faster than exhaustive grid search and works well in practice.

<h4>AIC — Akaike Information Criterion</h4>
<span class="formula">AIC = 2k − 2·ln(L̂)</span>
where k = number of free parameters, L̂ = maximised log-likelihood.
AIC rewards goodness-of-fit (high L) but penalises complexity (high k).
Lower AIC = better balance of fit vs. parsimony.

<h4>BIC — Bayesian Information Criterion</h4>
<span class="formula">BIC = k·ln(n) − 2·ln(L̂)</span>
BIC penalises complexity more heavily than AIC (uses ln(n) instead of 2),
so it tends to select simpler models. Both are shown below.

<h4>Log-Likelihood</h4>
Measures how probable the observed data is under the fitted model.
Higher = model fits the data better.
Comparable only between models on the same series with the same d.
""")

    fit_btn = st.button("🚀  Fit ARIMA Model", type="primary")
    if "arima_result" not in st.session_state:
        st.session_state["arima_result"] = None
    if "arima_ticker_fitted" not in st.session_state:
        st.session_state["arima_ticker_fitted"] = None

    if fit_btn or (
        st.session_state["arima_result"] is not None
        and st.session_state["arima_ticker_fitted"] == arima_ticker
    ):
        if fit_btn:
            with st.spinner("Running auto_arima — searching for optimal (p,d,q)…"):
                import pmdarima as pm
                auto = pm.auto_arima(
                    series,
                    max_p=max_p, max_q=max_q,
                    d=None,             # auto-detect via ADF
                    information_criterion="aic",
                    stepwise=True,
                    suppress_warnings=True,
                    error_action="ignore",
                    seasonal=False,
                )
                st.session_state["arima_result"] = auto
                st.session_state["arima_ticker_fitted"] = arima_ticker

        auto = st.session_state["arima_result"]
        order = auto.order   # (p, d, q)
        p, d, q = order

        # ── Model summary cards ───────────────────────────────────────────────
        mc1, mc2, mc3, mc4, mc5 = st.columns(5)
        mc1.metric("AR order p",      str(p))
        mc2.metric("Difference d",    str(d))
        mc3.metric("MA order q",      str(q))
        mc4.metric("AIC",             f"{auto.aic():.2f}")
        mc5.metric("BIC",             f"{auto.bic():.2f}")

        with st.expander("📖  What do p, d, q mean for this specific model?"):
            hbox(f"""
<h4>Your fitted model: ARIMA({p}, {d}, {q})</h4>

<strong>d = {d}</strong> — The series needed to be differenced {d} time(s) to become stationary.
{"This means prices are non-stationary (as expected for most stocks) and we model daily changes, not price levels." if d == 1 else
 "d=0 means the series was already stationary — unusual for prices, possible for very stable or mean-reverting stocks." if d == 0 else
 "d=2 means even first differences were non-stationary — the series has a strong acceleration/deceleration trend."}
<br><br>

<strong>p = {p}</strong> — The model uses the last {p} value(s) of the differenced series as predictors.
{"No auto-regressive term — yesterday's change does not directly predict today's. Consistent with a near-random walk." if p == 0 else
 f"The model includes {p} AR lag(s). The differenced series has statistically significant autocorrelation up to lag {p}."}
<br><br>

<strong>q = {q}</strong> — The model uses the last {q} forecast error(s) as predictors.
{"No moving-average term." if q == 0 else
 f"The model corrects for the last {q} surprise shock(s). This helps the model adapt quickly to unexpected price jumps."}
<br><br>

<strong>AIC = {auto.aic():.2f}</strong> — Lower is better. This is the best AIC found in the stepwise search.
Comparing to a random walk (ARIMA(0,1,0)): a lower AIC here means the extra AR/MA terms
are justified by the improvement in fit.
""")

        # ── Fitted values vs actual ────────────────────────────────────────────
        sec("Step 4 — In-Sample Fit: Fitted Values vs Actual Prices")
        with st.expander("📖  What is in-sample fit and how to judge it?"):
            hbox("""
<h4>What in-sample fit shows</h4>
The model is re-fitted on the same data used for estimation.
The <strong>fitted values</strong> are what the model would have predicted at each past date
given all previous information.
Comparing fitted vs. actual prices reveals how well the model captures historical patterns.

<h4>What to look for</h4>
<ul>
  <li><strong class="good">Good fit</strong>: fitted line closely tracks actual price, residuals (errors) are small and appear random (no systematic pattern).</li>
  <li><strong class="bad">Poor fit</strong>: fitted line lags far behind actual price, or consistently overshoots/undershoots — the model is missing structure in the data.</li>
  <li>Even a "perfect" in-sample fit can be misleading — complex models (high p+q) can overfit and perform worse out-of-sample.</li>
</ul>

<h4>Residual plot</h4>
The residual is <code>actual − fitted</code>. Good residuals should:
<ul>
  <li>Be centred near zero (no bias).</li>
  <li>Show no pattern over time (white noise).</li>
  <li>Have roughly constant variance (no volatility clustering).</li>
</ul>
Note: ARIMA does <em>not</em> model volatility clustering. For that, you would need GARCH.
""")

        fitted_log  = auto.fittedvalues()
        fitted_vals = np.exp(fitted_log) if use_log else fitted_log
        # Robustly align fitted values with actual prices:
        # pmdarima may return len(series) or len(series)-d fitted values depending
        # on the version and d value, so we trim both arrays to the same length.
        n_fit       = len(fitted_vals)
        prices_aln  = prices[-n_fit:]          # last n_fit actual prices
        dates_aln   = dates[-n_fit:]           # matching dates
        residuals   = prices_aln - fitted_vals
        fit_dates   = dates_aln

        fig_fit = make_subplots(rows=2, cols=1, shared_xaxes=True,
                                row_heights=[0.65, 0.35], vertical_spacing=0.04)
        fig_fit.add_trace(go.Scatter(
            x=dates, y=prices, mode="lines", name="Actual",
            line=dict(color=TXT_H, width=1.8),
            hovertemplate="%{x|%b %d %Y}<br>Actual: %{y:,.2f} MAD<extra></extra>",
        ), row=1, col=1)
        fig_fit.add_trace(go.Scatter(
            x=fit_dates, y=fitted_vals, mode="lines", name="Fitted",
            line=dict(color=CYAN, width=1.4, dash="dot"),
            hovertemplate="%{x|%b %d %Y}<br>Fitted: %{y:,.2f} MAD<extra></extra>",
        ), row=1, col=1)
        fig_fit.add_trace(go.Bar(
            x=fit_dates, y=residuals,
            name="Residuals",
            marker_color=[GREEN if r >= 0 else RED for r in residuals],
            marker_opacity=0.6, marker_line_width=0,
            hovertemplate="%{x|%b %d %Y}<br>Residual: %{y:,.3f}<extra></extra>",
        ), row=2, col=1)
        fig_fit.add_hline(y=0, line_color=TICK, line_width=1, row=2, col=1)

        ax = {**_AX}
        fig_fit.update_layout(
            paper_bgcolor=PAPER, plot_bgcolor=BG, height=440,
            hovermode="x unified", legend=leg(), hoverlabel=HOVER,
            margin=dict(l=10, r=10, t=20, b=10),
            xaxis=dict(**ax), yaxis=dict(**ax, tickformat=",.0f"),
            xaxis2=dict(**ax), yaxis2=dict(**{**ax, "linecolor": "rgba(0,0,0,0)"}),
        )
        st.plotly_chart(fig_fit, width="stretch")

        # fit metrics
        mae  = np.mean(np.abs(residuals))
        rmse = np.sqrt(np.mean(residuals ** 2))
        mape = np.mean(np.abs(residuals / prices_aln)) * 100

        fm1, fm2, fm3 = st.columns(3)
        fm1.metric("MAE  (Mean Abs Error)",  f"{mae:.3f} MAD")
        fm2.metric("RMSE (Root Mean Sq Err)", f"{rmse:.3f} MAD")
        fm3.metric("MAPE (Mean Abs % Error)", f"{mape:.3f}%")

        with st.expander("📖  Understanding MAE, RMSE, MAPE"):
            hbox("""
<h4>MAE — Mean Absolute Error</h4>
<span class="formula">MAE = (1/n) × Σ |actual_t − fitted_t|</span>
Average absolute error in MAD. Easy to interpret: "on average, the model's fitted value
was off by MAE MAD." Less sensitive to large outlier errors than RMSE.

<h4>RMSE — Root Mean Squared Error</h4>
<span class="formula">RMSE = √[ (1/n) × Σ (actual_t − fitted_t)² ]</span>
Same units as MAD but penalises large errors more heavily (squaring magnifies outliers).
RMSE > MAE always. The larger the gap between them, the more the model struggles with
occasional large price spikes.

<h4>MAPE — Mean Absolute Percentage Error</h4>
<span class="formula">MAPE = (1/n) × Σ |actual_t − fitted_t| / actual_t × 100</span>
Scale-free: expresses error as a percentage of the actual price.
Useful for comparing across stocks at different price levels.
<ul>
  <li><strong class="good">MAPE &lt; 1%</strong>: excellent in-sample fit for a daily price model.</li>
  <li><strong>MAPE 1–3%</strong>: acceptable.</li>
  <li><strong class="bad">MAPE &gt; 5%</strong>: the model is not capturing the price dynamics well.</li>
</ul>
""")

        # ── Ljung-Box residual test ────────────────────────────────────────────
        sec("Step 5 — Residual Diagnostics (Ljung-Box Test)")
        with st.expander("📖  What is the Ljung-Box test and what should residuals look like?"):
            hbox("""
<h4>Why we test residuals</h4>
If the ARIMA model has captured all the systematic structure in the data,
the residuals should behave like <strong>white noise</strong> — uncorrelated random errors.
Any remaining correlation in the residuals means the model is leaving predictable
signal on the table.

<h4>Ljung-Box Q test</h4>
Tests whether any group of autocorrelations of the residuals is different from zero:
<span class="formula">H₀: residuals are independently distributed (white noise)</span>
<span class="formula">H₁: residuals exhibit serial correlation up to lag h</span>
<span class="formula">Q = n(n+2) × Σ [ r²_k / (n−k) ]  for k = 1 to h</span>
where r_k = autocorrelation of residuals at lag k.

<h4>Interpreting results</h4>
<ul>
  <li><strong class="good">p-value &gt; 0.05</strong>: Fail to reject H₀ → residuals look like white noise → the model is well-specified.</li>
  <li><strong class="bad">p-value ≤ 0.05</strong>: Reject H₀ → residuals have structure → model may need higher p or q, or may need a seasonal component.</li>
</ul>

<div class="note">Even if Ljung-Box passes, ARIMA residuals often show <em>volatility clustering</em> (large errors cluster together). This is normal for financial data and would require GARCH modelling to address.</div>
""")

        lb_lags = min(10, len(residuals) // 5)
        lb      = acorr_ljungbox(residuals, lags=[lb_lags], return_df=True)
        lb_stat = lb["lb_stat"].values[0]
        lb_p    = lb["lb_pvalue"].values[0]
        lb_col  = GREEN if lb_p > 0.05 else RED
        lb_msg  = "✅ Residuals appear to be white noise — model is well-specified." \
                  if lb_p > 0.05 else \
                  "⚠️  Residuals show serial correlation — consider increasing p or q."

        st.markdown(
            f"<div style='background:#0D1117;border:1px solid #21262D;"
            f"border-left:3px solid {lb_col};border-radius:6px;padding:.9rem 1.2rem;"
            f"display:flex;gap:3rem;align-items:center;'>"
            f"<div><div style='font-family:JetBrains Mono;font-size:.58rem;color:{BLUE};"
            f"text-transform:uppercase;letter-spacing:.12em;'>Ljung-Box Q (lag {lb_lags})</div>"
            f"<div style='font-family:JetBrains Mono;font-size:1.1rem;font-weight:600;"
            f"color:{TXT_H};'>{lb_stat:.3f}</div></div>"
            f"<div><div style='font-family:JetBrains Mono;font-size:.58rem;color:{BLUE};"
            f"text-transform:uppercase;letter-spacing:.12em;'>p-value</div>"
            f"<div style='font-family:JetBrains Mono;font-size:1.1rem;font-weight:600;"
            f"color:{lb_col};'>{lb_p:.4f}</div></div>"
            f"<div style='font-family:JetBrains Mono;font-size:.8rem;color:{lb_col};"
            f"font-weight:500;'>{lb_msg}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

        # ── Forecast ──────────────────────────────────────────────────────────
        sec(f"Step 6 — {forecast_horizon}-Day Price Forecast")
        with st.expander("📖  How the forecast is generated and how to read the cone"):
            hbox(f"""
<h4>Generating the forecast</h4>
The fitted ARIMA({p},{d},{q}) model is used to predict {forecast_horizon} steps ahead.
Each step uses the previous forecast as input for the next:
<span class="formula">X̂_{{t+1}} = f(X_t, X_{{t-1}}, …, ε_t, ε_{{t-1}}, …)</span>
For d=1, this means the model predicts the <em>change</em> in (log-)price each day,
then these changes are cumulatively summed to get the price path.

<h4>The forecast cone (95% prediction interval)</h4>
The shaded area is the 95% prediction interval:
<span class="formula">Forecast ± 1.96 × forecast_standard_error_t</span>
The standard error grows with the horizon because uncertainty compounds:
<ul>
  <li>1-day ahead: relatively tight — most of the uncertainty comes from today's residual.</li>
  <li>5-day ahead: noticeably wider — 5 days of compounding uncertainty.</li>
  <li>20-day ahead: very wide — reflects genuine unpredictability over a month.</li>
</ul>
<strong>A wide cone is not a model failure</strong> — it is honest communication of uncertainty.
Beware of models that show narrow cones far out: they are overconfident.

<h4>Point forecast vs. interval</h4>
The <strong>central line</strong> is the <em>expected value</em> (most likely path) under the model.
But any specific path within the cone is equally plausible statistically.
For ARIMA(0,1,0) (random walk), the point forecast is always the last known price —
the model says "the best guess for tomorrow is today."

<h4>Using the forecast practically</h4>
<ul>
  <li>If the entire cone stays well above/below a key price level (support/resistance), that is a stronger signal than if the cone straddles it.</li>
  <li>If the upper and lower bounds at horizon {forecast_horizon} span more than ±10% of current price, the uncertainty is too high to make directional trades based on ARIMA alone.</li>
  <li>Always use ARIMA with other tools: volume analysis, fundamental valuation, and news flow.</li>
</ul>
""")

        n_forecast       = forecast_horizon
        forecast_res     = auto.predict(n_periods=n_forecast, return_conf_int=True)
        fc_vals_log, fc_ci = forecast_res
        if use_log:
            fc_vals = np.exp(fc_vals_log)
            fc_lo   = np.exp(fc_ci[:, 0])
            fc_hi   = np.exp(fc_ci[:, 1])
        else:
            fc_vals = fc_vals_log
            fc_lo   = fc_ci[:, 0]
            fc_hi   = fc_ci[:, 1]

        # generate future business dates
        last_date  = pd.Timestamp(dates[-1])
        fc_dates   = pd.bdate_range(start=last_date + pd.Timedelta(days=1),
                                    periods=n_forecast)

        # ── Main forecast chart ───────────────────────────────────────────────
        # Show last 90 sessions of history for context
        hist_window = min(90, len(prices))
        h_dates = dates[-hist_window:]
        h_prices = prices[-hist_window:]

        fig_fc = go.Figure()

        # Historical price
        fig_fc.add_trace(go.Scatter(
            x=h_dates, y=h_prices,
            mode="lines", name="Historical Price",
            line=dict(color=TXT_H, width=2),
            hovertemplate="%{x|%b %d %Y}<br>Price: %{y:,.2f} MAD<extra></extra>",
        ))
        # Confidence cone (filled area)
        fig_fc.add_trace(go.Scatter(
            x=np.concatenate([fc_dates, fc_dates[::-1]]),
            y=np.concatenate([fc_hi, fc_lo[::-1]]),
            fill="toself",
            fillcolor="rgba(56,139,253,0.12)",
            line=dict(width=0),
            name="95% Prediction Interval",
            hoverinfo="skip",
        ))
        # Upper / lower bands
        fig_fc.add_trace(go.Scatter(
            x=fc_dates, y=fc_hi,
            mode="lines", name="Upper 95%",
            line=dict(color=BLUE, width=1, dash="dot"),
            hovertemplate="%{x|%b %d %Y}<br>Upper: %{y:,.2f} MAD<extra></extra>",
        ))
        fig_fc.add_trace(go.Scatter(
            x=fc_dates, y=fc_lo,
            mode="lines", name="Lower 95%",
            line=dict(color=RED, width=1, dash="dot"),
            hovertemplate="%{x|%b %d %Y}<br>Lower: %{y:,.2f} MAD<extra></extra>",
        ))
        # Point forecast
        fig_fc.add_trace(go.Scatter(
            x=fc_dates, y=fc_vals,
            mode="lines+markers", name="Point Forecast",
            line=dict(color=GOLD, width=2.2),
            marker=dict(size=5, color=GOLD),
            hovertemplate="%{x|%b %d %Y}<br>Forecast: %{y:,.2f} MAD<extra></extra>",
        ))
        # Vertical line at forecast start — use shape+annotation directly
        # (add_vline with string dates causes TypeError in newer Plotly versions)
        last_date_str = str(pd.Timestamp(last_date).date())
        fig_fc.add_shape(dict(
            type="line",
            x0=last_date_str, x1=last_date_str,
            y0=0, y1=1, yref="paper",
            line=dict(dash="dash", color=TICK, width=1.5),
        ))
        fig_fc.add_annotation(dict(
            x=last_date_str, y=1, yref="paper",
            text=" Forecast start", showarrow=False,
            xanchor="left", yanchor="top",
            font=dict(family="JetBrains Mono", size=9, color=TXT_M),
        ))

        fig_fc.update_layout(**cly(h=420, hovermode="x unified", legend=leg()))
        fig_fc.update_yaxes(tickformat=",.2f", ticksuffix=" MAD")
        st.plotly_chart(fig_fc, width="stretch")

        # ── Forecast table ────────────────────────────────────────────────────
        sec("Forecast Table — Day-by-Day Predictions")
        with st.expander("📖  How to read this table"):
            hbox("""
<h4>Columns explained</h4>
<ul>
  <li><strong>Date</strong>: the trading session being forecast (business days only, weekends skipped).</li>
  <li><strong>Forecast (MAD)</strong>: the model's point estimate — expected closing price.</li>
  <li><strong>Lower 95%</strong>: the 2.5th percentile of the prediction distribution. There is a 2.5% chance the actual price falls below this.</li>
  <li><strong>Upper 95%</strong>: the 97.5th percentile. There is a 2.5% chance the actual price exceeds this.</li>
  <li><strong>Interval Width</strong>: Upper − Lower. Grows over the forecast horizon. Wider = more uncertain.</li>
  <li><strong>Δ vs Last</strong>: percentage change from the last known price to the forecast. Sign indicates direction; magnitude reflects how far the model expects the price to move.</li>
</ul>
""")

        last_price = float(prices[-1])
        fc_rows_html = ""
        for i, (fdate, fval, flo, fhi) in enumerate(
            zip(fc_dates, fc_vals, fc_lo, fc_hi)
        ):
            width_pct  = fhi - flo
            delta_pct  = (fval - last_price) / last_price * 100
            delta_col  = GREEN if delta_pct >= 0 else RED
            row_bg     = "#0D1117" if i % 2 == 0 else "#0F1420"
            fc_rows_html += (
                f"<tr style='background:{row_bg};border-top:1px solid #21262D;'>"
                f"<td style='font-family:JetBrains Mono;font-size:.74rem;color:{TXT_M};"
                f"padding:7px 12px;'>{pd.Timestamp(fdate).strftime('%d %b %Y')}</td>"
                f"<td style='font-family:JetBrains Mono;font-size:.76rem;color:{GOLD};"
                f"font-weight:600;padding:7px 12px;'>{fval:,.2f}</td>"
                f"<td style='font-family:JetBrains Mono;font-size:.74rem;color:{RED};"
                f"padding:7px 12px;'>{flo:,.2f}</td>"
                f"<td style='font-family:JetBrains Mono;font-size:.74rem;color:{BLUE};"
                f"padding:7px 12px;'>{fhi:,.2f}</td>"
                f"<td style='font-family:JetBrains Mono;font-size:.74rem;color:{TXT_M};"
                f"padding:7px 12px;'>{width_pct:,.2f}</td>"
                f"<td style='font-family:JetBrains Mono;font-size:.74rem;color:{delta_col};"
                f"font-weight:500;padding:7px 12px;'>{'+' if delta_pct>=0 else ''}{delta_pct:.2f}%</td>"
                f"</tr>"
            )

        hdrs = ["Date", "Forecast (MAD)", "Lower 95%", "Upper 95%", "Interval Width", "Δ vs Last"]
        st.markdown(
            f"<div style='overflow-x:auto;'>"
            f"<table style='width:100%;border-collapse:collapse;background:#0D1117;"
            f"border:1px solid #21262D;border-radius:8px;overflow:hidden;'>"
            f"<thead><tr style='background:#161B22;'>"
            + "".join(
                f"<th style='font-family:JetBrains Mono;font-size:.6rem;text-transform:uppercase;"
                f"letter-spacing:.1em;color:{BLUE};padding:8px 12px;text-align:left;'>{h}</th>"
                for h in hdrs
            )
            + f"</tr></thead><tbody>{fc_rows_html}</tbody></table></div>",
            unsafe_allow_html=True,
        )

        # ── Forecast summary strip ────────────────────────────────────────────
        st.markdown("<div style='height:.8rem'></div>", unsafe_allow_html=True)
        end_fc    = float(fc_vals[-1])
        end_lo    = float(fc_lo[-1])
        end_hi    = float(fc_hi[-1])
        end_delta = (end_fc - last_price) / last_price * 100
        end_col   = GREEN if end_delta >= 0 else RED
        cone_pct  = (end_hi - end_lo) / last_price * 100

        st.markdown(
            f"<div style='display:flex;flex-wrap:wrap;gap:1.5rem;padding:1rem 1.2rem;"
            f"background:#0D1117;border:1px solid #21262D;border-radius:10px;'>"
            f"<div><div style='font-family:JetBrains Mono;font-size:.58rem;color:{BLUE};"
            f"text-transform:uppercase;letter-spacing:.1em;'>Last Known Price</div>"
            f"<div style='font-size:1.2rem;font-weight:700;color:{TXT_H};"
            f"letter-spacing:-.02em;'>{last_price:,.2f} MAD</div></div>"
            f"<div><div style='font-family:JetBrains Mono;font-size:.58rem;color:{BLUE};"
            f"text-transform:uppercase;letter-spacing:.1em;'>Point Forecast (day {n_forecast})</div>"
            f"<div style='font-size:1.2rem;font-weight:700;color:{GOLD};"
            f"letter-spacing:-.02em;'>{end_fc:,.2f} MAD</div></div>"
            f"<div><div style='font-family:JetBrains Mono;font-size:.58rem;color:{BLUE};"
            f"text-transform:uppercase;letter-spacing:.1em;'>Expected Change</div>"
            f"<div style='font-size:1.2rem;font-weight:700;color:{end_col};"
            f"letter-spacing:-.02em;'>{'+' if end_delta>=0 else ''}{end_delta:.2f}%</div></div>"
            f"<div><div style='font-family:JetBrains Mono;font-size:.58rem;color:{BLUE};"
            f"text-transform:uppercase;letter-spacing:.1em;'>95% Range at Horizon</div>"
            f"<div style='font-size:1.2rem;font-weight:700;color:{TXT_H};"
            f"letter-spacing:-.02em;'>{end_lo:,.2f} – {end_hi:,.2f}</div></div>"
            f"<div><div style='font-family:JetBrains Mono;font-size:.58rem;color:{BLUE};"
            f"text-transform:uppercase;letter-spacing:.1em;'>Cone Width (% of price)</div>"
            f"<div style='font-size:1.2rem;font-weight:700;"
            f"color:{'#F85149' if cone_pct > 15 else '#E3B341' if cone_pct > 7 else '#3FB950'};"
            f"letter-spacing:-.02em;'>{cone_pct:.1f}%</div></div>"
            f"</div>",
            unsafe_allow_html=True,
        )

        # ── Model equation display ────────────────────────────────────────────
        sec("Model Parameters")
        with st.expander("📖  Full model equation and estimated coefficients"):
            params = auto.params()
            param_names = auto.arima_res_.param_names

            eq_ar_terms = " ".join(
                [f"+ ({params[i]:.4f})·Δ^{d}X_{{t-{j}}}"
                 for j, i in enumerate(range(p), start=1)]
            ) if p > 0 else ""
            eq_ma_terms = " ".join(
                [f"+ ({params[p+i]:.4f})·ε_{{t-{j}}}"
                 for j, i in enumerate(range(q), start=1)]
            ) if q > 0 else ""
            intercept = params[0] if "intercept" in str(param_names[0]).lower() or "const" in str(param_names[0]).lower() else 0.0

            hbox(f"""
<h4>Estimated ARIMA({p},{d},{q}) equation</h4>
<span class="formula">Δ^{d}X_t = {intercept:.6f} {eq_ar_terms} {eq_ma_terms} + ε_t</span>

<h4>Coefficient table</h4>
{"<br>".join([
    f"<strong>{name}</strong>: {val:.6f}"
    for name, val in zip(param_names, params)
])}

<h4>Interpretation</h4>
All AR coefficients (φ) close to zero are consistent with the Efficient Market Hypothesis —
past prices have little predictive power over future prices.
If |φᵢ| is large (e.g. &gt; 0.3), there is meaningful momentum or mean-reversion at lag i.
""")

    else:
        st.markdown(
            '<div class="hbox">Click <strong>Fit ARIMA Model</strong> above to run the analysis. '
            'Fitting may take 5–15 seconds depending on the series length and max p/q.</div>',
            unsafe_allow_html=True,
        )
