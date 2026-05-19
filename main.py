import requests
import pandas as pd
import numpy as np
import time
from ta.trend import EMAIndicator, SMAIndicator
from datetime import datetime
from colorama import Fore, init

init(autoreset=True)

# =========================================
# CONFIG
# =========================================

API_KEY = "6019661d14c94cc7a34c7ec523c89ce4"

DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1504374915657371759/Zsv5wpigIJcYQTYaSILn8LRcPaw3T14IFEXGeKsBHd_ZEFiZIUAus2bbFtarO1xN0TVN"

PAIRS = [
    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "AUDUSD",
    "USDCAD",
    "EURJPY"
]

# =========================================
# DISCORD ALERT
# =========================================

def send_discord(message):

    try:

        data = {
            "content": message
        }

        requests.post(DISCORD_WEBHOOK, json=data)

    except Exception as e:

        print(Fore.RED + f"Discord Error: {e}")

# =========================================
# GET FOREX DATA
# =========================================

def get_data(symbol, interval="5min", outputsize=200):

    url = (
        f"https://api.twelvedata.com/time_series?"
        f"symbol={symbol}"
        f"&interval={interval}"
        f"&outputsize={outputsize}"
        f"&apikey={API_KEY}"
    )

    try:

        response = requests.get(url)

        data = response.json()

        # SHOW REAL API ERROR

        if "values" not in data:

            print(Fore.RED + f"API RESPONSE: {data}")

            print(Fore.RED + f"NO DATA: {symbol}")

            return None

        df = pd.DataFrame(data["values"])

        # REVERSE DATA
        df = df.iloc[::-1]

        # CONVERT TO FLOAT
        df["open"] = df["open"].astype(float)
        df["high"] = df["high"].astype(float)
        df["low"] = df["low"].astype(float)
        df["close"] = df["close"].astype(float)

        return df

    except Exception as e:

        print(Fore.RED + f"API ERROR: {e}")

        return None

# =========================================
# SUPPLY & DEMAND
# =========================================

def supply_demand(df):

    supply = df["high"].rolling(20).max().iloc[-1]

    demand = df["low"].rolling(20).min().iloc[-1]

    return supply, demand

# =========================================
# SMART MONEY STRUCTURE
# =========================================

def market_structure(df):

    previous_high = df["high"].iloc[-5]

    previous_low = df["low"].iloc[-5]

    current_price = df["close"].iloc[-1]

    bos_buy = current_price > previous_high

    bos_sell = current_price < previous_low

    return bos_buy, bos_sell

# =========================================
# ANALYZE PAIR
# =========================================

def analyze_pair(pair):

    print(Fore.CYAN + f"\nAnalyzing {pair}...")

    # =====================================
    # SESSION FILTER
    # =====================================

    hour = datetime.utcnow().hour

    if hour < 7 or hour > 20:

        print(Fore.YELLOW + "Outside active market session")

        return

    # =====================================
    # GET 5M DATA
    # =====================================

    df = get_data(pair, "5min")

    if df is None:

        return

    # =====================================
    # GET 1H DATA
    # =====================================

    h1 = get_data(pair, "1h")

    if h1 is None:

        return

    # =====================================
    # INDICATORS
    # =====================================

    df["EMA20"] = EMAIndicator(
        close=df["close"],
        window=20
    ).ema_indicator()

    df["SMA10"] = SMAIndicator(
        close=df["close"],
        window=10
    ).sma_indicator()

    h1["EMA50"] = EMAIndicator(
        close=h1["close"],
        window=50
    ).ema_indicator()

    current_price = df["close"].iloc[-1]

    # =====================================
    # TREND FILTER
    # =====================================

    trend_buy = h1["close"].iloc[-1] > h1["EMA50"].iloc[-1]

    trend_sell = h1["close"].iloc[-1] < h1["EMA50"].iloc[-1]

    # =====================================
    # EMA/SMA CROSS
    # =====================================

    ema_buy = df["EMA20"].iloc[-1] > df["SMA10"].iloc[-1]

    ema_sell = df["EMA20"].iloc[-1] < df["SMA10"].iloc[-1]

    # =====================================
    # SUPPLY DEMAND
    # =====================================

    supply, demand = supply_demand(df)

    demand_buy = current_price <= demand * 1.002

    supply_sell = current_price >= supply * 0.998

    # =====================================
    # SMART MONEY BOS
    # =====================================

    bos_buy, bos_sell = market_structure(df)

    # =====================================
    # CANDLE CONFIRMATION
    # =====================================

    bullish_candle = (
        df["close"].iloc[-1] >
        df["open"].iloc[-1]
    )

    bearish_candle = (
        df["close"].iloc[-1] <
        df["open"].iloc[-1]
    )

    # =====================================
    # CONFIDENCE SYSTEM
    # =====================================

    buy_confidence = 0

    sell_confidence = 0

    if trend_buy:
        buy_confidence += 20

    if ema_buy:
        buy_confidence += 20

    if demand_buy:
        buy_confidence += 20

    if bos_buy:
        buy_confidence += 20

    if bullish_candle:
        buy_confidence += 20

    if trend_sell:
        sell_confidence += 20

    if ema_sell:
        sell_confidence += 20

    if supply_sell:
        sell_confidence += 20

    if bos_sell:
        sell_confidence += 20

    if bearish_candle:
        sell_confidence += 20

    # =====================================
    # FINAL SIGNALS
    # =====================================

    current_time = datetime.now().strftime("%H:%M")

    # BUY SIGNAL

    if buy_confidence >= 80:

        signal = f"""
🟢 BUY SIGNAL

PAIR: {pair}
TIMEFRAME: 5 MINUTES
CONFIDENCE: {buy_confidence}%
STRATEGY: SMC + DEMAND + EMA
TIME: {current_time}
"""

        print(Fore.GREEN + signal)

        send_discord(signal)

    # SELL SIGNAL

    elif sell_confidence >= 80:

        signal = f"""
🔴 SELL SIGNAL

PAIR: {pair}
TIMEFRAME: 5 MINUTES
CONFIDENCE: {sell_confidence}%
STRATEGY: SMC + SUPPLY + EMA
TIME: {current_time}
"""

        print(Fore.RED + signal)

        send_discord(signal)

    else:

        print(Fore.YELLOW + f"No strong setup for {pair}")

# =========================================
# BOT HEADER
# =========================================

print(Fore.CYAN + "=" * 45)

print(Fore.CYAN + "POCKET OPTION AI SIGNAL BOT")

print(Fore.CYAN + "STRICT HIGH ACCURACY VERSION")

print(Fore.CYAN + "SMC + SUPPLY DEMAND + EMA")

print(Fore.CYAN + "DISCORD ALERTS ENABLED")

print(Fore.CYAN + "LOW API USAGE MODE")

print(Fore.CYAN + "=" * 45)

# =========================================
# MAIN LOOP
# =========================================

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