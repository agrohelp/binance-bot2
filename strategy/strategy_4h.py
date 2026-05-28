# strategy/strategy_4h.py

import numpy as np
from api import get_klines
from indicators.ema import ema
from indicators.macd import macd
from indicators.rsi import rsi
from indicators.stoch import stochastic

from settings import (
    SYMBOL,
    INTERVAL_4H,
    CANDLES_4H,
    EMA_FAST,
    EMA_SLOW,
    MACD_FAST,
    MACD_SLOW,
    MACD_SIGNAL,
    RSI_PERIOD,
    RSI_OVERBOUGHT_4H,
    RSI_OVERSOLD_4H,
    STO_K,
    STO_D,
    STO_SMOOTH,
)

from strategy.timeframe_1h import analyze_1h
from strategy.timeframe_1d import analyze_1d


def check_signal():
    """
    Główna logika sygnałów 4H.
    Zwraca:
        ("BUY", price)
        ("SELL", price)
        (None, price)
    """

    # ─────────────────────────────────────────────
    # 1) Pobranie świec
    # ─────────────────────────────────────────────
    df = get_klines(SYMBOL, INTERVAL_4H, CANDLES_4H)

    if df is None or len(df) < 50:
        return None, None

    # ─────────────────────────────────────────────
    # 2) Indykatory
    # ─────────────────────────────────────────────
    df["ema_fast"] = ema(df["close"], EMA_FAST)
    df["ema_slow"] = ema(df["close"], EMA_SLOW)

    df["macd"], df["macd_signal"], df["macd_hist"] = macd(
        df["close"], MACD_FAST, MACD_SLOW, MACD_SIGNAL
    )

    df["rsi"] = rsi(df["close"], RSI_PERIOD)

    df["stoch_k"], df["stoch_d"] = stochastic(
        df, STO_K, STO_D, STO_SMOOTH
    )

    # ─────────────────────────────────────────────
    # 3) Ostatnie wartości
    # ─────────────────────────────────────────────
    last = df.iloc[-1]
    prev = df.iloc[-2]

    price = float(last["close"])

    # sanity check
    if any(np.isnan([last["ema_fast"], last["ema_slow"], last["macd"], last["macd_signal"], last["rsi"]])):
        return None, price

    # ─────────────────────────────────────────────
    # 4) Filtry 1H i 1D
    # ─────────────────────────────────────────────
    try:
        h1 = analyze_1h()
        d1 = analyze_1d()
    except Exception:
        return None, price

    # brak danych z niższych/wyższych TF → brak sygnału
    if not h1 or not d1:
        return None, price

    # ─────────────────────────────────────────────
    # 5) BUY — rdzeń 4H
    # ─────────────────────────────────────────────
    buy_core = (
        last["ema_fast"] > last["ema_slow"] and
        last["macd"] > last["macd_signal"] and
        last["rsi"] < RSI_OVERBOUGHT_4H and
        prev["stoch_k"] < prev["stoch_d"] and
        last["stoch_k"] > last["stoch_d"]
    )

    buy_filters = (
        d1["trend"] == "UP" and
        d1["big_trend"] == "UP" and
        h1["trend"] == "UP" and
        h1["momentum"] == "UP" and
        h1["rsi_trend"] == "UP"
    )

    if buy_core and buy_filters:
        return "BUY", price

    # ─────────────────────────────────────────────
    # 6) SELL — rdzeń 4H
    # ─────────────────────────────────────────────
    sell_core = (
        last["ema_fast"] < last["ema_slow"] and
        last["macd"] < last["macd_signal"] and
        last["rsi"] > RSI_OVERSOLD_4H and
        prev["stoch_k"] > prev["stoch_d"] and
        last["stoch_k"] < last["stoch_d"]
    )

    sell_filters = (
        d1["trend"] == "DOWN" and
        d1["big_trend"] == "DOWN" and
        h1["trend"] == "DOWN" and
        h1["momentum"] == "DOWN" and
        h1["rsi_trend"] == "DOWN"
    )

    if sell_core and sell_filters:
        return "SELL", price

    # ─────────────────────────────────────────────
    # 7) Brak sygnału
    # ─────────────────────────────────────────────
    return None, price
