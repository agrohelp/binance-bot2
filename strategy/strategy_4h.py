# strategy/strategy_4h.py

import numpy as np
from utils.logger import get_logger
from api import get_klines
from indicators.ema import ema
from indicators.macd import macd
from indicators.rsi import rsi
from indicators.stoch import stochastic
from settings import DEBUG

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
)

from strategy.timeframe_1h import analyze_1h
from strategy.timeframe_1d import analyze_1d
from core.signal import Signal

logger = get_logger(__name__)


def check_signal() -> Signal | None:
    # 1) Świece
    try:
        df = get_klines(SYMBOL, INTERVAL_4H, CANDLES_4H)
    except Exception as e:
        logger.error(f"4H get_klines error: {e}")
        return None

    if df is None or len(df) < 50:
        logger.warning("4H: Za mało świec do analizy")
        return None

    # 2) Indykatory
    try:
        df["ema_fast"] = ema(df["close"], EMA_FAST)
        df["ema_slow"] = ema(df["close"], EMA_SLOW)

        macd_df = macd(df["close"], MACD_FAST, MACD_SLOW, MACD_SIGNAL)
        df["macd"] = macd_df["macd"]
        df["macd_signal"] = macd_df["signal"]
        df["macd_hist"] = macd_df["hist"]

        df["rsi"] = rsi(df["close"], RSI_PERIOD)

        stoch_df = stochastic(
            df["high"],
            df["low"],
            df["close"],
            STO_K,
            STO_D,
        )
        df["stoch_k"] = stoch_df["k"]
        df["stoch_d"] = stoch_df["d"]

    except Exception as e:
        logger.error(f"4H indicator error: {e}")
        return None

    last = df.iloc[-1]
    prev = df.iloc[-2]
    price = float(last["close"])

    indicators = [
        last["ema_fast"], last["ema_slow"],
        last["macd"], last["macd_signal"],
        last["rsi"], last["stoch_k"], last["stoch_d"]
    ]

    if any(np.isnan(indicators)):
        logger.warning("4H: NaN w indykatorach — brak sygnału")
        return None

    # 4) Filtry 1H / 1D
    try:
        h1 = analyze_1h()
        d1 = analyze_1d()
    except Exception as e:
        logger.warning(f"TF error (1H/1D): {e}")
        return None

    if not h1 or not d1:
        logger.info("Brak sygnału — filtry 1H/1D nie gotowe")
        return None

    # Test wł/wył DEBUG w settings.py
    if DEBUG:
        logger.info(
            f"DEBUG 4H: price={price}, "
            f"ema_fast={last['ema_fast']}, ema_slow={last['ema_slow']}, "
            f"macd={last['macd']}, macd_signal={last['macd_signal']}, "
            f"rsi={last['rsi']}, "
            f"stoch_k={last['stoch_k']}, stoch_d={last['stoch_d']}"
        )

    # k.Test

    # 5) BUY
    ema_distance = last["ema_fast"] - last["ema_slow"]
    ema_ok = ema_distance > (last["close"] * 0.001)

    stoch_cross = (
        prev["stoch_k"] < prev["stoch_d"] and
        last["stoch_k"] > last["stoch_d"] and
        abs(last["stoch_k"] - last["stoch_d"]) > 0.5
    )

    buy_core = (
        ema_ok and
        last["macd"] > last["macd_signal"] and
        last["rsi"] < RSI_OVERBOUGHT_4H and
        stoch_cross
    )

    buy_filters = (
        d1["trend"] == "UP" and
        d1["big_trend"] == "UP" and
        h1["trend"] == "UP" and
        h1["momentum"] == "UP" and
        h1["rsi_trend"] == "UP"
    )

    if buy_core and buy_filters:
        logger.info(f"BUY sygnał 4H @ {price}")
        return Signal(side="BUY", price=price)

    # 6) SELL (na przyszłość, na razie bot gra tylko LONG)
    # Możesz zostawić jako placeholder:
    # ...

    logger.info("4H: brak sygnału")
    return None
