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
    ema_ok = ema_distance > (last["close"] * 0.0003)

    stoch_cross = (
        prev["stoch_k"] < prev["stoch_d"]
        and last["stoch_k"] > last["stoch_d"]
        and abs(last["stoch_k"] - last["stoch_d"]) > 0.2
    )

    buy_checks = {
        "EMA trend (ema_fast > ema_slow + 0.03%)": ema_ok,
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


# ─────────────────────────────────────────────
#  DODATKOWE FUNKCJE DLA TELEGRAM / STATUS
# ─────────────────────────────────────────────
def get_trend_1h():
    h1 = analyze_1h()
    return {
        "trend": h1["trend"],
        "momentum": h1["momentum"],
        "rsi_trend": h1["rsi_trend"],
    }


def get_trend_1d():
    d1 = analyze_1d()
    return {
        "trend": d1["trend"],
        "big_trend": d1["big_trend"],
    }


def _get_last_context():
    df = load_df_4h()
    if df is None:
        return None, None, None, None

    if not sanity_check_candles(df, logger, "4H-STATUS"):
        return None, None, None, None

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

    except Exception:
        return None, None, None, None

    last = df.iloc[-1]
    prev = df.iloc[-2]
    price = float(last["close"])
    return df, last, prev, price


def get_buy_diagnostics():
    df, last, prev, price = _get_last_context()
    if df is None:
        return {}

    h1 = analyze_1h()
    d1 = analyze_1d()

    ema_distance = last["ema_fast"] - last["ema_slow"]
    ema_ok = ema_distance > (last["close"] * 0.0003)

    stoch_cross = (
        prev["stoch_k"] < prev["stoch_d"]
        and last["stoch_k"] > last["stoch_d"]
        and abs(last["stoch_k"] - last["stoch_d"]) > 0.2
    )

    buy_checks = {
        "EMA trend (ema_fast > ema_slow + 0.03%)": "OK" if ema_ok else "FAIL",
        "MACD (macd > macd_signal)": "OK" if last["macd"] > last["macd_signal"] - 0.0001 else "FAIL",
        "RSI (< 70)": "OK" if last["rsi"] < RSI_OVERBOUGHT_4H else "FAIL",
        "STOCH cross (K > D)": "OK" if stoch_cross else "FAIL",
        "Trend 1D": "OK" if d1["trend"] == "UP" else "FAIL",
        "Big trend 1D": "OK" if d1["big_trend"] == "UP" else "FAIL",
        "Trend 1H": "OK" if h1["trend"] == "UP" else "FAIL",
        "Momentum 1H": "OK" if h1["momentum"] == "UP" else "FAIL",
        "RSI trend 1H": "OK" if h1["rsi_trend"] == "UP" else "FAIL",
    }
    return buy_checks


def get_sell_diagnostics():
    df, last, prev, price = _get_last_context()
    if df is None:
        return {}

    sell_checks = {
        "EMA trend (ema_fast < ema_slow)": "OK" if last["ema_fast"] < last["ema_slow"] else "FAIL",
        "MACD (macd < macd_signal)": "OK" if last["macd"] < last["macd_signal"] else "FAIL",
        "RSI (> 30)": "OK" if last["rsi"] > RSI_OVERSOLD_4H else "FAIL",
        "STOCH cross (K < D)": "OK" if last["stoch_k"] < last["stoch_d"] else "FAIL",
    }
    return sell_checks


def get_debug_report():
    trend_1h = get_trend_1h()
    trend_1d = get_trend_1d()
    df, last, prev, price = _get_last_context()
    if df is None:
        return "Brak danych 4H do raportu."

    debug = {
        "price": float(last["close"]),
        "ema_fast": float(last["ema_fast"]),
        "ema_slow": float(last["ema_slow"]),
        "macd": float(last["macd"]),
        "macd_signal": float(last["macd_signal"]),
        "rsi": float(last["rsi"]),
        "stoch_k": float(last["stoch_k"]),
        "stoch_d": float(last["stoch_d"]),
        "atr": float(last["atr"]) if not np.isnan(last["atr"]) else None,
    }

    buy_diag = get_buy_diagnostics()
    sell_diag = get_sell_diagnostics()

    msg = "📊 *Status 4H*\n\n"

    msg += "⏱ *TREND 1H:*\n"
    msg += f"• 📈 trend: {trend_1h['trend']}\n"
    msg += f"• ⚡ momentum: {trend_1h['momentum']}\n"
    msg += f"• 🎯 rsi_trend: {trend_1h['rsi_trend']}\n\n"

    msg += "📅 *TREND 1D:*\n"
    msg += f"• 📈 trend: {trend_1d['trend']}\n"
    msg += f"• 🧭 big_trend: {trend_1d['big_trend']}\n\n"

    msg += "🧪 *DEBUG 4H:*\n"
    msg += (
        f"price={debug['price']}, "
        f"ema_fast={debug['ema_fast']}, "
        f"ema_slow={debug['ema_slow']}, "
        f"macd={debug['macd']}, "
        f"macd_signal={debug['macd_signal']}, "
        f"rsi={debug['rsi']}, "
        f"stoch_k={debug['stoch_k']}, "
        f"stoch_d={debug['stoch_d']}, "
        f"atr={debug['atr']}\n\n"
    )

    msg += "🟢 *BUY diagnostyka:*\n"
    for k, v in buy_diag.items():
        msg += f"• {k}: {v}\n"
    msg += "\n"

    msg += "🔴 *SELL diagnostyka:*\n"
    for k, v in sell_diag.items():
        msg += f"• {k}: {v}\n"

    return msg


def get_state_snapshot():
    """Snapshot do wykrywania zmian dla status_report."""
    trend_1h = get_trend_1h()
    trend_1d = get_trend_1d()
    buy_diag = get_buy_diagnostics()
    sell_diag = get_sell_diagnostics()

    return {
        "trend_1h": trend_1h,
        "trend_1d": trend_1d,
        "buy_diag": buy_diag,
        "sell_diag": sell_diag,
    }
