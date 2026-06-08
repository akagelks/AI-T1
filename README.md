# 📊 AI-T1: Quant Crypto Dashboard & Bot

> *Institutional-grade simplified dashboard for micro-scalping and buy-the-dip strategies in crypto assets.*

## 🎯 About the Project
**AI-T1** is a control panel designed to identify, simulate, and execute crypto trading operations with a focus on consistency and rigorous risk management. 
Unlike retail bots, this project utilizes quantitative logic (volume anomaly detection and mean reversion) and is optimized to run lightweight on the cloud (Streamlit Community Cloud), requiring no powerful local hardware.

## 🚀 Key Features
- **📈 Real-Time Market View:** Candlestick + Volume charts with live data from Binance/Bitget via public API (CCXT).
- **🧪 Backtest Simulator (Forward Test):** Test strategies with real historical data, calculating Win Rate, Net P&L (including 0.1% fees), and equity curve.
- **🤖 Bot Control Panel:** "Copy Trade" style interface to activate/deactivate strategies with a single click.
- **🔒 Security:** Credential management via Streamlit Secrets (encrypted).

## 🧠 Implemented Strategies
1. **Buy-the-Dip Scalp:** Buys during rapid drops (e.g., ≥ 0.8% in 10 min) with short Take Profit (0.5%) and controlled Stop Loss (2.5%).
2. **Volume Spike Reversal:** Detects institutional absorption when volume explodes (Z-Score > 2) but price drops, indicating potential reversal.
3. **Breakout Momentum:** Buys breakouts of recent highs accompanied by above-average volume.

## 🛠️ Tech Stack
- **Language:** Python 3.9+
- **Frontend/Dashboard:** Streamlit
- **Data Manipulation:** Pandas, NumPy
- **Exchange Connection:** CCXT (Binance/Bitget)
- **Visualization:** Plotly

## ⚙️ Setup Instructions (Deploy)

### 1. Configuring Secrets
In the Streamlit Cloud dashboard, go to **Settings > Secrets** and add your credentials in TOML format.
⚠️ **CRITICAL:** Your exchange API keys must have ONLY "Spot/Margin Trading" permissions. **NEVER** enable "Withdrawals".

```toml
[exchange]
api_key = "YOUR_API_KEY_HERE"
api_secret = "YOUR_API_SECRET_HERE"

[telegram]
bot_token = "YOUR_BOT_TOKEN_HERE" # Optional for future alerts
chat_id = "YOUR_CHAT_ID_HERE"