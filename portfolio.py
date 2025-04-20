# app.py
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px
from scipy.optimize import minimize

# Predefined list of 50 popular tickers
TICKER_LIST = [
    'AAPL','MSFT','GOOGL','AMZN','FB','TSLA','BRK-B','JPM','JNJ','V',
    'WMT','PG','MA','UNH','HD','BAC','DIS','NVDA','VZ','ADBE',
    'NFLX','PYPL','CMCSA','PFE','KO','PEP','INTC','T','CSCO','XOM',
    'ABT','CVX','MRK','CRM','WFC','COST','NKE','MDT','LLY','ORCL',
    'UPS','MCD','TXN','QCOM','BMY','NEE','AMGN','HON','IBM','LIN'
]

# Page layout
st.set_page_config(page_title="Portfolio Analyzer", layout="wide")
st.title("📈 Portfolio Analyzer")
st.markdown("Select up to 10 tickers from the dropdown and specify quantities, then click **Analyze**.")

# Sidebar inputs
st.sidebar.header("Portfolio Input")
selected = st.sidebar.multiselect(
    "Select Tickers (max 10)", TICKER_LIST, default=TICKER_LIST[:3]
)
if len(selected) > 10:
    st.sidebar.error("Please select at most 10 tickers.")

qtys = {t: st.sidebar.number_input(f"Qty of {t}", min_value=0, step=1, value=0) for t in selected}
rf = st.sidebar.number_input("Risk‑free rate (%)", value=0.0, step=0.1) / 100

if st.sidebar.button("Analyze"):
    import time
    # Animated "ANALYZING..." banner (show for 3 seconds)
    placeholder = st.empty()
    placeholder.markdown(
        "<h1 style='text-align:center; color:#ff0066;'>🤖 🚀 <span style=\"font-family:monospace; animation: blink 2s step-end infinite;\">ANALYZING...</span> 🚀 🤖</h1>"
        "<style>@keyframes blink{50%{opacity:0;}}</style>",
        unsafe_allow_html=True
    )
    time.sleep(3)
    placeholder.empty()

    # Gather input data
    data = [(t, qty) for t, qty in qtys.items() if qty > 0]
    if not data:
        st.error("Enter quantity > 0 for at least one selected ticker.")
        st.stop()

    # Fetch data
    rows, returns_weekly = [], {}
    for t, q in data:
        tk = yf.Ticker(t)
        info = tk.info
        name = info.get("shortName", t)

        hist = tk.history(period="10y", interval="1wk")["Close"].dropna()
        if hist.empty:
            st.warning(f"No weekly data for {t}, skipping.")
            continue
        price = hist.iloc[-1]
        weekly_ret = hist.pct_change().dropna()
        exp_ret = weekly_ret.mean() * 52
        std_dev = weekly_ret.std() * np.sqrt(52)
        returns_weekly[t] = weekly_ret

        rows.append({
            "Ticker": t,
            "Name": name,
            "Expected Return": exp_ret,
            "Std Deviation": std_dev,
            "Qty": q,
            "Value per Share": price,
            "Total value": price * q
        })

    df = pd.DataFrame(rows).set_index("Ticker").sort_values("Total value", ascending=False)

    # Per-ticker summary
    st.subheader("Per‑Ticker Summary")
    st.dataframe(
        df.style.format({
            "Expected Return": "{:.1%}",
            "Std Deviation": "{:.1%}",
            "Value per Share": "${:,.2f}",
            "Total value": "${:,.2f}"
        }), use_container_width=True
    )

    # Current allocation pie
    st.subheader("Current Portfolio Allocation")
    fig1 = px.pie(
        df.reset_index(),
        names='Ticker',
        values='Total value',
        hover_data={
            'Value per Share': ':.2f',
            'Total value': ':.2f'
        },
        title='Current Allocation'
    )
    fig1.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig1, use_container_width=True)

    # Current metrics
    total_val = df['Total value'].sum()
    w0 = df['Total value'] / total_val
    cov = pd.DataFrame(returns_weekly).cov() * 52
    port_exp = np.dot(w0, df['Expected Return'])
    port_std = np.sqrt(w0 @ cov.values @ w0)
    port_sharpe = (port_exp - rf) / port_std if port_std else np.nan

    st.subheader("Current Portfolio Metrics")
    st.write(f"- **Total value:** ${total_val:,.2f}")
    st.write(f"- **Expected Return:** {port_exp:.1%}")
    st.write(f"- **Std Deviation:** {port_std:.1%}")
    st.write(f"- **Sharpe Ratio:** {port_sharpe:.2f}")

    # Separator
    st.markdown("---")

        # Optimize portfolio: maximize Sharpe with w>=price/total_val and sum(w)=1
    mu = df['Expected Return'].values
    def neg_sharpe(w):
        r = w.dot(mu)
        s = np.sqrt(w @ cov.values @ w)
        return -(r - rf) / s if s else 0

    constraints = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1}]
    bounds = [(row['Value per Share'] / total_val, 1.0) for _, row in df.iterrows()]

    res = minimize(neg_sharpe, w0.values, bounds=bounds, constraints=constraints)
    w_opt = res.x

    # Continuous optimized allocations (no integer share rounding)
    alloc = w_opt * total_val
    shares_cont = alloc / df['Value per Share']

    opt = pd.DataFrame({
        'Ticker': df.index,
        'Name': df['Name'],
        'Weight': w_opt,
        'Allocated Value': alloc,
        'Shares (cont.)': shares_cont
    }).set_index('Ticker').sort_values('Allocated Value', ascending=False)

    alloc = w_opt * total_val
    shares = np.round(alloc / df['Value per Share']).astype(int)
    shares[shares < 1] = 1
    opt = pd.DataFrame({
        'Ticker': df.index,
        'Name': df['Name'],
        'Qty': shares,
        'Value per Share': df['Value per Share'],
        'Total value': shares * df['Value per Share']
    }).set_index('Ticker').sort_values('Total value', ascending=False)

    # Optimized allocation pie
    st.subheader("Optimized Portfolio Allocation")
    fig2 = px.pie(
        opt.reset_index(),
        names='Ticker',
        values='Total value',
        hover_data={
            'Value per Share': ':.2f',
            'Total value': ':.2f'
        },
        title='Optimized Allocation'
    )
    fig2.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig2, use_container_width=True)

    # Optimized allocation table
    st.subheader("Optimized Allocation Table")
    st.dataframe(
        opt.style.format({
            "Qty": "{:,}",
            "Value per Share": "${:,.2f}",
            "Total value": "${:,.2f}"
        }), use_container_width=True
    )

    # Optimized metrics
    w_opt_act = opt['Total value'] / opt['Total value'].sum()
    exp_opt = np.dot(w_opt_act, mu)
    std_opt = np.sqrt(w_opt_act @ cov.values @ w_opt_act)
    sharpe_opt = (exp_opt - rf) / std_opt if std_opt else np.nan

    st.subheader("Optimized Portfolio Metrics")
    st.write(f"- **Total value:** ${opt['Total value'].sum():,.2f}")
    st.write(f"- **Expected Return:** {exp_opt:.1%}")
    st.write(f"- **Std Deviation:** {std_opt:.1%}")
    st.write(f"- **Sharpe Ratio:** {sharpe_opt:.2f}")

    # CSV download
    st.download_button(
        label="📥 Download summary as CSV",
        data=df.to_csv().encode(),
        file_name="portfolio_summary.csv",
        mime="text/csv"
    )
