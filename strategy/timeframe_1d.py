# strategy/timeframe_1d.py

import numpy as np
from api import get_klines
from indicators.ema import ema
from indicators.macd import macd
from settings import (
    SYMBOL,
    INTERVAL_1D,
    CANDLES_1D,
    MACD_FAST,
    MACD_SLOW,
    MACD_SIGNAL,
)


def analyze_1d():
    """
    Analiza trendu 1D:
        - trend: kierunek EMA50/EMA200
        - big_trend: kierunek MACD (powyżej/poniżej zera)
    Zwraca:
        { "trend": "UP"/"DOWN", "big_trend": "UP"/"DOWN" }
    """

    # ─────────────────────────────────────────────
    # 1) Pobranie świec
    # ─────────────────────────────────────────────
    df = get_klines(SYMBOL, INTERVAL_1D, CANDLES_1D)

    if df is None or len(df) < 250:
        return None

    # ─────────────────────────────────────────────
    # 2) Indykatory
    # ─────────────────────────────────────────────
    df["ema_fast"] = ema(df["close"], 50)
    df["ema_slow"] = ema(df["close"], 200)

    df["macd"], df["macd_signal"], df["macd_hist"] = macd(
        df["close"], MACD_FAST, MACD_SLOW, MACD_SIGNAL
    )

    last = df.iloc[-1]

    # sanity check
    if any(np.isnan([last["ema_fast"], last["ema_slow"], last["macd"]])):
        return None

    # ─────────────────────────────────────────────
    # 3) Trendy
    # ─────────────────────────────────────────────
    trend = "UP" if last["ema_fast"] > last["ema_slow"] else "DOWN"
    big_trend = "UP" if last["macd"] > 0 else "DOWN"

    return {
        "trend": trend,
        "big_trend": big_trend,
    }
