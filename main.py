import requests
import pandas as pd
import numpy as np
import time
from ta.trend import EMAIndicator, SMAIndicator
from datetime import datetime
from colorama import Fore, init

init(autoreset=True)

# ==============================
# CONFIG
# ==============================

API_KEY = "6019661d14c94cc7a34c7ec523c89ce4"

DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1504374915657371759/Zsv5wpigIJcYQTYaSILn8LRcPaw3T14IFEXGeKsBHd_ZEFiZIUAus2bbFtarO1xN0TVN"

PAIRS = [
    "EUR/USD",
    "GBP/USD",
    "USD/JPY",
    "AUD/USD",
    "USD/CAD",
    "EUR/JPY"
]

TIMEFRAME = "5min"

# ==============================
# DISCORD ALERT
# ==============================

def send_discord(message):
    try:
        data = {
            "content": message
        }

        requests.post(DISCORD_WEBHOOK, json=data)

    except Exception as e:
        print(Fore.RED + f"Discord Error: {e}")

# ==============================
# GET FOREX DATA
# ==============================

def get_data(symbol, interval="5min", outputsize=200):

    pair = symbol.replace("/", "")

    url = (
        f"https://api.twelvedata.com/time_series?"
        f"symbol={pair}"
        f"&interval={interval}"
        f"&outputsize={outputsize}"
        f"&apikey={API_KEY}"
    )

    try:
        response = requests.get(url)
        data = response.json()

        if "values" not in data:
            print(Fore.RED + f"NO DATA: {symbol}")
            return None

        df = pd.DataFrame(data["values"])

        df = df.iloc[::-1]

        df["close"] = df["close"].astype(float)
        df["open"] = df["open"].astype(float)
        df["high"] = df["high"].astype(float)
        df["low"] = df["low"].astype(float)

        return df

    except Exception as e:
        print(Fore.RED + f"API ERROR: {e}")
        return None

# ==============================
# SUPPLY & DEMAND
# ==============================

def supply_demand(df):

    supply = df["high"].rolling(20).max().iloc[-1]
    demand = df["low"].rolling(20).min().iloc[-1]

    return supply, demand

# ==============================
# SMART MONEY STRUCTURE
# ==============================

def market_structure(df):

    previous_high = df["high"].iloc[-5]
    previous_low = df["low"].iloc[-5]

    current_price = df["close"].iloc[-1]

    bos_buy = current_price > previous_high
    bos_sell = current_price < previous_low

    return bos_buy, bos_sell

# ==============================
# MAIN ANALYSIS
# ==============================

def analyze_pair(pair):

    print(Fore.CYAN + f"\nAnalyzing {pair}...")

    # --------------------------
    # SESSION FILTER
    # --------------------------

    hour = datetime.utcnow().hour

    if hour < 7 or hour > 20:
        print(Fore.YELLOW + "Outside London/New York session")
        return

    # --------------------------
    # GET 5M DATA
    # --------------------------

    df = get_data(pair, "5min")

    if df is None:
        return

    # --------------------------
    # GET 1H DATA
    # --------------------------

    h1 = get_data(pair, "1h")

    if h1 is None:
        return

    # --------------------------
    # INDICATORS
    # --------------------------

    ema20 = EMAIndicator(df["close"], window=20).ema_indicator()
    sma10 = SMAIndicator(df["close"], window=10).sma_indicator()

    h1_ema50 = EMAIndicator(h1["close"], window=50).ema_indicator()

    df["EMA20"] = ema20
    df["SMA10"] = sma10

    current_price = df["close"].iloc[-1]

    # --------------------------
    # TREND FILTER
    # --------------------------

    h1_close = h1["close"].iloc[-1]
    h1_ema = h1_ema50.iloc[-1]

    trend_buy = h1_close > h1_ema
    trend_sell = h1_close < h1_ema

    # --------------------------
    # EMA/SMA CONFIRMATION
    # --------------------------

    ema_buy = df["EMA20"].iloc[-1] > df["SMA10"].iloc[-1]
    ema_sell = df["EMA20"].iloc[-1] < df["SMA10"].iloc[-1]

    # --------------------------
    # SUPPLY / DEMAND
    # --------------------------

    supply, demand = supply_demand(df)

    demand_buy = current_price <= demand * 1.002
    supply_sell = current_price >= supply * 0.998

    # --------------------------
    # CANDLE CONFIRMATION
    # --------------------------

    last_open = df["open"].iloc[-1]
    last_close = df["close"].iloc[-1]

    bullish_candle = last_close > last_open
    bearish_candle = last_close < last_open

    # --------------------------
    # SMART MONEY BOS
    # --------------------------

    bos_buy, bos_sell = market_structure(df)

    # --------------------------
    # CONFIDENCE SYSTEM
    # --------------------------

    buy_confidence = 0
    sell_confidence = 0

    if trend_buy:
        buy_confidence += 20

    if ema_buy:
        buy_confidence += 20

    if demand_buy:
        buy_confidence += 20

    if bullish_candle:
        buy_confidence += 20

    if bos_buy:
        buy_confidence += 20

    if trend_sell:
        sell_confidence += 20

    if ema_sell:
        sell_confidence += 20

    if supply_sell:
        sell_confidence += 20

    if bearish_candle:
        sell_confidence += 20

    if bos_sell:
        sell_confidence += 20

    # ==========================
    # FINAL SIGNALS
    # ==========================

    current_time = datetime.now().strftime("%H:%M")

    # BUY SIGNAL

    if buy_confidence >= 80:

        signal = (
            f"🟢 BUY SIGNAL\n\n"
            f"PAIR: {pair}\n"
            f"TIMEFRAME: 5 MINUTES\n"
            f"CONFIDENCE: {buy_confidence}%\n"
            f"STRATEGY: SMC + EMA + DEMAND\n"
            f"TIME: {current_time}"
        )

        print(Fore.GREEN + signal)

        send_discord(signal)

    # SELL SIGNAL

    elif sell_confidence >= 80:

        signal = (
            f"🔴 SELL SIGNAL\n\n"
            f"PAIR: {pair}\n"
            f"TIMEFRAME: 5 MINUTES\n"
            f"CONFIDENCE: {sell_confidence}%\n"
            f"STRATEGY: SMC + EMA + SUPPLY\n"
            f"TIME: {current_time}"
        )

        print(Fore.RED + signal)

        send_discord(signal)

    else:

        print(Fore.YELLOW + f"No strong setup for {pair}")

# ==============================
# MAIN LOOP
# ==============================

print(Fore.CYAN + "=" * 40)
print(Fore.CYAN + "POCKET OPTION AI SIGNAL BOT")
print(Fore.CYAN + "STRICT HIGH ACCURACY VERSION")
print(Fore.CYAN + "SMC + SUPPLY DEMAND + EMA")
print(Fore.CYAN + "DISCORD ALERTS ENABLED")
print(Fore.CYAN + "=" * 40)

while True:

    try:

        for pair in PAIRS:

            analyze_pair(pair)

            # WAIT BETWEEN PAIRS
            time.sleep(10)

        print(Fore.CYAN + "\nWaiting for next 5 minute candle...\n")

        # WAIT FOR NEXT 5M CANDLE
        time.sleep(300)

    except Exception as e:

        print(Fore.RED + f"MAIN ERROR: {e}")

        time.sleep(60) 