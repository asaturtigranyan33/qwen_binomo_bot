import ccxt
import talib
import numpy as np
import time
from telegram import Bot
from telegram.error import TelegramError

# ========== ՁԵՐ Config  Parametres ==========
TELEGRAM_BOT_TOKEN = "8438864481:AAFOZFAZq1KqiVdU-rE3SxMrlCvNaHaf79A"  # Ձեր Telegram Bot Token
TELEGRAM_CHAT_ID = "903610526"              # Ձեր Telegram Chat ID
SYMBOL = "ETH/USDT"
TIMEFRAME = "15m"
EXCHANGE_NAME = "binance"  # Օգտագործում ենք Binance-ի տվյալները, որպեսզի համապատասխանի Binomo-ին
CHECK_INTERVAL = 900  # 15 րոպե (900 վայրկյան)

# ========== Բոտի Սկզբնավորում ==========
bot = Bot(token=TELEGRAM_BOT_TOKEN)
exchange = getattr(ccxt, EXCHANGE_NAME)()

def get_candles(symbol, timeframe, limit=50):
    try:
        candles = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        close = np.array([c[4] for c in candles])
        open = np.array([c[1] for c in candles])
        high = np.array([c[2] for c in candles])
        low = np.array([c[3] for c in candles])
        return open, high, low, close
    except Exception as e:
        print(f"Error fetching candles: {e}")
        return None, None, None, None

def detect_support_resistance(high, low, close, lookback=10):
    # Պարզ մեթոդ՝ հայտնաբերելու համար հաջորդ մակարդակները
    recent_highs = high[-lookback:]
    recent_lows = low[-lookback:]
    resistance = np.max(recent_highs)
    support = np.min(recent_lows)
    return support, resistance

def detect_engulfing(open, close, i):
    if i < 1:
        return False
    # Bullish Engulfing
    if close[i-1] < open[i-1] and close[i] > open[i] and open[i] < close[i-1] and close[i] > open[i-1]:
        return "BULLISH"
    # Bearish Engulfing
    elif close[i-1] > open[i-1] and close[i] < open[i] and open[i] > close[i-1] and close[i] < open[i-1]:
        return "BEARISH"
    return False

def send_telegram_alert(message):
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        print(f"✅ Alert sent: {message}")
    except TelegramError as e:
        print(f"❌ Failed to send alert: {e}")

def main():
    print("🚀 SOL/USDT 15m բոտ սկսվեց...")
    while True:
        open, high, low, close = get_candles(SYMBOL, TIMEFRAME)
        if open is None:
            time.sleep(60)
            continue

        # Վերջին մոմի ինդեքս
        i = len(close) - 1

        # Պայման A: Support/Resistance Bounce
        support, resistance = detect_support_resistance(high, low, close)
        current_price = close[i]
        prev_price = close[i-1]

        # Ստուգում ենք, թե գինը հետ է գալիս հակառակ ուղղությամբ
        if abs(current_price - support) < (resistance - support) * 0.01 and prev_price > current_price:
            message = f"""
🚨 ՆՈՐ ՍԻԳՆԱԼ 🚨
Ապրանք: {SYMBOL}
Ժամանակ: {TIMEFRAME}
Սիգնալ: BUY (Support Bounce)
Գին: ${current_price:.2f}
Մակարդակ: Support = ${support:.2f}
Պատճառ: Գինը հետ է գալիս հակառակ ուղղությամբ Support մակարդակից
👉 Բացեք գործարք Binomo-ում!
"""
            send_telegram_alert(message)

        elif abs(current_price - resistance) < (resistance - support) * 0.01 and prev_price < current_price:
            message = f"""
🚨 ՆՈՐ ՍԻԳՆԱԼ 🚨
Ապրանք: {SYMBOL}
Ժամանակ: {TIMEFRAME}
Սիգնալ: SELL (Resistance Bounce)
Գին: ${current_price:.2f}
Մակարդակ: Resistance = ${resistance:.2f}
Պատճառ: Գինը հետ է գալիս հակառակ ուղղությամբ Resistance մակարդակից
👉 Բացեք գործարք Binomo-ում!
"""
            send_telegram_alert(message)

        # Պայման B: Engulfing Pattern
        engulfing = detect_engulfing(open, close, i)
        if engulfing == "BULLISH":
            message = f"""
🔥 ENGULFING ՍԻԳՆԱԼ 🔥
Ապրանք: {SYMBOL}
Ժամանակ: {TIMEFRAME}
Սիգնալ: BUY (Bullish Engulfing)
Գին: ${current_price:.2f}
Պատճառ: Գտնվել է Bullish Engulfing Pattern
👉 Բացեք գործարք Binomo-ում!
"""
            send_telegram_alert(message)

        elif engulfing == "BEARISH":
            message = f"""
🔥 ENGULFING ՍԻԳՆԱԼ 🔥
Ապրանք: {SYMBOL}
Ժամանակ: {TIMEFRAME}
Սիգնալ: SELL (Bearish Engulfing)
Գին: ${current_price:.2f}
Պատճառ: Գտնվել է Bearish Engulfing Pattern
👉 Բացեք գործարք Binomo-ում!
"""
            send_telegram_alert(message)

        print(f"⏱ Ստուգում ավարտվեց: {time.strftime('%H:%M:%S')}")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
