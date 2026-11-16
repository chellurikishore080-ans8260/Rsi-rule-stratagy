"""Streamlit app for the RSI Swing strategy (mobile friendly).

Run:  streamlit run app.py
"""
from dataclasses import replace

import pandas as pd
import streamlit as st

import rsi_swing as R

st.set_page_config(page_title="RSI Swing Backtest", layout="centered")
st.title("RSI Swing - Daily + Hourly")
st.caption("Long: Daily RSI low + Hourly RSI low, green candle breaks last red high. Short: mirror.")

preset = st.selectbox("Strategy version", list(R.PRESETS), format_func=lambda x: {
    "classic": "Classic (Long 30/25, Short 70/75)",
    "rsi20": "RSI 20 (Long 20/20, Short 80/80)"}[x])
base = R.PRESETS[preset]

c1, c2 = st.columns(2)
symbol = c1.text_input("Symbol", "ETH/USDT")
days = c2.slider("History (days)", 180, 1825, 1095, 30)

with st.expander("Rules / risk settings"):
    a, b = st.columns(2)
    d_long = a.number_input("Long: Daily RSI below", 5.0, 50.0, float(base.d_long_max))
    h_long = b.number_input("Long: Hourly RSI below", 5.0, 50.0, float(base.h_long_max))
    d_short = a.number_input("Short: Daily RSI above", 50.0, 95.0, float(base.d_short_min))
    h_short = b.number_input("Short: Hourly RSI above", 50.0, 95.0, float(base.h_short_min))
    tp = a.number_input("Take profit %", 0.5, 20.0, float(base.tp_pct), 0.5)
    trail = b.number_input("Candle trail starts at profit % (99 = off)", 0.0, 99.0, float(base.trail_start_pct), 0.5)
    arm = a.number_input("Armed window (hourly bars)", 1, 100, int(base.arm_bars))
    risk = b.number_input("Risk per trade %", 0.1, 5.0, float(base.risk_pct), 0.1)
    capital = a.number_input("Capital (Rs)", 10_000.0, 10_000_000.0, float(R.CAPITAL), 10_000.0)
    lev = b.number_input("Max leverage (1 = none)", 1.0, 20.0, float(base.max_leverage), 0.5)
    sides = st.multiselect("Sides", ["long", "short"], ["long", "short"])

p = replace(base, d_long_max=d_long, h_long_max=h_long, d_short_min=d_short, h_short_min=h_short,
            tp_pct=tp, trail_start_pct=trail, arm_bars=int(arm), risk_pct=risk, capital=capital,
            max_leverage=lev, allow_long="long" in sides, allow_short="short" in sides)


@st.cache_data(ttl=3600, show_spinner="Downloading hourly candles...")
def get_data(sym: str, n_days: int) -> pd.DataFrame:
    return R.fetch_ohlcv(sym, n_days)


up = st.file_uploader("...or upload 1h CSV (timestamp,open,high,low,close,volume)", type="csv")

b1, b2 = st.columns(2)
run_bt = b1.button("Run backtest", type="primary", use_container_width=True)
run_opt = b2.button("Optimize (train/test)", use_container_width=True)

if run_bt or run_opt:
    try:
        if up is not None:
            raw = R._frame(pd.read_csv(up).rename(columns=str.lower))
        else:
            raw = get_data(symbol, days)
    except Exception as e:  # noqa: BLE001
        st.error(f"Data error: {e}")
        st.stop()
    d = R.add_indicators(raw, p.rsi_len)
    st.write(f"{len(d):,} hourly bars  |  {d.index[0]:%Y-%m-%d} to {d.index[-1]:%Y-%m-%d}")

    if run_bt:
        trades, eq, s = R.backtest(d, p)
        m1, m2, m3 = st.columns(3)
        m1.metric("Win rate", f"{s['win_rate']}%")
        m2.metric("Profit factor", s["profit_factor"])
        m3.metric("Return", f"{s['return_pct']}%")
        m4, m5, m6 = st.columns(3)
        m4.metric("Trades", s["trades"])
        m5.metric("Max drawdown", f"{s['max_dd_pct']}%")
        m6.metric("Final equity", f"Rs {s['final_equity']:,.0f}")
        st.caption(f"Long: {s['long_trades']} trades, {s['long_wr']}% win  |  "
                   f"Short: {s['short_trades']} trades, {s['short_wr']}% win  |  "
                   f"Avg win {s['avg_win_pct']}%  Avg loss {s['avg_loss_pct']}%")
        if s["win_rate"] < 70:
            st.warning("Win rate is below 70% with these settings. Try the Optimize button, but check the TEST columns.")
        st.line_chart(eq.dropna())
        if not trades.empty:
            st.dataframe(trades[["entry_time", "exit_time", "side", "entry", "exit", "pnl", "ret_pct", "reason"]])
            st.download_button("Download trades CSV", trades.to_csv(index=False), f"trades_{preset}.csv")
    else:
        with st.spinner("Searching parameter grid..."):
            res = R.optimize(d, p, min_trades=15)
        st.dataframe(res)
        st.info("Trust a row only if test_wr and test_pf stay close to train. A big drop = curve-fit.")
