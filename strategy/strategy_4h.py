# strategy_4h.py — v2.3 (Looser Entries, ATR PRO, Pandas Stable)

import numpy as np
import pandas as pd
from utils.logger import get_logger
from api import get_klines
from indicators.ema import ema
from indicators.macd import macd
from indicators.rsi import rsi
from indicators.stoch import stochastic

from core.sanity import sanity_check_candles
from core.indicator_sanity import sanity_check_indicators
from core.force import load_force, clear_force
from core.trend_logger import log_trend
from core.watchdog import watchdog_candle_freeze
from logs.trade_logger import get_trade_logger

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
trade_logger = get_trade_logger()


# ─────────────────────────────────────────────
#  ATR PRO v2.3 — EMA, sanity, min/max
# ─────────────────────────────────────────────
def compute_atr(df: pd.DataFrame, period: int = 14) -> float | None:
    try:
        high = df["high"].astype(float)
        low = df["low"].astype(float)
        close = df["close"].astype(float)
    except Exception:
        return None

    prev_close = close.shift(1)

    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()

    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    # ATR EMA — szybsza, bardziej tradingowa wersja
    atr = true_range.ewm(span=period, adjust=False).mean()
    atr_value = float(atr.iloc[-1])

    # sanity: brak absurdalnych spike’ów
    if atr_value > close.iloc[-1] * 0.2:
        return None

    # minimalny ATR (żeby TS nie był za ciasny)
    min_atr = close.iloc[-1] * 0.0001
    if atr_value < min_atr:
        atr_value = min_atr

    return atr_value


def load_df_4h() -> pd.DataFrame | None:
    try:
        raw = get_klines(SYMBOL, INTERVAL_4H, CANDLES_4H)
    except Exception as e:
        logger.error(f"4H get_klines error: {e}")
        return None

    try:
        df = pd.DataFrame(
            raw,
            columns=[
                "open_time", "open", "high", "low", "close", "volume",
                "close_time", "quote_volume", "trades",
                "taker_buy_base", "taker_buy_quote", "ignore"
            ],
        )

        df = df[["open_time", "open", "high", "low", "close", "volume"]]
        df = df.astype(float)
        return df

    except Exception as e:
        logger.error(f"4H DataFrame conversion error: {e}")
        return None


def get_atr_4h(period: int = 14) -> float | None:
    df = load_df_4h()
    if df is None:
        return None

    if not sanity_check_candles(df, logger, "4H-ATR"):
        return None

    if not watchdog_candle_freeze(df, logger, "4H-ATR"):
        return None

    atr_value = compute_atr(df, period)
    if atr_value is None:
        return None

    if DEBUG:
        logger.info(f"4H ATR({period}) = {atr_value:.6f}")

    return atr_value


# ─────────────────────────────────────────────
#  GŁÓWNA FUNKCJA SYGNAŁÓW 4H
# ─────────────────────────────────────────────
def check_signal(df_override=None) -> Signal | None:

    # 0) FORCE BUY / SELL
    if df_override is None:
        force = load_force()

        if force.get("buy"):
            logger.warning("FORCE BUY aktywne — generuję BUY bez filtrów!")
            trade_logger.info("FORCE BUY")
            clear_force()
            return Signal(side="BUY", price=None)

        if force.get("sell"):
            logger.warning("FORCE SELL aktywne — generuję SELL bez filtrów!")
            trade_logger.info("FORCE SELL")
            clear_force()
            return Signal(side="SELL", price=None)

    # 1) ŚWIECE
    if df_override is not None:
        df = df_override.copy()
    else:
        df = load_df_4h()
        if df is None:
            return None

    if not sanity_check_candles(df, logger, "4H"):
        return None

    if not watchdog_candle_freeze(df, logger, "4H"):
        return None

    # 2) INDIKATORY
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

        atr_value = compute_atr(df)
        df["atr"] = np.nan
        if atr_value is not None:
            df.iloc[-1, df.columns.get_loc("atr")] = atr_value

    except Exception as e:
        logger.error(f"4H indicator error: {e}")
        return None

    last = df.iloc[-1]
    prev = df.iloc[-2]
    price = float(last["close"])

    if not sanity_check_indicators(last, logger, "4H"):
        return None

    # 3) FILTRY 1H / 1D
    try:
        h1 = analyze_1h()
        d1 = analyze_1d()
    except Exception as e:
        logger.warning(f"TF error (1H/1D): {e}")
        return None

    if not h1 or not d1:
        return None

    if DEBUG:
        log_trend(logger, "1H", h1)
        log_trend(logger, "1D", d1)

    if DEBUG:
        logger.info(
            f"DEBUG 4H: price={price}, "
            f"ema_fast={last['ema_fast']}, ema_slow={last['ema_slow']}, "
            f"macd={last['macd']}, macd_signal={last['macd_signal']}, "
            f"rsi={last['rsi']}, "
            f"stoch_k={last['stoch_k']}, stoch_d={last['stoch_d']}, "
            f"atr={last.get('atr', None)}"
        )

    # 4) BUY — poluzowane wejścia
    ema_distance = last["ema_fast"] - last["ema_slow"]
    # było 0.1%, teraz 0.03% — łapie trend wcześniej
    ema_ok = ema_distance > (last["close"] * 0.0003)

    stoch_cross = (
        prev["stoch_k"] < prev["stoch_d"]
        and last["stoch_k"] > last["stoch_d"]
        # było 0.5, teraz 0.2 — mniej rygorystyczny cross
        and abs(last["stoch_k"] - last["stoch_d"]) > 0.2
    )

    buy_checks = {
        "EMA trend (ema_fast > ema_slow + 0.03%)": ema_ok,
        # tolerancja na szum MACD
        "MACD (macd > macd_signal)": last["macd"] > last["macd_signal"] - 0.0001,
        "RSI (< 70)": last["rsi"] < RSI_OVERBOUGHT_4H,
        "STOCH cross (K > D)": stoch_cross,
        "Trend 1D": d1["trend"] == "UP",
        "Big trend 1D": d1["big_trend"] == "UP",
        "Trend 1H": h1["trend"] == "UP",
        "Momentum 1H": h1["momentum"] == "UP",
        "RSI trend 1H": h1["rsi_trend"] == "UP",
    }

    if DEBUG:
        logger.info("BUY — szczegółowa diagnostyka filtrów:")
        for name, result in buy_checks.items():
            logger.info(f" - {name}: {'OK' if result else 'FAIL'}")

    if all(buy_checks.values()):
        logger.info(f"BUY sygnał 4H @ {price}")
        trade_logger.info(f"BUY @ {price}")
        return Signal(side="BUY", price=price)

    # 5) SELL — bez zmian (może zostać bardziej rygorystyczny)
    sell_checks = {
        "EMA trend (ema_fast < ema_slow)": last["ema_fast"] < last["ema_slow"],
        "MACD (macd < macd_signal)": last["macd"] < last["macd_signal"],
        "RSI (> 30)": last["rsi"] > RSI_OVERSOLD_4H,
        "STOCH cross (K < D)": last["stoch_k"] < last["stoch_d"],
    }

    if DEBUG:
        logger.info("SELL — szczegółowa diagnostyka filtrów:")
        for name, result in sell_checks.items():
            logger.info(f" - {name}: {'OK' if result else 'FAIL'}")

    if all(sell_checks.values()):
        logger.info(f"SELL sygnał 4H @ {price}")
        trade_logger.info(f"SELL @ {price}")
        return Signal(side="SELL", price=price)

    logger.info("4H: brak sygnału")
    return None
