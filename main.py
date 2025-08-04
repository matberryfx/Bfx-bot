
import requests, json, time
import yfinance as yf
import pandas_ta as ta

TOKEN = "8024348789:AAHd5yfR1ujs83rgzEJi7SnD6gHe-ErA4u0"
CHAT_ID = "-1002638968108"
PAIR = "XAUUSD=X"

STEP_PIPS = 20
TP2_PIPS = 30
SL_PIPS = 25
RSI_PERIOD = 14
EMA_FAST = 20
EMA_SLOW = 50

def fetch_data():
    df = yf.download(PAIR, interval="1m", period="1d")
    df.dropna(inplace=True)
    df['RSI'] = ta.rsi(df['Close'], length=RSI_PERIOD)
    df['EMA20'] = ta.ema(df['Close'], length=EMA_FAST)
    df['EMA50'] = ta.ema(df['Close'], length=EMA_SLOW)
    return df

def find_nearest_sr(price, df, direction):
    highs = df['High'].values
    lows = df['Low'].values
    if direction == "buy":
        levels = [h for h in highs if h > price]
        return round(min(levels), 2) if levels else round(price + 3, 2)
    else:
        levels = [l for l in lows if l < price]
        return round(max(levels), 2) if levels else round(price - 3, 2)

def send_msg(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
    requests.post(url, data=payload)

def load_state():
    try:
        with open("memory.json", "r") as f:
            return json.load(f)
    except:
        return {"entry": None, "direction": None, "layers": 0}

def save_state(state):
    with open("memory.json", "w") as f:
        json.dump(state, f)

def signal_logic():
    df = fetch_data()
    last = df.iloc[-1]
    prev = df.iloc[-2]

    price = round(last["Close"], 2)
    state = load_state()

    rsi = last["RSI"]
    ema20 = last["EMA20"]
    ema50 = last["EMA50"]
    text = None

    if rsi < 30 and last["Close"] > ema20 > ema50 and prev["Close"] < ema20:
        tp1 = find_nearest_sr(price, df, "buy")
        tp2 = round(tp1 + TP2_PIPS * 0.1, 2)
        sl = round(price - SL_PIPS * 0.1, 2)

        text = f"XAUUSD Signal\nBUY\nEntry: {price}\nTP1: {tp1}\nTP2: {tp2}\nSL: {sl}"

        state = {"entry": price, "direction": "buy", "layers": 1}
        save_state(state)

    elif rsi > 70 and last["Close"] < ema20 < ema50 and prev["Close"] > ema20:
        tp1 = find_nearest_sr(price, df, "sell")
        tp2 = round(tp1 - TP2_PIPS * 0.1, 2)
        sl = round(price + SL_PIPS * 0.1, 2)

        text = f"XAUUSD Signal\nSELL\nEntry: {price}\nTP1: {tp1}\nTP2: {tp2}\nSL: {sl}"

        state = {"entry": price, "direction": "sell", "layers": 1}
        save_state(state)

    elif state["entry"] and state["layers"] < 10:
        diff = abs(price - state["entry"])
        if diff >= STEP_PIPS * 0.1:
            dir = state["direction"]
            if dir == "buy":
                tp1 = round(price + TP2_PIPS * 0.1, 2)
                sl = round(price - SL_PIPS * 0.1, 2)
            else:
                tp1 = round(price - TP2_PIPS * 0.1, 2)
                sl = round(price + SL_PIPS * 0.1, 2)

            text = f"Layer Recommendation\nNew Entry: {price}\nTP1: {tp1}\nSL: {sl}"

            state["entry"] = price
            state["layers"] += 1
            save_state(state)

    if text:
        send_msg(text.strip())

if __name__ == "__main__":
    while True:
        try:
            signal_logic()
        except Exception as e:
            print(f"[ERROR] {e}")
        time.sleep(120)
