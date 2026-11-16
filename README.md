# RSI Swing Strategy (Daily + Hourly)

Backtester, Streamlit app and TradingView strategies based on the Chirag Rathod RSI swing rules.

## Files
| File | What it is |
|---|---|
| `rsi_swing.py` | Engine: indicators, long + short backtest, stats, train/test optimizer, CLI |
| `app.py` | Streamlit app (works on mobile) |
| `rsi_swing_classic.pine` | TradingView Pine v6 strategy, Long 30/25, Short 70/75 |
| `rsi_swing_rsi20.pine` | TradingView Pine v6 strategy, Long 20/20, Short 80/80 (separate version) |
| `requirements.txt` | pandas, numpy, ccxt, streamlit |

## Rules
**Long**
1. Daily RSI below 30 and Hourly RSI below 25 (arms the setup for 12 hourly bars).
2. Entry: a green hourly candle closes above the high of the last red candle (filled at next open).
3. Exit (first hit): +4% take profit, or a red candle closes below the low of the last green candle (trail starts at +1% profit), or an hourly close below the entry-day Daily low, or an 8% emergency stop.

**Short** is the exact mirror: Daily RSI above 70, Hourly RSI above 75, red candle closes below the last green candle's low, stop = entry-day Daily high (close basis).

**RSI 20 version** (separate): Daily RSI below 20 and Hourly RSI below 20 for longs, above 80 / 80 for shorts. Fewer, rarer trades.

## Capital and sizing
Starts with Rs 1,00,000. Risk 1% of equity per trade to the stop, capped at 1x leverage. Fees 0.10% per side plus 0.02% slippage.

## Run
```
pip install -r requirements.txt
streamlit run app.py
python rsi_swing.py backtest --symbol ETH/USDT --preset classic
python rsi_swing.py backtest --symbol BTC/USDT --preset rsi20
python rsi_swing.py optimize --symbol ETH/USDT --preset classic
```
On Streamlit Cloud some exchanges block the server IP; the downloader tries Binance, OKX, KuCoin, Bybit in turn, or upload a 1h CSV in the app.

## About the 70% win rate
No parameter set can be promised to hit 70%. The `optimize` mode ranks combos by win rate on the first 70% of data and re-tests the best on the remaining 30% the optimizer never saw. Only trust a combo whose test win rate and profit factor hold up. A high win rate with a profit factor under 1 loses money (many small wins, few big losses).

Educational tool, not financial advice.
