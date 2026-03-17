import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import base64

st.set_page_config(page_title="AI Stock Decision App", layout="centered")

st.title("🤖 AI Stock Decision App")

# ================= SOUND FUNCTION =================
def play_sound(file_path):
    with open(file_path, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()

    audio_html = f"""
    <audio autoplay>
    <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
    </audio>
    """
    st.markdown(audio_html, unsafe_allow_html=True)

# ================= INPUT =================
stock = st.text_input("Enter Stock Symbol (e.g., AAPL, TSLA, INFY.NS)", "AAPL")

# ================= ANALYSIS FUNCTION =================
def analyze_stock(data):

    # Moving Averages
    data["MA50"] = data["Close"].rolling(50).mean()
    data["MA200"] = data["Close"].rolling(200).mean()

    # RSI
    delta = data["Close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    data["RSI"] = 100 - (100 / (1 + rs))

    # MACD
    exp1 = data["Close"].ewm(span=12, adjust=False).mean()
    exp2 = data["Close"].ewm(span=26, adjust=False).mean()
    data["MACD"] = exp1 - exp2
    data["Signal"] = data["MACD"].ewm(span=9, adjust=False).mean()

    # Bollinger Bands
    data["BB_Mid"] = data["Close"].rolling(20).mean()
    std = data["Close"].rolling(20).std()
    data["BB_Upper"] = data["BB_Mid"] + 2 * std
    data["BB_Lower"] = data["BB_Mid"] - 2 * std

    data = data.dropna()
    latest = data.iloc[-1]

    score = 0

    # Trend
    score += 1 if latest["MA50"] > latest["MA200"] else -1

    # RSI
    if latest["RSI"] < 30:
        score += 1
    elif latest["RSI"] > 70:
        score -= 1

    # MACD
    score += 1 if latest["MACD"] > latest["Signal"] else -1

    # Bollinger
    if latest["Close"] < latest["BB_Lower"]:
        score += 1
    elif latest["Close"] > latest["BB_Upper"]:
        score -= 1

    # Decision
    if score >= 2:
        decision = "BUY"
    elif score <= -2:
        decision = "SELL"
    else:
        decision = "HOLD"

    return decision, latest, data, score

# ================= SESSION =================
if "last_decision" not in st.session_state:
    st.session_state.last_decision = None

# ================= BUTTON =================
if st.button("Analyze Stock"):
    try:
        data = yf.download(stock, period="1y")

        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        if data.empty:
            st.error("❌ Invalid stock symbol")
            st.stop()

        decision, latest, data, score = analyze_stock(data)

        # ================= RESULT =================
        st.subheader(f"📊 Decision for {stock}")

        if decision == "BUY":
            st.success("📈 BUY")
        elif decision == "SELL":
            st.error("📉 SELL")
        else:
            st.warning("⚖️ HOLD")

        # ================= SOUND =================
        if decision != st.session_state.last_decision:
            if decision == "BUY":
                play_sound("assets/buy.mp3")
            elif decision == "SELL":
                play_sound("assets/sell.mp3")

        st.session_state.last_decision = decision

        # ================= CONFIDENCE =================
        confidence = min(abs(score) / 4 * 100, 100)
        st.progress(int(confidence))
        st.write(f"Confidence Score: **{round(confidence, 2)}%**")

        # ================= METRICS =================
        col1, col2, col3 = st.columns(3)
        col1.metric("Price", round(latest["Close"], 2))
        col2.metric("RSI", round(latest["RSI"], 2))
        col3.metric("MACD", round(latest["MACD"], 2))

        # ================= PRICE =================
        st.subheader("📈 Price + Moving Averages")
        fig1, ax1 = plt.subplots()
        ax1.plot(data["Close"], label="Price")
        ax1.plot(data["MA50"], label="MA50")
        ax1.plot(data["MA200"], label="MA200")
        ax1.legend()
        st.pyplot(fig1)

        # ================= RSI =================
        st.subheader("📊 RSI")
        fig2, ax2 = plt.subplots()
        ax2.plot(data["RSI"])
        ax2.axhline(70)
        ax2.axhline(30)
        st.pyplot(fig2)

        # ================= MACD =================
        st.subheader("📉 MACD")
        fig3, ax3 = plt.subplots()
        ax3.plot(data["MACD"], label="MACD")
        ax3.plot(data["Signal"], label="Signal")
        ax3.legend()
        st.pyplot(fig3)

        # ================= BOLLINGER =================
        st.subheader("📊 Bollinger Bands")
        fig4, ax4 = plt.subplots()
        ax4.plot(data["Close"])
        ax4.plot(data["BB_Upper"], linestyle="--")
        ax4.plot(data["BB_Lower"], linestyle="--")
        st.pyplot(fig4)

        # ================= VOLUME =================
        st.subheader("📦 Volume")
        fig5, ax5 = plt.subplots()
        ax5.bar(range(len(data)), data["Volume"])
        st.pyplot(fig5)

    except Exception as e:
        st.error(f"Error: {e}")
