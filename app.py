import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import datetime as dt
import plotly.graph_objs as go

st.set_page_config(layout="wide")
st.title("📊 Mini App Scalping GOLD (XAU/USD)")

# Sélection de timeframe
tf_map = {"1 Minute": "1m", "5 Minutes": "5m"}
timeframe = st.selectbox("Timeframe", list(tf_map.keys()))

# Récupérer les données
end = dt.datetime.now()
start = end - dt.timedelta(days=1)
data = yf.download("XAUUSD=X", start=start, end=end, interval=tf_map[timeframe])

if data.empty:
    st.warning("Erreur : Aucune donnée récupérée.")
    st.stop()

# Indicateurs techniques
data['EMA20'] = data['Close'].ewm(span=20).mean()
data['EMA50'] = data['Close'].ewm(span=50).mean()
delta = data['Close'].diff()
gain = np.where(delta > 0, delta, 0)
loss = np.where(delta < 0, -delta, 0)
avg_gain = pd.Series(gain).rolling(window=14).mean()
avg_loss = pd.Series(loss).rolling(window=14).mean()
rs = avg_gain / avg_loss
data['RSI'] = 100 - (100 / (1 + rs))

# MACD
ema12 = data['Close'].ewm(span=12).mean()
ema26 = data['Close'].ewm(span=26).mean()
data['MACD'] = ema12 - ema26
data['Signal'] = data['MACD'].ewm(span=9).mean()

# Signal de trading
def generate_signal(df):
    signal = []
    for i in range(1, len(df)):
        if df['Close'][i] > df['EMA50'][i] and df['RSI'][i] > 50 and df['MACD'][i] > df['Signal'][i]:
            signal.append("LONG")
        elif df['Close'][i] < df['EMA50'][i] and df['RSI'][i] < 50 and df['MACD'][i] < df['Signal'][i]:
            signal.append("SHORT")
        else:
            signal.append("")
    signal.insert(0, "")
    df['TradeSignal'] = signal
    return df

data = generate_signal(data)

# Graphique
fig = go.Figure()
fig.add_trace(go.Candlestick(x=data.index,
                             open=data['Open'],
                             high=data['High'],
                             low=data['Low'],
                             close=data['Close'],
                             name='XAU/USD'))
fig.add_trace(go.Scatter(x=data.index, y=data['EMA20'], line=dict(color='orange'), name='EMA20'))
fig.add_trace(go.Scatter(x=data.index, y=data['EMA50'], line=dict(color='blue'), name='EMA50'))

# Afficher les signaux
long_signals = data[data['TradeSignal'] == "LONG"]
short_signals = data[data['TradeSignal'] == "SHORT"]

fig.add_trace(go.Scatter(x=long_signals.index, y=long_signals['Close'],
                         mode='markers', marker=dict(color='green', size=10), name='LONG'))
fig.add_trace(go.Scatter(x=short_signals.index, y=short_signals['Close'],
                         mode='markers', marker=dict(color='red', size=10), name='SHORT'))

st.plotly_chart(fig, use_container_width=True)

# Dernier signal
latest_signal = data['TradeSignal'].iloc[-1]
if latest_signal == "LONG":
    st.success("📈 Signal actuel : LONG")
elif latest_signal == "SHORT":
    st.error("📉 Signal actuel : SHORT")
else:
    st.info("⏳ Pas de signal clair actuellement.")
