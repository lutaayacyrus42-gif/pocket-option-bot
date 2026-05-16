import requests
import pandas as pd
from ta.trend import EMAIndicator
from colorama import Fore, init
from datetime import datetime, timedelta
import time

# ====================================
# STARTUP
# ====================================

init(autoreset=True)

print(Fore.CYAN + "===================================")
print(Fore.CYAN + " POCKET OPTION AI SIGNAL BOT ")
print(Fore.CYAN + " SMC + SUPPLY DEMAND STRATEGY ")
print(Fore.CYAN + " DISCORD ALERTS ENABLED ")
print(Fore.CYAN + " 5 MINUTE SYSTEM ")
print(Fore.CYAN + "===================================")

# ====================================
# SETTINGS
# ====================================

API_KEY = "6019661d14c94cc7a34c7ec523c89ce4"

TRADE_DURATION = 5
MIN_CONFIDENCE = 80

# ====================================
# DISCORD WEBHOOK
# ====================================

DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1504374915657371759/Zsv5wpigIJcYQTYaSILn8LRcPaw3T14IFEXGeKsBHd_ZEFiZIUAus2bbFtarO1xN0TVN"

# ====================================
# FOREX PAIRS
# ====================================

PAIRS = {

    ("EUR", "USD"): "EUR/USD",
    ("GBP", "USD"): "GBP/USD",
    ("USD", "JPY"): "USD/JPY",
    ("AUD", "USD"): "AUD/USD"
}

# ====================================
# SEND DISCORD ALERT
# ====================================

def send_discord(message):

    try:

        data = {
            "content": message
        }

        requests.post(
            DISCORD_WEBHOOK,
            json=data
        )

    except Exception as e:

        print(f"Discord Error: {e}")

# ====================================
# GET MARKET DATA
# ====================================

def get_data(from_symbol, to_symbol):

    try:

        symbol = f"{from_symbol}/{to_symbol}"

        url = (
            f"https://api.twelvedata.com/time_series?"
            f"symbol={symbol}"
            f"&interval=1min"
            f"&outputsize=100"
            f"&apikey={API_KEY}"
        )

        response = requests.get(url)

        data = response.json()

        if "values" not in data:

            print(Fore.RED + f"❌ API ERROR: {data}")
            return None

        rows = []

        for candle in data["values"]:

            rows.append({

                "time": candle["datetime"],
                "open": float(candle["open"]),
                "high": float(candle["high"]),
                "low": float(candle["low"]),
                "close": float(candle["close"])
            })

        df = pd.DataFrame(rows)

        # OLDEST TO NEWEST
        df = df[::-1].reset_index(drop=True)

        return df

    except Exception as e:

        print(Fore.RED + f"DATA ERROR: {e}")

        return None

# ====================================
# SUPPLY & DEMAND
# ====================================

def demand_zone(df):

    recent_low = df["low"].rolling(20).min().iloc[-1]

    current_price = df["close"].iloc[-1]

    return current_price <= recent_low * 1.001

def supply_zone(df):

    recent_high = df["high"].rolling(20).max().iloc[-1]

    current_price = df["close"].iloc[-1]

    return current_price >= recent_high * 0.999

# ====================================
# SMART MONEY CONCEPTS (SMC)
# ====================================

def bullish_bos(df):

    recent_high = df["high"].iloc[-6:-1].max()

    current_close = df["close"].iloc[-1]

    return current_close > recent_high

def bearish_bos(df):

    recent_low = df["low"].iloc[-6:-1].min()

    current_close = df["close"].iloc[-1]

    return current_close < recent_low

# ====================================
# MARKET TREND
# ====================================

def market_trend(ema20, sma10):

    if ema20 > sma10:
        return "BULLISH"

    elif ema20 < sma10:
        return "BEARISH"

    else:
        return "SIDEWAYS"

# ====================================
# AI CONFIDENCE
# ====================================

def confidence_score(
    trend,
    bos,
    zone
):

    confidence = 50

    if trend:
        confidence += 20

    if bos:
        confidence += 20

    if zone:
        confidence += 15

    return confidence

# ====================================
# ANALYSIS ENGINE
# ====================================

def analyze(pair_name, df):

    ema20 = EMAIndicator(
        close=df["close"],
        window=20
    ).ema_indicator()

    sma10 = df["close"].rolling(10).mean()

    current_price = df["close"].iloc[-1]

    ema20_value = ema20.iloc[-1]
    sma10_value = sma10.iloc[-1]

    trend = market_trend(
        ema20_value,
        sma10_value
    )

    now = datetime.now()

    print("\n===================================")
    print(f"PAIR: {pair_name}")
    print(f"TIME: {now.strftime('%H:%M:%S')}")
    print(f"PRICE: {current_price}")
    print(f"EMA20: {round(ema20_value, 5)}")
    print(f"SMA10: {round(sma10_value, 5)}")
    print(f"TREND: {trend}")
    print("===================================")

    # ====================================
    # CALL CONDITIONS
    # ====================================

    bullish_zone = demand_zone(df)

    bullish_structure = bullish_bos(df)

    bullish_trend = (
        trend == "BULLISH"
        and current_price > ema20_value
    )

    bullish_confidence = confidence_score(
        bullish_trend,
        bullish_structure,
        bullish_zone
    )

    if (
        bullish_zone
        and bullish_structure
        and bullish_trend
        and bullish_confidence >= MIN_CONFIDENCE
    ):

        signal_time = now

        entry_time = signal_time + timedelta(minutes=1)

        message = f"""
🔥 HIGH ACCURACY CALL

PAIR: {pair_name}

📢 SIGNAL TIME:
{signal_time.strftime('%H:%M:%S')}

⏰ ENTER AT:
{entry_time.strftime('%H:%M:%S')}

⏱ TRADE TIME:
{TRADE_DURATION} MINUTES

🧠 AI CONFIDENCE:
{bullish_confidence}%
"""

        print(Fore.GREEN + message)

        send_discord(message)

    # ====================================
    # PUT CONDITIONS
    # ====================================

    bearish_zone = supply_zone(df)

    bearish_structure = bearish_bos(df)

    bearish_trend = (
        trend == "BEARISH"
        and current_price < ema20_value
    )

    bearish_confidence = confidence_score(
        bearish_trend,
        bearish_structure,
        bearish_zone
    )

    if (
        bearish_zone
        and bearish_structure
        and bearish_trend
        and bearish_confidence >= MIN_CONFIDENCE
    ):

        signal_time = now

        entry_time = signal_time + timedelta(minutes=1)

        message = f"""
🔥 HIGH ACCURACY PUT

PAIR: {pair_name}

📢 SIGNAL TIME:
{signal_time.strftime('%H:%M:%S')}

⏰ ENTER AT:
{entry_time.strftime('%H:%M:%S')}

⏱ TRADE TIME:
{TRADE_DURATION} MINUTES

🧠 AI CONFIDENCE:
{bearish_confidence}%
"""

        print(Fore.RED + message)

        send_discord(message)

# ====================================
# MAIN LOOP
# ====================================

while True:

    try:

        for pair, pair_name in PAIRS.items():

            from_symbol = pair[0]
            to_symbol = pair[1]

            df = get_data(
                from_symbol,
                to_symbol
            )

            if df is not None:

                analyze(
                    pair_name,
                    df
                )

            print("\nWaiting next pair...\n")

            time.sleep(10)

    except Exception as e:

        print(Fore.RED + f"ERROR: {e}")

    print(Fore.CYAN + "\nScanning market again...\n")

    time.sleep(15)
