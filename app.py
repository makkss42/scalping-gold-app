import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import datetime as dt
import plotly.graph_objs as go

st.set_page_config(layout="wide")
st.title("📊 Mini App Scalping EUR/USD")

# Sélection du timeframe
tf_map = {
    "5 Minutes": "5m",
    "15 Minutes": "15m",
    "30 Minutes": "30m",
    "1 Hour": "60m"
}
timeframe = st.selectbox("Choisir le timeframe :", list(tf_map.keys()))

# Télécharger les données
end = dt.datetime.now()
start = end - dt.timedelta(days=7)

ticker = "EURUSD=X"  # Ticker Yahoo Finance pour EUR/USD
data = yf.download(ticker, start=start, end=end, interval=tf_map[timeframe])

# 🛠️ Forcer la normalisation des colonnes
data.columns = [col.capitalize() for col in data.columns]

# 🔍 Vérification
if data.empty or 'Close' not in data.columns:
    st.warning("❌ Aucune donnée récupérée ou colonne 'Close' manquante.")
    st.stop()

# Indicateurs techniques
data['EMA20'] = data['Close'].ewm(span=20).mean()
data['EMA50'] = data['Close'].ewm(span=50).mean()

# RSI
delta = data['Close'].diff()
gain = delta.copy()
gain[gain < 0] = 0

loss = delta.copy()
loss[loss > 0] = 0
loss = -loss  # rendre les pertes positives

avg_gain = gain.rolling(window=14).mean()
avg_loss = loss.rolling(window=14).mean()
rs = avg_gain / avg_loss
data['RSI'] = 100 - (100 / (1 + rs))

# MACD
ema12 = data['Close'].ewm(span=12).mean()
ema26 = data['Close'].ewm(span=26).mean()
data['MACD'] = ema12 - ema26
data['Signal'] = data['MACD'].ewm(span=9).mean()

# Signaux scalping
def generate_signals(df):
    signals = []
    for i in range(1, len(df)):
        if (
            df['Close'].iloc[i] > df['EMA50'].iloc[i]
            and df['RSI'].iloc[i] > 50
            and df['MACD'].iloc[i] > df['Signal'].iloc[i]
        ):
            signals.append("LONG")
        elif (
            df['Close'].iloc[i] < df['EMA50'].iloc[i]
            and df['RSI'].iloc[i] < 50
            and df['MACD'].iloc[i] < df['Signal'].iloc[i]
        ):
            signals.append("SHORT")
        else:
            signals.append("")
    signals.insert(0, "")
    df['TradeSignal'] = signals
    return df

data = generate_signals(data)

# Affichage graphique
fig = go.Figure()
fig.add_trace(go.Candlestick(
    x=data.index,
    open=data['Open'],
    high=data['High'],
    low=data['Low'],
    close=data['Close'],
    name='EUR/USD'
))
fig.add_trace(go.Scatter(x=data.index, y=data['EMA20'], line=dict(color='orange'), name='EMA20'))
fig.add_trace(go.Scatter(x=data.index, y=data['EMA50'], line=dict(color='blue'), name='EMA50'))

# Signaux visuels
long_signals = data[data['TradeSignal'] == "LONG"]
short_signals = data[data['TradeSignal'] == "SHORT"]

fig.add_trace(go.Scatter(
    x=long_signals.index,
    y=long_signals['Close'],
    mode='markers',
    marker=dict(color='green', size=10),
    name='LONG'
))
fig.add_trace(go.Scatter(
    x=short_signals.index,
    y=short_signals['Close'],
    mode='markers',
    marker=dict(color='red', size=10),
    name='SHORT'
))

st.plotly_chart(fig, use_container_width=True)

# Dernier signal affiché
latest_signal = data['TradeSignal'].iloc[-1]
if latest_signal == "LONG":
    st.success("📈 Signal actuel : LONG")
elif latest_signal == "SHORT":
    st.error("📉 Signal actuel : SHORT")
else:
    st.info("⏳ Aucun signal clair pour le moment.")
