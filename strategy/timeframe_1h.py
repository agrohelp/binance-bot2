# strategy/timeframe_1h.py

import numpy as np
from api import get_klines
from indicators.ema import ema
from indicators.macd import macd
from indicators.rsi import rsi
from indicators.stoch import stochastic

from settings import (
    SYMBOL,
    INTERVAL_1H,
    CANDLES_1H,
    RSI_1H_UP,
    RSI_1H_DOWN,
    MACD_FAST,
    MACD_SLOW,
    MACD_SIGNAL,
)


def analyze_1h():
    """
    Analiza 1H:
        - trend: EMA50/EMA200
        - momentum: kierunek MACD histogramu
        - rsi_trend: UP / DOWN / NEUTRAL
    """

    # ─────────────────────────────────────────────
    # 1) Pobranie świec
    # ─────────────────────────────────────────────
    df = get_klines(SYMBOL, INTERVAL_1H, CANDLES_1H)

    if df is None or len(df) < 210:
        return None

    # ─────────────────────────────────────────────
    # 2) Indykatory
    # ─────────────────────────────────────────────
    df["ema_fast"] = ema(df["close"], 50)
    df["ema_slow"] = ema(df["close"], 200)

    df["macd"], df["macd_signal"], df["macd_hist"] = macd(
        df["close"], MACD_FAST, MACD_SLOW, MACD_SIGNAL
    )

    df["rsi"] = rsi(df["close"])

    df["stoch_k"], df["stoch_d"] = stochastic(
        df, k_period=14, d_period=3, smooth=3
    )

    last = df.iloc[-1]
    prev = df.iloc[-2]

    # sanity check
    if any(np.isnan([
        last["ema_fast"], last["ema_slow"],
        last["macd"], last["macd_signal"], last["macd_hist"],
        last["rsi"], last["stoch_k"], last["stoch_d"]
    ])):
        return None

    # ─────────────────────────────────────────────
    # 3) Trend EMA
    # ─────────────────────────────────────────────
    trend = "UP" if last["ema_fast"] > last["ema_slow"] else "DOWN"

    # ─────────────────────────────────────────────
    # 4) Momentum MACD histogram
    # ─────────────────────────────────────────────
    momentum = "UP" if last["macd_hist"] > prev["macd_hist"] else "DOWN"

    # ─────────────────────────────────────────────
    # 5) RSI trend
    # ─────────────────────────────────────────────
    if last["rsi"] > RSI_1H_UP:
        rsi_trend = "UP"
    elif last["rsi"] < RSI_1H_DOWN:
        rsi_trend = "DOWN"
    else:
        rsi_trend = "NEUTRAL"

    # ─────────────────────────────────────────────
    # 6) Wynik
    # ─────────────────────────────────────────────
    return {
        "trend": trend,
        "momentum": momentum,
        "rsi_trend": rsi_trend,
        "rsi": float(last["rsi"]),
        "macd_hist": float(last["macd_hist"]),
    }
