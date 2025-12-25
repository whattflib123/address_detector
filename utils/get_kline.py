import pandas as pd
import requests

def fmt_k(v):
    if v >= 1_000_000_000:
        return f"{v / 1_000_000_000:,.2f}B"
    elif v >= 1_000_000:
        return f"{v / 1_000_000:,.2f}M"
    elif v >= 1_000:
        return f"{v / 1_000:,.2f}K"
    else:
        return f"{v:,.2f}"

def get_kline_data(symbol, interval="1h", limit=1000):
    url = "https://fapi.binance.com/fapi/v1/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    df = pd.DataFrame(data, columns=[
        "timestamp", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "trades", "taker_base_volume",
        "taker_quote_volume", "ignore"
    ])
    df["close"] = df["close"].astype(float)
    df["low"] = df["low"].astype(float)
    df["high"] = df["high"].astype(float)
    df["volume"] = df["volume"].astype(float)
    df["time"] = pd.to_datetime(df["timestamp"], unit='ms', utc=True).dt.tz_convert('Asia/Taipei')
    return df
